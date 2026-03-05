using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;

namespace Glow.Training;

public sealed class StockfishClient : IDisposable
{
	readonly Process process;
	readonly StreamWriter input;
	readonly StreamReader output;

	public StockfishClient(string stockfishPath)
	{
		process = new Process();
		process.StartInfo.FileName = stockfishPath;
		process.StartInfo.RedirectStandardInput = true;
		process.StartInfo.RedirectStandardOutput = true;
		process.StartInfo.UseShellExecute = false;
		process.StartInfo.CreateNoWindow = true;
		process.Start();

		input = process.StandardInput;
		output = process.StandardOutput;

		Send("uci");
		ReadUntil("uciok");
		Send("isready");
		ReadUntil("readyok");
	}

	public int EvaluateCp(string fen, int depth)
	{
		Send($"position fen {fen}");
		Send($"go depth {depth}");
		int score = 0;
		while (true)
		{
			string? line = output.ReadLine();
			if (line == null)
			{
				break;
			}

			if (line.StartsWith("info") && line.Contains(" score "))
			{
				int parsed = TryParseScore(line);
				if (parsed != int.MinValue)
				{
					score = parsed;
				}
			}

			if (line.StartsWith("bestmove"))
			{
				break;
			}
		}
		return score;
	}

	void Send(string cmd)
	{
		input.WriteLine(cmd);
		input.Flush();
	}

	void ReadUntil(string expected)
	{
		while (true)
		{
			string? line = output.ReadLine();
			if (line == null || line.StartsWith(expected))
			{
				return;
			}
		}
	}

	static int TryParseScore(string line)
	{
		string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
		for (int i = 0; i < parts.Length - 2; i++)
		{
			if (parts[i] == "score")
			{
				if (parts[i + 1] == "cp" && int.TryParse(parts[i + 2], NumberStyles.Integer, CultureInfo.InvariantCulture, out int cp))
				{
					return cp;
				}
				if (parts[i + 1] == "mate" && int.TryParse(parts[i + 2], NumberStyles.Integer, CultureInfo.InvariantCulture, out int mate))
				{
					return Math.Sign(mate) * 100000;
				}
			}
		}
		return int.MinValue;
	}

	public void Dispose()
	{
		try
		{
			Send("quit");
		}
		catch {}
		process.Dispose();
	}
}
