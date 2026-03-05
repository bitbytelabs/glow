using Chess.Core;
using System;
using System.Collections.Generic;
using System.IO;

namespace Glow.Training;

public static class StockfishTrainer
{
	public static void Run(string stockfishPath, string fenFilePath, string outputWeightsPath, int depth = 10, int iterations = 20)
	{
		List<string> fens = LoadFens(fenFilePath);
		if (fens.Count == 0)
		{
			throw new InvalidOperationException("No FEN positions were found for training.");
		}

		Board board = Board.CreateBoard();
		EvaluationWeights weights = EvaluationWeights.LoadOrDefault(outputWeightsPath);
		Evaluation evaluator = new(weights);

		using StockfishClient stockfish = new(stockfishPath);
		Dictionary<string, int> targets = new();
		foreach (string fen in fens)
		{
			targets[fen] = stockfish.EvaluateCp(fen, depth);
		}

		double step = 0.25;
		double bestError = ComputeError(fens, targets, board, evaluator);

		for (int i = 0; i < iterations; i++)
		{
			bool improved = false;
			improved |= TryImprove(weights, step, w => w.MaterialScale, (w, v) => w.MaterialScale = v, fens, targets, board, ref evaluator, ref bestError);
			improved |= TryImprove(weights, step, w => w.PieceSquareScale, (w, v) => w.PieceSquareScale = v, fens, targets, board, ref evaluator, ref bestError);
			improved |= TryImprove(weights, step, w => w.PawnStructureScale, (w, v) => w.PawnStructureScale = v, fens, targets, board, ref evaluator, ref bestError);
			improved |= TryImprove(weights, step, w => w.KingSafetyScale, (w, v) => w.KingSafetyScale = v, fens, targets, board, ref evaluator, ref bestError);
			improved |= TryImprove(weights, step, w => w.MopUpScale, (w, v) => w.MopUpScale = v, fens, targets, board, ref evaluator, ref bestError);

			if (!improved)
			{
				step *= 0.5;
				if (step < 0.01)
				{
					break;
				}
			}
		}

		weights.Save(outputWeightsPath);
		Console.WriteLine($"Training finished. MSE={bestError:F2}");
		Console.WriteLine($"Saved tuned weights to: {outputWeightsPath}");
	}

	static bool TryImprove(
		EvaluationWeights weights,
		double step,
		Func<EvaluationWeights, double> get,
		Action<EvaluationWeights, double> set,
		List<string> fens,
		Dictionary<string, int> targets,
		Board board,
		ref Evaluation evaluator,
		ref double bestError)
	{
		double current = get(weights);
		double[] candidates = { Math.Max(0.1, current - step), current + step };
		foreach (double candidate in candidates)
		{
			set(weights, candidate);
			evaluator = new Evaluation(weights);
			double error = ComputeError(fens, targets, board, evaluator);
			if (error < bestError)
			{
				bestError = error;
				return true;
			}
		}

		set(weights, current);
		evaluator = new Evaluation(weights);
		return false;
	}

	static double ComputeError(List<string> fens, Dictionary<string, int> targets, Board board, Evaluation evaluator)
	{
		double squaredError = 0;
		foreach (string fen in fens)
		{
			board.LoadPosition(fen);
			int predicted = evaluator.Evaluate(board);
			int target = targets[fen];
			double delta = predicted - target;
			squaredError += delta * delta;
		}
		return squaredError / fens.Count;
	}

	static List<string> LoadFens(string fenFilePath)
	{
		List<string> fens = new();
		foreach (string line in File.ReadAllLines(fenFilePath))
		{
			string trimmed = line.Trim();
			if (!string.IsNullOrWhiteSpace(trimmed) && !trimmed.StartsWith('#'))
			{
				fens.Add(trimmed);
			}
		}
		return fens;
	}
}
