"""Toda página HTML do site precisa de Consent Mode v2 antes do GTM, noscript do GTM e acesso ao banner."""
import re

import pytest

from tracking.gerar import RAIZ

GTM_ID = "GTM-K8NTDB7L"
SITE = RAIZ / "site"
PAGINAS = sorted(SITE.glob("*.html"))
CONSENT_DEFAULT = ("gtag('consent','default',{ad_storage:'denied',analytics_storage:'denied',"
                   "ad_user_data:'denied',ad_personalization:'denied',wait_for_update:500});")


def test_existem_paginas():
    assert {p.name for p in PAGINAS} >= {"index.html", "privacidade.html"}


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_consent_mode_antes_do_gtm_no_head(pagina):
    html = pagina.read_text(encoding="utf-8")
    head = html[:html.index("</head>")]
    assert CONSENT_DEFAULT in head
    assert f"'dataLayer','{GTM_ID}')" in head, "snippet do GTM ausente ou com outro ID"
    assert head.index(CONSENT_DEFAULT) < head.index("googletagmanager.com/gtm.js"), "consent default precisa vir antes do GTM"
    assert head.index("window.dataLayer = window.dataLayer || []") < head.index(CONSENT_DEFAULT)


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_noscript_logo_apos_body(pagina):
    html = pagina.read_text(encoding="utf-8")
    assert re.search(r"<body>\s*(<!--[^>]*-->\s*)?<noscript><iframe src=\"https://www\.googletagmanager\.com/ns\.html\?id="
                     + GTM_ID + '"', html), "noscript do GTM deve ser o primeiro elemento do <body>"


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_banner_e_preferencias(pagina):
    html = pagina.read_text(encoding="utf-8")
    assert 'src="js/consentimento.js"' in html
    rodape = html[html.index('<footer'):html.index('</footer>')]
    assert "data-abrir-consentimento" in rodape and "Preferências de privacidade" in rodape
    assert 'href="privacidade.html"' in rodape
    assert "entra AQUI" not in html  # marcadores antigos removidos


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.name)
def test_caminhos_relativos(pagina):
    html = pagina.read_text(encoding="utf-8")
    absolutos = [r for r in re.findall(r'(?:href|src)="([^"]+)"', html) if r.startswith("/")]
    assert not absolutos, f"caminhos absolutos quebram em usuario.github.io/repo/: {absolutos}"


def test_chave_e_versao_do_consentimento_batem_com_o_js():
    js = (SITE / "js" / "consentimento.js").read_text(encoding="utf-8")
    chave = re.search(r'const CHAVE = "([^"]+)"', js).group(1)
    versao = re.search(r"const VERSAO_POLITICA = (\d+)", js).group(1)
    for pagina in PAGINAS:
        html = pagina.read_text(encoding="utf-8")
        assert f"localStorage.getItem('{chave}')" in html, pagina.name
        assert f"escolha.versao === {versao}" in html, pagina.name
