"""Extrai esforcos de CASCA (radier/laje) do Robot aberto para CSV. SOMENTE LEITURA.

Uso:  python extrair_cascas.py --combos 11 12 13 14 --saida elementos.csv [--painel 1] [--camada 3]
Requer: Robot aberto, projeto calculado, pywin32.

Saida (CSV, ';'): comb;elem;xc;yc;mxx;myy;mxy;qxx;qyy   -> kN.m/m e kN/m
(mesmo formato de estaq_R_rev_C45_elementos.csv, gerado por estaq_ler_rev_v1.ps1).
Observacoes:
 - Os valores brutos incluem a singularidade sobre as estacas; o verificador exclui o
   circulo de raio r = R_estaca + d/2 em torno de cada eixo (NBR 6118, cortante de laje).
 - O Robot devolve N e N.m (SI); dividimos por 1000.
 - Camada 3 / Panel 1 sao os do modelo estaq_R_rev_C45; ajuste se o modelo mudar.
"""
import argparse
import math
import win32com.client as w

ap = argparse.ArgumentParser()
ap.add_argument("--combos", type=int, nargs="+", required=True)
ap.add_argument("--saida", default="elementos.csv")
ap.add_argument("--painel", type=int, default=1)
ap.add_argument("--camada", type=int, default=3)
ap.add_argument("--z", type=float, default=0.0, help="cota Z dos nos da face do radier")
args = ap.parse_args()

robot = w.gencache.EnsureDispatch("Robot.Application")
st = robot.Project.Structure
if not st.Results.Available:
    raise SystemExit("ERRO: sem resultados. Calcule o modelo (Analise > Calculos) e salve.")

# coordenadas dos nos na cota do radier
nos = st.Nodes.GetAll()
xy = {}
for i in range(1, nos.Count + 1):
    nd = nos.Get(i)
    if abs(nd.Z - args.z) <= 0.001:
        xy[nd.Number] = (nd.X, nd.Y)

fe = st.Results.FiniteElems
elems = st.FiniteElems.GetAll()
print("elementos: %d | nos na cota %.3f: %d" % (elems.Count, args.z, len(xy)))

# centroide de cada elemento
cent = {}
for i in range(1, elems.Count + 1):
    el = elems.Get(i)
    nn = el.Nodes
    pts = [xy[nn.Get(j)] for j in range(1, nn.Count + 1) if nn.Get(j) in xy]
    if pts:
        cent[el.Number] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

linhas = ["comb;elem;xc;yc;mxx;myy;mxy;qxx;qyy"]
for cmb in args.combos:
    par = robot.CmpntFactory.Create(39)       # parametros de resultado detalhado de EF
    par.Case = cmb
    par.Layer = args.camada
    par.Panel = args.painel
    par.Node = 0
    n_ok = 0
    qmax = 0.0
    for i in range(1, elems.Count + 1):
        el = elems.Get(i)
        c = cent.get(el.Number)
        if c is None:
            continue
        par.Element = el.Number
        try:
            d = fe.Detailed(par)
        except Exception:
            continue
        linhas.append("%d;%d;%.4f;%.4f;%.3f;%.3f;%.3f;%.3f;%.3f" % (
            cmb, el.Number, c[0], c[1], d.MXX / 1000, d.MYY / 1000, d.MXY / 1000,
            d.QXX / 1000, d.QYY / 1000))
        qmax = max(qmax, math.hypot(d.QXX, d.QYY) / 1000)
        n_ok += 1
    print("comb %d: %d elementos | |Q| bruto max = %.1f kN/m" % (cmb, n_ok, qmax))

with open(args.saida, "w", encoding="utf-8-sig") as f:
    f.write("\n".join(linhas) + "\n")
print("OK ->", args.saida)
