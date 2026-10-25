---
name: memorial-de-calculo
description: >
  Esta skill deve ser usada quando o usuário pedir "memorial de cálculo",
  "memória de cálculo", "memorial descritivo", "relatório técnico estrutural",
  "dimensionamento de sapatas/blocos/radier/vigas/pilares", "verificação
  estrutural", "nota de cálculo", "laudo estrutural", ou qualquer documento
  técnico de engenharia estrutural destinado a assinatura, ART/RRT, aprovação
  de cliente ou auditoria. Define a estrutura obrigatória do documento, as
  regras de rastreabilidade de valores, a verificação ELU/ELS e o padrão de
  formatação Word.
metadata:
  version: "0.1.0"
  audience: agent
---

# Memorial de cálculo — padrão auditável

Produzir documento técnico que um terceiro possa auditar linha a linha sem
acesso ao autor. O critério de qualidade não é "parece bom": é **um revisor
externo consegue refazer cada número a partir do que está escrito**.

## Regras invioláveis

Violar qualquer uma destas invalida o documento. Não negociar por concisão.

1. **Todo valor tem origem declarada.** Nenhum número aparece sem uma destas
   quatro procedências, explicitada no texto ou em nota de rodapé:
   (a) dado fornecido pelo cliente/projetista — citar o documento e a data;
   (b) resultado de sondagem/ensaio — citar o furo, a profundidade e o relatório;
   (c) prescrição normativa — citar norma, edição e item;
   (d) cálculo derivado de (a)–(c) — mostrar a fórmula e a substituição.
   Não existe "valor usual", "valor de mercado", "adotado por experiência" sem
   justificativa escrita.

