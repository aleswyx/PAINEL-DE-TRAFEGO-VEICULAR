#!/usr/bin/env python3
"""Gera o painel do TCC (abas Visão geral, Contagens, Erro da contagem, Simulação e Documentos) como uma página index.html.

Uso:
    python gerar_painel.py          # cria/atualiza index.html na mesma pasta

Só usa a biblioteca padrão do Python. Para atualizar o painel, edite a lista
CONTAGENS (e, se mudar, os PARAMETROS), rode o script de novo e envie o
index.html para o GitHub.
"""
from html import escape
from pathlib import Path

# --------------------------------------------------------------------------
# DADOS: (dia, dia da semana, bloco, automóveis, motos, pesados)
# Use None nos três números de um bloco que ainda não foi contado.
# Pesados = ônibus + caminhões.
# --------------------------------------------------------------------------
CONTAGENS = [
    ("27/10", "Terça",  "17:30–17:45", 735, 311, 14),
    ("27/10", "Terça",  "17:45–18:00", 509, 247, 10),
    ("27/10", "Terça",  "18:00–18:15", 581, 230, 16),
    ("27/10", "Terça",  "18:15–18:30", 871, 417, 14),
    ("28/10", "Quarta", "17:30–17:45", 576, 232, 9),
    ("28/10", "Quarta", "17:45–18:00", 917, 364, 22),
    ("28/10", "Quarta", "18:00–18:15", 1047, 413, 12),
    ("28/10", "Quarta", "18:15–18:30", 978, 415, 24),
    ("29/10", "Quinta", "17:30–17:45", 823, 314, 13),
    ("29/10", "Quinta", "17:45–18:00", 840, 305, 10),
    ("29/10", "Quinta", "18:00–18:15", 852, 364, 9),
    ("29/10", "Quinta", "18:15–18:30", 886, 319, 11),
]

# --------------------------------------------------------------------------
# PARÂMETROS (valores provisórios: ver a nota no rodapé do painel)
# --------------------------------------------------------------------------
PARAMETROS = {
    "ciclo": 148,        # s
    "verde": 125,        # s
    "amarelo": 3,        # s
    "vermelho": 20,      # s
    "perda_inicial": 4,  # s, tempo perdido por ciclo (tp)
    "faixas": 3,
    "fluxo_saturacao": 1900,  # UCP/h/faixa (valor-base do HCM, provisório)
    "fator_moto_menor": 0.33,  # provisório
    "fator_moto_maior": 0.50,  # cenário de sensibilidade
    "fator_pesados": 2.0,      # HCM, E_T = 2,0 (confirmar a edição)
}
LIM_ALERTA = 0.85  # X a partir daqui: alerta (laranja)
LIM_SATURA = 1.00  # X acima daqui: saturado (vermelho)

TITULO = "Painel do TCC: Avenida Carlos Cunha, sentido Centro"
SUBTITULO = ("Contagem classificada por vídeo, blocos de 15 min, 17:30–18:30, "
             "referência no cruzamento do São Luís Shopping")


# --------------------------------------------------------------------------
# DOCUMENTOS: fichas da contagem manual, escaneadas em PDF (pasta documentos/)
# (dia, dia da semana, arquivo). Cada PDF tem uma página por bloco de 15 min.
# --------------------------------------------------------------------------
DOCUMENTOS = [
    ("27/10", "Terça", "documentos/Contagem dia 27 de outubro.pdf"),
    ("28/10", "Quarta", "documentos/Contagem dia 28 de outubro.pdf"),
    ("29/10", "Quinta", "documentos/Contagem dia 29 de outubro.pdf"),
]
LOCAL = "Avenida Prof. Carlos Cunha, sentido Centro"
PESQUISADOR = "Alessandro França Ramos"


def secao_documentos():
    """Aba Documentos: lista das fichas escaneadas e visualizador do PDF."""
    from urllib.parse import quote
    itens = []
    for i, (dia, sem, arq) in enumerate(DOCUMENTOS):
        url = escape(quote(arq))
        tit = f"Contagem de {dia} ({sem.lower()})"
        blocos = [r for r in CONTAGENS if r[0] == dia]
        total = sum(c + m + h for _, _, _, c, m, h in blocos if c is not None)
        meta = f"{len(blocos)} blocos de 15 min"
        if blocos:
            meta += f", {blocos[0][2][:5]}–{blocos[-1][2][-5:]}"
        if total:
            meta += f" · {fmt(total)} veículos"
        itens.append(
            f'<li class="doc"><div><div class="doc-t">{escape(tit)}</div><div class="doc-m">{meta}</div></div>'
            f'<div class="doc-a"><button class="btn" data-doc="{url}" data-t="{escape(tit)}" '
            f'aria-pressed="{"true" if i == 0 else "false"}">Ver aqui</button>'
            f'<a class="btn" href="{url}" target="_blank" rel="noopener">Abrir</a>'
            f'<a class="btn" href="{url}" download>Baixar</a></div></li>')
    return f"""
<div class="card"><h2>Fichas da contagem manual</h2>
<p class="cap">Fichas preenchidas à mão durante a contagem pelos vídeos, escaneadas em PDF. Cada página é um bloco de 15 minutos, com local, pesquisador, data, horário do bloco e a marcação de cada veículo (automóveis, motos e pesados).</p>
<div class="meta"><div><b>Local</b>{escape(LOCAL)}</div><div><b>Pesquisador</b>{escape(PESQUISADOR)}</div></div>
<ul class="docs">{"".join(itens)}</ul></div>
<div class="card"><h2 id="doc-tit">Visualização</h2>
<p class="cap">Se o PDF não aparecer abaixo (comum no celular), use Abrir ou Baixar.</p>
<iframe class="viewer" id="doc-view" title="Ficha de contagem em PDF"></iframe></div>
"""

