var alc = new System.Runtime.Loader.AssemblyLoadContext("probe_" + Guid.NewGuid().ToString("N"), true);
var asm = alc.LoadFromAssemblyPath((string)parameters[0]);
var lines = new List<string> { "carregado: " + System.Runtime.Loader.AssemblyLoadContext.GetLoadContext(asm).Name + " | " + asm.ManifestModule.ModuleVersionId + " | " + asm.Location };
foreach (var a in AppDomain.CurrentDomain.GetAssemblies().Where(a => a.GetName().Name == "Autodesk2027"))
    lines.Add("no processo: " + System.Runtime.Loader.AssemblyLoadContext.GetLoadContext(a).Name + " | " + a.ManifestModule.ModuleVersionId + " | " + (a.IsDynamic ? "" : a.Location));
alc.Unload();
return string.Join(Environment.NewLine, lines);
