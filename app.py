from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from yt_dlp import YoutubeDL
import os, threading, time
import random
import webbrowser
import threading
import sys 
from waitress import serve

phrases = [
    "🚀 ¡Al infinito y más allá! – Buzz Lightyear (Toy Story)",
    "🤡 ¿Por qué tan serio? – Joker (The Dark Knight)",
    "🦁 Hakuna Matata, vive y sé feliz. – El Rey León",
    "🌱 Yo soy Groot. – Guardianes de la Galaxia",
    "💊 Say my name. – Walter White (Breaking Bad)",
    "🍩 D’oh! – Homero Simpson",
    "💻 Yo no elegí la vida de programador, la vida de programador me eligió.",
    "📡 Hasta el infinito… pero con WiFi, por favor.",
    "🐞 No es un bug, es una feature.",
    "🤓 Bazinga! – Sheldon Cooper (The Big Bang Theory)",
    "🏃 Corre Forrest, corre! – Forrest Gump",
    "💸 Trabajo bajo presión… de mis deudas.",
    "🍋 Si la vida te da limones, pide sal y tequila.",
    "🌀 Soy multitask: puedo procrastinar y estresarme al mismo tiempo.",
    "😴 A veces finjo ser normal… pero me aburro rápido.",
    "⏰ Quien madruga… tiene sueño todo el día.",
    "📶 El WiFi se fue… y con él, mi felicidad.",
    "🔋 No soy vago, estoy en modo ahorro de energía.",
    "🧼 Mi superpoder es desaparecer cuando hay que fregar platos.",
    "🐢 El que ríe último, piensa más lento.",
    "☕ Pienso, luego existo… pero primero, café.",
    "💡 La imaginación es más importante que el conocimiento… excepto si estás buscando las llaves.",
    "🦇 Sé tú mismo… a menos que puedas ser Batman. Entonces sé Batman.",
    "🛠️ Divide y vencerás… los problemas en tickets de soporte.",
    "📚 El conocimiento es poder… y el WiFi es felicidad.",
    "⌛ El tiempo es oro… y yo ando en bancarrota.",
    "😁 La vida es breve. Sonríele al WiFi cuando conecte.",
    "🌀 Si no puedes convencerlos, confúndelos. – Harry S. Truman",
    "🥶 La esperanza es lo último que se pierde… salvo cuando abres la nevera y no hay nada.",
    "🚪 Algunas personas crean felicidad dondequiera que van… otras cuando se van."
]

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = "super_secret_key"

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def format_views(n):
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return str(n)

def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    mins, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    else:
        return f"{mins}m {secs}s"

def obtener_info(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    data = {
        "title": info.get("title"),
        "author": info.get("uploader"),
        "duration": format_duration(info.get("duration", 0)),
        "views": format_views(info.get("view_count", 0)),
        "upload_date": info.get("upload_date"),
        "thumbnail": info.get("thumbnail"),
        "url": url
    }

    if data["upload_date"]:
        d = data["upload_date"]
        data["upload_date"] = f"{d[6:8]}/{d[4:6]}/{d[0:4]}"

    return data

def descargar_video(url, formato):
    """
    Descarga un video o audio de YouTube según el formato indicado.
    MP4: video con audio
    MP3: audio con carátula incrustada
    """

    common_opts = {
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        # Usa cookies directamente desde Chrome, también puedes poner "firefox" o "edge"
        "cookiesfrombrowser": ("chrome",)
    }

    if formato == "mp4":
        ydl_opts = {
            **common_opts,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4"
        }
    else:
        ydl_opts = {
            **common_opts,
            "format": "bestaudio/best",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail"}
            ]
        }

    # Ejecuta la descarga
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # Obtiene la ruta del archivo descargado
    file_path = info["requested_downloads"][0]["filepath"]
    return file_path


def remove_file_later(path):
    def _remove():
        while True:
            try:
                with open(path, "a"): pass
                os.remove(path)
                break
            except:
                time.sleep(1)
    threading.Thread(target=_remove, daemon=True).start()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

threading.Timer(1.5, open_browser).start()

@app.route("/", methods=["GET", "POST"])
def index():
    phrase = random.choice(phrases) #FRASES RANDOM
    video_info = None
    
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            flash("Por favor pega una URL válida.")
            return redirect(url_for("index"))

        if "preview" in request.form:
            try:
                video_info = obtener_info(url)
                # Guardamos info en sesión o query string si quieres persistir
                return render_template("index.html", video_info=video_info, url=url)
            except Exception as e:
                flash(f"Error al obtener info: {e}")
                return redirect(url_for("index"))

        # POST de descarga, redirigimos a /download
        formato = request.form.get("formato")
        if url and formato:
            return redirect(url_for("download") + f"?url={url}&formato={formato}")

    return render_template("index.html", video_info=None, url="", phrase=phrase)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    formato = request.form.get("formato")
    if not url or not formato:
        return "Faltan datos", 400
    try:
        path = descargar_video(url, formato)
        response = send_file(path, as_attachment=True, download_name=os.path.basename(path))
        remove_file_later(path)
        return response
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    serve(app.app, host="0.0.0.0", port=8080)
