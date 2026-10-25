# Modelos de arquivo

## INDICE.md

```markdown
# Base Técnica — Índice

## Como usar (para agentes)
1. Ler este índice primeiro. Escolher notas pela descrição; abrir só essas.
2. Preferir abrir 1–3 notas específicas a varrer a base.
3. Citar o `id` da nota ao usar a informação.
4. Nota com norma desatualizada no campo `normas:` não é confiável — avisar.

## Como atualizar (para agentes)
- Assunto novo → nota nova (atômica). Assunto existente mudou → editar e
  atualizar `atualizado`.
- Criar, renomear ou remover nota exige atualizar este registro e o
  `_topico.md` do tópico na mesma operação.
- Usar apenas tags do vocabulário abaixo; incluir a tag aqui antes de usá-la.

## Vocabulário de tags
`fundacoes` `concreto` `aco` `pre-moldado` `spt` `vento` `piso-industrial`
`portuario` `detalhamento` `execucao` `software`

## Registro

### fundacoes
- `20260910-tensao-admissivel-por-spt` — **Tensão admissível a partir do NSPT** —
  `topicos/fundacoes/tensao-admissivel-por-spt.md` — Critério de média no bulbo
  de pressões e faixa de validade da correlação.

### criterios
- (vazio)
```

Formato da linha de registro:
`` `id` — **Título** — `caminho` — descrição de uma linha. ``

## _topico.md

```markdown
# Fundações

Métodos de capacidade de carga, correlações com SPT, critérios de recalque e
limites adotados pelo escritório.

- [Tensão admissível a partir do NSPT](tensao-admissivel-por-spt.md) — média no
  bulbo, faixa de validade.
```

## Nota tipo `criterio`

```markdown
---
id: 20260910-tensao-admissivel-por-spt
titulo: Tensão admissível a partir do NSPT
tipo: criterio
tags: [fundacoes, spt]
normas: ["ABNT NBR 6122:2019"]
criado: 2026-09-10
atualizado: 2026-09-10
autor: Warlen Dornelas
relacionadas: []
resumo: Média de NSPT no bulbo de pressões, individualizada por tipo de sapata.
---

# Tensão admissível a partir do NSPT

> Resumo: média de NSPT no bulbo de pressões, individualizada por tipo de sapata.

## Contexto
Quando este critério se aplica e quando não se aplica.

## Critério adotado
O valor ou método, objetivamente.

## Justificativa
Por que este e não outro. Com números.

## Faixa de validade
Limites numéricos e tipos de solo em que vale. Fora disso, o que fazer.

## Relacionadas
- [Bulbo de pressões](bulbo-de-pressoes.md) — pré-requisito: define o intervalo
  de integração usado aqui.
```

## Nota tipo `decisao`

```markdown
---
id: 20260910-radier-base-reservatorio
titulo: Radier para a base de reservatório
tipo: decisao
tags: [fundacoes]
normas: ["ABNT NBR 6122:2019", "ABNT NBR 6118:2023"]
criado: 2026-09-10
atualizado: 2026-09-10
autor: Warlen Dornelas
relacionadas: [20260910-tensao-admissivel-por-spt]
resumo: Escolha de radier sobre sapatas isoladas por baixa capacidade no bulbo.
---

# Radier para a base de reservatório

> Resumo: escolha de radier sobre sapatas isoladas por baixa capacidade no bulbo.

## Decisão
O que foi decidido, em uma frase.

## Alternativas consideradas
- Alternativa A — descartada porque [motivo com número].
- Alternativa B — descartada porque [motivo com número].

## Justificativa
O raciocínio completo, com os valores e a norma que respalda.

## Condições de validade
O que precisa continuar verdadeiro para a decisão seguir válida. O que exige
reanálise.

## Relacionadas
- [Tensão admissível a partir do NSPT](../fundacoes/tensao-admissivel-por-spt.md)
  — fundamenta: o critério que produziu o valor usado nesta decisão.
```

## Nota tipo `licao`

```markdown
---
id: 20260910-exemplo-licao
titulo: [O que aconteceu]
tipo: licao
tags: [execucao]
normas: []
criado: 2026-09-10
atualizado: 2026-09-10
autor: Warlen Dornelas
relacionadas: []
resumo: [uma frase]
---

# [Título]

## O que aconteceu
Fatos, sem atribuição de culpa.

## Causa
A causa técnica identificada.

## O que passou a ser feito diferente
A mudança concreta de prática. Sem isto, a nota não tem valor.

## Onde isso foi incorporado
Nota de critério ou detalhe padrão que foi alterada em consequência.
```
