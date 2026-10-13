// Thin wrapper around fetch. The browser only ever talks to /api/*;
// Nginx / Ingress routes that to the backend, so no backend hostname is needed here.
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join("; ");
    } catch {
      /* body was not JSON */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

const send = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  stats: () => request("/appointments/stats"),
  queue: () => request("/queue"),
  appointments: () => request("/appointments"),
  bookAppointment: (data) => request("/appointments", send("POST", data)),
  updateAppointment: (id, data) => request(`/appointments/${id}`, send("PUT", data)),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: "DELETE" }),
  doctors: () => request("/doctors"),
  addDoctor: (data) => request("/doctors", send("POST", data)),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: "DELETE" }),
  patients: () => request("/patients"),
  addPatient: (data) => request("/patients", send("POST", data)),
  deletePatient: (id) => request(`/patients/${id}`, { method: "DELETE" }),
};
