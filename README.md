# CivicEye AI+ (team CivicNova)

Frontend + Flask backend, fully wired together. No mock data remains —
every screen reads and writes through the real backend described in
`backend/API_CONTRACT.md`.

## Run it

**1. Backend**
```
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python3 app.py
```
Starts on `http://localhost:5000`. First run auto-creates `civiceye.db`
(SQLite) and loads `data/education.csv` into it.

**2. Frontend**
```
cd frontend
python3 -m http.server 8080
```
Open `http://localhost:8080/index.html`. (Any static server works — the
frontend is plain HTML/CSS/JS, no build step.)

If you serve the frontend from a different host/port, set
`window.CIVICEYE_API_BASE_URL = "http://your-backend-host:5000"` in a
`<script>` tag before `js/api.js` loads on every page, or edit
`CONFIG.BASE_URL` at the top of `frontend/js/api.js`.

## What's connected

Every one of these is a real network call to Flask + SQLite, verified
with an automated Playwright run (signup → dashboards → create/update
an intervention → reload the page → data still there):

| Frontend | Backend |
|---|---|
| Login / signup | `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me` |
| Citizen Mode | `GET /api/citizen/statistics`, `GET /api/citizen/problems` |
| Social Radar | `GET /api/social/patterns` |
| Relationships | `GET /api/social/relationships` |
| Impact Analyzer | `GET /api/social/impact` |
| Future Scanner | `GET /api/social/trends` |
| What-If Lab | `POST /api/social/simulation` |
| Action Center | `GET/POST /api/actions`, `PUT /api/actions/{id}` |
| Platform Admin | `GET /api/admin/users`, `PATCH /api/admin/users/{id}/role` |
| Data & Intelligence Admin | `GET /api/admin/dataset/summary`, `POST /api/admin/dataset/reload`, `GET/POST /api/admin/civic-items` |

