import { useState } from "react";
import { api } from "../services/api";
import ProbabilityBar from "./ProbabilityBar";

const GROUPS = ["A","B","C","D","E","F","G","H","I","J","K","L"];

export default function GroupPredictor() {
  const [group, setGroup] = useState("A");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    setLoading(true); setError(null);
    try {
      const data = await api.predictGroup(group);
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="lookup-row">
        <div className="lookup-select-wrap">
          <div className="field-label">Group</div>
          <select value={group} onChange={e => setGroup(e.target.value)} className="field-select">
            {GROUPS.map(g => <option key={g} value={g}>Group {g}</option>)}
          </select>
        </div>
        <button onClick={handlePredict} disabled={loading} className="predict-btn" style={{ alignSelf: "stretch", clipPath: "none" }}>
          {loading ? <span className="loading-row"><span className="spin" />Predicting</span> : "Predict Group"}
        </button>
      </div>

      {error && <div className="error-strip">{error}</div>}

      {result && (
        <div style={{ marginTop: "16px" }}>
          <div className="group-teams-row">
            {result.teams.map(t => <div key={t} className="team-tag">{t}</div>)}
          </div>

          {result.matches.map((m, i) => (
            <div key={i} className="match-block">
              <div className="match-title-row">
                <span className={`match-home ${m.home_win_probability > m.away_win_probability ? "fav" : ""}`}>
                  {m.home_team}
                </span>
                <span className="match-sep">VS</span>
                <span className={`match-home ${m.away_win_probability > m.home_win_probability ? "fav" : ""}`}>
                  {m.away_team}
                </span>
              </div>
              <ProbabilityBar label={`${m.home_team} Win`} value={m.home_win_probability} color="var(--pitch)" />
              <ProbabilityBar label="Draw" value={m.draw_probability} color="var(--chalk-3)" />
              <ProbabilityBar label={`${m.away_team} Win`} value={m.away_win_probability} color="var(--blue)" />
              <div className="match-predicted">
                Predicted: <strong>{m.predicted_winner}</strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
