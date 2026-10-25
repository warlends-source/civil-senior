# Servidores MCP do CIVIL SÊNIOR

Dois servidores [MCP](https://modelcontextprotocol.io) (stdio, .NET 10) que deixam o Claude operar os programas da
Autodesk 2027 abertos na máquina, pela COM, a partir de uma thread STA dedicada que repete automaticamente as chamadas
recusadas enquanto o programa está ocupado.

| Servidor | Programa | Ferramentas |
|---|---|---|
| `civilsenior-autocad` | AutoCAD 2027 e Civil 3D 2027 | `acad_status`, `acad_launch`, `acad_open`, `acad_new`, `acad_save`, `acad_layers`, `acad_create_layer`, `acad_query`, `acad_draw_polyline`, `acad_draw_circle`, `acad_draw_text`, `acad_modify`, `acad_zoom_extents`, `acad_command`; Civil 3D: `c3d_alignments`, `c3d_alignment_points`, `c3d_station_offset`, `c3d_surfaces`, `c3d_surface_elevations`, `c3d_surface_mesh`, `c3d_corridors`, `c3d_corridor_featurelines` |
| `civilsenior-robot` | Robot Structural Analysis 2027 | `robot_status`, `robot_launch`, `robot_new_project`, `robot_open`, `robot_save`, `robot_create_material`, `robot_create_section`, `robot_create_thickness`, `robot_create_support`, `robot_create_nodes`, `robot_create_bars`, `robot_create_panel`, `robot_assign_support`, `robot_split_bars_at_nodes`, `robot_nearest_nodes`, `robot_create_load_case`, `robot_add_load`, `robot_create_combination`, `robot_calculate`, `robot_node_displacements`, `robot_reactions`, `robot_bar_forces`, `robot_panel_forces`, `robot_check_equilibrium` |

Complementa o **MCP oficial da Autodesk** para AutoCAD (`MCPHTTPSTART` dentro do AutoCAD), que consulta e altera
propriedades de objetos e estilos do Civil 3D, mas não cria geometria, não lê dados de engenharia do Civil 3D e não existe
para o Robot.

## Instalação

Requisitos: Windows, .NET 10 (runtime), os programas na versão 2027. Para as linhas de feição de corredor e as malhas de
superfície, o plugin **CivilPython** do CivilConnection 2027 instalado em `%APPDATA%\Autodesk\ApplicationPlugins`.

```powershell
dotnet publish mcp\AutoCad\CivilSenior.Mcp.AutoCad.csproj -c Release -o "$env:LOCALAPPDATA\CivilSenior\mcp\autocad"
dotnet publish mcp\Robot\CivilSenior.Mcp.Robot.csproj -c Release -o "$env:LOCALAPPDATA\CivilSenior\mcp\robot"
claude mcp add --scope user civilsenior-autocad -- "$env:LOCALAPPDATA\CivilSenior\mcp\autocad\civilsenior-autocad.exe"
claude mcp add --scope user civilsenior-robot -- "$env:LOCALAPPDATA\CivilSenior\mcp\robot\civilsenior-robot.exe"
```

O projeto do Robot lê a interop de `D:\Autodesk\Robot Structural Analysis Professional 2027` ou de
`C:\Program Files\Autodesk\...`; outro local: `-p:RobotPath=...`. Os caminhos do `acad.exe` e do `robot.EXE` usados por
`acad_launch` e `robot_launch` ficam em `AcadSession.cs` e `RobotSession.cs`.

## Convenções
- **Robot:** unidades SI (m, N, N·m, Pa, N/m³); cargas para baixo são negativas em z. `robot_check_equilibrium` compara a
  reação total de um caso de peso próprio com Σ A·L·γ das barras e conta as pontas de barra soltas.
- **AutoCAD/Civil 3D:** unidades do desenho (`acad_status` informa `INSUNITS`). Pontos em JSON: `[[x,y],...]` ou `[[x,y,z],...]`.
- `acad_command` executa texto na linha de comando: use as versões de linha de comando (prefixo `-`), porque uma janela de
  diálogo aberta bloqueia o AutoCAD.
- Os servidores só se conectam a programas já abertos (ou que eles mesmos iniciam com `*_launch`) e não fecham nada.

## Testes
`tests/test_robot.py` (viga biapoiada: reações, momento, flecha e equilíbrio com 0,00 %) e `tests/test_autocad.py`
(conferências cruzadas no Civil 3D: estaca ↔ coordenada, linha de feição `Crown` sobre o eixo, entidades desenhadas):

```powershell
python mcp\tests\test_robot.py "$env:LOCALAPPDATA\CivilSenior\mcp\robot\civilsenior-robot.exe"
python mcp\tests\test_autocad.py "$env:LOCALAPPDATA\CivilSenior\mcp\autocad\civilsenior-autocad.exe" C:\caminho\copia.dwg
```

`RobotLink.cs` vem do CivilConnection 2027 (Apache-2.0, cabeçalho original mantido).
