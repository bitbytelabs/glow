# Glow
Version 2.0 of Glow. Good at beating up humans (~2600 on [lichess](https://lichess.org/@/Glow/playing)), but still has a very long way to go against its fellow machines (Stockfish crushes it even with rook-odds!)

You can find some videos about the bot's creation process here: [V1](https://www.youtube.com/watch?v=U4ogK0MIzqk) and [V2](https://youtu.be/_vqlIPDR2TU)

Note: this is the UCI version of the program, which does not have a graphical interface. The UCI implementation is also very barebones -- I just did the minimum to get it up and running on lichess.

## Run as a Lichess bot with GitHub Actions

This repository includes `.github/workflows/lichess-bot.yml`, which:

1. Builds Glow in release mode.
2. Clones the community `lichess-bot` runner.
3. Generates a `lichess-bot` config with your token and built engine path.
4. Connects to lichess and starts accepting/playing games.

### Setup

1. Create/upgrade your Lichess account to a bot account.
2. Create a Lichess API token with the bot scopes required by `lichess-bot`.
3. Add the token to your repo secrets as `LICHESS_BOT_TOKEN`.
4. Run the **Lichess Bot** workflow manually, or let the schedule run every 30 minutes.

### Optional idle puzzle warmup

The workflow now supports a `puzzle_warmup_minutes` input (default: `3`). Before connecting to lichess, it runs `.github/scripts/idle_puzzle_warmup.py`, which pulls real puzzles from the Lichess puzzle API and has Glow attempt the solution line as a short idle warmup. Set `puzzle_warmup_minutes` to `0` to disable it.

You can customize game filters and behavior in `.github/lichess/config.template.yml`.
You can also customize chat text used by the GitHub Action generator in `.github/workflows/lichess-bot.yml` (it builds large message pools and picks random greetings/goodbyes/spectator messages each run).
