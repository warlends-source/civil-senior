var assoc = Autodesk.Revit.DB.Structure.AnalyticalToPhysicalAssociationManager.GetAnalyticalToPhysicalAssociationManager(document);
var mem = new FilteredElementCollector(document).OfClass(typeof(Autodesk.Revit.DB.Structure.AnalyticalMember)).Cast<Autodesk.Revit.DB.Structure.AnalyticalMember>()
  .Select(m => { var c = m.GetCurve(); var ph = document.GetElement(assoc.GetAssociatedElementId(m.Id)) as FamilyInstance; return (A: c.GetEndPoint(0) * 0.3048, B: c.GetEndPoint(1) * 0.3048, Fam: ph?.Symbol.FamilyName + ":" + ph?.Symbol.Name); }).ToList();
Func<XYZ, XYZ, XYZ, double> seg = (p, a, b) => { var ab = b - a; double t = Math.Max(0, Math.Min(1, (p - a).DotProduct(ab) / ab.DotProduct(ab))); return p.DistanceTo(a + ab * t); };
var free = new List<(double D, string Fam, bool Dup)>();
for (int i = 0; i < mem.Count; i++)
  foreach (var p in new[] { mem[i].A, mem[i].B }) {
    double best = double.MaxValue; bool dup = false;
    for (int j = 0; j < mem.Count; j++) { if (j == i) continue; double d = seg(p, mem[j].A, mem[j].B); if (d < best) best = d;
      if (mem[j].A.DistanceTo(mem[i].A) < 0.001 && mem[j].B.DistanceTo(mem[i].B) < 0.001 || mem[j].A.DistanceTo(mem[i].B) < 0.001 && mem[j].B.DistanceTo(mem[i].A) < 0.001) dup = true; }
    if (best > 0.001) free.Add((best, mem[i].Fam, dup));
  }
var sb = new System.Text.StringBuilder();
sb.AppendLine("pontas livres: " + free.Count + " | membros duplicados (mesmos extremos): " + free.Count(f => f.Dup));
foreach (var g in free.GroupBy(f => f.D < 0.25 ? "< 0.25 m" : f.D < 0.5 ? "0.25-0.5 m" : f.D < 1 ? "0.5-1 m" : "> 1 m")) sb.AppendLine("  " + g.Key + ": " + g.Count());
foreach (var g in free.GroupBy(f => f.Fam).OrderByDescending(g => g.Count())) sb.AppendLine("  " + g.Key + ": " + g.Count() + " | dist min/med/max = " + g.Min(x => x.D).ToString("0.000") + "/" + g.Average(x => x.D).ToString("0.000") + "/" + g.Max(x => x.D).ToString("0.000"));
return sb.ToString();
