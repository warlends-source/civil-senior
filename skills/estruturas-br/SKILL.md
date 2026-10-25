---
name: estruturas-br
description: Fluxo de modelagem, analise, verificacao, detalhamento e memorial de calculo de estruturas de concreto armado, fundacoes e aco com normas brasileiras (NBR 6118, 6120, 6122, 6123, 8800), integrando Revit, Civil 3D, Robot Structural Analysis e SMath Solver. Use quando o usuario pedir dimensionar, verificar, extrair esforcos do Robot, gerar memorial de calculo (.sm) ou conectar esses programas, inclusive pelo CivilConnection 2027 (Dynamo: Civil 3D/Revit -> Robot, modelo analitico do Revit, cargas, calculo e resultados).
---

# Estruturas BR (concreto, fundacoes, aco)

Skill de apoio ao engenheiro estrutural. **O calculo e uma ajuda; a responsabilidade tecnica (ART) e do engenheiro.** Todo resultado sai com as normas citadas e os avisos de premissa. Nunca afirme conformidade com norma sem listar o que foi e o que nao foi verificado.

## Regras fixas
1. **Leitura primeiro.** Extrair do Robot/Revit/Civil 3D e mostrar o resumo antes de qualquer escrita. Nao alterar modelo, cargas ou arquivos `.rtd`/`.rvt`/`.dwg` sem pedido explicito e confirmacao.
2. **Esforcos de calculo.** As funcoes esperam valores ja majorados (gama_f, combinacao ULS). Se o Robot trouxer valores caracteristicos, majorar e dizer qual combinacao foi usada.
3. **Unidades:** kN, kN.m, m (concreto); kN, cm, kN/cm2 (aco). Converter na fronteira e explicitar.
4. **Norma brasileira primeiro.** Se nao houver (ou a funcao nao cobre), usar referencia internacional e dizer qual: Eurocode 2/3 (EN 1992/1993), ACI 318, AISC 360, ISO 2394. Nunca misturar coeficientes de normas diferentes sem avisar.
5. **O que nao esta implementado nao e inventado.** Ver `references/normas.md` (coluna "Status"). Pedir dados ao usuario ou indicar a norma.

## Fluxo
1. **Modelagem:** geometria vem do Revit/Civil 3D (JSON em coordenadas compartilhadas) ou ja esta no Robot.
2. **Analise:** Robot calculado. Extrair com `scripts/extrair_robot.py` (envoltoria N, Mz, V por barra, nas secoes 0/0,5L/1,0L).
3. **Verificacao:** usar `scripts/nbr6118.py` e `scripts/nbr8800.py`. Rodar `scripts/teste_calculos.py` apos qualquer edicao dessas bibliotecas.
4. **Detalhamento:** converter As/Asw em bitolas e espacamentos respeitando NBR 6118 cap. 18 (nao automatizado; propor e o engenheiro confirma).
5. **Memorial:** escrever um gerador por projeto a partir de UM modelo de calculo. `scripts/memorial_sm.py` gera o `.sm` do SMath com formulas vivas (nomes gregos com subscrito, fracoes e expoentes nativos); `scripts/docx_template.py` monta o Word a partir de um memorial oficial da empresa usado como template (cabecalho, estilos e tabelas preservados; so o corpo e trocado), com equacoes nativas OMML numeradas, sumario (campo TOC via Word/COM) e codigo/revisao editaveis por controles de conteudo (`definir_codigo`); `scripts/calc_ast.py` converte infixo em RPN do SMath e em OMML, com numeros pt-BR. **Regra: o memorial apresentavel (Word/PDF/SMath) NAO cita pendencias, limitacoes, scripts, "minuta" nem comparacoes internas**; isso vai para um arquivo de notas internas. Antes de gravar, conferir os resultados contra a referencia do projeto e abortar se divergir. Regras do SMath: nomes com ponto (sem sublinhado), sem `sqrt`/`min` (usar `^0.5` e `if`; no Word `if(a<=b,a,b)` vira min). `scripts/mapas_mef.py` gera mapas MEF coloridos a partir dos CSV do Robot (Pillow + numpy); `scripts/pdf_para_png.ps1` renderiza o PDF para conferir o visual. Responsavel tecnico, registro profissional e codigos de documento sao dados do projeto e ficam fora da skill.

## Ponte com os programas
- **Servidores MCP do Civil Senior (preferir quando disponiveis):** `civilsenior-autocad` (AutoCAD/Civil 3D 2027: desenho, consulta, alinhamentos estaca->coordenada, perfis, cotas de superficie, linhas de feicao de corredor) e `civilsenior-robot` (modelo, cargas, combinacoes, calculo, resultados e `robot_check_equilibrium`). Codigo em `civil-senior/mcp`, executaveis em `%LOCALAPPDATA%\CivilSenior\mcp`. Unidades: Robot em SI; AutoCAD nas unidades do desenho (`acad_status`).
- **Robot (COM):** `win32com.client.gencache.EnsureDispatch("Robot.Application")` anexa a instancia aberta. Nao usar `GetActiveObject` (falha). Colecoes: `GetAll().Count`/`.Get(i)`. Unidades da API: SI (N, m, Pa). Apoios elasticos (estacas) nao aparecem em `HasCalcSupport`.
- **SMath (.sm):** XML puro. Expressoes em RPN: `x := 5` = operand x, operand 5, operator `:` (args=2). Valores sao numeros; unidade no nome da variavel. Sem automacao ao vivo: gerar o arquivo e abrir no SMath.
- **Civil 3D 2027:** Dynamo 4.1 embutido (`Civil3DNodes.dll`: Alignment, Profile, Corridor, FeatureLine, TinSurface...). **CivilConnection 2027** (portado para .NET 10, 24/10/2026) liga Civil 3D, Revit e Robot pelo Dynamo do Revit: ver `references/civilconnection_2027.md` (nos, fluxos, afericoes, licoes).
- **Revit 2027:** via Dynamo/API ou pelo MCP do Revit (`send_code_to_revit`, socket 127.0.0.1:8080, JSON terminado em `\n`; cliente em `scripts/civilconnection/revit_mcp/rpc.py`). Revit -> Robot: `CreateRevitAnalyticalModel` (so em copia do `.rvt`) -> `FromRevitAnalytical` -> `SplitBarsAtNodes` -> `AssignSupportToColumnBases`. Devolver resultados como parametros so com confirmacao.
- **Robot, licoes da API 2027:** `CalcGamma` devolve radianos e `Gamma` recebe graus; `Calculate()` via COM funciona a partir de thread STA do .NET; conferir sempre Σ reacoes x peso (`scripts/civilconnection/robot_peso_proprio`).
- **XC (xcfem, GPL-3.0):** MEF de codigo aberto com interface Python, clonado em `Ferramentas\xc` como referencia de implementacao de normas; nucleo C++ nao compilado (exige WSL) e modulo NBR 6118 em rascunho, sem teste. Ver `references/xc.md` e `references/xc_nbr6118_esboco.md`. Nao misturar codigo do XC (GPL) em codigo MIT.

## Entrega ao usuario
Resumo curto + tabela de utilizacao (esforco / resistencia) + lista de premissas e itens nao verificados + caminho do `.sm` gerado.
