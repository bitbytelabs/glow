#!/usr/bin/env python3
"""Run a lightweight puzzle warmup so the bot does useful work before queueing games."""

from __future__ import annotations

import os
import random
import subprocess
import sys
import time
from pathlib import Path


PUZZLE_FENS = [
    ("r1bq1rk1/pppp1ppp/2n5/4P3/2B1n3/5N2/PPPP1PPP/RNBQ1RK1 w - - 0 1", "Bxf7+"),
    ("2r2rk1/pp3ppp/2n1pn2/2bp4/8/2NP1NP1/PP3PBP/R1B2RK1 w - - 0 1", "Bxh6"),
    ("r2q1rk1/pp1bbppp/2n1pn2/2pp4/3P4/2P1PN2/PPBN1PPP/R2Q1RK1 w - - 0 1", "dxc5"),
    ("r4rk1/pp2qppp/2n1b3/3pP3/3P4/2N1BN2/PP3PPP/R2QR1K1 w - - 0 1", "Bg5"),
    ("r1bqk2r/pppp1ppp/2n5/4N3/2B1n3/8/PPPP1PPP/RNBQ1RK1 w kq - 0 1", "Bxf7+"),
    ("2r3k1/5ppp/1q6/3Q4/8/5P2/5KPP/8 w - - 0 1", "Qb7"),
    ("4r1k1/1p3pp1/p1p1b2p/3pP3/1P1P4/P1N2N2/5PPP/3R2K1 w - - 0 1", "Ne4"),
]


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
    solved = 0

    print(f"Starting puzzle warmup for {minutes:.1f} minute(s).")
    engine = UciEngine(engine_path)
    try:
        while time.time() < deadline:
            fen, hint = random.choice(PUZZLE_FENS)
            move = engine.bestmove(fen, movetime_ms=1200)
            solved += 1
            print(f"Puzzle {solved:03d}: bestmove={move} (idea: {hint})")
    finally:
        engine.close()

    print(f"Warmup complete. Processed {solved} puzzle positions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
