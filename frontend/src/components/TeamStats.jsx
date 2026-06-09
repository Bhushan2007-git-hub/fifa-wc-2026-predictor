import { useState } from "react";
import { api } from "../services/api";

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

export default function TeamStats() {
  const [selected, setSelected] = useState("Brazil");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFetch = async () => {
    setLoading(true); setError(null);
    try { setStats(await api.getTeamStats(selected)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const StatCell = ({ label, value, accent }) => (
    <div className="stat-cell">
      <div className="stat-num" style={accent ? { color: "var(--pitch)" } : {}}>
        {value}
      </div>
      <div className="stat-lbl">{label}</div>
    </div>
  );

  const formColor = (v) => v >= 60 ? "var(--pitch)" : v >= 40 ? "var(--chalk-2)" : "var(--red)";

  return (
    <div>
      <div className="lookup-row">
        <div className="lookup-select-wrap">
          <div className="field-label">Select Nation</div>
          <select value={selected} onChange={e => setSelected(e.target.value)} className="field-select">
            {TEAMS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <button onClick={handleFetch} disabled={loading} className="predict-btn" style={{ alignSelf: "stretch", clipPath: "none" }}>
          {loading ? <span className="loading-row"><span className="spin" />Loading</span> : "Get Stats"}
        </button>
      </div>

      {error && <div className="error-strip">{error}</div>}

      {stats && (
        <div style={{ marginTop: "24px" }}>
          {/* Header */}
          <div className="stats-head">
            <div className="stats-name">{stats.team}</div>
            <div className="stats-badges">
              {stats.fifa_rank && <span className="badge badge-rank">FIFA #{stats.fifa_rank}</span>}
              <span className="badge badge-elo">ELO {stats.elo_rating}</span>
              {stats.wc_titles > 0 && (
                <span className="badge" style={{ background: "rgba(255,204,0,0.15)", color: "var(--gold)", border: "1px solid rgba(255,204,0,0.3)" }}>
                  {"🏆".repeat(stats.wc_titles)} {stats.wc_titles}× Champion
                </span>
              )}
            </div>
          </div>

          {/* Core stats grid */}
          <div className="stats-grid">
            <StatCell label="Total Matches" value={stats.total_wc_matches} />
            <StatCell label="Wins" value={stats.wins} accent />
            <StatCell label="Draws" value={stats.draws} />
            <StatCell label="Losses" value={stats.losses} />
            <StatCell label="Goals For" value={stats.goals_for} accent />
            <StatCell label="Goals Against" value={stats.goals_against} />
            <StatCell label="Goal Diff"
              value={stats.goal_difference > 0 ? `+${stats.goal_difference}` : stats.goal_difference}
              accent={stats.goal_difference > 0} />
            <StatCell label="WC Finals" value={stats.wc_finals} />
          </div>

          {/* Shootout + penalty row */}
          <div className="panel-row" style={{ marginBottom: "2px" }}>
            <div className="stat-cell" style={{ background: "var(--ink-3)", border: "1px solid var(--ink-4)", padding: "16px 20px" }}>
              <div className="field-label" style={{ marginBottom: "12px" }}>Penalty Shootouts</div>
              <div style={{ display: "flex", gap: "24px" }}>
                <div>
                  <div className="stat-num" style={{ fontSize: "28px" }}>{stats.shootout_played}</div>
                  <div className="stat-lbl">Played</div>
                </div>
                <div>
                  <div className="stat-num" style={{ fontSize: "28px", color: "var(--pitch)" }}>{stats.shootout_wins}</div>
                  <div className="stat-lbl">Won</div>
                </div>
                <div>
                  <div className="stat-num" style={{ fontSize: "28px", color: stats.shootout_win_rate >= 50 ? "var(--pitch)" : "var(--red)" }}>
                    {stats.shootout_win_rate}%
                  </div>
                  <div className="stat-lbl">Win Rate</div>
                </div>
              </div>
            </div>

            <div className="stat-cell" style={{ background: "var(--ink-3)", border: "1px solid var(--ink-4)", padding: "16px 20px" }}>
              <div className="field-label" style={{ marginBottom: "12px" }}>Penalty Conversion</div>
              <div className="stat-num" style={{ fontSize: "28px", color: "var(--pitch)" }}>
                {stats.penalty_conversion}%
              </div>
              <div className="stat-lbl">From spot kicks</div>
              <div className="winrate-track" style={{ marginTop: "10px" }}>
                <div className="winrate-fill" style={{ width: `${stats.penalty_conversion}%` }} />
              </div>
            </div>
          </div>

          {/* Form bars */}
          <div className="winrate-block">
            <div className="winrate-head">
              <span className="winrate-label">Win Rate (all matches)</span>
              <span className="winrate-val">{stats.win_rate}%</span>
            </div>
            <div className="winrate-track">
              <div className="winrate-fill" style={{ width: `${stats.win_rate}%` }} />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2px", marginTop: "2px" }}>
            <div className="winrate-block">
              <div className="winrate-head">
                <span className="winrate-label">Form — Last 5</span>
                <span className="winrate-val" style={{ color: formColor(stats.form_last5) }}>{stats.form_last5}%</span>
              </div>
              <div className="winrate-track">
                <div className="winrate-fill" style={{ width: `${stats.form_last5}%`, background: formColor(stats.form_last5) }} />
              </div>
            </div>
            <div className="winrate-block">
              <div className="winrate-head">
                <span className="winrate-label">Form — Last 10</span>
                <span className="winrate-val" style={{ color: formColor(stats.form_last10) }}>{stats.form_last10}%</span>
              </div>
              <div className="winrate-track">
                <div className="winrate-fill" style={{ width: `${stats.form_last10}%`, background: formColor(stats.form_last10) }} />
              </div>
            </div>
          </div>

          {/* Recent results */}
          {stats.recent_results && stats.recent_results.length > 0 && (
            <div style={{ marginTop: "2px", background: "var(--ink-3)", border: "1px solid var(--ink-4)", padding: "16px 20px" }}>
              <div className="field-label" style={{ marginBottom: "10px" }}>Recent Form</div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {stats.recent_results.map((r, i) => (
                  <div key={i} style={{
                    width: "32px", height: "32px",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: r === "W" ? "var(--pitch)" : r === "D" ? "var(--ink-5)" : "var(--red)",
                    color: r === "W" ? "var(--ink)" : "var(--chalk)",
                    fontFamily: "var(--font-display)", fontWeight: 800, fontSize: "14px",
                    letterSpacing: "1px",
                  }}>{r}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
