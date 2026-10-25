---
name: revit-bim
description: >
  Esta skill deve ser usada quando o usuário pedir qualquer coisa envolvendo
  Revit ou modelo BIM: "extrair quantitativo", "gerar pranchas", "criar tabela
  de quantidades", "auditar o modelo", "verificar interferências", "clash
  detection", "exportar para Excel", "renomear vistas", "criar folhas",
  "limpar o modelo", "quantos elementos tem", "listar avisos do Revit",
  "conferir famílias", "sincronizar parâmetros por CSV". Define a ordem de
  operações segura para as ferramentas do servidor revit-mcp, a classificação
  de risco de cada família de comandos e os fluxos que já vêm prontos.
metadata:
  version: "0.1.0"
  audience: agent
---

# Revit / BIM via revit-mcp

O servidor `revit-mcp` expõe mais de 150 ferramentas contra o modelo **aberto**
no Revit da máquina do usuário. Elas agem no arquivo real, em tempo real. Esta
skill define como usá-las sem estragar o modelo.

## Regra de ouro

**Ler antes de escrever. Sempre.** Nenhuma operação de escrita acontece antes de
uma leitura que confirme o estado atual e o conjunto exato de elementos
afetados. Contagem de elementos que serão alterados **é apresentada ao usuário
antes** de qualquer operação em lote.

## Classificação de risco

### Nível 0 — Leitura, livre

Rodar à vontade para entender o modelo antes de qualquer coisa.

`get_project_info` · `get_current_view_info` · `get_current_view_elements` ·
`get_selected_elements` · `get_element_parameters` · `get_worksets` ·
`get_elements_by_workset` · `get_phases` · `get_materials` ·
`get_material_quantities` · `get_warnings` · `get_shared_parameters` ·
`get_compound_structure` · `get_linked_elements` · `get_room_openings` ·
`get_schedule_data` · `get_available_family_types` · `list_schedulable_fields` ·
`list_family_sizes` · `analyze_model_statistics` · `check_model_health` ·
`check_family_health` · `audit_families` · `lines_per_view_count` ·
`find_untagged_elements` · `find_undimensioned_elements` · `calculate_rai` ·
`export_*` · `query_stored_data`

### Nível 1 — Criação aditiva, confirmar escopo

Cria coisa nova sem apagar nada. Confirmar quantidade e nomenclatura antes.

`create_view` · `create_sheet` · `batch_create_sheets` ·
`create_placeholder_sheets` · `duplicate_view` · `duplicate_sheet_*` ·
`place_viewport` · `create_schedule` e variantes · `create_view_template` ·
`create_view_filter` · `create_text_note` · `create_filled_region` ·
`create_dimensions` · `create_material` · `create_workset` ·
`create_revision` · `add_shared_parameter` · `create_level` · `create_grid` ·
`create_room`

### Nível 2 — Modificação em lote, exigir aprovação explícita

Altera elementos existentes. **Apresentar a lista (ou a contagem e uma amostra)
e obter "pode aplicar" antes de executar.**

`bulk_modify_parameter_values` · `set_element_parameters` · `batch_rename` ·
`add_prefix_suffix` · `rename_views` · `rename_families` · `renumber_elements` ·
`change_element_type` · `modify_element` · `operate_element` ·
`override_graphics` · `color_elements` · `apply_view_template` ·
`batch_modify_view_range` · `set_view_crop` · `set_element_workset` ·
`set_element_phase` · `set_compound_structure` · `set_material_*` ·
`sync_csv_parameters` · `import_from_excel` · `transfer_parameters` ·
`match_element_properties` · `manage_project_parameters`

### Nível 3 — Destrutivo, tratar como operação crítica

Apaga ou executa código arbitrário. **Nunca por iniciativa própria.** Exigir
pedido explícito do usuário, avisar que a operação é destrutiva, e confirmar
que há backup ou que o modelo está sincronizado antes.

`delete_element` · `delete_selection` · `delete_schedule` · `delete_workset` ·
`clear_parameter_values` · `purge_unused` · `cad_link_cleanup` ·
`wipe_empty_tags` · `send_code_to_revit`

**`send_code_to_revit` executa código arbitrário dentro do Revit.** É a
ferramenta mais perigosa do conjunto. Usar apenas quando nenhuma ferramenta
específica resolve, mostrando o código ao usuário antes e explicando o que ele
faz. Nunca usá-la para contornar uma confirmação recusada.

## Antes de qualquer sessão de trabalho

```
1. get_project_info          → confirmar que o modelo aberto é o esperado
2. get_current_view_info     → saber onde o Revit está posicionado
3. get_worksets              → modelo colaborativo? qual workset ativo?
4. get_warnings              → estado de saúde antes de mexer
```

Modelo em workshare: alertar o usuário para sincronizar antes de operações de
nível 2 ou 3, e lembrar que alterações ficam no workset ativo.

## Fluxos prontos

