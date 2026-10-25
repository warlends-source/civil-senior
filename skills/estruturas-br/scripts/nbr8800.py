"""NBR 8800:2008 - verificacoes basicas de aco (perfis laminados/soldados).

Unidades: kN, cm, kN/cm2 (MPa/10). Entradas de esforco = VALORES DE CALCULO.
gamma_a1 = 1,10 (escoamento/instabilidade); gamma_a2 = 1,35 (ruptura).
Cobertura: tracao, compressao (FLEXAO nao-esbelta, Q informado), momento resistente
simplificado (secao compacta, travada), cortante (alma sem esbeltez excessiva),
interacao N+M (5.5.1.2). NAO cobre: FLT/FLM/FLA gerais, flexo-torcional, ligacoes,
fadiga, ELS. Ver references/normas.md.
"""
from math import pi, sqrt

GA1 = 1.10
GA2 = 1.35
E = 20000.0      # kN/cm2


def tracao(Ag, Ae, fy, fu):
    """Ag, Ae (area liquida efetiva) em cm2; fy, fu em kN/cm2."""
    esc = Ag * fy / GA1
    rup = Ae * fu / GA2
    return {"norma": "NBR 8800 5.2.2", "Nt_Rd_escoamento_kN": esc,
            "Nt_Rd_ruptura_kN": rup, "Nt_Rd_kN": min(esc, rup)}


def compressao(Ag, fy, I, KL, Q=1.0):
    """I em cm4 (eixo de flambagem), KL em cm, Q (6.x/Anexo F) - 1,0 se sem flambagem local."""
    Ne = pi ** 2 * E * I / KL ** 2
    l0 = sqrt(Q * Ag * fy / Ne)
    chi = 0.658 ** (l0 ** 2) if l0 <= 1.5 else 0.877 / l0 ** 2
    Nrd = chi * Q * Ag * fy / GA1
    return {"norma": "NBR 8800 5.3", "Ne_kN": Ne, "lambda0": l0, "chi": chi,
            "Nc_Rd_kN": Nrd,
            "avisos": ["Verificar flambagem flexo-torcional (Anexo E) e Q (Anexo F) separadamente"]}


def momento_simplificado(Zx, Wx, fy):
    """SO vale para secao compacta (FLA/FLM) e Lb <= Lp. Confirme antes de usar."""
    Mpl = Zx * fy
    Mrd = min(Mpl, 1.5 * Wx * fy) / GA1
    return {"norma": "NBR 8800 5.4.2.2 (MRd = Mpl/gama_a1)", "Mpl_kNcm": Mpl,
            "M_Rd_kNcm": Mrd, "M_Rd_kNm": Mrd / 100.0,
            "avisos": ["Premissas: secao compacta e contencao lateral Lb<=Lp (nao verificado aqui)"]}


def cortante(Aw, h_tw, fy, kv=5.0):
    """Aw = d*tw (cm2); h_tw = h/tw da alma. Valido para lambda <= lambda_p."""
    lp = 1.10 * sqrt(kv * E / fy)
    if h_tw > lp:
        raise NotImplementedError("h/tw=%.1f > lambda_p=%.1f: usar 5.4.3.1.1 (inelastico/elastico)" % (h_tw, lp))
    Vpl = 0.6 * Aw * fy
    return {"norma": "NBR 8800 5.4.3", "lambda_p": lp, "Vpl_kN": Vpl, "V_Rd_kN": Vpl / GA1}


def interacao_NM(Nsd, Nrd, Mxsd, Mxrd, Mysd=0.0, Myrd=1.0):
    """NBR 8800 5.5.1.2 (equacoes de interacao para flexo-compressao/tracao)."""
    r = Nsd / Nrd
    soma_m = Mxsd / Mxrd + Mysd / Myrd
    util = r + 8.0 / 9.0 * soma_m if r >= 0.2 else r / 2.0 + soma_m
    return {"norma": "NBR 8800 5.5.1.2", "Nsd_Nrd": r, "utilizacao": util, "ok": util <= 1.0}
