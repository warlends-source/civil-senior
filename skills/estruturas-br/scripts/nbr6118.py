"""NBR 6118:2023 (formulas conferidas tambem com a :2014) - verificacoes basicas de concreto armado (secao retangular).

Unidades: forcas kN, momentos kN.m, comprimentos m, resistencias em MPa (entrada).
Todos os esforcos de entrada sao VALORES DE CALCULO (Md, Vsd ja majorados por gama_f).
Saidas incluem 'avisos' - o engenheiro responsavel deve revisar. Nao substitui o projeto.

Cobertura: flexao simples (armadura simples/dupla), cisalhamento (modelo I),
armadura minima/maxima de flexao. NAO cobre: torcao, flexao composta, ELS (fissuracao,
flecha), punçao, pilares esbeltos, ancoragem/detalhamento. Ver references/normas.md.
"""
from math import sqrt

GAMMA_C = 1.4   # NBR 6118 tab. 12.1 - combinacao normal
GAMMA_S = 1.15
ES = 210000.0   # MPa, aco CA-50/60

# NBR 6118 tab. 17.3 - taxa minima de armadura longitudinal (%), secao retangular, CA-50
_RHO_MIN = {20: 0.150, 25: 0.150, 30: 0.150, 35: 0.164, 40: 0.179,
            45: 0.194, 50: 0.208}


def _lambda_alfac(fck):
    """lambda (altura do bloco) e alfa_c (NBR 6118 8.2.10.1 / 17.2.2)."""
    if fck <= 50:
        return 0.8, 0.85
    return 0.8 - (fck - 50) / 400.0, 0.85 * (1 - (fck - 50) / 200.0)


def flexao_retangular(Md, bw, h, d, fck, fyk=500.0, dlinha=0.05):
    """Dimensiona armadura longitudinal. Md em kN.m; bw, h, d, dlinha em m."""
    avisos = []
    if fck > 90:
        raise ValueError("fck > 90 MPa fora do escopo da NBR 6118")
    lam, ac = _lambda_alfac(fck)
    fcd = fck / GAMMA_C * 1000.0          # kPa
    fyd = fyk / GAMMA_S * 1000.0          # kPa
    eyd = fyk / GAMMA_S / ES
    xi_lim = 0.45 if fck <= 50 else 0.35  # NBR 6118 14.6.4.3

    mu = Md / (ac * fcd * bw * d * d)
    # Md = ac*fcd*bw*d^2 * lam*xi*(1-lam*xi/2)  ->  xi
    disc = 1 - 2 * mu
    if disc < 0:
        raise ValueError("Secao insuficiente mesmo com armadura dupla: aumente bw/h/fck")
    xi = (1 - sqrt(disc)) / lam

    if xi <= xi_lim:
        x = xi * d
        z = d - lam * x / 2
        As = Md / (fyd * z)
        Asl = 0.0
    else:
        avisos.append("xi=%.3f > %.2f: armadura dupla (ductilidade, NBR 6118 14.6.4.3)" % (xi, xi_lim))
        x = xi_lim * d
        Mlim = ac * fcd * bw * x * lam * (d - lam * x / 2)
        dM = Md - Mlim
        eps_sl = 0.0035 * (1 - dlinha / x)
        sig_sl = min(ES * eps_sl, fyk / GAMMA_S) * 1000.0
        if eps_sl <= 0:
            raise ValueError("d' maior que x: armadura de compressao inviavel")
        Asl = dM / (sig_sl * (d - dlinha))
        As = Mlim / (fyd * (d - lam * x / 2)) + dM / (fyd * (d - dlinha))
        xi = xi_lim

    # armadura minima (tab. 17.3) e maxima (17.3.5.2.4: 4% Ac)
    chaves = sorted(_RHO_MIN)
    fck_ref = next((k for k in chaves if k >= fck), chaves[-1])
    if fck > 50:
        avisos.append("fck>50: As,min da tab. 17.3 nao implementada, usar valor da norma")
    if fyk != 500:
        avisos.append("As,min tabelada para CA-50; conferir para fyk=%s" % fyk)
    As_min = _RHO_MIN[fck_ref] / 100.0 * bw * h
    As_max = 0.04 * bw * h
    As_adot = max(As, As_min)
    if As_adot > As_max:
        avisos.append("As > 4%% Ac (As,max): revisar secao")
    return {
        "norma": "NBR 6118:2023 17.2",
        "fcd_MPa": fck / GAMMA_C, "fyd_MPa": fyk / GAMMA_S,
        "mu": mu, "xi": xi, "x_m": xi * d,
        "As_calc_cm2": As * 1e4, "As_min_cm2": As_min * 1e4,
        "As_adotada_cm2": As_adot * 1e4, "As_comprimida_cm2": Asl * 1e4,
        "avisos": avisos,
    }


