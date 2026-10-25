using CivilConnection.Robot;
using ModelContextProtocol.Server;
using RobotOM;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;

namespace CivilSenior.Mcp.Robot;

/// <summary>
/// Robot Structural Analysis 2027 tools. Units are SI everywhere: m, N, N.m, Pa, N/m3. Robot must be running.
/// </summary>
[McpServerToolType]
public static class RobotTools
{
    private static T Parse<T>(string prefix, string value) where T : struct, Enum
    {
        if (Enum.TryParse(prefix + value.ToUpperInvariant().Replace("FRAME3D", "FRAME_3D").Replace("TRUSS3D", "TRUSS_3D"), out T result)) return result;
        throw new ArgumentException($"invalid value '{value}'");
    }

    private static List<int> Ints(string json) => Json.List<int>(json);

    // ----- session -----

    [McpServerTool(Name = "robot_status"), Description("Robot connection and model summary: version, counts of nodes/bars/panels, labels by type, load cases and combinations, and whether results are available.")]
    public static Task<string> Status(RobotSession s) => s.Run(link =>
    {
        IRobotStructure st = link.Structure;
        var labels = new Dictionary<string, List<string>>();
        foreach (var (key, type) in new[] { ("materials", IRobotLabelType.I_LT_MATERIAL), ("sections", IRobotLabelType.I_LT_BAR_SECTION), ("thicknesses", IRobotLabelType.I_LT_PANEL_THICKNESS), ("supports", IRobotLabelType.I_LT_SUPPORT), ("releases", IRobotLabelType.I_LT_BAR_RELEASE) })
        {
            var names = new List<string>();
            IRobotCollection many = st.Labels.GetMany(type);
            for (int i = 1; i <= many.Count; i++) names.Add(((IRobotLabel)many.Get(i)).Name);
            labels[key] = names;
        }
        var cases = new List<object>();
        RobotCaseCollection all = st.Cases.GetAll();
        for (int i = 1; i <= all.Count; i++)
        {
            var c = (IRobotCase)all.Get(i);
            cases.Add(new { number = c.Number, name = c.Name, type = c.Type == IRobotCaseType.I_CT_COMBINATION ? "combination" : "simple" });
        }
        return new
        {
            version = link.App.Version,
            projectType = link.App.Project.Type.ToString(),
            file = link.App.Project.FileName,
            nodes = st.Nodes.GetAll().Count,
            bars = st.Bars.GetAll().Count,
            objects = st.Objects.GetAll().Count,
            labels,
            cases,
            resultsAvailable = link.ResultsAvailable
        };
    });

    [McpServerTool(Name = "robot_launch"), Description("Starts Robot 2027 if it is not running and waits for its main window. Then call robot_new_project or robot_open.")]
    public static Task<string> Launch([Description("Seconds to wait")] int timeoutSeconds = 300) => RobotSession.Launch(timeoutSeconds);

    [McpServerTool(Name = "robot_new_project"), Description("Starts a new Robot project, discarding the current one (save first if needed).")]
    public static Task<string> NewProject(RobotSession s, [Description("Frame3D, Truss3D, Grillage, Plate or Shell")] string structureType = "Shell")
        => s.NewProject(Parse<IRobotProjectType>("I_PT_", structureType));

    [McpServerTool(Name = "robot_open"), Description("Opens a Robot model (.rtd).")]
    public static Task<string> Open(RobotSession s, [Description("Full path of the .rtd file")] string path) => s.Run(link =>
    {
        link.App.Project.Open(path);
        link.Refresh();
        return new { ok = true, file = link.App.Project.FileName };
    });

    [McpServerTool(Name = "robot_save"), Description("Saves the Robot model; with a path, saves as a new file.")]
    public static Task<string> Save(RobotSession s, [Description("Full path of the .rtd file (empty = save in place)")] string path = "") => s.Run(link =>
    {
        if (string.IsNullOrWhiteSpace(path)) link.App.Project.Save(); else link.App.Project.SaveAs(path);
        return new { ok = true, file = link.App.Project.FileName };
    });

    // ----- labels -----

