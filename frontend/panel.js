/* Panel V2: gráfica de evolución, tarjetas con datos, último récord y confirmaciones propias.
   Extiende refresh(), renderProjects() y renderExperiments() de app.js sin modificarlas. */
const SVG = "http://www.w3.org/2000/svg";
const MENOR_ES_MEJOR = new Set(["RMSE", "MAE", "MSE", "MAPE", "LOSS", "LOG LOSS", "ERROR"]);
const tiempoRelativo = new Intl.RelativeTimeFormat("es", { numeric: "auto" });
const resumenOriginal = $(".stat-note").innerHTML;
let indicadores = new Map(), destacado = null;

const mayorEsMejor = (metrica) => !MENOR_ES_MEJOR.has(metrica.trim().toUpperCase());
const fechaUTC = (texto) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(texto) ? texto : `${texto}Z`);
const formatoValor = (valor) => valor.toLocaleString("es-MX", { maximumFractionDigits: Math.abs(valor) >= 10 ? 2 : 3 });
const formatoFecha = (texto) => fechaUTC(texto).toLocaleDateString("es-MX", { day: "numeric", month: "short" });

function hace(texto) {
  const dias = Math.round((fechaUTC(texto) - Date.now()) / 86400000);
  if (Math.abs(dias) < 1) {
    const horas = Math.round((fechaUTC(texto) - Date.now()) / 3600000);
    return horas === 0 ? "justo ahora" : tiempoRelativo.format(horas, "hour");
  }
  return Math.abs(dias) < 31 ? tiempoRelativo.format(dias, "day") : tiempoRelativo.format(Math.round(dias / 30), "month");
}

function nodo(tag, atributos = {}, padre) {
  const elemento = document.createElementNS(SVG, tag);
  for (const [nombre, valor] of Object.entries(atributos)) elemento.setAttribute(nombre, valor);
  if (padre) padre.append(elemento);
  return elemento;
}

/* ---------- 6. Confirmación propia en lugar de confirm() ---------- */
const dialogoConfirmar = document.createElement("dialog");
dialogoConfirmar.className = "confirmacion";
dialogoConfirmar.innerHTML = `<form method="dialog">
  <span class="confirmacion-icono" aria-hidden="true">✦</span>
  <h2 id="confirmacion-titulo">¿Seguro?</h2>
  <p class="confirmacion-texto"></p>
  <div class="dialog-footer"><button value="no" class="ghost" autofocus>Cancelar</button><button value="si" class="boton-peligro">Eliminar</button></div>
</form>`;
dialogoConfirmar.setAttribute("aria-labelledby", "confirmacion-titulo");
document.body.append(dialogoConfirmar);

function confirmar(mensaje) {
  dialogoConfirmar.querySelector(".confirmacion-texto").textContent = mensaje;
  dialogoConfirmar.returnValue = "";
  dialogoConfirmar.showModal();
  return new Promise((resolver) => {
    dialogoConfirmar.addEventListener("close", () => resolver(dialogoConfirmar.returnValue === "si"), { once: true });
  });
}

/* ---------- 2 y 3. Indicadores de proyectos y último récord ---------- */
async function cargarIndicadores() {
  try {
    const datos = await api("/insights");
    indicadores = new Map(datos.projects.map((proyecto) => [proyecto.id, proyecto]));
    destacado = datos.highlight;
  } catch (error) {
    indicadores = new Map(); destacado = null;
  }
  decorarTarjetas();
  pintarResumen();
}

function decorarTarjetas() {
  const tarjetas = document.querySelectorAll("#project-list .project-card");
  projects.forEach((proyecto, indice) => {
    const datos = indicadores.get(proyecto.id), tarjeta = tarjetas[indice];
    if (!datos || !tarjeta || tarjeta.querySelector(".tarjeta-datos")) return;
    const linea = document.createElement("span");
    linea.className = "tarjeta-datos";
    if (!datos.experiments) {
      linea.textContent = "Sin experimentos todavía";
    } else {
      const mejor = datos.best;
      linea.append(
        element("span", `${datos.experiments} exp.`),
        element("span", `★ ${formatoValor(mejor.metric_value)} ${mejor.metric_name}`, "tarjeta-mejor"),
        element("span", hace(datos.last_activity)),
      );
    }
    tarjeta.append(linea);
  });
}

function pintarResumen() {
  const caja = $(".stat-note");
  if (!destacado) { caja.innerHTML = resumenOriginal; caja.classList.remove("con-record"); return; }
  caja.classList.add("con-record");
  const valor = element("strong", formatoValor(destacado.metric_value), "resumen-valor");
  valor.append(element("small", ` ${destacado.metric_name}`));
  const ir = element("button", `${destacado.project_name} →`, "resumen-proyecto");
  ir.type = "button";
  ir.title = "Abrir el proyecto";
  ir.addEventListener("click", async () => {
    selectedId = destacado.project_id;
    $("#model-filter").value = "";
    renderProjects();
    try { await loadExperiments(); } catch (error) { notify(error.message); }
  });
  caja.replaceChildren(
    element("span", "Último récord", "resumen-etiqueta"),
    valor,
    element("span", `${destacado.name} · ${hace(destacado.created_at)}`, "resumen-detalle"),
    ir,
  );
}

/* ---------- 1. Gráfica de evolución de la métrica ---------- */
const evolucion = document.createElement("section");
evolucion.className = "evolucion";
evolucion.hidden = true;
evolucion.setAttribute("aria-label", "Evolución de la métrica");
$("#experiment-tools").before(evolucion);

