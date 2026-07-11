import { useState, useEffect } from "react";
import { getClientNotes, saveNote, updateNote } from "../../api/scheduling";

const S = {
  glass: { background: "rgba(255,255,255,0.055)", border: "1px solid rgba(255,255,255,0.10)", borderRadius: 14 },
  label: { fontSize: "0.7rem", letterSpacing: "2px", textTransform: "uppercase", color: "rgba(245,240,232,0.3)", marginBottom: 10, display: "block" },
  textarea: { width: "100%", background: "transparent", border: "none", outline: "none", color: "#F5F0E8", fontSize: "0.9rem", lineHeight: 1.9, resize: "none", fontFamily: "Vazirmatn, sans-serif", placeholder: "rgba(245,240,232,0.2)" },
  btn: { background: "#2DD4AC", color: "#0D0D0F", border: "none", borderRadius: 10, padding: "10px 22px", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer", fontFamily: "inherit" },
  btnGhost: { background: "transparent", color: "rgba(245,240,232,0.5)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "9px 18px", fontSize: "0.85rem", cursor: "pointer", fontFamily: "inherit" },
};

export default function TherapistNotesWidget({ clientId, clientName, bookingId }) {
  const [notes, setNotes]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft]     = useState("");
  const [saving, setSaving]   = useState(false);
  const [editId, setEditId]   = useState(null);
  const [error, setError]     = useState("");

  useEffect(() => {
    if (!clientId) return;
    getClientNotes(clientId)
      .then(setNotes)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [clientId]);

  const handleSave = async () => {
    if (!draft.trim()) return;
    setSaving(true); setError("");
    try {
      if (editId) {
        const updated = await updateNote(editId, draft);
        setNotes(prev => prev.map(n => n.id === editId ? updated : n));
        setEditId(null);
      } else {
        const created = await saveNote(clientId, draft, bookingId);
        setNotes(prev => [created, ...prev]);
      }
      setDraft("");
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };

  return (
    <div style={{ padding: 28, fontFamily: "Vazirmatn, sans-serif", direction: "rtl", color: "#F5F0E8" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <span style={S.label}>یادداشت‌های جلسه</span>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700 }}>{clientName || "مراجع"}</h2>
        </div>
        {editId && (
          <button onClick={() => { setEditId(null); setDraft(""); }} style={{ ...S.btnGhost, fontSize: "0.75rem" }}>لغو ویرایش</button>
        )}
      </div>

      {/* Editor */}
      <div style={{ ...S.glass, padding: 20, marginBottom: 20 }}>
        <textarea
          rows={5} value={draft} onChange={e => setDraft(e.target.value)}
          placeholder="یادداشت این جلسه را اینجا بنویسید…"
          style={S.textarea}
        />
        {error && <div style={{ fontSize: "0.78rem", color: "#fca5a5", marginTop: 8 }}>{error}</div>}
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12, borderTop: "1px solid rgba(255,255,255,0.07)", paddingTop: 12 }}>
          <button onClick={handleSave} disabled={saving || !draft.trim()} style={{ ...S.btn, opacity: saving || !draft.trim() ? 0.5 : 1 }}>
            {saving ? "ذخیره…" : editId ? "به‌روزرسانی" : "ذخیره یادداشت"}
          </button>
        </div>
      </div>

      {/* Notes list */}
      {loading ? (
        [1,2,3].map(i => <div key={i} style={{ height: 80, borderRadius: 14, background: "rgba(255,255,255,0.04)", marginBottom: 10 }}></div>)
      ) : notes.length === 0 ? (
        <div style={{ textAlign: "center", color: "rgba(245,240,232,0.25)", fontSize: "0.875rem", padding: "32px 0" }}>هنوز یادداشتی ثبت نشده است.</div>
      ) : (
        notes.map(note => (
          <div key={note.id} style={{ ...S.glass, padding: 18, marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <span style={{ fontSize: "0.75rem", color: "rgba(245,240,232,0.3)", direction: "ltr" }}>{note.created_at?.slice(0,10)}</span>
              <button onClick={() => { setEditId(note.id); setDraft(note.content); }}
                style={{ background: "none", border: "none", color: "rgba(245,240,232,0.35)", fontSize: "0.75rem", cursor: "pointer", fontFamily: "inherit" }}>
                ویرایش
              </button>
            </div>
            <p style={{ fontSize: "0.875rem", lineHeight: 1.9, color: "rgba(245,240,232,0.65)", whiteSpace: "pre-wrap" }}>{note.content}</p>
          </div>
        ))
      )}
    </div>
  );
}
