import os
import re
import uuid
import json
import queue
import threading
import subprocess
import platform
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, Response, stream_with_context, jsonify, send_file
)
from pytubefix import YouTube
import random
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
import ffmpeg
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"


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


# -------------------------
# Utilidades
# -------------------------
def get_default_downloads():
    d = Path.home() / "Downloads"
    if d.exists():
        return str(d)
    d2 = Path.home() / "Descargas"
    return str(d2) if d2.exists() else str(Path.home())

DOWNLOADS_PATH = get_default_downloads()

def clean_url(url):
    """Extrae solo el ID de video y reconstruye la URL limpia"""
    if not url:
        return url
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url

def format_views(views: int) -> str:
    if views >= 1_000_000_000:
        return f"{views/1_000_000_000:.1f}B".rstrip("0").rstrip(".")
    elif views >= 1_000_000:
        return f"{views/1_000_000:.1f}M".rstrip("0").rstrip(".")
    elif views >= 1_000:
        return f"{views/1_000:.1f}K".rstrip("0").rstrip(".")
    else:
        return str(views)

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

# -------------------------
# Tareas y colas de progreso (global)
# -------------------------
tasks = {}  # task_id -> {'queue': Queue(), 'progress_map': {...}, 'total': int}

# -------------------------
# Rutas principales - UPDATE
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    phrase = random.choice(phrases)
    video_info = None
    url = ""

    if request.method == "POST":
        url = clean_url(request.form.get("url"))
        try:
            yt = YouTube(url)

            # Duración del video en formato hh:mm:ss
            duration = format_duration(yt.length)

            # 🔹 Filtrar solo videos en 1080p y que tengan FPS válidos
            video_streams = [
                s for s in yt.streams.filter(adaptive=True, type="video", res="1080p")
                if getattr(s, "fps", None) and s.fps >= 24
            ]

            # 🔹 Ordenar por FPS de mayor a menor
            video_streams = sorted(video_streams, key=lambda s: s.fps or 0, reverse=True)

            # 🔹 Escoger el mejor stream de video (1080p, fps máximo)
            video_stream = video_streams[0] if video_streams else None

            # 🔹 Escoger el mejor audio disponible
            audio_stream = yt.streams.filter(adaptive=True, type="audio").order_by("abr").desc().first()

           if video_stream and audio_stream:
            fps = video_stream.fps or 0
            resolution = video_stream.resolution or "N/A"
        
            # Etiqueta de calidad (ejemplo: 1080p60)
            video_quality = f"{resolution}{fps if fps else ''}"
        
            # ✅ Calcular tamaños seguros
            video_size_bytes = (getattr(video_stream, "filesize", 0) or 0) + (getattr(audio_stream, "filesize", 0) or 0)
            video_size = format_size(video_size_bytes)
        
            audio_quality = getattr(audio_stream, "abr", "unknown")
            audio_size_bytes = getattr(audio_stream, "filesize", 0) or 0
            audio_size = format_size(audio_size_bytes)
        
            video_info = {
                "title": yt.title,
                "author": yt.author,
                "views": format_views(yt.views),
                "length": duration,
                "thumbnail": yt.thumbnail_url,
                "url": url,
                "publish_date": yt.publish_date.strftime("%d/%m/%Y") if getattr(yt, "publish_date", None) else "",
                "video_quality": video_quality,
                "fps": fps,
                "video_size": video_size,
                "audio_quality": audio_quality,
                "audio_size": audio_size
            }

            else:
                video_info = {"error": "No se encontraron streams en 1080p con fps >= 24."}

        except Exception as e:
            video_info = {"error": f"No se pudo obtener la información: {e}"}

    return render_template(
        "index.html",
        video_info=video_info,
        url=url,
        downloads_path=DOWNLOADS_PATH,
        phrase=phrase
    )

# -------------------------
# Iniciar descarga: endpoints que lanzan hilo en background y devuelven task_id
# -------------------------
@app.route("/start_download_mp4", methods=["POST"])
def start_download_mp4():
    url = clean_url(request.form.get("url"))
    if not url:
        return jsonify({"error": "URL vacía"}), 400
    task_id = uuid.uuid4().hex
    q = queue.Queue()
    tasks[task_id] = {'queue': q}
    thread = threading.Thread(target=_download_task_mp4, args=(task_id, url), daemon=True)
    thread.start()
    return jsonify({"task_id": task_id}), 202 #ESTA FUNCIONA

@app.route("/start_download_mp3", methods=["POST"])
def start_download_mp3():
    url = clean_url(request.form.get("url"))
    if not url:
        return jsonify({"error": "URL vacía"}), 400
    task_id = uuid.uuid4().hex
    q = queue.Queue()
    tasks[task_id] = {'queue': q}
    thread = threading.Thread(target=_download_task_mp3, args=(task_id, url), daemon=True)
    thread.start()
    return jsonify({"task_id": task_id}), 202 #ESTA FUNCIONA

