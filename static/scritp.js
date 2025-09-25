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
