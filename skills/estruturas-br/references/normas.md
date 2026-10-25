# Mapa de normas e status de implementacao

Status: **OK** = implementado e testado a mao; **Parcial** = so um caso; **Pendente** = nao implementado (nao improvisar).

| Tema | Norma | Status | Arquivo / observacao |
|---|---|---|---|
| Flexao simples, secao retangular (As, armadura dupla, As,min/max) | NBR 6118:2023 17.2, tab. 17.3 | OK (fck ate 50; MRd e As,min conferidos com o memorial 91101) | `nbr6118.flexao_retangular` |
| Cisalhamento, estribos verticais, modelo I | NBR 6118:2023 17.4.2.2 | OK (flexao simples) | `nbr6118.cisalhamento_modelo1` |
| Cortante de laje/radier sem armadura transversal (VRd1) | NBR 6118:2023 19.4.1 | OK (563,5 kN/m conferido com o memorial 91101) | `nbr6118.vrd1_laje` |
| Esforcos de casca do radier (extracao Robot) + verificacao do cortante vs VRd1 | NBR 6118:2023 19.4.1, 17.4.1.2.1 | OK (reproduz o memorial 91101; G4 a parte) | `extrair_cascas.py`, `verificar_cortante_radier.py` |
| Puncao em pilar/estaca circular de canto (contorno C' truncado, tau_Sd x tau_Rd1/Rd2) | NBR 6118:2023 19.5 | OK p/ canto circular (u, area, Wp, tau conferidos com o memorial 91101); FSd e momentos sao entradas; contorno C (face) e estacas de borda/internas pendentes | `nbr6118.contorno_punçao_canto`, `nbr6118.puncao_verificacao` |
| Abertura de fissuras ELS-W em laje/radier (estadio II, wk=min(w1,w2)) | NBR 6118:2023 17.3.3.2 | OK (x, sigma_s, wk1, wk2 conferidos com o memorial 91101); Mk da combinacao frequente e entrada | `nbr6118.fissuracao_laje` |
| Flexao do radier a partir de mxx/myy de casca (Md vs MRd, As,min 0,67 rho_min inf / rho_min sup) | NBR 6118:2023 17.2, 17.3.5.2.1, tab. 17.3 | OK (Md/MRd inf 0,88 e sup 0,10 conferidos com o memorial 91101; G4 a parte; sem Wood-Armer) | `nbr6118.momento_resistente`, `as_minima_laje`, `verificar_flexao_radier.py` |
| Flexao composta de estaca circular (diagrama N-M por integracao, rho_min, tensao media, cortante simplificado) | NBR 6118:2023 17.2; parametros de estaca NBR 6122:2019 | OK p/ MRd, Md/MRd, rho e sigma_media (conferidos com o memorial 91101); gamma_c=5,0 (fcd=8,0 MPa) e dado do memorial, a conferir na norma; cortante da estaca NAO conferido | `nbr6118.verificar_estaca`, `momento_resistente_circular`, `interacao_circular` |
| Cisalhamento modelo II, torcao, flexo-compressao, pilares esbeltos | NBR 6118 17.4, 17.5, 15 | Pendente | |
| ELS (fissuracao, flecha), punçao, ancoragem/detalhamento | NBR 6118 cap. 17-19 | Pendente | Ref. alternativa: EN 1992-1-1 |
| Tracao, compressao (flambagem global) | NBR 8800:2008 5.2, 5.3 | Parcial | `nbr8800`; FLT/flexo-torcional e Q nao calculados |
| Momento resistente | NBR 8800 5.4.2 | Parcial | so secao compacta e travada |
| Cortante | NBR 8800 5.4.3 | Parcial | so alma com lambda <= lambda_p |
| Interacao N+M | NBR 8800 5.5.1.2 | OK | `nbr8800.interacao_NM` |
| Ligacoes (parafusos, solda) | NBR 8800 cap. 6 | Pendente | Ref. alternativa: AISC 360 cap. J |
| Capacidade de carga de estacas - Decourt-Quaresma (PL, PP, Padm, FS global) | NBR 6122:2019 | OK (SP 01 + relatorio TQS + memorial 91101: PL 136,05; PP 112,53; Padm 124,3 tf; FS 2,48; sensibilidade 116,9 tf); alfa/beta/C sao entradas | `nbr6122.decourt_quaresma`, `fs_global_sistema` |
| Capacidade de carga - Aoki-Velloso, Antunes-Cabral, Velloso, Philipponnat, Alonso, David Cabral | NBR 6122:2019 | Pendente | fatores K/alfa por solo e tipo de estaca; os valores do TQS estao no relatorio, mas nao foram reproduzidos |
| Sapatas (tensao admissivel, recalque) | NBR 6122:2019 | Pendente | |
| Blocos sobre estacas (bielas e tirantes) | NBR 6118 22.3 | Pendente | |
| Cargas permanentes e acidentais | NBR 6120:2019 | Manual | usar tabelas da norma; registrar no memorial |
| Vento | NBR 6123:1988 | Manual | V0, S1/S2/S3, Ce, Cp: calcular e registrar; nao automatizado |
| Combinacoes de acoes | NBR 8681 | Manual | conferir combinacoes ULS/SLS do Robot |
| Sismo | NBR 15421 | Manual | |

## Itens complementares do projeto de referencia (secoes 8 a 14 do memorial gerado)
Todos reproduzem numeros do memorial 91101 R0 (conferencia automatica no gerador; aborta se divergir):
| Tema | Base | Status |
|---|---|---|
| Cargas verticais, vento (S2, Vk, q, Fw, Mw) e G4 | NBR 6123:2023 | OK, procedimento e dados do memorial (S2 do topo em toda a altura) |
| Tombamento, excentricidade, tracao na estaca, levantamento do costado | NBR 8681 (0,9/1,4) | OK (11.1.6 do memorial) |
| Recalque medio e distorcao angular (global 1/1.158; local a ~5 m 1/879) | recalques nodais do Robot | OK: distorcao reproduzida a partir de `estaq_R_rev_C45_nos.csv`, comb. 25 + 0,184 do vento |
| Interacao solo-estrutura, formulas finais de Randolph (1994) | Randolph | OK nas formulas finais; modelo acoplado (Mindlin/Boussinesq) NAO reexecutado |
| Puncao nas estacas de borda e internas (FSd < 0, nao governa) | NBR 6118:2023 19.5 | OK: `nbr6118.geometria_contorno` + `forca_liquida_puncao`; E8 = -1.733 kN, E7 = -4.710 kN (memorial -1.734 e -4.711) |
| Cortante da estaca (bw = D, d = 0,9 D, Vc0, gamma_c da tabela de estacas) | NBR 6118:2023 17.4 | Simplificado, nao consta do memorial R0 |
| Ancoragem basica do arranque (lb, aderencia boa/ma) | NBR 6118:2023 9.3 | Informativo: ma aderencia com sigma_s = fyd da 727 mm > 670 mm disponiveis (1,09): CONFERIR a tensao real nas barras |
| Dispersao entre metodos (TQS: Aoki-Velloso 62,3 tf; Antunes-Cabral 86,2; Pedro Paulo Velloso 115,8; Decourt-Quaresma 124,3) | NBR 6122:2019 | Valores do relatorio apenas registrados; Aoki-Velloso e Antunes-Cabral ficam abaixo da carga maxima de servico (988,3 kN) com os parametros do relatorio: calibrar parametros ou prova de carga (NBR 12131) |
O corpo do item 15 (pendencias) do memorial R0 nao consta do arquivo-base C45_3.

## Edicoes adotadas no projeto de referencia
NBR 6118:2023, NBR 6122:2019 (Emenda 1:2022), NBR 6123:2023, NBR 6484:2020, NBR 8681:2003, NBR 12655:2022, NBR 14931:2023. A numeracao dos itens muda entre edicoes: conferir item a item.

## Coeficientes usados (confirmar na edicao vigente)
- Concreto: gama_c = 1,4; aco: gama_s = 1,15 (combinacao normal).
- Aco estrutural NBR 8800: gama_a1 = 1,10; gama_a2 = 1,35.
- Limite de x/d: 0,45 (fck <= 50 MPa), 0,35 (fck > 50).

## Como ampliar
Adicionar a funcao em `scripts/`, um caso conferido a mao em `teste_calculos.py`, e atualizar a tabela acima. So marcar "OK" depois do teste.