# -------------------------
# SSE: stream de progreso
# -------------------------
@app.route("/progress/<task_id>")
def progress(task_id):
    task = tasks.get(task_id)
    def event_stream():
        if not task:
            yield 'data: ' + json.dumps({"status": "error", "message": "task not found"}) + '\n\n'
            return
        q = task['queue']
        while True:
            msg = q.get()
            yield 'data: ' + json.dumps(msg) + '\n\n'
            if msg.get('status') in ('finished', 'error'):
                break
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

# -------------------------
# Funciones internas de descarga (ejecutadas en thread)
# -------------------------
def _download_task_mp4(task_id, url):
    q = tasks[task_id]['queue']
    try:
        yt = YouTube(url)

        video_stream = yt.streams.filter(adaptive=True, type="video").order_by("resolution").desc().first()
        audio_stream = yt.streams.filter(adaptive=True, type="audio").order_by("abr").desc().first()

        v_size = video_stream.filesize or 0
        a_size = audio_stream.filesize or 0
        total = v_size + a_size
        # map para ir guardando lo descargado por stream itag
        progress_map = {str(video_stream.itag): 0, str(audio_stream.itag): 0}
        tasks[task_id]['progress_map'] = progress_map
        tasks[task_id]['total'] = total

        def on_progress(stream, chunk, bytes_remaining):
            try:
                downloaded = stream.filesize - bytes_remaining
            except Exception:
                downloaded = 0
            progress_map[str(stream.itag)] = downloaded
            downloaded_total = sum(progress_map.values())
            percent = int(downloaded_total / total * 100) if total > 0 else 0
            q.put({
                "status": "downloading",
                "percent": percent,
                "downloaded": downloaded_total,
                "total": total
            })

        yt.register_on_progress_callback(on_progress)

        q.put({"status": "started", "message": "Iniciando descarga (video...)"})
        video_ext = getattr(video_stream, "subtype", "mp4") or "mp4"
        audio_ext = getattr(audio_stream, "subtype", "mp3") or "mp3"

        video_filename = f"task_{task_id}_video.{video_ext}"
        audio_filename = f"task_{task_id}_audio.{audio_ext}"

        video_path = os.path.join(DOWNLOADS_PATH, video_filename)
        audio_path = os.path.join(DOWNLOADS_PATH, audio_filename)

        video_stream.download(DOWNLOADS_PATH, video_filename)
        audio_stream.download(DOWNLOADS_PATH, audio_filename)

        # Nombre final seguro
        safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in yt.title)
        output_path = os.path.join(DOWNLOADS_PATH, safe_title + ".mp4")

        # Unir con ffmpeg
        q.put({"status": "merging", "message": "Uniendo audio y video (ffmpeg)...", "percent": 100})
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # limpiar temporales
        try:
            os.remove(video_path)
            os.remove(audio_path)
        except Exception:
            pass

        q.put({"status": "finished", "message": f"✅ Descargado: {output_path}", "output_path": output_path})

    except Exception as e:
        q.put({"status": "error", "message": f"❌ Error: {e}"})

def _download_task_mp3(task_id, url):
    q = tasks[task_id]['queue']
    try:
        yt = YouTube(url)

        # 🎵 Mejor audio disponible
        audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        a_size = audio_stream.filesize or 0
        tasks[task_id]['total'] = a_size
        progress_map = {str(audio_stream.itag): 0}
        tasks[task_id]['progress_map'] = progress_map

        def on_progress(stream, chunk, bytes_remaining):
            try:
                downloaded = stream.filesize - bytes_remaining
            except Exception:
                downloaded = 0
            progress_map[str(stream.itag)] = downloaded
            downloaded_total = sum(progress_map.values())
            percent = int(downloaded_total / (a_size or 1) * 100) if a_size > 0 else 0
            q.put({"status": "downloading", "percent": percent, "downloaded": downloaded_total, "total": a_size})

        yt.register_on_progress_callback(on_progress)

        q.put({"status": "started", "message": "Iniciando descarga de audio..."})

        # Archivo temporal en MP4 (YouTube entrega el audio en contenedor MP4)
        temp_audio = os.path.join(DOWNLOADS_PATH, f"task_{task_id}_audio.mp4")
        audio_stream.download(DOWNLOADS_PATH, filename=f"task_{task_id}_audio.mp4")

        q.put({"status": "info", "message": "Convirtiendo a MP3 con miniatura..."})

        # Nombre seguro para el archivo final
        safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in yt.title)
        output_mp3 = os.path.join(DOWNLOADS_PATH, safe_title + ".mp3")

        # Descargar miniatura
        thumb_path = os.path.join(DOWNLOADS_PATH, f"task_{task_id}_thumb.jpg")
        try:
            import requests
            r = requests.get(yt.thumbnail_url, timeout=10)
            with open(thumb_path, "wb") as f:
                f.write(r.content)
        except Exception:
            thumb_path = None  # si falla, no se añade carátula

        # Convertir audio + insertar miniatura con ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_audio,
            "-i", thumb_path if thumb_path else temp_audio,  # si no hay thumb, solo audio
            "-map", "0:a", "-map", "1:v?",
            "-c:a", "libmp3lame", "-b:a", "320k",
            "-id3v2_version", "3",
            "-metadata", f"title={yt.title}",
            output_mp3
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # limpiar temporales
        try:
            os.remove(temp_audio)
            if thumb_path:
                os.remove(thumb_path)
        except Exception:
            pass

        q.put({"status": "finished", "message": f"🎵 Audio listo con carátula: {output_mp3}", "output_path": output_mp3})

    except Exception as e:
        q.put({"status": "error", "message": f"❌ Error: {e}"})