def vrd1_laje(d, As1, fck, bw=1.0, sigma_cp_MPa=0.0):
    """Cortante resistente de laje/radier SEM armadura transversal (por metro de largura).
    NBR 6118:2023 item 19.4.1: VRd1 = tauRd*k*(1,2+40*rho1)+0,15*sigma_cp)*bw*d
    tauRd = 0,25*fctd; k = |1,6 - d| (d em m), k >= 1; rho1 = As1/(bw*d) <= 0,02.
    d, bw em m; As1 em m2 (por bw). Retorna kN (por bw). Conferido com o memorial
    exemplo de referencia (radier estaqueado C45) (563,5 kN/m para d=0,92 m, As=20,94 cm2/m, C45)."""
    fctm = 0.3 * fck ** (2.0 / 3.0)
    fctd = 0.7 * fctm / GAMMA_C                                   # MPa
    tau = 0.25 * fctd * 1000.0                                     # kPa
    k = max(abs(1.6 - d), 1.0)
    rho1 = min(As1 / (bw * d), 0.02)
    v = tau * k * (1.2 + 40 * rho1) + 0.15 * sigma_cp_MPa * 1000.0
    return {"norma": "NBR 6118:2023 19.4.1", "tauRd_MPa": tau / 1000.0, "k": k,
            "rho1": rho1, "VRd1_kN": v * bw * d,
            "avisos": ["Vale para lajes/radiers sem armadura transversal; punçao verificada a parte"]}


def cisalhamento_modelo1(Vsd, bw, d, fck, fywk=500.0, gamma_c=GAMMA_C):
    """Estribos verticais, modelo I (theta=45). Vsd em kN; retorna Asw/s em cm2/m."""
    avisos = []
    if fck > 90:
        raise ValueError("fck > 90 MPa fora do escopo")
    alfa_v2 = 1 - fck / 250.0
    fcd = fck / gamma_c * 1000.0
    VRd2 = 0.27 * alfa_v2 * fcd * bw * d
    fctm = 0.3 * fck ** (2.0 / 3.0) if fck <= 50 else 2.12 * __import__("math").log(1 + 0.11 * fck)
    fctk_inf = 0.7 * fctm
    fctd = fctk_inf / gamma_c * 1000.0    # kPa
    Vc0 = 0.6 * fctd * bw * d
    fywd = min(fywk / GAMMA_S, 435.0) * 1000.0
    ok = Vsd <= VRd2
    if not ok:
        avisos.append("Vsd > VRd2: ruina da biela comprimida - aumentar secao/fck")
    asw_s = max(Vsd - Vc0, 0.0) / (0.9 * d * fywd)                  # m2/m
    asw_min = 0.2 * fctm / fywk * bw                                  # m2/m (17.4.1.1.1)
    avisos.append("Vc=Vc0 valido p/ flexao simples; em tracao/compressao outro Vc")
    return {
        "norma": "NBR 6118:2023 17.4.2.2",
        "VRd2_kN": VRd2, "Vc_kN": Vc0, "biela_ok": ok,
        "Asw_s_calc_cm2_m": asw_s * 1e4, "Asw_s_min_cm2_m": asw_min * 1e4,
        "Asw_s_adotada_cm2_m": max(asw_s, asw_min) * 1e4, "avisos": avisos,
    }


