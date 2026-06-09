#!/usr/bin/env python3
"""
Train the FIFA WC 2026 prediction model.
Run from backend/ directory: python scripts/train_model.py
Uses all 7 datasets. Takes ~2-4 minutes on first run.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.model import train_model, CURRENT_ELO

if __name__ == "__main__":
    print("=" * 60)
    print("  FIFA WC 2026 — Full Model Training")
    print("  Using all 7 datasets")
    print("=" * 60)

    model, scaler, elo, profiles = train_model()

    print("\nTop 15 teams — Current Elo + Key Stats:")
    print("-" * 70)
    sorted_teams = sorted(
        [(t, e) for t, e in CURRENT_ELO.items()
         if not any(x in t for x in ["West Germany", "Soviet", "Yugoslavia",
                                      "Czechoslovakia", "Zaire", "Republic of Ireland",
                                      "Northern Ireland"])],
        key=lambda x: x[1], reverse=True
    )[:15]

    for i, (team, rating) in enumerate(sorted_teams, 1):
        p = profiles.get(team, {})
        so_wr = p.get("shootout_win_rate", 0.5) * 100
        form  = p.get("form5", 0.5) * 100
        titles = p.get("wc_titles", 0)
        xg    = p.get("avg_xg", 1.2)
        print(f"  {i:2d}. {team:<22} ELO:{rating:4d}  "
              f"WC🏆:{titles}  SO-WR:{so_wr:.0f}%  "
              f"Form:{form:.0f}%  xG:{xg:.2f}")

    print("\n✓ Model ready. Run: uvicorn app.main:app --port 8000")
