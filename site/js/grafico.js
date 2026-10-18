// Gráficos de linha (Chart.js via CDN, carregado como script global `Chart`).
// Anos sem dado chegam como null e viram lacuna (spanGaps: false), nunca zero.

import { escaparHtml, formatarNumero } from "./formato.js";

const graficos = new Map();

const cor = (nome) => getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
const ESTILOS = {
  municipio: { variavel: "--municipio", traco: [], largura: 3 },
  uf: { variavel: "--uf", traco: [6, 4], largura: 2 },
  brasil: { variavel: "--brasil", traco: [2, 3], largura: 2 },
};

// Plugin próprio: linha tracejada vertical em 2020 com o rótulo "pandemia"
const anotacao2020 = {
  id: "anotacao2020",
  afterDatasetsDraw(chart, _args, opcoes) {
    if (!opcoes?.ativo) return;
    const i = chart.data.labels.indexOf("2020");
    if (i < 0) return;
    const x = chart.scales.x.getPixelForValue(i);
    const { top, bottom, right } = chart.chartArea;
    const ctx = chart.ctx;
    ctx.save();
    ctx.strokeStyle = cor("--texto-suave");
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = cor("--texto-suave");
    ctx.font = "600 12px system-ui, sans-serif";
    const texto = "2020: pandemia";
    const cabe = x + 6 + ctx.measureText(texto).width < right;
    ctx.textAlign = cabe ? "left" : "right";
    ctx.fillText(texto, cabe ? x + 6 : x - 6, top - 8);
    ctx.restore();
  },
};

export const graficosDisponiveis = () => typeof window.Chart !== "undefined";

/**
 * Desenha ou atualiza um gráfico de linha.
 * series: [{ rotulo, valores, tipo: "municipio" | "uf" | "brasil" }]
 */
export function desenharLinha(canvas, { anos, series, sufixo = "", comecarEmZero = false, maximo, anotar2020 = false, descricao }) {
  canvas.setAttribute("aria-label", descricao);
  if (!graficosDisponiveis()) return;
  const reduzirMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const datasets = series.map((s) => {
    const estilo = ESTILOS[s.tipo];
    const c = cor(estilo.variavel);
    return {
      label: s.rotulo, data: s.valores, borderColor: c, backgroundColor: c,
      borderDash: estilo.traco, borderWidth: estilo.largura, pointRadius: s.tipo === "municipio" ? 3 : 0,
      pointHoverRadius: 5, spanGaps: false, tension: 0,
    };
  });
  const corTexto = cor("--texto-suave");
  const corGrade = cor("--borda");
  const opcoes = {
    responsive: true,
    maintainAspectRatio: false,
    animation: reduzirMovimento ? false : { duration: 400 },
    interaction: { mode: "index", intersect: false },
    layout: { padding: { top: anotar2020 ? 22 : 4 } },
    scales: {
      x: { ticks: { color: corTexto, maxRotation: 0, autoSkipPadding: 8 }, grid: { display: false } },
      y: {
        beginAtZero: comecarEmZero, max: maximo,
        ticks: { color: corTexto, callback: (v) => `${formatarNumero(v).replace(",0", "")}${sufixo}` },
        grid: { color: corGrade },
      },
    },
    plugins: {
      legend: { position: "bottom", labels: { color: corTexto, usePointStyle: true, pointStyle: "line", boxWidth: 28 } },
      tooltip: {
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y == null ? "sem dado" : formatarNumero(ctx.parsed.y) + sufixo}`,
        },
      },
      anotacao2020: { ativo: anotar2020 },
    },
  };
  const dados = { labels: anos.map(String), datasets };
  const existente = graficos.get(canvas);
  if (existente) {
    existente.data = dados;
    existente.options = opcoes;
    existente.update();
  } else {
    graficos.set(canvas, new window.Chart(canvas, { type: "line", data: dados, options: opcoes, plugins: [anotacao2020] }));
  }
}

/** Mesmos dados em tabela (alternativa acessível ao gráfico). */
export function tabela(container, { anos, series, sufixo = "" }) {
  const cab = `<tr><th scope="col">Ano</th>${series.map((s) => `<th scope="col">${escaparHtml(s.rotulo)}</th>`).join("")}</tr>`;
  const linhas = anos
    .map((ano, i) => `<tr><th scope="row">${ano}</th>${series
      .map((s) => `<td>${s.valores[i] == null ? "–" : formatarNumero(s.valores[i]) + sufixo}</td>`).join("")}</tr>`)
    .join("");
  container.innerHTML = `<table><thead>${cab}</thead><tbody>${linhas}</tbody></table>`;
}
