from flask import Flask, render_template, request, send_file, redirect, url_for
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
    url = request.form.get("url", "").strip()
    formato = request.form.get("formato", "mp4")

    if not url:
        return "❌ URL faltante", 400

    # Opciones de yt-dlp
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
        # Descargar con yt-dlp
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Ajustar extensión final según el formato
        if formato == "mp3":
            filename = os.path.splitext(filename)[0] + ".mp3"
        elif formato == "mp4":
            filename = os.path.splitext(filename)[0] + ".mp4"

        # Enviar archivo al cliente
        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"""
        <h2>❌ Ocurrió un error</h2>
        <p>{str(e)}</p>
        <a href="/">⬅️ Volver</a>
        """, 500


if __name__ == "__main__":
    # Render expone el puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


