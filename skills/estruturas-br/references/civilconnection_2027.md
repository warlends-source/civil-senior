# CivilConnection 2027 + Robot (CIVIL SÊNIOR)

Ponte Civil 3D 2027 ↔ Revit 2027 (Dynamo 4.1) ↔ Robot 2027, portada do Autodesk/civilconnection (2022/2023, .NET Framework)
para .NET 10 em 24/10/2026. Tudo foi testado nos programas reais desta máquina.

## Onde está
| Item | Caminho |
|---|---|
| Código (branch `autodesk-2027`; `master` = original Autodesk) | `C:\Users\warlen.souza\.agents\Ferramentas\civilconnection` |
| Pacote Dynamo instalado | `%AppData%\Dynamo\Dynamo Revit\4.1\packages\CivilConnection2027` |
| Plugin Civil 3D (comandos de exportação) | `%AppData%\Autodesk\ApplicationPlugins\CivilPython.bundle` |
| Gráficos de exemplo | `<código>\Examples\Dynamo\2027` (Revit→Robot, Civil 3D→Robot) |
| Testes e scripts | `scripts/civilconnection/` desta skill |
| SDK .NET 10 (por usuário) | `C:\Users\warlen.souza\.dotnet10\dotnet.exe` |

Compilar: `dotnet build Src/CivilConnection/2027/Autodesk2027/Autodesk2027.csproj -c Release` (instala o pacote;
`-p:DeployPackage=false` não instala) e `dotnet build Src/CivilPython/2027/CivilPython2027.csproj -c Release`. Revit em
`D:\Revit 2027`, Civil 3D em `D:\Autodesk\AutoCAD 2027`, Robot em `D:\Autodesk\Robot Structural Analysis Professional 2027`.

## Nós `CivilConnection.Robot.RobotModel`
- **Conexão:** `Connect(newProject, structureType, lengthUnitToMeters=-1 → lê do Revit, origin)`. Robot aberto com um projeto.
- **Rótulos:** `CreateMaterial` (E em Pa, γ em N/m³ — usar E da NBR 6118, não o da biblioteca), `CreateRectangularSection`,
  `CreatePanelThickness` (com kv, N/m³), `CreateSupport`.
- **Geometria:** `CreateNodes`, `CreateBars`, `CreatePanels`, `NearestNodes`, `AssignSupport*`
  (`AssignSupportToColumnBases` = pontas inferiores livres de barras verticais, em qualquer cota).
- **Civil 3D → Robot:** `BarsFromFeaturelines`, `BarsFromAlignment`, `DeckPanelsBetweenFeaturelines`.
- **Revit → Robot:** `CreateRevitAnalyticalModel(tolerância)` → `RevitAnalyticalElements` → `FromRevitAnalytical` →
  `SplitBarsAtNodes`. Sem modelo analítico, `RevitStructuralElements` usa a geometria física (desconectada; só para
  conferência de peso/geometria).
- **Cargas:** `DeleteAllCases` (apaga o DL1 automático), `CreateLoadCase`, `AddSelfWeight`, `AddNodalForces`,
  `AddBarUniformLoads`, `AddPanelUniformLoads`, `CreateCombination`, `GenerateMesh`, `Calculate(run)`, `SaveAs`.
- **Resultados:** `NodeDisplacements`, `NodeReactions`, `BarForces`, `PanelForces` (SI: N, m, Pa).
- Cada execução do gráfico acrescenta objetos ao Robot: usar `Connect(newProject=true)`. Ordenar etapas pelas entradas `waitFor`.

## O que o Revit → Robot transfere
- Seção: retângulo maciço (concreto, barra retangular, paramétrico) → seção não padronizada; nome existente na base do
  Robot; barra redonda pelo diâmetro; propriedades do tipo Revit; **se a família não tem propriedades (comum em perfis
  de aço customizados), calcula A, Iy, Iz, Wy, Wz pela face de extremidade da peça** (J aproximado por Saint-Venant).
- Material: do ativo estrutural do Revit (E, ν, densidade × g).
- Orientação: z local do Robot = direção da altura da seção (transform da instância: BasisZ em vigas, BasisY em pilares
  verticais; rotação da seção incluída). O Robot calcula o γ (`CalcGamma`).
