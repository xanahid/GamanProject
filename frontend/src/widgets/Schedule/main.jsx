import React from "react";
import { createRoot } from "react-dom/client";
import ScheduleWidget from "./ScheduleWidget";

const el = document.getElementById("schedule-widget-root");
if (el) {
  const root = createRoot(el);
  root.render(
    <ScheduleWidget
      therapistId={el.dataset.therapistId}
      therapistName={el.dataset.therapistName}
      mode={el.dataset.mode}          // "client" | "therapist"
      lang={el.dataset.lang || "fa"}
      sessionPrice={parseInt(el.dataset.sessionPrice || "0", 10)}
    />
  );
}
