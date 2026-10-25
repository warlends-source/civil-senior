if (!document.PathName.EndsWith("analitico.rvt")) return "ABORTADO: documento ativo nao e a copia: " + document.PathName;
var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static;
var alc = new System.Runtime.Loader.AssemblyLoadContext("cc_analytic_" + Guid.NewGuid().ToString("N"), true);
var asm = alc.LoadFromAssemblyPath((string)parameters[0]);
var bt = asm.GetType("CivilConnection.Robot.AnalyticalBuilder");
object builder = Activator.CreateInstance(bt, true);
var ids = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType().ToElementIds()
    .Concat(new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().ToElementIds())
    .Concat(new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType().ToElementIds()).ToList();
var sw = System.Diagnostics.Stopwatch.StartNew();
bt.GetMethod("Build", flags).Invoke(builder, new object[] { document, ids, 0.25 });
var r = new {
    Membros = bt.GetProperty("MembersCreated", flags).GetValue(builder),
    Paineis = bt.GetProperty("PanelsCreated", flags).GetValue(builder),
    ExtremidadesMovidas = bt.GetProperty("EndsMoved", flags).GetValue(builder),
    ExtremidadesLivres = bt.GetProperty("FreeEnds", flags).GetValue(builder),
    JaAnaliticos = bt.GetProperty("AlreadyAnalytical", flags).GetValue(builder),
    Pulados = ((List<long>)bt.GetProperty("Skipped", flags).GetValue(builder)).Count,
    SemAlvo = bt.GetProperty("RejectedNoTarget", flags).GetValue(builder),
    Colapso = bt.GetProperty("RejectedCollapse", flags).GetValue(builder),
    Segundos = Math.Round(sw.Elapsed.TotalSeconds, 1)
};
alc.Unload();
return Newtonsoft.Json.JsonConvert.SerializeObject(r);
