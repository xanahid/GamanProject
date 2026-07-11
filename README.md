# گمان — Gaman Therapy Booking Platform

A full-stack psychotherapy session booking platform for **Gaman Institute** (مرکز روان‌درمانی گمان).

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Real-time | Django Channels 4 (WebSockets) + Redis |
| Task queue | Celery + Celery Beat + Redis |
| Database | PostgreSQL 16 |
| Frontend shell | Django templates + Tailwind CSS (CDN) |
| Interactive widgets | React 18 (Vite multi-entry build) |
| Payment gateway | ZarinPal (Shaparak) |
| Server | Daphne (ASGI — handles HTTP + WS) |
| Container | Docker + Docker Compose |

---

## Quick Start (Docker — recommended)

### Prerequisites
- Docker ≥ 24
- Docker Compose ≥ 2.20

### 1 — Clone and configure

```bash
git clone <repo-url> gaman
cd gaman
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set DJANGO_SECRET_KEY
```

### 2 — Build and start everything

```bash
docker compose up --build
```

This single command:
- Starts PostgreSQL and Redis
- Runs Django migrations
- Seeds demo data (therapists, a client account, sample articles)
- Registers Celery Beat periodic tasks
- Starts Daphne (web + WebSockets on port 8000)
- Starts Celery worker + beat
- Builds the React widget bundles (Vite) and copies them to Django's static directory

### 3 — Open the site

```
http://localhost:8000
```

### Demo accounts (all passwords: `ChangeMe123!`)

| Username | Role | Notes |
|---|---|---|
| `sarah.akbarzadeh` | Therapist + Staff (Head) | Django admin access at `/admin/` |
| `ali.mohammadi` | Therapist | Schema therapy |
| `mina.rezaei` | Therapist | CBT + couples |
| `reza.karimi` | Therapist | Adolescents |
| `client.demo` | Client | New client (no intake session yet) |

---

## Running without Docker (development)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# You need a running PostgreSQL and Redis — update .env DATABASE_URL and REDIS_URL
cp .env.example .env  # edit as needed

python manage.py migrate
python manage.py setup_periodic_tasks
python manage.py seed_demo_data

# Terminal 1 — Django + Channels
python manage.py runserver          # or: daphne config.asgi:application

# Terminal 2 — Celery worker
celery -A config worker -l info

# Terminal 3 — Celery beat (periodic tasks)
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend (React widgets)

```bash
cd frontend
npm install

# Development — Vite dev server proxies API calls to Django on :8000
npm run dev

# Production build — outputs to backend/static/js/widgets/
npm run build
```

---

## Architecture

```
gaman/
├── backend/
│   ├── config/          # settings, urls, asgi, celery
│   ├── apps/
│   │   ├── accounts/    # User model, ClientProfile, SavedCard, auth API
│   │   ├── therapists/  # TherapistProfile, Department, Specialty
│   │   ├── scheduling/  # WeeklyAvailability, SessionSlot, Booking, RecurringBooking, NotifyRequest
│   │   ├── payments/    # Payment, RefundRequest, ZarinPal gateway client
│   │   ├── content/     # Article (slideshow), TherapyMethod, HomepageSection
│   │   ├── notes/       # SessionNote (therapist private notes per client/session)
│   │   ├── payroll/     # TherapistCancellation, MonthlyPayrollSummary
│   │   ├── realtime/    # Channels consumers, Web Push tasks
│   │   └── core/        # Base models, middleware, context processors, homepage view
│   ├── templates/       # Django HTML templates (RTL Farsi default, LTR English via i18n)
│   └── static/          # base.css, toast.js, + React widget bundles (built by Vite)
│
└── frontend/
    └── src/widgets/
        ├── Schedule/         # Day-grid booking widget (client + therapist views)
        ├── Payment/          # Card selection → ZarinPal redirect
        ├── TherapistNotes/   # Per-client, per-session note editor
        └── AdminDashboard/   # Dr. Akbarzadeh's therapist hours + cancellation review
```

---

## Key Business Logic

### Booking state machine