# ---------------------------------------------------------------------------
# PUNCAO em estaca/pilar circular de canto - NBR 6118:2023 item 19.5
# ---------------------------------------------------------------------------
from math import asin, cos, pi, sin  # noqa: E402


def contorno_punçao_canto(R_pilar, d, ax, ay, n=20000):
    """Contorno critico C' a 2d da face de pilar circular de CANTO, truncado pelas bordas
    livres a distancias ax, ay (m) do eixo. Retorna u (m), area interna (m2) e Wp (m2, por
    direcao). Wp = integral de |e| dl em relacao ao eixo do pilar. Conferido com o memorial
    (R=0,35 m, d=0,935 m, ax=ay=1,40 m -> u=6,517; A=11,61; Wp=9,14)."""
    R = R_pilar + 2 * d
    if ax >= R or ay >= R:
        raise ValueError("Pilar nao e de canto: borda livre alem do contorno (usar caso de borda/interno)")
    t0 = -asin(ay / R)                       # inicio do arco (y = -ay)
    t1 = pi / 2 + asin(ax / R)               # fim do arco (x = -ax)
    u = R * (t1 - t0)
    # |x| integrado: R^2 * int |cos t| dt  (idem em y por simetria quando ax=ay)
    def integ_abs(f_prim, a, b, zeros):
        pts = [a] + [z for z in zeros if a < z < b] + [b]
        return sum(abs(f_prim(q) - f_prim(p)) for p, q in zip(pts[:-1], pts[1:]))
    wpx = R * R * integ_abs(sin, t0, t1, [pi / 2])
    wpy = R * R * integ_abs(lambda t: -cos(t), t0, t1, [0.0])
    # area: regiao {x >= -ax, y >= -ay} dentro do circulo de raio R (integracao numerica)
    h = (R + ax) / n
    area = 0.0
    for i in range(n):
        x = -ax + (i + 0.5) * h
        if x > R:
            break
        ymax = (R * R - x * x) ** 0.5
        # limite superior: circulo (ou y=+ymax); inferior: y=-ay ou o proprio circulo
        area += (ymax + min(ay, ymax)) * h
    return {"R_contorno_m": R, "u_m": u, "area_interna_m2": area, "Wp_x_m2": wpx, "Wp_y_m2": wpy}


def puncao_verificacao(FSd, MSd1, MSd2, u, Wp1, Wp2, d, fck, rho, K=0.6):
    """tau_Sd no contorno C' x tau_Rd1 (sem armadura de puncao). Unidades: kN, kN.m, m.
    tau_Sd = FSd/(u d) + K1*MSd1/(Wp1 d) + K2*MSd2/(Wp2 d)       (19.5.2.1)
    tau_Rd1 = 0,13*(1+sqrt(20/d_cm))*(100*rho*fck)^(1/3)  [MPa]  (19.5.3.1)
    rho = sqrt(rho_x*rho_y) <= 0,02. FSd e a forca LIQUIDA no contorno (reacao da estaca +
    reacao do solo interna - cargas aplicadas internas), fornecida pelo engenheiro."""
    avisos = ["FSd e momentos sao entradas: a skill nao calcula a forca liquida no contorno",
              "K=0,6 (pilar circular de canto/borda conforme adotado no memorial); conferir tab. da norma"]
    tau_sd = FSd / (u * d) + K * MSd1 / (Wp1 * d) + K * MSd2 / (Wp2 * d)        # kPa
    rho = min(rho, 0.02)
    tau_rd1 = 0.13 * (1 + sqrt(20.0 / (d * 100.0))) * (100 * rho * fck) ** (1.0 / 3.0)  # MPa
    alfa_v = 1 - fck / 250.0
    tau_rd2 = 0.27 * alfa_v * fck / GAMMA_C                                          # MPa
    return {"norma": "NBR 6118:2023 19.5", "tau_Sd_kPa": tau_sd, "tau_Rd1_MPa": tau_rd1,
            "tau_Rd2_MPa": tau_rd2, "relacao_Rd1": tau_sd / 1000.0 / tau_rd1,
            "ok_sem_armadura": tau_sd / 1000.0 <= tau_rd1, "avisos": avisos}