    [McpServerTool(Name = "robot_create_material"), Description("Creates an isotropic material. Use the modulus of the design code (e.g. NBR 6118 Ecs), not the library value.")]
    public static Task<string> CreateMaterial(RobotSession s, string name,
        [Description("Young's modulus E in Pa (e.g. 26.8e9)")] double youngModulus,
        [Description("Poisson's ratio")] double poisson = 0.2,
        [Description("Unit weight in N/m3 (e.g. 25000 for reinforced concrete)")] double unitWeight = 25000,
        [Description("Concrete, Steel, Timber, Aluminium or Other")] string materialType = "Concrete")
        => s.Run(link => new { name = link.CreateMaterial(name, Parse<IRobotMaterialType>("I_MT_", materialType), youngModulus, poisson, unitWeight) });

    [McpServerTool(Name = "robot_create_section"), Description("Creates a bar section: solid rectangle (width and height) or, when area is given, a section defined by properties (strong axis = y).")]
    public static Task<string> CreateSection(RobotSession s, string name,
        [Description("Material name (optional)")] string material = "",
        [Description("Rectangle width b in m")] double width = 0,
        [Description("Rectangle height h in m")] double height = 0,
        [Description("Area in m2 (section by properties)")] double area = 0,
        [Description("Iy in m4 (strong axis)")] double iy = 0,
        [Description("Iz in m4")] double iz = 0,
        [Description("Torsion constant Ix in m4")] double ix = 0,
        [Description("Elastic modulus Wy in m3")] double wy = 0,
        [Description("Elastic modulus Wz in m3")] double wz = 0)
        => s.Run(link =>
        {
            if (area > 0) return new { name = link.CreateSectionByProperties(name, area, iy, iz, ix, wy, wz, material), kind = "properties" };
            if (width <= 0 || height <= 0) throw new ArgumentException("give width and height, or area and inertias");
            return (object)new { name = link.CreateRectangularSection(name, width, height, material), kind = "rectangle" };
        });

    [McpServerTool(Name = "robot_create_thickness"), Description("Creates a panel thickness, optionally on an elastic (Winkler) foundation.")]
    public static Task<string> CreateThickness(RobotSession s, string name,
        [Description("Thickness in m")] double thickness,
        [Description("Material name")] string material = "",
        [Description("Subgrade modulus kv in N/m3 (0 = none)")] double elasticFoundation = 0)
        => s.Run(link => new { name = link.CreatePanelThickness(name, thickness, material, elasticFoundation) });

    [McpServerTool(Name = "robot_create_support"), Description("Creates a nodal support label; true blocks the degree of freedom.")]
    public static Task<string> CreateSupport(RobotSession s, string name, bool ux = true, bool uy = true, bool uz = true, bool rx = false, bool ry = false, bool rz = false)
        => s.Run(link => new { name = link.CreateSupport(name, ux, uy, uz, rx, ry, rz) });

    // ----- geometry -----

    [McpServerTool(Name = "robot_create_nodes"), Description("Creates nodes (existing nodes within 1 mm are reused). Returns the node numbers in input order.")]
    public static Task<string> CreateNodes(RobotSession s, [Description("JSON array of [x,y,z] in m")] string points)
        => s.Run(link => new { nodes = Json.Points(points).Select(p => link.GetOrCreateNode(p[0], p[1], p[2])).ToList() }, refreshNodes: true);

    public sealed class BarInput
    {
        public double[] Start { get; set; }
        public double[] End { get; set; }
        public string Section { get; set; } = "";
        public string Material { get; set; } = "";
        public double[] ZAxis { get; set; }
        public bool[] ReleaseStart { get; set; }
        public bool[] ReleaseEnd { get; set; }
    }

