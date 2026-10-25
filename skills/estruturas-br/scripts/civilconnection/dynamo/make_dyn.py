# Generates the Dynamo 4.1 example graphs for the CivilConnection 2027 Robot nodes.
# Each graph is one Code Block (one output port per statement) plus Watch nodes on chosen statements.
import json, sys, uuid, os

OUT = sys.argv[1]


def gid():
    return uuid.uuid4().hex


def port(name, desc):
    return {"Id": gid(), "Name": name, "Description": desc, "UsingDefaultValue": False,
            "Level": 2, "UseLevels": False, "KeepListStructure": False}


def graph(name, description, lines, watches, notes):
    code = "\n".join(lines)
    statements = [l for l in lines if l.strip() and not l.strip().startswith("//")]
    names = [s.split("=")[0].strip() for s in statements]
    cb_id = gid()
    outputs = [port("", "Value of expression at line %d" % (i + 1)) for i in range(len(statements))]
    nodes = [{
        "ConcreteType": "Dynamo.Graph.Nodes.CodeBlockNodeModel, DynamoCore",
        "Id": cb_id, "NodeType": "CodeBlockNode", "Inputs": [], "Outputs": outputs,
        "Replication": "Disabled", "Description": "Allows for DesignScript code to be authored directly",
        "Code": code}]
    views = [{"Id": cb_id, "Name": "CivilConnection Robot", "IsSetAsInput": False, "IsSetAsOutput": False,
              "Excluded": False, "ShowGeometry": True, "X": 0.0, "Y": 0.0}]
    connectors = []
    for k, var in enumerate(watches):
        idx = names.index(var)
        w_id = gid()
        w_in, w_out = port("", "Node to show output from"), port("", "Node output")
        nodes.append({"ConcreteType": "CoreNodeModels.Watch, CoreNodeModels", "WatchWidth": 320.0, "WatchHeight": 200.0,
                      "Id": w_id, "NodeType": "ExtensionNode", "Inputs": [w_in], "Outputs": [w_out],
                      "Replication": "Disabled", "Description": "Visualizes a node's output"})
        views.append({"Id": w_id, "Name": "Watch: " + var, "IsSetAsInput": False, "IsSetAsOutput": False,
                      "Excluded": False, "ShowGeometry": True, "X": 1400.0, "Y": 260.0 * k})
        connectors.append({"Start": outputs[idx]["Id"], "End": w_in["Id"], "Id": gid(), "IsHidden": "False"})

    note_id = gid()
    return {
        "Uuid": str(uuid.uuid4()), "IsCustomNode": False, "Description": description, "Name": name,
        "ElementResolver": {"ResolutionMap": {}},
        "Inputs": [], "Outputs": [], "Nodes": nodes, "Connectors": connectors, "Dependencies": [],
        "NodeLibraryDependencies": [{"Name": "CivilConnection2027", "Version": "7.0.0", "ReferenceType": "Package", "Nodes": [cb_id]}],
        "Thumbnail": "", "GraphDocumentationURL": None, "ExtensionWorkspaceData": [], "Author": "",
        "Linting": {"activeLinter": "None", "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a", "warningCount": 0, "errorCount": 0},
        "Bindings": [],
        "View": {
            "Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": True, "IsVisibleInDynamoLibrary": True,
                       "Version": "4.1.1.5050", "RunType": "Manual", "RunPeriod": "1000"},
            "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0, "EyeZ": 50.0, "LookX": 12.0,
                       "LookY": -13.0, "LookZ": -58.0, "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
            "ConnectorPins": [], "NodeViews": views,
            "Annotations": [{"Id": note_id, "Title": notes, "DescriptionText": None, "IsExpanded": True, "WidthAdjustment": 0.0,
                             "HeightAdjustment": 0.0, "Nodes": [], "HasNestedGroups": False, "Left": 0.0, "Top": -260.0,
                             "Width": 0.0, "Height": 0.0, "FontSize": 36.0, "GroupStyleId": "00000000-0000-0000-0000-000000000000",
                             "InitialTop": 0.0, "InitialHeight": 0.0, "TextblockHeight": 0.0, "Background": "#FFC1D676"}],
            "X": 60.0, "Y": 320.0, "Zoom": 0.6}}


R = "CivilConnection.Robot.RobotModel"

