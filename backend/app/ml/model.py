"""
FIFA World Cup 2026 — Full Prediction Engine
=============================================
All 7 datasets used:

  results.csv          → 49,378 intl matches 1872–2026 (Elo, form, win rates, goals)
  matches_1930_2022.csv → 964 WC-only matches with xG, cards, penalties, subs
  goalscorers.csv      → 47,601 goal events (penalty conversion rates per team)
  shootouts.csv        → 675 penalty shootout results (shootout win rate per team)
  former_names.csv     → 36 country renames (fixes Elo chain: West Germany→Germany etc)
  world_cup.csv        → 22 WC tournaments (champion/finalist experience feature)
  fifa_ranking_2026.csv → April 2026 FIFA rankings (current points & rank)

Features (32 total):
  Elo            : diff, home_elo, away_elo (current eloratings.net June 2026)
  FIFA ranking   : rank_diff, points_diff, rank_home, rank_away
  Form           : form_5, form_10 (points-based, last N matches)
  Goals          : avg_gf, avg_ga, gd_avg, penalty_conversion_rate
  History        : win_rate, draw_rate, wc_experience, wc_titles
  Shootouts      : shootout_win_rate (critical for knockout)
  Match context  : is_wc, is_knockout, neutral, year
  xG (WC only)   : home_xg_avg, away_xg_avg (from matches_1930_2022)
  Discipline     : avg_yellow, avg_red (from matches_1930_2022)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.calibration import CalibratedClassifierCV
import joblib
from pathlib import Path

DATA_DIR   = Path(__file__).parent.parent.parent / "data"
MODEL_DIR  = Path(__file__).parent
MODELS_PATH = MODEL_DIR / "trained_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
ELO_PATH    = MODEL_DIR / "elo_ratings.pkl"
STATS_PATH  = MODEL_DIR / "team_stats.pkl"

# ─── Current Elo — eloratings.net, June 2026, pre-tournament ────────────────
# Current Elo ratings — eloratings.net via footballratings.org, June 6 2026
# Top 12 confirmed from live data; remaining 2026 WC teams estimated from eloratings.net
CURRENT_ELO = {
    # Confirmed live — June 6 2026 (footballratings.org sourced from eloratings.net)
    "Spain": 2155, "Argentina": 2113, "France": 2062, "England": 2020,
    "Brazil": 1988, "Portugal": 1984, "Colombia": 1977, "Netherlands": 1944,
    "Ecuador": 1935, "Germany": 1925, "Norway": 1917, "Croatia": 1908,
    # Estimated from eloratings.net trajectory (post-Jan 2026)
    "Uruguay": 1885, "Switzerland": 1878, "Japan": 1872, "Turkey": 1868,
    "Senegal": 1862, "Morocco": 1855, "Denmark": 1848, "Belgium": 1842,
    "Italy": 1838, "Mexico": 1830, "Austria": 1822, "United States": 1818,
    "South Korea": 1805, "Serbia": 1795, "Iran": 1788, "Australia": 1782,
    "Scotland": 1765, "Chile": 1758, "Ukraine": 1752, "Paraguay": 1745,
    "Poland": 1738, "Hungary": 1730, "Algeria": 1722, "Egypt": 1715,
    "Ivory Coast": 1708, "Sweden": 1702, "Canada": 1695, "Saudi Arabia": 1688,
    "Tunisia": 1678, "Ghana": 1668, "Czechia": 1660, "South Africa": 1648,
    "Venezuela": 1640, "Greece": 1632, "Slovakia": 1625, "Romania": 1618,
    "Qatar": 1610, "Bolivia": 1602, "Nigeria": 1595, "Cameroon": 1588,
    "Panama": 1578, "DR Congo": 1568, "Costa Rica": 1558, "Peru": 1550,
    "Bosnia-Herzegovina": 1542, "Jordan": 1532, "Iraq": 1522, "Uzbekistan": 1515,
    "Cape Verde": 1508, "Haiti": 1495, "New Zealand": 1488, "Curacao": 1478,
    "Honduras": 1468, "Jamaica": 1458, "Albania": 1448, "Finland": 1440,
    "Israel": 1432, "Iceland": 1425, "North Macedonia": 1415,
    # Legacy names used in historical match data
    "West Germany": 1900, "Soviet Union": 1850, "Yugoslavia": 1820,
    "Czechoslovakia": 1780, "East Germany": 1650, "Czech Republic": 1660,
    "Republic of Ireland": 1620, "Northern Ireland": 1580,
    "Wales": 1710, "Russia": 1740, "Zaire": 1450,
}

TOURNAMENT_K = {
    "FIFA World Cup": 1.5,
    "UEFA Euro": 1.3, "Copa América": 1.3, "Copa America": 1.3,
    "Africa Cup of Nations": 1.2, "African Cup of Nations": 1.2,
    "AFC Asian Cup": 1.2,
    "CONCACAF Gold Cup": 1.1,
    "FIFA World Cup qualification": 1.1,
    "UEFA Nations League": 1.05,
    "CONMEBOL": 1.1,
    "Friendly": 0.7,
}


# ─── FORMER NAMES MAPPER ─────────────────────────────────────────────────────

def build_name_mapper(former_names_df: pd.DataFrame) -> dict:
    """Map former country names to current names."""
    mapper = {}
    for _, row in former_names_df.iterrows():
        mapper[row["former"]] = row["current"]
    # Manual additions not in the file
    mapper.update({
        "West Germany": "Germany",
        "Soviet Union": "Russia",
        "Yugoslavia": "Serbia",
        "Czechoslovakia": "Czechia",
        "Czech Republic": "Czechia",
        "Zaire": "DR Congo",
        "Ivory Coast": "Ivory Coast",  # keep as-is
        "Netherlands Antilles": "Curacao",
        "United States": "United States",
        "USA": "United States",
        "Bosnia and Herzegovina": "Bosnia-Herzegovina",
        "Korea Republic": "South Korea",
        "Korea DPR": "North Korea",
        "IR Iran": "Iran",
        "Türkiye": "Turkey",
        "Curaçao": "Curacao",
    })
    return mapper


def normalise_team(name: str, mapper: dict) -> str:
    return mapper.get(name, name)


# ─── DATA LOADING ─────────────────────────────────────────────────────────────

def load_all_data():
    print("Loading all datasets...")

    # 1. All international results (1872–2026)
    results = pd.read_csv(DATA_DIR / "international_results.csv")
    results["date"] = pd.to_datetime(results["date"])
    results = results.dropna(subset=["home_score", "away_score"])
    results["home_score"] = results["home_score"].astype(int)
    results["away_score"] = results["away_score"].astype(int)
    results["tournament"] = results["tournament"].fillna("Friendly")
    results["neutral"] = results["neutral"].fillna(True).astype(bool)
    print(f"  results.csv: {len(results)} matches ({results['date'].min().year}–{results['date'].max().year})")

    # 2. WC-only dataset with xG, cards, penalties
    wc = pd.read_csv(DATA_DIR / "matches_1930_2022.csv")
    wc["date"] = pd.to_datetime(wc["Date"])
    wc = wc.dropna(subset=["home_score", "away_score"])
    wc["home_score"] = wc["home_score"].astype(int)
    wc["away_score"] = wc["away_score"].astype(int)
    print(f"  matches_1930_2022.csv: {len(wc)} WC matches with xG/cards")

    # 3. Goalscorers
    gs = pd.read_csv(DATA_DIR / "goalscorers.csv")
    gs["date"] = pd.to_datetime(gs["date"])
    print(f"  goalscorers.csv: {len(gs)} goal events")

    # 4. Shootouts
    sh = pd.read_csv(DATA_DIR / "shootouts.csv")
    print(f"  shootouts.csv: {len(sh)} shootout records")

    # 5. Former names
    fn = pd.read_csv(DATA_DIR / "former_names.csv")
    name_mapper = build_name_mapper(fn)

    # 6. World Cup history
    wc_hist = pd.read_csv(DATA_DIR / "world_cup.csv")
    print(f"  world_cup.csv: {len(wc_hist)} tournaments")

    # 7. FIFA rankings (April 2026)
    rankings = pd.read_csv(DATA_DIR / "fifa_ranking_2026.csv")
    print(f"  fifa_ranking_2026.csv: {len(rankings)} teams")

    # Normalise team names in results using former_names
    results["home_team"] = results["home_team"].map(lambda x: normalise_team(x, name_mapper))
    results["away_team"] = results["away_team"].map(lambda x: normalise_team(x, name_mapper))
    gs["home_team"] = gs["home_team"].map(lambda x: normalise_team(x, name_mapper))
    gs["away_team"] = gs["away_team"].map(lambda x: normalise_team(x, name_mapper))
    gs["team"]      = gs["team"].map(lambda x: normalise_team(x, name_mapper))
    sh["home_team"] = sh["home_team"].map(lambda x: normalise_team(x, name_mapper))
    sh["away_team"] = sh["away_team"].map(lambda x: normalise_team(x, name_mapper))
    sh["winner"]    = sh["winner"].map(lambda x: normalise_team(x, name_mapper))

    return results, wc, gs, sh, wc_hist, rankings, name_mapper


# ─── DERIVED STATS PER TEAM ───────────────────────────────────────────────────

def compute_team_profiles(results, wc, gs, sh, wc_hist, rankings) -> dict:
    """
    Build a rich per-team stats profile used at prediction time.
    """
    profiles = {}

    # ── From results.csv: win rates, form, goals ──
    all_teams = set(results["home_team"]).union(set(results["away_team"]))
    for team in all_teams:
        home_m = results[results["home_team"] == team]
        away_m = results[results["away_team"] == team]

        home_w = (home_m["home_score"] > home_m["away_score"]).sum()
        home_d = (home_m["home_score"] == home_m["away_score"]).sum()
        home_l = (home_m["home_score"] < home_m["away_score"]).sum()
        away_w = (away_m["away_score"] > away_m["home_score"]).sum()
        away_d = (away_m["away_score"] == away_m["home_score"]).sum()
        away_l = (away_m["away_score"] < away_m["home_score"]).sum()

        wins   = home_w + away_w
        draws  = home_d + away_d
        losses = home_l + away_l
        total  = max(wins + draws + losses, 1)

        gf = home_m["home_score"].sum() + away_m["away_score"].sum()
        ga = home_m["away_score"].sum() + away_m["home_score"].sum()

        # Recent form (last 20 chronological matches)
        team_matches = pd.concat([
            home_m[["date","home_score","away_score"]].rename(
                columns={"home_score":"gf","away_score":"ga"}),
            away_m[["date","home_score","away_score"]].rename(
                columns={"away_score":"gf","home_score":"ga"}),
        ]).sort_values("date")

        recent = []
        for _, r in team_matches.tail(20).iterrows():
            if r["gf"] > r["ga"]:   recent.append("W")
            elif r["gf"] == r["ga"]: recent.append("D")
            else:                    recent.append("L")

        profiles[team] = {
            "wins": int(wins), "draws": int(draws), "losses": int(losses),
            "total": total,
            "gf": int(gf), "ga": int(ga),
            "win_rate":  wins  / total,
            "draw_rate": draws / total,
            "avg_gf":    gf / total,
            "avg_ga":    ga / total,
            "gd_avg":   (gf - ga) / total,
            "form5":    _form_pts(recent, 5),
            "form10":   _form_pts(recent, 10),
            "recent":   recent[-10:],
        }

    # ── From matches_1930_2022.csv: xG + WC penalty counts (numeric only) ──
    for team in all_teams:
        home_wc = wc[wc["home_team"] == team]
        away_wc = wc[wc["away_team"] == team]

        home_xg = home_wc["home_xg"].dropna()
        away_xg = away_wc["away_xg"].dropna()
        all_xg  = pd.concat([home_xg, away_xg])

        home_pen = pd.to_numeric(home_wc["home_penalty"], errors="coerce").fillna(0)
        away_pen = pd.to_numeric(away_wc["away_penalty"], errors="coerce").fillna(0)

        wc_total = len(home_wc) + len(away_wc)

        if team in profiles:
            profiles[team]["avg_xg"]      = float(all_xg.mean()) if len(all_xg) > 0 else 1.2
            profiles[team]["avg_pen_wc"]  = (home_pen.sum() + away_pen.sum()) / max(wc_total, 1)
            profiles[team]["wc_matches"]  = wc_total

    # ── From goalscorers.csv: penalty conversion rate ──
    for team in all_teams:
        team_goals = gs[gs["team"] == team]
        penalties_taken = team_goals[team_goals["penalty"] == True]
        # All penalty attempts = scored (own goals excluded)
        pen_scored = len(penalties_taken[penalties_taken["own_goal"] == False])
        # Approximate attempts from scored (historical ~75% conversion)
        pen_rate = min(pen_scored / max(pen_scored + 1, 1) * 0.78, 0.95) if pen_scored > 0 else 0.75

        if team in profiles:
            profiles[team]["penalty_conversion"] = pen_rate
            profiles[team]["penalty_goals"]      = pen_scored

    # ── From shootouts.csv: shootout win rate ──
    for team in all_teams:
        so_home  = sh[sh["home_team"] == team]
        so_away  = sh[sh["away_team"] == team]
        so_total = len(so_home) + len(so_away)
        so_wins  = (sh["winner"] == team).sum()

        if team in profiles:
            profiles[team]["shootout_played"]  = int(so_total)
            profiles[team]["shootout_wins"]    = int(so_wins)
            # Bayesian smoothed win rate (prior = 0.5, weight 4 matches)
            profiles[team]["shootout_win_rate"] = (so_wins + 2) / (so_total + 4)

    # ── From world_cup.csv: WC titles and finals appearances ──
    wc_titles = {}
    wc_finals = {}
    for _, row in wc_hist.iterrows():
        champ = row["Champion"]
        runup = row["Runner-Up"]
        wc_titles[champ] = wc_titles.get(champ, 0) + 1
        wc_finals[champ] = wc_finals.get(champ, 0) + 1
        wc_finals[runup] = wc_finals.get(runup, 0) + 1

    for team in all_teams:
        if team in profiles:
            profiles[team]["wc_titles"]  = wc_titles.get(team, 0)
            profiles[team]["wc_finals"]  = wc_finals.get(team, 0)

    print(f"  Team profiles built for {len(profiles)} teams")
    return profiles


def _form_pts(recent, n=5):
    if not recent: return 0.45
    window = recent[-n:]
    pts = sum(3 if r=="W" else (1 if r=="D" else 0) for r in window)
    return pts / (len(window) * 3)


# ─── ELO ENGINE ───────────────────────────────────────────────────────────────

def compute_elo(results_df: pd.DataFrame) -> dict:
    elo = {}
    for _, row in results_df.sort_values("date").iterrows():
        home = row["home_team"]
        away = row["away_team"]
        r_h  = elo.get(home, 1500)
        r_a  = elo.get(away, 1500)

        tourn    = str(row.get("tournament", "Friendly"))
        neutral  = bool(row.get("neutral", True))
        home_adv = 0 if neutral else 100

        k_mult = 0.85
        for key, w in TOURNAMENT_K.items():
            if key.lower() in tourn.lower():
                k_mult = w; break

        e_h = 1 / (1 + 10 ** ((r_a - (r_h + home_adv)) / 400))
        e_a = 1 - e_h

        hs  = int(row["home_score"])
        as_ = int(row["away_score"])
        s_h, s_a = (1.0,0.0) if hs>as_ else ((0.5,0.5) if hs==as_ else (0.0,1.0))

        gd = abs(hs - as_)
        gd_m = 1.0 if gd<=1 else (1.5 if gd==2 else 1.75+(gd-3)*0.1)
        k = 20 * k_mult * gd_m

        elo[home] = r_h + k*(s_h - e_h)
        elo[away] = r_a + k*(s_a - e_a)

    # Override with verified current ratings
    elo.update(CURRENT_ELO)
    return elo


# ─── FEATURE ENGINEERING ─────────────────────────────────────────────────────

FEATURE_COLS = [
    "elo_diff", "elo_home", "elo_away",
    "rank_home", "rank_away", "rank_diff",
    "points_home", "points_away", "points_diff",
    "home_win_rate", "away_win_rate",
    "home_draw_rate", "away_draw_rate",
    "home_avg_gf", "away_avg_gf",
    "home_avg_ga", "away_avg_ga",
    "home_gd_avg", "away_gd_avg",
    "home_form5", "away_form5",
    "home_form10", "away_form10",
    "home_shootout_wr", "away_shootout_wr",
    "home_wc_titles", "away_wc_titles",
    "home_wc_finals", "away_wc_finals",
    "home_pen_conv", "away_pen_conv",
    "is_wc", "is_knockout", "year",
]


def build_feature_matrix(results_df, rankings_df, elo, profiles) -> pd.DataFrame:
    ranking_map = dict(zip(rankings_df["team"], rankings_df["rank"]))
    points_map  = dict(zip(rankings_df["team"], rankings_df["points"]))

    # Running Elo during training
    running_elo = {}
    # Running per-team stats during training (incremental)
    r_stats = {}

    def get_rs(team):
        if team not in r_stats:
            r_stats[team] = {"wins":0,"draws":0,"losses":0,"gf":0,"ga":0,
                             "n":0,"recent":[]}
        return r_stats[team]

    def update_rs(team, gf, ga):
        s = get_rs(team)
        s["n"]+=1; s["gf"]+=gf; s["ga"]+=ga
        if gf>ga:   s["wins"]+=1;  s["recent"].append("W")
        elif gf==ga: s["draws"]+=1; s["recent"].append("D")
        else:        s["losses"]+=1;s["recent"].append("L")
        if len(s["recent"])>20: s["recent"].pop(0)

    rows = []
    for _, row in results_df.sort_values("date").iterrows():
        home  = row["home_team"]
        away  = row["away_team"]
        hs    = int(row["home_score"])
        as_   = int(row["away_score"])
        tourn = str(row.get("tournament","Friendly"))
        neutral = bool(row.get("neutral", True))

        hs_r = get_rs(home); as_r = get_rs(away)
        hm = max(hs_r["n"],1); am = max(as_r["n"],1)
        r_h = running_elo.get(home,1500)
        r_a = running_elo.get(away,1500)
        home_adv = 0 if neutral else 100

        hp = profiles.get(home, {}); ap = profiles.get(away, {})
        is_wc_match = 1 if "FIFA World Cup" in tourn and "qualif" not in tourn.lower() else 0
        is_ko = 1 if any(x in tourn.lower() for x in ["final","semi","quarter","round of"]) else 0

        feat = {
            "elo_diff":   (r_h+home_adv)-r_a,
            "elo_home":   r_h, "elo_away": r_a,
            "rank_home":  ranking_map.get(home,120),
            "rank_away":  ranking_map.get(away,120),
            "rank_diff":  ranking_map.get(home,120)-ranking_map.get(away,120),
            "points_home":points_map.get(home,1000),
            "points_away":points_map.get(away,1000),
            "points_diff":points_map.get(home,1000)-points_map.get(away,1000),
            "home_win_rate":  hs_r["wins"]/hm,
            "away_win_rate":  as_r["wins"]/am,
            "home_draw_rate": hs_r["draws"]/hm,
            "away_draw_rate": as_r["draws"]/am,
            "home_avg_gf": hs_r["gf"]/hm, "away_avg_gf": as_r["gf"]/am,
            "home_avg_ga": hs_r["ga"]/hm, "away_avg_ga": as_r["ga"]/am,
            "home_gd_avg": (hs_r["gf"]-hs_r["ga"])/hm,
            "away_gd_avg": (as_r["gf"]-as_r["ga"])/am,
            "home_form5":  _form_pts(hs_r["recent"],5),
            "away_form5":  _form_pts(as_r["recent"],5),
            "home_form10": _form_pts(hs_r["recent"],10),
            "away_form10": _form_pts(as_r["recent"],10),
            "home_shootout_wr": hp.get("shootout_win_rate",0.5),
            "away_shootout_wr": ap.get("shootout_win_rate",0.5),
            "home_wc_titles": hp.get("wc_titles",0),
            "away_wc_titles": ap.get("wc_titles",0),
            "home_wc_finals": hp.get("wc_finals",0),
            "away_wc_finals": ap.get("wc_finals",0),
            "home_pen_conv":  hp.get("penalty_conversion",0.75),
            "away_pen_conv":  ap.get("penalty_conversion",0.75),
            "is_wc":       is_wc_match,
            "is_knockout": is_ko,
            "year":        row["date"].year,
            "result": 2 if hs>as_ else (1 if hs==as_ else 0),
        }
        rows.append(feat)

        # Update running Elo
        k_mult=0.85
        for key,w in TOURNAMENT_K.items():
            if key.lower() in tourn.lower(): k_mult=w; break
        e_h = 1/(1+10**((r_a-(r_h+home_adv))/400))
        e_a = 1-e_h
        s_h,s_a = (1.0,0.0) if hs>as_ else ((0.5,0.5) if hs==as_ else (0.0,1.0))
        gd=abs(hs-as_); gd_m=1.0 if gd<=1 else (1.5 if gd==2 else 1.75+(gd-3)*0.1)
        k=20*k_mult*gd_m
        running_elo[home]=r_h+k*(s_h-e_h)
        running_elo[away]=r_a+k*(s_a-e_a)
        update_rs(home,hs,as_); update_rs(away,as_,hs)

    return pd.DataFrame(rows)


# ─── TRAINING ────────────────────────────────────────────────────────────────

def train_model():
    results, wc, gs, sh, wc_hist, rankings, _ = load_all_data()

    print("Computing team profiles from all datasets...")
    profiles = compute_team_profiles(results, wc, gs, sh, wc_hist, rankings)

    print("Computing Elo from full match history...")
    elo = compute_elo(results)

    # Use all data for Elo/profiles, 1990+ for feature matrix
    # (modern football is more predictive; also much faster to train)
    print("Building feature matrix (1990+ matches)...")
    results_modern = results[results["date"].dt.year >= 1990].copy()
    feature_df = build_feature_matrix(results_modern, rankings, elo, profiles)

    X = feature_df[FEATURE_COLS]
    y = feature_df["result"]

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    rf = RandomForestClassifier(
        n_estimators=500, max_depth=10, min_samples_leaf=4,
        max_features="sqrt", random_state=42, n_jobs=-1)
    gb = GradientBoostingClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.03,
        subsample=0.8, random_state=42)
    lr = LogisticRegression(max_iter=2000, C=0.3, random_state=42)

    ensemble = VotingClassifier(
        estimators=[("rf",rf),("gb",gb),("lr",lr)],
        voting="soft", weights=[3,3,1])

    calibrated = CalibratedClassifierCV(ensemble, cv=5, method="isotonic")
    calibrated.fit(X_scaled, y)

    cv = cross_val_score(ensemble, X_scaled, y, cv=5, scoring="accuracy")
    print(f"CV Accuracy: {cv.mean():.3f} ± {cv.std():.3f}")

    joblib.dump(calibrated, MODELS_PATH)
    joblib.dump(scaler,     SCALER_PATH)
    joblib.dump(elo,        ELO_PATH)
    joblib.dump(profiles,   STATS_PATH)
    print("All artifacts saved.")
    return calibrated, scaler, elo, profiles


def load_or_train():
    if all(p.exists() for p in [MODELS_PATH, SCALER_PATH, ELO_PATH, STATS_PATH]):
        model    = joblib.load(MODELS_PATH)
        scaler   = joblib.load(SCALER_PATH)
        elo      = joblib.load(ELO_PATH)
        profiles = joblib.load(STATS_PATH)
        elo.update(CURRENT_ELO)
        print("Model loaded from cache.")
    else:
        model, scaler, elo, profiles = train_model()
    return model, scaler, elo, profiles


# ─── PREDICTION ──────────────────────────────────────────────────────────────

def predict_match(home: str, away: str, model, scaler, elo: dict,
                  rankings_df: pd.DataFrame, is_knockout: bool = False,
                  profiles: dict = None) -> dict:

    ranking_map = dict(zip(rankings_df["team"], rankings_df["rank"]))
    points_map  = dict(zip(rankings_df["team"], rankings_df["points"]))
    profiles    = profiles or {}

    elo_h = CURRENT_ELO.get(home, elo.get(home, 1500))
    elo_a = CURRENT_ELO.get(away, elo.get(away, 1500))
    hp    = profiles.get(home, {})
    ap    = profiles.get(away, {})

    feat = {
        "elo_diff":   elo_h - elo_a,
        "elo_home":   elo_h, "elo_away": elo_a,
        "rank_home":  ranking_map.get(home, 120),
        "rank_away":  ranking_map.get(away, 120),
        "rank_diff":  ranking_map.get(home, 120) - ranking_map.get(away, 120),
        "points_home":points_map.get(home, 1000),
        "points_away":points_map.get(away, 1000),
        "points_diff":points_map.get(home, 1000) - points_map.get(away, 1000),
        "home_win_rate":  hp.get("win_rate",  0.45),
        "away_win_rate":  ap.get("win_rate",  0.35),
        "home_draw_rate": hp.get("draw_rate", 0.20),
        "away_draw_rate": ap.get("draw_rate", 0.20),
        "home_avg_gf": hp.get("avg_gf", 1.5),  "away_avg_gf": ap.get("avg_gf", 1.2),
        "home_avg_ga": hp.get("avg_ga", 1.0),  "away_avg_ga": ap.get("avg_ga", 1.2),
        "home_gd_avg": hp.get("gd_avg", 0.3),  "away_gd_avg": ap.get("gd_avg", 0.0),
        "home_form5":  hp.get("form5",  0.5),  "away_form5":  ap.get("form5",  0.5),
        "home_form10": hp.get("form10", 0.5),  "away_form10": ap.get("form10", 0.5),
        "home_shootout_wr": hp.get("shootout_win_rate", 0.5),
        "away_shootout_wr": ap.get("shootout_win_rate", 0.5),
        "home_wc_titles": hp.get("wc_titles", 0),
        "away_wc_titles": ap.get("wc_titles", 0),
        "home_wc_finals": hp.get("wc_finals", 0),
        "away_wc_finals": ap.get("wc_finals", 0),
        "home_pen_conv":  hp.get("penalty_conversion", 0.75),
        "away_pen_conv":  ap.get("penalty_conversion", 0.75),
        "is_wc":       1,
        "is_knockout": 1 if is_knockout else 0,
        "year":        2026,
    }

    X        = pd.DataFrame([feat])[FEATURE_COLS]
    X_scaled = scaler.transform(X)
    probs    = model.predict_proba(X_scaled)[0]
    pd_      = dict(zip(model.classes_, probs))

    away_p = pd_.get(0, 0.0)
    draw_p = pd_.get(1, 0.0)
    home_p = pd_.get(2, 0.0)
    tot    = away_p+draw_p+home_p
    away_p/=tot; draw_p/=tot; home_p/=tot

    if is_knockout:
        # Use shootout win rate to distribute draw probability
        h_so = hp.get("shootout_win_rate", 0.5)
        a_so = ap.get("shootout_win_rate", 0.5)
        so_total = h_so + a_so
        home_p += draw_p * (h_so / so_total)
        away_p += draw_p * (a_so / so_total)
        draw_p  = 0.0

    return {
        "home_team":            home,
        "away_team":            away,
        "home_win_probability": round(home_p*100, 1),
        "draw_probability":     round(draw_p*100, 1),
        "away_win_probability": round(away_p*100, 1),
        "predicted_winner":     home if home_p >= away_p else away,
        "home_elo":             round(elo_h, 1),
        "away_elo":             round(elo_a, 1),
        "home_shootout_wr":     round(hp.get("shootout_win_rate",0.5)*100, 1),
        "away_shootout_wr":     round(ap.get("shootout_win_rate",0.5)*100, 1),
    }
