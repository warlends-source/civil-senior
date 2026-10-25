"""Nucleo de expressoes: UMA fonte para SMath (RPN) e Word (OMML).

Sintaxe infixa: numeros, nomes (letras latinas/gregas, digitos, PONTO = subscrito: f.ck.r, tau.Rd),
operadores + - * / ^ (menos unario), <=, if(c,a,b), parenteses. Constante: π.
  nome        -> SMath: operando "f.ck.r"  | Word: f com subscrito "ck,r"
  a/b         -> SMath: fracao empilhada    | Word: m:f
  x^0.5       -> SMath: potencia            | Word: raiz (m:rad)
  if(a<=b,a,b)-> SMath: if(...)             | Word: min(a,b);  if(a<=b,b,a) -> max(a,b)
"""
import math
import re

_NOME = r"[A-Za-zͰ-Ͽ][A-Za-z0-9Ͱ-Ͽ]*(?:\.[A-Za-z0-9Ͱ-Ͽ]+)*"
_TOK = re.compile(r"\s*(\d+\.?\d*|%s|<=|[-+*/^(),])" % _NOME)
CONST = {"π": math.pi}


def _tokens(s):
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = _TOK.match(s, pos)
        if not m:
            raise ValueError("token invalido em %r (pos %d)" % (s, pos))
        out.append(m.group(1))
        pos = m.end()
    return out


class _P:
    def __init__(self, t):
        self.t, self.i = t, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self, x=None):
        v = self.peek()
        if x is not None and v != x:
            raise ValueError("esperado %r, veio %r" % (x, v))
        self.i += 1
        return v

    def cmp(self):
        a = self.add()
        if self.peek() == "<=":
            self.eat()
            return ("cmp", a, self.add())
        return a

    def add(self):
        a = self.mul()
        while self.peek() in ("+", "-"):
            op = self.eat()
            a = ("bin", op, a, self.mul())
        return a

    def mul(self):
        a = self.unary()
        while self.peek() in ("*", "/"):
            op = self.eat()
            a = ("bin", op, a, self.unary())
        return a

    def unary(self):
        if self.peek() == "-":
            self.eat()
            return ("neg", self.unary())
        return self.pow()

    def pow(self):
        a = self.atom()
        if self.peek() == "^":
            self.eat()
            return ("bin", "^", a, self.unary())
        return a

    def atom(self):
        v = self.eat()
        if v == "(":
            a = self.cmp()
            self.eat(")")
            return ("par", a)
        if re.fullmatch(r"\d+\.?\d*", v):
            return ("num", v)
        if self.peek() == "(":
            self.eat("(")
            args = [self.cmp()]
            while self.peek() == ",":
                self.eat(",")
                args.append(self.cmp())
            self.eat(")")
            return ("fn", v, args)
        return ("var", v)


def parse(expr):
    p = _P(_tokens(expr))
    a = p.cmp()
    if p.peek() is not None:
        raise ValueError("sobra token %r em %r" % (p.peek(), expr))
    return a


def variaveis(n, acc=None):
    acc = set() if acc is None else acc
    k = n[0]
    if k == "var":
        acc.add(n[1])
    elif k == "bin":
        variaveis(n[2], acc), variaveis(n[3], acc)
    elif k == "cmp":
        variaveis(n[1], acc), variaveis(n[2], acc)
    elif k in ("neg", "par"):
        variaveis(n[1], acc)
    elif k == "fn":
        for a in n[2]:
            variaveis(a, acc)
    return {v for v in acc if v not in CONST}


# --------------------------------------------------------------------------- avaliacao
def avaliar(n, env):
    k = n[0]
    if k == "num":
        return float(n[1])
    if k == "var":
        return CONST[n[1]] if n[1] in CONST else env[n[1]]
    if k == "par":
        return avaliar(n[1], env)
    if k == "neg":
        return -avaliar(n[1], env)
    if k == "cmp":
        return 1.0 if avaliar(n[1], env) <= avaliar(n[2], env) else 0.0
    if k == "fn":
        if n[1] != "if" or len(n[2]) != 3:
            raise ValueError("funcao nao suportada: %s" % n[1])
        c, a, b = n[2]
        return avaliar(a, env) if avaliar(c, env) else avaliar(b, env)
    a, b = avaliar(n[2], env), avaliar(n[3], env)
    return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b,
            "/": lambda: a / b, "^": lambda: a ** b}[n[1]]()