```
free (white) → pending_payment (yellow, 15-min hold) → booked (red/green)
```

- Client view: white = free, yellow = soft-hold (recurring or checkout in progress), red = taken
- Therapist view: white = free, yellow = same, **green** = paid & confirmed

### First-session routing

A brand-new client is **always** routed to Dr. Sarah Akbarzadeh's schedule for their intake session, regardless of which therapist they clicked. After she marks `client_profile.has_completed_intake_session = True` and sets `recommended_therapist`, the client can book their recommended therapist directly.

### Weekly recurring bookings

Enabling "رزرو ثابت هفتگی" creates a `RecurringBooking` row. Future `SessionSlot` rows for that weekday+time are pre-marked yellow (`is_recurring_hold=True`) by the nightly slot-generation task. The client still pays week-by-week; the yellow just signals "this time is spoken for."

### Cancellation policies

| Who cancels | When | Outcome |
|---|---|---|
| Client | ≥ 24h before | Full refund queued |
| Client | < 24h before | No refund |
| Therapist | ≥ 4 days before | Salary unaffected (default) |
| Therapist | < 4 days before | Salary deduction (subject to Dr. Akbarzadeh's review) |

All therapist cancellations create a `TherapistCancellation` record reviewed via Django Admin → Payroll → Therapist Cancellations. Dr. Akbarzadeh has the final call on every case.

### Payment flow (ZarinPal)

1. Client selects a slot → slot gets a 15-minute hold
2. Client picks a saved card (or new card) → POST `/api/v1/payments/initiate/`
3. Server calls ZarinPal PaymentRequest → returns `authority`
4. Browser redirects to `https://payment.zarinpal.com/pg/StartPay/{authority}`
5. ZarinPal redirects back to `/payments/verify/?Authority=...&Status=OK`
6. Server calls ZarinPal PaymentVerification **server-to-server** — only on a `100` or `101` code does the slot become `booked`

Raw card data **never touches our server** — ZarinPal's hosted page handles PCI compliance.

### Real-time (Channels + Web Push)

- Every open schedule-grid tab subscribes to `ws://.../ws/schedule/{therapist_id}/{date}/`
- When any slot changes status, the Channels consumer broadcasts to that group → instant grid update
- "Notify me if this opens up" stores a `NotifyRequest`; when a slot becomes free, `resolve_notify_requests_for_slot()` sends both an in-app WS notification and a browser Web Push notification

---

## Django Admin (Dr. Akbarzadeh's powers)

Access at `/admin/` — log in with `sarah.akbarzadeh` / `ChangeMe123!`

| Admin section | What she can do |
|---|---|
| **Content → Articles** | Add/remove homepage slideshow articles |
| **Content → Homepage Sections** | Add sections with custom background colour, heading, body, CTA |
| **Therapists → Therapist Profiles** | View profiles, see sessions-last-6-months count per therapist |
| **Scheduling → Session Notes** | Read notes from all therapists |
| **Scheduling → Bookings** | Full booking history, see who cancelled |
| **Payroll → Therapist Cancellations** | Run "approve no deduction" or "apply full deduction" bulk actions |
| **Payroll → Monthly Payroll Summaries** | Monthly payout overview per therapist |

---

## ZarinPal setup (go live)

1. Create a merchant account at [zarinpal.com](https://zarinpal.com)
2. Set `ZARINPAL_MERCHANT_ID` in `.env` to your real merchant ID
3. Set `ZARINPAL_SANDBOX=False`
4. Set `ZARINPAL_CALLBACK_URL` to your production domain, e.g. `https://gaman.ir/payments/verify/`

---

## Web Push setup (optional)

```bash
python manage.py generate_vapid_keys
# Paste the output into .env as VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY
```

---

## Language switching

The site defaults to Farsi (RTL). Users switch to English via the language toggle button in the nav, which POSTs to Django's built-in `set_language` view. All user-facing strings are wrapped in `{% trans %}` / `gettext()` — run `django-admin makemessages -l en` to generate the English translation file and fill in `backend/locale/en/LC_MESSAGES/django.po`.
