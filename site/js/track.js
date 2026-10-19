// Helper único de tracking: todo evento do site passa por track(evento, parametros).
//
// - Faz dataLayer.push com event_id (UUID v4) e schema_version (versão do contrato).
// - Envia TODOS os parâmetros conhecidos do contrato em todo push, com undefined nos que não
//   pertencem ao evento. O modelo de dados do GTM é persistente (guarda o último valor de cada
//   chave entre pushes) e a tag do GA4 envia todos os parâmetros mapeados em todo evento: sem
//   isso, um search_term antigo vazaria para um share. Com undefined, o GTM limpa o valor e o
//   GA4 descarta o parâmetro. Não depende do histórico: vale mesmo se alguém fizer push por fora.
// - Em ambiente local (ou com ?debug_tracking na URL) mostra cada push no console e valida
//   contra o contrato gerado de tracking/schema/events.schema.json.

import { PARAMETROS } from "./parametros-eventos.js";

export const SCHEMA_VERSION = "1.0.0";

window.dataLayer = window.dataLayer || [];

export const MODO_DEBUG =
  ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname) ||
  new URLSearchParams(location.search).has("debug_tracking");

// O contrato só é baixado em modo debug (não pesa para o visitante em produção).
const contratoPronto = MODO_DEBUG
  ? import("./contrato-eventos.js").then((m) => m.CONTRATO).catch((erro) => {
      console.warn("[track] contrato de eventos não carregou; pushes não serão validados.", erro);
      return null;
    })
  : Promise.resolve(null);

function novoUuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40; // versão 4
  b[8] = (b[8] & 0x3f) | 0x80; // variante RFC 4122
  const h = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

/** Objeto do push: todos os parâmetros conhecidos como undefined, sobrescritos pelos do evento. */
export function montarPush(evento, parametros = {}) {
  const push = { event: evento, event_id: novoUuid(), schema_version: SCHEMA_VERSION };
  for (const nome of PARAMETROS) push[nome] = undefined;
  return Object.assign(push, parametros);
}

/** Só as chaves com valor (para mostrar no console). */
const semIndefinidos = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined));

/** Envia um evento ao dataLayer. Retorna uma cópia do objeto enviado. */
export function track(evento, parametros = {}) {
  const push = montarPush(evento, parametros);
  const copia = { ...push }; // o GTM grava gtm.uniqueEventId no objeto recebido; validamos a cópia
  window.dataLayer.push(push);

  if (MODO_DEBUG) {
    console.info(`%c[track] ${evento}`, "color:#0f5e9c;font-weight:bold", semIndefinidos(copia));
    contratoPronto.then((contrato) => {
      if (!contrato) return;
      const erros = validar(copia, contrato);
      if (erros.length) console.warn(`[track] "${evento}" viola o contrato v${SCHEMA_VERSION}:`, erros, semIndefinidos(copia));
    });
  }
  return copia;
}

// ---------- Validação (subconjunto de JSON Schema usado no contrato) ----------

function resolver(no, contrato) {
  if (!no.$ref) return no;
  const { $ref, ...resto } = no;
  return { ...resolver(contrato.$defs[$ref.split("/").pop()], contrato), ...resto };
}

const TIPOS = {
  string: (v) => typeof v === "string",
  integer: (v) => Number.isInteger(v),
  number: (v) => typeof v === "number" && Number.isFinite(v),
  boolean: (v) => typeof v === "boolean",
};

/**
 * Lista de violações do payload (vazia = válido).
 * Chaves com valor undefined são ignoradas: é assim que track() limpa os parâmetros de outros eventos.
 */
export function validar(payload, contrato) {
  const definicao = contrato.oneOf
    .map((r) => contrato.$defs[r.$ref.split("/").pop()])
    .find((d) => d.properties.event.const === payload.event);
  if (!definicao) return [`evento "${payload.event}" não existe no contrato`];

  const erros = [];
  for (const chave of definicao.required) {
    if (payload[chave] === undefined) erros.push(`falta o parâmetro obrigatório "${chave}"`);
  }
  for (const [chave, valor] of Object.entries(payload)) {
    if (valor === undefined) continue;
    const no = definicao.properties[chave];
    if (!no) {
      erros.push(`parâmetro "${chave}" não está previsto para "${payload.event}"`);
      continue;
    }
    const regra = resolver(no, contrato);
    const mostrar = JSON.stringify(valor);
    if (regra.type && !TIPOS[regra.type](valor)) erros.push(`"${chave}" deveria ser ${regra.type}, veio ${mostrar}`);
    if ("const" in regra && valor !== regra.const) erros.push(`"${chave}" deveria ser "${regra.const}", veio ${mostrar}`);
    if (regra.enum && !regra.enum.includes(valor)) erros.push(`"${chave}" fora da lista permitida: ${mostrar}`);
    if (typeof valor === "string") {
      if (regra.pattern && !new RegExp(regra.pattern).test(valor)) erros.push(`"${chave}" não segue o formato ${regra.pattern}: ${mostrar}`);
      if (regra.maxLength && valor.length > regra.maxLength) erros.push(`"${chave}" passa de ${regra.maxLength} caracteres`);
      if (regra.minLength && valor.length < regra.minLength) erros.push(`"${chave}" está vazio`);
    }
    if (typeof valor === "number" && regra.minimum !== undefined && valor < regra.minimum) {
      erros.push(`"${chave}" menor que ${regra.minimum}: ${mostrar}`);
    }
  }
  return erros;
}
