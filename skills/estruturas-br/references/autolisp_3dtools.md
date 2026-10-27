# AutoLISP-3DTools (Alejandro Burgueño Díaz) — referência do CIVIL SÊNIOR

[AutoLISP-3DTools](https://github.com/retrospectivePreposterous/AutoLISP-3DTools): 8 rotinas AutoLISP (2020) para
modelagem 3D no AutoCAD. **Sem arquivo de licença:** todos os direitos são do autor. Uso local permitido; não
redistribuir nem copiar o código para os repositórios do Civil Sênior.

Clone: `C:\Users\warlen.souza\.agents\Ferramentas\AutoLISP-3DTools` (`6d96bca`, 23/10/2020). Revisado em 26/10/2026:
nenhuma chamada fora do desenho (sem shell, arquivos ou registro) e parênteses balanceados nos 8 arquivos. **Ainda não
executado** no AutoCAD/Civil 3D 2027.

| Comando | Arquivo | O que faz |
|---|---|---|
| `MPA` | `MPathArray_MPA.lsp` | Vários arranjos de um bloco ao longo de caminhos (o bloco deve estar voltado para a direita) |
| `QDZ` | `QuickDiscretization_QDZ.lsp` | Polilinhas 3D com número fixo de segmentos sobre arcos, círculos, elipses e polilinhas 2D/3D |
| `S3D` | `SplineIn3DFaces_S3D.lsp` | Cria splines em cada 3DFACE |
| `SSH` | `SuperHollow_SSH.lsp` | Subtrai vários objetos de vários objetos 2D em planta |
| `SSC` | `SuperSlice_SSC.lsp` | Corta vários sólidos ou superfícies com uma polilinha em planta |
| `SSB` | `SuperSubtract_SSB.lsp` | Subtrai vários objetos de vários elementos sem uni-los |
| `STS` | `SurfacesToSolids_STS.lsp` | Sólidos 3D com espessura a partir de superfícies selecionadas |
| `ZFS` | `ZFixedSweep_ZFS.LSP` | Varredura de seção retangular ao longo de caminhos sem girar a seção (mantém Z) |

Usos no Civil Sênior: sólidos de estruturas e de escavação a partir de superfícies (`STS`, `SSC`, `SSB`), discretizar
eixos curvos antes de levar ao Robot (`QDZ`) e modelar elementos lineares sem torção (`ZFS`, por exemplo vigas e
guarda-corpos ao longo de alinhamentos).

## Carregar no AutoCAD/Civil 3D 2027
Com `SECURELOAD = 1` (padrão), um LISP fora das pastas confiáveis abre uma caixa de diálogo, e uma janela aberta
bloqueia a automação pelo MCP. Opções: copiar os `.lsp` para uma pasta já confiável (por exemplo
`%APPDATA%\Autodesk\C3D 2027\enu\Support`) ou incluir a pasta do clone em `TRUSTEDPATHS`; as duas mudam a configuração
do usuário e devem ser combinadas com ele. Depois: `(load "QuickDiscretization_QDZ.lsp")` e o comando (`QDZ`), também pelo
`acad_command` do servidor `civilsenior-autocad`. As rotinas pedem seleção e valores na tela (`getdist`, `ssget`), então
servem melhor para uso interativo do que para automação total.
