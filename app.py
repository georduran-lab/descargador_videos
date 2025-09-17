from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Hook para enviar progreso en tiempo real al frontend
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%')
        try:
            progress = float(percent.replace('%', ''))
            socketio.emit('progress', {"progress": progress, "status": "downloading"})
        except:
            pass
    elif d['status'] == 'finished':
        socketio.emit('progress', {"progress": 100, "status": "finished"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    formato = request.form.get("format", "mp3")

    if not url:
        return "❌ URL faltante", 400

    if formato == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:  # mp4
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
        }

    # Descargar archivo
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # Ajustar extensión correcta
    if formato == "mp3":
        filename = os.path.splitext(filename)[0] + ".mp3"
    else:
        filename = os.path.splitext(filename)[0] + ".mp4"

    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)