# ---------------------------------------------------------------------------
# ELS-W: abertura de fissuras em laje/radier - NBR 6118:2023 17.3.3.2
# ---------------------------------------------------------------------------
def modulo_ecs(fck, alfa_e=1.0):
    """Ecs (MPa) = alfa_i * Eci; Eci = alfa_E*5600*sqrt(fck); alfa_i = 0,8+0,2*fck/80 (<=1)."""
    eci = alfa_e * 5600.0 * sqrt(fck)
    return min(0.8 + 0.2 * fck / 80.0, 1.0) * eci


def fissuracao_laje(Mk, d, As_cm2_m, phi_mm, cob_cm, esp_cm, fck, wk_lim=0.30, eta1=2.25,
                    b_cm=100.0, Es=210000.0, alfa_e_agregado=1.0):
    """wk para flexao simples, estadio II, secao retangular de largura b (padrao 1 m).
    Mk em kN.m/m (combinacao frequente), d em m, As em cm2/m, phi/cob/esp em mm/cm/cm.
    sigma_s via estadio II; wk = min(w1, w2) (formulas 17.3.3.2).
    Regiao de envolvimento Acri = min(esp, 15*phi) x (cob + phi/2 + 7,5*phi) [NBR 6118 17.3.3.2]."""
    phi_cm = phi_mm / 10.0
    d_cm = d * 100.0
    ecs = modulo_ecs(fck, alfa_e_agregado)
    ae = Es / ecs
    k = ae * As_cm2_m * (b_cm / 100.0)                 # alfa_e*As na largura b
    x = (-k + sqrt(k * k + 2 * b_cm * k * d_cm)) / b_cm   # b x^2/2 = k (d-x)
    I2 = b_cm * x ** 3 / 3.0 + k * (d_cm - x) ** 2
    sig_s = ae * (Mk * 100.0) * (d_cm - x) / I2 * 10.0   # kN/cm2 -> MPa
    fctm = 0.3 * fck ** (2.0 / 3.0)
    As_barra = pi * phi_cm ** 2 / 4.0
    larg = min(esp_cm, 15 * phi_cm)
    alt = cob_cm + phi_cm / 2 + 7.5 * phi_cm
    rho_ri = As_barra / (larg * alt)
    f = phi_mm / (12.5 * eta1) * sig_s / Es
    w1 = f * 3 * sig_s / fctm
    w2 = f * (4.0 / rho_ri + 45)
    wk = min(w1, w2)
    avisos = ["Estadio II sem tension stiffening; Mk da combinacao frequente fornecido pelo usuario",
              "eta1=2,25 vale para barras nervuradas (CA-50)"]
    if sig_s > 0.8 * 500 / GAMMA_S:
        avisos.append("sigma_s alto: conferir estado limite de deformacao excessiva")
    return {"norma": "NBR 6118:2023 17.3.3.2", "alfa_e": ae, "Ecs_MPa": ecs, "x_cm": x,
            "sigma_s_MPa": sig_s, "rho_ri": rho_ri, "wk1_mm": w1, "wk2_mm": w2, "wk_mm": wk,
            "wk_lim_mm": wk_lim, "relacao": wk / wk_lim, "ok": wk <= wk_lim, "avisos": avisos}


