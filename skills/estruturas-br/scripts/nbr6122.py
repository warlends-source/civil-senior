"""NBR 6122:2019 - capacidade de carga de estacas por Decourt-Quaresma (1978/1982).

Convencao do TQS/SISE (usada no memorial 91101): forcas em tf com tf = kN/10 na parcela lateral
e C em tf/m2. Aqui ha DUAS saidas de Padm em kN:
  - padm_kN_memorial  = Padm[tf] * 9,80665  (como o memorial converte: 124,3 tf -> 1.219 kN)
  - padm_kN_estrito   = Padm[tf] * 10       (D-Q em kPa/kN, coerente com C=120 kPa)
A diferenca (~1,9 %) favorece a seguranca no memorial; o engenheiro decide qual adotar.

Formulas (D-Q):
  PP = alfa * C * Np * Ap                      Np = media do SPT na ponta, imediatamente acima e abaixo
  PL = beta * 10 * (NL/3 + 1) * U * L          NL = media do SPT ao longo do fuste (3 <= N <= 50)
  Padm = menor(Pult/CS, PL/1,3 + PP/4)         CS = 2,0
Limitacao RP <= RL para estaca escavada (NBR 6122, citada no memorial 91101): PP_efetivo = min(PP, PL).
Coeficientes alfa/beta/C dependem do tipo de estaca e do solo: SAO ENTRADAS (memorial: escavada em
argila, alfa=0,85, beta=0,80, C=12 tf/m2). Conferir as tabelas na edicao vigente.

Cobertura: so Decourt-Quaresma. Aoki-Velloso, Antunes-Cabral e Velloso: NAO implementados.
Validado com a SP 01 e o exemplo de referencia (radier estaqueado C45) (estaca de 8 m, D=70 cm).
"""
from math import pi

G = 9.80665


def decourt_quaresma(spt, D, L, alfa, beta, C_tf_m2, cs=2.0, limitar_pp_pl=True,
                     nl_niveis=None):
    """spt: dict {nivel_m: NSPT} onde nivel k = k metros abaixo da CABECA da estaca (1, 2, ...).
    Deve conter os niveis 1..L e, para a media de ponta, L-1, L e L+1 (se faltar L+1, usa o que ha).
    nl_niveis: lista de niveis para NL; padrao = 1..L (como o TQS, que inclui os da ponta).
    D (m) diametro, L (m) comprimento. SPT de nega: informar 50 (convencao do memorial)."""
    niveis = nl_niveis or list(range(1, int(round(L)) + 1))
    n_fuste = [min(max(spt[k], 3), 50) for k in niveis]          # D-Q: 3 <= N <= 50
    NL = sum(n_fuste) / len(n_fuste)
    pont = [spt[k] for k in (int(round(L)) - 1, int(round(L)), int(round(L)) + 1) if k in spt]
    Np = sum(pont) / len(pont)
    U = pi * D
    Ap = pi * D * D / 4.0
    PP = alfa * C_tf_m2 * Np * Ap                                  # tf
    PL = beta * (NL / 3.0 + 1.0) * U * L                           # tf  (= beta*10*(..)*U*L kN / 10)
    avisos = []
    PPe = PP
    if limitar_pp_pl and PP > PL:
        PPe = PL
        avisos.append("PP > PL: ponta limitada a PL (RP <= RL, estaca escavada)")
    Pult = PL + PPe
    padm = min(Pult / cs, PL / 1.3 + PPe / 4.0)
    avisos.append("Convencao TQS (tf = kN/10 no atrito): padm_kN_estrito = 10*tf; memorial usa 9,80665*tf")
    if any(k not in spt for k in niveis):
        avisos.append("Niveis ausentes no SPT")
    return {"norma": "NBR 6122:2019 / Decourt-Quaresma", "NL": NL, "Np": Np, "PL_tf": PL, "PP_tf": PP,
            "PP_efetivo_tf": PPe, "Pult_tf": Pult, "Pult_cs_tf": Pult / cs,
            "PL13_PP4_tf": PL / 1.3 + PPe / 4.0, "Padm_tf": padm,
            "padm_kN_memorial": padm * G, "padm_kN_estrito": padm * 10.0, "avisos": avisos}


def fs_global_sistema(n_estacas, Pult_tf, Nk_kN, g=G):
    """FS global desprezando o radier (memorial 11.1.3): n*Pult*g / Nk >= 2,0."""
    return n_estacas * Pult_tf * g / Nk_kN
