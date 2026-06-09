# FIFA WC 2026 Predictor — Backend

FastAPI + scikit-learn backend for predicting FIFA World Cup 2026 match outcomes.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/teams` | All teams with Elo + FIFA ranking |
| GET | `/api/v1/teams/{name}/stats` | Historical WC stats for a team |
| GET | `/api/v1/groups` | 2026 group assignments |
| GET | `/api/v1/predict/group/{A-L}` | Predict all matches in a group |
| POST | `/api/v1/predict/match` | Predict a single match |
| POST | `/api/v1/simulate/tournament` | Run full Monte-Carlo simulation |
| GET | `/api/v1/simulate/tournament/cached` | Get last simulation result |

## ML Architecture

- **Features**: Elo ratings (custom-computed from 1930-2022 WC data), FIFA ranking points, historical win/draw/loss rates, average goals scored/conceded, knockout stage flag
- **Models**: Random Forest (300 trees) + Gradient Boosting (200 estimators) + Logistic Regression → Soft Voting Ensemble
- **Calibration**: Isotonic regression via `CalibratedClassifierCV`
- **Tournament Simulation**: Monte-Carlo (default 1000 runs), 48-team 2026 format
- **Output**: Win/Draw/Loss probabilities in % for every match; champion/finalist/semifinalist % across simulations
