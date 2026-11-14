"use strict";

/* ============================================================
   TecNet Finder · Vista previa y demo de navegador
   El ejemplo web NO ejecuta el compilador Python de escritorio.
   ============================================================ */

(function () {
  const EXAMPLE = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina";
  const MAX_INPUT = 500;
  const SLIDES = [
    {
      title: "Editor del lenguaje de redes",
      subtitle: "Entrada, reconocimiento y asistencia de escritura",
      content: `
        <div class="tnf-mock-tabs"><span class="is-current">Entrada / Salida</span><span>Tablas</span><span>Sintaxis</span></div>
        <div class="tnf-mock-editor"><span class="tnf-mock-line">1</span><code><em>IP</em> 192.168.1.0 <b>MASK</b> /24 <strong>HOSTS</strong> 50,30,10 <i>NAME</i> Oficina</code></div>
        <div class="tnf-mock-action">▶ Compilar <span>Exportar reporte</span></div>
        <div class="tnf-mock-stats"><span>Tokens reconocidos<br><b>12</b></span><span>Errores léxicos<br><b>0</b></span><span>Errores semánticos<br><b>0</b></span></div>
      `,
    },
    {
      title: "Resultados de planificación VLSM",
      subtitle: "Tabla de subredes calculadas para la instrucción",
      content: `
        <div class="tnf-mock-tabs"><span>Resumen</span><span class="is-current">Tabla VLSM</span><span>Errores / Advertencias</span></div>
        <div class="tnf-mock-table-wrap"><table><thead><tr><th>Hosts</th><th>Subred</th><th>Máscara</th><th>Hosts útiles</th></tr></thead><tbody><tr><td>50</td><td>192.168.1.0</td><td>/26</td><td>62</td></tr><tr><td>30</td><td>192.168.1.64</td><td>/27</td><td>30</td></tr><tr><td>10</td><td>192.168.1.96</td><td>/28</td><td>14</td></tr></tbody></table></div>
        <p class="tnf-mock-note">Representación ilustrativa basada en el ejemplo de entrada.</p>
      `,
    },
    {
      title: "Configuración y mantenimiento",
      subtitle: "Preferencias, registros e idiomas de la interfaz",
      content: `
        <div class="tnf-mock-settings"><aside>Ventana y apariencia<br>Editor<br>Resultados y navegación<br>Asistencia de IA<br><b>Datos y preferencias</b></aside><div><strong>Datos y preferencias</strong><p>Administra la configuración personal de TecNet Finder.</p><div class="tnf-mock-setting-card">Restaurar valores predeterminados<br><small>Con respaldo previo y confirmación</small></div><div class="tnf-mock-setting-card">Exportar / importar preferencias<br><small>Archivos JSON locales y validación</small></div></div></div>
      `,
    },
  ];

  const toNumber = (value) => Number(value);

  function ipToNumber(text) {
    const parts = text.split(".");
    if (parts.length !== 4 || parts.some((part) => !/^\d{1,3}$/.test(part) || Number(part) > 255)) throw new Error("La dirección IP debe contener cuatro octetos entre 0 y 255.");
    return parts.reduce((total, part) => total * 256 + Number(part), 0);
  }

  function numberToIp(value) {
    return [24, 16, 8, 0].map((shift) => Math.floor(value / 2 ** shift) % 256).join(".");
  }

  function parseInstruction(text) {
    if (text.length > MAX_INPUT) throw new Error("La demo admite instrucciones de hasta 500 caracteres.");
    const expression = /^\s*IP\s+(\d{1,3}(?:\.\d{1,3}){3})\s+MASK\s+\/(\d{1,2})\s+HOSTS\s+(\d+(?:\s*,\s*\d+)*)\s*(?:NAME\s+([A-Za-z_][A-Za-z0-9_]*))?\s*$/;
    const match = text.match(expression);
    if (!match) throw new Error("Formato esperado: IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina");
    const ip = match[1];
    const prefix = Number(match[2]);
    const hosts = match[3].split(",").map((value) => Number(value.trim()));
    if (prefix > 30) throw new Error("La demo admite máscaras de /0 a /30 para redes con hosts útiles.");
    if (hosts.length > 20 || hosts.some((value) => !Number.isSafeInteger(value) || value < 1 || value > 2 ** 31 - 2)) throw new Error("Indica entre 1 y 20 cantidades de hosts válidas, mayores que cero.");
    return { ip, base: ipToNumber(ip), prefix, hosts, name: match[4] || "Sin nombre" };
  }

  function calculateSubnets(instruction) {
    const { base, prefix, hosts } = instruction;
    const rangeSize = 2 ** (32 - prefix);
    const rangeStart = Math.floor(base / rangeSize) * rangeSize;
    if (rangeStart !== base) throw new Error("La IP debe ser la dirección de red para la máscara base indicada.");
    const rangeEnd = rangeStart + rangeSize;
    const ordered = hosts.map((requested, index) => ({ requested, index })).sort((a, b) => b.requested - a.requested || a.index - b.index);
    let current = rangeStart;
    const rows = [];
    for (const entry of ordered) {
      const bits = Math.max(2, Math.ceil(Math.log2(entry.requested + 2)));
      const size = 2 ** bits;
      const blockStart = Math.ceil(current / size) * size;
      if (blockStart + size > rangeEnd) throw new Error("La red base no tiene espacio suficiente para las cantidades de hosts solicitadas.");
      const subnetPrefix = 32 - bits;
      rows.push({ requested: entry.requested, subnet: `${numberToIp(blockStart)}/${subnetPrefix}`, mask: numberToIp(2 ** 32 - size), first: numberToIp(blockStart + 1), last: numberToIp(blockStart + size - 2), broadcast: numberToIp(blockStart + size - 1), usable: size - 2 });
      current = blockStart + size;
    }
    return rows;
  }

  function markup() {
    return `
      <div class="tnf-showcase-intro">
        <span class="section-kicker">Vista previa de escritorio</span>
        <h2>Explora TecNet Finder</h2>
        <p>Conoce el editor, los resultados y la configuración de la v1.2.2. Luego prueba una demostración de cálculo VLSM sin instalar nada.</p>
      </div>
      <div class="tnf-showcase-grid">
        <article class="tnf-showcase-card">
          <header class="tnf-showcase-card-header"><div><span class="section-kicker">Slideshow</span><h3>La aplicación por dentro</h3><p>Vistas ilustrativas de sus principales áreas.</p></div><span class="tnf-showcase-pill">3 vistas</span></header>
          <div class="tnf-showcase-stage" id="tnfSlideStage" aria-label="Vista previa de TecNet Finder">
            ${SLIDES.map((slide, index) => `
              <div class="tnf-showcase-slide${index === 0 ? " is-active" : ""}" data-tnf-slide="${index}" aria-hidden="${index !== 0}">
                <div class="tnf-mock-window"><div class="tnf-mock-title">◉ TecNet Finder <span>− &nbsp; □ &nbsp; ×</span></div><div class="tnf-mock-body"><div class="tnf-mock-heading">${slide.title}<small>${slide.subtitle}</small></div>${slide.content}</div></div>
                <p class="tnf-showcase-caption">${slide.title}</p>
              </div>
            `).join("")}
          </div>
          <div class="tnf-showcase-controls" aria-label="Cambiar vista previa"><button type="button" id="tnfPrevSlide" aria-label="Vista anterior">←</button>${SLIDES.map((_, index) => `<button type="button" data-tnf-dot="${index}" class="tnf-showcase-dot${index === 0 ? " is-active" : ""}" aria-label="Ver vista ${index + 1}" aria-current="${index === 0 ? "true" : "false"}"></button>`).join("")}<button type="button" id="tnfNextSlide" aria-label="Vista siguiente">→</button></div>
        </article>
        <article class="tnf-showcase-card tnf-demo-card">
          <header class="tnf-showcase-card-header"><div><span class="section-kicker">Demo web</span><h3>Prueba un cálculo VLSM</h3><p>Escribe una instrucción del DSL y consulta un resultado ilustrativo.</p></div><span class="tnf-showcase-pill">En navegador</span></header>
          <label for="tnfDemoInput">Instrucción de entrada</label>
          <textarea id="tnfDemoInput" spellcheck="false" rows="4" maxlength="500">${EXAMPLE}</textarea>
          <div class="tnf-demo-actions"><button type="button" class="tnf-demo-primary" id="tnfDemoRun">Analizar ejemplo</button><button type="button" id="tnfDemoReset">Restaurar ejemplo</button></div>
          <p id="tnfDemoStatus" class="tnf-demo-status" role="status" aria-live="polite">Preparado para calcular las subredes del ejemplo.</p>
          <div id="tnfDemoOutput" class="tnf-demo-output" aria-live="polite"></div>
          <p class="tnf-demo-notice"><strong>Alcance:</strong> esta demo reproduce un cálculo VLSM básico en JavaScript. No ejecuta el lexer, parser, análisis semántico, asistente de IA ni exportadores de la aplicación de escritorio. La instrucción no se envía a servidores.</p>
        </article>
      </div>
    `;
  }

  function attachSlideshow(section) {
    const slides = Array.from(section.querySelectorAll("[data-tnf-slide]"));
    const dots = Array.from(section.querySelectorAll("[data-tnf-dot]"));
    const stage = section.querySelector("#tnfSlideStage");
    const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let selected = 0;
    let interval = null;
    function select(index) {
      selected = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.classList.toggle("is-active", i === selected); slide.setAttribute("aria-hidden", String(i !== selected)); });
      dots.forEach((dot, i) => { dot.classList.toggle("is-active", i === selected); dot.setAttribute("aria-current", String(i === selected)); });
    }
    const stop = () => { if (interval) clearInterval(interval); interval = null; };
    const start = () => { if (!reduceMotion && !document.hidden && !interval) interval = setInterval(() => select(selected + 1), 7500); };
    section.querySelector("#tnfPrevSlide").addEventListener("click", () => { select(selected - 1); stop(); start(); });
    section.querySelector("#tnfNextSlide").addEventListener("click", () => { select(selected + 1); stop(); start(); });
    dots.forEach((dot, index) => dot.addEventListener("click", () => { select(index); stop(); start(); }));
    stage.addEventListener("mouseenter", stop);
    stage.addEventListener("mouseleave", start);
    stage.addEventListener("focusin", stop);
    stage.addEventListener("focusout", start);
    document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());
    start();
  }

  function attachDemo(section) {
    const input = section.querySelector("#tnfDemoInput");
    const output = section.querySelector("#tnfDemoOutput");
    const status = section.querySelector("#tnfDemoStatus");
    function run() {
      output.replaceChildren();
      try {
        const instruction = parseInstruction(input.value);
        const rows = calculateSubnets(instruction);
        const summary = document.createElement("p");
        summary.className = "tnf-demo-summary";
        summary.textContent = `${instruction.name} · Red ${instruction.ip}/${instruction.prefix} · ${rows.length} subred(es)`;
        const scroll = document.createElement("div");
        scroll.className = "tnf-demo-table-scroll";
        const table = document.createElement("table");
        const head = document.createElement("thead");
        const header = document.createElement("tr");
        ["Hosts", "Subred", "Máscara", "Rango útil", "Broadcast"].forEach((label) => { const cell = document.createElement("th"); cell.textContent = label; header.append(cell); });
        head.append(header);
        const body = document.createElement("tbody");
        rows.forEach((row) => {
          const tr = document.createElement("tr");
          [String(row.requested), row.subnet, row.mask, `${row.first} – ${row.last}`, row.broadcast].forEach((value) => { const cell = document.createElement("td"); cell.textContent = value; tr.append(cell); });
          body.append(tr);
        });
        table.append(head, body);
        scroll.append(table);
        output.append(summary, scroll);
        status.textContent = "Cálculo ilustrativo completado. No se han enviado datos a servidores.";
        status.classList.remove("is-error");
      } catch (error) {
        status.textContent = error instanceof Error ? error.message : "No fue posible procesar la instrucción.";
        status.classList.add("is-error");
      }
    }
    section.querySelector("#tnfDemoRun").addEventListener("click", run);
    section.querySelector("#tnfDemoReset").addEventListener("click", () => { input.value = EXAMPLE; run(); });
    input.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); run(); } });
    run();
  }

  function install() {
    if (document.querySelector("#tecnet-showcase")) return true;
    const hero = document.querySelector("main > .hero");
    if (!hero) return false;
    const section = document.createElement("section");
    section.id = "tecnet-showcase";
    section.className = "tecnet-showcase";
    section.innerHTML = markup();
    hero.insertAdjacentElement("afterend", section);
    const nav = document.querySelector(".site-nav");
    if (nav && !nav.querySelector('a[href="#tecnet-showcase"]')) {
      const anchor = document.createElement("a");
      anchor.href = "#tecnet-showcase";
      anchor.textContent = "Demo";
      nav.prepend(anchor);
    }
    attachSlideshow(section);
    attachDemo(section);
    return true;
  }

  function boot() {
    if (install()) return;
    const root = document.querySelector("#projectPageRoot");
    if (!root) return;
    const observer = new MutationObserver(() => { if (install()) observer.disconnect(); });
    observer.observe(root, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
