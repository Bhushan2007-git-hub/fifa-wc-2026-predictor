import { useState } from "react";
import Navbar from "./components/Navbar";
import MatchPredictor from "./components/MatchPredictor";
import GroupPredictor from "./components/GroupPredictor";
import TournamentSimulator from "./components/TournamentSimulator";
import TeamStats from "./components/TeamStats";
import "./index.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("match");

  const titles = {
    match: { num: "01", title: "Match Predictor", sub: "Head-to-head probability analysis" },
    group: { num: "02", title: "Group Stage", sub: "Round-robin predictions per group" },
    tournament: { num: "03", title: "Tournament Simulator", sub: "Monte-Carlo bracket simulation" },
    teams: { num: "04", title: "Team Intelligence", sub: "Historical stats & current ranking" },
  };

  const t = titles[activeTab];

  return (
    <div className="app">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="hero">
        <div className="hero-eyebrow">FIFA World Cup 2026 · USA / Canada / Mexico</div>
        <h1 className="hero-headline">
          {t.num === "01" && <><em>Predict</em> the<br />next match</>}
          {t.num === "02" && <>Group stage<br /><em>breakdown</em></>}
          {t.num === "03" && <><em>Simulate</em><br />the tournament</>}
          {t.num === "04" && <>Team<br /><em>intelligence</em></>}
        </h1>
        <p className="hero-sub">{t.sub}</p>
      </div>

      <main className="main-content">
        <div className="content-area">
          {activeTab === "match" && <MatchPredictor />}
          {activeTab === "group" && <GroupPredictor />}
          {activeTab === "tournament" && <TournamentSimulator />}
          {activeTab === "teams" && <TeamStats />}
        </div>
      </main>

      <footer className="footer">
        <div className="footer-right">
          Trained on WC data 1930–2026<span className="footer-dot">·</span>
          Rankings Jun 2026
        </div>
      </footer>
    </div>
  );
}
