# XC (xcfem) — ferramenta de referência do CIVIL SÊNIOR

[XC](https://github.com/xcfem/xc) é um programa de elementos finitos de código aberto para análise e projeto estrutural:
núcleo em C++ (derivado do OpenSees) e interface Python, com módulos de verificação por norma (ACI, EC2, EC3, EHE,
AISC, AWC NDS...), combinações de ações, seções de fibras e leitura de DXF/IFC/FreeCAD. Licença **GPL-3.0**.

## Situação nesta máquina (24/10/2026)
| Item | Situação |
|---|---|
| Clone | `C:\Users\warlen.souza\.agents\Ferramentas\xc` (atualizado até `db86416`, 24/10/2026) |
| Núcleo C++ | **Não compilado.** Só roda em Linux; no Windows exige WSL (não instalado; pede administrador e reinicialização). C: tem pouco espaço livre: instalar a distribuição no D: |
| Módulo NBR 6118 | Rascunho local, não versionado: `xc\python_modules\materials\nbr6118\` (`NBR6118_materials.py`, `NBR6118_limit_state_checking.py`, `NBR6118_serviceability.py`; ~630 linhas). Escrito de memória da norma, **sem teste** |
| Esboço do módulo | `references/xc_nbr6118_esboco.md` (estrutura proposta, fórmulas a conferir, pendências) |

Enquanto o núcleo não estiver compilado, usar o XC só como **referência de implementação** (como cada norma é
organizada: `concrete_base.Concrete`, `ReinforcingSteel`, controladores de ELU/ELS). Os cálculos NBR do Civil Sênior
continuam em `scripts/nbr6118.py`, `nbr6122.py` e `nbr8800.py`, que já foram aferidos.

## Clone no Windows: cuidados
- O repositório tem pastas `aux` (nome reservado no Windows) e dois arquivos que diferem só na caixa
  (`src/solution/analysis/analysis/Analysis.h` e `analysis.h`). O clone usa sparse checkout para deixá-los fora do disco:
  padrões `/*`, `!**/aux/`, `!/src/solution/analysis/analysis/analysis.h`, com `core.ignorecase=false` no repositório.
- Atualizar com `git -c core.protectNTFS=false pull --ff-only`. Se `analysis.h` aparecer como apagado:
  `git update-index --skip-worktree src/solution/analysis/analysis/analysis.h`.
- No Git Bash, padrões que começam com `/` viram caminhos do Windows: usar `MSYS_NO_PATHCONV=1` em `git sparse-checkout set`.
- Testes do próprio XC ficam em `verif/tests/`; os dados auxiliares deles estão nas pastas `aux`, ausentes no Windows.

## Licença e publicação
O XC é GPL-3.0. O módulo NBR 6118 importa e estende classes do XC, então é obra derivada: publicar só sob GPL-3.0
(por exemplo, como contribuição ao xcfem/xc) e **nunca** dentro do repositório MIT do Civil Sênior.

## Próximos passos possíveis (quando houver decisão)
1. Instalar WSL + Ubuntu no D: e compilar o XC (ver `install/` no clone).
2. Testar o módulo NBR 6118 contra `scripts/nbr6118.py` e a viga de aferição do Robot.
3. Usar o XC como segundo solver para conferir modelos enviados ao Robot pelo CivilConnection 2027.
