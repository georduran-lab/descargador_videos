from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, emit
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

download_path = "downloads"
os.makedirs(download_path, exist_ok=True)

# ---- PROGRESS HOOK ----
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

# ---- ROUTES ----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    option = request.form['format']  # mp3 o mp4

    # Configuración dinámica según formato
    if option == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{download_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:  # mp4
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{download_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4'
        }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Buscar archivo más reciente
    files = os.listdir(download_path)
    latest = max([os.path.join(download_path, f) for f in files], key=os.path.getctime)
    return send_file(latest, as_attachment=True)

# ---- RUN ----
if __name__ == '__main__':
    socketio.run(app, debug=True)




