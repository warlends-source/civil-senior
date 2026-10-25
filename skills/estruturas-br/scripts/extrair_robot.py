"""Extrai dados do Robot (aberto) para JSON. SOMENTE LEITURA.

Uso:  python extrair_robot.py [saida.json]
Requer: Robot aberto com projeto calculado, pywin32.
Unidades: o Robot devolve valores em SI (N, m, Pa). Convertemos forcas para kN.
"""
import json
import sys
import win32com.client as w

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "robot_dados.json"

robot = w.gencache.EnsureDispatch("Robot.Application")
proj = robot.Project
st = proj.Structure

dados = {"projeto": proj.Name, "arquivo": proj.FileName, "casos": [], "barras": [], "reacoes": []}

# --- casos de carga ---
casos = st.Cases.GetAll()
for i in range(1, casos.Count + 1):
    c = casos.Get(i)
    dados["casos"].append({"num": c.Number, "nome": c.Name})

# --- barras: secao, comprimento, esforcos extremos entre todos os casos ---
barras = st.Bars.GetAll()
res_barras = st.Results.Bars.Forces
n_casos = len(dados["casos"])
for i in range(1, barras.Count + 1):
    b = barras.Get(i)
    reg = {"num": b.Number, "no_i": b.StartNode, "no_f": b.EndNode,
           "secao": None, "comprimento_m": None, "N_max_kN": None, "N_min_kN": None,
           "Mz_max_kNm": None, "Mz_min_kNm": None, "Fy_max_kN": None}
    try:
        reg["secao"] = b.GetLabel(w.constants.I_LT_BAR_SECTION).Name
    except Exception:
        pass
    try:
        reg["comprimento_m"] = round(b.Length, 4)
    except Exception:
        pass
    maxN = minN = maxM = minM = maxV = None
    for c in dados["casos"]:
        for pos in (0.0, 0.5, 1.0):  # inicio, meio, fim
            try:
                v = res_barras.Value(b.Number, c["num"], pos)
            except Exception:
                continue
            fx, fy, mz = v.FX / 1000.0, v.FY / 1000.0, v.MZ / 1000.0
            maxN = fx if maxN is None else max(maxN, fx)
            minN = fx if minN is None else min(minN, fx)
            maxM = mz if maxM is None else max(maxM, mz)
            minM = mz if minM is None else min(minM, mz)
            maxV = abs(fy) if maxV is None else max(maxV, abs(fy))
    reg.update({"N_max_kN": maxN, "N_min_kN": minN, "Mz_max_kNm": maxM,
                "Mz_min_kNm": minM, "Fy_max_kN": maxV})
    dados["barras"].append(reg)

# --- reacoes nos nos com apoio ---
nos = st.Nodes.GetAll()
res_nos = st.Results.Nodes.Reactions
for i in range(1, nos.Count + 1):
    nd = nos.Get(i)
    if not nd.HasCalcSupport:
        continue
    for c in dados["casos"]:
        try:
            r = res_nos.Value(nd.Number, c["num"])
        except Exception:
            continue
        dados["reacoes"].append({"no": nd.Number, "caso": c["num"],
                                 "FX_kN": r.FX / 1000.0, "FY_kN": r.FY / 1000.0,
                                 "FZ_kN": r.FZ / 1000.0})

with open(SAIDA, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=1)

print("OK: %d casos, %d barras, %d reacoes -> %s" %
      (len(dados["casos"]), len(dados["barras"]), len(dados["reacoes"]), SAIDA))
