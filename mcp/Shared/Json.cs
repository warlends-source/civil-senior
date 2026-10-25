using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace CivilSenior.Mcp;

/// <summary>
/// Tool results are JSON text: compact, with rounded doubles and NaN/Infinity written as null.
/// </summary>
public static class Json
{
    private static readonly JsonSerializerOptions Options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        Converters = { new RoundedDouble() }
    };

    public static string Of(object value) => JsonSerializer.Serialize(value, Options);

    public static string Error(string message) => Of(new { error = message });

    private sealed class RoundedDouble : JsonConverter<double>
    {
        public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => reader.GetDouble();

        public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options)
        {
            if (double.IsNaN(value) || double.IsInfinity(value)) writer.WriteNullValue();
            else writer.WriteNumberValue(Math.Round(value, 6));
        }
    }

    /// <summary>
    /// Parses "[[x,y,z],...]" or "[[x,y],...]" (z = 0) into points.
    /// </summary>
    public static List<double[]> Points(string json)
    {
        var raw = JsonSerializer.Deserialize<double[][]>(json) ?? throw new ArgumentException("points must be a JSON array of [x,y] or [x,y,z]");
        var points = new List<double[]>();
        foreach (double[] p in raw)
        {
            if (p.Length < 2) throw new ArgumentException("each point needs at least x and y");
            points.Add(new[] { p[0], p[1], p.Length > 2 ? p[2] : 0 });
        }
        return points;
    }

    public static List<T> List<T>(string json) => JsonSerializer.Deserialize<List<T>>(json) ?? new List<T>();
}
