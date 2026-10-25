// Orientation check: Robot local z of every bar vs the section height direction exported from Revit.
using CivilConnection.Robot;
using RobotOM;
using System.Globalization;
static class G
{
    [STAThread]
    static void Main(string[] args)
    {
        var inv = CultureInfo.InvariantCulture;
        var members = File.ReadAllLines(args[0]).Skip(1).Select(l => l.Split(';')).Select(p => (Type: p[0],
            A: new[] { double.Parse(p[1], inv), double.Parse(p[2], inv), double.Parse(p[3], inv) },
            B: new[] { double.Parse(p[4], inv), double.Parse(p[5], inv), double.Parse(p[6], inv) },
            U: new[] { double.Parse(p[7], inv), double.Parse(p[8], inv), double.Parse(p[9], inv) })).ToList();

        var link = RobotLink.Connect(false, IRobotProjectType.I_PT_SHELL);
        var st = link.Structure;
        var xyz = new Dictionary<int, double[]>();
        var nodes = st.Nodes.GetAll();
        for (int i = 1; i <= nodes.Count; i++) { var n = (IRobotNode)nodes.Get(i); xyz[n.Number] = new[] { n.X, n.Y, n.Z }; }

        double Dist(double[] p, double[] a, double[] b)
        {
            double[] ab = { b[0] - a[0], b[1] - a[1], b[2] - a[2] };
            double t = Math.Clamp(((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1] + (p[2] - a[2]) * ab[2]) / (ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]), 0, 1);
            double dx = a[0] + t * ab[0] - p[0], dy = a[1] + t * ab[1] - p[1], dz = a[2] + t * ab[2] - p[2];
            return Math.Sqrt(dx * dx + dy * dy + dz * dz);
        }

        var dev = new Dictionary<string, List<double>>();
        int unmatched = 0, released = 0;
        var bars = st.Bars.GetAll();
        for (int i = 1; i <= bars.Count; i++)
        {
            var b = (IRobotBar)bars.Get(i);
            if (b.HasLabel(IRobotLabelType.I_LT_BAR_RELEASE) != 0) released++;
            double[] p0 = xyz[b.StartNode], p1 = xyz[b.EndNode];
            double[] mid = { (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2 };
            var m = members.Where(mm => Dist(p0, mm.A, mm.B) < 0.002 && Dist(p1, mm.A, mm.B) < 0.002 && Dist(mid, mm.A, mm.B) < 0.002).ToList();
            if (m.Count != 1) { unmatched++; continue; }
            var z = link.BarLocalZ(b.Number);
            var u = m[0].U;
            double ang = Math.Acos(Math.Clamp(z[0] * u[0] + z[1] * u[1] + z[2] * u[2], -1, 1)) * 180 / Math.PI;
            if (!dev.ContainsKey(m[0].Type)) dev[m[0].Type] = new List<double>();
            dev[m[0].Type].Add(ang);
        }
        Console.WriteLine($"Barras: {bars.Count}; sem membro unico correspondente: {unmatched}; com liberacao: {released}");
        foreach (var d in dev.OrderBy(k => k.Key)) Console.WriteLine($"  {d.Key,-22} n={d.Value.Count,5}  desvio max = {d.Value.Max(),8:F3} graus");
        link.EndSession();
    }
}