# --------------------------------------------------------------------------
# SIMULAÇÃO NO VISSIM (dia 28/10, sentido Centro, só a faixa marcada no modelo)
# (cenário, verde SG2 em s, bloco, demanda em veíc./h, fila média em m, fila máxima em m,
#  paradas na fila, atraso em s/veíc., paradas por veículo, velocidade em km/h)
# Médias de 10 rodadas (sementes 42 a 51), medidas de 148 s a 600 s.
# --------------------------------------------------------------------------
SIMULACAO = [
('C0 – plano atual', 125, '17:30–17:45', 3268, 7.7, 77.4, 90, 4.1, 0.18, 54.5),
('C0 – plano atual', 125, '17:45–18:00', 5212, 93.0, 312.1, 377, 12.1, 0.59, 43.8),
('C0 – plano atual', 125, '18:00–18:15', 5888, 131.7, 320.1, 473, 19.2, 0.75, 36.6),
('C0 – plano atual', 125, '18:15–18:30', 5668, 121.7, 320.3, 457, 16.8, 0.82, 38.8),
('C1 – verde +6 s', 131, '18:00–18:15', 5888, 103.9, 317.8, 417, 12.5, 0.59, 43.4),
('C1 – verde +6 s', 131, '18:15–18:30', 5668, 87.1, 316.6, 362, 10.7, 0.55, 45.4),
('C2 – verde +12 s', 137, '18:00–18:15', 5888, 47.6, 282.4, 229, 6.4, 0.28, 51.0),
('C2 – verde +12 s', 137, '18:15–18:30', 5668, 31.3, 239.0, 171, 5.8, 0.24, 52.0),
]

def secao_simulacao():
    """Aba Simulação: resultados do Vissim por cenário de semáforo e bloco."""
    def c(v, casas=0):
        return "—" if v is None else fmt(v, casas)
    linhas_sim = "".join(
        f"<tr><td>{escape(cen)}</td><td>{c(v)}</td><td>{escape(bl)}</td><td>{c(q)}</td>"
        f"<td>{c(fm, 1)}</td><td>{c(fx, 1)}</td><td>{c(pa)}</td><td>{c(at, 1)}</td><td>{c(pv, 2)}</td><td>{c(ve, 1)}</td></tr>"
        for cen, v, bl, q, fm, fx, pa, at, pv, ve in SIMULACAO)
    return f"""
<div class="card"><h2>Simulação no Vissim</h2>
<p class="cap">Dia 28/10, sentido Centro, só a faixa marcada no modelo. Cada bloco de 15 minutos foi simulado separadamente, com 10 rodadas (sementes 42 a 51), medindo de 148 s a 600 s. Médias das rodadas.</p>
<div class="tw"><table class="sim"><thead><tr><th>Cenário</th><th>Verde (s)</th><th>Bloco</th><th>Demanda (veíc./h)</th><th>Fila média (m)</th><th>Fila máxima (m)</th><th>Paradas na fila</th><th>Atraso (s/veíc.)</th><th>Paradas por veíc.</th><th>Velocidade (km/h)</th></tr></thead>
<tbody>{linhas_sim}</tbody></table></div>
<p class="note">Limites: o Vissim Student encerra cada rodada em 600 s, então a medição cobre cerca de 3 ciclos (o primeiro é descartado). A fila máxima chega perto de 320 m, limite do contador. Motos entram como veículos de uma faixa só, sem circular entre carros. O bloco 17:30–17:45 do plano atual (817 veículos, 3.268 veíc./h) tem demanda menor e não satura: fila máxima de cerca de 77 m. Quando a fila máxima fica perto de 320 m, fila média e máxima são limites inferiores. Nos cenários C1 e C2 só a fase do sentido Centro mudou (o verde dos outros movimentos não foi deslocado).</p></div>
"""

# --------------------------------------------------------------------------
# Cálculos
# --------------------------------------------------------------------------
def capacidade():
    p = PARAMETROS
    ge = p["verde"] + p["amarelo"] - p["perda_inicial"]
    return p["fluxo_saturacao"] * p["faixas"] * ge / p["ciclo"], ge


CAP, GE = capacidade()


def ucp(c, m, h, fm):
    return c + m * fm + h * PARAMETROS["fator_pesados"]


def atraso_uniforme(x):
    C = PARAMETROS["ciclo"]
    g = GE / C
    return 0.5 * C * (1 - g) ** 2 / (1 - min(1.0, x) * g)


def linhas():
    out = []
    for dia, sem, bloco, c, m, h in CONTAGENS:
        r = {"dia": dia, "sem": sem, "bloco": bloco, "c": c, "m": m, "h": h,
             "contado": c is not None}
        if r["contado"]:
            r["total"] = c + m + h
            r["fluxo"] = ucp(c, m, h, PARAMETROS["fator_moto_menor"]) * 4
            r["x1"] = r["fluxo"] / CAP
            r["x2"] = ucp(c, m, h, PARAMETROS["fator_moto_maior"]) * 4 / CAP
            r["d"] = atraso_uniforme(r["x1"])
        out.append(r)
    return out


