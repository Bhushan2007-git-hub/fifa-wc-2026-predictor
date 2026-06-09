import { useState } from "react";
import { api } from "../services/api";

export default function TournamentSimulator() {
  const [simulations, setSimulations] = useState(1000);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("champion");

  const handleSimulate = async () => {
    setLoading(true); setError(null);
    try { setResult(await api.simulateTournament(simulations)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const tabs = [
    { key: "champion",  label: "Champion %" },
    { key: "finalist",  label: "Finalist %" },
    { key: "semifinal", label: "Semi-Final %" },
    { key: "groups",    label: "Group Standings" },
  ];

  const maxChamp  = result ? Math.max(...Object.values(result.champion_probabilities))  : 1;
  const maxFinal  = result ? Math.max(...Object.values(result.finalist_probabilities))  : 1;
  const maxSemi   = result ? Math.max(...Object.values(result.semifinalist_probabilities)) : 1;

  const LbRow = ({ rank, team, prob, max, color }) => (
    <div className="lb-row">
      <div className="lb-rank">{rank}</div>
      <div className="lb-team">{team}</div>
      <div className="lb-bar-wrap">
        <div className="lb-bar-row">
          <div className="lb-track">
            <div
              className="lb-fill"
              style={{
                width: `${(prob / max) * 100}%`,
                backgroundColor: color,
              }}
            />
          </div>
          <div className="lb-pct">{prob}%</div>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <div className="sim-config">
        <div className="sim-field">
          <div className="field-label">Simulations</div>
          <select
            value={simulations}
            onChange={e => setSimulations(Number(e.target.value))}
            className="field-select"
          >
            <option value={100}>100 — Fast preview</option>
            <option value={500}>500</option>
            <option value={1000}>1000 — Balanced</option>
            <option value={2000}>2000 — Accurate</option>
            <option value={5000}>5000 — Precise</option>
          </select>
        </div>
      </div>

      <button
        onClick={handleSimulate}
        disabled={loading}
        className="predict-btn full"
      >
        {loading
          ? <span className="loading-row"><span className="spin" /> Simulating {simulations.toLocaleString()} full tournaments...</span>
          : `Run ${simulations.toLocaleString()} Simulations`}
      </button>

      {error && <div className="error-strip">{error}</div>}

      {result && (
        <div style={{ marginTop: "24px" }}>
          <div className="sim-meta-bar">
            ▸ {result.simulations_run.toLocaleString()} tournaments simulated
            &nbsp;·&nbsp; 48 teams &nbsp;·&nbsp; official 2026 draw
            &nbsp;·&nbsp; all 7 datasets used
            &nbsp;·&nbsp; shootout rates included
          </div>

          <div className="tab-strip">
            {tabs.map(t => (
              <button
                key={t.key}
                className={`tab-btn ${activeTab === t.key ? "active" : ""}`}
                onClick={() => setActiveTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {activeTab === "champion" && (
            <div className="leaderboard">
              {result.top_champions.map((item, i) => (
                <LbRow
                  key={item.team} rank={i + 1}
                  team={item.team} prob={item.probability}
                  max={maxChamp} color="var(--gold)"
                />
              ))}
            </div>
          )}

          {activeTab === "finalist" && (
            <div className="leaderboard">
              {result.top_finalists.map((item, i) => (
                <LbRow
                  key={item.team} rank={i + 1}
                  team={item.team} prob={item.probability}
                  max={maxFinal} color="var(--chalk-2)"
                />
              ))}
            </div>
          )}

          {activeTab === "semifinal" && (
            <div className="leaderboard">
              {Object.entries(result.semifinalist_probabilities)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 16)
                .map(([team, prob], i) => (
                  <LbRow
                    key={team} rank={i + 1}
                    team={team} prob={prob}
                    max={maxSemi} color="var(--pitch)"
                  />
                ))}
            </div>
          )}

          {activeTab === "groups" && result.group_stage_results && (
            <div className="groups-grid">
              {Object.entries(result.group_stage_results).map(([gName, gData]) => (
                <div key={gName} className="group-block">
                  <div className="group-head">
                    <span className="group-letter">{gName}</span>
                    <span className="group-word">Group</span>
                  </div>
                  <table className="group-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Team</th>
                        <th>Pts</th>
                        <th>GD</th>
                        <th>GF</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gData.standings.map(s => (
                        <tr key={s.team} className={s.position <= 2 ? "q" : ""}>
                          <td className="td-pos">{s.position}</td>
                          <td className="td-team">{s.team}</td>
                          <td className="td-pts">{s.points}</td>
                          <td className="td-center">{s.gd > 0 ? `+${s.gd}` : s.gd}</td>
                          <td className="td-center">{s.gf}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
