using ModelContextProtocol.Server;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Xml.Linq;

namespace CivilSenior.Mcp.AutoCad;

/// <summary>
/// Civil 3D 2027 engineering data: alignments, profiles, surfaces and corridors (drawing units).
/// Corridor feature lines and surface triangles come from the CivilPython commands (CivilPython.bundle must be installed).
/// </summary>
[McpServerToolType]
public static class Civil3DTools
{
    private static IEnumerable<dynamic> Items(dynamic collection)
    {
        int n = (int)collection.Count;
        for (int i = 0; i < n; i++) yield return collection.Item(i);
    }

    private static IEnumerable<dynamic> Alignments(dynamic civil)
    {
        foreach (dynamic a in Items(civil.AlignmentsSiteless)) yield return a;
        foreach (dynamic site in Items(civil.Sites))
            foreach (dynamic a in Items(site.Alignments)) yield return a;
    }

    private static dynamic Find(IEnumerable<dynamic> items, string name, string kind)
    {
        foreach (dynamic x in items)
            if (((string)x.Name).Equals(name, StringComparison.OrdinalIgnoreCase)) return x;
        throw new ArgumentException($"{kind} '{name}' not found");
    }

    private static double? Try(Func<dynamic> get)
    {
        try
        {
            double v = (double)get();
            // empty surfaces report +/-double.MaxValue as statistics
            return Math.Abs(v) > 1e300 ? null : v;
        }
        catch (Exception) { return null; }
    }

    [McpServerTool(Name = "c3d_alignments"), Description("Lists the alignments of the active Civil 3D drawing with length, station range and profiles.")]
    public static Task<string> ListAlignments(AcadSession s) => s.Run(app =>
    {
        dynamic civil = AcadSession.Civil(app);
        var list = new List<object>();
        foreach (dynamic a in Alignments(civil))
        {
            var profiles = new List<string>();
            foreach (dynamic p in Items(a.Profiles)) profiles.Add((string)p.Name);
            list.Add(new { name = (string)a.Name, handle = (string)a.Handle, length = (double)a.Length, startStation = (double)a.StartingStation, endStation = (double)a.EndingStation, profiles });
        }
        return list;
    });

    [McpServerTool(Name = "c3d_alignment_points"), Description("Coordinates along an alignment: x, y at each station (every step, plus the ends) and an offset; with a profile name, also the profile elevation z.")]
    public static Task<string> AlignmentPoints(AcadSession s, string alignment,
        [Description("Station interval")] double step = 20,
        [Description("Offset from the alignment (right positive)")] double offset = 0,
        [Description("Profile name for elevations (optional)")] string profile = "",
        [Description("First station (omit = start of the alignment)")] double? startStation = null,
        [Description("Last station (omit = end of the alignment)")] double? endStation = null,
        int maxPoints = 1000) => s.Run(app =>
    {
        dynamic al = Find(Alignments(AcadSession.Civil(app)), alignment, "alignment");
        dynamic prof = string.IsNullOrWhiteSpace(profile) ? null : Find(Items(al.Profiles), profile, "profile");
        double s0 = startStation ?? (double)al.StartingStation;
        double s1 = endStation ?? (double)al.EndingStation;
        var stations = new List<double>();
        for (double st = s0; st < s1 - 1e-9 && stations.Count < maxPoints - 1; st += step) stations.Add(st);
        stations.Add(s1);
        var points = new List<object>();
        foreach (double st in stations)
        {
            double e = 0, n = 0;
            al.PointLocation(st, offset, ref e, ref n);
            double? z = prof == null ? null : Try(() => prof.ElevationAt(st));
            points.Add(new { station = st, x = e, y = n, z });
        }
        return new { alignment = (string)al.Name, offset, profile = prof == null ? null : (string)prof.Name, points };
    });

