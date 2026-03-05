using System;
using System.IO;
using System.Text.Json;

namespace Chess.Core;

public class EvaluationWeights
{
	public double MaterialScale { get; set; } = 1.0;
	public double PieceSquareScale { get; set; } = 1.0;
	public double PawnStructureScale { get; set; } = 1.0;
	public double KingSafetyScale { get; set; } = 1.0;
	public double MopUpScale { get; set; } = 1.0;

	public static EvaluationWeights Default() => new();

	public static EvaluationWeights LoadOrDefault(string path)
	{
		if (!File.Exists(path))
		{
			return Default();
		}

		string json = File.ReadAllText(path);
		EvaluationWeights? loaded = JsonSerializer.Deserialize<EvaluationWeights>(json);
		return loaded ?? Default();
	}

	public void Save(string path)
	{
		string? directory = Path.GetDirectoryName(path);
		if (!string.IsNullOrWhiteSpace(directory))
		{
			Directory.CreateDirectory(directory);
		}

		string json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
		File.WriteAllText(path, json);
	}
}
