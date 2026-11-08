#!/usr/bin/env python3
"""Gera o painel do TCC (abas Visão geral e Contagens) como uma página index.html.

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
    ("28/10", "Quarta", "17:30–17:45", 806, 384, 9),
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
"""

JS = """
const tabs=[...document.querySelectorAll('.tab')],panels=[...document.querySelectorAll('.panel')];
function abrir(id){tabs.forEach(t=>t.setAttribute('aria-selected',t.dataset.p===id));
panels.forEach(p=>p.hidden=p.id!==id);}
tabs.forEach(t=>t.addEventListener('click',()=>abrir(t.dataset.p)));
const chips=[...document.querySelectorAll('.chip')],linhas=[...document.querySelectorAll('#tb tr')];
chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(o=>o.setAttribute('aria-pressed',o===c));
linhas.forEach(l=>l.hidden=c.dataset.d!=='todos'&&l.dataset.d!==c.dataset.d);}));
"""


def pagina():
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
<button class="tab" role="tab" data-p="contagens" aria-selected="false">Contagens</button></div>
<section class="panel" id="visao">{visao}</section>
<section class="panel" id="contagens" hidden>{contagens}</section>
{rodape}
</div><script>{JS}</script></body></html>"""


if __name__ == "__main__":
    destino = Path(__file__).with_name("index.html")
    destino.write_text(pagina(), encoding="utf-8")
    print(f"Painel gerado em {destino}")