    [McpServerTool(Name = "c3d_station_offset"), Description("Station and offset of points relative to an alignment.")]
    public static Task<string> StationOffset(AcadSession s, string alignment, [Description("JSON array of [x,y]")] string points) => s.Run(app =>
    {
        dynamic al = Find(Alignments(AcadSession.Civil(app)), alignment, "alignment");
        var list = new List<object>();
        foreach (double[] p in Json.Points(points))
        {
            double st = 0, off = 0;
            al.StationOffset(p[0], p[1], ref st, ref off);
            list.Add(new { x = p[0], y = p[1], station = st, offset = off });
        }
        return list;
    });

    [McpServerTool(Name = "c3d_surfaces"), Description("Lists the surfaces of the active drawing with elevation statistics when available.")]
    public static Task<string> ListSurfaces(AcadSession s) => s.Run(app =>
    {
        dynamic civil = AcadSession.Civil(app);
        var list = new List<object>();
        foreach (dynamic sf in Items(civil.Surfaces))
        {
            dynamic stats = null;
            try { stats = sf.Statistics; } catch (Exception) { }
            list.Add(new
            {
                name = (string)sf.Name,
                handle = (string)sf.Handle,
                type = Name(() => sf.ObjectName),
                points = stats == null ? null : Try(() => (double)stats.NumberOfPoints),
                minElevation = stats == null ? null : Try(() => stats.MinElevation),
                maxElevation = stats == null ? null : Try(() => stats.MaxElevation),
                meanElevation = stats == null ? null : Try(() => stats.MeanElevation),
                area2d = stats == null ? null : Try(() => stats.Area2d),
                area3d = stats == null ? null : Try(() => stats.Area3d)
            });
        }
        return list;
    });

    [McpServerTool(Name = "c3d_surface_elevations"), Description("Surface elevation at points (null outside the surface).")]
    public static Task<string> SurfaceElevations(AcadSession s, string surface, [Description("JSON array of [x,y]")] string points) => s.Run(app =>
    {
        dynamic sf = Find(Items(AcadSession.Civil(app).Surfaces), surface, "surface");
        return Json.Points(points).Select(p => new { x = p[0], y = p[1], z = Try(() => sf.FindElevationAtXY(p[0], p[1])) }).ToList();
    });

    [McpServerTool(Name = "c3d_corridors"), Description("Lists the corridors with their baselines (alignment, profile, station range, regions).")]
    public static Task<string> ListCorridors(AcadSession s) => s.Run(app =>
    {
        var list = new List<object>();
        foreach (dynamic c in Items(AcadSession.Civil(app).Corridors))
        {
            var baselines = new List<object>();
            foreach (dynamic b in Items(c.Baselines))
            {
                baselines.Add(new
                {
                    alignment = Name(() => b.Alignment.Name),
                    profile = Name(() => b.Profile.Name),
                    startStation = Try(() => b.StartStation),
                    endStation = Try(() => b.EndStation),
                    regions = (int)b.BaselineRegions.Count
                });
            }
            list.Add(new { name = (string)c.Name, handle = (string)c.Handle, baselines });
        }
        return list;
    });

    private static string Name(Func<dynamic> get)
    {
        try { return (string)get(); } catch (Exception) { return null; }
    }

    private static string TempFile(string name) => Path.Combine(Environment.GetEnvironmentVariable("TMP", EnvironmentVariableTarget.User) ?? Path.GetTempPath(), name);

    /// <summary>
    /// Runs a CivilPython export command and waits for its XML file.
    /// </summary>
    private static XDocument Export(dynamic app, string command, string file)
    {
        if (File.Exists(file)) File.Delete(file);
        AcadSession.Command(app, command);
        var sw = Stopwatch.StartNew();
        while (!File.Exists(file) && sw.Elapsed.TotalSeconds < 120) Thread.Sleep(250);
        if (!File.Exists(file)) throw new InvalidOperationException($"{Path.GetFileName(file)} was not created: check that CivilPython.bundle is installed in %APPDATA%\\Autodesk\\ApplicationPlugins.");
        for (int i = 0; ; i++)
        {
            try { return XDocument.Load(file); }
            catch (IOException) when (i < 40) { Thread.Sleep(250); }
        }
    }

