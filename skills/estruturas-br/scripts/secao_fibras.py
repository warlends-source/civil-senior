"""Analise de secao circular de concreto armado por FIBRAS (tensao real nas barras).

Estado-limite ultimo de projeto: concreto parabola-retangulo (0,85 fcd; eps_c2 = 2,0 permil; eps_cu = 3,5 permil),
aco elastoplastico (Es = 210 GPa; fyd). Para (Nd, Md) de calculo, resolve o plano de deformacoes (eps0, curvatura)
que equilibra N e M e devolve a tensao de cada barra (tracao +). Compressao e positiva no concreto/esforco normal.
Usa numpy. Unidades: kN, m, MPa.
"""
import numpy as np


def _tensao_concreto(eps, fcd):
    """MPa; compressao positiva; sem resistencia a tracao."""
    e = np.clip(eps, 0.0, 0.0035)
    sig = np.where(e <= 0.002, 0.85 * fcd * (1 - (1 - e / 0.002) ** 2), 0.85 * fcd)
    return np.where(eps <= 0, 0.0, sig)


def analisa(Nd, Md, D, n_barras, phi_mm, R_barras, fcd, fyd=434.78, Es=210000.0, ng=160, fase_graus=0.0):
    """Retorna dict com eps0, curvatura, tensoes das barras (MPa, tracao negativa = compressao como convencao do aco:
    aqui 'sig_barra' > 0 compressao, < 0 tracao) e a tensao maxima de tracao."""
    R = D / 2.0
    xs = (np.arange(ng) + 0.5) / ng * D - R              # coordenadas y das fatias (y + = fibra mais comprimida)
    dy = D / ng
    larg = 2 * np.sqrt(np.maximum(R * R - xs * xs, 0.0))
    area_f = larg * dy                                    # m2
    th = 2 * np.pi * np.arange(n_barras) / n_barras + np.deg2rad(fase_graus)
    yb = R_barras * np.cos(th)
    Ab = n_barras * np.pi * (phi_mm / 1000.0) ** 2 / 4.0 / n_barras

    def esforcos(eps0, kap):
        ec = eps0 + kap * xs                              # deformacao (compressao +), y medido do centro
        sc = _tensao_concreto(ec, fcd)
        N = np.sum(sc * area_f) * 1000.0                  # kN (MPa * m2 * 1000)
        M = np.sum(sc * area_f * xs) * 1000.0
        eb = eps0 + kap * yb
        sb = np.clip(Es * eb, -fyd, fyd)                  # MPa; compressao +
        # desconta concreto deslocado pela barra (compressao)
        sb_liq = sb - np.where(eb > 0, _tensao_concreto(eb, fcd), 0.0)
        N += np.sum(sb_liq * Ab) * 1000.0
        M += np.sum(sb_liq * Ab * yb) * 1000.0
        return N, M, sb

    # busca: para cada curvatura, eps0 que da N = Nd (monotono); depois curvatura que da M = Md
    def eps0_para_N(kap):
        lo, hi = -0.02, 0.0035 + abs(kap) * R
        for _ in range(70):
            mid = (lo + hi) / 2
            if esforcos(mid, kap)[0] < Nd:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    klo, khi = 0.0, 0.0035 / (0.05 * D)                   # curvatura ate topo a 3,5 permil com LN a 5 % do diametro
    for _ in range(60):
        km = (klo + khi) / 2
        e0 = eps0_para_N(km)
        N, M, _s = esforcos(e0, km)
        if M < Md:
            klo = km
        else:
            khi = km
    kap = (klo + khi) / 2
    e0 = eps0_para_N(kap)
    N, M, sb = esforcos(e0, kap)
    return {"eps0": e0, "curvatura": kap, "N": N, "M": M, "sig_barras": sb,
            "sig_tracao_max": float(max(0.0, -sb.min())), "sig_compressao_max": float(max(0.0, sb.max())),
            "eps_topo": float(e0 + kap * R)}
