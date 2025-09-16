from flask import Flask, render_template, request, send_file
import os
from yt_dlp import YoutubeDL

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/descargar", methods=["POST"])
def descargar():
    url = request.form["url"]
    formato = request.form["formato"]

    if not url:
        return "❌ URL faltante"

    if formato == "mp4":
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
        }
    else:  # mp3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if formato == "mp3":
            filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"❌ Error: {e}"

if __name__ == "__main__":
    # Railway expone el puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