    [McpServerTool(Name = "robot_create_bars"), Description("Creates bars between points, sharing nodes within 1 mm. Each item: {\"start\":[x,y,z],\"end\":[x,y,z],\"section\":\"\",\"material\":\"\",\"zAxis\":[x,y,z] (optional, direction of the section height), \"releaseStart\":[ux,uy,uz,rx,ry,rz] (optional, true = released), \"releaseEnd\":[...]}. Returns the bar numbers (0 = zero-length bar skipped).")]
    public static Task<string> CreateBars(RobotSession s, [Description("JSON array of bars (camelCase keys)")] string bars)
        => s.Run(link =>
        {
            var input = System.Text.Json.JsonSerializer.Deserialize<List<BarInput>>(bars, new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true }) ?? new List<BarInput>();
            var numbers = new List<int>();
            foreach (BarInput b in input)
            {
                int n = link.CreateBar(b.Start, b.End, b.Section, b.Material);
                numbers.Add(n);
                if (n == 0) continue;
                if (b.ZAxis != null) link.SetBarOrientation(n, b.ZAxis[0], b.ZAxis[1], b.ZAxis[2]);
                if (b.ReleaseStart != null || b.ReleaseEnd != null) link.SetBarRelease(n, b.ReleaseStart ?? new bool[6], b.ReleaseEnd ?? new bool[6]);
            }
            return new { bars = numbers };
        }, refreshNodes: true);

    [McpServerTool(Name = "robot_create_panel"), Description("Creates a meshed panel from a planar closed contour (do not repeat the first point at the end).")]
    public static Task<string> CreatePanel(RobotSession s,
        [Description("JSON array of [x,y,z] in m, in order around the contour")] string contour,
        [Description("Thickness label name")] string thickness,
        [Description("Finite element size in m (0 = Robot default)")] double meshSize = 0)
        => s.Run(link => new { panel = link.CreatePanel(Json.Points(contour), thickness, meshSize) }, refreshNodes: true);

    [McpServerTool(Name = "robot_assign_support"), Description("Assigns a support label to nodes: a JSON list of node numbers, or the keyword column_bases (free lower ends of vertical bars) or lowest (nodes at the minimum elevation).")]
    public static Task<string> AssignSupport(RobotSession s, [Description("JSON array of node numbers, \"column_bases\" or \"lowest\"")] string nodes, [Description("Support label name")] string support)
        => s.Run(link =>
        {
            List<int> list = nodes.Trim() switch
            {
                "column_bases" => link.ColumnBaseNodes(),
                "lowest" => link.NodesAtMinimumZ(0.01),
                _ => Ints(nodes)
            };
            link.AssignSupport(list, support);
            return new { support, nodes = list };
        });

    [McpServerTool(Name = "robot_split_bars_at_nodes"), Description("Splits bars at nodes lying on them (T joints), keeping section, material, orientation and end releases. Run after all bars exist and before meshing.")]
    public static Task<string> SplitBars(RobotSession s) => s.Run(link => new { barsSplit = link.SplitBarsAtNodes() });

    [McpServerTool(Name = "robot_nearest_nodes"), Description("Existing nodes closest to points (including panel mesh nodes), without creating nodes. Use it to read results at locations of a panel.")]
    public static Task<string> NearestNodes(RobotSession s, [Description("JSON array of [x,y,z] in m")] string points)
        => s.Run(link => Json.Points(points).Select(p => { int n = link.FindNearestNode(p[0], p[1], p[2], out double d); return new { node = n, distance = d }; }).ToList());

    // ----- loads -----

    [McpServerTool(Name = "robot_create_load_case"), Description("Creates a static linear load case (an existing case with the same number is replaced). deleteExisting = true first deletes ALL cases and combinations, including the automatic self-weight case DL1.")]
    public static Task<string> CreateLoadCase(RobotSession s, int number, string name,
        [Description("Permanent, Exploatation (live), Wind, Snow, Temperature, Accidental or Seismic")] string nature = "Permanent",
        bool deleteExisting = false)
        => s.Run(link =>
        {
            if (deleteExisting) link.DeleteAllCases();
            return new { number = link.CreateLoadCase(number, name, Parse<IRobotCaseNature>("I_CN_", nature)) };
        });

    [McpServerTool(Name = "robot_add_load"), Description("Adds loads to a simple load case. kind: self_weight (values: [factor]); nodal (objects = nodes, values: [fx,fy,fz,mx,my,mz] in N and N.m); bar_uniform (objects = bars, values: [px,py,pz] in N/m); panel_uniform (objects = panels, values: [px,py,pz] in Pa). Global axes unless local = true. Downward loads are negative z.")]
    public static Task<string> AddLoad(RobotSession s, int caseNumber,
        [Description("self_weight, nodal, bar_uniform or panel_uniform")] string kind,
        [Description("JSON array of numbers (empty for self_weight)")] string objects = "[]",
        [Description("JSON array of values")] string values = "[1]",
        bool local = false)
        => s.Run(link =>
        {
            List<int> obj = Ints(objects);
            double[] v = System.Text.Json.JsonSerializer.Deserialize<double[]>(values) ?? Array.Empty<double>();
            double V(int i) => i < v.Length ? v[i] : 0;
            switch (kind)
            {
                case "self_weight": link.AddSelfWeight(caseNumber, v.Length > 0 ? v[0] : 1); break;
                case "nodal": link.AddNodalForce(caseNumber, obj, V(0), V(1), V(2), V(3), V(4), V(5)); break;
                case "bar_uniform": link.AddBarUniformLoad(caseNumber, obj, V(0), V(1), V(2), local); break;
                case "panel_uniform": link.AddPanelUniformLoad(caseNumber, obj, V(0), V(1), V(2), local); break;
                default: throw new ArgumentException("kind must be self_weight, nodal, bar_uniform or panel_uniform");
            }
            return new { ok = true, caseNumber, kind, objects = obj.Count };
        });

    [McpServerTool(Name = "robot_create_combination"), Description("Creates a linear combination of load cases.")]
    public static Task<string> CreateCombination(RobotSession s, int number, string name,
        [Description("JSON array of case numbers")] string cases,
        [Description("JSON array of factors, one per case")] string factors,
        [Description("ULS, SLS or ALS")] string type = "ULS")
        => s.Run(link => new { number = link.CreateCombination(number, name, Parse<IRobotCombinationType>("I_CBT_", type), Ints(cases), Json.List<double>(factors)) });

    // ----- analysis -----

    [McpServerTool(Name = "robot_calculate"), Description("Generates the panel mesh (optional) and runs the analysis. Returns whether results are available.")]
    public static Task<string> Calculate(RobotSession s, bool generateMesh = true) => s.Run(link =>
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        if (generateMesh) link.GenerateMesh();
        int status = link.Calculate();
        return new { status, resultsAvailable = link.ResultsAvailable, seconds = Math.Round(sw.Elapsed.TotalSeconds, 1) };
    });

    // ----- results -----

    [McpServerTool(Name = "robot_node_displacements"), Description("Node displacements (m) and rotations (rad) for a case or combination.")]
    public static Task<string> NodeDisplacements(RobotSession s, [Description("JSON array of node numbers")] string nodes, int caseNumber)
        => s.Run(link => Ints(nodes).Select(n => { var d = link.NodeDisplacement(n, caseNumber); return new { node = n, ux = d[0], uy = d[1], uz = d[2], rx = d[3], ry = d[4], rz = d[5] }; }).ToList());

    [McpServerTool(Name = "robot_reactions"), Description("Support reactions (N, N.m) for a case or combination: each supported node (or the given nodes) and the total.")]
    public static Task<string> Reactions(RobotSession s, int caseNumber, [Description("JSON array of node numbers (empty = all supported nodes)")] string nodes = "[]")
        => s.Run(link =>
        {
            List<int> list = Ints(nodes);
            if (list.Count == 0)
            {
                IRobotCollection all = link.Structure.Nodes.GetAll();
                for (int i = 1; i <= all.Count; i++)
                {
                    var node = (IRobotNode)all.Get(i);
                    if (node.HasLabel(IRobotLabelType.I_LT_SUPPORT) != 0) list.Add(node.Number);
                }
            }
            var rows = list.Select(n => { var r = link.NodeReaction(n, caseNumber); return new { node = n, fx = r[0], fy = r[1], fz = r[2], mx = r[3], my = r[4], mz = r[5] }; }).ToList();
            IRobotReactionData sum = link.Structure.Results.Nodes.Reactions.Sum(caseNumber);
            return new { total = new { fx = sum.FX, fy = sum.FY, fz = sum.FZ, mx = sum.MX, my = sum.MY, mz = sum.MZ }, nodes = rows };
        });

    [McpServerTool(Name = "robot_bar_forces"), Description("Bar internal forces (N, N.m) at equally spaced points along each bar (local axes).")]
    public static Task<string> BarForces(RobotSession s, [Description("JSON array of bar numbers")] string bars, int caseNumber, [Description("Points per bar (2 = ends)")] int points = 3)
        => s.Run(link =>
        {
            points = Math.Max(2, points);
            return Ints(bars).Select(b => new
            {
                bar = b,
                stations = Enumerable.Range(0, points).Select(i =>
                {
                    double x = (double)i / (points - 1);
                    var f = link.BarForce(b, caseNumber, x);
                    return new { x, fx = f[0], fy = f[1], fz = f[2], mx = f[3], my = f[4], mz = f[5] };
                }).ToList()
            }).ToList();
        });

    [McpServerTool(Name = "robot_panel_forces"), Description("Shell forces of a panel per finite element (moments N.m/m, membrane and shear N/m) with the extreme values. detail = false returns only the extremes.")]
    public static Task<string> PanelForces(RobotSession s, int panel, int caseNumber, bool detail = false)
        => s.Run(link =>
        {
            List<double[]> rows = link.PanelElementForces(panel, caseNumber, out List<int> elements);
            string[] keys = { "mxx", "myy", "mxy", "nxx", "nyy", "nxy", "qxx", "qyy" };
            var extremes = keys.Select((k, i) => new { component = k, min = rows.Count == 0 ? double.NaN : rows.Min(r => r[i]), max = rows.Count == 0 ? double.NaN : rows.Max(r => r[i]) }).ToList();
            object perElement = detail ? elements.Select((e, j) => new { element = e, values = rows[j] }).ToList() : null;
            return new { panel, caseNumber, elements = elements.Count, extremes, order = keys, perElement };
        });

    [McpServerTool(Name = "robot_check_equilibrium"), Description("Checks a self-weight case: total vertical reaction vs the weight of the bars (sum of A x L x unit weight), plus connectivity (bar ends connected to a single bar). Large differences mean disconnected parts or missing supports. Panels are not included in the weight.")]
    public static Task<string> CheckEquilibrium(RobotSession s, int caseNumber)
        => s.Run(link =>
        {
            IRobotStructure st = link.Structure;
            double weight = 0;
            var gamma = new Dictionary<string, double>();
            var use = new Dictionary<int, int>();
            int noSection = 0;
            IRobotCollection bars = st.Bars.GetAll();
            for (int i = 1; i <= bars.Count; i++)
            {
                var bar = (IRobotBar)bars.Get(i);
                use[bar.StartNode] = use.TryGetValue(bar.StartNode, out int a) ? a + 1 : 1;
                use[bar.EndNode] = use.TryGetValue(bar.EndNode, out int b) ? b + 1 : 1;
                if (bar.HasLabel(IRobotLabelType.I_LT_BAR_SECTION) == 0) { noSection++; continue; }
                var sec = (IRobotBarSectionData)bar.GetLabel(IRobotLabelType.I_LT_BAR_SECTION).Data;
                string mat = bar.HasLabel(IRobotLabelType.I_LT_MATERIAL) != 0 ? bar.GetLabelName(IRobotLabelType.I_LT_MATERIAL) : sec.MaterialName ?? "";
                if (!gamma.TryGetValue(mat, out double g))
                {
                    g = mat.Length > 0 && st.Labels.Exist(IRobotLabelType.I_LT_MATERIAL, mat) != 0 ? ((IRobotMaterialData)st.Labels.Get(IRobotLabelType.I_LT_MATERIAL, mat).Data).RO : 0;
                    gamma[mat] = g;
                }
                weight += sec.GetValue(IRobotBarSectionDataValue.I_BSDV_AX) * bar.Length * g;
            }
            double fz = st.Results.Nodes.Reactions.Sum(caseNumber).FZ;
            return new
            {
                reactionFz = fz,
                barWeight = weight,
                differencePercent = weight > 0 ? (fz / weight - 1) * 100 : double.NaN,
                barsWithoutSection = noSection,
                freeBarEnds = use.Count(kv => kv.Value == 1),
                note = "Reactions should match the weight within about 1-2 %; free bar ends and missing supports explain larger gaps."
            };
        });
}
