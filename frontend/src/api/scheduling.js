import { apiFetch } from "./client";

export const getMyRoute = () =>
  apiFetch("/api/v1/scheduling/my-route/");

export const getDaySlots = (therapistId, date) =>
  apiFetch(`/api/v1/scheduling/therapists/${therapistId}/day/?date=${date}`);

export const bookSlot = (slotId, makeWeekly = false) =>
  apiFetch("/api/v1/scheduling/book/", {
    method: "POST",
    body: { slot_id: slotId, make_weekly_recurring: makeWeekly },
  });

export const cancelBooking = (bookingId) =>
  apiFetch(`/api/v1/scheduling/bookings/${bookingId}/cancel/`, { method: "POST" });

export const requestNotify = (therapistId, weekday, startTime) =>
  apiFetch("/api/v1/scheduling/notify-me/", {
    method: "POST",
    body: { therapist: therapistId, weekday, start_time: startTime },
  });

export const subscribePush = (subscription) =>
  apiFetch("/api/v1/scheduling/push/subscribe/", {
    method: "POST",
    body: {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey("p256dh")))),
        auth:   btoa(String.fromCharCode(...new Uint8Array(subscription.getKey("auth")))),
      },
    },
  });

export const initiatePayment = (bookingId, savedCardId = null) =>
  apiFetch("/api/v1/payments/initiate/", {
    method: "POST",
    body: { booking_id: bookingId, ...(savedCardId ? { saved_card_id: savedCardId } : {}) },
  });

export const getMyCards = () =>
  apiFetch("/api/v1/payments/checkout-cards/");

export const getClientNotes = (clientId) =>
  apiFetch(`/api/v1/notes/clients/${clientId}/`);

export const saveNote = (clientId, content, bookingId = null) =>
  apiFetch(`/api/v1/notes/clients/${clientId}/`, {
    method: "POST",
    body: { content, ...(bookingId ? { booking: bookingId } : {}) },
  });

export const updateNote = (noteId, content) =>
  apiFetch(`/api/v1/notes/${noteId}/`, {
    method: "PATCH",
    body: { content },
  });
