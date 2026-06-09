"""FastAPI routes — FIFA WC 2026 Predictor"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

from ..ml.model import load_or_train, predict_match, CURRENT_ELO
from ..ml.simulator import run_full_tournament, GROUPS_2026

DATA_DIR = Path(__file__).parent.parent.parent / "data"
router   = APIRouter()

_model    = None
_scaler   = None
_elo      = None
_profiles = None
_rankings = None

def get_state():
    global _model, _scaler, _elo, _profiles, _rankings
    if _model is None:
        _model, _scaler, _elo, _profiles = load_or_train()
        _rankings = pd.read_csv(DATA_DIR / "fifa_ranking_2026.csv")
    return _model, _scaler, _elo, _profiles, _rankings


def _i(v, default=0):
    """Convert any numeric type to plain Python int."""
    try: return int(v) if v is not None else default
    except: return default

def _f(v, default=0.0):
    """Convert any numeric type to plain Python float, rounded."""
    try: return round(float(v), 2) if v is not None else default
    except: return default


class MatchRequest(BaseModel):
    home_team: str
    away_team: str
    is_knockout: bool = False

class TournamentRequest(BaseModel):
    simulations: int = 1000


@router.get("/health")
def health(): return {"status": "ok"}


@router.post("/predict/match")
def predict_single(req: MatchRequest):
    model, scaler, elo, profiles, rankings = get_state()
    all_teams = list(CURRENT_ELO.keys())
    home = _fuzzy(req.home_team, all_teams)
    away = _fuzzy(req.away_team, all_teams)
    if not home: raise HTTPException(404, f"Team not found: {req.home_team}")
    if not away: raise HTTPException(404, f"Team not found: {req.away_team}")
    if home == away: raise HTTPException(400, "Teams must be different")
    return predict_match(home, away, model, scaler, elo, rankings, req.is_knockout, profiles)


@router.post("/simulate/tournament")
def simulate(req: TournamentRequest):
    model, scaler, elo, profiles, rankings = get_state()
    sims = max(100, min(req.simulations, 5000))
    return run_full_tournament(model, scaler, elo, rankings, profiles, n_simulations=sims)


@router.get("/simulate/tournament/cached")
def cached_sim():
    raise HTTPException(404, "Run POST /simulate/tournament first")


@router.get("/teams")
def list_teams():
    _, _, elo, profiles, rankings = get_state()
    ranking_map = dict(zip(rankings["team"], rankings["rank"]))
    points_map  = dict(zip(rankings["team"], rankings["points"]))
    assoc_map   = dict(zip(rankings["team"], rankings["association"]))
    teams = []
    for team, er in CURRENT_ELO.items():
        if any(x in team for x in ["West Germany","Soviet","Yugoslavia","Czechoslovakia","Zaire"]): continue
        p = profiles.get(team, {})
        teams.append({
            "team": team,
            "elo_rating": _f(er),
            "fifa_rank": _i(ranking_map.get(team)) or None,
            "fifa_points": _f(points_map.get(team)) or None,
            "association": assoc_map.get(team),
            "wc_titles": _i(p.get("wc_titles", 0)),
            "shootout_win_rate": _f(p.get("shootout_win_rate", 0.5) * 100),
        })
    return sorted(teams, key=lambda x: x["elo_rating"], reverse=True)


@router.get("/teams/{team_name}/stats")
def team_stats(team_name: str):
    _, _, elo, profiles, rankings = get_state()
    all_teams = list(CURRENT_ELO.keys())
    matched = _fuzzy(team_name, all_teams)
    if not matched: raise HTTPException(404, f"Team not found: {team_name}")
    p = profiles.get(matched, {})
    ranking_map = dict(zip(rankings["team"], rankings["rank"]))
    points_map  = dict(zip(rankings["team"], rankings["points"]))
    return {
        "team": matched,
        "elo_rating": _f(CURRENT_ELO.get(matched, elo.get(matched, 1500))),
        "fifa_rank": _i(ranking_map.get(matched)) or None,
        "fifa_points": _f(points_map.get(matched)) or None,
        "total_wc_matches": _i(p.get("total", 0)),
        "wins": _i(p.get("wins", 0)),
        "draws": _i(p.get("draws", 0)),
        "losses": _i(p.get("losses", 0)),
        "win_rate": _f(p.get("win_rate", 0) * 100),
        "goals_for": _i(p.get("gf", 0)),
        "goals_against": _i(p.get("ga", 0)),
        "goal_difference": _i(p.get("gf", 0)) - _i(p.get("ga", 0)),
        "avg_goals_for": _f(p.get("avg_gf", 0)),
        "avg_goals_against": _f(p.get("avg_ga", 0)),
        "form_last5": _f(p.get("form5", 0.5) * 100),
        "form_last10": _f(p.get("form10", 0.5) * 100),
        "wc_titles": _i(p.get("wc_titles", 0)),
        "wc_finals": _i(p.get("wc_finals", 0)),
        "shootout_played": _i(p.get("shootout_played", 0)),
        "shootout_wins": _i(p.get("shootout_wins", 0)),
        "shootout_win_rate": _f(p.get("shootout_win_rate", 0.5) * 100),
        "penalty_conversion": _f(p.get("penalty_conversion", 0.75) * 100),
        "recent_results": [str(r) for r in p.get("recent", [])],
    }


@router.get("/groups")
def get_groups(): return {"groups": GROUPS_2026}


@router.get("/predict/group/{group_name}")
def predict_group(group_name: str):
    gn = group_name.upper()
    if gn not in GROUPS_2026: raise HTTPException(404, f"Group {gn} not found")
    model, scaler, elo, profiles, rankings = get_state()
    teams = GROUPS_2026[gn]
    matches = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append(predict_match(teams[i], teams[j], model, scaler, elo, rankings, False, profiles))
    return {"group": gn, "teams": teams, "matches": matches}


def _fuzzy(name, candidates):
    nl = name.lower().strip()
    for c in candidates:
        if c.lower() == nl: return c
    for c in candidates:
        if nl in c.lower() or c.lower() in nl: return c
    return None
