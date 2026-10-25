"""Mapas coloridos (MEF) do radier a partir dos CSV exportados do Robot — sem matplotlib (Pillow + numpy).

Entradas (gerados por extrair_cascas.py / estaq_ler_rev_v1.ps1):
  elementos.csv : comb;elem;xc;yc;mxx;myy;mxy;qxx;qyy  (kN.m/m, kN/m)
  nos.csv       : no;x;y;uz_cNN_mm;...                 (mm)
  estacas.csv   : comb;estaca;R_molas_kN;...           (kN)
Saidas: PNG com mapa em faixas de cor (estilo Robot), eixos em metros, estacas, costado e barra de legenda.

Uso como modulo:  from mapas_mef import gerar_todos; gerar_todos(pasta_csv, prefixo, pasta_saida)
Uso em linha:     python mapas_mef.py <pasta_csv> <prefixo> ./figuras
"""
import csv
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ESTACAS = [(x, y) for x in (-3.6, -1.2, 1.2, 3.6) for y in (-3.6, -1.2, 1.2, 3.6)]
R_EST, R_RES, LADO = 0.35, 3.82, 10.0

# paleta tipo "jet" do Robot (azul -> ciano -> verde -> amarelo -> vermelho)
_JET = [(0, 0, 143), (0, 0, 255), (0, 127, 255), (0, 255, 255), (127, 255, 127), (255, 255, 0),
        (255, 127, 0), (255, 0, 0), (127, 0, 0)]


