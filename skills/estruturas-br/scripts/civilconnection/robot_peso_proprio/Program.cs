// Step B: self-weight check of the Revit -> Robot transfer of the shed (model already open in Robot).
using CivilConnection.Robot;
using RobotOM;

static class B
{
    static void Log(string s) { Console.WriteLine(s); Console.Out.Flush(); }

    [STAThread]
    static int Main(string[] args)
    {
        double reference = double.Parse(args[0], System.Globalization.CultureInfo.InvariantCulture); // kN

        var link = RobotLink.Connect(false, IRobotProjectType.I_PT_SHELL);
        IRobotStructure st = link.Structure;
        Log($"Modelo: {st.Nodes.GetAll().Count} nos, {st.Bars.GetAll().Count} barras");

        // Robot's own sum of A x L x unit weight, to separate transfer errors from analysis errors
        double wRobot = 0; int noSection = 0;
        var gammaBySection = new Dictionary<string, double>();
        IRobotCollection bars = st.Bars.GetAll();
        var nodeUse = new Dictionary<int, int>();
        for (int i = 1; i <= bars.Count; i++)
        {
            var bar = (IRobotBar)bars.Get(i);
            nodeUse[bar.StartNode] = nodeUse.TryGetValue(bar.StartNode, out int a) ? a + 1 : 1;
            nodeUse[bar.EndNode] = nodeUse.TryGetValue(bar.EndNode, out int b) ? b + 1 : 1;
            if (bar.HasLabel(IRobotLabelType.I_LT_BAR_SECTION) == 0) { noSection++; continue; }
            var sec = (IRobotBarSectionData)bar.GetLabel(IRobotLabelType.I_LT_BAR_SECTION).Data;
            string matName = bar.HasLabel(IRobotLabelType.I_LT_MATERIAL) != 0 ? bar.GetLabelName(IRobotLabelType.I_LT_MATERIAL) : sec.MaterialName;
            if (!gammaBySection.TryGetValue(matName ?? "", out double gamma))
            {
                gamma = string.IsNullOrEmpty(matName) || st.Labels.Exist(IRobotLabelType.I_LT_MATERIAL, matName) == 0 ? 0
                    : ((IRobotMaterialData)st.Labels.Get(IRobotLabelType.I_LT_MATERIAL, matName).Data).RO;
                gammaBySection[matName ?? ""] = gamma;
            }
            wRobot += sec.GetValue(IRobotBarSectionDataValue.I_BSDV_AX) * bar.Length * gamma;
        }
        int freeEnds = nodeUse.Count(kv => kv.Value == 1);
        Log($"Barras sem secao: {noSection}; materiais: {string.Join(", ", gammaBySection.Select(k => $"{(k.Key == "" ? "(padrao)" : k.Key)}={k.Value / 1000:F1} kN/m3"))}");
        Log($"Conectividade: {nodeUse.Count} nos de barra, {freeEnds} extremidades livres (ligadas a uma unica barra)");

        link.DeleteAllCases();
        int g = link.CreateLoadCase(1, "PP", IRobotCaseNature.I_CN_PERMANENT);
        link.AddSelfWeight(g, 1);
        Log("Calculando...");
        var t = System.Diagnostics.Stopwatch.StartNew();
        int status = -999;
        var th = new Thread(() => status = link.Calculate());
        th.SetApartmentState(ApartmentState.STA);
        th.Start();
        if (!th.Join(TimeSpan.FromSeconds(400))) { Log("Calculate nao retornou em 400 s"); return 3; }
        Log($"Calculate = {status} em {t.Elapsed.TotalSeconds:F0} s; resultados = {link.ResultsAvailable}");
        if (!link.ResultsAvailable) return 2;

        IRobotReactionData sum = st.Results.Nodes.Reactions.Sum(g);
        double fz = sum.FZ / 1000;
        Log($"Soma das reacoes FZ (PP)          : {fz,10:F2} kN");
        Log($"Peso no Robot (soma A x L x gama)  : {wRobot / 1000,10:F2} kN   dif. reacoes/peso Robot = {(fz / (wRobot / 1000) - 1) * 100:F2} %");
        Log($"Peso de referencia do Revit        : {reference,10:F2} kN   dif. reacoes/Revit      = {(fz / reference - 1) * 100:F2} %");
        Log($"Resultantes horizontais FX, FY     : {sum.FX / 1000:F3}, {sum.FY / 1000:F3} kN");

        link.App.Project.Save();
        link.EndSession();
        return 0;
    }
}
