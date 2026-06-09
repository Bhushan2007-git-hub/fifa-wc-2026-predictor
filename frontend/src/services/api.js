const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),

  getTeams: () => request("/teams"),

  getTeamStats: (name) => request(`/teams/${encodeURIComponent(name)}/stats`),

  getGroups: () => request("/groups"),

  predictGroup: (groupName) => request(`/predict/group/${groupName}`),

  predictMatch: (homeTeam, awayTeam, isKnockout = false) =>
    request("/predict/match", {
      method: "POST",
      body: JSON.stringify({
        home_team: homeTeam,
        away_team: awayTeam,
        is_knockout: isKnockout,
      }),
    }),

  simulateTournament: (simulations = 1000) =>
    request("/simulate/tournament", {
      method: "POST",
      body: JSON.stringify({ simulations }),
    }),

  getCachedTournament: () => request("/simulate/tournament/cached"),
};