# ---------------------------------------------------------------------------
# MOMENTO RESISTENTE de laje/radier (armadura simples) - NBR 6118:2023 17.2
# ---------------------------------------------------------------------------
def momento_resistente(As_cm2_m, d, fck, bw=1.0, fyk=500.0):
    """MRd (kN.m por bw) com armadura simples. d, bw em m; As em cm2 por bw.
    Conferido com o memorial 91101: As=20,94 cm2/m, d=0,92 m, C45 -> 822,4 kN.m/m."""
    lam, ac = _lambda_alfac(fck)
    fcd = fck / GAMMA_C * 1000.0
    fyd = fyk / GAMMA_S * 1000.0
    As = As_cm2_m * 1e-4
    x = As * fyd / (ac * lam * fcd * bw)
    xi = x / d
    xi_lim = 0.45 if fck <= 50 else 0.35
    avisos = []
    if xi > xi_lim:
        avisos.append("x/d=%.3f > %.2f: ductilidade (armadura dupla ou aumentar secao)" % (xi, xi_lim))
    return {"norma": "NBR 6118:2023 17.2", "x_m": x, "xi": xi, "MRd_kNm": As * fyd * (d - lam * x / 2),
            "avisos": avisos}


def as_minima_laje(fck, h, bw=1.0, bidirecional_positivo=True):
    """As,min (cm2) tab. 17.3 (CA-50). Para lajes armadas nas duas direcoes, o momento
    positivo admite 0,67*rho_min (17.3.5.2.1)."""
    chaves = sorted(_RHO_MIN)
    ref = next((k for k in chaves if k >= fck), chaves[-1])
    f = 0.67 if bidirecional_positivo else 1.0
    return f * _RHO_MIN[ref] / 100.0 * bw * h * 1e4


# ---------------------------------------------------------------------------
# FLEXAO COMPOSTA de secao circular (estaca) - diagrama de interacao por integracao
# NBR 6118:2023 17.2 (blocos retangulares) - Ver notas de validacao abaixo.
# ---------------------------------------------------------------------------
def _area_segmento_circ(R, y_lim):
    """Area do segmento circular acima de y = y_lim (eixo y para a fibra comprimida), -R<=y_lim<=R."""
    from math import acos
    y = max(-R, min(R, y_lim))
    return R * R * acos(y / R) - y * sqrt(max(R * R - y * y, 0.0))


def _mom_segmento_circ(R, y_lim):
    """Momento estatico da area do segmento acima de y_lim em relacao ao centro: (2/3)(R^2-y^2)^1.5."""
    y = max(-R, min(R, y_lim))
    return (2.0 / 3.0) * max(R * R - y * y, 0.0) ** 1.5


