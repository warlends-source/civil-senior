"""Verifica o cortante de laje/radier sem armadura transversal contra VRd1 (NBR 6118:2023 19.4.1).

Uso:
  python verificar_cortante_radier.py elementos.csv --d 0.92 --as-cm2 20.94 --fck 45 \
         [--combos 11 12 13 14] [--raio-estaca 0.35] [--estacas estacas.csv] [--fator-g4 0]
Entrada: CSV de extrair_cascas.py (qxx, qyy em kN/m).
Metodo (igual ao exemplo de referencia (radier estaqueado C45), item 11.2.2):
  Vd = sqrt(qxx^2 + qyy^2) por elemento, envoltoria das combinacoes ELU escolhidas;
  exclui o circulo de raio (R_estaca + d/2) ao redor do eixo de cada estaca
  (a regiao interna e coberta pela puncao - NAO verificada aqui);
  compara com VRd1 (nbr6118.vrd1_laje).
LIMITES: nao soma a parcela de G4 (momento excentrico da torre) nem outras parcelas que o
  memorial acrescenta fora do Robot; informe --fator-g4 (acrescimo percentual de Vd) se
  quiser incluir. Resultado e verificacao auxiliar, nao substitui o memorial.
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
ap.add_argument("--d", type=float, required=True, help="altura util (m)")
ap.add_argument("--as-cm2", type=float, required=True, help="As1 de tracao (cm2/m)")
ap.add_argument("--fck", type=float, required=True)
ap.add_argument("--combos", type=int, nargs="*", default=None)
ap.add_argument("--raio-estaca", type=float, default=0.35)
ap.add_argument("--estacas", default=None, help="CSV x;y (m) dos eixos; padrao: malha 4x4 de 2,40 m")
ap.add_argument("--fator-g4", type=float, default=0.0, help="acrescimo relativo de Vd (ex.: 0.055)")
args = ap.parse_args()

if args.estacas:
    est = [(float(r[0]), float(r[1])) for r in csv.reader(open(args.estacas), delimiter=";") if r and r[0][0] != "x"]
else:
    g = (-3.6, -1.2, 1.2, 3.6)
    est = [(x, y) for x in g for y in g]
r_exc = args.raio_estaca + args.d / 2.0

vrd1 = c.vrd1_laje(args.d, args.as_cm2 * 1e-4, args.fck)["VRd1_kN"]
env = {}  # elem -> (Vd max, comb, xc, yc)
with open(args.csv, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter=";"):
        cmb = int(r["comb"])
        if args.combos and cmb not in args.combos:
            continue
        x, y = float(r["xc"]), float(r["yc"])
        if any(math.hypot(x - ex, y - ey) < r_exc for ex, ey in est):
            continue
        vd = math.hypot(float(r["qxx"]), float(r["qyy"])) * (1 + args.fator_g4)
        e = int(r["elem"])
        if e not in env or vd > env[e][0]:
            env[e] = (vd, cmb, x, y)

if not env:
    raise SystemExit("Nenhum elemento apos filtros (combos/exclusao de estacas).")
pior = max(env.values())
n_90 = sum(1 for v in env.values() if v[0] > 0.9 * vrd1)
n_exc = sum(1 for v in env.values() if v[0] > vrd1)
print("VRd1 = %.1f kN/m (d=%.2f m, As=%.2f cm2/m, fck=%g)" % (vrd1, args.d, args.as_cm2, args.fck))
print("Elementos verificados: %d (fora de r=%.2f m das estacas)" % (len(env), r_exc))
print("Vd max = %.1f kN/m  comb %d  em (%.2f; %.2f)  -> Vd/VRd1 = %.3f" %
      (pior[0], pior[1], pior[2], pior[3], pior[0] / vrd1))
print("Elementos com Vd > 0,9 VRd1: %d | com Vd > VRd1: %d" % (n_90, n_exc))
print("SITUACAO:", "ATENDE sem armadura transversal" if n_exc == 0 else "NAO ATENDE: armadura transversal ou reanalise")
if args.fator_g4 == 0:
    print("AVISO: parcela de G4 nao incluida (use --fator-g4 para acrescimo percentual).")