- Liberações dos membros analíticos (ReleaseConditions; `true` = liberado) → rótulos `REL_<início>_<fim>`.

## Aferições feitas (24/10/2026)
| Caso | Resultado |
|---|---|
| Viga biapoiada L=6 m, q=10 kN/m, 20×50, E=30 GPa | R=30 kN, M=45 kN·m, f=2,70 mm: 0,00 % |
| Viga engastada com rótulas nas pontas, dividida no meio | M=qL²/8 no meio, 0 nas pontas: 0,00 % |
| Placa 10×10×0,5 m sobre Winkler kv=20 MN/m³ | w = p/kv (G, Q e 1,4G+1,4Q): 0,00 % |
| Galpão `Est.Galpão V24` (1.383 peças) — seções | concreto 0,0 %; perfis de aço pela geometria −1,0 a +3,5 % |
| Galpão — peso no Robot × Revit | 1.107,96 × 1.108,04 kN (0,02 %) |
| Galpão — Σ reações × peso | modelo físico −17,7 %; **modelo analítico −1,3 %** (resíduo = peças soltas no Revit) |
| Galpão — orientação | z local × altura da seção: desvio máx 0,008° em 1.892 barras |
| Civil 3D — COM em .NET 10 e 5 comandos do CivilPython | todos geram o XML esperado |

Cópia do galpão com modelo analítico: `D:\Downloads\Est.Galpão V24 - analitico.rvt` (original intocado).

## Lições (não repetir os erros)
- Robot: `CalcGamma` devolve **radianos**; a propriedade `Gamma` recebe **graus**. `Calculate()` via COM funcionou
  (thread STA do .NET). O Robot não fica na ROT: `new RobotApplication()` anexa à instância aberta.
- Revit: perfis C/U/L também herdam de `StructuralSectionRectangular` — não tratar como retângulo maciço.
- Revit: linhas de locação físicas quase nunca se encontram; análise só com modelo analítico conectado.
- Ajuste de extremidades: em peças curtas o alvo mais próximo pode ser a junta da outra ponta — aceitar só se a peça
  mantiver o sentido e ≥ 50 % do comprimento; repetir as passadas até estabilizar.
- Civil 3D 2027 **não varre** `C:\ProgramData\Autodesk\ApplicationPlugins`; bundle sem `ProductCode` é ignorado em silêncio.
- MCP do Revit (add-in `mcp-servers-for-revit`, socket `127.0.0.1:8080`): JSON-RPC **terminado em `\n`**; comando
  `send_code_to_revit` executa C# dentro do Revit. Tem tempo-limite interno (~6 min): chamada que estoura continua
  rodando e **a próxima resposta chega fora de ordem**. Esperar o Robot/Revit ficarem ociosos e fazer uma chamada por vez.
  Carregar DLLs de teste num `AssemblyLoadContext` coletável, com pasta nova a cada versão.
- Alterar `.rvt` só numa cópia salva (`SaveAs`) e com o documento sem alterações pendentes.

## Testes reutilizáveis (`scripts/civilconnection/`)
- `civil3d_com/`: conecta ao Civil 3D 2027 como o CivilConnection, lista corredores/superfícies e (`--exports`) roda os 5
  comandos do CivilPython. `dotnet run -- <desenho.dwg> [--exports]`.
- `robot_afericao/`: viga, viga com rótulas dividida, placa sobre Winkler (`--calc` calcula via COM).
- `robot_peso_proprio/`: Σ reações × Σ A·L·γ × peso de referência (`dotnet run -- <peso_kN>`), conectividade.
- `robot_orientacao/`: compara o z local de cada barra com o CSV exportado por `revit_mcp/exportUp.cs`.
- `revit_mcp/rpc.py`: cliente do socket; `stepAnalytic.cs` cria o modelo analítico (na cópia); `stepA3.cs` envia ao Robot;
  `q4.cs`/`q5.cs` medem folgas e pontas livres (somente leitura).
- `dynamo/make_dyn.py`: gera os `.dyn` de exemplo.

## Pendências de engenharia (decisão do engenheiro)
- Cantoneiras de treliça costumam ser rotuladas na prática; no Revit do galpão estão todas rígidas.
- Seções por propriedades usam os eixos da peça: cantoneiras não ficam nos eixos principais.
- Lajes sobre o solo precisam de base elástica (kv) para entrar na análise.