def interacao_circular(D, n_barras, phi_mm, R_barras, fcd_MPa, fyd_MPa=434.8, Es=210000.0,
                       ecu=0.0035, lam=0.8, alfa_c=0.85, n_pontos=400, fase_graus=0.0,
                       desconta_concreto=False):
    """Diagrama de interacao N-M (compressao positiva) de estaca circular de diametro D (m)
    com n_barras de phi_mm igualmente espacadas no raio R_barras (m), flexao em torno de um diametro.
    fcd_MPa e ENTRADA (para estaca escavada o memorial 91101 usa 8,0 MPa = fck 40 / gamma_c 5,0,
    segundo a tabela de estacas moldadas in loco da NBR 6122 - conferir na edicao vigente).
    Retorna lista de (N_kN, M_kNm) do ramo de maior excentricidade ate a compressao pura."""
    R = D / 2.0
    As1 = pi * (phi_mm / 1000.0) ** 2 / 4.0                           # m2 por barra
    fcd = fcd_MPa * 1000.0                                            # kPa
    fyd = fyd_MPa * 1000.0
    ys = [R_barras * cos(2 * pi * i / n_barras + fase_graus * pi / 180.0) for i in range(n_barras)]   # posicao (a partir do centro, + = comprimida)
    pts = []
    # profundidade da LN medida a partir da fibra mais comprimida (y = +R): x de ~0 a 4D
    for k in range(1, n_pontos + 1):
        x = (4.0 * D) * (k / n_pontos) ** 2 + 1e-6
        ytop = R
        # deformacao: eps(y) = ecu * (x - (ytop - y)) / x   (compressao +); limite de 2% na tracao
        Nc = Mc = 0.0
        a = lam * x
        y_lim = ytop - a                                              # bloco comprimido: y >= y_lim
        if x >= D / lam:                                              # bloco cobre toda a secao
            A = pi * R * R
            Nc = alfa_c * fcd * A
            Mc = 0.0
        else:
            A = _area_segmento_circ(R, y_lim)
            Nc = alfa_c * fcd * A
            Mc = alfa_c * fcd * _mom_segmento_circ(R, y_lim)
        Ns = Ms = 0.0
        for y in ys:
            eps = ecu * (x - (ytop - y)) / x
            eps = max(min(eps, ecu), -0.010)
            sig = max(min(Es * eps, fyd), -fyd) * 1000.0 / 1000.0     # MPa -> ja em MPa; converter abaixo
            sig_kPa = max(min(Es * eps, fyd_MPa), -fyd_MPa) * 1000.0
            # desconta o concreto deslocado pela barra se comprimida dentro do bloco
            if desconta_concreto and y >= y_lim:
                sig_kPa -= alfa_c * fcd
            F = sig_kPa * As1
            Ns += F
            Ms += F * y
        pts.append(((Nc + Ns), (Mc + Ms)))
    return pts


def momento_resistente_circular(Nd, D, n_barras, phi_mm, R_barras, fcd_MPa, **kw):
    """MRd (kN.m) para o Nd dado (compressao +), interpolando o diagrama de interacao."""
    pts = interacao_circular(D, n_barras, phi_mm, R_barras, fcd_MPa, **kw)
    pts = sorted(pts, key=lambda p: p[0])
    for (n1, m1), (n2, m2) in zip(pts[:-1], pts[1:]):
        if n1 <= Nd <= n2:
            t = (Nd - n1) / (n2 - n1) if n2 != n1 else 0.0
            return m1 + t * (m2 - m1)
    raise ValueError("Nd=%.0f fora do diagrama (Nmin=%.0f, Nmax=%.0f kN)" % (Nd, pts[0][0], pts[-1][0]))


