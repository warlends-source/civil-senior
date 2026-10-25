---
name: base-tecnica
description: >
  Esta skill deve ser usada quando o usuário quiser criar ou manter a base
  técnica do escritório: "criar a base técnica", "registrar esse critério",
  "anotar essa decisão de projeto", "guardar esse detalhe padrão", "o que a
  gente adotou para X", "por que escolhemos esse método", "indexar as notas
  técnicas", "revisar a base de conhecimento". Gerencia um acervo Markdown de
  normas, critérios adotados, detalhes padrão, decisões de projeto e lições
  aprendidas, navegável por qualquer agente sem banco vetorial.
metadata:
  version: "0.1.0"
  audience: agent
---

# Base técnica do escritório

Acervo de notas Markdown que responde uma pergunta específica: **"por que
adotamos isso, quando, e com que respaldo?"** — três anos depois, com o
projetista original indisponível.

Não é um repositório de normas (as normas ficam com a ABNT). É o registro do
que *este escritório decidiu*, com rastreabilidade.

## Princípios

1. **Índice primeiro.** O agente lê `INDICE.md`, escolhe notas pela descrição de
   uma linha, e abre só essas. Nota não registrada no índice não existe.
2. **Uma nota, um assunto.** Título que precisa de "e" são duas notas.
3. **ID estável.** `AAAAMMDD-slug`, permanente, nunca reaproveitado. Links
   sobrevivem a renomeação.
4. **Toda decisão tem data, autor e respaldo.** Critério sem justificativa
   escrita é folclore, não base técnica.
5. **Norma citada com edição.** `ABNT NBR 6118:2023` — nunca sem ano.
6. **Nota é o que decidimos, não o que o projeto tem.** Dado de um projeto
   específico vive no projeto; o que vira nota é o critério generalizável.

## Estrutura

```
base-tecnica/
  INDICE.md
  topicos/
    normas/            _topico.md + notas sobre aplicação de normas
    criterios/         critérios de cálculo adotados pelo escritório
    fundacoes/         métodos, correlações, limites
    detalhes/          detalhes padrão de armação e ligação
    decisoes/          decisões de projeto com justificativa
    materiais/         especificações, fornecedores, desempenho
    licoes/            lições aprendidas de obra
  anexos/              imagens, PDFs, planilhas referenciadas
```

Pastas em minúsculo, sem acento, sem espaço. Arquivos em kebab-case:
`topicos/fundacoes/tensao-admissivel-por-spt.md`.

## Frontmatter obrigatório

```yaml
---
id: 20260910-tensao-admissivel-por-spt
titulo: Tensão admissível a partir do NSPT
tipo: criterio          # norma | criterio | detalhe | decisao | material | licao
tags: [fundacoes, spt]  # apenas tags do vocabulário controlado do INDICE.md
normas: ["ABNT NBR 6122:2019"]
criado: 2026-09-10
atualizado: 2026-09-10
autor: Warlen Dornelas
relacionadas: [20260910-bulbo-de-pressoes]
resumo: Uma frase que permita ao agente decidir se abre a nota.
---
```

`resumo` é exatamente a linha que vai para o registro do índice — escrevê-la
pensando em quem está decidindo se abre o arquivo.

## Tipos de nota

| tipo | responde | seção que não pode faltar |
|------|----------|---------------------------|
| `norma` | como aplicamos tal prescrição | Interpretação adotada |
| `criterio` | qual valor/método adotamos por padrão | Justificativa + faixa de validade |
| `detalhe` | como detalhamos tal ligação | Desenho/anexo + condições de uso |
| `decisao` | por que escolhemos A em vez de B | Alternativas descartadas + motivo |
| `material` | o que especificamos e por quê | Requisito + norma de aceitação |
| `licao` | o que deu errado e o que mudou | O que passou a ser feito diferente |

Modelos completos de corpo em `references/modelos.md`.

## A nota de decisão é a mais valiosa

É a que protege responsabilidade técnica anos depois. Ela registra o que foi
descartado, não só o que foi adotado:

```markdown
## Decisão
Radier em vez de sapatas isoladas.

## Alternativas consideradas
- Sapatas isoladas — descartada: NSPT médio de 4 no bulbo levaria a
  dimensões inviáveis frente ao afastamento disponível.
- Estacas escavadas — descartada: custo de mobilização desproporcional
  ao porte da estrutura.

## Justificativa
[o raciocínio, com os números e a norma que respalda]

## Condições de validade
Vale para carga de reservatório até [X] kN e perfil similar ao de SP-02.
Perfil diferente exige reanálise.
```

"Condições de validade" é o que impede a nota de ser aplicada onde não cabe.

## Fluxos

### Criar a base do zero

1. Criar a estrutura de pastas.
2. Escrever `INDICE.md` com: instruções de uso para agentes, vocabulário
   controlado de tags (começar curto), e registro vazio.
3. Criar o primeiro tópico e sua `_topico.md`.
4. Escrever a primeira nota e registrá-la no índice **na mesma operação**.

### Registrar algo novo

1. Verificar se já existe nota do assunto (buscar por slug e por tag antes de
   criar — duplicata é o defeito mais comum).
2. Assunto existente que mudou → editar a nota, atualizar `atualizado`.
   Assunto novo → nota nova.
3. Registrar no `INDICE.md` e ligar em `_topico.md`, na mesma operação.
4. Preencher `relacionadas` nos dois sentidos.

### Revisão periódica

- **Normas desatualizadas** — verificar todo campo `normas:` contra o catálogo
  ABNT. Norma que teve emenda desde a nota exige revisão da nota, não só do
  campo. Esta é a manutenção mais importante da base.
- **Órfãs** — notas sem link de entrada (fora do índice e do `_topico.md`):
  ligar a algo relevante ou arquivar.
- **Links quebrados** — conferir que cada caminho do registro e cada id em
  `relacionadas` existe de fato no disco, não só como texto.
- **Duplicatas** — mesclar, manter um id, redirecionar links.
- **Notas não atômicas** — nota que cresceu para dois assuntos: dividir.
- **Tags fora do vocabulário** — reconciliar contra a lista do `INDICE.md`.

## Ligação com os documentos oficiais

A base técnica é a memória; o memorial de cálculo é o documento. **Nunca citar
a base técnica dentro de um memorial** — nem como referência, nem como "conforme
critério interno". O memorial é autocontido (regra 5 da skill
`memorial-de-calculo`). A base alimenta a redação; ela não aparece no produto.

## Antes de fechar qualquer edição

- [ ] Frontmatter completo e válido
- [ ] `id` único, slug do arquivo igual ao slug do id
- [ ] Normas citadas com edição
- [ ] `INDICE.md` e `_topico.md` refletem a mudança
- [ ] `relacionadas` espelhado nos dois sentidos
- [ ] `atualizado` alterado
- [ ] Nota do tipo `criterio` ou `decisao` tem "Condições de validade"
