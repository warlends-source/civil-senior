# CIVIL SÊNIOR

Agente de apoio ao projeto estrutural para o Claude, com foco em normas brasileiras (ABNT NBR 6118, 6120, 6122, 6123,
8800) e na integração entre **Revit 2027**, **Civil 3D 2027**, **Robot Structural Analysis 2027** e **SMath Solver**.

> O cálculo é uma ajuda. A responsabilidade técnica (ART) é do engenheiro: confira premissas, normas e resultados antes
> de usar qualquer número em projeto.

## Conteúdo

| Pasta | O que é |
|---|---|
| [`skills/estruturas-br`](skills/estruturas-br) | Skill do Claude: verificações NBR 6118/6122/8800 em Python, extração de esforços do Robot (barras e cascas), geração de memoriais em SMath (`.sm`, fórmulas vivas) e Word (OMML), mapas MEF, e a ponte Civil 3D/Revit → Robot pelo CivilConnection 2027 |
| [`mcp`](mcp) | Servidores MCP `civilsenior-autocad` (AutoCAD/Civil 3D 2027) e `civilsenior-robot` (Robot 2027): o Claude desenha, lê alinhamentos, superfícies e corredores, monta e calcula modelos no Robot e confere o equilíbrio |
| [`plugins/eng3-estrutural`](plugins/eng3-estrutural) | Plugin do Claude **ENG3 — Engenharia Estrutural**: memorial de cálculo auditável, base técnica de normas e critérios, automação Revit/BIM pelo MCP do Revit e leitura de saídas de CYPE/TQS/Eberick e sondagens SPT |

### Destaques da skill `estruturas-br`
- `scripts/nbr6118.py`, `nbr6122.py`, `nbr8800.py`: flexão, cortante, punção, fissuração, flexão composta de estacas,
  capacidade Décourt-Quaresma; `teste_calculos.py` confere tudo contra um exemplo de referência (radier estaqueado C45).
- `scripts/extrair_robot.py`, `extrair_cascas.py`: leitura dos resultados do Robot pela API COM.
- `scripts/memorial_sm.py`, `docx_template.py`, `calc_ast.py`: memorial em SMath e Word a partir de um único modelo de cálculo.
- `references/civilconnection_2027.md`: nós, fluxos e aferições do **CivilConnection 2027** (Autodesk/civilconnection
  portado para .NET 10, com nós do Robot: modelo analítico do Revit, cargas, cálculo e resultados).
- `references/xc.md` e `xc_nbr6118_esboco.md`: o [XC](https://github.com/xcfem/xc) (MEF de código aberto, GPL-3.0) como
  referência de implementação de normas, com o esboço de um módulo NBR 6118. O código do módulo não está aqui, porque
  estende classes GPL do XC.
- `scripts/civilconnection/`: testes reaplicáveis (COM do Civil 3D, aferições no Robot, equilíbrio de peso próprio,
  orientação das seções) e o cliente do MCP do Revit (`send_code_to_revit`).

## Instalação

**Skill** — copie `skills/estruturas-br` para a pasta de skills do Claude Code:

```powershell
Copy-Item -Recurse .\skills\estruturas-br "$env:USERPROFILE\.claude\skills\"
```

**Plugin ENG3** — compacte o conteúdo de `plugins/eng3-estrutural` (com `.claude-plugin/plugin.json` na raiz do `.zip`) e
envie na área de plugins do claude.ai.

## Requisitos
- Windows com Revit 2027, Civil 3D 2027 e/ou Robot Structural Analysis 2027, conforme o fluxo.
- Python 3.10+ (scripts de cálculo; `pywin32` para o Robot, `Pillow` e `numpy` para os mapas).
- .NET 10 SDK para compilar os testes em C# de `scripts/civilconnection`. Os `.csproj` apontam para o código do
  CivilConnection 2027 numa pasta local; ajuste o caminho do `Compile Include` para a sua cópia.

## CivilConnection 2027
O pacote do Dynamo e o plugin CivilPython que ligam Civil 3D, Revit e Robot 2027 ficam no fork
[warlends-source/civilconnection](https://github.com/warlends-source/civilconnection) (Apache 2.0). Pacotes prontos na
[release v7.0.0-2027](https://github.com/warlends-source/civilconnection/releases/tag/v7.0.0-2027):
`CivilConnection2027-Dynamo-Revit-4.1.zip` (extrair em `%AppData%\Dynamo\Dynamo Revit\4.1\packages\`) e
`CivilPython-2027.bundle.zip` (extrair em `%AppData%\Autodesk\ApplicationPlugins\`).

## Licença
[MIT](LICENSE). O CivilConnection original é da Autodesk, sob Apache 2.0, e não está incluído aqui.
