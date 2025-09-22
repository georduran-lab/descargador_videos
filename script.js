function showOverlay(){
    document.getElementById('overlay').classList.add('show');
    document.getElementById('modal-title').textContent = 'Descargando...';
    document.getElementById('status-text').textContent = 'Conectando al servidor...';
    setProgress(0);
  }
  function hideOverlay(){
    document.getElementById('overlay').classList.remove('show');
  }
  function setProgress(p){
    const fill = document.getElementById('progress-fill');
    const pct = Math.max(0, Math.min(100, p));
    fill.style.width = pct + '%';
    document.getElementById('percent-text').textContent = pct + '%';
  }

  async function startDownload(kind){
    const videoUrl = document.getElementById('video_url')?.value || document.getElementById('url_input')?.value;
    if(!videoUrl){
      alert('Pega primero la URL y pulsa "Obtener información" o escribe la URL.');
      return;
    }
    const endpoint = kind === 'mp4' ? '/start_download_mp4' : '/start_download_mp3';
    try{
      const body = new URLSearchParams({url: videoUrl});
      const res = await fetch(endpoint, { method: 'POST', body: body });
      if(!res.ok){
        const err = await res.json().catch(()=>({error:'error'}));
        alert('Error al iniciar: ' + (err.error || 'Status ' + res.status));
        return;
      }
      const data = await res.json();
      const taskId = data.task_id;
      showOverlay();

      const es = new EventSource('/progress/' + taskId);
      es.onmessage = function(evt){
        try{
          const msg = JSON.parse(evt.data);
          if(msg.status === 'downloading'){
            setProgress(msg.percent || 0);
            document.getElementById('status-text').textContent = `Descargando... ${msg.percent || 0}%`;
          } else if(msg.status === 'started'){
            document.getElementById('status-text').textContent = msg.message || 'Iniciando...';
          } else if(msg.status === 'info'){
            document.getElementById('status-text').textContent = msg.message || '';
          } else if(msg.status === 'merging'){
            setProgress(100);
            document.getElementById('status-text').textContent = msg.message || 'Uniendo...';
          } else if(msg.status === 'finished'){
            setProgress(100);
            document.getElementById('status-text').textContent = msg.message || 'Finalizado';
            // cerramos EventSource y escondemos overlay tras 1.5s
            es.close();
            setTimeout(hideOverlay, 1500);
            alert(msg.message || 'Descarga completada');
          } else if(msg.status === 'error'){
            es.close();
            document.getElementById('status-text').textContent = 'Error: ' + (msg.message || '');
            alert('Error: ' + (msg.message || 'Error desconocido'));
            setTimeout(hideOverlay, 2000);
          }
        }catch(e){
          console.error('parse error', e, evt.data);
        }
      };

      es.onerror = function(e){
        console.error('EventSource error', e);
        // no alert inmediato; seguirá intentando hasta finalizar
      };

    }catch(err){
      console.error(err);
      alert('Error iniciando descarga. Revisa la consola.');
    }
  }

  // prevenir reenvío de POST al recargar la página (simple)
  if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
  }

    document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("footer-phrase");
    const text = el.textContent;
    el.textContent = "";
    let i = 0;

    function typeWriter() {
        if (i < text.length) {
        el.textContent += text.charAt(i);
        i++;
        setTimeout(typeWriter, 50);
        }
    }
    typeWriter();
     });

  /* ANIMACION DE DESTELLOS ROJOS Y BLANCO RANDOM */
      const bg = document.querySelector(".background");
      let flashInterval; // aquí guardamos el intervalo activo

      function createFlash() {
        const flash = document.createElement("div");
        flash.classList.add("flash");

        // tamaño aleatorio para variedad
        const size = 300 + Math.random() * 400; // entre 300 y 700 px
        flash.style.width = `${size}px`;
        flash.style.height = `${size}px`;

        // posición aleatoria dentro de la ventana
        const x = Math.random() * window.innerWidth;
        const y = Math.random() * window.innerHeight;

        flash.style.left = `${x - size/2}px`;
        flash.style.top = `${y - size/2}px`;

        bg.appendChild(flash);

        // eliminar después de la animación
        setTimeout(() => {
          flash.remove();
        }, 4000); // mismo tiempo que la animación
      }

      // ⏳ iniciar los destellos cada 2s
      function startFlashes() {
        flashInterval = setInterval(createFlash, 2000);
      }

      // observar el DOM por si aparece el <p>
      const observer = new MutationObserver(() => {
        const author = document.querySelector("#author");
        if (author) {
          stopFlashes(); // detenemos destellos
          observer.disconnect(); // dejamos de observar
        }
      });

      // 🛑 detener destellos al activar .flash.fade-out
      function stopFlashes() {
        if (flashInterval) {
          clearInterval(flashInterval); // detiene creación de destellos
          flashInterval = null;
        }

        // aplicar fade-out a todos los destellos en pantalla
        document.querySelectorAll(".flash").forEach(f => {
          f.classList.add("fade-out");
          setTimeout(() => f.remove(), 1000); // coincide con el transition
        });

        bg.classList.add("active"); // activa el ::before
      }

      // arrancamos los destellos al cargar
      startFlashes();

      // observar cambios en el body
      observer.observe(document.body, { childList: true, subtree: true });

      // PRUEBA ARREGLAR SUBMENU Y QUE CADA BOTON TENGA SU SUBMENU

      async function showQualityMenu() {
      const url = document.getElementById("video_url").value;
      const res = await fetch("/get_streams", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url})
      });
      const streams = await res.json();

      const menu = document.getElementById("qualityMenu");
      menu.innerHTML = "";
      menu.style.display = "block";

      streams.forEach(s => {
        const btn = document.createElement("button");
        if (s.type === "video") {
          btn.innerText = `🎥 ${s.resolution} @${s.fps || 30}fps (${s.size})`;
        } else {
          btn.innerText = `🎵 ${s.abr} (${s.size})`;
        }

        btn.onclick = async () => {
          const r = await fetch("/start_download", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url, itag: s.itag})
          });
          const {task_id} = await r.json();
          alert(`✅ Descarga iniciada (task: ${task_id})`);
        };

        menu.appendChild(btn);
      });
    } 