def verificar_estaca(Nd, Md, Hd, D, n_barras, phi_mm, R_barras, fck, gamma_c_estaca, cob_ate_eixo_barra=None):
    """Verificacao estrutural da estaca circular (flexao composta + tensao media + rho_min + cortante).
    Nd (kN, compressao +), Md (kN.m), Hd (kN): valores de calculo na cabeca da estaca.
    fcd = fck/gamma_c_estaca. O memorial 91101 usa gamma_c=5,0 (tabela de estacas moldadas in loco
    da NBR 6122, estaca escavada sem fluido) -> fcd=8,0 MPa para C40. CONFERIR na edicao vigente.
    MRd: integracao numerica, barra no eixo de flexao e SEM descontar o concreto deslocado
    (reproduz o memorial: 351,3 kN.m). Orientacao a 22,5 graus e desconto do concreto deslocado
    reduzem MRd em ~1,4 % e ~0,5 %; ambos sao reportados em 'MRd_conservador_kNm'."""
    fcd = fck / gamma_c_estaca
    Ac = pi * D * D / 4.0
    As = n_barras * pi * (phi_mm / 1000.0) ** 2 / 4.0
    mrd = momento_resistente_circular(Nd, D, n_barras, phi_mm, R_barras, fcd)
    mrd_cons = momento_resistente_circular(Nd, D, n_barras, phi_mm, R_barras, fcd,
                                           fase_graus=180.0 / n_barras, desconta_concreto=True)
    sig_med = Nd / Ac / 1000.0                                   # MPa
    rho = As / Ac
    # cortante (NAO conferido com o memorial): bw=D, d=0,9D (simplificacao usual para secao circular)
    cs = cisalhamento_modelo1(Hd, D, 0.9 * D, fck, gamma_c=gamma_c_estaca)
    avisos = ["Cortante da estaca: bw=D e d=0,9D (simplificacao); o memorial 91101 nao o apresenta",
              "Md e Hd na cabeca vem do modelo de viga sobre molas CRH; esta funcao nao os calcula"]
    if rho < 0.004:
        avisos.append("rho=%.2f %% < 0,40 %% (armadura minima da tabela de estacas da NBR 6122)" % (rho * 100))
    return {"norma": "NBR 6118:2023 17.2 / NBR 6122:2019", "fcd_MPa": fcd, "rho": rho,
            "sigma_media_MPa": sig_med, "MRd_kNm": mrd, "Md_MRd": Md / mrd,
            "MRd_conservador_kNm": mrd_cons, "Md_MRd_conservador": Md / mrd_cons,
            "ok": Md <= mrd and rho >= 0.004,
            "VRd2_kN": cs["VRd2_kN"], "Vc_kN": cs["Vc_kN"], "cortante_ok": Hd <= cs["VRd2_kN"],
            "avisos": avisos}


# ---------------------------------------------------------------------------
# PUNCAO - forca liquida no contorno C' de estaca qualquer (radier estaqueado sob reservatorio)
# ---------------------------------------------------------------------------
def geometria_contorno(x, y, R_pilar, d, lado=10.0, R_res=3.82, n=600):
    """Para a estaca em (x, y) [m, origem no centro do radier quadrado de 'lado'] e contorno C' de
    raio R = R_pilar + 2d, retorna: area interna no radier (m2), area interna sob a base do
    reservatorio (circulo R_res, m2) e comprimento do costado (circunferencia R_res) dentro do
    contorno (m). Integracao numerica por malha n x n. Conferido com o memorial 91101 (E16:
    A=11,61 m2; base=2,04 m2; costado=3,18 m)."""
    from math import hypot, atan2, pi as _pi
    R = R_pilar + 2 * d
    h = lado / 2.0
    x0, x1 = max(x - R, -h), min(x + R, h)
    y0, y1 = max(y - R, -h), min(y + R, h)
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    A = Ab = 0.0
    for i in range(n):
        px = x0 + (i + 0.5) * dx
        for j in range(n):
            py = y0 + (j + 0.5) * dy
            if (px - x) ** 2 + (py - y) ** 2 <= R * R:
                A += dx * dy
                if px * px + py * py <= R_res * R_res:
                    Ab += dx * dy
    # costado: arco da circunferencia R_res dentro do contorno
    m = 20000
    Lc = 0.0
    for k in range(m):
        t = 2 * _pi * (k + 0.5) / m
        px, py = R_res * cos(t), R_res * sin(t)
        if (px - x) ** 2 + (py - y) ** 2 <= R * R and abs(px) <= h and abs(py) <= h:
            Lc += R_res * 2 * _pi / m
    return A, Ab, Lc


def forca_liquida_puncao(Rest, p_solo, A, Ab, Lc, g1=25.0, q_agua=256.22, g3=61.38, q1=2.87,
                         f_perm=1.4, f_var=0.98):
    """FSd = reacao da estaca + p_solo*A - cargas aplicadas no interior do contorno (kN), com os
    coeficientes do memorial (1,4 para G1, G2+, G3 e 0,98 para a sobrecarga linear Q1)."""
    cargas = f_perm * (g1 * A + q_agua * Ab + g3 * Lc) + f_var * q1 * Lc
    return Rest + p_solo * A - cargas, cargas
