# FIFA WC 2026 Predictor — Backend

FastAPI + scikit-learn backend for predicting FIFA World Cup 2026 match outcomes.

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

## Train the Model

```bash
python scripts/train_model.py
```

Takes 20–30 minutes on first run. Saves `.pkl` files to `app/ml/` — subsequent runs load from cache instantly.

## Run

```bash
uvicorn app.main:app --port 8000
```

API docs available at: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/teams` | All teams with Elo + FIFA ranking |
| GET | `/api/v1/teams/{name}/stats` | Full team stats — form, shootout record, WC history |
| GET | `/api/v1/groups` | Official 2026 group draw |
| GET | `/api/v1/predict/group/{A-L}` | Predict all matches in a group |
| POST | `/api/v1/predict/match` | Predict a single match |
| POST | `/api/v1/simulate/tournament` | Run full Monte-Carlo simulation |

## ML Architecture

- **Training data**: 32,000+ international matches (1990–2026), Elo computed from 49,306 matches (1872–2026)
- **Features (34 total)**: Current Elo ratings, FIFA ranking + points, win/draw/loss rates, form (last 5 and 10 matches), average goals scored/conceded, xG averages, penalty conversion rate, shootout win rate, WC titles, WC finals appearances, knockout stage flag
- **Models**: Random Forest (200 trees) + Gradient Boosting (100 estimators) + Logistic Regression → Soft Voting Ensemble (weights 3:3:1)
- **Calibration**: Isotonic regression via `CalibratedClassifierCV`
- **Elo ratings**: Computed from full match history then overridden with verified current values from eloratings.net (June 2026)
- **Shootout predictions**: Team-specific penalty shootout win rates from historical data used to distribute draw probability in knockout matches
- **Tournament Simulation**: Monte-Carlo (default 1000 runs), official 48-team 2026 bracket with probability caching for performance
- **Output**: Win/Draw/Loss probabilities in % for every match; champion/finalist/semifinalist % across simulations

## Datasets

| File | Description | Rows |
|---|---|---|
| `international_results.csv` | All international match results 1872–2026 | 49,306 |
| `matches_1930_2022.csv` | World Cup matches with xG, penalties, cards, subs | 964 |
| `goalscorers.csv` | Individual goal events with penalty and own goal flags | 47,601 |
| `shootouts.csv` | Penalty shootout results per match | 675 |
| `former_names.csv` | Country name changes (e.g. West Germany → Germany) | 36 |
| `world_cup.csv` | Tournament-level summary (champion, runner-up, attendance) | 22 |
| `fifa_ranking_2026.csv` | FIFA world rankings as of April 2026 | 75 |

## Notes
- Elo ratings are computed incrementally in chronological order, then overridden with current verified values from eloratings.net (June 2026).
- The 2026 group draw reflects the official December 2025 draw. Update `GROUPS_2026` in `simulator.py` if needed.
- Model accuracy on 3-fold CV is typically 55–60% for 3-class prediction, competitive for football prediction tasks.
- Shootout win rates make knockout predictions team-specific — England's historically low shootout rate affects their knockout probability accordingly.