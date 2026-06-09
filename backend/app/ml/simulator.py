"""
FIFA WC 2026 Tournament Simulator
Runs fast by pre-computing all match probabilities once at startup,
then simulations only do random number draws — no model calls during loop.
"""
import numpy as np
from .model import predict_match, CURRENT_ELO

GROUPS_2026 = {
    "A": ["Mexico",        "South Korea",   "South Africa",      "Czechia"],
    "B": ["Canada",        "Switzerland",   "Qatar",             "Bosnia-Herzegovina"],
    "C": ["Brazil",        "Morocco",       "Scotland",          "Haiti"],
    "D": ["United States", "Paraguay",      "Australia",         "Turkey"],
    "E": ["Germany",       "Ecuador",       "Ivory Coast",       "Curacao"],
    "F": ["Netherlands",   "Japan",         "Tunisia",           "Sweden"],
    "G": ["Belgium",       "Iran",          "Egypt",             "New Zealand"],
    "H": ["Spain",         "Uruguay",       "Saudi Arabia",      "Cape Verde"],
    "I": ["France",        "Senegal",       "Norway",            "Iraq"],
    "J": ["Argentina",     "Austria",       "Algeria",           "Jordan"],
    "K": ["Portugal",      "Colombia",      "Uzbekistan",        "DR Congo"],
    "L": ["England",       "Croatia",       "Panama",            "Ghana"],
}

# Global probability cache — built once per server session
_PROB_CACHE: dict = {}
_CACHE_BUILT = False


def _build_prob_cache(model, scaler, elo, rankings_df, profiles):
    """
    Pre-compute ALL match probabilities once.
    Group: 72 matchups. Knockout pairwise: 48*47/2 = 1128 matchups.
    Total: ~1200 predict_match calls. Done once, reused forever.
    """
    global _PROB_CACHE, _CACHE_BUILT
    if _CACHE_BUILT:
        return

    print("Building match probability cache...")
    all_teams = [t for ts in GROUPS_2026.values() for t in ts]

    # Group matchups
    for teams in GROUPS_2026.values():
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                h, a = teams[i], teams[j]
                p = predict_match(h, a, model, scaler, elo, rankings_df, False, profiles)
                _PROB_CACHE[(h, a, False)] = (
                    p["home_win_probability"] / 100,
                    p["draw_probability"] / 100,
                    p["away_win_probability"] / 100,
                )
                _PROB_CACHE[(h, a, "pred")] = p  # keep full dict for display

    # Knockout pairwise (both directions, so bracket shuffle works)
    for i, t1 in enumerate(all_teams):
        for t2 in all_teams[i + 1:]:
            p = predict_match(t1, t2, model, scaler, elo, rankings_df, True, profiles)
            hw = p["home_win_probability"] / 100
            aw = p["away_win_probability"] / 100
            _PROB_CACHE[(t1, t2, True)] = (hw, 0.0, aw)
            _PROB_CACHE[(t2, t1, True)] = (aw, 0.0, hw)
            _PROB_CACHE[(t1, t2, "pred")] = p

    _CACHE_BUILT = True
    print(f"  Cache built: {len([k for k in _PROB_CACHE if k[2] != 'pred'])} matchups cached.")


def _get(home, away, is_ko):
    key = (home, away, is_ko)
    if key in _PROB_CACHE:
        return _PROB_CACHE[key]
    # Should never happen after cache is built, but fallback
    return (0.5, 0.0 if is_ko else 0.2, 0.5)


