import { useState } from "react";
import { api } from "../services/api";
import ProbabilityBar from "./ProbabilityBar";

const TEAMS = [
  "France","Spain","Argentina","England","Portugal","Brazil","Netherlands",
  "Morocco","Belgium","Germany","Croatia","Italy","Colombia","Senegal",
  "Mexico","United States","Uruguay","Japan","Switzerland","Denmark",
  "Ecuador","South Korea","Austria","Iran","Australia","Turkey","Norway",
  "Serbia","Paraguay","Saudi Arabia","Ivory Coast","Egypt","Canada",
  "Tunisia","Scotland","Algeria","Ghana","Czechia","Qatar",
  "Bosnia-Herzegovina","Haiti","Panama","DR Congo","Jordan","Iraq",
  "Uzbekistan","Cape Verde","New Zealand","Curacao","South Africa","Sweden",
];

export default function MatchPredictor() {
  const [home, setHome] = useState("Brazil");
  const [away, setAway] = useState("France");
  const [isKnockout, setIsKnockout] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    if (!home || !away || home === away) return;
    setLoading(true); setError(null);
    try { setResult(await api.predictMatch(home, away, isKnockout)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="fixture-builder">
        <div className="fixture-team">
          <div className="fixture-label">Home Team</div>
          <select value={home} onChange={e => setHome(e.target.value)} className="fixture-select">
            {TEAMS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="fixture-vs">VS</div>
        <div className="fixture-team">
          <div className="fixture-label">Away Team</div>
          <select value={away} onChange={e => setAway(e.target.value)} className="fixture-select">
            {TEAMS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="controls-row">
        <label className="toggle-pill">
          <input
            type="checkbox"
            checked={isKnockout}
            onChange={e => setIsKnockout(e.target.checked)}
          />
          <span className="toggle-text">Knockout stage — no draws</span>
        </label>
        <div className="spacer" />
        <button
          onClick={handlePredict}
          disabled={loading || home === away}
          className="predict-btn"
        >
          {loading
            ? <span className="loading-row"><span className="spin" /> Analysing</span>
            : "Run Prediction"}
        </button>
      </div>

      {error && <div className="error-strip">{error}</div>}

      {result && (
        <div className="result-strip">
          {/* Teams + Elo */}
          <div className="result-scoreline">
            <div className="result-team home">
              <div className="result-team-name">{result.home_team}</div>
              <div className="result-elo">ELO {result.home_elo}</div>
            </div>
            <div className="result-center">
              <div className="result-winner-tag">Predicted winner</div>
              <div className="result-winner-name">{result.predicted_winner}</div>
            </div>
            <div className="result-team away" style={{ textAlign: "right" }}>
              <div className="result-team-name">{result.away_team}</div>
              <div className="result-elo">ELO {result.away_elo}</div>
            </div>
          </div>

          {/* Win/Draw/Loss probabilities */}
          <ProbabilityBar
            label={`${result.home_team} Win`}
            value={result.home_win_probability}
            color="var(--pitch)"
          />
          {result.draw_probability > 0 && (
            <ProbabilityBar
              label="Draw"
              value={result.draw_probability}
              color="var(--chalk-3)"
            />
          )}
          <ProbabilityBar
            label={`${result.away_team} Win`}
            value={result.away_win_probability}
            color="var(--blue)"
          />

          {/* Shootout panel — shown in knockout mode */}
          {isKnockout && (
            <div className="shootout-panel">
              <div className="field-label" style={{ marginBottom: "10px" }}>
                Penalty Shootout Win Rate (if it goes to penalties)
              </div>
              <div className="shootout-row">
                <div className="shootout-team">
                  <div className="shootout-name">{result.home_team}</div>
                  <div className="shootout-pct">{result.home_shootout_wr}%</div>
                </div>
                <div className="shootout-bar-wrap">
                  <div className="shootout-track">
                    <div
                      className="shootout-fill-home"
                      style={{ width: `${result.home_shootout_wr}%` }}
                    />
                  </div>
                </div>
                <div className="shootout-team right">
                  <div className="shootout-name">{result.away_team}</div>
                  <div className="shootout-pct">{result.away_shootout_wr}%</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
