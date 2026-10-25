using CivilConnection.Robot;
using RobotOM;
using System;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;

namespace CivilSenior.Mcp.Robot;

/// <summary>
/// One connection to the running Robot, used from a single STA thread. Robot dialogs are disabled (Interactive = 0)
/// only while a tool runs, so the user can keep working in Robot between calls.
/// </summary>
public sealed class RobotSession : IDisposable
{
    public const string RobotExe = @"D:\Autodesk\Robot Structural Analysis Professional 2027\Exe\robot.EXE";

    private readonly ComThread _com = new("robot-com");
    private RobotLink _link;

    internal Task<string> Run(Func<RobotLink, object> action, bool refreshNodes = false)
    {
        return _com.Run(() =>
        {
            try
            {
                RobotLink link = Link();
                link.App.Interactive = 0;
                try
                {
                    if (refreshNodes) link.Refresh();
                    return Json.Of(action(link));
                }
                finally
                {
                    try { link.App.Interactive = 1; } catch (COMException) { }
                }
            }
            catch (Exception ex)
            {
                if (ex is COMException) _link = null;
                return Json.Error(Message(ex));
            }
        });
    }

    public Task<string> NewProject(IRobotProjectType type)
    {
        return _com.Run(() =>
        {
            try
            {
                _link = RobotLink.Connect(true, type);
                _link.App.Interactive = 1;
                return Json.Of(new { ok = true, projectType = type.ToString() });
            }
            catch (Exception ex) { return Json.Error(Message(ex)); }
        });
    }

    /// <summary>
    /// Starts Robot when it is not running and waits for its main window.
    /// </summary>
    public static async Task<string> Launch(int timeoutSeconds)
    {
        if (Process.GetProcessesByName("robot").Length > 0) return Json.Of(new { ok = true, alreadyRunning = true });
        Process.Start(new ProcessStartInfo(RobotExe) { UseShellExecute = true });
        var sw = Stopwatch.StartNew();
        while (sw.Elapsed.TotalSeconds < timeoutSeconds)
        {
            await Task.Delay(3000);
            Process p = Process.GetProcessesByName("robot").FirstOrDefault();
            if (p != null && p.MainWindowHandle != IntPtr.Zero && sw.Elapsed.TotalSeconds > 30) return Json.Of(new { ok = true, seconds = (int)sw.Elapsed.TotalSeconds });
        }
        return Json.Error("Robot did not open its main window in time.");
    }

    private RobotLink Link()
    {
        if (_link != null)
        {
            try { _ = _link.App.Version; return _link; }
            catch (COMException) { _link = null; }
        }
        _link = RobotLink.Connect(false, IRobotProjectType.I_PT_SHELL);
        return _link;
    }

    private static string Message(Exception ex)
    {
        while (ex.InnerException != null && (ex is System.Reflection.TargetInvocationException || ex is AggregateException)) ex = ex.InnerException;
        return ex.Message;
    }

    public void Dispose() => _com.Dispose();
}