**Auth & sessions:** JWT-style bearer token returned by
login/register, stored in `localStorage` (`civiceye_auth`), attached
as `Authorization: Bearer <token>` on every request by
`frontend/js/api.js`. A 401 anywhere clears the stored session and
bounces to `login.html?expired=1`. Logout clears storage client-side
(the backend has no token-blacklist endpoint — see "Remaining
issues").

**Role-based access:** backend roles are `citizen`, `researcher`,
`organization`, `platform_admin`, `data_admin`. The frontend mirrors
the backend's own RBAC exactly:
- `citizen.html`, `social-explorer.html`, `action-center.html` — any
  logged-in role can view; only `organization` / `platform_admin` /
  `data_admin` see the "New intervention" button and status-update
  controls (matches `ACTION_CENTER_ROLES` in the backend).
- `admin-platform.html` — `platform_admin` only.
- `admin-data.html` — `data_admin` or `platform_admin` (matches
  `DATA_ADMIN_ROLES`).
- Visiting a page your role can't use shows an in-page "Access
  restricted" screen instead of a blank page or a silent redirect
  loop; visiting any app page with no session at all redirects to
  `login.html`.

## What I fixed to make integration possible

- **Auth payload mismatch** — old frontend sent `{identifier, password,
  role}`; backend expects `{username|email, password}` for login and a
  full `{username, email, password, role, organization_name}` for
  registration. Login/signup forms were rewritten to match.
- **Role vocabulary mismatch** — old frontend used
  `citizen/explorer/action/admin-platform/admin-data` as "modes";
  backend roles are `citizen/researcher/organization/platform_admin/
  data_admin`. Centralized the mapping in `js/shell.js`
  (`ROLE_LABELS`, `ROLE_HOME`, `ROLE_LINKS`) so it's defined once.
- **Field-name drift everywhere** — e.g. patterns now carry a generic
  `indicators: [{field, value, district_median}]` array instead of the
  fixed `attendance/transport_access/dropout_rate` fields the mock
  assumed; relationships use `direction: "inverse"|"direct"` and
  `interpretation` instead of `"negative"|"positive"` and
  `explanation`; interventions use a 4-step
  `proposed → in_progress → completed → verified` status enum instead
  of the originally-designed 5-step one. Rewrote every render function
  against the actual response shapes in `API_CONTRACT.md`, not the
  earlier guesses.
- **No `domain` concept in the backend** — Social Explorer's domain
  selector is decorative-only pending future domains; "Education"
  is the only one the API serves right now.
- **Backend CORS dependency missing in this sandbox** — `Flask-Cors`
  wasn't installable here (no PyPI access in the test environment),
  so I could not run the server exactly as shipped. I did **not**
  change `requirements.txt` or `app.py` — a temporary local stub was
  used only inside my own test sandbox and was deleted before
  delivery. On a machine with normal internet access,
  `pip install -r requirements.txt` installs the real `Flask-Cors` and
  nothing further is needed.
- **Chart/map CDN failures no longer break unrelated data** — Chart.js
  and Leaflet load from CDN; if that fails (offline dev, strict
  network policy), the Impact Analyzer's stat cards and the Citizen
  Mode data list now still render — only the chart/map itself shows a
  small inline fallback message instead of taking the whole panel
  down. This surfaced as a real bug during testing (a chart-init
  exception was silently blanking already-fetched data) and is now
  fixed with an isolated try/catch around chart/map init specifically.
- **Loading/empty/error states** — every panel shows a skeleton while
  loading, an explicit empty state ("No interventions yet…") when the
  API returns zero rows, and a dismissible error card with a **Try
  again** button (calls the same loader function) on any failed
  request — instead of a blank panel or an uncaught exception.

## Testing performed

Full Playwright run against the live Flask + SQLite backend (not
mocked) covering: landing page, citizen signup → dashboard data load →
map, cross-role nav visibility, direct-URL access control (unauth →
login, wrong-role → access-restricted), Social Explorer's all six
panels including a real POST to `/api/social/simulation`, organization
signup → create an intervention → update its status → **reload the
page and confirm the change survived** (proves real DB persistence,
not client-side state), platform_admin user list + live role change
(`PATCH`, re-verified after reload), and data_admin dataset
summary/reload + civic-item creation. All checks passed on the final
run.

What I did **not** get to exercise end-to-end: production-mode
deployment (both servers were run via their built-in dev servers, as
the backend's own README recommends at this stage), and the
`GET /api/citizen/problems` / `/api/social/patterns` `area` query-string
filters beyond what the UI's own dropdowns exercise.

## UI polish pass (theming, contrast, responsiveness)

The frontend has since had a UI-only polish pass — no backend, API, layout,
page structure, or functionality changes. Summary:

- **Light/Dark toggle** in the header/top bar of every page, persisted to
  `localStorage` (`civiceye_theme`) and applied consistently everywhere. It
  is the single source of truth — the app does **not** switch theme based
  on `prefers-color-scheme`; a tiny inline script in each page's `<head>`
  applies the stored theme before first paint to avoid a flash of the
  wrong theme.
- **Semantic color tokens** (`css/tokens.css`): a fixed "raw palette" layer
  plus a theme-aware semantic layer (`--bg`, `--surface`, `--text`,
  `--button-bg`, `--button-text`, `--accent` vs `--accent-text`, `--soft-*`
  badge colors, etc.), so no component reuses one variable for two
  different jobs. That reuse was the root cause of a real bug this pass
  fixed: the old dark theme redefined `--ink-900` (used as both "dark ink
  text" and "the brand's dark button/sidebar fill") to a near-white value
  for text purposes, which silently turned every primary button and the
  sidebar into a light-on-light / white-on-near-white element in dark
  mode. Buttons, the nav rail, badges, and data-viz colors now each read
  from their own token.
- **Contrast verified programmatically** (WCAG relative-luminance contrast
  ratio, not eyeballed) across buttons, links, nav, cards, tables, and
  severity/status pills in both themes — see `theme_test.py` used during
  this pass for the method, not shipped as part of the app.
- **Mobile/responsive fixes**: a couple of two-column layouts and admin
  tables that didn't collapse below ~900px now do (`.grid-split` /
  `.grid-split-even` utility classes, `.table-scroll` wrapper), verified
  at a 375px viewport on every page.
- **Chart.js and Leaflet now degrade gracefully** if their CDN fails to
  load (already true from the earlier integration pass) — this pass
  additionally made the Impact Analyzer's chart redraw with correct
  colors on theme toggle without crashing on a second render, which a
  naive first attempt at "redraw on toggle" did not handle correctly.
- The left navigation rail is **intentionally** the same dark ink color in
  both themes (a fixed brand rail, not a bug) — only the main content
  area switches between the cinematic dark and paper/teal light looks.

## Remaining issues / things worth knowing before you ship this

1. **Logout is client-side only.** The backend issues a stateless
   token with a 12h expiry and has no `/api/auth/logout` or token
   revocation endpoint, so "Sign out" simply clears local storage —
   the old token is technically still valid until it expires if
   captured beforehand. Fine for a class project; worth a real
   revocation list (or short-lived tokens + refresh) before production
   use.
2. **Intervention list shows `Organization #<id>`, not a name.** There
   is no endpoint that maps an arbitrary `organization_id` to a
   display name for other users to read (the users list is
   `platform_admin`-only). A small public "organization directory"
   endpoint, or embedding `organization_name` directly in the
   intervention response, would fix this.
3. **Future Scanner shows model estimates, not a historical chart.**
   `GET /api/social/trends` returns a slope/forecast per indicator but
   no year-by-year series, so there's no raw data to honestly chart. I
   used exactly what the backend provides (direction, annual change,
   R², forecast year/value) rather than fabricate a data series to
   plot.
4. **No pagination on `/api/citizen/problems`, `/api/actions`, or
   `/api/admin/civic-items`.** Fine at demo-dataset scale; would need
   attention if the tables grow.
5. **This environment's egress proxy blocks `cdnjs.cloudflare.com` and
   `fonts.googleapis.com`,** so I couldn't visually confirm Chart.js /
   Leaflet / web-font rendering in this sandbox — only that the app
   degrades gracefully when they fail to load (see above). Please do
   a visual check once you open it on a normal network; I'd expect it
   to look as designed there.
6. **Registering a `platform_admin` or `data_admin` account is
   currently open to anyone via the public sign-up form**, because the
   backend's `/api/auth/register` accepts any of the five roles with
   no invite/approval step. That's a backend design choice (documented
   in its own `API_CONTRACT.md`, not something I changed) — worth
   flagging before a real deployment: you'll likely want a separate,
   protected path for creating admin accounts.
