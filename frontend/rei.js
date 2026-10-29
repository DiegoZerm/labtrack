/* Easter egg: escribe "rei" (fuera de los campos de texto) o haz 5 clics en el pie del acceso.
   Muestra cuatro stickers decorativos; Esc o volver a escribir "rei" los guarda. */
(function () {
  const STICKERS = ["mariposa", "varita", "rosa", "pollito"];
  const PALABRA = "rei";
  let escrito = "", capa = null, clics = [];

  function mostrar() {
    capa = document.createElement("div");
    capa.className = "rei-capa";
    capa.setAttribute("aria-hidden", "true");
    STICKERS.forEach((nombre, indice) => {
      const imagen = document.createElement("img");
      imagen.src = `/static/rei/${nombre}.svg`;
      imagen.alt = "";
      imagen.className = `rei-sticker rei-${nombre}`;
      imagen.style.setProperty("--retraso", `${indice * 140}ms`);
      capa.append(imagen);
    });
    for (let i = 0; i < 12; i++) {
      const chispa = document.createElement("span");
      chispa.className = "rei-chispa";
      chispa.textContent = i % 2 ? "✧" : "✦";
      chispa.style.setProperty("--angulo", `${i * 30}deg`);
      capa.append(chispa);
    }
    document.body.append(capa);
  }

  function ocultar() {
    capa.classList.add("rei-saliendo");
    const anterior = capa;
    capa = null;
    setTimeout(() => anterior.remove(), 400);
  }

  const alternar = () => (capa ? ocultar() : mostrar());

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && capa) { ocultar(); return; }
    const objetivo = event.target;
    if (objetivo.closest("input, textarea, select, [contenteditable]") || event.key.length !== 1) return;
    escrito = (escrito + event.key.toLowerCase()).slice(-PALABRA.length);
    if (escrito === PALABRA) { escrito = ""; alternar(); }
  });

  document.addEventListener("DOMContentLoaded", () => {
    const pie = document.querySelector(".login-pie");
    if (!pie) return;
    pie.addEventListener("click", () => {
      const ahora = Date.now();
      clics = [...clics.filter((tiempo) => ahora - tiempo < 2000), ahora];
      if (clics.length >= 5) { clics = []; alternar(); }
    });
  });
})();