2. **Nunca inventar parâmetro.** Faltou dado de entrada (fck, NSPT, carga,
   geometria, nível d'água, classe de agressividade), **parar e perguntar**.
   Se o usuário determinar que se prossiga com hipótese, registrar em bloco
   destacado "HIPÓTESE ADOTADA — PENDENTE DE CONFIRMAÇÃO", com o impacto da
   hipótese sobre o resultado.

3. **Nunca citar item de norma sem verificação.** Número de item, tabela e
   fórmula só entram no documento se lidos na norma. Não reconstituir de
   memória — errar um item numerado é pior que omiti-lo. Sem acesso ao texto,
   citar a norma e descrever a prescrição sem numerar o item, e sinalizar ao
   usuário que a referência precisa ser conferida.

4. **Versão inicial por padrão.** Todo documento é emitido como versão inicial
   (REV. 00) **salvo** se o usuário disser explicitamente "revisão". Nunca
   escrever "conforme versão anterior", "atualizando o memorial de", "diferente
   do que foi feito em", nem qualquer referência a entregas passadas.

5. **Sem analogias externas.** Nunca comparar o objeto com outro projeto,
   subestação, obra ou empreendimento dentro do documento oficial. Cada
   memorial é autocontido.

6. **ELU e ELS sempre.** Nenhum elemento é dado por verificado só no ELU.
   Estado limite de serviço (deslocamentos, fissuração, vibração, recalques)
   entra com valor calculado e valor limite normativo, lado a lado.

7. **Incerteza é sinalizada, não maquiada.** Onde o modelo é simplificado, a
   correlação é empírica, ou o dado é escasso, dizer isso no corpo do texto e
   dimensionar o conservadorismo adotado.

## Estrutura obrigatória do documento

Nesta ordem. Não suprimir seções; seção sem conteúdo aplicável recebe a nota
"Não aplicável a este escopo" com uma linha de justificativa.

| # | Seção | Conteúdo mínimo |
|---|-------|-----------------|
| — | Capa | Objeto, local, contratante, responsável técnico, CREA, revisão, data |
| — | Sumário | Automático, com números de página |
| 1 | Introdução | Contexto do empreendimento e do documento |
| 2 | Objetivo | O que este memorial dimensiona/verifica e o que **não** cobre |
| 3 | Normas aplicáveis | Designação + edição + título completo (ver `references/normas.md`) |
| 4 | Dados de entrada | Geometria, cargas, materiais, sondagem, com fonte de cada dado |
| 5 | Critérios adotados | Coeficientes, classe de agressividade, cobrimento, modelo estrutural, hipóteses |
| 6 | Metodologia de cálculo | Sequência do cálculo e software utilizado, com versão |
| 7 | Formulação | Fórmulas no editor de equações + lista de variáveis com unidade |
| 8 | Tabelas de elementos | Um elemento por linha, com entradas e saídas |
| 9 | Verificações | ELU e ELS, valor calculado × valor limite × relação de utilização |
| 10 | Resultados | Geometrias e armaduras finais, consolidadas |
| 11 | Conclusão técnica | Declaração objetiva de atendimento, com escopo e limitações |
| 12 | Notas executivas | O que a obra precisa saber: sequência, tolerâncias, controles |
| — | Anexos | Sondagens, plantas, saídas de software, planilhas |

### Seções que costumam ser mal feitas

**Objetivo (2)** — o valor está no que ele *exclui*. Escrever o que o memorial
não cobre (ex.: "não contempla a superestrutura metálica, objeto de documento
específico") protege a responsabilidade técnica.

**Critérios adotados (5)** — é aqui que o auditor procura o que foi decidido.
Cada critério é uma frase com o valor e a razão: "Classe de agressividade
ambiental II (urbana), conforme NBR 6118; cobrimento nominal de 30 mm para
vigas e pilares."

**Verificações (9)** — formato de três colunas, sempre:
`Solicitante (Sd) | Resistente (Rd) | Sd/Rd`. Relação > 1,00 é reprovação e
deve aparecer marcada, não escondida. Relação < 0,30 sugere superdimensionamento
e merece um comentário.

**Conclusão técnica (11)** — não é um parágrafo genérico de encerramento.
Declara: o que foi verificado, sob quais premissas, com qual resultado, e o que
condiciona a validade (ex.: "válido para as cargas informadas em [doc], em
[data]; alteração de carga exige reanálise").

## Fluxo de trabalho

1. **Levantar os dados de entrada antes de escrever qualquer coisa.** Ler todos
   os anexos fornecidos (sondagem, plantas, planilhas de carga, memorial de
   arquitetura). Listar o que está faltando e perguntar.
2. **Fechar os critérios com o usuário** antes de calcular, quando houver
   escolha de projeto (modelo de apoio, coeficiente de segurança, método de
   capacidade de carga).
3. **Calcular.** Preferir cálculo verificável em script (Python) a cálculo
   mental — o script fica como anexo e é reexecutável.
4. **Escrever o documento** na estrutura acima.
5. **Rodar o checklist final** (abaixo) antes de entregar.

## Fundações — regra específica

Tensão admissível determinada a partir do **NSPT médio no bulbo de pressões**,
não do NSPT da cota de apoio isolada. O bulbo é tomado como a profundidade de
influência da sapata (ordem de 2B abaixo da base, com B a menor dimensão), e a
média é feita nos golpes dentro desse intervalo.

**Individualizar por tipo de sapata.** Sapatas de dimensões diferentes mobilizam
bulbos diferentes e, portanto, tensões admissíveis diferentes. Uma tabela única
de σ_adm para toda a obra é erro de método — produzir uma linha por tipo, com o
intervalo de profundidade, o NSPT médio e a tensão resultante.

Detalhamento do procedimento, correlações e suas limitações em
`references/fundacoes-spt.md`.

## Formatação (Word .docx)

- Corpo: **Arial 11**
- Títulos de seção: **Arial 12, negrito**
- Subtítulos: **Arial 11, negrito**
- Equações: **editor de equações do Word (OMML)** — nunca imagem, nunca texto
  corrido com barras
- Sumário automático com números de página
- Numeração de páginas, cabeçalho com identificação do documento e da revisão
- Tabelas com cabeçalho repetido entre páginas

Receita técnica de produção (python-docx, OMML, sumário, estilos, quebra de
tabela) em `references/formatacao-docx.md`. Ler antes de gerar o arquivo, nunca
antes de ter o conteúdo pronto.

## Checklist antes de entregar

- [ ] Todo número tem origem declarada (regra 1)
- [ ] Nenhum item de norma citado sem verificação (regra 3)
- [ ] Nenhuma referência a versão anterior ou a outro projeto (regras 4 e 5)
- [ ] Todas as edições de norma conferidas contra `references/normas.md`
- [ ] ELU **e** ELS verificados para cada elemento
- [ ] Relações Sd/Rd tabeladas; nenhuma > 1,00 sem tratamento explícito
- [ ] Hipóteses pendentes destacadas em bloco próprio
- [ ] Objetivo declara o que o documento **não** cobre
- [ ] Conclusão declara premissas e condições de validade
- [ ] Fontes Arial 11/12 aplicadas; equações em OMML; sumário atualizado
- [ ] Anexos referenciados no corpo e efetivamente presentes
