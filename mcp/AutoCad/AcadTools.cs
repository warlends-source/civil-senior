using ModelContextProtocol.Server;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

namespace CivilSenior.Mcp.AutoCad;

/// <summary>
/// AutoCAD 2027 drawing tools (also valid inside Civil 3D). Coordinates and lengths are in drawing units (see INSUNITS
/// in acad_status). The official Autodesk AutoCAD MCP (MCPHTTPSTART) covers property queries and edits; these tools add
/// drawing creation and file handling.
/// </summary>
[McpServerToolType]
public static class AcadTools
{
    private static readonly string[] InsUnits = { "unitless", "in", "ft", "mi", "mm", "cm", "m", "km" };

    [McpServerTool(Name = "acad_status"), Description("AutoCAD / Civil 3D connection: version, whether Civil 3D objects are available, open drawings, active drawing and its units.")]
    public static Task<string> Status(AcadSession s) => s.Run(app =>
    {
        var docs = new List<object>();
        dynamic all = app.Documents;
        for (int i = 0; i < (int)all.Count; i++)
        {
            dynamic d = all.Item(i);
            docs.Add(new { name = (string)d.Name, path = (string)d.FullName, saved = (bool)d.Saved, readOnly = (bool)d.ReadOnly });
        }
        bool civil = false;
        object units = null, activeName = null;
        if (docs.Count > 0)
        {
            dynamic doc = app.ActiveDocument;
            activeName = (string)doc.Name;
            int u = (int)(short)doc.GetVariable("INSUNITS");
            units = u >= 0 && u < InsUnits.Length ? InsUnits[u] : u.ToString();
            try { AcadSession.Civil(app); civil = true; } catch (InvalidOperationException) { }
        }
        return new { version = (string)app.Version, civil3d = civil, activeDrawing = activeName, units, documents = docs };
    });

    [McpServerTool(Name = "acad_launch"), Description("Starts Civil 3D 2027 (or plain AutoCAD 2027) if it is not running and waits until it accepts commands (can take several minutes).")]
    public static Task<string> Launch(AcadSession s, [Description("civil3d or autocad")] string product = "civil3d", [Description("Civil 3D metric profile")] bool metric = true, int timeoutSeconds = 600)
        => s.Launch(product, metric, timeoutSeconds);

    [McpServerTool(Name = "acad_open"), Description("Opens a drawing (.dwg) and makes it active.")]
    public static Task<string> Open(AcadSession s, [Description("Full path of the .dwg")] string path, bool readOnly = false) => s.Run(app =>
    {
        dynamic doc = app.Documents.Open(path, readOnly);
        AcadSession.WaitQuiescent(app);
        return new { ok = true, name = (string)doc.Name };
    });

    [McpServerTool(Name = "acad_new"), Description("Creates a new drawing, optionally from a template (.dwt).")]
    public static Task<string> New(AcadSession s, [Description("Template path (empty = default)")] string template = "") => s.Run(app =>
    {
        dynamic doc = string.IsNullOrWhiteSpace(template) ? app.Documents.Add() : app.Documents.Add(template);
        return new { ok = true, name = (string)doc.Name };
    });

    [McpServerTool(Name = "acad_save"), Description("Saves the active drawing; with a path, saves it as a new file.")]
    public static Task<string> Save(AcadSession s, [Description("Full path (empty = save in place)")] string path = "") => s.Run(app =>
    {
        dynamic doc = app.ActiveDocument;
        if (string.IsNullOrWhiteSpace(path)) doc.Save(); else doc.SaveAs(path);
        return new { ok = true, path = (string)doc.FullName };
    });

    [McpServerTool(Name = "acad_layers"), Description("Lists the layers of the active drawing.")]
    public static Task<string> Layers(AcadSession s) => s.Run(app =>
    {
        var list = new List<object>();
        dynamic layers = app.ActiveDocument.Layers;
        for (int i = 0; i < (int)layers.Count; i++)
        {
            dynamic l = layers.Item(i);
            list.Add(new { name = (string)l.Name, color = (int)l.color, on = (bool)l.LayerOn, frozen = (bool)l.Freeze, locked = (bool)l.Lock, linetype = (string)l.Linetype });
        }
        return list;
    });

    [McpServerTool(Name = "acad_create_layer"), Description("Creates a layer (or updates color and linetype of an existing one).")]
    public static Task<string> CreateLayer(AcadSession s, string name, [Description("AutoCAD color index 1-255")] int colorIndex = 7, string linetype = "Continuous") => s.Run(app =>
    {
        dynamic layer = app.ActiveDocument.Layers.Add(name);
        layer.color = colorIndex;
        try { layer.Linetype = linetype; } catch (COMException) { return new { name, warning = $"linetype {linetype} is not loaded; kept the current one" }; }
        return (object)new { name };
    });

