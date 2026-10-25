// Read-only: document state and distance from every member end to the closest other member axis (m)
var members = new List<(long Id, XYZ A, XYZ B)>();
foreach (var fi in new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType().OfType<FamilyInstance>()
    .Concat(new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().OfType<FamilyInstance>()))
{
    XYZ a, b;
    if (fi.Location is LocationCurve lc) { a = lc.Curve.GetEndPoint(0); b = lc.Curve.GetEndPoint(1); }
    else {
        var lp = (LocationPoint)fi.Location;
        double z0 = ((Level)document.GetElement(fi.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM).AsElementId())).Elevation + fi.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).AsDouble();
        double z1 = ((Level)document.GetElement(fi.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).AsElementId())).Elevation + fi.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).AsDouble();
        a = new XYZ(lp.Point.X, lp.Point.Y, z0); b = new XYZ(lp.Point.X, lp.Point.Y, z1);
    }
    members.Add((fi.Id.Value, a * 0.3048, b * 0.3048));
}
Func<XYZ, XYZ, XYZ, double> segDist = (p, a, b) => { var ab = b - a; double t = Math.Max(0, Math.Min(1, (p - a).DotProduct(ab) / ab.DotProduct(ab))); return p.DistanceTo(a + ab * t); };
var d = new List<double>();
for (int i = 0; i < members.Count; i++)
    foreach (var p in new[] { members[i].A, members[i].B })
    {
        double best = double.MaxValue;
        for (int j = 0; j < members.Count; j++) if (j != i) best = Math.Min(best, segDist(p, members[j].A, members[j].B));
        d.Add(best);
    }
var bins = new[] { 0.001, 0.01, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0, 1e9 };
var sb = new System.Text.StringBuilder();
sb.AppendLine($"Documento: {document.Title} | workshared={document.IsWorkshared} | modificado={document.IsModified} | caminho={document.PathName}");
double prev = 0;
foreach (var b in bins) { sb.AppendLine($"  {prev,6:0.###} a {(b > 1e8 ? "inf" : b.ToString("0.###")),5} m : {d.Count(x => x >= prev && x < b)} extremidades"); prev = b; }
sb.AppendLine("Copia existe: " + System.IO.File.Exists(@"D:\Downloads\Est.Galpão V24 - analitico.rvt"));
return sb.ToString();
