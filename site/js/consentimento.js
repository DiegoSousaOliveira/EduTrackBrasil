// Banner de cookies e Consent Mode v2.
//
// O padrão (tudo "denied") e a reaplicação da escolha salva acontecem num <script> inline
// no <head>, ANTES do GTM — aqui só cuidamos do banner e das mudanças de escolha.
// Sinais de anúncio (ad_storage, ad_user_data, ad_personalization) ficam sempre negados:
// o site não faz publicidade.

import { track } from "./track.js";

// Mesma chave e versão lidas pelo script inline do <head> (index.html e privacidade.html)
const CHAVE = "edutrack_consentimento";
const VERSAO_POLITICA = 1; // subir quando a política mudar: o banner volta a aparecer para todos

export function lerEscolha() {
  try {
    const escolha = JSON.parse(localStorage.getItem(CHAVE));
    return escolha?.versao === VERSAO_POLITICA ? escolha : null;
  } catch {
    return null; // modo privado / armazenamento bloqueado: trata como "sem escolha"
  }
}

function salvarEscolha(valor) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ analytics_storage: valor, versao: VERSAO_POLITICA, data: new Date().toISOString() }));
  } catch {
    // sem armazenamento: a escolha vale só para esta página
  }
}

/** Ao revogar o consentimento, apaga os cookies do Google Analytics (_ga, _ga_XXXX) já gravados. */
function apagarCookiesAnalytics() {
  for (const cookie of document.cookie.split(";")) {
    const nome = cookie.split("=")[0].trim();
    if (!/^_ga(_|$)/.test(nome)) continue;
    for (const dominio of ["", `; domain=${location.hostname}`, `; domain=.${location.hostname}`]) {
      document.cookie = `${nome}=; Max-Age=0; path=/${dominio}`;
    }
  }
}

const TEXTO_ESCOLHA = { granted: "Você aceitou os cookies de análise.", denied: "Você recusou os cookies de análise." };

const HTML_BANNER = `
  <section id="banner-consentimento" class="consentimento" role="region" aria-labelledby="consentimento-titulo" hidden>
    <h2 id="consentimento-titulo">Sua privacidade</h2>
    <p>Usamos o Google Analytics para entender como o site é usado: quais cidades são buscadas, quais gráficos são vistos.
      Não usamos anúncios. Os cookies de análise só são gravados se você aceitar.
      <a href="privacidade.html">Política de privacidade</a></p>
    <p class="consentimento__atual" id="consentimento-atual" hidden></p>
    <div class="consentimento__acoes">
      <button type="button" class="botao" data-consentimento="granted">Aceitar</button>
      <button type="button" class="botao" data-consentimento="denied">Recusar</button>
    </div>
  </section>`;

let banner;

function mostrarBanner({ focar = false } = {}) {
  const escolha = lerEscolha();
  const atual = banner.querySelector("#consentimento-atual");
  atual.hidden = !escolha;
  atual.textContent = escolha ? `${TEXTO_ESCOLHA[escolha.analytics_storage]} Você pode mudar quando quiser.` : "";
  banner.hidden = false;
  // reserva espaço no fim da página para o banner fixo não cobrir o rodapé
  document.body.style.paddingBottom = `${banner.offsetHeight}px`;
  if (focar) banner.querySelector("button").focus();
}

function esconderBanner() {
  banner.hidden = true;
  document.body.style.paddingBottom = "";
}

function decidir(valor) {
  window.gtag("consent", "update", { analytics_storage: valor });
  salvarEscolha(valor);
  if (valor === "denied") apagarCookiesAnalytics();
  track("consent_update", { analytics_storage: valor }); // depois do update: o GTM já vê o novo estado
  esconderBanner();
}

export function iniciarConsentimento() {
  document.body.insertAdjacentHTML("beforeend", HTML_BANNER);
  banner = document.getElementById("banner-consentimento");
  banner.addEventListener("click", (ev) => {
    const botao = ev.target.closest("[data-consentimento]");
    if (botao) decidir(botao.dataset.consentimento);
  });
  // Link "Preferências de privacidade" do rodapé (em todas as páginas)
  document.querySelectorAll("[data-abrir-consentimento]").forEach((link) =>
    link.addEventListener("click", (ev) => {
      ev.preventDefault();
      mostrarBanner({ focar: true });
    }));
  if (!lerEscolha()) mostrarBanner();
}

iniciarConsentimento();