def run_full_tournament(model, scaler, elo, rankings_df, profiles,
                        n_simulations=1000):
    # Build cache once — subsequent calls reuse it instantly
    _build_prob_cache(model, scaler, elo, rankings_df, profiles)

    all_teams = [t for ts in GROUPS_2026.values() for t in ts]
    champ_c = {t: 0 for t in all_teams}
    final_c = {t: 0 for t in all_teams}
    semi_c  = {t: 0 for t in all_teams}
    first_groups  = None
    first_bracket = []

    for sim in range(n_simulations):
        rng = np.random.default_rng(sim)

        # ── Group stage ──────────────────────────────────────────────────
        group_results = {}
        for gname, teams in GROUPS_2026.items():
            pts = {t: 0 for t in teams}
            gf  = {t: 0 for t in teams}
            ga  = {t: 0 for t in teams}
            matches = []

            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    h, a   = teams[i], teams[j]
                    hw, dw, aw = _get(h, a, False)
                    r = rng.random()

                    if r < hw:
                        hg = int(rng.integers(1, 4))
                        ag = int(rng.integers(0, hg))
                        pts[h] += 3; oc = "home_win"
                    elif r < hw + dw:
                        s = int(rng.integers(0, 3))
                        hg = ag = s
                        pts[h] += 1; pts[a] += 1; oc = "draw"
                    else:
                        ag = int(rng.integers(1, 4))
                        hg = int(rng.integers(0, ag))
                        pts[a] += 3; oc = "away_win"

                    gf[h] += hg; ga[h] += ag
                    gf[a] += ag; ga[a] += hg

                    if sim == 0:
                        pred = _PROB_CACHE.get((h, a, "pred"), {})
                        matches.append({**pred,
                            "simulated_home_score": hg,
                            "simulated_away_score": ag,
                            "outcome": oc,
                            "stage": f"Group {gname}"})

            standings = sorted(teams,
                key=lambda t: (pts[t], gf[t] - ga[t], gf[t]), reverse=True)

            group_results[gname] = {
                "standings": [
                    {"team": t, "points": pts[t], "gf": gf[t],
                     "ga": ga[t], "gd": gf[t] - ga[t], "position": idx + 1}
                    for idx, t in enumerate(standings)
                ],
                "matches": matches,
            }

        if sim == 0:
            first_groups = group_results

        # ── Qualify 32 teams ─────────────────────────────────────────────
        qualifiers = []
        thirds = []
        for gdata in group_results.values():
            s = gdata["standings"]
            qualifiers.append(s[0]["team"])
            qualifiers.append(s[1]["team"])
            thirds.append(s[2])

        thirds_sorted = sorted(thirds,
            key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)
        for t in thirds_sorted[:8]:
            qualifiers.append(t["team"])

        # ── Knockout bracket ─────────────────────────────────────────────
        bracket = qualifiers[:]
        rng.shuffle(bracket)
        round_names = ["Round of 32", "Round of 16",
                       "Quarter-finals", "Semi-finals", "Final"]
        current = bracket
        ri = 0
        sim_matches = []

        while len(current) > 1:
            stage = round_names[min(ri, len(round_names) - 1)]
            nxt   = []
            for i in range(0, len(current), 2):
                if i + 1 >= len(current):
                    nxt.append(current[i]); continue

                h, a = current[i], current[i + 1]
                hw_p, _, aw_p = _get(h, a, True)

                if sim == 0:
                    pred = _PROB_CACHE.get((h, a, "pred"),
                           _PROB_CACHE.get((a, h, "pred"), {}))
                    sim_matches.append({**pred, "stage": stage})

                if stage == "Semi-finals":
                    semi_c[h] = semi_c.get(h, 0) + 1
                    semi_c[a] = semi_c.get(a, 0) + 1
                if stage == "Final":
                    final_c[h] = final_c.get(h, 0) + 1
                    final_c[a] = final_c.get(a, 0) + 1

                winner = h if rng.random() < hw_p else a
                nxt.append(winner)

            current = nxt
            ri += 1

        champ_c[current[0]] = champ_c.get(current[0], 0) + 1
        if sim == 0:
            first_bracket = sim_matches

    def pct(d):
        return {k: round(v / n_simulations * 100, 1) for k, v in d.items()}

    cp = pct(champ_c)
    fp = pct(final_c)
    sp = pct(semi_c)

    return {
        "champion_probabilities":     cp,
        "finalist_probabilities":     fp,
        "semifinalist_probabilities": sp,
        "top_champions":  [{"team": t, "probability": p}
                           for t, p in sorted(cp.items(), key=lambda x: x[1], reverse=True)[:16]],
        "top_finalists":  [{"team": t, "probability": p}
                           for t, p in sorted(fp.items(), key=lambda x: x[1], reverse=True)[:16]],
        "group_stage_results": first_groups,
        "sample_bracket":      first_bracket,
        "simulations_run":     n_simulations,
    }
