"""End-to-end test of civilsenior-autocad against Civil 3D 2027 (cross-checks between tools).

Usage: python test_autocad.py <civilsenior-autocad.exe> <drawing copy with a corridor (.dwg)>
"""
import math
import sys
from mcp_client import McpClient

exe, dwg = sys.argv[1], sys.argv[2]
c = McpClient([exe])
print("servidor:", c.server, "| ferramentas:", len(c.tools()))
fail = 0


def check(name, ok, detail=""):
    global fail
    fail += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name} {detail}")


try:
    st = c.call("acad_status")
except RuntimeError:
    print("iniciando o Civil 3D...", c.call("acad_launch", product="civil3d", timeoutSeconds=600))
    st = c.call("acad_status")
print("versao:", st["version"])

c.call("acad_open", path=dwg)
st = c.call("acad_status")
check("desenho ativo e Civil 3D", st["civil3d"] and st["activeDrawing"].lower() == dwg.split("\\")[-1].lower(), f"({st['activeDrawing']}, unidades {st['units']})")

als = c.call("c3d_alignments")
al = als[0]
print("alinhamento:", al["name"], f"L={al['length']:.2f}", "perfis:", al["profiles"])
prof = al["profiles"][0] if al["profiles"] else ""
pts = c.call("c3d_alignment_points", alignment=al["name"], step=250, profile=prof)["points"]
check("pontos do alinhamento", len(pts) >= 2 and abs(pts[-1]["station"] - al["endStation"]) < 1e-6, f"({len(pts)} pontos, z com perfil: {pts[0]['z'] is not None})")
back = c.call("c3d_station_offset", alignment=al["name"], points=str([[p["x"], p["y"]] for p in pts]))
err = max(abs(b["station"] - p["station"]) + abs(b["offset"]) for b, p in zip(back, pts))
check("estaca/afastamento de volta", err < 1e-3, f"(erro max {err:.2e})")

surfs = c.call("c3d_surfaces")
print("superficies:", [(s["name"], s.get("minElevation"), s.get("maxElevation")) for s in surfs])
el = c.call("c3d_surface_elevations", surface=surfs[0]["name"], points=str([[p["x"], p["y"]] for p in pts]))
inside = [e for e in el if e["z"] is not None]
check("cotas da superficie", len(inside) > 0, f"({len(inside)}/{len(el)} pontos dentro, ex.: {inside[0]['z'] if inside else None})")

cors = c.call("c3d_corridors")
cor = cors[0]
print("corredor:", cor["name"], cor["baselines"])
summ = c.call("c3d_corridor_featurelines", corridor=cor["name"])["summary"]
check("resumo de linhas de feicao", len(summ) > 0, f"({len(summ)} codigos: {[s['code'] for s in summ][:6]}...)")
crown = c.call("c3d_corridor_featurelines", corridor=cor["name"], codes='["Crown"]', maxPoints=50)["featureLines"][0]
cp = crown["points"]
ax = c.call("c3d_station_offset", alignment=al["name"], points=str([[p[0], p[1]] for p in cp]))
off = max(abs(a["offset"]) for a in ax)
check("Crown sobre o eixo (afastamento ~0)", off < 0.01, f"({len(cp)}/{crown['totalPoints']} pontos, afastamento max {off:.4f})")
mesh = c.call("c3d_surface_mesh", surface=surfs[0]["name"])
check("malha da superficie", mesh["triangles"] > 0, f"({mesh['vertices']} vertices, {mesh['triangles']} triangulos)")

c.call("acad_create_layer", name="MCP_TESTE", colorIndex=1)
pl = c.call("acad_draw_polyline", points=str([[p[0], p[1], p[2]] for p in cp]), layer="MCP_TESTE")
ci = c.call("acad_draw_circle", center=f"[{cp[0][0]},{cp[0][1]}]", radius=5, layer="MCP_TESTE")
tx = c.call("acad_draw_text", text="Crown (MCP)", position=f"[{cp[0][0]},{cp[0][1]}]", height=3, layer="MCP_TESTE")
q = c.call("acad_query", layer="MCP_TESTE")
types = sorted(e["type"] for e in q["entities"])
check("entidades desenhadas na consulta", q["matched"] == 3, f"({types})")
length3d = sum(math.dist(cp[i][:3], cp[i + 1][:3]) for i in range(len(cp) - 1))
plq = [e for e in q["entities"] if e["handle"] == pl["handle"]][0]
check("comprimento da polilinha 3D", plq["length"] is not None and abs(plq["length"] - length3d) < 1e-3, f"({plq['length']:.3f} x {length3d:.3f})")
c.call("acad_modify", handles=f'["{ci["handle"]}"]', colorIndex=3)
c.call("acad_zoom_extents")
c.call("acad_save")
c.close()
print("TODOS OK" if fail == 0 else f"{fail} FALHA(S)")
sys.exit(fail)
