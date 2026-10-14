import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

const STATUS_LABEL = {
  booked: "Booked",
  checked_in: "Checked in",
  completed: "Completed",
  cancelled: "Cancelled",
};
const FILTERS = ["all", "booked", "checked_in", "completed", "cancelled"];
const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "▦" },
  { id: "doctors", label: "Doctors", icon: "✚" },
  { id: "patients", label: "Patients", icon: "☺" },
];

const fmtTime = (iso) =>
  new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
const fmtClock = (iso) => new Date(iso).toLocaleTimeString([], { timeStyle: "short" });

function defaultSlot() {
  const d = new Date();
  d.setMinutes(0, 0, 0);
  d.setHours(d.getHours() + 1);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function Badge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABEL[status]}</span>;
}

function Kpi({ label, value, tone }) {
  return (
    <div className={`card kpi kpi-${tone}`}>
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value ?? "–"}</strong>
    </div>
  );
}

function QueueBoard({ queue }) {
  const byDoctor = queue.reduce((acc, q) => {
    (acc[q.doctor_name] ||= []).push(q);
    return acc;
  }, {});
  const names = Object.keys(byDoctor);
  return (
    <section className="card">
      <h2>Live queue <span className="live-dot" title="Refreshes every 5 seconds" /></h2>
      {names.length === 0 && <p className="muted">Nobody is waiting right now.</p>}
      <div className="queue-grid">
        {names.map((name) => {
          const [now, ...next] = byDoctor[name];
          return (
            <div key={name} className="queue-col">
              <h3>{name}</h3>
              <div className={`now-serving ${now.status === "checked_in" ? "ready" : ""}`}>
                <small>{now.status === "checked_in" ? "Now serving" : "Up next"}</small>
                <strong>#{now.token_number}</strong>
                <span>{now.patient_name}</span>
              </div>
              <ul className="queue-list">
                {next.map((q) => (
                  <li key={q.id}>
                    <b>#{q.token_number}</b> {q.patient_name}
                    <span className="muted"> · {fmtClock(q.scheduled_at)}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function AppointmentsTable({ appointments, filter, setFilter, onAction, onBook }) {
  const rows = appointments.filter((a) => filter === "all" || a.status === filter);
  return (
    <section className="card">
      <div className="row-between">
        <h2>Appointments</h2>
        <button className="btn primary" onClick={onBook}>+ Book appointment</button>
      </div>
      <div className="chips">
        {FILTERS.map((f) => (
          <button key={f} className={`chip ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
            {f === "all" ? "All" : STATUS_LABEL[f]}
          </button>
        ))}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Token</th><th>Patient</th><th>Doctor</th><th>When</th><th>Reason</th><th>Status</th><th /></tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td><b>#{a.token_number}</b></td>
                <td>{a.patient_name}</td>
                <td>{a.doctor_name}</td>
                <td>{fmtTime(a.scheduled_at)}</td>
                <td className="muted">{a.reason || "—"}</td>
                <td><Badge status={a.status} /></td>
                <td className="actions">
                  {a.status === "booked" && (
                    <button className="btn small" onClick={() => onAction(a.id, "checked_in")}>Check in</button>
                  )}
                  {(a.status === "booked" || a.status === "checked_in") && (
                    <>
                      <button className="btn small ok" onClick={() => onAction(a.id, "completed")}>Done</button>
                      <button className="btn small danger" onClick={() => onAction(a.id, "cancelled")}>Cancel</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan="7" className="muted empty">No appointments to show.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Activity({ appointments }) {
  const recent = [...appointments]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 6);
  return (
    <section className="card">
      <h2>Recent activity</h2>
      <ul className="feed">
        {recent.map((a) => (
          <li key={a.id}>
            <span className={`dot dot-${a.status}`} />
            <span><b>{a.patient_name}</b> with {a.doctor_name} — {STATUS_LABEL[a.status].toLowerCase()}</span>
          </li>
        ))}
        {recent.length === 0 && <li className="muted">Nothing yet.</li>}
      </ul>
    </section>
  );
}

function BookModal({ doctors, patients, onClose, onSaved }) {
  const [form, setForm] = useState({
    doctor_id: doctors[0]?.id ?? "",
    patient_id: patients[0]?.id ?? "",
    scheduled_at: defaultSlot(),
    reason: "",
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const ready = doctors.length > 0 && patients.length > 0;

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.bookAppointment({
        ...form,
        doctor_id: Number(form.doctor_id),
        patient_id: Number(form.patient_id),
      });
      onSaved();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal card" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>Book appointment</h2>
        {!ready && <p className="error">Add at least one doctor and one patient first.</p>}
        <label>Doctor
          <select value={form.doctor_id} onChange={set("doctor_id")} required>
            {doctors.map((d) => <option key={d.id} value={d.id}>{d.name} — {d.specialization}</option>)}
          </select>
        </label>
        <label>Patient
          <select value={form.patient_id} onChange={set("patient_id")} required>
            {patients.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
        <label>Date and time
          <input type="datetime-local" value={form.scheduled_at} onChange={set("scheduled_at")} required />
        </label>
        <label>Reason
          <input value={form.reason} onChange={set("reason")} maxLength={255} placeholder="e.g. Fever and cough" />
        </label>
        {error && <p className="error">{error}</p>}
        <div className="row-end">
          <button type="button" className="btn" onClick={onClose}>Close</button>
          <button className="btn primary" disabled={!ready || saving}>{saving ? "Booking…" : "Book"}</button>
        </div>
      </form>
    </div>
  );
}

function SimpleForm({ fields, onSubmit, submitLabel }) {
  const empty = Object.fromEntries(fields.map((f) => [f.name, ""]));
  const [values, setValues] = useState(empty);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      const payload = Object.fromEntries(
        fields.map((f) => [f.name, f.type === "number" ? (values[f.name] === "" ? null : Number(values[f.name])) : values[f.name]]),
      );
      await onSubmit(payload);
      setValues(empty);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      {fields.map((f) => (
        <input
          key={f.name}
          type={f.type || "text"}
          placeholder={f.label}
          value={values[f.name]}
          required={f.required}
          onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
        />
      ))}
      <button className="btn primary">{submitLabel}</button>
      {error && <p className="error full">{error}</p>}
    </form>
  );
}

function DoctorsView({ doctors, refresh, onError }) {
  return (
    <section className="card">
      <h2>Doctors</h2>
      <SimpleForm
        submitLabel="Add doctor"
        fields={[
          { name: "name", label: "Full name", required: true },
          { name: "specialization", label: "Specialization", required: true },
          { name: "room", label: "Room" },
        ]}
        onSubmit={async (p) => { await api.addDoctor(p); refresh(); }}
      />
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Specialization</th><th>Room</th><th /></tr></thead>
          <tbody>
            {doctors.map((d) => (
              <tr key={d.id}>
                <td>{d.name}</td><td>{d.specialization}</td><td>{d.room || "—"}</td>
                <td className="actions">
                  <button className="btn small danger" onClick={() => api.deleteDoctor(d.id).then(refresh).catch((e) => onError(e.message))}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PatientsView({ patients, refresh, onError }) {
  return (
    <section className="card">
      <h2>Patients</h2>
      <SimpleForm
        submitLabel="Add patient"
        fields={[
          { name: "name", label: "Full name", required: true },
          { name: "phone", label: "Phone", required: true },
          { name: "age", label: "Age", type: "number" },
        ]}
        onSubmit={async (p) => { await api.addPatient(p); refresh(); }}
      />
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Phone</th><th>Age</th><th /></tr></thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td><td>{p.phone}</td><td>{p.age ?? "—"}</td>
                <td className="actions">
                  <button className="btn small danger" onClick={() => api.deletePatient(p.id).then(refresh).catch((e) => onError(e.message))}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function App() {
  const [view, setView] = useState("dashboard");
  const [data, setData] = useState({ stats: null, queue: [], appointments: [], doctors: [], patients: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [showBook, setShowBook] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [stats, queue, appointments, doctors, patients] = await Promise.all([
        api.stats(), api.queue(), api.appointments(), api.doctors(), api.patients(),
      ]);
      setData({ stats, queue, appointments, doctors, patients });
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, [refresh]);

  const act = (id, status) =>
    api.updateAppointment(id, { status }).then(refresh).catch((e) => setError(e.message));

  const { stats } = data;
  return (
    <div className="layout">
      <aside className={`sidebar ${navOpen ? "open" : ""}`}>
        <div className="brand"><span className="logo">✚</span> ClinicQ</div>
        <nav>
          {NAV.map((n) => (
            <button
              key={n.id}
              className={`nav-item ${view === n.id ? "active" : ""}`}
              onClick={() => { setView(n.id); setNavOpen(false); }}
            >
              <span>{n.icon}</span> {n.label}
            </button>
          ))}
        </nav>
        <p className="sidebar-foot">Less waiting, better care</p>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setNavOpen(!navOpen)} aria-label="Toggle menu">☰</button>
          <div>
            <h1>{NAV.find((n) => n.id === view).label}</h1>
            <p className="muted">{new Date().toLocaleDateString([], { dateStyle: "full" })}</p>
          </div>
        </header>

        {error && <div className="banner">⚠ {error} — is the backend reachable?</div>}
        {loading && <p className="muted">Loading…</p>}

        {!loading && view === "dashboard" && (
          <>
            <div className="kpis">
              <Kpi label="Today's appointments" value={stats?.total_today} tone="teal" />
              <Kpi label="Waiting now" value={stats?.waiting} tone="amber" />
              <Kpi label="Completed" value={stats?.completed} tone="green" />
              <Kpi label="Cancelled" value={stats?.cancelled} tone="red" />
            </div>
            <div className="dash-grid">
              <QueueBoard queue={data.queue} />
              <Activity appointments={data.appointments} />
            </div>
            <AppointmentsTable
              appointments={data.appointments}
              filter={filter}
              setFilter={setFilter}
              onAction={act}
              onBook={() => setShowBook(true)}
            />
          </>
        )}
        {!loading && view === "doctors" && <DoctorsView doctors={data.doctors} refresh={refresh} onError={setError} />}
        {!loading && view === "patients" && <PatientsView patients={data.patients} refresh={refresh} onError={setError} />}
      </main>

      {showBook && (
        <BookModal
          doctors={data.doctors}
          patients={data.patients}
          onClose={() => setShowBook(false)}
          onSaved={() => { setShowBook(false); refresh(); }}
        />
      )}
    </div>
  );
}