O servidor expõe fluxos compostos. Preferi-los a orquestrar ferramentas soltas
quando o objetivo bate:

| Objetivo | Ferramenta |
|----------|-----------|
| Auditoria completa do modelo | `workflow_model_audit` |
| Revisão de interferências | `workflow_clash_review` |
| Ida e volta de dados (Revit → Excel → Revit) | `workflow_data_roundtrip` |
| Documentação de ambientes | `workflow_room_documentation` |
| Montagem de conjunto de pranchas | `workflow_sheet_set` |

Rodar o fluxo, ler o resultado, e só então decidir as ações pontuais.

## Receitas frequentes

### Quantitativo de estrutura para orçamento

```
get_material_quantities         → volumes por material
create_material_takeoff_schedule → tabela nativa no modelo
export_schedule / export_to_excel → planilha
```

Conferir o total contra `analyze_model_statistics` antes de entregar. Divergência
entre a tabela e a estatística do modelo quase sempre significa elemento fora de
fase, em workset não carregado, ou modelado como genérico.

### Conjunto de pranchas

```
manage_unplaced_views     → o que ainda não está em prancha
create_placeholder_sheets → reservar a numeração
batch_create_sheets       → criar em lote
place_viewport            → posicionar
align_viewports           → alinhar entre pranchas
create_sheet_list_schedule → índice de pranchas
```

Fechar a numeração com o usuário **antes** de criar. Renumerar prancha depois é
retrabalho que se propaga para carimbo, índice e ART.

### Auditoria antes de entrega

```
check_model_health · get_warnings · audit_families · lines_per_view_count
find_untagged_elements · find_undimensioned_elements · calculate_rai
```

Entregar como relatório com prioridade, não como despejo de lista. Avisos do
Revit por si só não são defeito de projeto — separar o que afeta o resultado
estrutural do que é ruído de modelagem.

### Sincronizar parâmetros por planilha

```
export_elements_data → o usuário edita → sync_csv_parameters (nível 2)
```

Antes de aplicar: mostrar quantos elementos e quais parâmetros mudam, e uma
amostra de 5 linhas do antes/depois.

## Ponte com o Robot (CivilConnection 2027 — CIVIL SÊNIOR)

Para levar o modelo do Revit (ou de um corredor do Civil 3D) ao Robot Structural
Analysis, usar o **CivilConnection 2027** do agente CIVIL SÊNIOR. Referência
completa (nós, fluxos, aferições, lições):
`C:\Users\warlen.souza\.claude\skills\estruturas-br\references\civilconnection_2027.md`.

Fluxo Revit → Robot e nível de risco de cada passo:

| Passo | Nível |
|-------|-------|
| Medir folgas entre peças e pontas livres (`q4.cs`, `q5.cs` via `send_code_to_revit`) | 0 |
| `SaveAs` de uma cópia do `.rvt` — o documento não pode ter alterações pendentes | 1 |
| `CreateRevitAnalyticalModel` (cria membros/painéis analíticos e ajusta extremidades até a tolerância) — **só na cópia** | 2 |
| `FromRevitAnalytical` → `SplitBarsAtNodes` → `AssignSupportToColumnBases` (escreve no Robot, não no Revit) | 0 no Revit |

- Análise só com o **modelo analítico conectado**: as linhas de locação físicas
  quase nunca se encontram (no galpão de teste, o modelo físico perdia 17,7 % do
  peso nas reações; o analítico, 1,3 %).
- Conferir sempre Σ reações × peso antes de usar qualquer esforço.

Particularidades do servidor `mcp-servers-for-revit` (socket 127.0.0.1:8080),
observadas em 24/10/2026:

- JSON-RPC **terminado em quebra de linha**; sem ela a chamada fica pendurada.
- `send_code_to_revit` executa C# dentro do Revit (`transactionMode`: `auto`
  envolve em transação; `none` para `SaveAs` e leitura).
- Tempo-limite interno de cerca de 6 minutos: a chamada que estoura **continua
  rodando** e a resposta seguinte chega fora de ordem. Esperar o Revit (e o
  Robot) ficarem ociosos e fazer uma chamada por vez.

## Limites honestos

- **O Revit precisa estar aberto** com o modelo carregado. Ferramenta que falha
  por modelo fechado não é problema a contornar — avisar e parar.
- **Não há desfazer confiável através do MCP.** O Ctrl+Z do Revit pode não
  agrupar a operação como você espera. Tratar toda escrita como definitiva.
- **O MCP não substitui o julgamento estrutural.** Quantitativo extraído do
  modelo vale o que vale o modelo. Antes de usar número de BIM em memorial de
  cálculo, confirmar que o modelo reflete o projeto dimensionado — e citar isso
  como fonte do dado (regra 1 da skill `memorial-de-calculo`).
- **Modelo federado / vinculado**: `get_linked_elements` lê os vínculos, mas
  escrita não atravessa o vínculo. Alteração em arquivo linkado é feita
  abrindo aquele arquivo.
