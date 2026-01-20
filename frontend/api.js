const TOKEN_KEY = "oa_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data?.detail || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/api/auth/login", { method: "POST", body: { username, password }, auth: false }),
  me: () => request("/api/auth/me"),
  listAnnouncements: () => request("/api/announcements"),
  createAnnouncement: (title, content) =>
    request("/api/announcements", { method: "POST", body: { title, content } }),
  createRequest: (payload) => request("/api/requests", { method: "POST", body: payload }),
  listMyRequests: () => request("/api/requests/mine"),
  listPendingApprovals: () => request("/api/approvals/pending"),
  decide: (id, decision, comment) =>
    request(`/api/approvals/${id}/decide`, { method: "POST", body: { decision, comment } }),

  listDepts: () => request("/api/depts"),
  createDept: (name) => request("/api/depts", { method: "POST", body: { name } }),
  listUsers: () => request("/api/users"),
  createUser: (payload) => request("/api/users", { method: "POST", body: payload }),
  updateUser: (id, payload) => request(`/api/users/${id}`, { method: "PATCH", body: payload }),
  setUserPassword: (id, password) =>
    request(`/api/users/${id}/password`, { method: "PUT", body: { password } }),
};