def fmt(n, casas=0):
    s = f"{n:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def classe_x(x):
    if x > LIM_SATURA:
        return "x-red"
    if x >= LIM_ALERTA:
        return "x-orange"
    return ""


# --------------------------------------------------------------------------
# Gráficos em SVG
# --------------------------------------------------------------------------
def svg_cobertura(rows):
    dias = []
    for r in rows:
        if r["dia"] not in [d for d, _ in dias]:
            dias.append((r["dia"], r["sem"]))
    blocos = []
    for r in rows:
        if r["bloco"] not in blocos:
            blocos.append(r["bloco"])
    w_lab, cw, ch, top = 120, 150, 44, 28
    W = w_lab + cw * len(blocos)
    H = top + ch * len(dias)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Cobertura das contagens por dia e bloco">']
    for j, b in enumerate(blocos):
        s.append(f'<text x="{w_lab + cw * j + cw / 2}" y="18" text-anchor="middle" class="ax">{escape(b)}</text>')
    for i, (d, sem) in enumerate(dias):
        y = top + ch * i
        s.append(f'<text x="0" y="{y + ch / 2 + 4}" class="ax">{d} ({sem[:3].lower()})</text>')
        for j, b in enumerate(blocos):
            r = next(x for x in rows if x["dia"] == d and x["bloco"] == b)
            cls = "cell-ok" if r["contado"] else "cell-no"
            txt = f'{fmt(r["total"])} veíc.' if r["contado"] else "falta"
            s.append(f'<rect x="{w_lab + cw * j + 3}" y="{y + 3}" width="{cw - 6}" height="{ch - 6}" rx="6" class="{cls}"/>')
            s.append(f'<text x="{w_lab + cw * j + cw / 2}" y="{y + ch / 2 + 4}" text-anchor="middle" class="cell-t">{txt}</text>')
    s.append("</svg>")
    return "".join(s)


def _grupos(rows):
    """Posições x das barras, agrupadas por dia."""
    pos, x, ultimo = [], 0, None
    for r in rows:
        if ultimo is not None and r["dia"] != ultimo:
            x += 0.8
        pos.append(x)
        x += 1
        ultimo = r["dia"]
    return pos, x


def svg_volume(rows):
    W, H, ml, mr, mt, mb = 820, 340, 52, 12, 14, 62
    pw, ph = W - ml - mr, H - mt - mb
    pos, n = _grupos(rows)
    unit = pw / n
    bw = unit * 0.68
    topo = max((r["total"] for r in rows if r["contado"]), default=1)
    ymax = (int(topo / 200) + 1) * 200
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Volume por classe e bloco">']
    for v in range(0, ymax + 1, 200):
        y = mt + ph - ph * v / ymax
        s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{y}" y2="{y}" class="grid"/>')
        s.append(f'<text x="{ml - 8}" y="{y + 4}" text-anchor="end" class="ax">{fmt(v)}</text>')
    s.append(f'<text x="12" y="{mt + ph / 2}" transform="rotate(-90 12 {mt + ph / 2})" text-anchor="middle" class="ax">veículos por bloco</text>')
    dia_x = {}
    for r, p in zip(rows, pos):
        x = ml + p * unit + (unit - bw) / 2
        base = mt + ph
        if r["contado"]:
            y = base
            for chave, cls in (("c", "k-car"), ("m", "k-moto"), ("h", "k-pes")):
                hh = ph * r[chave] / ymax
                y -= hh
                s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{hh:.1f}" class="{cls}"><title>{r["dia"]} {r["bloco"]}: {chave}={r[chave]}</title></rect>')
            s.append(f'<text x="{x + bw / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle" class="val">{fmt(r["total"])}</text>')
        else:
            s.append(f'<rect x="{x:.1f}" y="{base - 26}" width="{bw:.1f}" height="26" class="cell-no"/>')
            s.append(f'<text x="{x + bw / 2:.1f}" y="{base - 9}" text-anchor="middle" class="ax">falta</text>')
        s.append(f'<text x="{x + bw / 2:.1f}" y="{base + 15}" text-anchor="middle" class="ax">{r["bloco"][:5]}</text>')
        dia_x.setdefault(r["dia"], []).append(x + bw / 2)
    for d, xs in dia_x.items():
        sem = next(r["sem"] for r in rows if r["dia"] == d)
        s.append(f'<text x="{sum(xs) / len(xs):.1f}" y="{mt + ph + 36}" text-anchor="middle" class="axb">{d} ({sem.lower()})</text>')
    s.append("</svg>")
    return "".join(s)


