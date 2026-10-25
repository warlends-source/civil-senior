# ENG3 — Engenharia Estrutural

Plugin de skills para projeto estrutural, fundações e documentação técnica
auditável, no contexto de normas brasileiras.

## Skills

| Skill | Dispara quando | O que faz |
|-------|----------------|-----------|
| `memorial-de-calculo` | memorial, memória de cálculo, dimensionamento, verificação estrutural, laudo | Estrutura obrigatória do documento, rastreabilidade de todo valor, ELU/ELS, formatação Word Arial 11/12 com equações em OMML, regra de versão inicial |
| `base-tecnica` | registrar critério, anotar decisão, base de conhecimento | Acervo Markdown de normas, critérios, detalhes padrão, decisões e lições, navegável sem banco vetorial |
| `revit-bim` | quantitativo, pranchas, auditoria de modelo, clash detection, levar o modelo ao Robot | Ordem de operações segura para o servidor `revit-mcp`, classificação de risco em 4 níveis, fluxos prontos, ponte Revit → Robot pelo CivilConnection 2027 (CIVIL SÊNIOR) |
| `arquivos-tecnicos` | extrair do CYPE/TQS/Eberick, ler SPT em PDF, converter DWG | Rotas de extração por formato, validação em três conferências, conversão de unidades |

## Referências incluídas

- `memorial-de-calculo/references/normas.md` — edições ABNT verificadas em
  10/09/2026, com as que ainda precisam de confirmação separadas das
  confirmadas
- `memorial-de-calculo/references/fundacoes-spt.md` — bulbo de pressões, NSPT
  médio, limitações honestas das correlações
- `memorial-de-calculo/references/formatacao-docx.md` — Pandoc e python-docx,
  equações OMML, sumário automático
- `base-tecnica/references/modelos.md` — modelos de índice e de cada tipo de nota

## Dependências

Nenhum servidor MCP é instalado por este plugin. As skills assumem, quando
disponíveis:

- `revit-mcp` já conectado na máquina, para a skill `revit-bim`
- `pandoc`, `python-docx`, `pdfplumber`, `pandas`, `ezdxf` — instalados sob
  demanda pelas skills que precisarem

## Manutenção

A tabela de normas em `memorial-de-calculo/references/normas.md` tem data de
verificação. **Revisar a cada emenda ABNT** e atualizar a data. Uma edição
errada na seção "Normas aplicáveis" compromete o documento inteiro.

## Licença

MIT.
