#!/usr/bin/env python3
"""Run an idle warmup by solving real Lichess puzzles with Glow before queueing games."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

try:
    import chess
    import chess.pgn
except ModuleNotFoundError:
    print("python-chess is required for Lichess puzzle warmup; skipping.")
    sys.exit(0)


class UciEngine:
    def __init__(self, path: Path):
        self.proc = subprocess.Popen(
            [str(path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._send("uci")
        self._wait_for("uciok")
        self._send("isready")
        self._wait_for("readyok")
        self._send("ucinewgame")

    def _send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def _wait_for(self, token: str) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            if token in line:
                return
        raise RuntimeError(f"Engine closed before sending {token}.")

    def bestmove(self, fen: str, movetime_ms: int) -> str:
        self._send(f"position fen {fen}")
        self._send(f"go movetime {movetime_ms}")
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            if line.startswith("bestmove "):
                return line.split()[1]
        raise RuntimeError("Engine closed before returning bestmove.")

    def close(self) -> None:
        if self.proc.poll() is None:
            self._send("quit")
            self.proc.wait(timeout=5)


def fetch_next_puzzle(token: str | None) -> dict:
    request = Request("https://lichess.org/api/puzzle/next")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def puzzle_board_from_pgn(pgn_text: str, initial_ply: int) -> chess.Board:
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise ValueError("Invalid PGN returned by Lichess puzzle API.")

    board = game.board()
    for ply_index, move in enumerate(game.mainline_moves()):
        if ply_index >= initial_ply:
            break
        board.push(move)
    return board


def run_single_puzzle(engine: UciEngine, movetime_ms: int, token: str | None) -> tuple[bool, str]:
    payload = fetch_next_puzzle(token)
    puzzle = payload["puzzle"]
    board = puzzle_board_from_pgn(payload["game"]["pgn"], puzzle["initialPly"])
    solution = puzzle["solution"]

    matched = 0
    for expected in solution:
        predicted = engine.bestmove(board.fen(), movetime_ms=movetime_ms)
        if predicted != expected:
            return False, f"{puzzle['id']} miss at ply {matched + 1}: expected {expected}, got {predicted}"

        board.push(chess.Move.from_uci(expected))
        matched += 1

    return True, f"{puzzle['id']} solved ({matched}/{len(solution)} moves)"


def main() -> int:
    minutes = float(os.environ.get("PUZZLE_WARMUP_MINUTES", "3"))
    if minutes <= 0:
        print("Puzzle warmup disabled (PUZZLE_WARMUP_MINUTES <= 0).")
        return 0

    engine_path = Path("dist/glow/Glow")
    if not engine_path.exists():
        print(f"Engine not found at {engine_path}; skipping warmup.")
        return 0

    deadline = time.time() + (minutes * 60)
    movetime_ms = int(os.environ.get("PUZZLE_WARMUP_MOVE_MS", "900"))
    token = os.environ.get("LICHESS_BOT_TOKEN")

    print(f"Starting Lichess puzzle warmup for {minutes:.1f} minute(s).")
    engine = UciEngine(engine_path)
    solved = 0
    attempted = 0

    try:
        while time.time() < deadline:
            attempted += 1
            try:
                ok, message = run_single_puzzle(engine, movetime_ms, token)
            except Exception as exc:
                print(f"Puzzle {attempted:03d}: failed to fetch/solve puzzle ({exc}); retrying.")
                time.sleep(1)
                continue

            if ok:
                solved += 1
            print(f"Puzzle {attempted:03d}: {message}")
    finally:
        engine.close()

    print(f"Warmup complete. Solved {solved}/{attempted} Lichess puzzles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
