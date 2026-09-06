async function request(path, { method = "GET", body, headers } = {}) {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
      : detail || data?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  me: () => request("/api/auth/me"),
  register: (body) => request("/api/auth/register", { method: "POST", body }),
  login: (body) => request("/api/auth/login", { method: "POST", body }),
  logout: () => request("/api/auth/logout", { method: "POST", body: {} }),
  getProfile: () => request("/api/profile"),
  saveProfile: (body) => request("/api/profile", { method: "PUT", body }),
  profileChat: (body) => request("/api/profile/chat", { method: "POST", body }),
  uploadResume: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/profile/resume", {
      method: "POST",
      credentials: "include",
      body: form,
    });
    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
    }
    if (!response.ok) {
      const detail = data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
        : detail || data?.error || `Request failed (${response.status})`;
      throw new Error(message);
    }
    return data;
  },
  startSearch: () => request("/api/searches", { method: "POST", body: {} }),
  getSearch: (id) => request(`/api/searches/${id}`),
  listJobs: (params = {}) => {
    const query = new URLSearchParams();
    if (params.recommendation) query.set("recommendation", params.recommendation);
    if (params.min_score != null && params.min_score !== "") query.set("min_score", String(params.min_score));
    const suffix = query.toString() ? `?${query}` : "";
    return request(`/api/jobs${suffix}`);
  },
  createManualJob: (body) => request("/api/jobs/manual", { method: "POST", body }),
  prepareJob: (id) => request(`/api/jobs/${id}/prepare`, { method: "POST", body: {} }),
  listApplications: () => request("/api/applications"),
  getApplication: (id) => request(`/api/applications/${id}`),
  patchApplication: (id, body) => request(`/api/applications/${id}`, { method: "PATCH", body }),
  insights: () => request("/api/insights"),
};
