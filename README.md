# Glow
Version 2.0 of the Coding Adventure Bot. Good at beating up humans (~2600 on [lichess](https://lichess.org/@/CodingAdventureBot/playing)), but still has a very long way to go against its fellow machines (Stockfish crushes it even with rook-odds!)

You can find some videos about the bot's creation process here: [V1](https://www.youtube.com/watch?v=U4ogK0MIzqk) and [V2](https://youtu.be/_vqlIPDR2TU)

Note: this is the UCI version of the program, which does not have a graphical interface. The UCI implementation is also very barebones -- I just did the minimum to get it up and running on lichess.

## Training against Stockfish

Glow can now tune its evaluation component weights directly from Stockfish scores.

```bash
dotnet run --project Glow -- train /path/to/stockfish positions.fen Glow/resources/eval-weights.json 10 30
```

- `positions.fen`: one FEN per line (lines starting with `#` are ignored).
- `depth` (optional): Stockfish analysis depth (default `10`).
- `iterations` (optional): tuning passes over weights (default `20`).

After training, Glow will automatically load `Glow/resources/eval-weights.json` if it exists.
