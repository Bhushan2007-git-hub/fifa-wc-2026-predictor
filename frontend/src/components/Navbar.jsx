export default function Navbar({ activeTab, setActiveTab }) {
  const tabs = [
    { key: "match", label: "Match", icon: "⚽" },
    { key: "group", label: "Group Stage", icon: "🗂" },
    { key: "tournament", label: "Simulate", icon: "🌍" },
    { key: "teams", label: "Teams", icon: "📈" },
  ];

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <div className="nav-logo-mark">26</div>
        <div className="nav-title-block">
          <div className="nav-title-top">FIFA WC Predictor</div>
          <div className="nav-title-sub">▸ LIVE MODEL</div>
        </div>
      </div>
      <div className="nav-tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`nav-tab ${activeTab === t.key ? "active" : ""}`}
            onClick={() => setActiveTab(t.key)}
          >
            <span className="nav-icon">{t.icon}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