    [McpServerTool(Name = "acad_query"), Description("Lists model space entities with handle, type, layer, bounding box and length/area when available. Filter by type (substring of the object name, e.g. Polyline, Circle, AeccDbAlignment), layer, or a list of handles.")]
    public static Task<string> Query(AcadSession s, string type = "", string layer = "", [Description("JSON array of handles (optional)")] string handles = "", int limit = 200) => s.Run(app =>
    {
        dynamic doc = app.ActiveDocument;
        var items = new List<dynamic>();
        if (!string.IsNullOrWhiteSpace(handles))
        {
            foreach (string h in Json.List<string>(handles)) items.Add(doc.HandleToObject(h));
        }
        else
        {
            dynamic ms = doc.ModelSpace;
            for (int i = 0; i < (int)ms.Count; i++) items.Add(ms.Item(i));
        }

        var result = new List<object>();
        int matched = 0;
        foreach (dynamic e in items)
        {
            string name = e.ObjectName;
            string lay = e.Layer;
            if (type.Length > 0 && name.IndexOf(type, StringComparison.OrdinalIgnoreCase) < 0) continue;
            if (layer.Length > 0 && !lay.Equals(layer, StringComparison.OrdinalIgnoreCase)) continue;
            matched++;
            if (result.Count >= limit) continue;
            double[] min = null, max = null;
            try { object mn, mx; e.GetBoundingBox(out mn, out mx); min = (double[])mn; max = (double[])mx; } catch (Exception) { }
            result.Add(new { handle = (string)e.Handle, type = name, layer = lay, min, max, length = TryDouble(() => e.Length), area = TryDouble(() => e.Area) });
        }
        return new { matched, returned = result.Count, entities = result };
    });

    private static double? TryDouble(Func<dynamic> get)
    {
        try { return (double)get(); } catch (Exception) { return null; }
    }

    [McpServerTool(Name = "acad_draw_polyline"), Description("Draws a polyline in model space: 2D lightweight polyline when all z are equal (at that elevation), otherwise a 3D polyline. Returns the handle.")]
    public static Task<string> DrawPolyline(AcadSession s, [Description("JSON array of [x,y] or [x,y,z]")] string points, bool closed = false, string layer = "") => s.Run(app =>
    {
        List<double[]> pts = Json.Points(points);
        if (pts.Count < 2) throw new ArgumentException("a polyline needs at least two points");
        dynamic ms = app.ActiveDocument.ModelSpace;
        dynamic pl;
        if (pts.All(p => Math.Abs(p[2] - pts[0][2]) < 1e-9))
        {
            pl = ms.AddLightWeightPolyline(pts.SelectMany(p => new[] { p[0], p[1] }).ToArray());
            pl.Elevation = pts[0][2];
        }
        else
        {
            pl = ms.Add3DPoly(pts.SelectMany(p => p).ToArray());
        }
        pl.Closed = closed;
        if (layer.Length > 0) pl.Layer = layer;
        return new { handle = (string)pl.Handle, vertices = pts.Count };
    });

    [McpServerTool(Name = "acad_draw_circle"), Description("Draws a circle in model space. Returns the handle.")]
    public static Task<string> DrawCircle(AcadSession s, [Description("[x,y] or [x,y,z]")] string center, double radius, string layer = "") => s.Run(app =>
    {
        double[] c = Json.Points("[" + center + "]")[0];
        dynamic circle = app.ActiveDocument.ModelSpace.AddCircle(c, radius);
        if (layer.Length > 0) circle.Layer = layer;
        return new { handle = (string)circle.Handle };
    });

    [McpServerTool(Name = "acad_draw_text"), Description("Writes single-line text in model space. Returns the handle.")]
    public static Task<string> DrawText(AcadSession s, string text, [Description("[x,y] or [x,y,z] insertion point")] string position, double height = 2.5, [Description("Rotation in degrees")] double rotation = 0, string layer = "") => s.Run(app =>
    {
        double[] p = Json.Points("[" + position + "]")[0];
        dynamic t = app.ActiveDocument.ModelSpace.AddText(text, p, height);
        t.Rotation = rotation * Math.PI / 180;
        if (layer.Length > 0) t.Layer = layer;
        return new { handle = (string)t.Handle };
    });

    [McpServerTool(Name = "acad_modify"), Description("Changes the layer and/or color of entities given by handle, or deletes them (delete = true).")]
    public static Task<string> Modify(AcadSession s, [Description("JSON array of handles")] string handles, string layer = "", [Description("Color index 1-255 (0 = keep)")] int colorIndex = 0, bool delete = false) => s.Run(app =>
    {
        dynamic doc = app.ActiveDocument;
        int done = 0;
        foreach (string h in Json.List<string>(handles))
        {
            dynamic e = doc.HandleToObject(h);
            if (delete) { e.Delete(); done++; continue; }
            if (layer.Length > 0) e.Layer = layer;
            if (colorIndex > 0) e.color = colorIndex;
            done++;
        }
        return new { ok = true, entities = done, deleted = delete };
    });

    [McpServerTool(Name = "acad_zoom_extents"), Description("Zooms the active view to the drawing extents.")]
    public static Task<string> ZoomExtents(AcadSession s) => s.Run(app => { app.ZoomExtents(); return new { ok = true }; });

    [McpServerTool(Name = "acad_command"), Description("Runs a command line string in the active drawing and waits for AutoCAD to be idle, e.g. \"_.REGEN \" or \"-LAYER _S 0  \". Use command-line versions (prefix -) to avoid dialogs; a dialog left open blocks AutoCAD.")]
    public static Task<string> Command(AcadSession s, string command) => s.Run(app =>
    {
        string cmd = command.EndsWith(" ") || command.EndsWith("\n") ? command : command + "\n";
        AcadSession.Command(app, cmd);
        return new { ok = true };
    });
}