    private static double D(XElement e, string a) => double.Parse((string)e.Attribute(a), CultureInfo.InvariantCulture);

    [McpServerTool(Name = "c3d_corridor_featurelines"), Description("Corridor feature lines with their codes and 3D points (x, y, z, station, offset). Filter by codes; long lines are thinned to maxPoints. Without codes, lists the codes and counts only (summary).")]
    public static Task<string> CorridorFeatureLines(AcadSession s, string corridor,
        [Description("JSON array of codes, e.g. [\"ETW\",\"Crown\"] (empty = summary of all codes)")] string codes = "",
        int maxPoints = 200) => s.Run(app =>
    {
        dynamic c = Find(Items(AcadSession.Civil(app).Corridors), corridor, "corridor");
        string name = c.Name;
        XDocument xml = Export(app, $"-ExportCorridorFeatureLinesToXML\n{(string)c.Handle}\n", TempFile($"CorridorFeatureLines_{name}.xml"));
        var lines = xml.Descendants("FeatureLine").ToList();
        if (string.IsNullOrWhiteSpace(codes))
        {
            return new { corridor = name, summary = lines.GroupBy(f => (string)f.Attribute("Code")).Select(g => new { code = g.Key, lines = g.Count(), points = g.Sum(f => f.Descendants("Point").Count()) }).OrderBy(x => x.code).ToList() };
        }
        var wanted = new HashSet<string>(Json.List<string>(codes), StringComparer.OrdinalIgnoreCase);
        var result = new List<object>();
        foreach (XElement f in lines.Where(f => wanted.Contains((string)f.Attribute("Code"))))
        {
            var pts = f.Descendants("Point").ToList();
            int stride = Math.Max(1, (int)Math.Ceiling(pts.Count / (double)maxPoints));
            var kept = pts.Where((p, i) => i % stride == 0 || i == pts.Count - 1)
                .Select(p => new[] { D(p, "X"), D(p, "Y"), D(p, "Z"), D(p, "Station"), D(p, "Offset") }).ToList();
            result.Add(new { code = (string)f.Attribute("Code"), side = (string)f.Attribute("Side"), baseline = (string)f.Ancestors("Baseline").FirstOrDefault()?.Attribute("Name"), totalPoints = pts.Count, pointOrder = "x,y,z,station,offset", points = kept });
        }
        return new { corridor = name, featureLines = result };
    });

    [McpServerTool(Name = "c3d_surface_mesh"), Description("Exports the triangles of a surface (via CivilPython) and returns vertex/triangle counts, extents and the XML path; with includeMesh = true also the vertices [x,y,z] and triangles [i,j,k] (use for small surfaces).")]
    public static Task<string> SurfaceMesh(AcadSession s, string surface, bool includeMesh = false) => s.Run(app =>
    {
        dynamic sf = Find(Items(AcadSession.Civil(app).Surfaces), surface, "surface");
        string file = TempFile("Surface.xml");
        XDocument xml = Export(app, $"-ExportSurfaceToXML\n{(string)sf.Handle}\n", file);
        var v = xml.Descendants("Vertex").Select(e => new[] { D(e, "X"), D(e, "Y"), D(e, "Z") }).ToList();
        var t = xml.Descendants("Triangle").Select(e => new[] { (int)e.Attribute("V0"), (int)e.Attribute("V1"), (int)e.Attribute("V2") }).ToList();
        return new
        {
            surface = (string)sf.Name,
            vertices = v.Count,
            triangles = t.Count,
            min = v.Count == 0 ? null : new[] { v.Min(p => p[0]), v.Min(p => p[1]), v.Min(p => p[2]) },
            max = v.Count == 0 ? null : new[] { v.Max(p => p[0]), v.Max(p => p[1]), v.Max(p => p[2]) },
            file,
            mesh = includeMesh ? new { vertices = v, triangles = t } : null
        };
    });
}
