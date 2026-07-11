import React from "react";
import { createRoot } from "react-dom/client";
import TherapistNotesWidget from "./TherapistNotesWidget";

const el = document.getElementById("notes-widget-root");
if (el) {
  createRoot(el).render(
    <TherapistNotesWidget
      clientId={el.dataset.clientId}
      clientName={el.dataset.clientName}
      bookingId={el.dataset.bookingId || null}
    />
  );
}