function dibujarEvolucion() {
  const lista = [...experiments].sort((a, b) => fechaUTC(a.created_at) - fechaUTC(b.created_at));
  const conteo = new Map();
  lista.forEach((e) => conteo.set(e.metric_name, (conteo.get(e.metric_name) || 0) + 1));
  const metrica = [...conteo.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  const puntos = lista.filter((e) => e.metric_name === metrica);
  evolucion.hidden = puntos.length < 2;
  if (evolucion.hidden) return;

  const subeEsMejor = mayorEsMejor(metrica);
  const mejor = puntos.reduce((a, b) => ((subeEsMejor ? b.metric_value > a.metric_value : b.metric_value < a.metric_value) ? b : a));
  const ancho = Math.max(evolucion.clientWidth || 0, 320), alto = 170;
  const margen = { izq: 46, der: 18, arriba: 30, abajo: 26 };
  const valores = puntos.map((e) => e.metric_value);
  let min = Math.min(...valores), max = Math.max(...valores);
  const holgura = (max - min || Math.abs(max) || 1) * 0.18;
  min -= holgura; max += holgura;
  const x = (i) => margen.izq + (i * (ancho - margen.izq - margen.der)) / (puntos.length - 1);
  const y = (v) => margen.arriba + ((max - v) * (alto - margen.arriba - margen.abajo)) / (max - min);

  const svg = nodo("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho, height: alto, role: "img",
    "aria-label": `Evolución de ${metrica} en ${puntos.length} experimentos; mejor ${formatoValor(mejor.metric_value)}` });
  const defs = nodo("defs", {}, svg);
  const relleno = nodo("linearGradient", { id: "evolucion-relleno", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  nodo("stop", { offset: "0%", "stop-color": "#9d8fd0", "stop-opacity": 0.35 }, relleno);
  nodo("stop", { offset: "100%", "stop-color": "#e9ddf5", "stop-opacity": 0 }, relleno);
  const trazo = nodo("linearGradient", { id: "evolucion-trazo", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
  nodo("stop", { offset: "0%", "stop-color": "#5b68ae" }, trazo);
  nodo("stop", { offset: "100%", "stop-color": "#7a62a6" }, trazo);

  for (let i = 0; i <= 2; i++) {
    const v = min + holgura + ((max - min - 2 * holgura) * i) / 2;
    nodo("line", { x1: margen.izq, x2: ancho - margen.der, y1: y(v), y2: y(v), class: "evolucion-guia" }, svg);
    nodo("text", { x: margen.izq - 8, y: y(v) + 4, class: "evolucion-eje", "text-anchor": "end" }, svg).textContent = formatoValor(v);
  }
  const linea = puntos.map((e, i) => `${x(i)},${y(e.metric_value)}`).join(" L");
  nodo("path", { d: `M${linea} L${x(puntos.length - 1)},${alto - margen.abajo} L${x(0)},${alto - margen.abajo} Z`, fill: "url(#evolucion-relleno)" }, svg);
  nodo("path", { d: `M${linea}`, class: "evolucion-linea", stroke: "url(#evolucion-trazo)" }, svg);

  puntos.forEach((e, i) => {
    const esMejor = e === mejor;
    const punto = nodo("circle", { cx: x(i), cy: y(e.metric_value), r: esMejor ? 6.5 : 4, class: esMejor ? "evolucion-punto mejor" : "evolucion-punto" }, svg);
    nodo("title", {}, punto).textContent = `${e.name} — ${e.model} · ${formatoValor(e.metric_value)} ${metrica} · ${formatoFecha(e.created_at)}`;
  });
  const etiquetaX = Math.min(Math.max(x(puntos.indexOf(mejor)), margen.izq + 40), ancho - margen.der - 40);
  nodo("text", { x: etiquetaX, y: y(mejor.metric_value) - 13, class: "evolucion-mejor", "text-anchor": "middle" }, svg)
    .textContent = `★ ${formatoValor(mejor.metric_value)}`;
  nodo("text", { x: x(0), y: alto - 6, class: "evolucion-eje", "text-anchor": "start" }, svg).textContent = formatoFecha(puntos[0].created_at);
  nodo("text", { x: x(puntos.length - 1), y: alto - 6, class: "evolucion-eje", "text-anchor": "end" }, svg)
    .textContent = formatoFecha(puntos.at(-1).created_at);

  const encabezado = document.createElement("div");
  encabezado.className = "evolucion-encabezado";
  encabezado.append(
    element("strong", `Evolución de ${metrica}`),
    element("span", `${puntos.length} experimentos · ${subeEsMejor ? "mayor es mejor" : "menor es mejor"}`),
  );
  evolucion.replaceChildren(encabezado, svg);
}

/* ---------- Enganche con app.js ---------- */
const refreshBase = refresh, renderProjectsBase = renderProjects, renderExperimentsBase = renderExperiments;
refresh = async function () { await refreshBase(); await cargarIndicadores(); };
renderProjects = function () { renderProjectsBase(); decorarTarjetas(); };
renderExperiments = function () { renderExperimentsBase(); dibujarEvolucion(); };
new ResizeObserver(() => { if (!evolucion.hidden) dibujarEvolucion(); }).observe($(".experiments-panel"));
if (!$("#workspace").hidden) { cargarIndicadores(); dibujarEvolucion(); }
