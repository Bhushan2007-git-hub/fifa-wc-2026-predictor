#!/usr/bin/env python3
"""
Quick CLI simulation of the 2026 World Cup.
Run from backend/ directory:
    python scripts/simulate_tournament.py [--sims 1000]
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.ml.model import load_or_train
from app.ml.simulator import run_full_tournament
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=1000)
    args = parser.parse_args()

    print(f"Loading model and running {args.sims} simulations...")
    model, scaler, elo = load_or_train()
    rankings_df = pd.read_csv(DATA_DIR / "fifa_ranking_2022-10-06.csv")

    results = run_full_tournament(model, scaler, elo, rankings_df, n_simulations=args.sims)

    print("\n" + "=" * 50)
    print("  FIFA WORLD CUP 2026 — PREDICTED CHAMPION %")
    print("=" * 50)
    for item in results["top_champions"]:
        bar = "█" * int(item["probability"] / 2)
        print(f"  {item['team']:<20} {bar:<25} {item['probability']:5.1f}%")

    print("\n" + "=" * 50)
    print("  TOP FINALISTS")
    print("=" * 50)
    for item in results["top_finalists"][:8]:
        print(f"  {item['team']:<20} {item['probability']:5.1f}%")

    print(f"\nSimulations run: {results['simulations_run']}")


if __name__ == "__main__":
    main()
