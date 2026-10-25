// Read-only: for every analytical member, end points (m) and section height direction, written to a CSV file.
var assoc = Autodesk.Revit.DB.Structure.AnalyticalToPhysicalAssociationManager.GetAnalyticalToPhysicalAssociationManager(document);
var inv = System.Globalization.CultureInfo.InvariantCulture;
var lines = new List<string> { "type;ax;ay;az;bx;by;bz;ux;uy;uz" };
foreach (var am in new FilteredElementCollector(document).OfClass(typeof(Autodesk.Revit.DB.Structure.AnalyticalMember)).Cast<Autodesk.Revit.DB.Structure.AnalyticalMember>())
{
    var fi = document.GetElement(assoc.GetAssociatedElementId(am.Id)) as FamilyInstance;
    if (fi == null) continue;
    var c = am.GetCurve();
    XYZ a = c.GetEndPoint(0), b = c.GetEndPoint(1), ax = (b - a).Normalize();
    // same rule as RevitToRobot.SectionUp
    Transform t = fi.GetTransform();
    XYZ up = Math.Abs(t.BasisZ.DotProduct(ax)) > 0.99 ? t.BasisY : t.BasisZ;
    up = (up - ax * up.DotProduct(ax)).Normalize();
    lines.Add(string.Join(";", new[] { fi.Symbol.Name.Replace(";", ","),
        (a.X * 0.3048).ToString("R", inv), (a.Y * 0.3048).ToString("R", inv), (a.Z * 0.3048).ToString("R", inv),
        (b.X * 0.3048).ToString("R", inv), (b.Y * 0.3048).ToString("R", inv), (b.Z * 0.3048).ToString("R", inv),
        up.X.ToString("R", inv), up.Y.ToString("R", inv), up.Z.ToString("R", inv) }));
}
System.IO.File.WriteAllLines((string)parameters[0], lines, new System.Text.UTF8Encoding(false));
return (lines.Count - 1) + " membros exportados";
