import { useState, useEffect, useCallback, useRef } from "react";
import { getDaySlots, bookSlot, requestNotify, initiatePayment, getMyCards } from "../../api/scheduling";

// ── constants ────────────────────────────────────────────────────────────────

const FA_DAYS = ["شنبه","یک‌شنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","جمعه"];
const EN_DAYS = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"];

const toDateStr = (d) =>
  `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;

const jsToLocal = (d) => { const py = d.getDay(); return py === 6 ? 0 : py + 1; };
const fmt = (t) => (t || "").slice(0, 5);

// Slot appearance — clean, refined design system tokens
const slotConfig = (status, mode) => {
  if (mode === "client") {
    if (status === "booked") return {
      bg: "rgba(239,68,68,0.06)", border: "rgba(239,68,68,0.2)", color: "#fca5a5",
      label: "رزرو شده", disabled: true,
    };
    if (status === "pending_payment") return {
      bg: "rgba(232,184,75,0.06)", border: "rgba(232,184,75,0.25)", color: "#E8B84B",
      label: "در انتظار پرداخت", disabled: false,
    };
    return {
      bg: "rgba(255,255,255,0.03)", border: "rgba(255,255,255,0.08)", color: "#F5F0E8",
      label: "آزاد", disabled: false,
    };
  }
  // therapist view
  if (status === "booked") return {
    bg: "rgba(45,212,172,0.06)", border: "rgba(45,212,172,0.2)", color: "#2DD4AC",
    label: "رزرو شده", disabled: true,
  };
  if (status === "pending_payment") return {
    bg: "rgba(232,184,75,0.06)", border: "rgba(232,184,75,0.25)", color: "#E8B84B",
    label: "در انتظار پرداخت", disabled: true,
  };
  return {
    bg: "rgba(255,255,255,0.03)", border: "rgba(255,255,255,0.08)", color: "rgba(245,240,232,0.5)",
    label: "آزاد", disabled: true,
  };
};

const LEGENDS_CLIENT = [
  { bg: "rgba(255,255,255,0.04)", border: "rgba(255,255,255,0.1)", label: "آزاد" },
  { bg: "rgba(232,184,75,0.08)", border: "rgba(232,184,75,0.25)", label: "در انتظار پرداخت" },
  { bg: "rgba(239,68,68,0.06)", border: "rgba(239,68,68,0.2)", label: "رزرو شده" },
];
const LEGENDS_THERAPIST = [
  { bg: "rgba(255,255,255,0.04)", border: "rgba(255,255,255,0.1)", label: "آزاد" },
  { bg: "rgba(232,184,75,0.08)", border: "rgba(232,184,75,0.25)", label: "در انتظار پرداخت" },
  { bg: "rgba(45,212,172,0.06)", border: "rgba(45,212,172,0.2)", label: "رزرو شده" },
];

// ── shared style tokens ───────────────────────────────────────────────────────
const S = {
  surface:        { background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14 },
  surfaceElevated:{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 20 },
  btn: {
    background: "#2DD4AC", color: "#0D0D0F", border: "none", borderRadius: 10,
    padding: "12px 24px", fontWeight: 600, fontSize: "0.875rem", cursor: "pointer",
    fontFamily: "inherit", transition: "all 0.2s", width: "100%",
  },
  btnGhost: {
    background: "transparent", color: "rgba(245,240,232,0.6)",
    border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10,
    padding: "10px 18px", fontSize: "0.875rem", cursor: "pointer",
    fontFamily: "inherit", transition: "all 0.2s",
  },
  label: { fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(245,240,232,0.4)", marginBottom: 10, display: "block" },
  error: { fontSize: "0.82rem", color: "#fca5a5", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: "12px 16px", marginBottom: 16 },
  row: { display: "grid", gridTemplateColumns: "80px 1fr", gap: 12, alignItems: "center", marginBottom: 8 },
  timeCell: { fontSize: "0.75rem", color: "rgba(245,240,232,0.4)", textAlign: "center", fontFamily: "monospace", direction: "ltr" },
};

// ── component ─────────────────────────────────────────────────────────────────
export default function ScheduleWidget({ therapistId, therapistName, mode, lang, sessionPrice }) {
  const isRtl = lang === "fa";
  const isTherapist = mode === "therapist";

  const [date, setDate]               = useState(new Date());
  const [slots, setSlots]             = useState([]);
  const [loading, setLoading]         = useState(true);
  const [selected, setSelected]       = useState(null);
  const [makeWeekly, setMakeWeekly]   = useState(false);
  const [step, setStep]               = useState("grid"); // grid | confirm | cards
  const [cards, setCards]             = useState([]);
  const [chosenCard, setChosenCard]   = useState(null);
  const [error, setError]             = useState("");
  const [notifySlot, setNotifySlot]   = useState(null);
  const [hovered, setHovered]         = useState(null);
  const wsRef = useRef(null);

  const dateStr = toDateStr(date);

  // fetch slots
  const fetchSlots = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const data = await getDaySlots(therapistId, dateStr);
      setSlots(data.slots || []);
    } catch (e) { setError(e.message || "خطا در بارگذاری"); }
    finally { setLoading(false); }
  }, [therapistId, dateStr]);

  useEffect(() => { fetchSlots(); }, [fetchSlots]);

  // WebSocket live updates
  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws/schedule/${therapistId}/${dateStr}/`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "slot_update") {
        setSlots(prev => prev.map(s => s.id === msg.slot.id ? { ...s, ...msg.slot } : s));
      }
    };
    return () => ws.close();
  }, [therapistId, dateStr]);

  const changeDay = (delta) => {
    const d = new Date(date);
    d.setDate(d.getDate() + delta);
    setDate(d);
    setSelected(null);
    setStep("grid");
  };

  const dayLabel = () => {
    const idx = jsToLocal(date);
    return isRtl ? FA_DAYS[idx] : EN_DAYS[idx];
  };

  const handleSlotClick = async (slot) => {
    if (isTherapist || slot.status === "booked") return;
    setSelected(slot);
    setMakeWeekly(false);
    setStep("confirm");
  };

  const handleConfirm = async () => {
    setError("");
    try {
      const booking = await bookSlot(selected.id, makeWeekly);
      window._pendingBooking = booking;
      const cardList = await getMyCards();
      setCards(cardList);
      setChosenCard(cardList.find(c => c.is_default)?.id || cardList[0]?.id || null);
      setStep("cards");
      fetchSlots();
    } catch (e) { setError(e.message); }
  };

  const handlePay = async () => {
    setError("");
    try {
      const result = await initiatePayment(window._pendingBooking.booking.id, chosenCard);
      window.location.href = result.redirect_url;
    } catch (e) { setError(e.message); }
  };

  const handleNotify = async (slot) => {
    try {
      await requestNotify(therapistId, jsToLocal(date), slot.start_time);
      window.gamanToast?.("🔔 اطلاع‌رسانی فعال شد");
      setNotifySlot(null);
    } catch (e) { setError(e.message); }
  };

  // ── CONFIRM STEP ────────────────────────────────────────────────────────────
  if (step === "confirm" && selected) return (
    <div style={{ padding: 32, fontFamily: "Vazirmatn, sans-serif", direction: "rtl" }}>
      <button onClick={() => setStep("grid")} style={{ ...S.btnGhost, width: "auto", marginBottom: 24, fontSize: "0.8rem" }}>
        {isRtl ? "← بازگشت" : "← Back"}
      </button>
      <span style={S.label}>تأیید رزرو</span>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F5F0E8", marginBottom: 20 }}>جزئیات جلسه</h2>

      <div style={{ ...S.surfaceElevated, padding: 20, marginBottom: 20 }}>
        {[
          ["درمانگر", therapistName],
          ["تاریخ", dateStr],
          ["ساعت", `${fmt(selected.start_time)} — ${fmt(selected.end_time)}`],
          ["مبلغ", `${(sessionPrice||0).toLocaleString()} ریال`],
        ].map(([k, v]) => (
          <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", fontSize: "0.875rem" }}>
            <span style={{ color: "rgba(245,240,232,0.4)" }}>{k}</span>
            <span style={{ color: "#F5F0E8", fontWeight: 600, direction: "ltr" }}>{v}</span>
          </div>
        ))}
      </div>

      {/* Weekly toggle */}
      <div style={{ ...S.surface, padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: "0.875rem", color: "#F5F0E8", fontWeight: 600 }}>رزرو ثابت هفتگی</div>
          <div style={{ fontSize: "0.75rem", color: "rgba(245,240,232,0.4)", marginTop: 4 }}>این زمان همیشه برای شما حفظ می‌شود</div>
        </div>
        <button onClick={() => setMakeWeekly(!makeWeekly)}
          style={{ width: 44, height: 24, borderRadius: 12, background: makeWeekly ? "#2DD4AC" : "rgba(255,255,255,0.1)", border: "none", cursor: "pointer", position: "relative", transition: "background 0.2s" }}>
          <span style={{ position: "absolute", top: 2, width: 20, height: 20, background: "#0D0D0F", borderRadius: "50%", transition: "all 0.2s",
            [isRtl ? "right" : "left"]: makeWeekly ? (isRtl ? 2 : 22) : (isRtl ? 22 : 2) }}></span>
        </button>
      </div>

      {error && <div style={S.error}>{error}</div>}
      <button onClick={handleConfirm} style={S.btn}>ادامه به انتخاب کارت</button>
    </div>
  );

  // ── CARDS STEP ──────────────────────────────────────────────────────────────
  if (step === "cards") return (
    <div style={{ padding: 32, fontFamily: "Vazirmatn, sans-serif", direction: "rtl" }}>
      <button onClick={() => setStep("confirm")} style={{ ...S.btnGhost, width: "auto", marginBottom: 24, fontSize: "0.8rem" }}>
        {isRtl ? "← بازگشت" : "← Back"}
      </button>
      <span style={S.label}>پرداخت</span>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F5F0E8", marginBottom: 6 }}>انتخاب کارت</h2>
      <p style={{ fontSize: "0.85rem", color: "rgba(245,240,232,0.4)", marginBottom: 24 }}>کارت پرداخت را انتخاب کنید</p>

      <div style={{ marginBottom: 20 }}>
        {cards.map(card => (
          <button key={card.id} onClick={() => setChosenCard(card.id)}
            style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "14px 18px", borderRadius: 12, marginBottom: 8, cursor: "pointer", fontFamily: "inherit",
              background: chosenCard === card.id ? "rgba(45,212,172,0.08)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${chosenCard === card.id ? "rgba(45,212,172,0.3)" : "rgba(255,255,255,0.08)"}`,
              transition: "all 0.2s",
            }}>
            <span style={{ fontFamily: "monospace", color: "#F5F0E8", fontSize: "0.875rem", direction: "ltr" }}>{card.masked_pan}</span>
            <span style={{ fontSize: "0.75rem", color: "rgba(245,240,232,0.4)" }}>{card.bank_name}</span>
            {card.is_default && <span style={{ fontSize: "0.7rem", padding: "2px 10px", borderRadius: 100, background: "rgba(45,212,172,0.12)", color: "#2DD4AC", border: "1px solid rgba(45,212,172,0.25)" }}>پیش‌فرض</span>}
          </button>
        ))}
        {cards.length === 0 && (
          <p style={{ color: "rgba(245,240,232,0.4)", fontSize: "0.85rem", textAlign: "center", padding: "16px 0" }}>
            با کارت جدید پرداخت می‌کنید — اطلاعات در درگاه شاپرک وارد می‌شود.
          </p>
        )}
      </div>

      {error && <div style={S.error}>{error}</div>}
      <button onClick={handlePay} style={S.btn}>پرداخت از طریق درگاه شاپرک</button>
      <p style={{ textAlign: "center", fontSize: "0.75rem", color: "rgba(245,240,232,0.3)", marginTop: 12 }}>پس از کلیک به درگاه امن شاپرک منتقل می‌شوید</p>
    </div>
  );

  // ── MAIN GRID ────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: 32, fontFamily: "Vazirmatn, sans-serif", direction: "rtl", color: "#F5F0E8" }}>

      {/* Day navigation */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, paddingBottom: 24, borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <button onClick={() => changeDay(isRtl ? 1 : -1)}
          style={{ width: 38, height: 38, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#F5F0E8", cursor: "pointer", fontSize: "1.1rem", transition: "all 0.2s" }}>
          {isRtl ? "›" : "‹"}
        </button>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontWeight: 700, fontSize: "1rem" }}>{dayLabel()}</div>
          <div style={{ fontSize: "0.8rem", color: "rgba(245,240,232,0.4)", marginTop: 4, direction: "ltr" }}>{dateStr}</div>
        </div>
        <button onClick={() => changeDay(isRtl ? -1 : 1)}
          style={{ width: 38, height: 38, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#F5F0E8", cursor: "pointer", fontSize: "1.1rem", transition: "all 0.2s" }}>
          {isRtl ? "‹" : "›"}
        </button>
      </div>

      {/* Slots */}
      {loading ? (
        <div>{[...Array(7)].map((_,i) => (
          <div key={i} style={{ ...S.row }}>
            <div style={{ height: 14, borderRadius: 4, background: "rgba(255,255,255,0.04)" }}></div>
            <div style={{ height: 52, borderRadius: 12, background: "rgba(255,255,255,0.04)", opacity: 1 - i * 0.1 }}></div>
          </div>
        ))}</div>
      ) : slots.length === 0 ? (
        <div style={{ textAlign: "center", color: "rgba(245,240,232,0.4)", padding: "48px 0", fontSize: "0.875rem" }}>این روز وقت آزاد ندارد.</div>
      ) : (
        <div>
          {slots.map(slot => {
            const cfg = slotConfig(slot.status, mode);
            const isSelected = selected?.id === slot.id && step === "confirm";
            return (
              <div key={slot.id} style={S.row}>
                <div style={S.timeCell}>{fmt(slot.start_time)}<br/><span style={{ fontSize: "0.6rem", opacity: 0.4 }}>—</span><br/>{fmt(slot.end_time)}</div>
                <div style={{ position: "relative" }}>
                  <button
                    disabled={cfg.disabled}
                    onClick={() => !cfg.disabled && handleSlotClick(slot)}
                    onMouseEnter={() => setHovered(slot.id)}
                    onMouseLeave={() => setHovered(null)}
                    style={{
                      width: "100%", textAlign: "right", padding: "14px 16px", borderRadius: 12,
                      background: isSelected ? "rgba(45,212,172,0.1)" : cfg.bg,
                      border: `1px solid ${isSelected ? "rgba(45,212,172,0.3)" : cfg.border}`,
                      color: cfg.color, cursor: cfg.disabled ? "default" : "pointer",
                      fontSize: "0.875rem", fontWeight: 500, fontFamily: "inherit",
                      transition: "all 0.2s",
                      boxShadow: isSelected ? "0 0 0 2px rgba(45,212,172,0.15)" : "none",
                    }}>
                    {isTherapist && slot.patient_name ? slot.patient_name : cfg.label}
                  </button>

                  {/* Therapist hover: click patient name → notes */}
                  {isTherapist && hovered === slot.id && slot.patient_name && (
                    <div style={{ position: "absolute", bottom: "calc(100% + 6px)", right: 0, background: "#141418", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, padding: "8px 14px", fontSize: "0.78rem", whiteSpace: "nowrap", zIndex: 20, boxShadow: "0 12px 32px rgba(0,0,0,0.4)" }}>
                      <span style={{ color: "rgba(245,240,232,0.4)" }}>مراجع: </span>
                      <span style={{ color: "#2DD4AC", cursor: "pointer" }}>{slot.patient_name}</span>
                    </div>
                  )}

                  {/* Notify-me bell for taken slots */}
                  {!isTherapist && slot.status === "booked" && hovered === slot.id && (
                    <button onClick={() => setNotifySlot(slot)}
                      style={{ position: "absolute", top: "50%", transform: "translateY(-50%)", [isRtl ? "left" : "right"]: 10, background: "none", border: "none", cursor: "pointer", color: "rgba(245,240,232,0.4)", fontSize: "0.9rem", padding: "4px 6px", borderRadius: 6, transition: "color 0.2s" }}
                      title="اطلاع‌رسانی اگر آزاد شد">
                      🔔
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Legend */}
      <div style={{ display: "flex", gap: 20, marginTop: 24, flexWrap: "wrap", paddingTop: 20, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        {(isTherapist ? LEGENDS_THERAPIST : LEGENDS_CLIENT).map(item => (
          <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: "0.75rem", color: "rgba(245,240,232,0.4)" }}>
            <span style={{ width: 14, height: 14, borderRadius: 4, background: item.bg, border: `1px solid ${item.border}`, flexShrink: 0 }}></span>
            {item.label}
          </div>
        ))}
      </div>

      {error && <div style={{ ...S.error, marginTop: 16 }}>{error}</div>}

      {/* Notify-me modal */}
      {notifySlot && (
        <div onClick={() => setNotifySlot(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 24, backdropFilter: "blur(4px)" }}>
          <div onClick={e => e.stopPropagation()} style={{ ...S.surfaceElevated, padding: 32, maxWidth: 380, width: "100%", fontFamily: "Vazirmatn, sans-serif", direction: "rtl", boxShadow: "0 24px 48px rgba(0,0,0,0.5)" }}>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#F5F0E8", marginBottom: 10 }}>🔔 اطلاع‌رسانی</div>
            <p style={{ fontSize: "0.85rem", color: "rgba(245,240,232,0.6)", lineHeight: 1.8, marginBottom: 24 }}>
              اگر این زمان آزاد شود، یک اعلان به مرورگر شما ارسال می‌شود — حتی اگر تب بسته باشد.
            </p>
            <button onClick={() => handleNotify(notifySlot)} style={{ ...S.btn, marginBottom: 8 }}>فعال‌سازی اطلاع‌رسانی</button>
            <button onClick={() => setNotifySlot(null)} style={{ ...S.btnGhost, width: "100%", textAlign: "center" }}>انصراف</button>
          </div>
        </div>
      )}
    </div>
  );
}
