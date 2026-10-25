# Tensão admissível a partir do SPT — procedimento

## Princípio

A sapata não "sente" o solo da cota de apoio. Ela mobiliza um volume de solo
abaixo dela — o **bulbo de pressões** — e o comportamento depende da média
ponderada desse volume. Usar o NSPT do golpe da cota de apoio é o erro mais
comum e o mais fácil de um auditor apontar.

## Passo a passo

### 1. Definir o bulbo de cada tipo de sapata

Profundidade de influência tomada como **2B abaixo da base**, com `B` = menor
dimensão da sapata. Para sapatas corridas a influência é maior (ordem de 3B a
4B); registrar qual critério foi adotado e por quê.

```
Intervalo de integração: de (cota de apoio) até (cota de apoio − 2B)
```

Sapata quadrada de 2,00 m apoiada a −1,50 m → bulbo de −1,50 m a −5,50 m.

### 2. Extrair o NSPT médio no intervalo

Média aritmética dos golpes dos ensaios contidos no intervalo, por furo.
Regras:

- **Descartar** valores de N acima de 30–40 apenas se houver justificativa
  (impenetrável, matacão) — e registrar o descarte.
- **Não descartar** valores baixos por serem inconvenientes. Camada mole dentro
  do bulbo é o dado mais importante do documento.
- Havendo mais de um furo influente, avaliar por furo e adotar o **mais
  desfavorável**, ou justificar interpolação.
- Camada de comportamento muito distinto dentro do bulbo (ex.: argila mole
  entre areias) invalida a média simples — nesse caso a média esconde o
  problema. Tratar por camadas e verificar recalque explicitamente.

### 3. Individualizar por tipo de sapata

Sapatas de dimensões diferentes têm bulbos diferentes e, portanto, **tensões
admissíveis diferentes**. Produzir uma linha por tipo:

| Tipo | B (m) | Cota apoio | Bulbo (2B) | Furos | NSPT médio | σ_adm (kPa) |
|------|-------|-----------|------------|-------|-----------|-------------|
| S1 | 1,20 | −1,50 | −1,50 a −3,90 | SP-02 | | |
| S2 | 2,00 | −1,50 | −1,50 a −5,50 | SP-02, SP-03 | | |

Uma tensão admissível única para a obra inteira só é aceitável se o perfil for
comprovadamente homogêneo no intervalo de todos os bulbos — e isso precisa ser
dito e demonstrado.

### 4. Aplicar a correlação

Correlações semi-empíricas usuais na prática brasileira, para solos sedimentares:

```
σ_adm ≈ N_médio / 50        [MPa]      (faixa de validade usual: 5 ≤ N ≤ 20)
```

**Limitações que precisam constar no memorial:**

- Correlação empírica, calibrada para solos sedimentares brasileiros; não se
  aplica automaticamente a solos residuais, colapsíveis, expansivos, orgânicos
  ou aterros.
- Fora da faixa de N indicada, a extrapolação não é confiável — para N < 5
  investigar compressibilidade; para N > 20 a correlação tende a subestimar e o
  ganho deve ser justificado por método mais robusto.
- A correlação estima **capacidade de carga**; ela não verifica **recalque**.
  Recalque é ELS e é verificação independente e obrigatória.
- O SPT é ensaio de baixa resolução. Onde a obra for relevante ou o perfil
  duvidoso, a NBR 6122 prevê métodos mais confiáveis (prova de carga, ensaios
  complementares). Se o escopo não os contempla, dizer isso na conclusão como
  limitação, não omitir.

**Texto-padrão para o memorial:**

> A tensão admissível foi estimada por correlação semi-empírica com o índice de
> resistência à penetração (NSPT), tomado como média dos golpes contidos no
> bulbo de pressões de cada tipo de sapata. Trata-se de método estimativo; os
> valores adotados são conservadores dentro da faixa de validade da correlação.
> Verificação de recalque apresentada em [seção]. Recomenda-se confirmação das
> hipóteses geotécnicas na abertura das cavas, com registro fotográfico e
> comunicação imediata a este projetista em caso de divergência do perfil.

### 5. Verificar recalque (ELS) — sempre

Capacidade de carga atendida não significa recalque aceitável, e em solo mole o
recalque governa. Apresentar:

- recalque total estimado por sapata;
- recalque diferencial entre sapatas vizinhas;
- distorção angular resultante;
- limites normativos adotados, com a fonte.

## Erros a não cometer

- NSPT da cota de apoio em vez da média no bulbo.
- Tensão admissível única para sapatas de dimensões muito diferentes.
- Aplicar a correlação fora da faixa de validade sem dizer.
- Concluir "atende" só com capacidade de carga, sem ELS.
- Ignorar nível d'água — ele altera peso específico efetivo e capacidade.
- Ignorar camada mole dentro do bulbo porque a média "fechou".
- Citar item numerado da NBR 6122 sem ter lido a norma.