# --------------------------------------------------------------------------- RPN (SMath)
def rpn(n):
    k = n[0]
    if k == "num" or k == "var":
        return [("operand", n[1])]
    if k == "par":
        return rpn(n[1])
    if k == "neg":
        return rpn(n[1]) + [("operator", "-", 1)]
    if k == "cmp":
        return rpn(n[1]) + rpn(n[2]) + [("operator", "≤", 2)]
    if k == "fn":
        out = []
        for a in n[2]:
            out += rpn(a)
        return out + [("function", n[1], len(n[2]))]
    return rpn(n[2]) + rpn(n[3]) + [("operator", n[1], 2)]


def avaliar_rpn(tokens, env):
    st = []
    for tk in tokens:
        if tk[0] == "operand":
            v = tk[1]
            st.append(float(v) if re.fullmatch(r"\d+\.?\d*", v) else (CONST[v] if v in CONST else env[v]))
        elif tk[0] == "operator":
            if tk[2] == 1:
                st.append(-st.pop())
                continue
            b, a = st.pop(), st.pop()
            op = tk[1]
            if op == "+":
                st.append(a + b)
            elif op == "-":
                st.append(a - b)
            elif op == "*":
                st.append(a * b)
            elif op == "/":
                st.append(a / b)
            elif op == "^":
                st.append(a ** b)
            elif op == "≤":
                st.append(1.0 if a <= b else 0.0)
            else:
                raise ValueError(op)
        else:
            f, t, c = st.pop(), st.pop(), st.pop()
            st.append(t if c else f)
    return st[0]


def contagens(n):
    """(divisoes, potencias, funcoes, profundidade de fracao) - para dimensionar linhas no SMath."""
    k = n[0]
    if k in ("num", "var"):
        return 0, 0, 0
    if k in ("par", "neg"):
        return contagens(n[1])
    if k == "cmp":
        a, b = contagens(n[1]), contagens(n[2])
        return tuple(x + y for x, y in zip(a, b))
    if k == "fn":
        t = (0, 0, 1)
        for a in n[2]:
            t = tuple(x + y for x, y in zip(t, contagens(a)))
        return t
    a, b = contagens(n[2]), contagens(n[3])
    t = tuple(x + y for x, y in zip(a, b))
    return (t[0] + (n[1] == "/"), t[1] + (n[1] == "^"), t[2])


def profundidade(n):
    """(aninhamento de fracoes, aninhamento de potencias, usa if) - altura visual no SMath."""
    k = n[0]
    if k in ("num", "var"):
        return 0, 0, 0
    if k in ("par", "neg"):
        return profundidade(n[1])
    if k == "cmp":
        a, b = profundidade(n[1]), profundidade(n[2])
        return max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])
    if k == "fn":
        ps = [profundidade(a) for a in n[2]]
        return max(p[0] for p in ps), max(p[1] for p in ps), 1
    a, b = profundidade(n[2]), profundidade(n[3])
    return (max(a[0], b[0]) + (n[1] == "/"), max(a[1], b[1]) + (n[1] == "^"), max(a[2], b[2]))


# --------------------------------------------------------------------------- numeros pt-BR
def fmt_br(v, sig=4, casas=None):
    """4 algarismos significativos, virgula decimal, ponto de milhar (>= 1000)."""
    if casas is None:
        if v == 0:
            s = "0"
        else:
            mag = math.floor(math.log10(abs(v)))
            dec = max(0, sig - 1 - mag)
            if abs(v) >= 100:
                dec = max(dec, 2)
            s = ("%.*f" % (dec, v))
            if "." in s:
                s = s.rstrip("0").rstrip(".")
    else:
        s = "%.*f" % (casas, v)
    ip, _, fp = s.partition(".")
    neg = ip.startswith("-")
    ip = ip.lstrip("-")
    if len(ip) >= 4:
        ip = "{:,}".format(int(ip)).replace(",", ".")
    return ("-" if neg else "") + ip + ("," + fp if fp else "")


