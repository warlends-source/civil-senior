# Produção do .docx — receita técnica

Ler **depois** de ter o conteúdo técnico pronto. Formatação nunca antecede o
cálculo.

## Escolha da ferramenta

| Situação | Ferramenta |
|----------|-----------|
| Documento novo, do zero, com equações | **Pandoc** a partir de Markdown com LaTeX |
| Edição cirúrgica em .docx existente | **python-docx** |
| Documento existente com controle de alterações | python-docx + manipulação de OOXML |

Verificar disponibilidade antes: `which pandoc`, `python3 -c "import docx"`.
Instalar o que faltar (`pip install python-docx --break-system-packages`).

## Caminho recomendado: Pandoc

O Pandoc converte matemática LaTeX diretamente para **OMML** (o formato nativo
do editor de equações do Word). É a única rota que produz equações realmente
editáveis no Word sem escrever XML à mão.

### 1. Criar o template de estilos (uma vez)

```bash
pandoc -o referencia.docx --print-default-data-file reference.docx
```

Abrir `referencia.docx` no Word e ajustar os estilos — não o texto:

- `Normal` → Arial 11
- `Título 1` / `Heading 1` → Arial 12, negrito
- `Título 2` / `Heading 2` → Arial 11, negrito
- `Título 3` / `Heading 3` → Arial 11, negrito
- Cabeçalho e rodapé → identificação do documento, revisão, numeração de páginas

Guardar como template do escritório e reutilizar. Estilo ajustado uma vez vale
para todos os memoriais.

### 2. Escrever o conteúdo em Markdown

Matemática em LaTeX entre `$$`:

```markdown
# 7. Formulação

A tensão admissível é estimada por:

$$\sigma_{adm} = \frac{N_{SPT,médio}}{50}$$

Onde:

| Símbolo | Descrição | Unidade |
|---------|-----------|---------|
| $\sigma_{adm}$ | Tensão admissível do solo | MPa |
| $N_{SPT,médio}$ | Índice de resistência médio no bulbo de pressões | golpes/30 cm |
```

A tabela de variáveis logo abaixo de cada fórmula é obrigatória (regra da
skill). Símbolo, descrição e **unidade** — sempre as três colunas.

### 3. Converter

```bash
pandoc memorial.md \
  -o memorial.docx \
  --reference-doc=referencia.docx \
  --toc --toc-depth=3 \
  --number-sections
```

`--toc` gera o sumário. Ao abrir no Word, atualizar campos (Ctrl+A, F9) para os
números de página aparecerem.

### 4. Forçar atualização do sumário na abertura

Para o sumário vir preenchido sem intervenção manual, injetar
`<w:updateFields w:val="true"/>` em `word/settings.xml`:

```python
import zipfile, shutil, re

src, dst = "memorial.docx", "memorial_final.docx"
shutil.copy(src, dst)

with zipfile.ZipFile(src) as z:
    settings = z.read("word/settings.xml").decode("utf-8")

if "updateFields" not in settings:
    settings = settings.replace(
        "<w:settings ", "<w:settings ", 1
    )
    # insere logo após a abertura da tag raiz
    settings = re.sub(
        r"(<w:settings[^>]*>)",
        r'\1<w:updateFields w:val="true"/>',
        settings, count=1
    )

# reescrever o pacote com o settings.xml alterado
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/settings.xml":
            data = settings.encode("utf-8")
        zout.writestr(item, data)
```

## Caminho alternativo: python-docx

Para edição pontual de arquivo existente.

### Estilos Arial

```python
from docx import Document
from docx.shared import Pt

doc = Document("memorial.docx")

def set_font(style_name, size, bold=False):
    st = doc.styles[style_name]
    st.font.name = "Arial"
    st.font.size = Pt(size)
    st.font.bold = bold
    # garante a fonte também para caracteres de leste asiático / complexos
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        rfonts.set(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            + attr, "Arial"
        )

set_font("Normal", 11)
set_font("Heading 1", 12, bold=True)
set_font("Heading 2", 11, bold=True)
set_font("Heading 3", 11, bold=True)
```

### Equação OMML injetada diretamente

python-docx não cria equações. Injetar o XML OMML no parágrafo:

```python
from docx.oxml import parse_xml

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def omml_fracao(numerador, denominador):
    return parse_xml(
        f'<m:oMathPara xmlns:m="{M_NS}" xmlns:w="{W_NS}">'
        f'<m:oMath>'
        f'<m:f><m:num><m:r><m:t>{numerador}</m:t></m:r></m:num>'
        f'<m:den><m:r><m:t>{denominador}</m:t></m:r></m:den></m:f>'
        f'</m:oMath></m:oMathPara>'
    )

p = doc.add_paragraph()
p._p.append(omml_fracao("N_SPT", "50"))
```

Escrever OMML à mão é trabalhoso e frágil para expressões longas. Para qualquer
coisa além de fração e potência, gerar via Pandoc:

```bash
echo '$$V_{Rd2} = 0.27 \alpha_{v2} f_{cd} b_w d$$' | pandoc -f markdown -t docx -o eq.docx
```

e extrair o bloco `<m:oMath>` de `word/document.xml`.

### Cabeçalho de tabela repetido entre páginas

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def repetir_cabecalho(table):
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)
```

Obrigatório em qualquer tabela de elementos que passe de uma página.

## Verificação antes de entregar

Abrir o arquivo gerado e conferir — não confiar no script:

```bash
python3 -c "
from docx import Document
d = Document('memorial_final.docx')
print('parágrafos:', len(d.paragraphs))
print('tabelas:', len(d.tables))
fontes = {p.style.font.name for p in d.paragraphs if p.style.font.name}
print('fontes de estilo:', fontes)
"
```

Checar visualmente:

- [ ] Sumário com números de página corretos
- [ ] Equações selecionáveis como objeto de equação (não imagem, não texto)
- [ ] Arial 11/12 em todo o documento, inclusive tabelas
- [ ] Cabeçalho de tabela repetindo nas quebras
- [ ] Numeração de páginas e identificação da revisão no rodapé
- [ ] Anexos presentes e referenciados
