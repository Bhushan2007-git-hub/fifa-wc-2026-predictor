# FIFA World Cup 2026 Predictor

An ML-powered full-stack application that predicts all FIFA World Cup 2026 match outcomes, group standings, and ultimately the champion — with every metric expressed as a percentage.

---

## Features

| Feature | Description |
|---|---|
| **Match Predictor** | Win/Draw/Loss % for any two teams using trained ensemble model |
| **Group Stage** | All 6 matches per group predicted with probabilities |
| **Tournament Simulator** | Monte-Carlo simulation of the full 48-team bracket (up to 5000 runs) |
| **Champion Odds** | % probability for each team to win the tournament |
| **Finalist/Semi-Finalist Odds** | Breakdown of how far each team is expected to go |
| **Team Stats** | Historical World Cup record + Elo + FIFA ranking |

---

## ML Architecture

### Algorithms
- **Random Forest** (200 trees, depth 8)
- **Gradient Boosting** (100 estimators, LR 0.08)
- **Logistic Regression** (L2 regularisation)
- Combined as a **Soft Voting Ensemble** (weights 3:3:1)
- Output calibrated using **Isotonic Regression** (`CalibratedClassifierCV`)

### Features Used (34 total)
| Feature | Source |
|---|---|
| Elo rating differential + absolute ratings | eloratings.net (June 2026) |
| FIFA ranking + points differential | `fifa_ranking_2026.csv` |
| Win / draw / loss rates | `international_results.csv` |
| Form — last 5 and last 10 matches | `international_results.csv` |
| Average goals scored / conceded | `international_results.csv` |
| xG averages | `matches_1930_2022.csv` |
| Penalty conversion rate | `goalscorers.csv` |
| Shootout win rate | `shootouts.csv` |
| WC titles + WC finals appearances | `world_cup.csv` |
| Knockout stage flag + year | Match metadata |

### Simulation Method
The tournament simulator runs **Monte-Carlo sampling** (default: 1,000 full tournaments):
1. Group stage — all 6 matches per group simulated; teams ranked by points → GD → GF
2. Best 8 third-place teams qualify (48-team 2026 format = 32 knockout round)
3. Knockout rounds — no draws; penalty shootout probability folded into win/loss odds
4. Results aggregated → championship %, finalist %, semi-finalist %

---

## Project Structure

```
fifa_predictor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── api/
│   │   │   └── routes.py        # All API endpoints
│   │   └── ml/
│   │       ├── model.py         # Elo engine + feature engineering + training
│   │       └── simulator.py     # Tournament bracket + Monte-Carlo simulator
│   ├── data/                    # CSV datasets (gitignored model cache)
│   ├── scripts/
│   │   ├── train_model.py       # Standalone training script
│   │   └── simulate_tournament.py  # CLI tournament runner
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── MatchPredictor.jsx
│   │   │   ├── GroupPredictor.jsx
│   │   │   ├── TournamentSimulator.jsx
│   │   │   ├── TeamStats.jsx
│   │   │   └── ProbabilityBar.jsx
│   │   └── services/
│   │       └── api.js           # Axios-style fetch wrapper
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### Option 1 — Docker Compose (recommended)

```bash
git clone https://github.com/Bhushan2007-git-hub/fifa-wc-2026-predictor.git
cd fifa-wc-2026-predictor
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

---

### Option 2 — Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: pre-train the model
python scripts/train_model.py

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at http://localhost:3000

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/teams` | All teams with Elo + FIFA rank |
| `GET` | `/api/v1/teams/{name}/stats` | Team historical WC stats |
| `GET` | `/api/v1/groups` | 2026 group draw |
| `GET` | `/api/v1/predict/group/{A-L}` | All match predictions for a group |
| `POST` | `/api/v1/predict/match` | Single match prediction |
| `POST` | `/api/v1/simulate/tournament` | Run Monte-Carlo tournament simulation |
| `GET` | `/api/v1/simulate/tournament/cached` | Get last simulation result |

### POST `/api/v1/predict/match`
```json
{
  "home_team": "Brazil",
  "away_team": "France",
  "is_knockout": false
}
```

**Response:**
```json
{
  "home_team": "Brazil",
  "away_team": "France",
  "home_win_probability": 42.3,
  "draw_probability": 24.1,
  "away_win_probability": 33.6,
  "predicted_winner": "Brazil",
  "home_elo": 2089.4,
  "away_elo": 2041.7
}
```

### POST `/api/v1/simulate/tournament`
```json
{ "simulations": 1000 }
```

**Response includes:**
- `champion_probabilities` — `{ "Brazil": 18.4, "France": 14.2, ... }`
- `finalist_probabilities` — % chance of reaching the final
- `semifinalist_probabilities` — % chance of reaching semi-finals
- `top_champions` — sorted list of top 16 contenders
- `group_stage_results` — predicted group standings
- `sample_bracket` — full bracket from simulation run #1

---

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

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| ML | scikit-learn (RF + GB + LR ensemble) |
| Data | pandas, numpy |
| Model persistence | joblib |
| Frontend | React 18 + Vite |
| Styling | Pure CSS (no framework) |
| Containerisation | Docker + Docker Compose |
| Reverse proxy | Nginx |

---

## Notes

- The model is trained on 32,000+ international matches (1990–2026), with Elo computed from the full 49,306 match history (1872–2026).
- Elo ratings are computed incrementally in chronological order, then overridden with current verified values from eloratings.net (June 2026).
- The 2026 group draw reflects the official December 2025 draw. Update `GROUPS_2026` in `simulator.py` if needed.
- Model accuracy on 3-fold CV is typically 55–60% for 3-class prediction (home win / draw / away win), which is competitive for football prediction tasks.
- Shootout win rates from `shootouts.csv` are used to distribute draw probability in knockout matches, making penalty predictions team-specific.
