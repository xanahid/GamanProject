/**
 * Thin fetch wrapper shared by all Gaman React widgets.
 *
 * Auth strategy:
 *   1. Django session cookie (set automatically by the browser after the
 *      server-rendered login/signup flow) — works out of the box with
 *      credentials: 'same-origin'.
 *   2. JWT Bearer token stored in memory (set by PaymentWidget after a
 *      standalone login, or read from localStorage as a fallback for
 *      dev/testing).  Memory-first avoids XSS token theft.
 *
 * CSRF: reads the csrftoken cookie that Django sets and injects it as the
 * X-CSRFToken header on mutating requests, matching Django's default
 * CsrfViewMiddleware expectations.
 */

let _memoryToken = null;

export function setMemoryToken(token) {
  _memoryToken = token;
}

function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

export async function apiFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const isMutating = ["POST", "PUT", "PATCH", "DELETE"].includes(method);

  const token = _memoryToken || localStorage.getItem("gaman_access_token");

  const headers = {
    "Content-Type": "application/json",
    ...(isMutating ? { "X-CSRFToken": getCsrfToken() } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(path, {
    ...options,
    headers,
    credentials: "same-origin",
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw Object.assign(new Error(error.detail || JSON.stringify(error)), { status: response.status, data: error });
  }

  if (response.status === 204) return null;
  return response.json();
}
