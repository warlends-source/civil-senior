// Calibration test of CivilConnection.Robot.RobotLink against Robot 2027 (analytical answers).
using CivilConnection.Robot;
using RobotOM;
using System.Diagnostics;

static class T
{
    static int failures;
    static void Log(string s) { Console.WriteLine(s); Console.Out.Flush(); }

    static void Check(string name, double robot, double expected, double tolPct)
    {
        double d = expected == 0 ? Math.Abs(robot) : Math.Abs(robot / expected - 1) * 100;
        bool ok = expected == 0 ? Math.Abs(robot) < 1e-6 : d <= tolPct;
        if (!ok) failures++;
        Log($"  {(ok ? "OK  " : "FAIL")} {name,-38} Robot {robot,14:G6}  esperado {expected,14:G6}  dif {d,6:F2} %");
    }

    static string SafeLabel(RobotLink link, int bar)
    {
        var b = (IRobotBar)link.Structure.Bars.Get(bar);
        return b.HasLabel(IRobotLabelType.I_LT_BAR_RELEASE) != 0 ? b.GetLabelName(IRobotLabelType.I_LT_BAR_RELEASE) : "(nenhuma)";
    }

    [STAThread]
    static int Main(string[] args)
    {
        bool calculate = args.Contains("--calc");
        string rtd = Path.Combine(Path.GetTempPath(), "CivilConnection_RobotTest.rtd");

        if (Process.GetProcessesByName("robot").Length == 0)
        {
            Log("Iniciando o Robot 2027...");
            Process.Start(@"D:\Autodesk\Robot Structural Analysis Professional 2027\Exe\robot.EXE");
            var sw = Stopwatch.StartNew();
            while (sw.Elapsed < TimeSpan.FromMinutes(5))
            {
                Thread.Sleep(5000);
                var p = Process.GetProcessesByName("robot").FirstOrDefault();
                if (p != null && p.MainWindowHandle != IntPtr.Zero && sw.Elapsed > TimeSpan.FromSeconds(40)) break;
            }
        }

        Log("Conectando...");
        var link = RobotLink.Connect(true, IRobotProjectType.I_PT_SHELL);
        Log($"Robot {link.App.Version}, projeto ativo = {link.App.Project.IsActive}, tipo = {link.App.Project.Type}");

        // Labels
        const double E = 30e9, NU = 0.2, GAMMA = 25000;
        link.CreateMaterial("CC_C30", IRobotMaterialType.I_MT_CONCRETE, E, NU, GAMMA);
        link.CreateRectangularSection("CC_R20x50", 0.20, 0.50, "CC_C30");
        link.CreatePanelThickness("CC_TH50_KV20", 0.50, "CC_C30", 20e6);
        link.CreateSupport("CC_PINNED", true, true, true, true, false, false);
        link.CreateSupport("CC_ROLLER", false, true, true, false, false, false);

        // Simply supported beam, L = 6 m, two bars so there is a node at midspan
        const double L = 6, Y = 20;
        int b1 = link.CreateBar(new[] { 0.0, Y, 0 }, new[] { L / 2, Y, 0 }, "CC_R20x50", "CC_C30");
        int b2 = link.CreateBar(new[] { L / 2, Y, 0 }, new[] { L, Y, 0 }, "CC_R20x50", "CC_C30");
        int nA = link.GetOrCreateNode(0, Y, 0), nM = link.GetOrCreateNode(L / 2, Y, 0), nB = link.GetOrCreateNode(L, Y, 0);
        link.AssignSupport(new[] { nA }, "CC_PINNED");
        link.AssignSupport(new[] { nB }, "CC_ROLLER");
        Log($"Viga: barras {b1},{b2}; nos {nA},{nM},{nB} (no do meio reaproveitado: {link.GetOrCreateNode(L / 2, Y, 0) == nM})");

        // Beam with fully fixed supports and pinned end releases (RY, RZ), created as one bar and then split at
        // a midspan node: must behave as simply supported (M = qL2/8 at midspan, 0 at the ends)
        const double Y2 = 30;
        link.CreateSupport("CC_FIXED", true, true, true, true, true, true);
        int rb = link.CreateBar(new[] { 0.0, Y2, 0 }, new[] { L, Y2, 0 }, "CC_R20x50", "CC_C30");
        var pin = new[] { false, false, false, false, true, true };
        link.SetBarRelease(rb, pin, pin);
        link.SetBarOrientation(rb, 0, 0, 1);
        int rA = link.GetOrCreateNode(0, Y2, 0), rM = link.GetOrCreateNode(L / 2, Y2, 0), rB = link.GetOrCreateNode(L, Y2, 0);
        link.AssignSupport(new[] { rA, rB }, "CC_FIXED");
        int nSplit = link.SplitBarsAtNodes();
        var released = new List<int>();
        IRobotCollection allBars = link.Structure.Bars.GetAll();
        for (int i = 1; i <= allBars.Count; i++)
        {
            var b = (IRobotBar)allBars.Get(i);
            if (b.StartNode == rA || b.EndNode == rB || b.StartNode == rM || b.EndNode == rM) released.Add(b.Number);
        }
        int rb1 = released.First(n => ((IRobotBar)link.Structure.Bars.Get(n)).StartNode == rA);
        int rb2 = released.First(n => ((IRobotBar)link.Structure.Bars.Get(n)).EndNode == rB);
        Log($"Viga com rotulas: barra {rb} dividida ({nSplit} barra(s) dividida(s)) em {rb1},{rb2}; liberacoes: {SafeLabel(link, rb1)} / {SafeLabel(link, rb2)}");

        // Plate 10 x 10 m on Winkler foundation
        int panel = link.CreatePanel(new List<double[]> { new[] { 0.0, 0, 0 }, new[] { 10.0, 0, 0 }, new[] { 10.0, 10, 0 }, new[] { 0.0, 10, 0 } }, "CC_TH50_KV20", 0.5);
        Log($"Placa: painel {panel}");

        // Loads
        link.DeleteAllCases();
        int cG = link.CreateLoadCase(1, "G placa", IRobotCaseNature.I_CN_PERMANENT);
        int cQ = link.CreateLoadCase(2, "Q", IRobotCaseNature.I_CN_EXPLOATATION);
        link.AddPanelUniformLoad(cG, new[] { panel }, 0, 0, -GAMMA * 0.5, false);   // self-weight of the plate as pressure
        link.AddPanelUniformLoad(cQ, new[] { panel }, 0, 0, -10000, false);
        link.AddBarUniformLoad(cQ, new[] { b1, b2, rb1, rb2 }, 0, 0, -10000, false);
        int cC = link.CreateCombination(3, "ELU 1.4G+1.4Q", IRobotCombinationType.I_CBT_ULS, new[] { cG, cQ }, new[] { 1.4, 1.4 });
        Log($"Casos {cG},{cQ}; combinacao {cC}; casos no modelo = {link.Structure.Cases.GetAll().Count}");

        link.GenerateMesh();
        link.App.Project.SaveAs(rtd);
        Log($"Modelo salvo: {rtd}; nos = {link.Structure.Nodes.GetAll().Count}");

        if (calculate)
        {
            Log("Calculando via COM (limite 180 s)...");
            int status = -999;
            var th = new Thread(() => { status = link.Calculate(); });
            th.SetApartmentState(ApartmentState.STA);
            th.Start();
            if (!th.Join(TimeSpan.FromSeconds(180)))
            {
                Log("Calculate NAO retornou em 180 s (mesmo comportamento registrado na skill).");
                return 3;
            }
            Log($"Calculate retornou {status}; resultados disponiveis = {link.ResultsAvailable}");
        }

        if (!link.ResultsAvailable)
        {
            Log("Sem resultados. Calcule no Robot (Analise > Calculos) e rode com --read.");
            return 2;
        }

        // Beam: q = 10 kN/m, L = 6 m, I = b h^3 / 12
        double I = 0.20 * Math.Pow(0.50, 3) / 12, q = 10000;
        Log("Viga biapoiada (caso Q):");
        Check("Reacao FZ apoio A [N]", link.NodeReaction(nA, cQ)[2], q * L / 2, 1);
        Check("Reacao FZ apoio B [N]", link.NodeReaction(nB, cQ)[2], q * L / 2, 1);
        Check("|MY| no meio do vao [N.m]", Math.Abs(link.BarForce(b1, cQ, 1.0)[4]), q * L * L / 8, 1);
        Check("|UZ| no meio do vao [m]", Math.Abs(link.NodeDisplacement(nM, cQ)[2]), 5 * q * Math.Pow(L, 4) / (384 * E * I), 3);

        Log("Viga engastada com rotulas nas pontas, dividida no meio (caso Q):");
        Check("|MY| no meio do vao [N.m]", Math.Abs(link.BarForce(rb1, cQ, 1.0)[4]), q * L * L / 8, 1);
        Check("|MY| na ponta inicial [N.m]", Math.Abs(link.BarForce(rb1, cQ, 0.0)[4]), 0, 1);
        Check("|MY| na ponta final [N.m]", Math.Abs(link.BarForce(rb2, cQ, 1.0)[4]), 0, 1);
        Check("|UZ| no meio do vao [m]", Math.Abs(link.NodeDisplacement(rM, cQ)[2]), 5 * q * Math.Pow(L, 4) / (384 * E * I), 3);

        Log("Placa sobre Winkler (centro do painel):");
        int nC = link.FindNearestNode(5, 5, 0, out double dC);
        Log($"  no mais proximo do centro: {nC} (a {dC:F3} m); nos no modelo = {link.Structure.Nodes.GetAll().Count}");
        Check("UZ caso G [m]", -link.NodeDisplacement(nC, cG)[2], GAMMA * 0.5 / 20e6, 1);
        Check("UZ caso Q [m]", -link.NodeDisplacement(nC, cQ)[2], 10000 / 20e6, 1);
        Check("UZ combinacao 1.4G+1.4Q [m]", -link.NodeDisplacement(nC, cC)[2], 1.4 * (GAMMA * 0.5 + 10000) / 20e6, 1);

        var forces = link.PanelElementForces(panel, cQ, out var elements);
        double mmax = forces.Count == 0 ? double.NaN : forces.Max(f => Math.Abs(f[0]));
        Log($"  Painel: {elements.Count} elementos finitos; |MXX| max caso Q = {mmax:G4} N.m/m (placa livre com carga uniforme sobre Winkler: ~0)");

        link.EndSession();
        Log(failures == 0 ? "TODAS AS AFERICOES OK" : $"{failures} AFERICAO(OES) FORA DA TOLERANCIA");
        return failures;
    }
}
