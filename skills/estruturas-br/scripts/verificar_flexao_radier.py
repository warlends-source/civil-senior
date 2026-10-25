"""Verifica a flexao do radier a partir dos momentos de casca (CSV de extrair_cascas.py).

Uso:
  python verificar_flexao_radier.py elementos.csv --fck 45 --h 1.0 \
      --d-inf 0.92 --as-inf 20.94 --d-sup 0.925 --as-sup 20.94 \
      [--combos 11 12 13 14] [--raio-estaca 0.35] [--estacas estacas.csv]
Convencao de sinal do Robot neste modelo: momento NEGATIVO = tracao na face INFERIOR.
Criterio (igual ao exemplo de referencia (radier estaqueado C45), item 11.2.1 / 10.4):
  Md,inf = max(-mxx, -myy);  Md,sup = max(mxx, myy), envoltoria elemento a elemento das
  combinacoes ELU; ignora o interior do circulo de raio R_estaca em torno de cada estaca
  (singularidade do apoio pontual; momentos tomados a face da estaca).
  SEM Wood-Armer (o memorial nao o usa; com WA o Md inferior sobe ~0,7 %).
LIMITES: nao soma a parcela G4 (momento excentrico da torre); Md real do memorial e um pouco
  maior (inf +0,1 %, sup +5 %). Use --fator-g4 para majorar. Verificacao auxiliar.
"""
import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbr6118 as c  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--fck", type=float, required=True)
ap.add_argument("--h", type=float, required=True)
ap.add_argument("--d-inf", type=float, required=True)
ap.add_argument("--as-inf", type=float, required=True, help="cm2/m")
ap.add_argument("--d-sup", type=float, required=True)
ap.add_argument("--as-sup", type=float, required=True, help="cm2/m")
ap.add_argument("--combos", type=int, nargs="*", default=None)
ap.add_argument("--raio-estaca", type=float, default=0.35)
ap.add_argument("--estacas", default=None)
ap.add_argument("--fator-g4", type=float, default=0.0)
a = ap.parse_args()

if a.estacas:
    est = [(float(r[0]), float(r[1])) for r in csv.reader(open(a.estacas), delimiter=";") if r and r[0][0] != "x"]
else:
    g = (-3.6, -1.2, 1.2, 3.6)
    est = [(x, y) for x in g for y in g]

md_inf = md_sup = 0.0
pos_inf = pos_sup = None
with open(a.csv, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if a.combos and int(r["comb"]) not in a.combos:
            continue
        x, y = float(r["xc"]), float(r["yc"])
        if any(math.hypot(x - ex, y - ey) < a.raio_estaca for ex, ey in est):
            continue
        mxx, myy = float(r["mxx"]), float(r["myy"])
        vi, vs = max(-mxx, -myy), max(mxx, myy)
        if vi > md_inf:
            md_inf, pos_inf = vi, (int(r["comb"]), x, y)
        if vs > md_sup:
            md_sup, pos_sup = vs, (int(r["comb"]), x, y)
md_inf *= 1 + a.fator_g4
md_sup *= 1 + a.fator_g4

def face(nome, md, pos, d, as_, positivo):
    mr = c.momento_resistente(as_, d, a.fck)
    asmin = c.as_minima_laje(a.fck, a.h, bidirecional_positivo=positivo)
    rel = md / mr["MRd_kNm"]
    print("%s: Md = %.1f kN.m/m (comb %d em %.2f;%.2f) | MRd = %.1f (d=%.3f, As=%.2f) | Md/MRd = %.2f | As,min = %.2f cm2/m -> %s%s" % (
        nome, md, pos[0], pos[1], pos[2], mr["MRd_kNm"], d, as_, rel, asmin,
        "ATENDE" if rel <= 1 and as_ >= asmin else "NAO ATENDE", " (governa As,min)" if md < mr["MRd_kNm"] and rel < 0.5 else ""))
    for av in mr["avisos"]:
        print("   AVISO:", av)

face("Face inferior", md_inf, pos_inf, a.d_inf, a.as_inf, True)
face("Face superior", md_sup, pos_sup, a.d_sup, a.as_sup, False)
if a.fator_g4 == 0:
    print("AVISO: parcela G4 nao incluida (memorial: inf +0,1 %, sup +5 %).")
