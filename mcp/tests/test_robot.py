"""End-to-end test of civilsenior-robot: simply supported beam with known answers (Robot must be running).

L = 6 m, q = 10 kN/m, b x h = 0.20 x 0.50 m, E = 30 GPa:
reactions qL/2 = 30 kN, midspan moment qL2/8 = 45 kN.m, deflection 5qL4/(384EI) = 2.70 mm.
"""
import sys
from mcp_client import McpClient

exe = sys.argv[1]
c = McpClient([exe])
print("servidor:", c.server, "| ferramentas:", len(c.tools()))

L, q, E = 6.0, 10000.0, 30e9
I = 0.20 * 0.50 ** 3 / 12

c.call("robot_new_project", structureType="Frame3D")
c.call("robot_create_material", name="MCP_C30", youngModulus=E, poisson=0.2, unitWeight=25000)
c.call("robot_create_section", name="MCP_R20x50", material="MCP_C30", width=0.20, height=0.50)
c.call("robot_create_support", name="MCP_PIN", ux=True, uy=True, uz=True, rx=True, ry=False, rz=False)
c.call("robot_create_support", name="MCP_ROLL", ux=False, uy=True, uz=True, rx=False, ry=False, rz=False)
bars = c.call("robot_create_bars", bars='[{"start":[0,0,0],"end":[3,0,0],"section":"MCP_R20x50","material":"MCP_C30"},'
                                        '{"start":[3,0,0],"end":[6,0,0],"section":"MCP_R20x50","material":"MCP_C30"}]')["bars"]
nodes = c.call("robot_create_nodes", points="[[0,0,0],[3,0,0],[6,0,0]]")["nodes"]
c.call("robot_assign_support", nodes=f"[{nodes[0]}]", support="MCP_PIN")
c.call("robot_assign_support", nodes=f"[{nodes[2]}]", support="MCP_ROLL")
c.call("robot_create_load_case", number=1, name="Q", nature="Exploatation", deleteExisting=True)
c.call("robot_add_load", caseNumber=1, kind="bar_uniform", objects=str(bars), values=f"[0,0,{-q}]")
c.call("robot_create_load_case", number=2, name="PP", nature="Permanent")
c.call("robot_add_load", caseNumber=2, kind="self_weight", values="[1]")
calc = c.call("robot_calculate", generateMesh=False)
print("calculo:", calc)

reac = c.call("robot_reactions", caseNumber=1)
mid = c.call("robot_bar_forces", bars=f"[{bars[0]}]", caseNumber=1, points=2)[0]["stations"][-1]
uz = c.call("robot_node_displacements", nodes=f"[{nodes[1]}]", caseNumber=1)[0]["uz"]
eq = c.call("robot_check_equilibrium", caseNumber=2)

checks = [
    ("Reacao total FZ [N]", reac["total"]["fz"], q * L),
    ("|MY| no meio [N.m]", abs(mid["my"]), q * L * L / 8),
    ("|UZ| no meio [m]", abs(uz), 5 * q * L ** 4 / (384 * E * I)),
    ("Equilibrio PP: reacao [N]", eq["reactionFz"], eq["barWeight"]),
]
fail = 0
for name, got, exp in checks:
    d = abs(got / exp - 1) * 100
    ok = d <= 1.0
    fail += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name:30} MCP {got:14.6g}  esperado {exp:14.6g}  dif {d:5.2f} %")
status = c.call("robot_status")
print("status:", {k: status[k] for k in ("nodes", "bars", "resultsAvailable")}, "| casos:", status["cases"])
c.close()
print("TODOS OK" if fail == 0 else f"{fail} FALHA(S)")
sys.exit(fail)
