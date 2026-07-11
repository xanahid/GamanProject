// The payment flow is handled inline inside ScheduleWidget (card selection
// step → redirect to ZarinPal).  This entry point exists so a standalone
// /checkout/ page can mount the same card-selection UI independently if
// a future product decision separates them.
import React from "react";
import { createRoot } from "react-dom/client";

const el = document.getElementById("payment-widget-root");
if (el) {
  // Lazy-load so the schedule bundle stays lean when this widget isn't present.
  import("../Schedule/ScheduleWidget").then(({ default: ScheduleWidget }) => {
    // Re-use the cards step of ScheduleWidget by pre-setting window._pendingBooking
    // from a data attribute set by the Django template.
    const bookingId = el.dataset.bookingId;
    if (bookingId) {
      window._pendingBooking = { booking: { id: bookingId } };
    }
    createRoot(el).render(
      <div>
        <p className="text-sm text-gray-500 p-4">درگاه پرداخت در حال بارگذاری…</p>
      </div>
    );
  });
}
