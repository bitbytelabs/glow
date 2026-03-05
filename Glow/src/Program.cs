namespace Glow;
using Glow.Training;
using System;

public static class Program
{
    public static void Main(string[] args)
    {
        if (args.Length > 0 && args[0].Equals("train", StringComparison.OrdinalIgnoreCase))
        {
            RunTraining(args);
            return;
        }

        EngineUCI engine = new();

        string command = String.Empty;
        while (command != "quit")
        {
            command = Console.ReadLine() ?? string.Empty;
            engine.ReceiveCommand(command);
        }
    }

    static void RunTraining(string[] args)
    {
        if (args.Length < 4)
        {
            Console.WriteLine("Usage: glow train <stockfish-path> <fen-file> <weights-output> [depth] [iterations]");
            return;
        }

        int depth = args.Length >= 5 && int.TryParse(args[4], out int parsedDepth) ? parsedDepth : 10;
        int iterations = args.Length >= 6 && int.TryParse(args[5], out int parsedIterations) ? parsedIterations : 20;

        StockfishTrainer.Run(args[1], args[2], args[3], depth, iterations);
    }
}
