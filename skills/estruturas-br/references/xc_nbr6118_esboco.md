# Esboço: módulo NBR 6118 para o XC

Baseado na leitura de `xc/python_modules/materials/aci/` e `ec2/`. Nada foi executado; o núcleo C++ do XC não está compilado nesta máquina.
Fórmulas da NBR 6118:2023 citadas de memória: **conferir cada item na norma antes de usar**.

## 1. Como o XC organiza um código de projeto

| Peça | Classe base (XC) | Exemplo ACI (`ACI_materials.py`, `ACI_limit_state_checking.py`) | Exemplo EC2 |
|---|---|---|---|
| Concreto | `concrete_base.Concrete(nmb, fck, gammaC, alphacc)` | `ACIConcrete` (sobrescreve `getEcm`, `getEpsc2`, `getEpscu2`, `getFctm`) | `EC2Concrete` |
| Aço passivo | `concrete_base.ReinforcingSteel(steelName, fyk, emax, gammaS)` | `A615G60` (instância direta) | `ReinforcingSteel` |
| Deformações limite | `ReinforcedConcreteLimitStrains(EpsCU, EpsC0, SMaxStrain)` | `aciRCLimitStrains` (-3,0‰ / -2,0‰ / 10‰) | idem |
| Flexão ELU | `lsc.UniaxialBendingNormalStressControllerBase` / `Biaxial...` | `UniaxialBendingNormalStressController` | idem |
| Cortante ELU | `lsc.ShearControllerBase` | `ShearController` (~100 linhas, simplificado) | `ShearController` (~250 linhas, modelo de bielas) |
| Dados do estado limite | `lsd.ShearResistanceRCLimitStateData` etc. | `ShearResistanceRCLimitStateData.getController()` | idem |
| Famílias de armadura | `rf.RebarFamily` | `ACIRebarFamily` | `EC2RebarFamily` |

O ACI é o molde mais curto (~1.200 linhas somando os dois arquivos). O EC2 tem bielas com ângulo variável, fissuração e punção, que correspondem ao Modelo II e ao ELS da NBR.

## 2. Estrutura proposta

```
python_modules/materials/nbr6118/
    __init__.py
    NBR6118_materials.py            # concreto, aço CA-50/CA-60, diagrama
    NBR6118_limit_state_checking.py # flexão, cortante, ELS
```

### 2.1 Materiais (`NBR6118_materials.py`)

Subclasse de `concrete_base.Concrete`, como `ACIConcrete`:

- `gammaC = 1,4` e `gammaS = 1,15` (combinações normais). `fcd = fck/γc`; `fyd = fyk/γs`.
- `alphacc = 0,85` (parâmetro `alphacc` do construtor da classe base). O `fcd` do XC usa esse fator.
- `getEpscu2()` → `-3,5e-3` para fck ≤ 50 MPa. Acima disso, `-2,6e-3 - 35e-3*((90-fck)/100)^4`.
- `getEpsc2()` → `-2,0e-3` para fck ≤ 50 MPa; acima, `-2,0e-3 - 0,085e-3*(fck-50)^0,53`.
- `getFctm()` → `0,3·fck^(2/3)` (fck ≤ 50 MPa); `2,12·ln(1+0,11·fck)` acima. `fctk,inf = 0,7·fctm`; `fctk,sup = 1,3·fctm`.
- `Ecm()` → `Eci = αE·5600·√fck` (αE = 1,0 granito/gnaisse; 0,9 calcário; 0,7 arenito; 1,2 basalto), e `Ecs = αi·Eci` com `αi = 0,8 + 0,2·fck/80 ≤ 1,0`.
- Aço: `CA50 = ReinforcingSteel("CA50", fyk=500e6, emax=0.08, gammaS=1.15)`; `CA60` com 600e6; `Es = 210 GPa`.
- Limites de deformação: `nbrRCLimitStrains = ReinforcedConcreteLimitStrains(EpsCU=-3.5e-3, EpsC0=-2.0e-3, SMaxStrain=10e-3)`.

Atenção às unidades: o XC trabalha em SI (Pa, N, m) e tensões de compressão negativas (`fck=-25e6`, como em `c3000` do ACI).

### 2.2 Flexão e esforço normal (ELU)

Os controladores `UniaxialBendingNormalStressController` do ACI e do EC2 são cascas que apenas apontam para a classe base. O cálculo vem do modelo de fibras do XC, com o diagrama parábola-retângulo do concreto. Basta fornecer concreto, aço e limites de deformação corretos. A parte da NBR é só dados.

### 2.3 Cortante (`ShearController`)

Partir de `ec2.ShearController` (que já implementa ângulo de biela variável) e trocar as fórmulas:

**Modelo I (θ = 45°)**
- `VRd2 = 0,27·αv2·fcd·bw·d`, com `αv2 = 1 − fck/250` (fck em MPa)
- `Vc0 = 0,6·fctd·bw·d`, com `fctd = fctk,inf/γc`
- `Vc = Vc0` na flexão simples
- `Vsw = (Asw/s)·0,9·d·fywd·(sen α + cos α)`
- Verificação: `VSd ≤ VRd2` e `VSd ≤ Vc + Vsw`

**Modelo II (30° ≤ θ ≤ 45°)**
- `VRd2 = 0,54·αv2·fcd·bw·d·sen²θ·(cotg α + cotg θ)`
- `Vsw = (Asw/s)·0,9·d·fywd·(cotg α + cotg θ)·sen α`
- `Vc = Vc1`: igual a `Vc0` quando `VSd ≤ Vc0`, decresce linearmente até zero em `VSd = VRd2`

**Armadura mínima:** `ρsw = Asw/(bw·s·sen α) ≥ 0,2·fctm/fywk`.

Aproveitamento: o campo `d` vem do modelo de fibras (`scc.getEffectiveDepth()`, como no EC2). O ACI usa `0,9·h`, que é só uma aproximação.

### 2.4 ELS

Reaproveitar o `CrackController` do EC2 (abertura de fissura) com as expressões da NBR 6118 item 17.3.3.2 (menor entre os dois valores de wk, por σs/ρri). Flecha e tensão em serviço usam análise com `Ecs` e inércia equivalente de Branson. As verificações de flecha não estão nos módulos que li.

## 3. Pontos em aberto

1. **Compilar o XC** (WSL + CMake): sem isso, nenhum teste é possível. Os testes do próprio repositório ficam em `xc/verif/tests/` (parte das pastas `aux` não foi baixada).
2. **Combinações da NBR 8681** com ψ0/ψ1/ψ2. O XC tem módulo de combinações de ações em `python_modules/actions`, mas os coeficientes precisariam ser carregados.
3. **Detalhamento** (ancoragem, comprimento de emenda, ganchos, NBR 6118 item 9) não existe nos módulos lidos; ficaria como funções separadas.
4. **Verificação cruzada**: comparar contra um exemplo conhecido (viga biapoiada) feito no Robot ou no SMath.

## 4. Esforço estimado

- Materiais + flexão: pequeno (um arquivo, cerca de 150 linhas, copiando o ACI).
- Cortante Modelo I e II: médio.
- ELS fissuração e flecha: maior; precisa validação.
- A maior barreira é o ambiente (compilar o núcleo), não o código.
