# Autocad-Civil3d-Tools (shtirlitsDva) — referência do CIVIL SÊNIOR

[Autocad-Civil3d-Tools](https://github.com/shtirlitsDva/Autocad-Civil3d-Tools): conjunto de plugins .NET para AutoCAD e
Civil 3D, com cerca de 440 comandos (316 em `IntersectUtilities`). Licença **GPL-3.0**. Foco principal: projeto de redes
de aquecimento distrital na Dinamarca (FJV = *fjernvarme*), com o cadastro dinamarquês de redes de utilidades (LER),
dimensionamento de tubulação e exportação para análise de tubulações (NTR/ROHR2).

## Situação nesta máquina (26/10/2026)
| Item | Situação |
|---|---|
| Clone | `C:\Users\warlen.souza\.agents\Ferramentas\Autocad-Civil3d-Tools` (raso, últimos 50 commits; `9b1a5e2`, 26/10/2026) |
| Versão alvo | AutoCAD / Civil 3D **2025** (.NET 8); referências em `C:\Program Files\Autodesk\AutoCAD 2025` e `$(AutoCADPath)` |
| Nesta máquina (2027, .NET 10) | **Não compilado nem portado.** Usar como referência de implementação |
| Build original | Visual Studio 2022 (MSBuild) ou `dotnet build Projeto.csproj --nologo -v q`; scripts `build-*.bat` na raiz |

## Partes úteis para o Civil Sênior (genéricas, fora do domínio de aquecimento distrital)
- Alinhamentos, perfis e vistas em lote: `CREATEALIGNMENTS`, `CREATEPROFILES`, `CREATESURFACEPROFILES`,
  `CREATEOFFSETPROFILES`, `CREATEPROFILEVIEWS`, `LABELALLALIGNMENTS`, `LABELPROFILEVIEWS`.
- Verificações de terreno e cotas: `CHECKSOILCOVER` (recobrimento), `CHECK3DELEVATIONS`, `CREATEELEVATIONREPORT`,
  `CALCULATESLOPE`, `CALCULATEEXCAVATIONVOLUMES`.
- Produção de folhas: `SheetCreationAutomation`, `COLORVIEWFRAMES`, `EXPORTVIEWFRAMESTODWG`, `FINALIZESHEETSAUTO`.
- Lote e limpeza: `BATCHPROCESSDRAWINGS`, `AcCoreConsoleAutomation` (desenhos em lote sem abrir o AutoCAD),
  `CLEANPLINES`, `DELETEBADENTITIES`, `FIXBROKENLABELS`.
- Exportação: `ExportShapeFiles`, `EXPORTFJVTOGEOJSON*`, `EXPORTFJVTOKML` (padrão aproveitável para outros dados),
  `ExportBlocksToSvg`.
- Conjuntos de propriedades (Property Sets) da AEC: `AecPropertySetsSHARED`, `COPYPSFROMENTTOENT`, `DSPSBROWSER`.

## Como usar com o Civil Sênior
- Para automação nesta máquina, preferir os servidores MCP do Civil Sênior (`civilsenior-autocad`) e o CivilConnection
  2027. Quando faltar uma função, este repositório mostra como ela foi resolvida na API .NET do Civil 3D (perfis,
  vistas, volumes, folhas) e serve de ponto de partida para portar só o comando necessário.
- O `AGENTS.md` do repositório tem as convenções do autor (resultados em vez de exceções, `switch` exaustivo, novos
  comandos no projeto `IntersectUtilities`). Seguir essas regras ao contribuir com ele.

## Licença e publicação
GPL-3.0: código copiado ou derivado daqui só pode ser publicado sob GPL-3.0 (por exemplo, como contribuição ao próprio
repositório) e **nunca** dentro do repositório MIT do Civil Sênior nem no fork Apache-2.0 do CivilConnection.

## Próximos passos possíveis (quando houver decisão)
1. Portar para 2027 só os comandos genéricos necessários (retarget para .NET 10 e caminhos do `D:\Autodesk\AutoCAD 2027`).
2. Expor esses comandos pelos servidores MCP via `acad_command`, depois de carregados no Civil 3D.
