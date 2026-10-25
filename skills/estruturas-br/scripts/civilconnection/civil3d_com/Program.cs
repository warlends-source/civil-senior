// Smoke test for the CivilConnection 2027 COM path and CivilPython 2027 commands.
// Mirrors CivilApplication.GetApplication (P/Invoke GetActiveObject + GetInterfaceObject)
// and the SendCommand / poll-XML pattern used by Corridor, Baseline and CivilDocument.
using System.Diagnostics;
using System.Runtime.InteropServices;

static class P
{
    [DllImport("ole32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    static extern void CLSIDFromProgID(string progId, out Guid clsid);
    [DllImport("oleaut32.dll", PreserveSig = false)]
    static extern void GetActiveObject(ref Guid rclsid, IntPtr reserved, [MarshalAs(UnmanagedType.IUnknown)] out object ppunk);

    static object GetActive(string progId)
    {
        CLSIDFromProgID(progId, out Guid clsid);
        GetActiveObject(ref clsid, IntPtr.Zero, out object o);
        return o;
    }

    // AutoCAD rejects COM calls while busy (RPC_E_CALL_REJECTED / RPC_E_SERVERCALL_RETRYLATER)
    static T Retry<T>(Func<T> f)
    {
        for (int i = 0; ; i++)
        {
            try { return f(); }
            catch (COMException ex) when (((uint)ex.HResult == 0x80010001 || (uint)ex.HResult == 0x8001010A) && i < 600)
            { Thread.Sleep(500); }
        }
    }
    static void Retry(Action a) => Retry(() => { a(); return 0; });

    static void WaitQuiescent(dynamic app)
    {
        for (int i = 0; i < 1200; i++)
        {
            try { if ((bool)app.GetAcadState().IsQuiescent) return; } catch (COMException) { }
            Thread.Sleep(500);
        }
        throw new TimeoutException("AutoCAD not quiescent");
    }

    static string Tmp => Environment.GetEnvironmentVariable("TMP", EnvironmentVariableTarget.User);

    static void Step(string name, Action a)
    {
        Console.Write($"[{name}] ");
        try { a(); }
        catch (Exception ex) { Console.WriteLine($"FAIL: {ex.GetType().Name}: {ex.Message}"); Failures++; }
    }
    static int Failures;

    // Same pattern as CivilConnection: send command, then wait for a fresh XML in %TMP%
    static void RunExport(dynamic doc, dynamic app, string command, string xmlName)
    {
        string path = Path.Combine(Tmp, xmlName);
        if (File.Exists(path)) File.Delete(path);
        DateTime start = DateTime.Now;
        Retry(() => doc.SendCommand(command));
        WaitQuiescent(app);
        var sw = Stopwatch.StartNew();
        while (!File.Exists(path) && sw.Elapsed < TimeSpan.FromSeconds(60)) Thread.Sleep(250);
        if (!File.Exists(path)) throw new Exception($"{xmlName} not created");
        var xml = System.Xml.Linq.XDocument.Load(path);
        int elements = xml.Descendants().Count();
        Console.WriteLine($"OK  {xmlName}: {new FileInfo(path).Length:N0} bytes, {elements:N0} XML elements, root <{xml.Root.Name}>");
    }

    static int Main(string[] args)
    {
        string dwg = args[0];
        const string acadProgId = "AutoCAD.Application.26";
        const string aeccProgId = "AeccXUiRoadway.AeccRoadwayApplication.13.9";

        dynamic app = null;
        try { app = GetActive(acadProgId); Console.WriteLine("Attached to running Civil 3D 2027"); }
        catch (COMException ex) when ((uint)ex.HResult == 0x800401E3)
        {
            Console.WriteLine("Starting Civil 3D 2027 (Metric)...");
            Process.Start(new ProcessStartInfo(@"D:\Autodesk\AutoCAD 2027\acad.exe",
                @"/ld ""D:\Autodesk\AutoCAD 2027\AecBase.dbx"" /p ""<<C3D_Metric>>"" /product C3D /language en-US /nologo"));
            var sw = Stopwatch.StartNew();
            while (app == null && sw.Elapsed < TimeSpan.FromMinutes(10))
            {
                Thread.Sleep(3000);
                try { app = GetActive(acadProgId); } catch (COMException) { }
            }
            if (app == null) { Console.WriteLine("Civil 3D did not register in the ROT"); return 2; }
        }
        WaitQuiescent(app);
        Console.WriteLine($"AutoCAD version: {Retry(() => (string)app.Version)}");

        dynamic doc = Retry(() => app.Documents.Open(dwg, false));
        WaitQuiescent(app);
        Console.WriteLine($"Opened: {Retry(() => (string)doc.Name)}");

        dynamic aecc = null, aeccDoc = null;
        string corridorHandle = null, corridorName = null, surfaceHandle = null;

        Step("COM GetInterfaceObject " + aeccProgId, () =>
        {
            aecc = Retry(() => app.GetInterfaceObject(aeccProgId));
            aeccDoc = Retry(() => aecc.ActiveDocument);
            Console.WriteLine($"OK  Civil document: {(string)aeccDoc.Name}");
        });

        Step("COM corridors/baselines", () =>
        {
            dynamic corridors = aeccDoc.Corridors;
            int n = corridors.Count;
            Console.WriteLine($"OK  {n} corridor(s)");
            for (int i = 0; i < n; i++)
            {
                dynamic c = corridors.Item(i);
                if (corridorHandle == null) { corridorHandle = (string)c.Handle; corridorName = (string)c.Name; }
                dynamic baselines = c.Baselines;
                Console.WriteLine($"      - {(string)c.Name} (handle {(string)c.Handle}), {(int)baselines.Count} baseline(s)");
                for (int b = 0; b < (int)baselines.Count; b++)
                {
                    dynamic bl = baselines.Item(b);
                    Console.WriteLine($"          baseline {b}: alignment '{(string)bl.Alignment.Name}', {(int)bl.BaselineRegions.Count} region(s), stations {(double)bl.StartStation:F2}-{(double)bl.EndStation:F2}");
                }
            }
        });

        Step("COM alignments/surfaces", () =>
        {
            Console.WriteLine($"OK  {(int)aeccDoc.AlignmentsSiteless.Count} siteless alignment(s), {(int)aeccDoc.Surfaces.Count} surface(s)");
            if ((int)aeccDoc.Surfaces.Count > 0) surfaceHandle = (string)aeccDoc.Surfaces.Item(0).Handle;
        });

        // CivilPython export commands run only when they are already available in the session
        // (CivilPython.bundle installed in ApplicationPlugins). Nothing is loaded or changed here.
        if (args.Length > 1 && args[1] == "--exports")
        {
            if (corridorHandle != null)
            {
                Step("-ExportCorridorFeatureLinesToXml", () => RunExport(doc, app, $"-ExportCorridorFeatureLinesToXml\n{corridorHandle}\n", $"CorridorFeatureLines_{corridorName}.xml"));
                Step("-ExportSubassemblyShapesToXML", () => RunExport(doc, app, $"-ExportSubassemblyShapesToXML\n{corridorHandle}\n-1\n-1\n", "CorridorShapes.xml"));
                Step("-ExportSubassemblyLinksToXML", () => RunExport(doc, app, $"-ExportSubassemblyLinksToXML\n{corridorHandle}\n-1\n-1\n", "CorridorLinks.xml"));
            }
            Step("-ExportLandFeatureLinesToXml", () => RunExport(doc, app, "-ExportLandFeatureLinesToXml\n", "LandFeatureLinesReport.xml"));
            if (surfaceHandle != null)
                Step("-ExportSurfaceToXML", () => RunExport(doc, app, $"-ExportSurfaceToXML\n{surfaceHandle}\n", "Surface.xml"));
        }
        else
        {
            Console.WriteLine("[CivilPython exports] skipped (pass --exports once CivilPython.bundle is installed)");
        }

        Console.WriteLine(Failures == 0 ? "ALL PASSED" : $"{Failures} FAILURE(S)");
        return Failures;
    }
}
