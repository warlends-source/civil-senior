"""Gera worksheets SMath (.sm) com FORMULAS VIVAS a partir do nucleo comum (calc_ast).

O que o SMath aceita (conferido nos exemplos instalados e em abertura real no SMath Solver):
  - nomes: letras latinas/GREGAS (γ, α, τ, σ, ρ, η, φ, κ, π...), digitos e PONTO = subscrito
    (f.ck.r aparece como f_ck.r; τ.Rd como τ_Rd). NAO usar sublinhado.
  - operadores: :  + - * / ^, menos unario, ≤  |  funcao: if(c,a,b). Sem sqrt/min escalares:
    use ^0,5 e if.
  - divisao vira fracao empilhada e potencia vira expoente: a altura da linha acompanha isso.
  - o valor mostrado vem de <result action="numeric">.
Layout (pagina ~600 px de largura util):
    legenda cinza (9 pt)  x=9                       <- ACIMA da linha a que se refere
    [ definicao  x=9 ]  [ = valor  x=335 ]  [ unidade x=476 ]
"""
from xml.sax.saxutils import escape

import calc_ast as ca

LARG = 600
NL = "\n"


def _fmt(v):
    return "%.6g" % v


class SmDoc:
    def __init__(self, titulo):
        self.titulo, self.reg, self.y, self.env = titulo, [], 12, {}

    def _id(self):
        return len(self.reg)

    def _prox(self, h, gap=6):
        t = self.y
        self.y += h + gap
        return t

    def _texto(self, txt, left=9, w=LARG, h=24, cor="#000000", fundo="#ffffff", tam=10,
               negrito=False, borda=False, top=None):
        top = self._prox(h) if top is None else top
        b = ' bold="true"' if negrito else ""
        bd = ' border="true"' if borda else ""
        self.reg.append(
            '  <region id="%d" left="%d" top="%d" width="%d" height="%d"%s color="%s" bgColor="%s" fontSize="%d">%s'
            '    <text lang="eng">%s      <p%s>%s</p>%s    </text>%s  </region>'
            % (self._id(), left, top, w, h, bd, cor, fundo, tam, NL, NL, b, escape(txt), NL, NL))

    # ----------------------------------------------------------------- blocos de texto
    def titulo_doc(self, linhas):
        for i, (t, tam) in enumerate(linhas):
            self._texto(t, tam=tam, negrito=(i == 0), cor="#1F3864" if i == 0 else "#000000",
                        h=int(tam * 2.2), w=LARG)

    def secao(self, txt):
        self.y += 10
        self._texto(txt, negrito=True, cor="#FFFFFF", fundo="#1F3864", tam=11, h=28)

    def subsecao(self, txt):
        self.y += 4
        self._texto(txt, negrito=True, cor="#1F3864", fundo="#D9E2F3", tam=10, h=24)

    def nota(self, txt):
        linhas = -(-len(txt) // 98)
        self._texto(txt, fundo="#FFF2CC", tam=9, h=max(24, 15 * linhas + 10))

    def texto(self, txt, tam=10):
        linhas = -(-len(txt) // 98)
        self._texto(txt, tam=tam, h=max(22, 15 * linhas + 8))

    # ----------------------------------------------------------------- definicoes vivas
    def definir(self, nome, expr, unidade="", comentario="", destaque=False, mostrar=True):
        tree = ca.parse(expr)
        val = ca.avaliar(tree, self.env)
        toks = ca.rpn(tree)                       # confere RPN x arvore (o que o SMath vai ler)
        assert abs(ca.avaliar_rpn(toks, self.env) - val) <= 1e-9 * max(1.0, abs(val)), nome
        self.env[nome] = val
        df, dp, usa_if = ca.profundidade(tree)
        h = 28 + 24 * df + 8 * min(dp, 2) + (50 if usa_if else 0)
        if comentario:                             # legenda cinza ACIMA da linha
            self._texto(comentario, left=9, w=LARG, h=18, cor="#595959", tam=9)
        top = self._prox(h, gap=6)
        xml = []
        for tk in toks:
            if tk[0] == "operand":
                xml.append('        <e type="operand">%s</e>' % escape(tk[1]))
            elif tk[0] == "operator":
                xml.append('        <e type="operator" args="%d">%s</e>' % (tk[2], escape(tk[1])))
            else:
                xml.append('        <e type="function" args="%d">%s</e>' % (tk[2], escape(tk[1])))
        self.reg.append(
            '  <region id="%d" left="9" top="%d" width="320" height="%d" color="#000000" bgColor="#ffffff" fontSize="10">%s'
            '    <math>%s      <input>%s        <e type="operand">%s</e>%s%s%s'
            '        <e type="operator" args="2">:</e>%s      </input>%s    </math>%s  </region>'
            % (self._id(), top, h, NL, NL, NL, escape(nome), NL, NL.join(xml), NL, NL, NL, NL))
        meio = top + max(0, (h - 28) // 2)         # resultado centrado na altura da fracao
        if mostrar:
            fundo = "#E2EFDA" if destaque else "#ffffff"
            self.reg.append(
                '  <region id="%d" left="335" top="%d" width="135" height="28" color="#000000" bgColor="%s" fontSize="10">%s'
                '    <math>%s      <input>%s        <e type="operand">%s</e>%s      </input>%s'
                '      <result action="numeric">%s        <e type="operand">%s</e>%s      </result>%s    </math>%s  </region>'
                % (self._id(), meio, fundo, NL, NL, NL, escape(nome), NL, NL, NL, _fmt(val), NL, NL, NL))
        if unidade:
            self._texto(unidade, left=476, w=120, h=28, cor="#1F3864", tam=10, top=meio, negrito=True)
        return val

    def imagem(self, caminho, largura_px=420, legenda=""):
        """Insere uma imagem PNG (reduzida a largura_px para manter o arquivo leve), centralizada, com legenda."""
        import base64
        import io
        from PIL import Image
        im = Image.open(caminho).convert("RGB")
        alt = int(largura_px * im.height / im.width)
        im = im.resize((largura_px, alt), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        left = max(9, (LARG - largura_px) // 2)
        top = self._prox(alt, gap=6)
        self.reg.append(
            '  <region id="%d" left="%d" top="%d" width="%d" height="%d" color="#000000" bgColor="#ffffff">%s'
            '    <picture>%s      <raw format="png" encoding="base64">%s</raw>%s    </picture>%s  </region>'
            % (self._id(), left, top, largura_px, alt, NL, NL, b64, NL, NL))
        if legenda:
            self._texto(legenda, left=9, w=LARG, h=24, cor="#595959", tam=9)

    def espaco(self, px=10):
        self.y += px

    def salvar(self, caminho, autor="", descricao=""):
        cab = ('﻿<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
               '<?application progid="SMath Studio Desktop" version="0.98.6606.22069"?>\n'
               '<regions xmlns="http://smath.info/schemas/worksheet/1.0">\n'
               '  <settings dpi="96">\n'
               '    <metadata lang="eng">\n      <title>%s</title>\n      <author>%s</author>\n'
               '      <description>%s</description>\n    </metadata>\n  </settings>\n'
               % (escape(self.titulo), escape(autor), escape(descricao)))
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(cab + NL.join(self.reg) + "\n</regions>\n")
