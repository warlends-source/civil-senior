"""Gera um memorial de calculo SMath (.sm) a partir do JSON do Robot.

Uso:  python gerar_memorial.py robot_dados.json memorial.sm [N_barras_criticas]
O .sm e XML puro (formato dos exemplos do SMath). Expressoes em notacao pos-fixa (RPN):
  x := 5  ->  <operand>x</operand> <operand>5</operand> <operator args=2>:</operator>
Valores sao guardados como numeros; a unidade fica no nome da variavel (ex.: Mz_kNm).
"""
import json
import sys
from datetime import date
from xml.sax.saxutils import escape

entrada = sys.argv[1] if len(sys.argv) > 1 else "robot_dados.json"
saida = sys.argv[2] if len(sys.argv) > 2 else "memorial.sm"
n_crit = int(sys.argv[3]) if len(sys.argv) > 3 else 10

d = json.load(open(entrada, encoding="utf-8"))
barras = [b for b in d["barras"] if b["Mz_max_kNm"] is not None]

regioes = []
y = [9]  # posicao vertical corrente


def _prox(h):
    t = y[0]
    y[0] += h + 6
    return t


def texto(txt, negrito=False, cor="#000000", fundo="#ffffff", tam=10, h=24, w=600):
    rid = len(regioes)
    b = ' bold="true"' if negrito else ""
    regioes.append(
        '  <region id="%d" left="9" top="%d" width="%d" height="%d" color="%s" bgColor="%s" fontSize="%d">\n'
        '    <text lang="eng">\n      <p%s>%s</p>\n    </text>\n  </region>'
        % (rid, _prox(h), w, h, cor, fundo, tam, b, escape(txt)))


def definir(nome, valor, h=26):
    """nome := valor  (RPN)"""
    rid = len(regioes)
    regioes.append(
        '  <region id="%d" left="9" top="%d" width="260" height="%d" color="#000000" bgColor="#ffffff" fontSize="10">\n'
        '    <math>\n      <input>\n'
        '        <e type="operand">%s</e>\n'
        '        <e type="operand">%s</e>\n'
        '        <e type="operator" args="2">:</e>\n'
        '      </input>\n    </math>\n  </region>'
        % (rid, _prox(h), h, escape(nome), ("%.4f" % valor).rstrip("0").rstrip(".")))


# ---- cabecalho ----
texto("Memorial de Calculo - Esforcos de Barras (Robot)", negrito=True, cor="#0000ff", tam=14, h=30)
texto("Projeto: %s" % d["projeto"])
texto("Arquivo: %s" % d["arquivo"], h=24)
texto("Gerado em %s a partir do Robot Structural Analysis 2027 | %d casos, %d barras."
      % (date.today().strftime("%d/%m/%Y"), len(d["casos"]), len(d["barras"])))
texto("Unidades: forcas em kN, momentos em kN.m, comprimentos em m. Valores extraidos nas secoes 0, 0,5 L e 1,0 L de cada barra, envoltoria de todos os casos.",
      fundo="#ffff80", h=40)

# ---- barras criticas ----
crit = sorted(barras, key=lambda b: max(abs(b["Mz_max_kNm"]), abs(b["Mz_min_kNm"])), reverse=True)[:n_crit]
texto("Barras criticas (maiores |Mz|)", negrito=True, fundo="#dddddd", h=26)
for b in crit:
    texto("Barra %d (secao %s, L = %s m, nos %d-%d)"
          % (b["num"], b["secao"], b["comprimento_m"], b["no_i"], b["no_f"]), negrito=True, h=24)
    p = "B%d" % b["num"]
    definir("%s_N_max_kN" % p, b["N_max_kN"])
    definir("%s_N_min_kN" % p, b["N_min_kN"])
    definir("%s_Mz_max_kNm" % p, b["Mz_max_kNm"])
    definir("%s_Mz_min_kNm" % p, b["Mz_min_kNm"])
    definir("%s_V_max_kN" % p, b["Fy_max_kN"])

# ---- documento ----
cab = ('﻿<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
       '<?application progid="SMath Studio Desktop" version="0.98.6606.22069"?>\n'
       '<regions xmlns="http://smath.info/schemas/worksheet/1.0">\n'
       '  <settings dpi="96">\n'
       '    <metadata lang="eng">\n'
       '      <title>Memorial - %s</title>\n'
       '    </metadata>\n'
       '  </settings>\n' % escape(d["projeto"]))
with open(saida, "w", encoding="utf-8") as f:
    f.write(cab + "\n".join(regioes) + "\n</regions>\n")

print("OK: %s (%d regioes)" % (saida, len(regioes)))
