 if (performance.navigation.type === 1) {
        // Si se recarga la página, redirige al inicio
        window.location.href = "/";
    }

    //ANIMACION MAQUINA DE ESCRIBIR 
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
  
  // UPDATE

  // === Variables globales para animación de puntos ===
let dotsInterval = null;
let dotCount = 0;

function startDotsAnimation() {
  const dots = document.getElementById("dots");
  dotCount = 0;
  dots.textContent = "";
  clearInterval(dotsInterval);

  dotsInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4; // Repite 0, 1, 2, 3
    dots.textContent = ".".repeat(dotCount);
  }, 500); // velocidad del bucle
}

function stopDotsAnimation() {
  clearInterval(dotsInterval);
  document.getElementById("dots").textContent = ""; // Limpia los puntos
}

// === Barra de progreso + animación ===
let intervalo; // Declara fuera de la función (variable global o de nivel superior)
let progresoActivo = false;

  function iniciarProgreso() {
  if (progresoActivo) return; // 👈 evita duplicados
  progresoActivo = true;
  const contenedor = document.getElementById('progress-container');
  const barra = document.getElementById('progress-bar');
  const velocidad = document.getElementById('progress-speed');

  contenedor.style.display = 'block';
  startDotsAnimation(); // 👈 inicia los puntos

  const intervalo = setInterval(() => {
    fetch('/progress')
      .then(r => r.json())
      .then(data => {
        barra.style.width = data.percent + '%';
        barra.textContent = data.percent + '%';

        // Mostrar velocidad en MB/s
        const speedMB = (data.speed).toFixed(2);
        velocidad.textContent = `Velocidad: ${speedMB} MB/s`;

        if (data.status === 'done') {
          stopDotsAnimation(); // 👈 detener puntos
          clearInterval(intervalo);
          progresoActivo = false; // 👈 libera para la próxima vez
          barra.style.backgroundColor = '#2196F3';
          barra.textContent = 'Completado ✅';          

          // 🕒 Esperar 2 segundos y reiniciar la barra suavemente
          setTimeout(() => {
            barra.style.transition = 'width 1s ease, opacity 0.5s ease';
            barra.style.opacity = '0'; // Desaparece suavemente
            setTimeout(() => {
              barra.style.width = '0%';
              barra.textContent = '';
              barra.style.opacity = '1'; // La vuelve visible lista para el siguiente proceso
              barra.style.backgroundColor = '#4CAF50'; // Color original (opcional)
              contenedor.style.display = 'none'; // 👈 Oculta contenedor
            }, 1500);
          }, 2000);
        }
      if (data.status === 'error') {
          stopDotsAnimation();
          clearInterval(intervalo);
          barra.style.backgroundColor = '#f44336';
          barra.textContent = 'Error ❌';
        }
      })
      .catch(() => clearInterval(intervalo));
  }, 1000);
}

fetch(`/progress?_=${Date.now()}`)

if (data.status === 'done') {
  barra.style.backgroundColor = '#2196F3';
  barra.textContent = 'Completado';
  clearInterval(intervalo);
  setTimeout(() => {
    location.reload(); // 🔄 recarga la página después de 2 segundos
  }, 2000);
}