def _cor(t):
    t = min(max(t, 0.0), 1.0) * (len(_JET) - 1)
    i = min(int(t), len(_JET) - 2)
    f = t - i
    a, b = _JET[i], _JET[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


def _fonte(tam):
    for nome in ("arial.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _fmt(v):
    s = "%.0f" % v if abs(v) >= 100 else ("%.1f" % v if abs(v) >= 10 else "%.2f" % v)
    return s.replace(".", ",")


def ler_elementos(caminho, combos):
    out = {}
    with open(caminho, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            c = int(r["comb"])
            if c in combos:
                out.setdefault(c, []).append((float(r["xc"]), float(r["yc"]), float(r["mxx"]), float(r["myy"]),
                                              float(r["mxy"]), float(r["qxx"]), float(r["qyy"])))
    return {c: np.array(v) for c, v in out.items()}


def ler_nos(caminho, coluna):
    pts = []
    with open(caminho, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r.get("no"):
                pts.append((float(r["x"]), float(r["y"]), float(r[coluna])))
    return np.array(pts)


def ler_estacas(caminho, comb):
    out = {}
    with open(caminho, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if int(r["comb"]) == comb:
                out[int(r["estaca"])] = float(r["R_molas_kN"])
    return out


def _interp_nn(px, py, valores, passo=0.05):
    """Interpola valores dispersos (centroides/nos) numa malha regular por vizinho mais proximo."""
    gx = np.arange(-LADO / 2 + passo / 2, LADO / 2, passo)
    gy = np.arange(-LADO / 2 + passo / 2, LADO / 2, passo)
    GX, GY = np.meshgrid(gx, gy)
    Z = np.empty(GX.shape)
    flat_x, flat_y = GX.ravel(), GY.ravel()
    res = np.empty(flat_x.size)
    bloco = 4000
    for i in range(0, flat_x.size, bloco):
        dx = flat_x[i:i + bloco, None] - px[None, :]
        dy = flat_y[i:i + bloco, None] - py[None, :]
        idx = np.argmin(dx * dx + dy * dy, axis=1)
        res[i:i + bloco] = valores[idx]
    Z[:] = res.reshape(GX.shape)
    return gx, gy, Z


def mapa(Z, gx, gy, titulo, unidade, saida, vmin=None, vmax=None, n_faixas=12, excluir_estacas_r=None,
         marcar_max=True, simetrico=False, largura_px=1500, nota=""):
    vmin = float(np.nanmin(Z)) if vmin is None else vmin
    vmax = float(np.nanmax(Z)) if vmax is None else vmax
    if simetrico:
        m = max(abs(vmin), abs(vmax))
        vmin, vmax = -m, m
    # faixas discretas
    niveis = np.linspace(vmin, vmax, n_faixas + 1)
    Zc = np.clip(Z, vmin, vmax)
    ind = np.clip(np.searchsorted(niveis, Zc, side="right") - 1, 0, n_faixas - 1)
    cores = np.array([_cor((k + 0.5) / n_faixas) for k in range(n_faixas)], dtype=np.uint8)
    img_arr = cores[ind]                                          # (ny, nx, 3)
    img_arr = img_arr[::-1]                                       # y para cima
    mapa_img = Image.fromarray(img_arr, "RGB")
    # layout
    margem, legenda_w, topo, base = 110, 230, 90, 70
    esc = (largura_px - margem - legenda_w - 40) / LADO            # px por metro
    w_map = int(LADO * esc)
    mapa_img = mapa_img.resize((w_map, w_map), Image.NEAREST)
    W, H = largura_px, topo + w_map + base
    im = Image.new("RGB", (W, H), "white")
    im.paste(mapa_img, (margem, topo))
    d = ImageDraw.Draw(im)
    f_t, f_e, f_l = _fonte(30), _fonte(20), _fonte(19)

    def X(x):
        return margem + (x + LADO / 2) * esc

    def Y(y):
        return topo + (LADO / 2 - y) * esc

    # exclusao ao redor das estacas (regiao coberta pela puncao) e estacas
    for ex, ey in ESTACAS:
        if excluir_estacas_r:
            r = excluir_estacas_r * esc
            d.ellipse([X(ex) - r, Y(ey) - r, X(ex) + r, Y(ey) + r], fill=(235, 235, 235), outline=(120, 120, 120), width=2)
        r = R_EST * esc
        d.ellipse([X(ex) - r, Y(ey) - r, X(ex) + r, Y(ey) + r], outline="black", width=3)
    # costado do reservatorio
    r = R_RES * esc
    d.ellipse([X(0) - r, Y(0) - r, X(0) + r, Y(0) + r], outline="black", width=4)
    # contorno e eixos
    d.rectangle([margem, topo, margem + w_map, topo + w_map], outline="black", width=3)
    for v in range(-5, 6):
        d.line([X(v), topo + w_map, X(v), topo + w_map + 8], fill="black", width=2)
        d.text((X(v), topo + w_map + 12), "%d" % v, fill="black", font=f_e, anchor="mt")
        d.line([margem - 8, Y(v), margem, Y(v)], fill="black", width=2)
        d.text((margem - 12, Y(v)), "%d" % v, fill="black", font=f_e, anchor="rm")
    d.text((margem + w_map / 2, topo + w_map + 42), "x (m)", fill="black", font=f_e, anchor="mt")
    d.text((28, topo + w_map / 2), "y (m)", fill="black", font=f_e, anchor="mm")
    # titulo
    d.text((margem, 22), titulo, fill="black", font=f_t, anchor="lt")
    if nota:
        d.text((margem, 60), nota, fill=(80, 80, 80), font=f_l, anchor="lt")
    # legenda (barra de faixas)
    lx = margem + w_map + 40
    ly0, ly1 = topo, topo + w_map
    hf = (ly1 - ly0) / n_faixas
    for k in range(n_faixas):
        y1 = ly1 - k * hf
        d.rectangle([lx, y1 - hf, lx + 36, y1], fill=_cor((k + 0.5) / n_faixas), outline="black")
    for k, nv in enumerate(niveis):
        y = ly1 - k * hf
        d.text((lx + 46, y), _fmt(nv), fill="black", font=f_l, anchor="lm")
    d.text((lx, ly0 - 30), unidade, fill="black", font=f_e, anchor="lb")
    # maximo
    if marcar_max:
        mask = np.ones(Z.shape, bool)
        if excluir_estacas_r:
            GX, GY = np.meshgrid(gx, gy)
            for ex, ey in ESTACAS:
                mask &= (GX - ex) ** 2 + (GY - ey) ** 2 >= excluir_estacas_r ** 2
        Zm = np.where(mask, Z, np.nan)
        j, i = np.unravel_index(np.nanargmax(np.abs(Zm)), Z.shape)
        xm, ym, vm = gx[i], gy[j], Z[j, i]
        d.ellipse([X(xm) - 9, Y(ym) - 9, X(xm) + 9, Y(ym) + 9], outline="black", fill="white", width=3)
        d.text((X(xm) + 14, Y(ym) - 14), "%s (%s; %s)" % (_fmt(vm), _fmt(xm), _fmt(ym)), fill="black", font=f_l, anchor="lb")
    im.save(saida, optimize=True)
    return saida


def _env(el, combos, func, excluir_r=None):
    """Envoltoria elemento a elemento (mesma malha em todas as combinacoes). Elementos cujo CENTROIDE
    esta a menos de excluir_r de um eixo de estaca recebem 0 (mesmo criterio dos verificadores)."""
    base = el[combos[0]]
    px, py = base[:, 0], base[:, 1]
    vals = np.stack([func(el[c]) for c in combos], axis=0)
    if excluir_r:
        mask = np.ones(px.shape, bool)
        for ex, ey in ESTACAS:
            mask &= (px - ex) ** 2 + (py - ey) ** 2 >= excluir_r ** 2
        px, py, vals = px[mask], py[mask], vals[:, mask]      # elementos excluidos saem da interpolacao
    return px, py, vals


def gerar_todos(pasta, prefixo, saida, fator_g4=0.0, combos_elu=(11, 12, 13, 14), comb_servico=24,
                comb_vento=25, comb_freq=21):
    os.makedirs(saida, exist_ok=True)
    el = ler_elementos(os.path.join(pasta, prefixo + "_elementos.csv"), set(combos_elu) | {comb_servico, comb_freq})
    figs = {}
    f = 1 + fator_g4
    # 1) momento de calculo com tracao na face INFERIOR (envoltoria do maximo de -mxx, -myy)
    px, py, v = _env(el, list(combos_elu), lambda a: np.maximum(-a[:, 2], -a[:, 3]) * f, excluir_r=R_EST)
    gx, gy, Z = _interp_nn(px, py, v.max(axis=0))
    figs["m_inf"] = mapa(Z, gx, gy, "Momento fletor de cálculo — tração na face inferior (envoltória ELU)", "kN·m/m",
                         os.path.join(saida, "MEF_momento_inferior.png"), vmin=0, excluir_estacas_r=R_EST,
                         nota="Combinações 11 a 14, sem a parcela G4; máx(−mxx; −myy); região sobre as estacas excluída (apoio pontual)")
    # 2) momento de calculo com tracao na face SUPERIOR
    px, py, v = _env(el, list(combos_elu), lambda a: np.maximum(a[:, 2], a[:, 3]) * f, excluir_r=R_EST)
    gx, gy, Z = _interp_nn(px, py, v.max(axis=0))
    figs["m_sup"] = mapa(Z, gx, gy, "Momento fletor de cálculo — tração na face superior (envoltória ELU)", "kN·m/m",
                         os.path.join(saida, "MEF_momento_superior.png"), vmin=0, vmax=120, excluir_estacas_r=R_EST,
                         nota="Combinações 11 a 14; máx(mxx; myy); escala limitada a 120 kN·m/m; sobre as estacas: singularidade")
    # 3) mxx e myy da combinacao 14 (mapas brutos, com sinal)
    a = el[combos_elu[-1]]
    for k, nome, rot in ((2, "mxx", "Mxx"), (3, "myy", "Myy")):
        gx, gy, Z = _interp_nn(a[:, 0], a[:, 1], a[:, k] * f)
        figs[nome] = mapa(Z, gx, gy, "%s — combinação %d (ELU, vento a 45°)" % (rot, combos_elu[-1]), "kN·m/m",
                          os.path.join(saida, "MEF_%s_c%d.png" % (nome, combos_elu[-1])), simetrico=True,
                          vmin=-750, vmax=750, nota="Convenção do modelo: negativo = tração na face inferior")
    # 4) cortante de calculo |Q| (envoltoria ELU), com exclusao de d/2 + R ao redor das estacas
    px, py, v = _env(el, list(combos_elu), lambda a: np.hypot(a[:, 5], a[:, 6]) * f, excluir_r=0.81)
    gx, gy, Z = _interp_nn(px, py, v.max(axis=0))
    figs["q"] = mapa(Z, gx, gy, "Esforço cortante de cálculo |Vd| = √(Vx² + Vy²) (envoltória ELU)", "kN/m",
                     os.path.join(saida, "MEF_cortante.png"), vmin=0, vmax=600, excluir_estacas_r=0.81,
                     nota="Combinações 11 a 14, sem a parcela G4; região r < 0,81 m das estacas coberta pela punção; escala até 600 kN/m (VRd1 = 563,5)")
    # 5) recalque em servico (comb 24, reservatorio cheio)
    n = ler_nos(os.path.join(pasta, prefixo + "_nos.csv"), "uz_c%d_mm" % comb_servico)
    gx, gy, Z = _interp_nn(n[:, 0], n[:, 1], -n[:, 2])
    figs["uz"] = mapa(Z, gx, gy, "Recalque do radier — serviço, reservatório cheio (combinação %d)" % comb_servico, "mm",
                      os.path.join(saida, "MEF_recalque_c%d.png" % comb_servico), marcar_max=True,
                      nota="Valores positivos para baixo; recalque elástico do modelo")
    # 6) recalque com vento (comb 25)
    try:
        n2 = ler_nos(os.path.join(pasta, prefixo + "_nos.csv"), "uz_c%d_mm" % comb_vento)
        n24 = ler_nos(os.path.join(pasta, prefixo + "_nos.csv"), "uz_c%d_mm" % comb_servico)
        u = -(n2[:, 2] + 0.184 * (n2[:, 2] - n24[:, 2]))
        gx, gy, Z = _interp_nn(n2[:, 0], n2[:, 1], u)
        figs["uz_v"] = mapa(Z, gx, gy, "Recalque do radier — serviço com vento a 0° + G4 (combinação %d)" % comb_vento, "mm",
                            os.path.join(saida, "MEF_recalque_vento.png"), marcar_max=True,
                            nota="Inclinação do plano do costado; Δw máximo entre nós a 11,18 m = 9,65 mm")
    except KeyError:
        pass
    # 7) reacoes nas estacas (bolhas) — servico cheio e ELU maximo
    figs["reacoes"] = mapa_reacoes(os.path.join(pasta, prefixo + "_estacas.csv"), os.path.join(saida, "MEF_reacoes_estacas.png"),
                                   comb_servico, combos_elu)
    return figs


def mapa_reacoes(caminho, saida, comb_servico, combos_elu, largura_px=1500):
    serv = ler_estacas(caminho, comb_servico)
    elu = {}
    for c in combos_elu:
        for k, v in ler_estacas(caminho, c).items():
            elu[k] = max(elu.get(k, 0.0), v)
    # ordem das estacas no modelo: 1..16 = (x: -3.6,-1.2,1.2,3.6) por linha y = -3.6, -1.2, 1.2, 3.6
    pos = {}
    k = 1
    for y in (-3.6, -1.2, 1.2, 3.6):
        for x in (-3.6, -1.2, 1.2, 3.6):
            pos[k] = (x, y)
            k += 1
    margem, topo, base = 110, 90, 70
    esc = (largura_px - margem - 40) / LADO
    w_map = int(LADO * esc)
    W, H = largura_px, topo + w_map + base
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f_t, f_e, f_l = _fonte(30), _fonte(20), _fonte(18)

    def X(x):
        return margem + (x + LADO / 2) * esc

    def Y(y):
        return topo + (LADO / 2 - y) * esc

    d.rectangle([margem, topo, margem + w_map, topo + w_map], outline="black", width=3, fill=(248, 248, 248))
    r = R_RES * esc
    d.ellipse([X(0) - r, Y(0) - r, X(0) + r, Y(0) + r], outline="black", width=4)
    vmax = max(elu.values())
    for k, (x, y) in pos.items():
        rs = 0.55 * esc * math.sqrt(serv[k] / vmax)
        re = 0.55 * esc * math.sqrt(elu[k] / vmax)
        d.ellipse([X(x) - re, Y(y) - re, X(x) + re, Y(y) + re], fill=(255, 190, 120), outline=(200, 80, 0), width=2)
        d.ellipse([X(x) - rs, Y(y) - rs, X(x) + rs, Y(y) + rs], fill=(120, 170, 255), outline=(0, 60, 160), width=2)
        d.text((X(x), Y(y) - re - 8), "E%d" % k, fill="black", font=f_e, anchor="mb")
        d.text((X(x), Y(y) + re + 6), "%s | %s" % (_fmt(serv[k]), _fmt(elu[k])), fill="black", font=f_l, anchor="mt")
    for v in range(-5, 6):
        d.line([X(v), topo + w_map, X(v), topo + w_map + 8], fill="black", width=2)
        d.text((X(v), topo + w_map + 12), "%d" % v, fill="black", font=f_e, anchor="mt")
        d.line([margem - 8, Y(v), margem, Y(v)], fill="black", width=2)
        d.text((margem - 12, Y(v)), "%d" % v, fill="black", font=f_e, anchor="rm")
    d.text((margem + w_map / 2, topo + w_map + 42), "x (m)", fill="black", font=f_e, anchor="mt")
    d.text((28, topo + w_map / 2), "y (m)", fill="black", font=f_e, anchor="mm")
    d.text((margem, 22), "Reações nas estacas (kN) — serviço cheio (azul, comb. %d) | ELU máximo (laranja, comb. %s)"
           % (comb_servico, "–".join(str(c) for c in (combos_elu[0], combos_elu[-1]))), fill="black", font=f_t, anchor="lt")
    d.text((margem, 60), "Área dos círculos proporcional à reação; valores: serviço | ELU. Soma serviço = %s kN; máx. ELU = %s kN (E%d)"
           % (_fmt(sum(serv.values())), _fmt(vmax), max(elu, key=elu.get)), fill=(80, 80, 80), font=f_l, anchor="lt")
    im.save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    pasta, prefixo, saida = sys.argv[1], sys.argv[2], sys.argv[3]
    for k, v in gerar_todos(pasta, prefixo, saida).items():
        print(k, "->", v)
