using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;

namespace CivilSenior.Mcp.AutoCad;

/// <summary>
/// Connection to the running AutoCAD / Civil 3D 2027 through COM, used from a single STA thread.
/// </summary>
public sealed class AcadSession : IDisposable
{
    public const string AcadProgId = "AutoCAD.Application.26";               // 2027 only
    public const string CivilProgId = "AeccXUiRoadway.AeccRoadwayApplication.13.9";
    public const string AcadExe = @"D:\Autodesk\AutoCAD 2027\acad.exe";

    private readonly ComThread _com = new("acad-com");
    private dynamic _app;

    internal Task<string> Run(Func<dynamic, object> action)
    {
        return _com.Run<string>(() =>
        {
            try { object result = action(App()); return Json.Of(result); }
            catch (Exception ex)
            {
                if (ex is COMException) _app = null;
                return Json.Error(Message(ex));
            }
        });
    }

    private dynamic App()
    {
        if (_app != null)
        {
            try { string _ = _app.Name; return _app; }
            catch (COMException) { _app = null; }
        }
        try { _app = ComThread.GetActiveObject(AcadProgId); }
        catch (COMException) { throw new InvalidOperationException("AutoCAD / Civil 3D 2027 is not running. Open it or call acad_launch."); }
        return _app;
    }

    /// <summary>
    /// Civil 3D document of the active drawing (fails in plain AutoCAD).
    /// </summary>
    internal static dynamic Civil(dynamic app)
    {
        try
        {
            dynamic aecc = app.GetInterfaceObject(CivilProgId);
            return aecc.ActiveDocument;
        }
        catch (Exception)
        {
            throw new InvalidOperationException("Civil 3D objects are not available: the running product is plain AutoCAD or no drawing is open.");
        }
    }

    internal static void WaitQuiescent(dynamic app, int timeoutMs = 600_000)
    {
        var sw = Stopwatch.StartNew();
        while (sw.ElapsedMilliseconds < timeoutMs)
        {
            try { if ((bool)app.GetAcadState().IsQuiescent) return; } catch (COMException) { }
            Thread.Sleep(250);
        }
        throw new TimeoutException("AutoCAD stayed busy.");
    }

    /// <summary>
    /// Sends a command line string and waits until AutoCAD is idle again.
    /// </summary>
    internal static void Command(dynamic app, string command)
    {
        dynamic doc = app.ActiveDocument;
        doc.SendCommand(command);
        WaitQuiescent(app);
    }

    /// <summary>
    /// Starts Civil 3D (or plain AutoCAD) 2027 when it is not running and waits until it accepts COM calls.
    /// </summary>
    public async Task<string> Launch(string product, bool metric, int timeoutSeconds)
    {
        return await Task.Run(async () =>
        {
            if (Process.GetProcessesByName("acad").Length == 0)
            {
                string args = product.Equals("autocad", StringComparison.OrdinalIgnoreCase)
                    ? "/product ACAD /nologo"
                    : $"/ld \"{Path.Combine(Path.GetDirectoryName(AcadExe), "AecBase.dbx")}\" /p \"<<C3D_{(metric ? "Metric" : "Imperial")}>>\" /product C3D /language en-US /nologo";
                // shell execute: the new process must not inherit the MCP stdio pipes
                Process.Start(new ProcessStartInfo(AcadExe, args) { UseShellExecute = true });
            }
            var sw = Stopwatch.StartNew();
            while (sw.Elapsed.TotalSeconds < timeoutSeconds)
            {
                string state = await Run(app => (bool)app.GetAcadState().IsQuiescent ? "ready" : "busy");
                if (state.Contains("ready")) return Json.Of(new { ok = true, seconds = (int)sw.Elapsed.TotalSeconds });
                await Task.Delay(3000);
            }
            return Json.Error("AutoCAD did not become ready in time.");
        });
    }

    internal static string Message(Exception ex)
    {
        while (ex.InnerException != null && (ex is System.Reflection.TargetInvocationException || ex is AggregateException)) ex = ex.InnerException;
        return ex.Message;
    }

    public void Dispose() => _com.Dispose();
}