# --------------------------------------------------------------------------- OMML (Word)
_RPR = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
_CTRL = '<m:ctrlPr>%s</m:ctrlPr>' % _RPR


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def r(t, plain=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    return "<m:r>%s%s<m:t xml:space=\"preserve\">%s</m:t></m:r>" % (sty, _RPR, _esc(t))


def num_omml(txt):
    """'0,85' -> runs '0' ',' '85' (como o Pandoc/Word do memorial); '15.734,86' idem."""
    if "," in txt:
        a, b = txt.split(",", 1)
        return r(a) + r(",", True) + r(b)
    return r(txt)


def f(num, den):
    return "<m:f><m:fPr>%s</m:fPr><m:num>%s</m:num><m:den>%s</m:den></m:f>" % (_CTRL, num, den)


def sub(base, s):
    return "<m:sSub><m:sSubPr>%s</m:sSubPr><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>" % (_CTRL, base, s)


def sup(base, s):
    return "<m:sSup><m:sSupPr>%s</m:sSupPr><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>" % (_CTRL, base, s)


def rad(x):
    return ("<m:rad><m:radPr><m:degHide m:val=\"1\"/>%s</m:radPr><m:deg/><m:e>%s</m:e></m:rad>" % (_CTRL, x))


def par(x):
    return "<m:d><m:dPr>%s</m:dPr><m:e>%s</m:e></m:d>" % (_CTRL, x)


def nome_omml(nome):
    """f.ck.r -> f_{ck,r};  tau.Rd -> tau_{Rd};  FS -> FS (multiletra sem ponto: romano)."""
    partes = nome.split(".")
    base = partes[0]
    b = r(base, plain=len(base) > 1 and base[0] < "Ͱ")
    if len(partes) == 1:
        return b
    return sub(b, r(",".join(partes[1:]), True))


def _prec(n):
    k = n[0]
    if k == "bin":
        return {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}[n[1]]
    if k == "neg":
        return 2
    if k == "cmp":
        return 0
    return 4


def unpar(n):
    while n[0] == "par":
        n = n[1]
    return n


def omml(n, subst=None, fmt=None):
    """Arvore -> OMML. subst: dict nome->valor (numerico) para a linha de substituicao."""
    k = n[0]
    if k == "num":
        return num_omml(n[1].replace(".", ","))
    if k == "var":
        if n[1] == "π":
            return r("π", True)
        if subst is not None and n[1] in subst:
            t = (fmt or fmt_br)(subst[n[1]])
            return num_omml(t) if not t.startswith("-") else par(r("−", True) + num_omml(t[1:]))
        return nome_omml(n[1])
    if k == "par":
        return par(omml(n[1], subst, fmt))
    if k == "neg":
        x = omml(n[1], subst, fmt)
        return r("−", True) + (par(x) if _prec(n[1]) < 3 else x)
    if k == "cmp":
        return omml(n[1], subst, fmt) + r("≤", True) + omml(n[2], subst, fmt)
    if k == "fn":
        c, a, b = n[2]
        if n[1] == "if" and c[0] == "cmp":
            x, y = c[1], c[2]
            same = lambda p, q: p == q or (p[0] == "par" and p[1] == q) or (q[0] == "par" and q[1] == p)
            if same(a, x) and same(b, y):
                nm = "min"
            elif same(a, y) and same(b, x):
                nm = "max"
            else:
                nm = None
            if nm:
                return r(nm, True) + par(omml(x, subst, fmt) + r(";", True) + omml(y, subst, fmt))
        raise ValueError("if nao reconhecido como min/max")
    op, a, b = n[1], n[2], n[3]
    if op == "/":
        return f(omml(unpar(a), subst, fmt), omml(unpar(b), subst, fmt))
    if op == "^":
        base = omml(a, subst, fmt)
        if _prec(a) < 4 and a[0] not in ("par",):
            base = par(base)
        if unpar(b) == ("num", "0.5"):
            return rad(omml(unpar(a), subst, fmt))
        return sup(base, omml(unpar(b), subst, fmt))
    la, lb = omml(a, subst, fmt), omml(b, subst, fmt)
    if op in "+-":
        if op == "-" and _prec(b) == 1:
            lb = par(lb)
        return la + r("+" if op == "+" else "−", True) + lb
    # produto
    if _prec(a) < 2:
        la = par(la)
    if _prec(b) < 2 or (b[0] == "neg"):
        lb = par(lb)
    return la + r("⋅", True) + lb
