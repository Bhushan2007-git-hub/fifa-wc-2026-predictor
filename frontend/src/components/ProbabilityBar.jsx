export default function ProbabilityBar({ label, value, color }) {
  return (
    <div className="prob-block">
      <div className="prob-meta">
        <span className="prob-name">{label}</span>
        <span className="prob-pct">{value}%</span>
      </div>
      <div className="prob-track">
        <div
          className="prob-fill"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
