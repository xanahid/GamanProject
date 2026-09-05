import { useState, useEffect } from "react";
import { apiFetch } from "../../api/client";

const S = {
  surface: { background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16 },
  label: { fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(245,240,232,0.4)", marginBottom: 12, display: "block" },
  row: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,0.05)", fontSize: "0.875rem" },
};

export default function AdminDashboard() {
  const [therapists, setTherapists] = useState([]);
  const [selected,   setSelected]   = useState(null);
  const [summaries,  setSummaries]  = useState([]);
  const [cancels,    setCancels]    = useState([]);
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    apiFetch("/api/v1/therapists/")
      .then(setTherapists)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selected) return;
    Promise.all([apiFetch("/api/v1/payroll/my-summaries/"), apiFetch("/api/v1/payroll/my-cancellations/")])
      .then(([s, c]) => { setSummaries(s); setCancels(c); })
      .catch(() => {});
  }, [selected]);

  if (loading) return <div style={{ padding: 32, color: "rgba(245,240,232,0.4)", fontFamily: "Vazirmatn, sans-serif" }}>در حال بارگذاری…</div>;

  return (
    <div style={{ padding: 28, fontFamily: "Vazirmatn, sans-serif", direction: "rtl", color: "#F5F0E8" }}>
      <span style={S.label}>داشبورد مدیریتی</span>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: 24 }}>دکتر اکبرزاده</h2>

      {/* Therapist selector */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10, marginBottom: 28 }}>
        {therapists.map(t => (
          <button key={t.id} onClick={() => setSelected(t)}
            style={{ padding: "12px 14px", borderRadius: 12, textAlign: "right", fontFamily: "inherit", cursor: "pointer", transition: "all 0.2s",
              background: selected?.id === t.id ? "rgba(45,212,172,0.08)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${selected?.id === t.id ? "rgba(45,212,172,0.3)" : "rgba(255,255,255,0.08)"}`,
              color: "#F5F0E8" }}>
            <div style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: 3 }}>{t.name}</div>
            <div style={{ fontSize: "0.75rem", color: "rgba(245,240,232,0.4)" }}>{t.years_active} سال سابقه</div>
          </button>
        ))}
      </div>

      {selected && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Summaries */}
          <div style={{ ...S.surface, padding: 22 }}>
            <span style={S.label}>جلسات ۶ ماه اخیر</span>
            {summaries.length === 0
              ? <p style={{ color: "rgba(245,240,232,0.4)", fontSize: "0.85rem" }}>داده‌ای یافت نشد.</p>
              : summaries.map(s => (
                <div key={`${s.year}-${s.month}`} style={S.row}>
                  <span style={{ color: "rgba(245,240,232,0.5)", direction: "ltr" }}>{s.year}/{String(s.month).padStart(2,"0")}</span>
                  <span>{s.completed_sessions} جلسه</span>
                  <span style={{ direction: "ltr" }}>{Number(s.total_hours).toFixed(1)} ساعت</span>
                  <span style={{ fontSize: "0.75rem", color: s.total_deductions_rials > 0 ? "#fca5a5" : "#2DD4AC" }}>
                    {s.total_deductions_rials > 0 ? `−${Number(s.total_deductions_rials).toLocaleString()} ریال` : "بدون کسر"}
                  </span>
                </div>
              ))
            }
          </div>

          {/* Pending cancellations */}
          {cancels.filter(c => !c.decided_by_head).length > 0 && (
            <div style={{ ...S.surface, padding: 22 }}>
              <span style={S.label}>لغوهای نیازمند تصمیم</span>
              {cancels.filter(c => !c.decided_by_head).map(c => (
                <div key={c.id} style={S.row}>
                  <span style={{ direction: "ltr", color: "rgba(245,240,232,0.6)" }}>{Number(c.days_before_session).toFixed(1)} روز قبل</span>
                  <span style={{ fontSize: "0.72rem", padding: "3px 10px", borderRadius: 100,
                    background: c.salary_safe ? "rgba(45,212,172,0.08)" : "rgba(239,68,68,0.08)",
                    border: `1px solid ${c.salary_safe ? "rgba(45,212,172,0.2)" : "rgba(239,68,68,0.2)"}`,
                    color: c.salary_safe ? "#2DD4AC" : "#fca5a5" }}>
                    {c.salary_safe ? "ایمن" : "نیاز به کسر"}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "rgba(245,240,232,0.4)" }}>از Admin Panel تصمیم بگیرید</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