# -------------------------
# Nueva ruta: devolver calidades disponibles
# -------------------------
@app.route("/get_streams", methods=["POST"])
def get_streams():
    url = clean_url(request.json.get("url"))
    try:
        yt = YouTube(url)

        # 🎥 Video con audio (progresivos, más simples de manejar)
        video_streams = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()

        # 🎥 + 🎵 Progresivos (para que al menos haya 1 "directo" con audio)
        progressive = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()

        # 🎵 Solo audio
        audio_streams = yt.streams.filter(only_audio=True).order_by("abr").desc()

        # armamos lista para frontend
        result = []

            # ✅ Progresivos (video+audio)
        for s in yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc():
            result.append({
                "itag": s.itag,
                "type": "progressive",
                "resolution": s.resolution,
                "fps": getattr(s, "fps", None),
                "size": format_size(s.filesize or 0)
            })

        # 🎥 Solo video (adaptativos)
        for s in yt.streams.filter(only_video=True, file_extension="mp4").order_by("resolution").desc():
            result.append({
                "itag": s.itag,
                "type": "video",
                "resolution": s.resolution,
                "fps": getattr(s, "fps", None),
                "size": format_size(s.filesize or 0)
            })

        # 🎵 Solo audio
        for s in yt.streams.filter(only_audio=True).order_by("abr").desc():
            result.append({
                "itag": s.itag,
                "type": "audio",
                "abr": getattr(s, "abr", "N/A"),
                "size": format_size(s.filesize or 0)
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/streams", methods=["POST"])
def streams():
    url = clean_url(request.json["url"])
    yt = YouTube(url)

    # Video (progresivos con audio incluido)
    video_streams = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()
    video = [
        {"itag": s.itag, "resolution": s.resolution, "size": format_size(s.filesize)}
        for s in video_streams
    ]

    # Audio
    audio_streams = yt.streams.filter(only_audio=True).order_by("abr").desc()
    audio = [
        {"itag": s.itag, "abr": s.abr, "size": format_size(s.filesize)}
        for s in audio_streams
    ]

    return jsonify({"video": video, "audio": audio})


@app.route("/download_mp4", methods=["POST"])
def download_mp4():
    url = clean_url(request.json["url"])
    itag = request.json["itag"]
    yt = YouTube(url)

    # 🎥 + 🎵 Progresivos (para que al menos haya 1 "directo" con audio)
    progressive = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()

    result = []

    # ✅ Progresivos (video+audio)
    for s in yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc():
            result.append({
                "itag": s.itag,
                "type": "progressive",
                "resolution": s.resolution,
                "fps": getattr(s, "fps", None),
                "size": format_size(s.filesize or 0)
            })
    

    stream = yt.streams.get_by_itag(itag)
    file_path = os.path.join(DOWNLOADS_PATH, yt.title + ".mp4")
    stream.download(output_path=DOWNLOADS_PATH, filename=os.path.basename(file_path))
    return jsonify({"success": True, "file": file_path})


@app.route("/download_mp3", methods=["POST"])
def download_mp3():
    url = clean_url(request.json["url"])
    itag = request.json["itag"]
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)
    file_path = os.path.join(DOWNLOADS_PATH, yt.title + ".mp3")
    stream.download(output_path=DOWNLOADS_PATH, filename=os.path.basename(file_path))
    return jsonify({"success": True, "file": file_path})


# -------------------------
# Ejecutar app
# -------------------------
if __name__ == "__main__":
    print("📂 Carpeta de descargas usada:", DOWNLOADS_PATH)
    # app.run(host="0.0.0.0", port=5000, debug=False)
    app = Flask(__name__)





