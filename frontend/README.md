# call insight — frontend

Call quality control UI on top of the API in the repository root: a filtered call list, a call
report with quotes, statistics by operator, checklist item and day, team management and API keys.

## Run

```bash
npm install
npm run dev        # http://localhost:3100
```

The API must be running on `http://localhost:8090`:

```bash
docker compose up -d postgres redis rabbitmq
python -m uvicorn app.main:app --port 8090
```

The API address comes from `NEXT_PUBLIC_API_URL` (see `.env.example`). The API must allow the
frontend origin through `CORS_ORIGINS` in the backend `.env`; the default is `http://localhost:3100`.

In production the frontend runs from its own image (`frontend/Dockerfile`, Next in standalone
mode) as the `frontend` service of the root compose file — see Deployment in the root README.
`NEXT_PUBLIC_API_URL` is a build argument there, because Next inlines it into the bundle.

## Demo

With `DEMO_ENABLED=true` on the backend and demo data seeded
(`python -m app.fixtures.demo demo --create "Demo Company" --login`), the login page shows a
demo button. It opens a filled company in read-only mode without registration.

## Structure

```
app/
  layout.tsx            shell: AuthProvider → navigation → AuthGate → page
  globals.css           CSS variable tokens, tables, forms, chart, responsive navigation
  page.tsx              overview: tiles, daily chart, operators and checklist items
  calls/page.tsx        calls: filters, sorting, pagination
  calls/[id]/page.tsx   call report: checklist, quotes, score confirmation
  login, register, verify, invite    public auth pages
  cabinet/page.tsx      profile, company and what the role can do
  team/page.tsx         team: invitations, roles, access
  keys/page.tsx         API keys: shown once, revocation (owner only)
components/
  auth-provider.tsx     current user, redirects, AuthGate, demo banner
  nav.tsx               role-aware navigation
  ui.tsx                Card, Badge, Button, Field, SortHeader, AuthCard, …
  daily-chart.tsx       per-day calls and average score
  status-badge.tsx      call status → colour and label
lib/
  api.ts                typed client, the only place that knows about HTTP
  auth.ts               token storage
  permissions.ts        mirror of backend roles, used only to show or hide UI
  limits.ts             mirror of app/core/limits.py
  redirect.ts           safeNext, protection against open redirects
  use-sort.ts           table sort state
  theme.ts, format.ts   colours and formatting
```

## Decisions

- **Response types are written by hand** in `lib/api.ts` and follow the backend schemas.
  `Numeric` values arrive as **strings** (`"100.00"`) and are converted by `num()`, not by
  `Number()` scattered across components.
- **Pagination is server-side.** A page requests `limit`/`offset` and shows `total`, so the client
  never receives more rows than it displays.
- **Filters apply on a button**, not on every keystroke, so typing does not query the database.
- **Overview tables sort locally**: they already hold every row for the period, so changing the
  sort does not refetch.
- **Quote highlighting**: hovering a checklist item finds its quote in the transcript lines
  (`markQuote`), case-insensitive, ignoring very short fragments.
- **Score confirmation** updates local state from the `PATCH` response without reloading the report.
- **Data loading** uses a cancellable effect (`alive`) so a stale response never overwrites
  fresh state when filters change quickly.
- **The token lives in `localStorage`** and is read through `useSyncExternalStore`. A deliberate
  trade-off: simple, but exposed to XSS. The stronger option is an `httpOnly` cookie behind Next.
- **Until hydration finishes the status is "checking", not "guest"**, otherwise the first render
  sees the server value (`null`) and sends a signed-in user to the login page.
- **Errors are told apart by the backend `code`** (`EmailNotVerified`), not by message text.
- **Frontend permissions only hide buttons.** The API enforces access.

## Not yet

- Uploading audio from the UI (only `POST /calls` in Swagger)
- Live status updates while a call is processed; the page has to be refreshed
- Managing the company checklist from the UI
