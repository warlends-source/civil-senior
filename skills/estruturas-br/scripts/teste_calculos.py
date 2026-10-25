"""Autoteste: compara com contas feitas a mao. Rodar: python teste_calculos.py"""
import nbr6118 as c, nbr8800 as a

def prox(x, y, tol): assert abs(x - y) <= tol, (x, y)

# Flexao: bw=20, h=50, d=45 cm, fck=25, CA-50, Md=140 kN.m  -> As ~ 8,24 cm2 (a mao)
r = c.flexao_retangular(140, 0.20, 0.50, 0.45, 25)
prox(r["As_calc_cm2"], 8.24, 0.1); prox(r["xi"], 0.3276, 0.002)
# Armadura dupla: Md alto
r2 = c.flexao_retangular(250, 0.20, 0.50, 0.45, 25)
assert r2["As_comprimida_cm2"] > 0 and r2["avisos"]
# Cisalhamento: Vsd=150 kN -> Vc=69,25 kN; Asw/s ~ 4,59 cm2/m; VRd2 ~ 390 kN
v = c.cisalhamento_modelo1(150, 0.20, 0.45, 25)
prox(v["Vc_kN"], 69.25, 0.3); prox(v["Asw_s_calc_cm2_m"], 4.59, 0.05); prox(v["VRd2_kN"], 390.5, 1.0)
# Aco: tracao Ag=50 cm2, fy=34,5 -> 1568 kN
t = a.tracao(50, 40, 34.5, 45.0)
prox(t["Nt_Rd_escoamento_kN"], 1568.2, 0.5)
# Compressao: chi limites
k = a.compressao(50, 34.5, 5000, 300)
assert 0 < k["chi"] <= 1
prox(a.interacao_NM(100, 500, 20, 100)["utilizacao"], 100/500 + 8/9*0.2, 1e-9)
# --- Validacao contra o exemplo de referencia (radier estaqueado C45) (radier C45, d=0,92 m) ---
# MRd da face inferior: As = 20,94 cm2/m, fck=45, b=1 m -> 822,4 kN.m/m (memorial)
fcd = 45/1.4*1000; fyd = 500/1.15*1000; As = 20.94e-4
x = As*fyd/(0.68*fcd*1.0); MRd = As*fyd*(0.92-0.4*x)
prox(MRd, 822.4, 0.5)
# armadura minima C45: rho_min = 0,194 % -> 19,40 cm2/m na face superior
r3 = c.flexao_retangular(87.4, 1.0, 1.0, 0.92, 45)
prox(r3["As_min_cm2"], 19.40, 0.01)
# VRd1 sem armadura transversal: 563,5 kN/m (memorial, item 11.2.2)
prox(c.vrd1_laje(0.92, 20.94e-4, 45)["VRd1_kN"], 563.5, 0.5)
# --- Puncao, estaca de canto E16 (memorial 11.2.3) ---
g = c.contorno_punçao_canto(0.35, 0.935, 1.40, 1.40)
prox(g["u_m"], 6.517, 0.002); prox(g["area_interna_m2"], 11.61, 0.01); prox(g["Wp_x_m2"], 9.14, 0.01)
pz = c.puncao_verificacao(297.7, 116.4, 95.4, g["u_m"], g["Wp_x_m2"], g["Wp_y_m2"], 0.935, 45, 0.00224)
prox(pz["tau_Sd_kPa"], 63.7, 0.1); prox(pz["tau_Rd1_MPa"], 0.411, 0.001); prox(pz["tau_Rd2_MPa"], 7.116, 0.002)
# --- ELS-W (memorial 11.2.4): Mk=512,9; x=14,13 cm; sigma_s=280,6; wk1=0,211; wk2=0,424 ---
fz = c.fissuracao_laje(512.9, 0.92, 20.94, 20, 5.0, 15.0, 45)
prox(fz["x_cm"], 14.13, 0.01); prox(fz["sigma_s_MPa"], 280.6, 0.1)
prox(fz["wk1_mm"], 0.211, 0.001); prox(fz["wk2_mm"], 0.424, 0.001); assert fz["ok"]
# --- Flexao do radier (memorial 11.2.1) ---
prox(c.momento_resistente(20.94, 0.92, 45)["MRd_kNm"], 822.4, 0.2)
prox(c.momento_resistente(20.94, 0.925, 45)["MRd_kNm"], 826.9, 0.3)
prox(c.as_minima_laje(45, 1.0, bidirecional_positivo=False), 19.40, 0.01)   # face superior
prox(c.as_minima_laje(45, 1.0, bidirecional_positivo=True), 13.00, 0.01)    # face inferior (0,67)
# --- Estaca E16 (memorial 11.3): Nd=1335, Md=187,5, Hd=36,9; MRd=351,3; rho=0,65 %; sig=3,59 MPa (Nd,max=1381,7) ---
e = c.verificar_estaca(1335, 187.5, 36.9, 0.70, 8, 20, 0.275, 40, 5.0)
prox(e["MRd_kNm"], 351.3, 0.5); prox(e["Md_MRd"], 0.53, 0.01); prox(e["rho"]*100, 0.65, 0.01)
prox(e["sigma_media_MPa"], 1335/(3.14159265*0.35**2)/1000, 1e-6)
prox(1381.7/(3.14159265*0.35**2)/1000, 3.59, 0.01)
assert e["ok"] and e["MRd_conservador_kNm"] < e["MRd_kNm"] and e["Md_MRd_conservador"] < 0.56
# --- Capacidade de estaca: Decourt-Quaresma, SP 01 / TQS / memorial 11.1.1 ---
import nbr6122 as g
# NSPT (30 cm finais) da SP 01, amostras 1..11, com nega = 50 (amostras 7 e 8); nivel = amostra-1 abaixo da cabeca (1 m)
spt = {1: 5, 2: 5, 3: 16, 4: 28, 5: 33, 6: 50, 7: 50, 8: 21, 9: 15, 10: 18}
dq = g.decourt_quaresma(spt, 0.70, 8.0, 0.85, 0.80, 12.0)
prox(dq["NL"], 26.0, 1e-9); prox(dq["Np"], 28.667, 0.001)
prox(dq["PL_tf"], 136.05, 0.01); prox(dq["PP_tf"], 112.53, 0.01); prox(dq["Pult_tf"], 248.58, 0.02)
prox(dq["PL13_PP4_tf"], 132.78, 0.02); prox(dq["Padm_tf"], 124.29, 0.02)
prox(dq["padm_kN_memorial"], 1219.0, 1.0)
prox(g.fs_global_sistema(16, 248.58, 15734.86), 2.48, 0.01)
# sensibilidade do memorial: NL restrito aos niveis 2..7 (22,83) -> PL=121,2; Pult=233,7; Padm=116,9 tf (1.146 kN)
dr = g.decourt_quaresma(spt, 0.70, 8.0, 0.85, 0.80, 12.0, nl_niveis=[1, 2, 3, 4, 5, 6])
prox(dr["NL"], 22.8333, 0.001); prox(dr["PL_tf"], 121.2, 0.05); prox(dr["Pult_tf"], 233.7, 0.1)
prox(dr["Padm_tf"], 116.9, 0.1); prox(dr["padm_kN_memorial"], 1146.0, 1.0)
# curva PL acumulada do relatorio TQS: cota -3 -> 20,53 tf; cota -5 -> 59,82 tf
d3 = g.decourt_quaresma({1: 5, 2: 5, 3: 16, 4: 28}, 0.70, 3.0, 0.85, 0.80, 12.0)
prox(d3["PL_tf"], 20.53, 0.01)
# --- Secao circular por fibras: tensao real nas barras do arranque (E16: Nd=1335, Md=187,5) ---
import secao_fibras as sf
fb = sf.analisa(1335, 187.5, 0.70, 8, 20, 0.275, 8.0)
prox(fb["N"], 1335, 1.0); prox(fb["M"], 187.5, 0.5); prox(fb["sig_tracao_max"], 49.8, 0.6)
fu = sf.analisa(1335, 351.2, 0.70, 8, 20, 0.275, 8.0)       # no estado limite a barra tracionada chega a fyd
prox(fu["sig_tracao_max"], 434.8, 1.0)
print("todos os testes passaram")