def svg_x(rows):
    W, H, ml, mr, mt, mb = 820, 320, 52, 84, 14, 62
    pw, ph = W - ml - mr, H - mt - mb
    pos, n = _grupos(rows)
    unit = pw / n
    bw = unit * 0.68
    ymax = 1.2

    def Y(v):
        return mt + ph - ph * v / ymax

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Grau de saturação X por bloco">']
    v = 0.0
    while v <= ymax + 1e-9:
        s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(v)}" y2="{Y(v)}" class="grid"/>')
        s.append(f'<text x="{ml - 8}" y="{Y(v) + 4}" text-anchor="end" class="ax">{fmt(v, 2)}</text>')
        v += 0.2
    s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(LIM_SATURA)}" y2="{Y(LIM_SATURA)}" class="ref-rd"/>')
    s.append(f'<text x="{W - 4}" y="{Y(LIM_SATURA) + 4}" text-anchor="end" class="ref-t">{fmt(LIM_SATURA, 2)} saturação</text>')
    s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(LIM_ALERTA)}" y2="{Y(LIM_ALERTA)}" class="ref-or"/>')
    s.append(f'<text x="{W - 4}" y="{Y(LIM_ALERTA) + 4}" text-anchor="end" class="ref-t">{fmt(LIM_ALERTA, 2)} atenção</text>')
    dia_x = {}
    for r, p in zip(rows, pos):
        x = ml + p * unit + (unit - bw) / 2
        base = mt + ph
        if r["contado"]:
            cls = {"x-red": "bar-rd", "x-orange": "bar-or"}.get(classe_x(r["x1"]), "bar-ok")
            hh = ph * r["x1"] / ymax
            s.append(f'<rect x="{x:.1f}" y="{base - hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="2" class="{cls}"><title>{r["dia"]} {r["bloco"]}: X = {fmt(r["x1"], 2)} (fator menor), {fmt(r["x2"], 2)} (fator maior)</title></rect>')
            ty = Y(r["x2"])
            s.append(f'<line x1="{x - 3:.1f}" x2="{x + bw + 3:.1f}" y1="{ty:.1f}" y2="{ty:.1f}" class="tick"/>')
        else:
            s.append(f'<rect x="{x:.1f}" y="{base - 26}" width="{bw:.1f}" height="26" class="cell-no"/>')
            s.append(f'<text x="{x + bw / 2:.1f}" y="{base - 9}" text-anchor="middle" class="ax">falta</text>')
        s.append(f'<text x="{x + bw / 2:.1f}" y="{base + 15}" text-anchor="middle" class="ax">{r["bloco"][:5]}</text>')
        dia_x.setdefault(r["dia"], []).append(x + bw / 2)
    for d, xs in dia_x.items():
        sem = next(r["sem"] for r in rows if r["dia"] == d)
        s.append(f'<text x="{sum(xs) / len(xs):.1f}" y="{mt + ph + 36}" text-anchor="middle" class="axb">{d} ({sem.lower()})</text>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# Página
# --------------------------------------------------------------------------
CSS = """
:root{--bg:#f6f7f9;--card:#fff;--tx:#1b1f24;--mut:#667085;--bd:#e3e6eb;--grid:#e8ebf0;
--car:#338ced;--moto:#e76624;--pes:#00a888;--or:#e49c06;--rd:#dc3c3d;--or-tx:#b27600;--rd-tx:#c42b2c;
--ok:#f3f4f6;--no:#f1f2f4;--ref:#9aa0a8;--tick:#555a61;}
@media (prefers-color-scheme:dark){:root{--bg:#0b0b0b;--card:#1f1f1f;--tx:#efefef;--mut:#9b9b9b;--bd:#282828;--grid:#2b2b2b;
--or-tx:#e49c06;--rd-tx:#dc3c3d;--ok:#0b0b0b;--no:#1f1f1f;--ref:#5a5a5a;--tick:#afafaf;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 18px}
.tabs{display:flex;gap:6px;border-bottom:1px solid var(--bd);margin-bottom:18px}
.tab{background:none;border:0;color:var(--mut);padding:10px 14px;font:inherit;cursor:pointer;border-bottom:2px solid transparent}
.tab[aria-selected=true]{color:var(--tx);border-color:var(--car);font-weight:600}
.panel[hidden]{display:none}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px;margin-bottom:16px}
.kpi .n{font-size:28px;font-weight:650;line-height:1.1}.kpi .l{color:var(--mut);font-size:13px;margin-top:4px}
h2{font-size:16px;margin:0 0 2px}.cap{color:var(--mut);font-size:13px;margin:0 0 12px}
svg{width:100%;height:auto;display:block}
.ax{fill:var(--mut);font-size:12px}.axb{fill:var(--tx);font-size:12px;font-weight:600}.val{fill:var(--tx);font-size:11px}
.grid{stroke:var(--grid)}.k-car{fill:var(--car)}.k-moto{fill:var(--moto)}.k-pes{fill:var(--pes)}
.cell-ok{fill:var(--ok)}.cell-no{fill:var(--no);stroke:var(--bd);stroke-dasharray:4 3}.cell-t{fill:var(--tx);font-size:12px}
.ref-or{stroke:var(--or);stroke-dasharray:5 4}.ref-rd{stroke:var(--ref);stroke-dasharray:5 4}.ref-t{fill:var(--mut);font-size:11px}
.bar-ok{fill:var(--car)}.bar-or{fill:var(--or)}.bar-rd{fill:var(--rd)}.tick{stroke:var(--tick);stroke-width:2.5}
.leg{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--mut);margin-top:6px}
.leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.filt{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.chip{border:1px solid var(--bd);background:var(--card);color:var(--tx);border-radius:999px;padding:5px 12px;font:inherit;font-size:13px;cursor:pointer}
.chip[aria-pressed=true]{background:var(--car);border-color:var(--car);color:#fff}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:8px 10px;border-bottom:1px solid var(--bd);text-align:right;white-space:nowrap}
th{color:var(--mut);font-weight:500;font-size:13px}th:nth-child(-n+2),td:nth-child(-n+2),th:last-child,td:last-child{text-align:left}
.x-orange{color:var(--or-tx);font-weight:600}.x-red{color:var(--rd-tx);font-weight:600}.falta{color:var(--mut)}
details{margin-top:8px}summary{cursor:pointer;color:var(--mut)}
.par td:first-child,.par th:first-child{text-align:left}.par td,.par th{text-align:left}
.note{color:var(--mut);font-size:13px}code{background:var(--no);padding:1px 5px;border-radius:4px}
.sim th:nth-child(3),.sim td:nth-child(3){text-align:left}.sim th:last-child,.sim td:last-child{text-align:right}
.docs{list-style:none;margin:12px 0 0;padding:0}
.doc{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;padding:12px 0;border-top:1px solid var(--bd)}
.doc-t{font-weight:600}.doc-m{color:var(--mut);font-size:13px}.doc-a{display:flex;gap:6px;flex-wrap:wrap}
.btn{border:1px solid var(--bd);background:var(--card);color:var(--tx);border-radius:999px;padding:5px 12px;font:inherit;font-size:13px;cursor:pointer;text-decoration:none}
.btn[aria-pressed=true]{background:var(--car);border-color:var(--car);color:#fff}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 16px;font-size:14px}
.meta b{display:block;color:var(--mut);font-weight:500;font-size:13px}
.viewer{display:block;width:100%;height:80vh;min-height:460px;border:1px solid var(--bd);border-radius:8px;background:var(--no)}
"""

JS = """
const tabs=[...document.querySelectorAll('.tab')],panels=[...document.querySelectorAll('.panel')];
function abrir(id){tabs.forEach(t=>t.setAttribute('aria-selected',t.dataset.p===id));
panels.forEach(p=>p.hidden=p.id!==id);}
tabs.forEach(t=>t.addEventListener('click',()=>abrir(t.dataset.p)));
const chips=[...document.querySelectorAll('.chip')],linhas=[...document.querySelectorAll('#tb tr')];
chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(o=>o.setAttribute('aria-pressed',o===c));
linhas.forEach(l=>l.hidden=c.dataset.d!=='todos'&&l.dataset.d!==c.dataset.d);}));
const dbtn=[...document.querySelectorAll('.btn[data-doc]')],dview=document.getElementById('doc-view'),dtit=document.getElementById('doc-tit');
function verDoc(b){dbtn.forEach(o=>o.setAttribute('aria-pressed',o===b));dview.src=b.dataset.doc;dtit.textContent=b.dataset.t;}
dbtn.forEach(b=>b.addEventListener('click',()=>verDoc(b)));
tabs.forEach(t=>t.addEventListener('click',()=>{if(t.dataset.p==='documentos'&&dview&&!dview.getAttribute('src')&&dbtn.length)
verDoc(dbtn.find(b=>b.getAttribute('aria-pressed')==='true')||dbtn[0]);}));
"""


# --------------------------------------------------------------------------
# ERRO DA CONTAGEM (recontagem nos vídeos x folha de campo, bloco 28/10 17:30–17:45)
# C1 = folha de campo (576 carros, 232 motos, 9 pesados); C2 = soma de 5 trechos de 3 min recontados.
# Erro = |C1 − C2| / C2 × 100. Trechos de 27/10 e 29/10 não têm C1 por trecho (só ordem de grandeza).
# --------------------------------------------------------------------------
# Dados da recontagem (3 min) e erro; tudo calculado aqui
C1 = {"carros":576,"motos":232,"pesados":9}
TRECHOS = [  # dia, trecho, carros, motos, pesados, comparavel
 ("27/10","17:57–18:00",94,49,4,False),
 ("28/10","17:30–17:33",111,33,1,True),
 ("28/10","17:33–17:36",99,41,2,True),
 ("28/10","17:36–17:39",108,35,1,True),
 ("28/10","17:39–17:42",104,49,1,True),
 ("28/10","17:42–17:45",132,55,5,True),
 ("29/10","18:15–18:18",138,50,4,False),
]
C2={k:sum(t[i] for t in TRECHOS if t[5]) for k,i in (("carros",2),("motos",3),("pesados",4))}
def f1(v): return f"{v:.1f}".replace(".",",")
def f0(v): return f"{v:,.0f}".replace(",",".")
def err(a,b): return abs(a-b)/b*100
E_cls={k:err(C1[k],C2[k]) for k in C1}
T1=sum(C1.values()); T2=sum(C2.values()); E_tot=err(T1,T2)

def table(head, rows, cls_first_left=2, th_cls=None):
    h="".join(f'<th class="l">{c}</th>' if i<cls_first_left else f'<th>{c}</th>' for i,c in enumerate(head))
    b=""
    for r in rows:
        tds="".join((f'<td class="l">{c}</td>' if i<cls_first_left else f'<td>{c}</td>') for i,c in enumerate(r))
        b+=f"<tr>{tds}</tr>"
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'

nomes={"carros":"Automóveis","motos":"Motos","pesados":"Pesados"}
resumo=[(nomes[k],f0(C1[k]),f0(C2[k]),f"{C1[k]-C2[k]:+d}".replace("-","−"),f1(E_cls[k])+"%") for k in C1]
resumo.append(("<b>Total</b>",f"<b>{f0(T1)}</b>",f"<b>{f0(T2)}</b>",f"<b>{T1-T2:+d}</b>",f"<b>{f1(E_tot)}%</b>"))
tr_rows=[]
for d,t,c,m,p,ok in TRECHOS:
    tr_rows.append((d,t,f0(c),f0(m),f0(p),f0(c+m+p),"Sim, soma o bloco 17:30–17:45" if ok else "Não: sem C1 por trecho"))
tr_rows.append(("<b>28/10</b>","<b>17:30–17:45 (5 trechos)</b>",f"<b>{C2['carros']}</b>",f"<b>{C2['motos']}</b>",f"<b>{C2['pesados']}</b>",f"<b>{T2}</b>","<b>C2 do bloco</b>"))



def graficos(estilo):
    if estilo=="art":
        tx="var(--color-fg)"; mu="var(--color-fg-muted)"; grid="var(--color-border-line)"
        wrap=lambda svg,leg: f'<div class="tc-legend">{leg}</div><div class="tc-chart" style="min-height:0">{svg}</div>'
    else:
        tx="var(--tx)"; mu="var(--mut)"; grid="var(--grid)"
        wrap=lambda svg,leg: f'<div class="leg" style="margin:10px 0 0">{leg}</div>{svg}'
    cores=[("Automóveis","carros","#338ced"),("Motos","motos","#e76624"),("Pesados","pesados","#00a888")]
    cols=[(n,E_cls[k],f"{C1[k]} × {C2[k]}",c) for n,k,c in cores]+[("Total",E_tot,f"{T1} × {T2}","#e49c06")]
    H=96.0; mx=12.0; base=118
    svg=f'<svg viewBox="0 0 560 176" role="img" aria-label="Erro percentual por classe e no total" style="width:100%;height:auto;display:block;font-family:inherit">'
    for g in (0,5,10):
        y=base-g/mx*H
        svg+=f'<line x1="36" x2="552" y1="{y:.1f}" y2="{y:.1f}" stroke="{grid}"/><text x="30" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{mu}">{g}%</text>'
    for i,(n,e,sub,c) in enumerate(cols):
        x=60+i*128; h=e/mx*H
        svg+=f'<rect x="{x}" y="{base-h:.1f}" width="84" height="{h:.1f}" rx="4" fill="{c}"><title>{n}: erro de {f1(e)}% (folha × recontagem: {sub})</title></rect>'
        svg+=f'<text x="{x+42}" y="{base-h-6:.1f}" text-anchor="middle" font-size="13" font-weight="600" fill="{tx}">{f1(e)}%</text>'
        svg+=f'<text x="{x+42}" y="{base+17}" text-anchor="middle" font-size="12" fill="{tx}">{n}</text>'
        svg+=f'<text x="{x+42}" y="{base+33}" text-anchor="middle" font-size="11" fill="{mu}">{sub}</text>'
    svg+='</svg>'
    leg="".join(f'<span><i style="background:{c}"></i>{n}</span>' for n,_,c in [(a,b,c) for a,b,c in cores]+[("Total do bloco","","#e49c06")])
    return wrap(svg,leg)

def conteudo(estilo):
    # estilo 'art' (painel Claude) ou 'gh' (site GitHub)
    if estilo=="art":
        card=lambda t,sub,body: f'<div class="tc-card"><header><h2>{t}</h2><p class="tc-sub">{sub}</p></header>{body}</div>'
        scroll=lambda x: f'<div class="tc-scroll">{x}</div>'
        kpi=lambda lab,val,sub: f'<div class="tc-kpi"><span class="lab">{lab}</span><b class="val">{val}</b><span class="sub">{sub}</span></div>'
        kpis=lambda x: f'<div class="tc-kpis">{x}</div>'
        note=lambda x: f'<p class="tc-sub">{x}</p>'
        grid2=lambda x: f'<div class="tc-grid2">{x}</div>'
    else:
        card=lambda t,sub,body: f'<div class="card"><h2>{t}</h2><p class="cap">{sub}</p>{body}</div>'
        scroll=lambda x: f'<div class="tw">{x}</div>'
        kpi=lambda lab,val,sub: f'<div class="card kpi"><div class="n">{val}</div><div class="l">{lab}. {sub}</div></div>'
        kpis=lambda x: f'<div class="kpis">{x}</div>'
        note=lambda x: f'<p class="note">{x}</p>'
        grid2=lambda x: x
    sub_k=f"{f0(T1)} na folha contra {f0(T2)} na recontagem"
    visao_kpis=kpis(
        kpi("Erro total da contagem",f1(E_tot)+"%",sub_k)+
        kpi("Automóveis",f1(E_cls['carros'])+"%",f"{C1['carros']} contra {C2['carros']}")+
        kpi("Motos",f1(E_cls['motos'])+"%",f"{C1['motos']} contra {C2['motos']}")+
        kpi("Pesados",f1(E_cls['pesados'])+"%",f"{C1['pesados']} contra {C2['pesados']}: um veículo de diferença"))
    visao=card("Erro da contagem","Contagem original (folha) comparada com a recontagem nos vídeos, no bloco 28/10 17:30–17:45",
        visao_kpis+graficos(estilo)+note("Erro = |C1 − C2| ÷ C2 × 100, com C1 da folha e C2 da recontagem. Só esse bloco tem as duas contagens comparáveis. Detalhes na aba Erro da contagem."))
    eq=note("Fórmula do TCC: E (%) = |C1 − C2| ÷ C2 × 100, com C1 = contagem original (folha de campo) e C2 = recontagem nos vídeos.")
    sec1=card("Resultado por classe","Bloco 28/10, 17:30–17:45 (único bloco com C1 e C2 comparáveis)",
        scroll(table(["Classe","C1: folha","C2: recontagem","Diferença (C1 − C2)","Erro"],resumo,1))+eq+
        note("O total usa a diferença líquida (817 − 777 = 40). Somando as diferenças de cada classe (22 + 19 + 1 = 42) o valor seria 5,4%; o TCC usa a diferença líquida, que segue a fórmula aplicada ao total."))
    sec2=card("Recontagem por trecho de 3 minutos","Cada trecho foi recontado nos vídeos em câmera lenta",
        scroll(table(["Dia","Trecho","Automóveis","Motos","Pesados","Total","Entra no erro?"],tr_rows,2))+
        note("A contagem original foi anotada por bloco de 15 minutos, então só o bloco 28/10 17:30–17:45 (5 trechos seguidos) pode ser comparado. Os trechos de 27/10 e 29/10 não têm C1 e servem só como ordem de grandeza."))
    sec4=card("Como o trecho foi escolhido","Sorteio com semente fixa, para poder repetir",
        note("Foram sorteados 20 trechos de 3 minutos por hora, 1 por dia, com semente 20261115 e sem repetir o trecho já recontado (28/10, 18:00–18:15). Cada dia recebeu um trecho. No dia 28, o trecho sorteado foi estendido para todo o bloco 17:30–17:45 para poder comparar com a folha."))
    sec5=card("Como ler o resultado","Limites da comparação",
        note("O erro mede a diferença entre duas contagens e não diz qual das duas é a verdadeira. É um bloco só, e a diferença de pesados (1 veículo) pesa pouco. Em ordem de grandeza, um erro de 5,1% no fluxo muda o grau de saturação X do bloco 17:30 de 0,56 para algo entre 0,53 e 0,59, e o X da hora de 28/10 de 0,86 para algo entre 0,82 e 0,91 (fator de moto 0,33). Em nenhum desses casos o X ultrapassa 1."))
    return visao, sec1+sec2+sec4+sec5


def pagina():
    ERRO_VISAO, ERRO_ABA = conteudo("gh")
    rows = linhas()
    cont = [r for r in rows if r["contado"]]
    p = PARAMETROS
    tot_veic = sum(r["total"] for r in cont)
    pior = max(cont, key=lambda r: r["x1"])
    n_sat1 = sum(r["x1"] > LIM_SATURA for r in cont)
    n_sat2 = sum(r["x2"] > LIM_SATURA for r in cont)
    dias = list(dict.fromkeys(r["dia"] for r in rows))

    kpis = f"""
<div class="kpis">
 <div class="card kpi"><div class="n">{len(cont)} de {len(rows)}</div><div class="l">blocos de 15 min contados</div></div>
 <div class="card kpi"><div class="n">{fmt(tot_veic)}</div><div class="l">veículos contados (automóveis + motos + pesados)</div></div>
 <div class="card kpi"><div class="n">{fmt(pior['x1'], 2)}</div><div class="l">maior grau de saturação X: {pior['dia']}, {pior['bloco']} (fator de moto {fmt(p['fator_moto_menor'], 2)})</div></div>
 <div class="card kpi"><div class="n">{n_sat1} a {n_sat2}</div><div class="l">blocos com X acima de 1, conforme o fator de moto ({fmt(p['fator_moto_menor'], 2)} a {fmt(p['fator_moto_maior'], 2)})</div></div>
</div>"""

    leg_vol = ('<div class="leg"><span><i style="background:var(--car)"></i>Automóveis</span>'
               '<span><i style="background:var(--moto)"></i>Motocicletas</span>'
               '<span><i style="background:var(--pes)"></i>Ônibus e caminhões</span></div>')
    leg_x = (f'<div class="leg"><span><i style="background:var(--car)"></i>X com fator de moto {fmt(p["fator_moto_menor"], 2)}</span>'
             f'<span><i style="background:var(--or)"></i>entre {fmt(LIM_ALERTA, 2)} e {fmt(LIM_SATURA, 2)}</span>'
             f'<span><i style="background:var(--rd)"></i>acima de {fmt(LIM_SATURA, 2)}</span>'
             f'<span><i style="background:var(--tick);height:3px;width:14px;border-radius:0;vertical-align:3px"></i>com fator de moto {fmt(p["fator_moto_maior"], 2)}</span></div>')

    visao = f"""
{kpis}
<div class="card"><h2>Cobertura das contagens</h2><p class="cap">Dia e bloco de 15 minutos; o número é o total de veículos contados.</p>{svg_cobertura(rows)}</div>
<div class="card"><h2>Volume por classe</h2><p class="cap">Veículos contados em cada bloco de 15 minutos.</p>{svg_volume(rows)}{leg_vol}</div>
<div class="card"><h2>Grau de saturação X por bloco</h2>
<p class="cap">X = fluxo em UCP/h ÷ capacidade ({fmt(CAP)} UCP/h). Acima de 1, chega mais veículo do que o semáforo escoa em um ciclo.</p>{svg_x(rows)}{leg_x}</div>
"""

    chips_html = '<button class="chip" data-d="todos" aria-pressed="true">Todos os dias</button>' + "".join(
        f'<button class="chip" data-d="{d}" aria-pressed="false">{d}</button>' for d in dias)
    linhas_html = []
    for r in rows:
        if r["contado"]:
            linhas_html.append(
                f'<tr data-d="{r["dia"]}"><td>{r["dia"]}</td><td>{r["bloco"]}</td><td>{fmt(r["c"])}</td><td>{fmt(r["m"])}</td>'
                f'<td>{fmt(r["h"])}</td><td>{fmt(r["total"])}</td><td>{fmt(r["fluxo"])}</td>'
                f'<td class="{classe_x(r["x1"])}">{fmt(r["x1"], 2)}</td><td class="{classe_x(r["x2"])}">{fmt(r["x2"], 2)}</td>'
                f'<td>{fmt(r["d"], 1)}</td><td>Contado</td></tr>')
        else:
            linhas_html.append(
                f'<tr data-d="{r["dia"]}" class="falta"><td>{r["dia"]}</td><td>{r["bloco"]}</td>'
                + "<td>—</td>" * 8 + "<td>Falta contar</td></tr>")

    contagens = f"""
<div class="card"><h2>Todas as contagens</h2>
<p class="cap">Por bloco de 15 minutos; fluxo e atraso calculados com os parâmetros do rodapé.
<span class="x-orange">Laranja</span>: X entre {fmt(LIM_ALERTA, 2)} e {fmt(LIM_SATURA, 2)} (alerta).
<span class="x-red">Vermelho</span>: X acima de {fmt(LIM_SATURA, 2)} (demanda maior que a capacidade).</p>
<div class="filt">{chips_html}</div>
<div class="tw"><table><thead><tr><th>Dia</th><th>Bloco</th><th>Automóveis</th><th>Motos</th><th>Pesados</th><th>Total</th>
<th>Fluxo (UCP/h)</th><th>X, fator menor</th><th>X, fator maior</th><th>Atraso unif. (s)</th><th>Situação</th></tr></thead>
<tbody id="tb">{"".join(linhas_html)}</tbody></table></div></div>
"""

    par_rows = [
        ("Ciclo semafórico", f"{p['ciclo']} s", f"verde {p['verde']} s, amarelo {p['amarelo']} s, vermelho {p['vermelho']} s"),
        ("Verde efetivo", f"{GE} s", f"verde + amarelo − perda inicial ({p['perda_inicial']} s)"),
        ("Faixas", f"{p['faixas']}", "sentido Centro"),
        ("Fluxo de saturação", f"{fmt(p['fluxo_saturacao'])} UCP/h/faixa", "valor-base do HCM, provisório; pode ser medido nos vídeos"),
        ("Capacidade", f"{fmt(CAP)} UCP/h", "fluxo de saturação × faixas × verde efetivo ÷ ciclo"),
        ("Fator da moto", f"{fmt(p['fator_moto_menor'], 2)} e {fmt(p['fator_moto_maior'], 2)}", "provisórios, ainda sem fonte definida"),
        ("Fator de pesados", f"{fmt(p['fator_pesados'], 1)}", "E_T do HCM para interseção semaforizada; confirmar a edição"),
    ]
    par_html = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in par_rows)
    rodape = f"""
<details><summary>Parâmetros e fórmulas</summary><div class="card tw" style="margin-top:8px">
<table class="par"><thead><tr><th>Parâmetro</th><th>Valor</th><th>Observação</th></tr></thead><tbody>{par_html}</tbody></table>
<p class="note">UCP do bloco = automóveis + motos × fator da moto + pesados × {fmt(p['fator_pesados'], 1)}. Fluxo (UCP/h) = UCP do bloco × 4.
X = fluxo ÷ capacidade. Atraso uniforme d1 = 0,5·C·(1 − ge/C)² ÷ (1 − min(1, X)·ge/C), calculado com o fator menor.
Com X acima de 1, o atraso uniforme subestima o atraso real, pois não inclui a fila acumulada.
Os fatores de equivalência e o fluxo de saturação ainda serão definidos com a orientadora e podem mudar os valores de X.</p></div></details>
"""

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(TITULO)}</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>{escape(TITULO)}</h1><p class="sub">{escape(SUBTITULO)}</p>
<div class="tabs" role="tablist">
<button class="tab" role="tab" data-p="visao" aria-selected="true">Visão geral</button>
<button class="tab" role="tab" data-p="contagens" aria-selected="false">Contagens</button>
<button class="tab" role="tab" data-p="erro" aria-selected="false">Erro da contagem</button>
<button class="tab" role="tab" data-p="simulacao" aria-selected="false">Simulação</button>
<button class="tab" role="tab" data-p="documentos" aria-selected="false">Documentos</button></div>
<section class="panel" id="visao">{visao}{ERRO_VISAO}</section>
<section class="panel" id="contagens" hidden>{contagens}</section>
<section class="panel" id="erro" hidden>{ERRO_ABA}</section>
<section class="panel" id="simulacao" hidden>{secao_simulacao()}</section>
<section class="panel" id="documentos" hidden>{secao_documentos()}</section>
{rodape}
</div><script>{JS}</script></body></html>"""


if __name__ == "__main__":
    destino = Path(__file__).with_name("index.html")
    destino.write_text(pagina(), encoding="utf-8")
    print(f"Painel gerado em {destino}")
