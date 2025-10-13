from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from yt_dlp import YoutubeDL
import os, threading, time
import random
import webbrowser
import threading
import sys 
import time 

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
    
def format_size(size_bytes: int) -> str:
    try:
        size = float(size_bytes)
    except Exception:
        return "0 B"
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"

def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    mins, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    else:
        return f"{mins}m {secs}s"

# UPDATE ----------------------------------------------------------------
def obtener_info(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,       # ✅ evita análisis innecesario de listas
        "force_generic_extractor": False,
        "noplaylist": True,          # ✅ ignora listas de reproducción
        "player_client": "android",  # ✅ usa cliente Android (sin cifrados nsig)
        "cachedir": os.path.expanduser("~/.cache/yt-dlp"),  # ✅ usa caché
        "no_warnings": True,
        "socket_timeout": 10,
        "retries": 3,
        "source_address": "0.0.0.0",
        "concurrent_fragment_downloads": 8,
        "quiet": True,
    }
# UPDATE------------------------------------------------------------------
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    data = {
        "title": info.get("title"),
        "author": info.get("uploader"),
        "duration": format_duration(info.get("duration", 0)),
        "views": format_views(info.get("view_count", 0)),
        "upload_date": info.get("upload_date"),
        "thumbnail": info.get("thumbnail"),
        "url": url,
    }

    if data["upload_date"]:
        d = data["upload_date"]
        data["upload_date"] = f"{d[6:8]}/{d[4:6]}/{d[0:4]}"

     # --- 🔍 Buscar formatos de video/audio ---
    formats = info.get("formats", [])
    best_video = None
    best_audio = None

    for f in formats:
        # Buscar mejor video MP4
        if f.get("vcodec") != "none" and f.get("ext") == "mp4":
            if not best_video or f.get("height", 0) > best_video.get("height", 0):
                best_video = f

        # Buscar mejor audio (m4a, mp3, webm)
        if f.get("acodec") != "none" and f.get("ext") in ["m4a", "mp3", "webm"]:
            if not best_audio or f.get("abr", 0) > best_audio.get("abr", 0):
                best_audio = f

    # --- 📊 Agregar detalles ---
    video_size = (best_video.get("filesize") or best_video.get("filesize_approx") or 0) if best_video else 0
    audio_size = (best_audio.get("filesize") or best_audio.get("filesize_approx") or 0) if best_audio else 0

    total_size = video_size + audio_size
    total_size_mb = f"{total_size / (1024 * 1024):.2f} MB" if total_size > 0 else "Desconocido"

    # --- 📊 Agregar detalles de calidad ---
    if best_video:
        data["video_resolution"] = f"{best_video.get('height', 0)}p"
        data["video_fps"] = f"{best_video.get('fps', 0)} FPS" if best_video.get('fps') else "N/A"
        data["video_size"] = total_size_mb  # ✅ suma de video + audio
    else:
        data["video_resolution"] = "N/A"
        data["video_fps"] = "N/A"
        data["video_size"] = "N/A"

    if best_audio:
        data["audio_quality"] = f"{best_audio.get('abr', 0)} kbps"
        size = best_audio.get("filesize") or best_audio.get("filesize_approx", 0)
        data["audio_size"] = f"{size / (1024 * 1024):.2f} MB" if size else "Desconocido"
    else:
        data["audio_quality"] = "N/A"
        data["audio_size"] = "N/A"


    return data

# UPDATE------------------------------------------------------------------

def descargar_video(url, formato):
    """
    Descarga un video o audio de YouTube según el formato indicado.
    MP4: video con audio
    MP3: audio con carátula incrustada
    """

    def progreso(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1  # evita división por cero
            descargado = d.get("downloaded_bytes", 0)
            velocidad = d.get("speed") or 0
            porcentaje = (descargado / total) * 100
            print(f"⬇️ {porcentaje:.1f}% | {velocidad/1024:.1f} KB/s", end="\r")
        elif d.get("status") == "finished":
            print("\n✅ Descarga completada, procesando...")

    # 🔧 Configuración base
    base_opts = {
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "progress_hooks": [progreso],
        "quiet": True,
        "concurrent_fragment_downloads": 5,
        "http_chunk_size": 5_000_000,
        "retries": 10,
        "fragment_retries": 10,
        "no_warnings": True,
    }

    # 🎬 Formatos según tipo
    if formato == "mp4":
        ydl_opts = {
            **base_opts,
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
        }
    else:  # MP3
        ydl_opts = {
            **base_opts,
            "format": "bestaudio/best",
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # ✅ proteger contra errores internos
            if not info or "requested_downloads" not in info:
                raise Exception("Descarga incompleta o sin información válida.")
    except ZeroDivisionError:
        print("\n⚠️ Se detectó división por cero (probablemente tamaño desconocido). Reintentando sin progreso...\n")
        ydl_opts.pop("progress_hooks", None)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

    file_path = (
        info["requested_downloads"][0].get("filepath")
        if "requested_downloads" in info and info["requested_downloads"]
        else os.path.join(DOWNLOAD_FOLDER, f"{info.get('title', 'video')}.mp4")
    )

    return file_path

def iniciar_descarga_en_hilo(url, formato):
    def _run():
        try:
            path = descargar_video(url, formato)
            print(f"✅ Descargado: {path}")
        except Exception as e:
            print(f"❌ Error al descargar: {e}")

    threading.Thread(target=_run, daemon=True).start()

# UPDATE------------------------------------------------------------------

def remove_file_later(path):
    def _remove():
        # Espera 10 Minutos antes de intentar eliminar el archivo
        time.sleep(600)
        while True:
            try:
                # Verifica que el archivo exista antes de intentar eliminarlo
                if os.path.exists(path):
                    with open(path, "a"): 
                        pass
                    os.remove(path)
                break
            except Exception:
                # Espera 1 segundo antes de volver a intentar
                time.sleep(1)

    # Inicia el hilo en segundo plano
    threading.Thread(target=_remove, daemon=True).start()

#def open_browser():
#   webbrowser.open_new("http://127.0.0.1:5000")

#threading.Timer(1.5, open_browser).start()

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
                return render_template("index.html", video_info=video_info, url=url, phrase=phrase)
            except Exception as e:
                flash(f"Error al obtener info: {e}")
                return redirect(url_for("index"))

        # POST de descarga, redirigimos a /download
        formato = request.form.get("formato")
        if url and formato:
            return redirect(url_for("download") + f"?url={url}&formato={formato}")

    return render_template("index.html", video_info=None, url="", phrase=phrase)

@app.route("/download", methods=["GET", "POST"])
def download():
    # Lee datos desde POST o GET
    url = request.form.get("url") or request.args.get("url")
    formato = request.form.get("formato") or request.args.get("formato")

    # Si el navegador hace un GET sin parámetros (confirmación)
    if request.method == "GET" and (not url or not formato):
        return redirect(url_for("index"))

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
    #import socket
    #local_ip = socket.gethostbyname(socket.gethostname())
    #print(f"Servidor disponible en: http://{local_ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
