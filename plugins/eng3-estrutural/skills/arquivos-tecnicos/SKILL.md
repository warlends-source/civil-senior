---
name: arquivos-tecnicos
description: >
  Esta skill deve ser usada quando o usuário pedir para tratar arquivos de saída
  de software de engenharia: "extrair as reações do CYPE", "ler o relatório do
  CYPECAD", "pegar os esforços do TQS", "converter a saída do Eberick",
  "extrair o SPT desse PDF", "tabular a sondagem", "consolidar as planilhas de
  cargas", "converter DWG em lote", "renomear as pranchas", "comparar duas
  revisões de planilha". Define como ler cada formato, como validar o que foi
  extraído e o que não é possível fazer.
metadata:
  version: "0.1.0"
  audience: agent
---

# Arquivos técnicos — extração e tratamento

Dado extraído de saída de software vira insumo de memorial de cálculo. Se a
extração estiver errada, o erro entra num documento assinado. Portanto:
**nenhuma extração é entregue sem validação contra a fonte.**

## Regra de validação

Toda extração passa por três conferências antes de ser usada:

1. **Contagem** — número de linhas extraídas = número de elementos esperado.
   Divergência é erro até prova em contrário.
2. **Extremos** — máximo e mínimo de cada coluna fazem sentido físico?
   Reação vertical negativa, momento de 10⁶ kN·m, tensão de 3 MPa em argila
   mole: sinal de coluna trocada ou unidade errada.
3. **Amostra cega** — escolher 3 linhas aleatórias e conferir manualmente
   contra o PDF/planilha original. Registrar quais linhas foram conferidas.

Extração sem essas três conferências é rascunho, não dado de projeto.

## Unidades — a fonte mais comum de erro grave

Software de estrutura mistura unidades entre módulos e entre versões. Nunca
assumir; **ler o cabeçalho da tabela de origem**.

| Software | Padrão frequente | Armadilha |
|----------|------------------|-----------|
| CYPE / CYPECAD | kN, kN·m, m | Relatórios antigos e configurações em tf e tf·m |
| TQS | tf, tf·m, cm | Módulos diferentes com unidades diferentes no mesmo projeto |
| Eberick | kN, kN·m, cm | Cotas em cm e esforços em m no mesmo relatório |
| SAP2000 / Robot | conforme configurado | Nada é padrão; sempre ler o cabeçalho |

Ao consolidar dados de fontes diferentes, **converter tudo para um sistema único
antes de qualquer operação** e declarar o sistema adotado no topo da planilha
resultante. `1 tf = 9,80665 kN` — usar o valor completo, não 10.

## Por formato

### Planilhas (.xlsx, .csv) — reações, esforços, cargas

```python
import pandas as pd
df = pd.read_excel(caminho, sheet_name=None)   # None = todas as abas
for nome, aba in df.items():
    print(nome, aba.shape, list(aba.columns)[:8])
```

Saídas de CYPE e Eberick costumam ter linhas de título e legenda acima da tabela
— localizar a linha de cabeçalho real antes de ler com `header=`. Nunca assumir
`header=0`.

Arquivo grande (acima de ~50 MB): abrir uma vez num REPL persistente e
trabalhar em memória, em vez de reler a cada pergunta.

### PDF de relatório de cálculo

Tentar nesta ordem:

```python
import pdfplumber
with pdfplumber.open(caminho) as pdf:
    for i, page in enumerate(pdf.pages):
        for t in page.extract_tables():
            ...
```

`pdfplumber` extrai tabelas com estrutura. Se o resultado vier desalinhado,
`camelot` (modo `lattice` para tabelas com linhas, `stream` para sem linhas)
costuma resolver. Texto corrido sem tabela: `pypdf` para o texto e regex.

**PDF escaneado** (texto não selecionável) exige OCR:

```bash
ocrmypdf --language por --force-ocr entrada.pdf saida.pdf
```

Depois extrair normalmente. OCR de tabela numérica erra dígito — a conferência
por amostra cega deixa de ser opcional e passa a ser 10 linhas, não 3.

### Sondagem SPT

Relatório de sondagem quase sempre chega como PDF escaneado ou como desenho.
Objetivo da extração: para cada furo, a tabela `profundidade → NSPT`, mais nível
d'água e descrição das camadas.

Estrutura de saída:

```
furo, cota_boca, prof_inicial, prof_final, nspt, camada, na_medido
SP-01, 12.40, 1.00, 1.45, 6, "Argila siltosa mole", -2.30
```

Regras:

- Registrar **golpes/30 cm** conforme o relatório. Se vier como `n1/n2/n3`
  (golpes por 15 cm), guardar os três e calcular o NSPT como a soma dos dois
  últimos — e dizer que foi isso que se fez.
- `impenetrável` / `N > 50` não é número: guardar o rótulo, não converter.
- Nível d'água ausente ("seco") é informação, não vazio.
- Anexar a extração como planilha ao memorial e citar o relatório de origem
  (empresa, número, data) — é a procedência (b) da regra 1 da skill
  `memorial-de-calculo`.

### Documentos Word (.docx)

Para editar relatório existente sem regerar: `python-docx`. Para gerar novo, ver
`references/formatacao-docx.md` da skill `memorial-de-calculo`.

Comparar duas revisões:

```bash
pandoc -f docx -t markdown rev00.docx -o rev00.md
pandoc -f docx -t markdown rev01.docx -o rev01.md
diff -u rev00.md rev01.md
```

### DWG / DXF

**Limite real: DWG é formato binário proprietário e não é lido diretamente por
biblioteca livre.** Não prometer o que não dá.

| Objetivo | Caminho |
|----------|---------|
| Ler geometria/textos/layers | Converter DWG → DXF (ODA File Converter, gratuito) e ler com `ezdxf` |
| Conversão em lote | ODA File Converter em linha de comando, ou script AutoCAD (`.scr`) com `_DXFOUT` |
| Plotar em lote para PDF | Publish do AutoCAD com arquivo `.dsd`, ou script `.scr` |
| Renomear/organizar arquivos | Operação de sistema de arquivos, sem abrir o CAD |

```python
import ezdxf
doc = ezdxf.readfile("prancha.dxf")
msp = doc.modelspace()
textos = [e.dxf.text for e in msp.query("TEXT")]
layers = [l.dxf.name for l in doc.layers]
```

Extrair carimbo de prancha: os campos costumam ser `TEXT`/`MTEXT` dentro de um
bloco de título — consultar `msp.query("INSERT")` e inspecionar os atributos.

## Organização de arquivos de projeto

Ao reorganizar pastas de projeto: **nunca sobrescrever original**. Cópia
transformada vai ao lado, com nome que diga o que é. Antes de mover em lote,
apresentar o plano de movimentação e obter confirmação.

Nomenclatura que sobrevive a auditoria:

```
<PROJETO>_<DISCIPLINA>_<ELEMENTO>_<TIPO>_REV<nn>.<ext>
EMPRESA_EST_RADIER-RESERVATORIO_MC_REV00.docx
EMPRESA_EST_FUNDACOES_PL_REV01.dwg
```

Data no nome só quando não houver revisão. Revisão sempre com dois dígitos.

## O que não fazer

- Entregar extração sem as três conferências.
- Somar valores de fontes com unidades diferentes.
- Converter "impenetrável" em número.
- Assumir que a primeira linha do Excel é o cabeçalho.
- Sobrescrever arquivo original do usuário numa transformação.
- Afirmar que leu um DWG quando na verdade leu um DXF convertido — dizer qual
  foi a rota, porque a conversão pode perder objeto proxy.
