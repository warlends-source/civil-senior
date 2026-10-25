var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static;
var alc = new System.Runtime.Loader.AssemblyLoadContext("cc_robot_a2_" + Guid.NewGuid().ToString("N"), true);
var asm = alc.LoadFromAssemblyPath((string)parameters[0]);
var linkType = asm.GetType("CivilConnection.Robot.RobotLink");
var sw = System.Diagnostics.Stopwatch.StartNew();
object link = linkType.GetMethod("Connect", flags).Invoke(null, new object[] { true, Enum.ToObject(asm.GetType("RobotOM.IRobotProjectType"), 7) });
var ids = new FilteredElementCollector(document).OfClass(typeof(Autodesk.Revit.DB.Structure.AnalyticalMember)).ToElementIds().ToList();
Func<XYZ, double[]> toRobot = p => new[] { p.X * 0.3048, p.Y * 0.3048, p.Z * 0.3048 };
var senderType = asm.GetType("CivilConnection.Robot.RevitToRobot");
object sender = Activator.CreateInstance(senderType, flags, null, new object[] { document, link, toRobot }, null);
senderType.GetMethod("Send", flags).Invoke(sender, new object[] { ids, "", 0.5, 0.0 });
var source = (List<string>)senderType.GetProperty("Source", flags).GetValue(sender);
var bars = (List<List<int>>)senderType.GetProperty("Bars", flags).GetValue(sender);
// Orientation check: Robot local z of the first bar of each member vs the section height direction in Revit
var assoc = Autodesk.Revit.DB.Structure.AnalyticalToPhysicalAssociationManager.GetAnalyticalToPhysicalAssociationManager(document);
var upMethod = senderType.GetMethod("SectionUp", flags);
var lczMethod = linkType.GetMethod("BarLocalZ", flags);
var elIds = (List<long>)senderType.GetProperty("ElementIds", flags).GetValue(sender);
var angles = new Dictionary<string, List<double>>();
for (int k = 0; k < elIds.Count; k++)
{
    if (bars[k].Count == 0) continue;
    var am = document.GetElement(new ElementId(elIds[k])) as Autodesk.Revit.DB.Structure.AnalyticalMember;
    var fi = document.GetElement(assoc.GetAssociatedElementId(am.Id)) as FamilyInstance;
    var c = am.GetCurve(); var ax = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize();
    var up = (XYZ)upMethod.Invoke(null, new object[] { fi, ax });
    var z = (double[])lczMethod.Invoke(link, new object[] { bars[k][0] });
    double ang = Math.Acos(Math.Max(-1, Math.Min(1, up.X * z[0] + up.Y * z[1] + up.Z * z[2]))) * 180 / Math.PI;
    string key = fi.Symbol.Name;
    if (!angles.ContainsKey(key)) angles[key] = new List<double>();
    angles[key].Add(ang);
}
int split = (int)linkType.GetMethod("SplitBarsAtNodes", flags).Invoke(link, null);
var bases = (List<int>)linkType.GetMethod("ColumnBaseNodes", flags).Invoke(link, null);
linkType.GetMethod("CreateSupport", flags).Invoke(link, new object[] { "ENGASTE", true, true, true, true, true, true });
linkType.GetMethod("AssignSupport", flags).Invoke(link, new object[] { bases, "ENGASTE" });
dynamic app = linkType.GetProperty("App", flags).GetValue(link);
dynamic st = app.Project.Structure;
app.Project.SaveAs((string)parameters[1]);
linkType.GetMethod("EndSession", flags).Invoke(link, null);
var r = new { Membros = ids.Count, PorOrigem = source.GroupBy(s => s).ToDictionary(g => g.Key, g => g.Count()), SemBarra = bars.Count(b => b.Count == 0),
  BarrasDivididas = split, RobotNos = (int)st.Nodes.GetAll().Count, RobotBarras = (int)st.Bars.GetAll().Count, ApoiosBasePilar = bases.Count, Segundos = Math.Round(sw.Elapsed.TotalSeconds, 1),
  DesvioOrientacao_graus = angles.ToDictionary(a => a.Key, a => $"n={a.Value.Count} max={a.Value.Max():F3}") };
alc.Unload();
return Newtonsoft.Json.JsonConvert.SerializeObject(r);