revit = graph(
    "Revit para Robot",
    "Envia a estrutura do Revit 2027 para o Robot 2027, aplica peso proprio e sobrecarga, calcula e le as reacoes.",
    [
        "// PARAMETROS (abra o Robot com um projeto qualquer antes de executar)",
        "// criarAnalitico = true cria o modelo analitico do Revit que faltar, ajustando as extremidades ate a tolerancia (m).",
        "// ALTERA O DOCUMENTO DO REVIT: use uma copia do arquivo e revise o resultado.",
        "criarAnalitico = true;",
        "toleranciaAnalitico = 0.25;",
        "// incluirLajes = false deixa de fora as lajes (pisos sobre o solo ficam soltos sem base elastica)",
        "incluirLajes = false;",
        "calcular = true;",
        "// sobrecarga nas lajes em Pa (N/m2), negativa = para baixo",
        "cargaLaje = -3000;",
        "// FLUXO",
        "analitico = criarAnalitico ? %s.CreateRevitAnalyticalModel(toleranciaAnalitico, incluirLajes) : null;" % R,
        "elementos = criarAnalitico ? analitico[\"AnalyticalElements\"] : %s.RevitAnalyticalElements(true, incluirLajes);" % R,
        "robot = %s.Connect(true, \"Shell\", -1, null);" % R,
        "envio = robot.FromRevitAnalytical(elementos, \"\", 0.5, 0.5);",
        "// liga as pecas que chegam no meio de outras (juncoes em T)",
        "divididas = robot.SplitBarsAtNodes(envio);",
        "engaste = robot.CreateSupport(\"ENGASTE\", true, true, true, true, true, true);",
        "apoios = robot.AssignSupportToColumnBases(engaste, divididas);",
        "limpar = robot.DeleteAllCases(apoios);",
        "casoG = robot.CreateLoadCase(1, \"G - peso proprio\", \"Permanent\", limpar);",
        "pp = robot.AddSelfWeight(casoG, 1);",
        "casoQ = robot.CreateLoadCase(2, \"Q - sobrecarga\", \"Exploatation\", pp);",
        "sobrecarga = robot.AddPanelUniformLoads(casoQ, envio[\"Panels\"], 0, 0, cargaLaje, false);",
        "elu = robot.CreateCombination(3, \"ELU 1.4G + 1.4Q\", [pp, sobrecarga], [1.4, 1.4], \"ULS\");",
        "malha = robot.GenerateMesh(elu);",
        "calculado = robot.Calculate(calcular, malha);",
        "reacoesG = robot.NodeReactions(apoios, pp, calculado);",
        "pesoProprio_kN = Math.Sum(reacoesG[\"FZ\"]) / 1000;",
        "reacoesELU = robot.NodeReactions(apoios, elu, calculado);",
        "somaFZ_ELU_kN = Math.Sum(reacoesELU[\"FZ\"]) / 1000;",
        "fim = robot.EndSession(somaFZ_ELU_kN);",
    ],
    ["analitico", "divididas", "pesoProprio_kN", "somaFZ_ELU_kN"],
    "CivilConnection 2027 - Revit para Robot")

civil = graph(
    "Civil 3D para Robot",
    "Cria no Robot 2027 o tabuleiro entre duas linhas de feicao de um corredor do Civil 3D 2027, com apoios, cargas, calculo e reacoes.",
    [
        "// PARAMETROS (Civil 3D 2027 com o desenho do corredor aberto, CivilPython instalado e Robot aberto)",
        "calcular = true;",
        "// codigo das linhas de feicao dos bordos do tabuleiro (veja a lista 'codigos')",
        "codigoBordo = \"ETW\";",
        "// comprimento dos paineis ao longo do bordo e distancia entre apoios, em unidades do Civil 3D",
        "passo = 5;",
        "vao = 30;",
        "// fator de unidade do desenho para metros (1 = desenho em metros)",
        "unidadeParaMetro = 1;",
        "// FLUXO",
        "civil = CivilConnection.CivilApplication();",
        "documento = civil.GetDocuments()[0];",
        "corredor = documento.GetCorridors()[0];",
        "codigos = List.UniqueItems(List.Flatten(corredor.GetFeaturelines(), -1).Code);",
        "bordos = List.Flatten(corredor.GetFeaturelinesByCode(codigoBordo), -1);",
        "origem = bordos[0].Curve.StartPoint;",
        "robot = %s.Connect(true, \"Shell\", unidadeParaMetro, origem);" % R,
        "concreto = robot.CreateMaterial(\"C35\", 29.4e9, 0.2, 25000, \"Concrete\");",
        "laje = robot.CreatePanelThickness(\"LAJE 25\", 0.25, concreto, 0);",
        "nApoios = Math.Ceiling(bordos[0].Curve.Length / vao) + 1;",
        "t = 0..1..#nApoios;",
        "pontosApoio = List.Flatten([bordos[0].Curve.PointAtParameter(t), bordos[1].Curve.PointAtParameter(t)], -1);",
        "apoio = robot.CreateSupport(\"APOIO\", true, true, true, false, false, false);",
        "apoios = robot.AssignSupportAtPoints(pontosApoio, apoio);",
        "paineis = robot.DeckPanelsBetweenFeaturelines(bordos[0], bordos[1], laje, passo, 0.5);",
        "limpar = robot.DeleteAllCases(paineis);",
        "casoG = robot.CreateLoadCase(1, \"G - peso proprio\", \"Permanent\", limpar);",
        "pp = robot.AddSelfWeight(casoG, 1);",
        "casoQ = robot.CreateLoadCase(2, \"Q - multidao 5 kPa\", \"Exploatation\", pp);",
        "q = robot.AddPanelUniformLoads(casoQ, paineis, 0, 0, -5000, false);",
        "elu = robot.CreateCombination(3, \"ELU 1.35G + 1.5Q\", [pp, q], [1.35, 1.5], \"ULS\");",
        "malha = robot.GenerateMesh(elu);",
        "calculado = robot.Calculate(calcular, malha);",
        "reacoes = robot.NodeReactions(apoios, elu, calculado);",
        "somaFZ_ELU_kN = Math.Sum(reacoes[\"FZ\"]) / 1000;",
        "fim = robot.EndSession(somaFZ_ELU_kN);",
    ],
    ["codigos", "paineis", "somaFZ_ELU_kN"],
    "CivilConnection 2027 - Civil 3D para Robot")

os.makedirs(OUT, exist_ok=True)
for fname, g in [("01_Revit para Robot_2027.dyn", revit), ("02_Civil 3D para Robot_2027.dyn", civil)]:
    path = os.path.join(OUT, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=2, ensure_ascii=False)
    print(path, len(g["Nodes"][0]["Outputs"]), "portas")
