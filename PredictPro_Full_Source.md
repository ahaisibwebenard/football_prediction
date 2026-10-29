# PredictPro — complete project source

```text
PredictPro/
├── backend/
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   └── matches.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── migrations/
│   │   ├── versions/
│   │   │   ├── 001_initial.py
│   │   │   └── 001_schema.sql
│   │   └── env.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── user.py
│   ├── seed/
│   │   ├── __init__.py
│   │   ├── sample.json
│   │   └── seed.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── football.py
│   │   ├── prediction.py
│   │   └── recovery.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_prediction.py
│   │   └── test_security.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── security.py
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   ├── preview.py
│   ├── schemas.py
│   └── worker.py
├── frontend/
│   ├── components/
│   │   ├── layout.js
│   │   └── ui.js
│   ├── hooks/
│   │   └── state.js
│   ├── pages/
│   │   ├── admin.js
│   │   ├── auth.js
│   │   ├── community.js
│   │   ├── dashboard.js
│   │   ├── match.js
│   │   └── profile.js
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   │   ├── main.css
│   │   └── typography.css
│   ├── vendor/
│   │   ├── LICENSE-Chart.js.txt
│   │   └── chart.umd.js
│   ├── app.js
│   └── index.html
├── scripts/
│   ├── check_frontend.py
│   └── init_env.py
├── .env.example
├── .gitignore
├── API.md
├── FEATURE_CHECKLIST.md
├── README.md
├── VERIFICATION.md
├── alembic.ini
├── package.json
└── requirements.txt
```

The files below are complete. Runtime credentials, databases, email outbox contents and caches are excluded; use `.env.example` and `scripts/init_env.py` to create your local configuration.

## .env.example

````text
APP_ENV=development
APP_URL=http://localhost:8000
DATABASE_URL=sqlite:///./predictpro.db
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_PASSWORD=benard
SEED_ADMIN_EMAIL=admin@example.com
FOOTBALL_API_KEY=
FOOTBALL_COMPETITIONS=PL,PD
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=noreply@predictpro.local
SMTP_STARTTLS=true
# Production also requires an explicit comma-separated host allowlist.
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
````

## .gitignore

````text
.env
.venv/
__pycache__/
.pytest_cache/
*.pyc
*.db
*.db-*
backend/outbox/
````

## API.md

````markdown
# PredictPro API reference

Base path `/api`. JSON request and response bodies. Cookies are same-origin and httpOnly. Login/signup responses and `GET /auth/me` return a session-bound `csrf` token. Send it in `X-CSRF-Token` for every authenticated POST, PUT or DELETE. Use the exact configured Origin if sending an Origin header. Public authentication writes require `Content-Type: application/json`.

Errors use `{"detail":"message"}` or a validation array of `loc`/`msg`. Status codes: 201 created; 400 invalid recovery/current password; 401 unauthenticated; 403 role/CSRF/account restriction; 404 missing record; 409 conflict/deadline/foreign key; 413 oversized declared body; 415 wrong content type; 422 validation; 429 rate limited; 503 maintenance.

## Public and authentication

| Method | Path | Request / purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/site` | Site name only; no secrets |
| POST | `/auth/signup` | `{name,email,username,password}`; role always USER |
| POST | `/auth/login` | `{login,password}`; login accepts email or username |
| POST | `/auth/forgot` | `{email}`; generic response |
| POST | `/auth/reset` | `{token,password}`; 30-minute single-use token |
| GET | `/auth/me` | Authenticated identity, CSRF, impersonation flag |
| POST | `/auth/logout` | Revoke current session and clear cookie |
| PUT | `/auth/profile` | `{name,email,username}` |
| POST | `/auth/password` | `{current_password,password}`; rotates sessions |

Names are 2–80 plain-text characters. Usernames use 3–30 letters, digits or underscores and are normalized to lowercase. Emails are validated and normalized to lowercase. Normal passwords need at least 10 characters and at most 72 UTF-8 bytes. Only the configured initial seed password may be shorter; it is blocked from normal application access until changed.

## Signed-in users

| Method | Path | Purpose |
|---|---|---|
| GET | `/catalog` | Leagues, teams and account's favorite flags |
| GET | `/matches` | Filters: `league`, `date` (UTC YYYY-MM-DD), `team`, `search`, `status` (SCHEDULED/FINISHED/ALL), `limit` (1–100), `offset`; returns `{items,total}` |
| GET | `/matches/{id}` | Match, stored prediction and prior head-to-head |
| POST | `/matches/{id}/pick` | `{outcome:"Home"}` or Draw/Away; update until kickoff |
| POST | `/matches/{id}/follow` | Toggle following; new follows close at kickoff |
| POST | `/favorites/{team_id}` | Toggle favorite |
| GET | `/history` | Stored predictions; 50 per page, `offset` |
| GET | `/leaderboard` | 3 points per correct completed outcome; AI source rows separate |
| GET | `/notifications` | Latest 100 account notifications |
| POST | `/notifications/{id}/read` | Mark an owned notification read |
| GET | `/metrics` | Source-separated accuracy, Brier loss and prospective trend |

Match timestamps returned by the API are UTC without an offset suffix; the supplied frontend appends `Z` before converting to local time. Match writes require an explicit timezone, such as `2026-11-01T15:00:00Z`. Form guides are oldest-to-newest. Probability fields are numbers in [0,1], not percentages. Notifications are generated during result ingestion or administrator result entry.

## ADMIN only

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/overview` | User counts, predictions, source-separated metrics, activity |
| GET | `/admin/users` | Search `q`; 50 per page, `offset` |
| GET | `/admin/users/{id}` | Safe account details; excludes password hash |
| POST | `/admin/users` | `{name,email,username,password,role}`; force change |
| PUT | `/admin/users/{id}` | `{name,email,username,role}` |
| POST | `/admin/users/{id}/state` | `{suspended:true}` to suspend; false activates and unlocks |
| DELETE | `/admin/users/{id}` | Delete account and dependent personal data; preserve audit |
| POST | `/admin/users/{id}/reset` | Create one-time reset link and revoke sessions |
| POST | `/admin/users/{id}/temporary-password` | Generate temporary password; force change |
| POST | `/admin/users/{id}/impersonate` | Active normal USER only; audited |
| POST | `/admin/return` | Impersonated session only; return to original administrator |
| GET | `/admin/audit` | Latest 100 audit records; `offset` |
| POST | `/admin/sync` | Import configured competitions; offline fallback |
| POST | `/admin/retrain` | Walk-forward Elo multiplier calibration |
| GET | `/admin/settings` | Site name, maintenance, API-key configured flag |
| PUT | `/admin/settings` | `{site_name,maintenance,api_key?}`; omit key to retain, empty string to disable |
| POST / PUT | `/admin/leagues` / `/admin/leagues/{id}` | `{name,code}` |
| DELETE | `/admin/leagues/{id}` | Delete if unreferenced |
| POST / PUT | `/admin/teams` / `/admin/teams/{id}` | `{name,league_id}` |
| DELETE | `/admin/teams/{id}` | Delete if unreferenced |
| POST / PUT | `/admin/matches` / `/admin/matches/{id}` | Match body below |
| DELETE | `/admin/matches/{id}` | Delete with related predictions, picks and notifications |

Example match write (use existing team and league IDs from `/catalog`):

```json
{
  "league_id": 1,
  "home_id": 1,
  "away_id": 2,
  "kickoff": "2026-11-10T15:00:00Z",
  "status": "SCHEDULED",
  "home_goals": null,
  "away_goals": null
}
```

For a completed match, use status FINISHED, a past kickoff and both nonnegative integer scores. POST creates manual-source fixtures. PUT retains the existing source and participants. Participant/competition changes require deleting and recreating the fixture; this prevents reusing another match's snapshot. Participant IDs need not belong to one league, allowing cross-league competitions. Upcoming fixtures created through the admin API receive an immediate frozen prediction. Past matches added after the event do not get a fabricated prospective score.

The current administrator cannot delete/suspend themselves through user-management routes. At least one active administrator must remain. Maintenance blocks USER feature endpoints while preserving login, password change, logout and administrator access. Impersonated sessions never gain ADMIN permissions and cannot change passwords or submit competitive picks.
````

## FEATURE_CHECKLIST.md

````markdown
# PredictPro acceptance checklist

“Implemented” means the code and UI flow are included. Automated verification is identified separately; it does not claim a completed browser or live-provider test.

| Requirement | Implemented | Verification / acceptance action |
|---|---|---|
| FastAPI, SQLAlchemy/SQLite and migrations | Yes | Fresh Alembic upgrade and seed smoke test completed |
| Organized backend/frontend, env example and README | Yes | Full source manifest and archive validated |
| Name/email/username signup; login/logout | Yes | Automated auth, role and logout tests |
| JWT httpOnly cookies and bcrypt hashes | Yes | Automated cookie/hash checks; Secure prefix enforced by production config |
| One initial admin from environment | Yes | Idempotent seed; default admin hash and forced change tested |
| Forgot password and single-use recovery | Yes | Delivery captured in tests; token reuse and expiry tested; real SMTP unverified |
| Login throttling and account lock/unlock | Yes | Automated failed-login, rate-limit and recovery tests |
| Input validation, SQL injection and XSS defenses | Yes | Validation/injection-shaped input tests; frontend escapes dynamic HTML; CSP and origin checks |
| CSRF and role-based admin protection | Yes | Automated missing/foreign-origin CSRF and role checks |
| Poisson + Elo + recent form + home advantage + H2H | Yes | Distribution and chronological isolation tests; all coefficients explained in source/README |
| Outcome probabilities, xG, scoreline, O/U and BTTS | Yes | Probability normalization/bounds tested; numbers accompany charts |
| Confidence labels and plain-English explanations | Yes | Service tests verify explanation and sparse-data confidence |
| Provider ingestion and bundled offline fallback | Yes | Mocked live import/deduplication and provider failure tests; no live credentials used |
| Stored predictions and honest accuracy history | Yes | Frozen snapshot, eligibility and source separation tests |
| Football-data disclaimers | Yes | Auth, navigation, footer, match explanations and README |
| Dashboard league/date/team/search filters | Yes | API filters tested; browser interaction unverified |
| Match details, Chart.js chart, form and H2H | Yes | Data service covered; chart syntax/assets checked, browser rendering unverified |
| Prediction history | Yes | History endpoint covered; 50-record pagination |
| Favorite teams | Yes | Toggle and persistence tested |
| User picks and AI leaderboard | Yes | Pick closure tested; correct-outcome points computed after final results |
| Profile and password changes | Yes | Profile and recovery tested; password rotation in first-login tests |
| Followed-match notifications | Yes | Duplicate-safe result notifications and mark-read tested; UI polls every 60 seconds |
| Admin overview with charts/activity | Yes | Protected overview endpoint tested; chart presentation unverified |
| User search/view/create/edit/delete | Yes | Account lifecycle integration test |
| Suspend/activate/unlock | Yes | Automated suspension and activation checks |
| Reset link and temporary password | Yes | Both recovery routes tested; hashes only and forced change |
| Audited impersonation and return banner | Yes | Start/return, role denial and password denial tested; visible banner implemented |
| Audit actor/action/time/IP | Yes | Audit persistence verified; secrets omitted |
| Match, team and league CRUD | Yes | Team/league constraints tested; result/prediction service covered |
| Trigger sync and calibration | Yes | API tests verify offline sync, mocked live sync and calibration report |
| Site name, API-key settings, maintenance | Yes | Maintenance tested; site name updates public metadata; API key contents never returned |
| Dark navy/emerald theme and light toggle | Yes | Responsive styles and persistent toggle included; visual inspection pending |
| Mobile sidebar, labels, focus and keyboard affordances | Yes | CSS breakpoints, native controls, skip link, modal focus and Escape handling; device/keyboard audit pending |
| Skeletons, empty states, toasts, validation errors | Yes | Included across pages; browser walkthrough pending |
| Automated auth/role/model tests | Yes | 19 tests passed; see VERIFICATION.md. Run `python -m pytest backend/tests -q` to repeat |
| Deployment instructions | Yes | Render/Railway persistent-volume instructions; Vercel limitation explained; no deployment created |

## Local browser walkthrough

1. Start the app using README instructions. At http://localhost:8000 sign in as admin/benard and confirm access is blocked until the password changes.
2. Set a new administrator password. Open Match center. Switch theme, resize to phone/tablet/desktop widths and operate the mobile menu using keyboard and pointer.
3. Filter by one demo league, team and UTC date. Open a match and compare the numerical probabilities with its Chart.js bars. Inspect form, earlier meetings and the full explanation.
4. Create a USER account. Submit a pick, follow an upcoming match and favorite a team. Reload to confirm persistence. Edit profile and change password.
5. Test Forgot password. Open the new development email under backend/outbox, follow its link, reset, then confirm the link cannot be reused.
6. As admin, search/view/edit the user. Generate a recovery link or temporary password. Suspend the user and verify they cannot continue; activate/unlock and verify access returns.
7. Log in as the active normal user. Confirm the banner, denied admin routes, blocked password/pick actions, then Return to admin. Inspect audit entries.
8. Create a manual league, two teams and a fixture with kickoff a few minutes ahead. As USER, follow it and submit a pick before kickoff. After kickoff, enter a final score as admin, retaining its kickoff and participant IDs. Return as USER; verify the notification, leaderboard points, history and manual-source accuracy. Never adjust a past kickoff merely to make an old pick count.
9. Exercise admin match/team/league create/edit/delete. A referenced team/league delete should return a clear conflict. Read the confirmation before permanently deleting a match and its picks.
10. Enable maintenance. USER features should show maintenance; admin retains controls. Disable it. Change the site name and reload to verify the header and document title.
11. Configure a valid provider key and sync. Verify live fixtures have source `live` and no “Demo” label. Review provider-plan errors in the sync report. Calibrate and inspect its walk-forward report; existing match predictions must remain frozen.
12. Before a real deployment, verify actual SMTP delivery, HTTPS Secure cookies, host/origin configuration, database backups and device/keyboard behavior with your hosting configuration.

## Known verification limits

The authoring environment's managed browser-preview process could not access its Python runtime. Consequently, no claim is made that browser screenshots, responsive rendering, keyboard navigation or Chart.js rendering were visually tested. Backend tests and JavaScript syntax checks are independent of that limitation. The model is not externally validated on a real prospective football dataset; synthetic backtests establish software behavior only.
````

## README.md

````markdown
# PredictPro

Explainable football probabilities, match analysis, community picks, and an audited administration panel.

**Stack:** Python 3.12+, FastAPI, SQLAlchemy, SQLite, Alembic, native JavaScript ES modules, responsive CSS, and locally bundled Chart.js 4.4.8. The frontend uses the clean HTML/CSS/JavaScript option in the specification. FastAPI serves both frontend and API from one origin, so no Node installation, frontend build, CORS configuration, or second server is required.

**Predictions are statistical estimates, not guarantees, and not betting advice.**

## Start on Windows with VS Code

1. Extract the ZIP. In VS Code, select **File → Open Folder → PredictPro**. Open a PowerShell terminal inside this folder. Install Python 3.12 or newer first if `python --version` does not show a suitable version.
2. Run the following commands, one line at a time. Calling the virtual environment's Python directly avoids PowerShell activation-policy problems.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/init_env.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m backend.seed.seed
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

3. Open **http://localhost:8000**. Use this hostname consistently: development CSRF checks expect the `APP_URL` in `.env`, which defaults to `http://localhost:8000`.
4. Sign in with **username `admin` and password `benard`**. The server requires a new password before any protected feature can be used. The new password needs at least 10 characters and at most 72 UTF-8 bytes. The password is bcrypt-hashed in the database; the initial credentials come from `.env`.
5. Create a normal user through **Create an account** on the sign-in screen, or create one in the administrator's **Manage users** page. Administrator-created users must change their initial password too.

Do not rerun `init_env.py` to rotate an existing key: it deliberately preserves existing configuration. To change environment values, edit `.env` and restart the server. Keep this file out of source control.

## Start on Linux or macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/init_env.py
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m backend.seed.seed
.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The same URL and initial administrator credentials apply. Stop the server with Ctrl+C. Your SQLite file persists in the project directory. Repeating the migration and seed commands preserves existing records and does not reset administrator passwords.

## Included data and first use

The seed inserts two **demo** leagues, 12 demo teams, 180 synthetic completed matches, 12 upcoming synthetic fixtures, stored predictions, and exactly one initial administrator if no administrator exists. The fixture generator uses the bundled `backend/seed/sample.json` and a fixed random seed; dates are relative to the day you first seed. Team names explicitly carry “Demo”. Scores and schedules are invented for software demonstration and are not real football records.

The seed does not create fake users, artificial community picks, or fake notifications. The leaderboard starts empty until picks are settled. Notifications start empty until followed matches finish. Existing sample fixtures are not automatically shifted forward by reseeding an existing database.

Historical sample predictions are labeled **retrospective backtests**. Only snapshots recorded while a fixture is scheduled and before kickoff are eligible for prospective accuracy. Live, manual, sample, and retrospective results are reported separately. The initial synthetic backtest percentage is not a claim about predictive skill on real matches.

## Live fixtures and results

1. Obtain your own football-data.org API token and confirm which competitions your plan permits.
2. Set `FOOTBALL_API_KEY` in `.env`, or use **Admin → Site settings**. The form never returns an existing key. An empty saved key disables live sync even if an environment key exists. A blank form field otherwise retains the current key.
3. `FOOTBALL_COMPETITIONS=PL,PD` selects the competition codes. Adjust it to your subscription. Restart after editing the environment.
4. Select **Admin overview → Sync football data**. The client uses `/v4/competitions/{code}/matches` with an `X-Auth-Token` header, imports finished results and scheduled fixtures, and deduplicates external IDs. In-play states are not misrepresented as finished. New past results are not given invented prospective predictions.
5. If there is no key or the provider is unavailable, bundled synthetic data remains usable. The returned sync report identifies errors and the source used. Provider limits, coverage, and current-season history affect the available sample size.

To sync once from a terminal:

```powershell
.\.venv\Scripts\python.exe -m backend.worker --once
```

For a single persistent sync process, run this in a second terminal:

```powershell
.\.venv\Scripts\python.exe -m backend.worker --interval 900
```

Linux/macOS equivalents use `.venv/bin/python`. Sync is otherwise manual; the web server does not silently launch a scheduler. Follow a match before kickoff to receive its full-time notification when sync or an administrator records the result. The browser polls notifications every 60 seconds while signed in. Notifications are in-app, not email or push alerts.

## Model and interpretation

The independent Poisson goal model calculates a score grid for 0–24 goals per team, normalizes its numerical mass, and aggregates Home/Draw/Away, Over/Under 2.5 and Both Teams To Score probabilities. The modal scoreline is the single most probable score cell, which can differ from the most probable overall outcome.

Features use only completed matches in the same competition and data source with kickoff strictly earlier than the target fixture, within a two-year window. Live results never mix with synthetic demo results.

- League home and away goal means shrink toward 1.45 and 1.15 using 20 pseudo-matches. The separate rates encode home advantage.
- Each team's last ten scoring and conceding records shrink toward the league mean using five pseudo-matches. The displayed form guide shows the latest five, oldest first.
- Elo starts at 1500, updates chronologically with K=24, and uses a 65-point home adjustment when updating match expectations.
- Capped Elo, recent points-per-match and up to five earlier head-to-head meetings adjust expected goals. Expected goal means are capped between 0.2 and 4.5 for numerical stability.
- “Higher”, “Moderate” and “Low” confidence combine the largest outcome probability with recent-match sample counts. These are descriptive labels, not calibrated confidence intervals.

**Calibrate model** performs walk-forward grid selection of the Elo multiplier using multiclass Brier loss on earlier results. It persists a versioned model setting for **new snapshots only**. Existing forecasts remain unchanged. Its report is a tuning-set score, not independent test accuracy, and explicitly identifies the possible inclusion of synthetic data. This is a real explainable statistical model; there is no external LLM or fabricated trained classifier.

Predictions are immutable snapshots; result reconciliation updates evaluation fields. Brier loss is the sum of squared errors across the three outcome probabilities, ranging from 0 to 2; lower is better. Real-world accuracy remains unknown until enough prospective live predictions finish. Injuries, lineups, player availability, weather and correlated goals are not modeled.

## Account recovery and support

**Forgot password:** enter the registered email. The response stays generic, whether or not an account exists. A random, single-use link expires after 30 minutes. Only the token's SHA-256 digest is stored. A successful reset invalidates all existing sessions and clears login locks. Suspension remains in force until an administrator activates the account.

**Local email:** without SMTP, development writes the recovery email into `backend/outbox/*.eml`, which is excluded from the archive and never served by the web server. Open the latest file locally and copy its link. Links use a URL fragment so their token is not placed in HTTP access-log query strings. You do not need a real SMTP account for local recovery testing.

**Production email:** set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` and `SMTP_STARTTLS` as appropriate for your provider. STARTTLS defaults to enabled. Production startup requires an SMTP host and HTTPS `APP_URL`. Actual email delivery needs valid credentials and sender-domain configuration. Update the initial admin email to an address you control.

**Administrator recovery:** Manage users offers a one-time link, a randomly generated temporary password, and activation/unlock. Temporary passwords are displayed once, stored only as bcrypt hashes, and require a change after login. Recovery revokes existing sessions. Existing reset tokens are invalidated when replaced or when a password changes.

**Impersonation:** “Log in as” is available for active USER accounts that have no lock or forced password change. A prominent banner identifies the user and offers **Return to admin**. The signed token binds the impersonation to the original administrator's active session and account version. Admin routes, password changes and competitive picks are blocked during impersonation. Start and return are audited. A revoked or demoted administrator loses the ability to continue that impersonation. If a target is suspended during support, the administrator can sign in normally again.

**Audit:** sensitive admin operations record actor identity, action, target, UTC timestamp, and request IP. Passwords, reset tokens and API-key contents are omitted. Audit rows survive account deletion. The panel does not offer log deletion. These are application audit records, not a tamper-proof external ledger.

## Security and operations

JWTs are signed, expiring, httpOnly cookies; server-side session records support logout and revocation. Cookies use SameSite Strict and become Secure with the `__Host-` prefix in production. Password changes rotate account versions and invalidate other sessions. Authenticated writes require a session-bound `X-CSRF-Token` and same-origin validation. Public authentication writes require JSON and reject foreign Origin headers; no cross-origin CORS access is enabled.

Login and recovery rate limits use shared SQLite counters, rather than per-process memory. Five failed passwords lock an account for 15 minutes. Password hashing uses bcrypt cost 12. Pydantic validates payloads; SQLAlchemy binds query parameters; output is escaped before HTML insertion. The app applies a CSP, frame denial, content-type protection and production HSTS. Validation responses omit submitted input. SQLite foreign keys and explicit transaction completion prevent broken references and false success responses.

Use a single application instance with a persistent local disk for SQLite. Back up the database using SQLite's backup API or a consistent snapshot; copying an active WAL database by itself can lose data. Protect the disk and backups: administrator-configured provider keys are stored in the settings table and require filesystem encryption/access controls. Keep JWT and SMTP secrets in environment variables. Database migrations must run before application startup.

The code includes security controls and automated checks, but this delivery is not an independent penetration test or a certification of production readiness. Review dependency updates and your hosting configuration before exposing a deployment. Bootstrap the administrator privately and change the initial password before allowing public access.

## Tests and verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Linux/macOS:

```bash
.venv/bin/python -m pytest backend/tests -q
```

Tests use their own SQLite test database and never the configured production database. They cover password hashing, forced first-login change, logout revocation, roles, CSRF/origin checks, validation, injection-shaped searches, login locks and rate limits, recovery expiry and reuse, recovery session revocation, user management, profile/favorites, audited impersonation/return, last-admin protection, probability normalization, snapshot integrity, chronological feature isolation, pick deadlines, duplicate-safe notifications, catalog constraints, maintenance, mocked live ingestion and offline fallback.

Optional first-party JavaScript syntax checks require Node 20+ (Node is not needed to run the app):

```bash
python scripts/check_frontend.py
```

See [VERIFICATION.md](VERIFICATION.md) for the 19-test result and smoke checks, and [FEATURE_CHECKLIST.md](FEATURE_CHECKLIST.md) for the acceptance walkthrough and measured limits. Browser visual/keyboard verification was unavailable in the authoring environment because its preview runtime could not access Python. Live HTTP provider calls and actual SMTP delivery require your credentials; tests substitute deterministic provider responses and capture email delivery.

## Deployment

**Render:** deploy a Python web service with a persistent disk mounted at `/var/data`. Set `DATABASE_URL=sqlite:////var/data/predictpro.db`, the exact HTTPS `APP_URL`, an explicit `ALLOWED_HOSTS` list, `APP_ENV=production`, a fresh random `JWT_SECRET`, seed credentials and SMTP configuration in the host's environment. Install with `pip install -r requirements.txt`. On the disk-attached instance, migrate and seed before starting:

```bash
python -m alembic upgrade head
python -m backend.seed.seed
python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers 1
```

Run the first two commands only where the mounted database is available, not in an isolated build job. Protect initial access while changing the bootstrap password. Configure scheduled sync on the same instance/filesystem, or invoke **Sync football data** manually. A separate container cannot assume access to the same SQLite disk. Do not use an ephemeral disk for durable data.

**Railway:** use a Python service with a persistent volume, the same database path and environment settings, and the same migration/start sequence. Keep a single replica for SQLite. Review the provider's current volume/backup and startup documentation.

**Vercel:** this single-server SQLite version is not suitable for Vercel Functions' ephemeral filesystem. For Vercel, migrate to a managed database, redesign the backend adapter and connection configuration, and verify same-origin cookies/CSRF through an API proxy. For this delivered application, Render or Railway with a persistent volume is the direct route.

Official references:

- https://docs.football-data.org/general/v4/competition.html
- https://docs.football-data.org/general/v4/match.html
- https://render.com/docs/deploy-fastapi
- https://render.com/docs/disks
- https://docs.railway.com/volumes
- https://vercel.com/kb/guide/is-sqlite-supported-in-vercel

## Source navigation

`backend/routes` exposes API endpoints. `controllers` handles serialization and shared actions. `services` contains modeling, data ingestion and recovery delivery. `models` defines records. `middleware` checks sessions, roles and CSRF. `utils` contains password/token/rate utilities. `seed` contains bundled data and its deterministic generator. `migrations` contains the frozen initial SQL schema. `frontend` contains independent pages, shared components, state hooks, API services, styles and the complete vendored chart distribution.

See [API.md](API.md) for the endpoint reference. Interactive OpenAPI docs are at **http://localhost:8000/api/docs** in development (the optional Swagger UI requires internet); they and its OpenAPI schema are disabled in production. Direct API clients must send the CSRF token returned by login or `/api/auth/me` on authenticated writes.
````

## VERIFICATION.md

````markdown
# Verification record

Verified on 29 October 2026 using Python 3.12 and Node.js 24.22.1.

- `python -m pytest backend/tests -q`: **19 passed**, one upstream Starlette TestClient deprecation warning, no test failures.
- `python scripts/check_frontend.py`: **11 first-party JavaScript modules passed syntax checks**.
- `python -m compileall -q backend scripts`: passed.
- A fresh temporary SQLite database migrated successfully with `python -m alembic upgrade head`.
- Running the seed twice created 192 matches and one administrator on the first run, then added zero matches on the second run. The administrator password column contained no plaintext initial password.
- Production-mode ASGI smoke checks verified a `__Host-predictpro` cookie with Secure and HttpOnly flags and confirmed that developer docs and the OpenAPI schema are disabled.
- Chart.js is bundled locally, and static-file responses and security headers were checked through the application.

Provider HTTP responses and recovery email delivery were substituted in tests. Real football-data.org credentials and SMTP delivery were not exercised. Browser preview could not launch because its separate runtime could not access Python, so responsive layout, visual appearance, chart rendering and keyboard behavior remain unverified in a real browser. The manual acceptance walkthrough is in FEATURE_CHECKLIST.md.

No real-match accuracy claim is made. Bundled schedules/results are synthetic; retrospective backtests are separated from prospective forecasts. No hosted deployment was created.
````

## alembic.ini

````ini
[alembic]
script_location = backend/migrations
prepend_sys_path = .
sqlalchemy.url = sqlite:///./predictpro.db
````

## backend/__init__.py

````python
"""PredictPro application package."""
````

## backend/config.py

````python
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ENV = os.getenv("APP_ENV", "development")
URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")
SECRET = os.getenv("JWT_SECRET", "")
if len(SECRET) < 32:
    raise RuntimeError("Set JWT_SECRET to at least 32 random characters in .env.")
if ENV == "production" and (
    not URL.startswith("https://") or not os.getenv("SMTP_HOST")
):
    raise RuntimeError("Production requires an HTTPS APP_URL and SMTP_HOST.")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./predictpro.db")
COOKIE = "__Host-predictpro" if ENV == "production" else "predictpro"
SECURE = ENV == "production"
HOSTS = [
    x.strip()
    for x in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if x.strip()
]
````

## backend/controllers/__init__.py

````python
"""PredictPro application package."""
````

## backend/controllers/common.py

````python
from fastapi import HTTPException
from backend.models.entities import Audit


def require(db, model, pk):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(404, "Record not found.")
    return obj


def audit(db, request, actor, action, target):
    db.add(
        Audit(
            actor=f"{actor.username} (#{actor.id})",
            action=action,
            target=str(target)[:100],
            ip=request.client.host if request.client else "unknown",
        )
    )
````

## backend/controllers/matches.py

````python
import json
from sqlalchemy import select
from backend.models.entities import Team, League, Match, Prediction, Follow, Pick
from backend.services.prediction import history_for


def match_json(db, m, user_id=None, detail=False):
    home, away = db.get(Team, m.home_id), db.get(Team, m.away_id)
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    result = {
        k: getattr(m, k)
        for k in (
            "id",
            "league_id",
            "home_id",
            "away_id",
            "kickoff",
            "status",
            "home_goals",
            "away_goals",
            "source",
        )
    }
    result.update(
        home=home.name, away=away.name, league=db.get(League, m.league_id).name
    )
    result["prediction"] = json.loads(p.payload) if p else None
    result["prediction_id"] = p.id if p else None
    result["eligible"] = p.eligible if p else False
    result["correct"] = p.correct if p else None
    result["model_version"] = p.model_version if p else None
    result["prediction_created_at"] = p.created_at if p else None
    if user_id:
        result["following"] = db.get(Follow, (user_id, m.id)) is not None
        pick = db.scalar(
            select(Pick).where(Pick.user_id == user_id, Pick.match_id == m.id)
        )
        result["pick"] = pick.outcome if pick else None
    if detail:
        rows = [
            x
            for x in history_for(db, m)
            if {x.home_id, x.away_id} == {m.home_id, m.away_id}
        ][-5:]
        result["head_to_head"] = [
            {
                "date": x.kickoff,
                "home": db.get(Team, x.home_id).name,
                "away": db.get(Team, x.away_id).name,
                "score": f"{x.home_goals}–{x.away_goals}",
            }
            for x in reversed(rows)
        ]
    return result
````

## backend/db.py

````python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.config import DB_URL

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    hide_parameters=True,
)


@event.listens_for(engine, "connect")
def sqlite_config(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
````

## backend/main.py

````python
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError
from fastapi import Depends
from backend.db import get_db
from backend.models.entities import Setting
from backend.config import ROOT, ENV, HOSTS, URL
from backend.routes import auth, user, admin

app = FastAPI(
    title="PredictPro API",
    version="1.0.0",
    docs_url="/api/docs" if ENV != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if ENV != "production" else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=HOSTS)


@app.middleware("http")
async def harden(request: Request, call_next):
    length = request.headers.get("content-length", "0")
    if length.isdigit() and int(length) > 65536:
        return JSONResponse({"detail": "Request too large."}, 413)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") not in (None, URL):
            return JSONResponse({"detail": "Origin rejected."}, 403)
    try:
        response = await call_next(request)
    except Exception:
        logging.exception("Unhandled request error")
        response = JSONResponse({"detail": "An unexpected error occurred."}, 500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if ENV != "production" and request.url.path == "/api/docs":
        # Only the optional developer docs load Swagger UI from its CDN.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    if ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(IntegrityError)
async def integrity(request, exc):
    return JSONResponse(
        {
            "detail": "Conflicting or referenced record. Check unique fields and delete dependent records first."
        },
        409,
    )


@app.exception_handler(RequestValidationError)
async def validation(request, exc):
    return JSONResponse(
        {"detail": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]},
        422,
    )


@app.get("/api/site")
def site(db=Depends(get_db, scope="function")):
    name = db.get(Setting, "site_name")
    return {"site_name": name.value if name else "PredictPro"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PredictPro"}


@app.get("/")
def index():
    return FileResponse(ROOT / "frontend" / "index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")
````

## backend/middleware/__init__.py

````python
"""PredictPro application package."""
````

## backend/middleware/auth.py

````python
import secrets
from fastapi import Depends, HTTPException, Request
from backend.db import get_db
from backend.models.entities import User, Session, Setting, now
from backend.utils.security import decode
from backend.config import URL


def identity(request: Request, db=Depends(get_db, scope="function")):
    claims = decode(request)
    user = db.get(User, int(claims["sub"]))
    session = db.get(Session, claims["jti"])
    if (
        not user
        or not session
        or session.user_id != user.id
        or session.revoked
        or session.expires_at <= now()
        or claims["ver"] != user.version
    ):
        raise HTTPException(401, "Session expired. Please sign in.")
    if user.suspended or (user.locked_until and user.locked_until > now()):
        raise HTTPException(403, "Account unavailable. Contact an administrator.")
    if claims.get("actor"):
        actor = db.get(User, claims["actor"])
        parent = db.get(Session, claims.get("parent"))
        if (
            not actor
            or actor.suspended
            or actor.role != "ADMIN"
            or actor.must_change
            or actor.version != claims["actor_ver"]
            or not parent
            or parent.user_id != actor.id
            or parent.revoked
            or parent.expires_at <= now()
        ):
            raise HTTPException(401, "Administrator session expired.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") not in (None, URL):
            raise HTTPException(403, "Origin rejected.")
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), session.csrf
        ):
            raise HTTPException(403, "Invalid CSRF token. Reload and try again.")
    allowed = (
        "/api/auth/me",
        "/api/auth/logout",
        "/api/auth/password",
        "/api/admin/return",
    )
    if user.must_change and request.url.path not in allowed:
        raise HTTPException(403, "Change your password before continuing.")
    setting = db.get(Setting, "maintenance")
    if (
        setting
        and setting.value == "true"
        and user.role != "ADMIN"
        and request.url.path not in allowed
    ):
        raise HTTPException(503, "PredictPro is undergoing maintenance.")
    if (now() - user.last_active).total_seconds() > 300:
        user.last_active = now()
    request.state.claims, request.state.session = claims, session
    return user


def admin(request: Request, user=Depends(identity)):
    if user.role != "ADMIN" or request.state.claims.get("actor"):
        raise HTTPException(403, "Administrator access required.")
    return user
````

## backend/migrations/env.py

````python
from alembic import context
from backend.db import engine
from backend.models.entities import Base

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()
````

## backend/migrations/versions/001_initial.py

````python
"""Initial PredictPro schema, frozen SQL snapshot."""

from pathlib import Path
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    sql = Path(__file__).with_name("001_schema.sql").read_text()
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    for table in (
        "rate_buckets",
        "settings",
        "audit",
        "notifications",
        "follows",
        "favorites",
        "picks",
        "predictions",
        "matches",
        "teams",
        "leagues",
        "resets",
        "sessions",
        "users",
    ):
        op.drop_table(table)
````

## backend/migrations/versions/001_schema.sql

````sql
CREATE TABLE audit (
	id INTEGER NOT NULL, 
	actor VARCHAR(100) NOT NULL, 
	action VARCHAR(60) NOT NULL, 
	target VARCHAR(100) NOT NULL, 
	ip VARCHAR(80) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE leagues (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(12) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
);

CREATE TABLE rate_buckets (
	"key" VARCHAR(100) NOT NULL, 
	count INTEGER NOT NULL, 
	started DATETIME NOT NULL, 
	PRIMARY KEY ("key")
);

CREATE TABLE settings (
	"key" VARCHAR(60) NOT NULL, 
	value TEXT NOT NULL, 
	PRIMARY KEY ("key")
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	username VARCHAR(30) NOT NULL, 
	password_hash VARCHAR(100) NOT NULL, 
	role VARCHAR(10) NOT NULL, 
	suspended BOOLEAN NOT NULL, 
	must_change BOOLEAN NOT NULL, 
	version INTEGER NOT NULL, 
	locked_until DATETIME, 
	failed INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	last_active DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('ADMIN','USER')), 
	UNIQUE (email), 
	UNIQUE (username)
);

CREATE TABLE resets (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	digest VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (digest)
);

CREATE TABLE sessions (
	id VARCHAR(64) NOT NULL, 
	user_id INTEGER NOT NULL, 
	csrf VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE teams (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	league_id INTEGER NOT NULL, 
	external_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE RESTRICT, 
	UNIQUE (external_id)
);

CREATE TABLE favorites (
	user_id INTEGER NOT NULL, 
	team_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, team_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE
);

CREATE TABLE matches (
	id INTEGER NOT NULL, 
	external_id INTEGER, 
	league_id INTEGER NOT NULL, 
	home_id INTEGER NOT NULL, 
	away_id INTEGER NOT NULL, 
	kickoff DATETIME NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	home_goals INTEGER, 
	away_goals INTEGER, 
	source VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (home_id != away_id), 
	CHECK (status IN ('SCHEDULED','FINISHED','POSTPONED','CANCELLED')), 
	UNIQUE (external_id), 
	FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE RESTRICT, 
	FOREIGN KEY(home_id) REFERENCES teams (id) ON DELETE RESTRICT, 
	FOREIGN KEY(away_id) REFERENCES teams (id) ON DELETE RESTRICT
);

CREATE TABLE follows (
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, match_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	text VARCHAR(300) NOT NULL, 
	read BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, match_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE picks (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	outcome VARCHAR(4) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, match_id), 
	CHECK (outcome IN ('Home','Draw','Away')), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE predictions (
	id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	payload TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	model_version VARCHAR(80) NOT NULL, 
	eligible BOOLEAN NOT NULL, 
	correct BOOLEAN, 
	brier FLOAT, 
	PRIMARY KEY (id), 
	UNIQUE (match_id), 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);
````

## backend/models/__init__.py

````python
"""PredictPro application package."""
````

## backend/models/entities.py

````python
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="USER")
    suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    must_change: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    locked_until: Mapped[datetime | None]
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=now)
    last_active: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (CheckConstraint("role IN ('ADMIN','USER')"),)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Reset(Base):
    __tablename__ = "resets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(12), unique=True)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="RESTRICT")
    )
    external_id: Mapped[int | None] = mapped_column(unique=True)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(unique=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="RESTRICT")
    )
    home_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"))
    away_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"))
    kickoff: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(16), default="SCHEDULED")
    home_goals: Mapped[int | None]
    away_goals: Mapped[int | None]
    source: Mapped[str] = mapped_column(String(20), default="manual")
    __table_args__ = (
        CheckConstraint("home_id != away_id"),
        CheckConstraint("status IN ('SCHEDULED','FINISHED','POSTPONED','CANCELLED')"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), unique=True
    )
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=now)
    model_version: Mapped[str] = mapped_column(String(80))
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    correct: Mapped[bool | None]
    brier: Mapped[float | None] = mapped_column(Float)


class Pick(Base):
    __tablename__ = "picks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    outcome: Mapped[str] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (
        UniqueConstraint("user_id", "match_id"),
        CheckConstraint("outcome IN ('Home','Draw','Away')"),
    )


class Favorite(Base):
    __tablename__ = "favorites"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )


class Follow(Base):
    __tablename__ = "follows"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(300))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (UniqueConstraint("user_id", "match_id"),)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(100))
    ip: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    started: Mapped[datetime] = mapped_column(default=now)
````

## backend/preview.py

````python
"""Local development launcher; production uses the documented uvicorn command."""

import os
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args, _ = parser.parse_known_args()
    uvicorn.run("backend.main:app", host=args.host, port=args.port)
````

## backend/routes/__init__.py

````python
"""PredictPro application package."""
````

## backend/routes/admin.py

````python
import json
import os
import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from sqlalchemy import select, func, update
from backend.db import get_db
from backend.middleware.auth import admin, identity
from backend.models.entities import (
    User,
    Match,
    Team,
    League,
    Prediction,
    Audit,
    Setting,
    Session,
    Reset,
    now,
)
from backend.schemas import (
    UserCreate,
    UserEdit,
    StateInput,
    LeagueInput,
    TeamInput,
    MatchInput,
    SettingsInput,
)
from backend.utils.security import (
    public_user,
    hash_password,
    password_check,
    revoke_all,
    issue,
)
from backend.controllers.common import require, audit
from backend.controllers.matches import match_json
from backend.services.recovery import create_reset
from backend.services.football import refresh, notify_result
from backend.services.prediction import get_prediction, retrain
from backend.routes.user import model_metrics

router = APIRouter(prefix="/api/admin", tags=["Administration"])


def protect_admin(db, target, actor, destructive=False):
    # Serialize last-admin checks so concurrent requests cannot remove all admins.
    db.execute(update(User).where(User.id == actor.id).values(version=User.version))
    if target.id == actor.id and destructive:
        raise HTTPException(
            409,
            "Use your profile for your own account. This action cannot target yourself.",
        )
    if target.role == "ADMIN" and not target.suspended:
        count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "ADMIN", User.suspended == False)
        )
        if count <= 1 and destructive:
            raise HTTPException(409, "At least one active administrator is required.")


@router.get("/overview")
def overview(actor=Depends(admin), db=Depends(get_db, scope="function")):
    activity = list(
        db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(12))
    )
    daily = db.execute(
        select(func.date(Audit.created_at), func.count())
        .group_by(func.date(Audit.created_at))
        .order_by(func.date(Audit.created_at).desc())
        .limit(14)
    ).all()
    return {
        "total_users": db.scalar(select(func.count()).select_from(User)),
        "active_users": db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.last_active > now() - timedelta(days=30), User.suspended == False
            )
        ),
        "predictions": db.scalar(select(func.count()).select_from(Prediction)),
        "metrics": model_metrics(db),
        "recent": [
            {
                "actor": a.actor,
                "action": a.action,
                "target": a.target,
                "created_at": a.created_at,
            }
            for a in activity
        ],
        "daily": [{"date": d, "count": n} for d, n in reversed(daily)],
    }


@router.get("/users")
def users(
    q: str = Query("", max_length=100),
    offset: int = Query(0, ge=0),
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    rows = db.scalars(
        select(User)
        .where(
            User.username.icontains(q, autoescape=True)
            | User.email.icontains(q, autoescape=True)
            | User.name.icontains(q, autoescape=True)
        )
        .order_by(User.id)
        .offset(offset)
        .limit(50)
    )
    return [public_user(u) for u in rows]


@router.get("/users/{uid}")
def user_detail(uid: int, actor=Depends(admin), db=Depends(get_db, scope="function")):
    return public_user(require(db, User, uid))


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    password_check(body.password)
    user = User(
        **body.model_dump(exclude={"password"}),
        password_hash=hash_password(body.password),
        must_change=True,
    )
    db.add(user)
    db.flush()
    audit(db, request, actor, "CREATE_USER", user.id)
    return {
        "message": "User created. Password change required.",
        "user": public_user(user),
    }


@router.put("/users/{uid}")
def edit_user(
    uid: int,
    body: UserEdit,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.role != body.role:
        protect_admin(db, target, actor, True)
        revoke_all(db, target)
    for k, v in body.model_dump().items():
        setattr(target, k, v)
    audit(db, request, actor, "EDIT_USER", uid)
    return {"message": "User updated."}


@router.post("/users/{uid}/state")
def state(
    uid: int,
    body: StateInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    protect_admin(db, target, actor, body.suspended)
    target.suspended = body.suspended
    target.failed = 0
    target.locked_until = None
    revoke_all(db, target)
    audit(
        db, request, actor, "SUSPEND_USER" if body.suspended else "ACTIVATE_UNLOCK", uid
    )
    return {
        "message": "Account suspended."
        if body.suspended
        else "Account activated and unlocked."
    }


@router.delete("/users/{uid}")
def delete_user(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    protect_admin(db, target, actor, True)
    audit(db, request, actor, "DELETE_USER", f"{target.username} (#{uid})")
    db.delete(target)
    return {"message": "User deleted."}


@router.post("/users/{uid}/reset")
def reset_user(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.id == actor.id:
        raise HTTPException(409, "Change your own password in Profile.")
    link = create_reset(db, target)
    revoke_all(db, target)
    target.must_change = True
    target.failed = 0
    target.locked_until = None
    audit(db, request, actor, "PASSWORD_RESET_LINK", uid)
    return {
        "message": "One-time link expires in 30 minutes. Share it securely. Suspended users must also be activated.",
        "reset_link": link,
    }


@router.post("/users/{uid}/temporary-password")
def temporary(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.id == actor.id:
        raise HTTPException(409, "Change your own password in Profile.")
    password = secrets.token_urlsafe(15)
    target.password_hash = hash_password(password)
    target.must_change = True
    target.failed = 0
    target.locked_until = None
    revoke_all(db, target)
    db.execute(update(Reset).where(Reset.user_id == uid).values(used=True))
    audit(db, request, actor, "TEMPORARY_PASSWORD", uid)
    return {
        "message": "Temporary password shown once. A change is required at login.",
        "temporary_password": password,
    }


@router.post("/users/{uid}/impersonate")
def impersonate(
    uid: int,
    request: Request,
    response: Response,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if (
        target.role == "ADMIN"
        or target.suspended
        or target.must_change
        or (target.locked_until and target.locked_until > now())
    ):
        raise HTTPException(
            409,
            "Impersonation requires an active USER with no forced password change or lock.",
        )
    audit(db, request, actor, "IMPERSONATE_START", f"{target.username} (#{uid})")
    csrf = issue(db, target, response, actor=actor, parent=request.state.session.id)
    return {"user": public_user(target), "csrf": csrf, "impersonating": True}


@router.post("/return")
def return_admin(
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    claims = request.state.claims
    if not claims.get("actor"):
        raise HTTPException(400, "No impersonation session.")
    actor = require(db, User, claims["actor"])
    request.state.session.revoked = True
    parent = db.get(Session, claims["parent"])
    parent.revoked = True
    audit(db, request, actor, "IMPERSONATE_END", user.id)
    csrf = issue(db, actor, response)
    return {"user": public_user(actor), "csrf": csrf, "impersonating": False}


@router.get("/audit")
def logs(
    offset: int = Query(0, ge=0),
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    return [
        {
            k: getattr(a, k)
            for k in ("id", "actor", "action", "target", "ip", "created_at")
        }
        for a in db.scalars(
            select(Audit).order_by(Audit.id.desc()).limit(100).offset(offset)
        )
    ]


@router.post("/sync")
def sync(request: Request, actor=Depends(admin), db=Depends(get_db, scope="function")):
    audit(db, request, actor, "SYNC_DATA", "football-data.org")
    db.commit()
    return refresh(db)


@router.post("/retrain")
def train(request: Request, actor=Depends(admin), db=Depends(get_db, scope="function")):
    report = retrain(db)
    audit(db, request, actor, "MODEL_CALIBRATION", report.get("version", "retained"))
    return report


@router.get("/settings")
def settings(actor=Depends(admin), db=Depends(get_db, scope="function")):
    name = db.get(Setting, "site_name")
    maintenance = db.get(Setting, "maintenance")
    key = db.get(Setting, "api_key")
    return {
        "site_name": name.value if name else "PredictPro",
        "maintenance": bool(maintenance and maintenance.value == "true"),
        "api_key_configured": bool(
            key.value if key else os.getenv("FOOTBALL_API_KEY", "")
        ),
    }


@router.put("/settings")
def edit_settings(
    body: SettingsInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    values = {"site_name": body.site_name, "maintenance": str(body.maintenance).lower()}
    if body.api_key is not None:
        values["api_key"] = body.api_key.strip()
    for key, value in values.items():
        setting = db.get(Setting, key)
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    audit(db, request, actor, "UPDATE_SETTINGS", ",".join(values))
    return {
        "message": "Settings saved. API key is never returned. Protect database backups as secrets."
    }


@router.post("/leagues", status_code=201)
def create_league(
    body: LeagueInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = League(**body.model_dump())
    db.add(obj)
    db.flush()
    audit(db, request, actor, "CREATE_LEAGUE", obj.id)
    return {"message": "League created.", "id": obj.id}


@router.put("/leagues/{pk}")
def edit_league(
    pk: int,
    body: LeagueInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = require(db, League, pk)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    audit(db, request, actor, "EDIT_LEAGUE", pk)
    return {"message": "League updated."}


@router.delete("/leagues/{pk}")
def delete_league(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, League, pk))
    audit(db, request, actor, "DELETE_LEAGUE", pk)
    return {"message": "League deleted."}


@router.post("/teams", status_code=201)
def create_team(
    body: TeamInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    require(db, League, body.league_id)
    obj = Team(**body.model_dump())
    db.add(obj)
    db.flush()
    audit(db, request, actor, "CREATE_TEAM", obj.id)
    return {"message": "Team created.", "id": obj.id}


@router.put("/teams/{pk}")
def edit_team(
    pk: int,
    body: TeamInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = require(db, Team, pk)
    require(db, League, body.league_id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    audit(db, request, actor, "EDIT_TEAM", pk)
    return {"message": "Team updated."}


@router.delete("/teams/{pk}")
def delete_team(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, Team, pk))
    audit(db, request, actor, "DELETE_TEAM", pk)
    return {"message": "Team deleted."}


def validate_match(db, body):
    require(db, League, body.league_id)
    for tid in (body.home_id, body.away_id):
        require(db, Team, tid)
    if body.status == "FINISHED" and body.kickoff > now():
        raise HTTPException(422, "A future match cannot be finished.")


@router.post("/matches", status_code=201)
def create_match(
    body: MatchInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    validate_match(db, body)
    m = Match(**body.model_dump(), source="manual")
    db.add(m)
    db.flush()
    if m.status == "SCHEDULED" and m.kickoff > now():
        get_prediction(db, m)
    audit(db, request, actor, "CREATE_MATCH", m.id)
    return {"message": "Match created.", "id": m.id}


@router.put("/matches/{pk}")
def edit_match(
    pk: int,
    body: MatchInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    m = require(db, Match, pk)
    validate_match(db, body)
    if (body.home_id, body.away_id, body.league_id) != (
        m.home_id,
        m.away_id,
        m.league_id,
    ):
        raise HTTPException(
            409,
            "To change participants or competition, delete and recreate the fixture.",
        )
    old_kickoff = m.kickoff
    for k, v in body.model_dump().items():
        setattr(m, k, v)
    p = db.scalar(select(Prediction).where(Prediction.match_id == pk))
    # A changed kickoff can never retroactively qualify a post-kickoff prediction.
    if p and body.kickoff != old_kickoff:
        p.eligible = p.eligible and p.created_at < body.kickoff
    if m.status == "FINISHED":
        notify_result(db, m)
    elif p:
        p.correct = None
        p.brier = None
    elif m.status == "SCHEDULED" and m.kickoff > now():
        get_prediction(db, m)
    audit(db, request, actor, "EDIT_MATCH", pk)
    return {
        "message": "Match updated; recorded results evaluated and followers notified."
    }


@router.delete("/matches/{pk}")
def delete_match(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, Match, pk))
    audit(db, request, actor, "DELETE_MATCH", pk)
    return {"message": "Match deleted, including dependent picks and predictions."}
````

## backend/routes/auth.py

````python
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy import select, update, or_
from backend.db import get_db
from backend.middleware.auth import identity
from backend.models.entities import User, Reset, Session, now
from backend.schemas import Signup, Login, Password, Forgot, ResetInput, Profile
from backend.utils.security import (
    hash_password,
    verify,
    password_check,
    issue,
    public_user,
    rate,
    digest,
    revoke_all,
)
from backend.services.recovery import create_reset, send_reset
from backend.config import COOKIE, URL

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def public_guard(request, db, action, limit):
    if request.headers.get("origin") not in (None, URL):
        raise HTTPException(403, "Origin rejected.")
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "JSON required.")
    rate(
        db, action + ":" + (request.client.host if request.client else "unknown"), limit
    )


@router.post("/signup", status_code=201)
def signup(
    body: Signup,
    request: Request,
    response: Response,
    db=Depends(get_db, scope="function"),
):
    public_guard(request, db, "signup", 10)
    password_check(body.password)
    if db.scalar(
        select(User).where(
            or_(User.email == body.email, User.username == body.username)
        )
    ):
        raise HTTPException(409, "Email or username is already registered.")
    user = User(
        **body.model_dump(exclude={"password"}),
        password_hash=hash_password(body.password),
        role="USER",
    )
    db.add(user)
    db.flush()
    csrf = issue(db, user, response)
    return {"user": public_user(user), "csrf": csrf}


@router.post("/login")
def login(
    body: Login,
    request: Request,
    response: Response,
    db=Depends(get_db, scope="function"),
):
    public_guard(request, db, "login", 20)
    key = body.login.lower().strip()
    user = db.scalar(select(User).where(or_(User.email == key, User.username == key)))
    # A fixed bcrypt workload for unknown accounts reduces timing differences.
    dummy = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6Ttx2M3kyE/JDFrjKkL9lHfYzvF5K"
    good = verify(body.password, user.password_hash if user else dummy)
    if not user or not good:
        if user:
            user.failed += 1
            if user.failed >= 5:
                user.locked_until = now() + timedelta(minutes=15)
            db.commit()
        raise HTTPException(401, "Invalid login details or account unavailable.")
    if user.suspended or (user.locked_until and user.locked_until > now()):
        raise HTTPException(
            403, "Account unavailable. Contact an administrator or try later."
        )
    user.failed = 0
    user.locked_until = None
    user.last_active = now()
    csrf = issue(db, user, response)
    return {"user": public_user(user), "csrf": csrf}


@router.get("/me")
def me(request: Request, user=Depends(identity)):
    return {
        "user": public_user(user),
        "csrf": request.state.session.csrf,
        "impersonating": bool(request.state.claims.get("actor")),
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    request.state.session.revoked = True
    if request.state.claims.get("parent"):
        parent = db.get(Session, request.state.claims["parent"])
        if parent:
            parent.revoked = True
    response.delete_cookie(COOKIE, path="/")
    return {"message": "Signed out."}


@router.put("/profile")
def profile(body: Profile, user=Depends(identity)):
    for key, value in body.model_dump().items():
        setattr(user, key, value)
    return {"user": public_user(user), "message": "Profile updated."}


@router.post("/password")
def password(
    body: Password,
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    if request.state.claims.get("actor"):
        raise HTTPException(403, "Password changes are disabled while impersonating.")
    if not verify(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    password_check(body.password)
    if verify(body.password, user.password_hash):
        raise HTTPException(422, "Choose a different password.")
    user.password_hash = hash_password(body.password)
    user.must_change = False
    revoke_all(db, user)
    db.execute(update(Reset).where(Reset.user_id == user.id).values(used=True))
    csrf = issue(db, user, response)
    return {
        "message": "Password changed. Other sessions were revoked.",
        "csrf": csrf,
        "user": public_user(user),
    }


@router.post("/forgot")
def forgot(body: Forgot, request: Request, db=Depends(get_db, scope="function")):
    public_guard(request, db, "forgot", 5)
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if user and not user.suspended:
        link = create_reset(db, user)
        db.commit()
        try:
            send_reset(user.email, link)
        except Exception:
            logging.getLogger("predictpro").error(
                "Password reset delivery failed; check SMTP configuration."
            )
    return {
        "message": "If that account can recover, a reset email has been sent. Local development writes email to backend/outbox."
    }


@router.post("/reset")
def reset(body: ResetInput, request: Request, db=Depends(get_db, scope="function")):
    public_guard(request, db, "reset", 10)
    password_check(body.password)
    # Atomic token consumption prevents concurrent reuse.
    uid = db.execute(
        update(Reset)
        .where(
            Reset.digest == digest(body.token),
            Reset.used == False,
            Reset.expires_at > now(),
        )
        .values(used=True)
        .returning(Reset.user_id)
    ).scalar_one_or_none()
    if not uid:
        raise HTTPException(400, "Reset link is invalid or expired.")
    user = db.get(User, uid)
    if user.suspended:
        raise HTTPException(403, "Ask an administrator to activate your account.")
    user.password_hash = hash_password(body.password)
    user.must_change = False
    user.failed = 0
    user.locked_until = None
    revoke_all(db, user)
    return {"message": "Password reset. Sign in with your new password."}
````

## backend/routes/user.py

````python
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from backend.db import get_db
from backend.middleware.auth import identity
from backend.controllers.common import require
from backend.controllers.matches import match_json
from backend.models.entities import (
    User,
    Match,
    Team,
    League,
    Pick,
    Favorite,
    Follow,
    Notification,
    Prediction,
    now,
)
from backend.schemas import PickInput
from backend.services.prediction import outcome

router = APIRouter(prefix="/api", dependencies=[Depends(identity)], tags=["Football"])


@router.get("/catalog")
def catalog(user=Depends(identity), db=Depends(get_db, scope="function")):
    return {
        "leagues": [
            {"id": x.id, "name": x.name, "code": x.code}
            for x in db.scalars(select(League).order_by(League.name))
        ],
        "teams": [
            {
                "id": x.id,
                "name": x.name,
                "league_id": x.league_id,
                "favorite": db.get(Favorite, (user.id, x.id)) is not None,
            }
            for x in db.scalars(select(Team).order_by(Team.name))
        ],
    }


@router.get("/matches")
def matches(
    league: int | None = None,
    date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    team: int | None = None,
    search: str = Query("", max_length=100),
    status: str = Query("SCHEDULED", pattern="^(SCHEDULED|FINISHED|ALL)$"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    q = select(Match)
    if status != "ALL":
        q = q.where(Match.status == status)
    if league:
        q = q.where(Match.league_id == league)
    if team:
        q = q.where((Match.home_id == team) | (Match.away_id == team))
    if date:
        q = q.where(func.date(Match.kickoff) == date)
    if search:
        ids = select(Team.id).where(Team.name.icontains(search, autoescape=True))
        q = q.where(Match.home_id.in_(ids) | Match.away_id.in_(ids))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.order_by(Match.kickoff.desc() if status == "FINISHED" else Match.kickoff)
    return {
        "items": [
            match_json(db, m, user.id)
            for m in db.scalars(q.limit(limit).offset(offset))
        ],
        "total": total,
    }


@router.get("/matches/{mid}")
def match(mid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    return match_json(db, require(db, Match, mid), user.id, True)


@router.post("/matches/{mid}/pick")
def pick(
    mid: int,
    body: PickInput,
    request: Request,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    if request.state.claims.get("actor"):
        raise HTTPException(403, "Picks are disabled while impersonating.")
    m = require(db, Match, mid)
    # Acquire a write lock before checking the deadline and existing pick.
    from sqlalchemy import update

    db.execute(update(Match).where(Match.id == mid).values(status=Match.status))
    db.refresh(m)
    if m.status != "SCHEDULED" or m.kickoff <= now():
        raise HTTPException(409, "Picks close at kickoff.")
    p = db.scalar(select(Pick).where(Pick.user_id == user.id, Pick.match_id == mid))
    if p:
        p.outcome = body.outcome
    else:
        db.add(Pick(user_id=user.id, match_id=mid, outcome=body.outcome))
    return {"message": "Pick saved. You can change it until kickoff."}


@router.post("/matches/{mid}/follow")
def follow(mid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    m = require(db, Match, mid)
    old = db.get(Follow, (user.id, mid))
    if old:
        db.delete(old)
    else:
        if m.status != "SCHEDULED" or m.kickoff <= now():
            raise HTTPException(409, "Follow upcoming matches before kickoff.")
        db.add(Follow(user_id=user.id, match_id=mid))
    return {
        "message": "Match unfollowed."
        if old
        else "Following: a notification will appear when a result is recorded."
    }


@router.post("/favorites/{tid}")
def favorite(tid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    require(db, Team, tid)
    old = db.get(Favorite, (user.id, tid))
    if old:
        db.delete(old)
    else:
        db.add(Favorite(user_id=user.id, team_id=tid))
    return {"message": "Favorite removed." if old else "Favorite added."}


@router.get("/history")
def history(
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
    offset: int = Query(0, ge=0),
):
    rows = list(
        db.scalars(
            select(Match)
            .join(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(50)
            .offset(offset)
        )
    )
    return {"items": [match_json(db, m, user.id) for m in rows], "offset": offset}


@router.get("/leaderboard")
def leaderboard(db=Depends(get_db, scope="function")):
    results = []
    for u in db.scalars(select(User).where(User.suspended == False)):
        pairs = db.execute(
            select(Pick, Match)
            .join(Match, Match.id == Pick.match_id)
            .where(
                Pick.user_id == u.id,
                Match.status == "FINISHED",
                Pick.created_at < Match.kickoff,
            )
        ).all()
        if not pairs:
            continue
        hits = sum(p.outcome == outcome(m.home_goals, m.away_goals) for p, m in pairs)
        results.append(
            {
                "name": u.username,
                "correct": hits,
                "total": len(pairs),
                "points": hits * 3,
                "accuracy": hits / len(pairs),
                "kind": "user",
            }
        )
    for source in ("live", "sample", "manual"):
        pairs = db.execute(
            select(Prediction, Match)
            .join(Match, Match.id == Prediction.match_id)
            .where(
                Prediction.correct.is_not(None),
                Prediction.eligible == True,
                Match.source == source,
            )
        ).all()
        if pairs:
            hits = sum(p.correct for p, m in pairs)
            results.append(
                {
                    "name": f"PredictPro AI · {source}",
                    "correct": hits,
                    "total": len(pairs),
                    "points": hits * 3,
                    "accuracy": hits / len(pairs),
                    "kind": "AI",
                }
            )
    return sorted(results, key=lambda x: (-x["points"], -x["accuracy"], x["name"]))


@router.get("/notifications")
def notifications(user=Depends(identity), db=Depends(get_db, scope="function")):
    return [
        {
            "id": n.id,
            "text": n.text,
            "read": n.read,
            "created_at": n.created_at,
            "match_id": n.match_id,
        }
        for n in db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/notifications/{nid}/read")
def read(nid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    n = require(db, Notification, nid)
    if n.user_id != user.id:
        raise HTTPException(404, "Notification not found.")
    n.read = True
    return {"message": "Notification marked as read."}


@router.get("/metrics")
def metrics(db=Depends(get_db, scope="function")):
    return model_metrics(db)


def model_metrics(db):
    groups = {}
    trend = []
    pairs = db.execute(
        select(Prediction, Match)
        .join(Match, Match.id == Prediction.match_id)
        .where(Prediction.correct.is_not(None))
        .order_by(Match.kickoff)
    ).all()
    for p, m in pairs:
        key = m.source if p.eligible else m.source + " backtest"
        group = groups.setdefault(key, {"total": 0, "correct": 0, "brier_sum": 0.0})
        group["total"] += 1
        group["correct"] += int(p.correct)
        group["brier_sum"] += p.brier or 0
        if p.eligible:
            trend.append(
                {
                    "date": m.kickoff.date().isoformat(),
                    "source": m.source,
                    "correct": int(p.correct),
                    "brier": p.brier,
                }
            )
    for g in groups.values():
        g.update(
            accuracy=g["correct"] / g["total"], brier=g.pop("brier_sum") / g["total"]
        )
    return {
        "groups": groups,
        "trend": trend,
        "note": "Only predictions frozen before kickoff enter prospective accuracy. Synthetic backtests are separate. Brier score: lower is better (0–2).",
    }
````

## backend/schemas.py

````python
from datetime import datetime, timezone
from typing import Literal
import re
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


class Profile(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{3,30}$")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        if "<" in v or ">" in v or not v.strip():
            raise ValueError("Use plain text for names.")
        return v.strip()

    @field_validator("email", "username")
    @classmethod
    def lower(cls, v):
        return str(v).lower()


class Signup(Profile):
    password: str = Field(min_length=10, max_length=72)


class Login(BaseModel):
    login: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class Password(BaseModel):
    current_password: str = Field(max_length=72)
    password: str = Field(min_length=10, max_length=72)


class Forgot(BaseModel):
    email: EmailStr


class ResetInput(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=10, max_length=72)


class UserCreate(Signup):
    role: Literal["ADMIN", "USER"] = "USER"


class UserEdit(Profile):
    role: Literal["ADMIN", "USER"] = "USER"


class StateInput(BaseModel):
    suspended: bool


class PickInput(BaseModel):
    outcome: Literal["Home", "Draw", "Away"]


class LeagueInput(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^<>]+$")
    code: str = Field(pattern=r"^[A-Z0-9_]{2,12}$")


class TeamInput(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^<>]+$")
    league_id: int = Field(gt=0)


class MatchInput(BaseModel):
    league_id: int = Field(gt=0)
    home_id: int = Field(gt=0)
    away_id: int = Field(gt=0)
    kickoff: datetime
    status: Literal["SCHEDULED", "FINISHED", "POSTPONED", "CANCELLED"] = "SCHEDULED"
    home_goals: int | None = Field(default=None, ge=0, le=50)
    away_goals: int | None = Field(default=None, ge=0, le=50)

    @model_validator(mode="after")
    def consistent(self):
        if self.kickoff.tzinfo is None:
            raise ValueError("Kickoff must include a timezone.")
        self.kickoff = self.kickoff.astimezone(timezone.utc).replace(tzinfo=None)
        if self.home_id == self.away_id:
            raise ValueError("Teams must differ.")
        if self.status == "FINISHED" and (
            self.home_goals is None or self.away_goals is None
        ):
            raise ValueError("Finished matches require both scores.")
        if self.status != "FINISHED" and (
            self.home_goals is not None or self.away_goals is not None
        ):
            raise ValueError("Scores are only accepted for finished matches.")
        return self


class SettingsInput(BaseModel):
    site_name: str = Field(min_length=2, max_length=60, pattern=r"^[^<>]+$")
    maintenance: bool
    api_key: str | None = Field(default=None, max_length=150)
````

## backend/seed/__init__.py

````python
"""PredictPro application package."""
````

## backend/seed/sample.json

````json
{
  "notice": "SYNTHETIC educational data. Team names are illustrative; fixtures and scores are not real sporting records.",
  "seed": 1047,
  "leagues": [
    {"code":"DEMO_PL","name":"Premier League · Demo","teams":["Manchester United · Demo","Arsenal · Demo","Liverpool · Demo","Manchester City · Demo","Chelsea · Demo","Newcastle · Demo"]},
    {"code":"DEMO_PD","name":"La Liga · Demo","teams":["Real Madrid · Demo","Barcelona · Demo","Atletico · Demo","Sevilla · Demo","Villarreal · Demo","Athletic Club · Demo"]}
  ]
}
````

## backend/seed/seed.py

````python
"""Idempotent seed: exactly one initial admin; deterministic synthetic seasons."""

import json
import os
import random
import math
from pathlib import Path
from datetime import timedelta
from sqlalchemy import select
from backend.db import SessionLocal
from backend.models.entities import User, League, Team, Match, Setting, now
from backend.utils.security import hash_password
from backend.services.prediction import get_prediction, evaluate


def poisson(rng, lam):
    value = 0
    p = 1.0
    limit = math.exp(-lam)
    while p > limit:
        value += 1
        p *= rng.random()
    return value - 1


def seed_sample(db):
    data = json.loads(Path(__file__).with_name("sample.json").read_text())
    rng = random.Random(data["seed"])
    added = 0
    for info in data["leagues"]:
        if db.scalar(select(League).where(League.code == info["code"])):
            continue
        league = League(name=info["name"], code=info["code"])
        db.add(league)
        db.flush()
        teams = [Team(name=n, league_id=league.id) for n in info["teams"]]
        db.add_all(teams)
        db.flush()
        base = now().replace(hour=15, minute=0, second=0, microsecond=0)
        # Ten rounds with all directed pairs. No future result is used to predict a prior game.
        idx = 0
        for round_no in range(3):
            for hi, h in enumerate(teams):
                for ai, a in enumerate(teams):
                    if hi == ai:
                        continue
                    idx += 1
                    m = Match(
                        league_id=league.id,
                        home_id=h.id,
                        away_id=a.id,
                        kickoff=base - timedelta(days=190 - idx * 2),
                        status="FINISHED",
                        home_goals=poisson(rng, 1.8 - hi * 0.12),
                        away_goals=poisson(rng, 1.35 - ai * 0.09),
                        source="sample",
                    )
                    db.add(m)
                    db.flush()
                    p = get_prediction(db, m, retrospective=True)
                    # Backtest rows are explicitly ineligible for live accuracy.
                    evaluate(db, m)
                    added += 1
        for i in range(6):
            h, a = teams[i], teams[(i + 1) % len(teams)]
            m = Match(
                league_id=league.id,
                home_id=h.id,
                away_id=a.id,
                kickoff=base + timedelta(days=i + 1),
                source="sample",
                status="SCHEDULED",
            )
            db.add(m)
            db.flush()
            get_prediction(db, m)
            added += 1
    return added


def main():
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.role == "ADMIN")):
            username = os.getenv("SEED_ADMIN_USERNAME")
            password = os.getenv("SEED_ADMIN_PASSWORD")
            if not username or not password:
                raise RuntimeError(
                    "Set SEED_ADMIN_USERNAME and SEED_ADMIN_PASSWORD in .env."
                )
            db.add(
                User(
                    name="PredictPro Administrator",
                    email=os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").lower(),
                    username=username.lower(),
                    password_hash=hash_password(password),
                    role="ADMIN",
                    must_change=True,
                )
            )
        if not db.get(Setting, "site_name"):
            db.add(Setting(key="site_name", value="PredictPro"))
        if not db.get(Setting, "maintenance"):
            db.add(Setting(key="maintenance", value="false"))
        count = seed_sample(db)
        db.commit()
        print(
            f"Seed complete: {count} synthetic matches added. Initial administrator must change password."
        )


if __name__ == "__main__":
    main()
````

## backend/services/__init__.py

````python
"""PredictPro application package."""
````

## backend/services/football.py

````python
import json
import os
from datetime import datetime
from sqlalchemy import select
import httpx
from backend.models.entities import League, Team, Match, Follow, Notification, now
from backend.services.prediction import get_prediction, evaluate


def notify_result(db, m):
    if m.status != "FINISHED":
        return
    evaluate(db, m)
    home, away = db.get(Team, m.home_id), db.get(Team, m.away_id)
    for follow in db.scalars(select(Follow).where(Follow.match_id == m.id)):
        if not db.scalar(
            select(Notification).where(
                Notification.user_id == follow.user_id, Notification.match_id == m.id
            )
        ):
            db.add(
                Notification(
                    user_id=follow.user_id,
                    match_id=m.id,
                    text=f"{home.name} {m.home_goals}–{m.away_goals} {away.name}: full time.",
                )
            )


def fetch_competition(code, key):
    with httpx.Client(timeout=20) as client:
        response = client.get(
            f"https://api.football-data.org/v4/competitions/{code}/matches",
            headers={"X-Auth-Token": key},
        )
        response.raise_for_status()
        return response.json()


def refresh(db):
    from backend.models.entities import Setting

    saved = db.get(Setting, "api_key")
    key = saved.value if saved else os.getenv("FOOTBALL_API_KEY", "")
    if not key:
        from backend.seed.seed import seed_sample

        added = seed_sample(db)
        return {
            "source": "sample",
            "message": "No API key. Bundled synthetic data retained or loaded; no real results invented.",
            "added": added,
        }
    count = 0
    errors = []
    for code in os.getenv("FOOTBALL_COMPETITIONS", "PL,PD").split(","):
        code = code.strip()
        if not code or not code.isalnum():
            continue
        try:
            data = fetch_competition(code, key)
            league = db.scalar(select(League).where(League.code == code))
            if not league:
                league = League(
                    code=code, name=data.get("competition", {}).get("name", code)
                )
                db.add(league)
                db.flush()
            for row in sorted(data.get("matches", []), key=lambda r: r["utcDate"]):
                if not row.get("homeTeam", {}).get("id") or not row.get(
                    "awayTeam", {}
                ).get("id"):
                    continue
                teams = []
                for field in ("homeTeam", "awayTeam"):
                    item = row[field]
                    team = db.scalar(select(Team).where(Team.external_id == item["id"]))
                    if not team:
                        team = Team(
                            name=item["name"],
                            league_id=league.id,
                            external_id=item["id"],
                        )
                        db.add(team)
                        db.flush()
                    teams.append(team)
                kick = datetime.fromisoformat(
                    row["utcDate"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                status = row["status"]
                score = row.get("score", {}).get("fullTime", {})
                if status in ("SCHEDULED", "TIMED"):
                    status = "SCHEDULED"
                elif status == "FINISHED":
                    if score.get("home") is None or score.get("away") is None:
                        continue
                elif status == "POSTPONED":
                    status = "POSTPONED"
                elif status == "CANCELLED":
                    status = "CANCELLED"
                else:
                    continue  # Do not mislabel in-play, suspended or unknown states.
                m = db.scalar(select(Match).where(Match.external_id == row["id"]))
                if not m:
                    m = Match(
                        external_id=row["id"],
                        league_id=league.id,
                        home_id=teams[0].id,
                        away_id=teams[1].id,
                        kickoff=kick,
                        source="live",
                    )
                    db.add(m)
                m.status = status
                m.kickoff = kick
                m.home_goals = score.get("home") if status == "FINISHED" else None
                m.away_goals = score.get("away") if status == "FINISHED" else None
                db.flush()
                notify_result(db, m)
                count += 1
            db.commit()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            db.rollback()
            errors.append(
                f"{code}: {type(exc).__name__}; check API plan, key and connectivity."
            )
    for m in db.scalars(
        select(Match).where(Match.status == "SCHEDULED", Match.kickoff > now())
    ):
        get_prediction(db, m)
    if not count:
        from backend.seed.seed import seed_sample

        seed_sample(db)
    return {
        "source": "live" if count else "sample",
        "synced": count,
        "errors": errors,
        "message": "Live sync complete."
        if count
        else "Sync unavailable. Existing bundled data remains usable.",
    }
````

## backend/services/prediction.py

````python
"""Independent Poisson goals with shrunk strengths, chronological Elo and form.
All feature rows precede kickoff. Predictions are immutable pre-match snapshots.
"""

import json
import math
from collections import defaultdict
from datetime import timedelta
from sqlalchemy import select
from backend.models.entities import Match, Prediction, Setting, Team, now

OUTCOMES = ("Home", "Draw", "Away")
BASE_VERSION = "poisson-elo-v1"


def outcome(h, a):
    return "Home" if h > a else "Away" if a > h else "Draw"


def goals(lam):
    # 0..24 retains effectively all mass for capped means <= 4.5.
    values = [math.exp(-lam)]
    for k in range(1, 25):
        values.append(values[-1] * lam / k)
    return values


def calculate(home_id, away_id, history, elo_weight=0.18):
    ratings = defaultdict(lambda: 1500.0)
    for m in history:
        expected = 1 / (
            1 + 10 ** ((ratings[m.away_id] - ratings[m.home_id] - 65) / 400)
        )
        actual = (
            1
            if m.home_goals > m.away_goals
            else 0
            if m.home_goals < m.away_goals
            else 0.5
        )
        change = 24 * (actual - expected)
        ratings[m.home_id] += change
        ratings[m.away_id] -= change
    n = len(history)
    home_mean = (sum(m.home_goals for m in history) + 1.45 * 20) / (n + 20)
    away_mean = (sum(m.away_goals for m in history) + 1.15 * 20) / (n + 20)
    league_mean = (home_mean + away_mean) / 2

    def team_stats(tid):
        rows = [m for m in history if tid in (m.home_id, m.away_id)][-10:]
        gf = ga = points = 0
        form = []
        for m in rows:
            g, c = (
                (m.home_goals, m.away_goals)
                if m.home_id == tid
                else (m.away_goals, m.home_goals)
            )
            gf += g
            ga += c
            points += 3 if g > c else 1 if g == c else 0
            form.append("W" if g > c else "D" if g == c else "L")
        # Five pseudo-matches shrink small samples to league average.
        return (
            (gf + 5 * league_mean) / (len(rows) + 5) / league_mean,
            (ga + 5 * league_mean) / (len(rows) + 5) / league_mean,
            (points + 5 * 1.35) / (len(rows) + 5),
            form[-5:],
            len(rows),
        )

    ha, hd, hp, hform, hn = team_stats(home_id)
    aa, ad, ap, aform, an = team_stats(away_id)
    elo_edge = max(-0.4, min(0.4, (ratings[home_id] - ratings[away_id]) / 800))
    form_edge = max(-0.12, min(0.12, (hp - ap) * 0.055))
    h2h = [m for m in history if {m.home_id, m.away_id} == {home_id, away_id}][-5:]
    edge = 0
    for m in h2h:
        edge += (
            (m.home_goals - m.away_goals)
            if m.home_id == home_id
            else (m.away_goals - m.home_goals)
        )
    h2h_edge = max(-0.06, min(0.06, edge / (len(h2h) + 5) * 0.03))
    xh = home_mean * ha * ad * math.exp(elo_weight * elo_edge + form_edge + h2h_edge)
    xa = away_mean * aa * hd * math.exp(-elo_weight * elo_edge - form_edge - h2h_edge)
    xh = max(0.2, min(4.5, xh))
    xa = max(0.2, min(4.5, xa))
    ph, pa = goals(xh), goals(xa)
    probs = dict.fromkeys(OUTCOMES, 0.0)
    over = btts = total = 0.0
    best = (0, 0, 0.0)
    for h, hprob in enumerate(ph):
        for a, aprob in enumerate(pa):
            p = hprob * aprob
            total += p
            probs[outcome(h, a)] += p
            if h + a > 2:
                over += p
            if h > 0 and a > 0:
                btts += p
            if p > best[2]:
                best = (h, a, p)
    probs = {k: v / total for k, v in probs.items()}
    winner = max(probs, key=probs.get)
    confidence = (
        "Higher"
        if probs[winner] >= 0.65 and min(hn, an) >= 8
        else "Moderate"
        if probs[winner] >= 0.48 and min(hn, an) >= 5
        else "Low"
    )
    return {
        "probabilities": probs,
        "expected_goals": {"home": xh, "away": xa},
        "scoreline": f"{best[0]}–{best[1]}",
        "over25": over / total,
        "under25": 1 - over / total,
        "btts": btts / total,
        "outcome": winner,
        "confidence": confidence,
        "home_form": hform,
        "away_form": aform,
        "elo": {"home": round(ratings[home_id]), "away": round(ratings[away_id])},
        "sample_sizes": {"home": hn, "away": an, "league": n, "head_to_head": len(h2h)},
        "explanation": [
            f"League scoring baseline is {home_mean:.2f} home and {away_mean:.2f} away goals; this includes home advantage.",
            f"Recent scoring and conceding strengths use up to ten matches per team, shrunk toward the league average with five pseudo-matches.",
            f"Elo ratings are {ratings[home_id]:.0f} versus {ratings[away_id]:.0f}; form points per match are {hp:.2f} versus {ap:.2f}.",
            f"{len(h2h)} earlier head-to-head meetings contribute a capped adjustment of {h2h_edge:+.3f}.",
            f"The independent Poisson model estimates {xh:.2f} and {xa:.2f} goals. {winner} is the largest outcome probability ({probs[winner]:.1%}).",
            "Confidence is a probability-and-sample-size label, not a calibrated guarantee. Injuries, lineups and red cards are not modeled.",
        ],
        "assumptions": "Independent goals; stable recent strength; league priors 1.45 home / 1.15 away for sparse data.",
    }


def history_for(db, m):
    return list(
        db.scalars(
            select(Match)
            .where(
                Match.league_id == m.league_id,
                Match.source == m.source,
                Match.status == "FINISHED",
                Match.kickoff < m.kickoff,
                Match.kickoff >= m.kickoff - timedelta(days=730),
            )
            .order_by(Match.kickoff, Match.id)
        )
    )


def get_prediction(db, m, retrospective=False):
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    if p:
        return p
    config = db.get(Setting, "model")
    settings = (
        json.loads(config.value)
        if config
        else {"elo_weight": 0.18, "version": BASE_VERSION}
    )
    data = calculate(m.home_id, m.away_id, history_for(db, m), settings["elo_weight"])
    eligible = m.status == "SCHEDULED" and m.kickoff > now() and not retrospective
    p = Prediction(
        match_id=m.id,
        payload=json.dumps(data),
        model_version=settings["version"],
        eligible=eligible,
    )
    db.add(p)
    db.flush()
    return p


def evaluate(db, m):
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    if not p or m.status != "FINISHED":
        return
    data = json.loads(p.payload)
    actual = outcome(m.home_goals, m.away_goals)
    p.correct = data["outcome"] == actual
    p.brier = sum(
        (data["probabilities"][k] - (1 if k == actual else 0)) ** 2 for k in OUTCOMES
    )


def retrain(db):
    # Walk-forward grid calibration on past results; future fixtures never enter training.
    rows = list(
        db.scalars(
            select(Match)
            .where(Match.status == "FINISHED", Match.kickoff < now())
            .order_by(Match.kickoff, Match.id)
        )
    )
    scored = []
    for weight in (0.0, 0.18, 0.4):
        losses = []
        for i, m in enumerate(rows):
            past = [
                x
                for x in rows[:i]
                if x.league_id == m.league_id
                and x.source == m.source
                and x.kickoff < m.kickoff
            ]
            if len(past) < 20:
                continue
            pred = calculate(m.home_id, m.away_id, past, weight)
            losses.append(
                sum(
                    (
                        pred["probabilities"][k]
                        - (k == outcome(m.home_goals, m.away_goals))
                    )
                    ** 2
                    for k in OUTCOMES
                )
            )
        if losses:
            scored.append((sum(losses) / len(losses), weight, len(losses)))
    if not scored:
        return {
            "message": "Need at least 21 earlier results within a league and source. Existing model retained."
        }
    loss, weight, n = min(scored)
    report = {
        "elo_weight": weight,
        "version": BASE_VERSION + "-" + now().strftime("%Y%m%d%H%M%S"),
        "walk_forward_brier": loss,
        "validation_matches": n,
        "note": "Tuning-set walk-forward score, not independent test accuracy. Includes synthetic data if present. Existing snapshots remain unchanged.",
    }
    setting = db.get(Setting, "model")
    if setting:
        setting.value = json.dumps(report)
    else:
        db.add(Setting(key="model", value=json.dumps(report)))
    return report
````

## backend/services/recovery.py

````python
import json
import os
import secrets
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote
from sqlalchemy import update
from backend.config import URL, ENV, ROOT
from backend.models.entities import Reset, now
from backend.utils.security import digest


def create_reset(db, user):
    db.execute(update(Reset).where(Reset.user_id == user.id).values(used=True))
    token = secrets.token_urlsafe(32)
    db.add(
        Reset(
            user_id=user.id,
            digest=digest(token),
            expires_at=now() + timedelta(minutes=30),
        )
    )
    return f"{URL}/#reset?token={quote(token)}"


def send_reset(email, link):
    message = EmailMessage()
    message["Subject"] = "Reset your PredictPro password"
    message["From"] = os.getenv("SMTP_FROM", "noreply@predictpro.local")
    message["To"] = email
    message.set_content(
        f"Use this one-time link within 30 minutes:\n{link}\nIf you did not request this, ignore this email."
    )
    host = os.getenv("SMTP_HOST")
    if host:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
            if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                smtp.starttls()
            if os.getenv("SMTP_USERNAME"):
                smtp.login(os.environ["SMTP_USERNAME"], os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(message)
    elif ENV != "production":
        folder = ROOT / "backend" / "outbox"
        folder.mkdir(mode=0o700, exist_ok=True)
        path = folder / (secrets.token_hex(12) + ".eml")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(str(message))
    else:
        raise RuntimeError("SMTP is not configured.")
````

## backend/tests/conftest.py

````python
import os
from pathlib import Path

os.environ["JWT_SECRET"] = "tests-use-an-isolated-signing-key-0123456789abcdef"
os.environ["DATABASE_URL"] = "sqlite:///./test_predictpro.db"
os.environ["APP_ENV"] = "development"
os.environ["APP_URL"] = "http://testserver"
os.environ["SEED_ADMIN_USERNAME"] = "admin"
os.environ["SEED_ADMIN_PASSWORD"] = "benard"
os.environ["SEED_ADMIN_EMAIL"] = "admin@predictpro.local"
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import engine, SessionLocal
from backend.models.entities import Base
from backend.seed.seed import main


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    main()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def login(client, name="admin", password="benard"):
    r = client.post("/api/auth/login", json={"login": name, "password": password})
    assert r.status_code == 200, r.text
    csrf = r.json()["csrf"]
    if name == "admin" and r.json()["user"]["must_change"]:
        r = client.post(
            "/api/auth/password",
            json={"current_password": password, "password": "Admin-secure-2026!"},
            headers={"x-csrf-token": csrf},
        )
        assert r.status_code == 200, r.text
        csrf = r.json()["csrf"]
    return {"x-csrf-token": csrf}


def signup(client, name="benard"):
    r = client.post(
        "/api/auth/signup",
        json={
            "name": "Benard Test",
            "username": name,
            "email": name + "@example.com",
            "password": "Test-password-2026!",
        },
    )
    assert r.status_code == 201, r.text
    return {"x-csrf-token": r.json()["csrf"]}, r.json()["user"]
````

## backend/tests/test_prediction.py

````python
import json
from datetime import timedelta
from sqlalchemy import select
from conftest import login, signup
from backend.models.entities import Match, Prediction, now
from backend.services.prediction import (
    calculate,
    get_prediction,
    evaluate,
    history_for,
    retrain,
)


def test_poisson_distribution():
    p = calculate(1, 2, [])
    assert abs(sum(p["probabilities"].values()) - 1) < 1e-9
    assert abs(p["over25"] + p["under25"] - 1) < 1e-9
    assert 0 <= p["btts"] <= 1
    assert p["expected_goals"]["home"] > p["expected_goals"]["away"]
    assert p["confidence"] == "Low" and len(p["explanation"]) >= 5


def test_snapshots_no_leakage_and_metrics(client, db):
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    p = get_prediction(db, m)
    snapshot = p.payload
    assert all(x.kickoff < m.kickoff for x in history_for(db, m))
    m.status = "FINISHED"
    m.home_goals = 2
    m.away_goals = 1
    evaluate(db, m)
    db.commit()
    assert get_prediction(db, m).payload == snapshot
    assert p.correct is not None and 0 <= p.brier <= 2
    h, u = signup(client)
    metrics = client.get("/api/metrics").json()
    assert "sample backtest" in metrics["groups"]
    assert "live" not in metrics["groups"]


def test_history_cannot_read_future_results(client, db):
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    original = calculate(m.home_id, m.away_id, history_for(db, m))
    future = Match(
        league_id=m.league_id,
        home_id=m.home_id,
        away_id=m.away_id,
        kickoff=m.kickoff + timedelta(days=1),
        status="FINISHED",
        home_goals=40,
        away_goals=0,
        source=m.source,
    )
    db.add(future)
    db.flush()
    assert calculate(m.home_id, m.away_id, history_for(db, m)) == original


def test_pick_deadline_follow_and_notification(client, db):
    h, u = signup(client)
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    assert (
        client.post(
            f"/api/matches/{m.id}/pick", json={"outcome": "Home"}, headers=h
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/matches/{m.id}/follow", json={}, headers=h).status_code
        == 200
    )
    from backend.services.football import notify_result

    m.kickoff = now() - timedelta(days=1)
    m.status = "FINISHED"
    m.home_goals = 2
    m.away_goals = 0
    notify_result(db, m)
    notify_result(db, m)
    db.commit()
    assert (
        client.post(
            f"/api/matches/{m.id}/pick", json={"outcome": "Away"}, headers=h
        ).status_code
        == 409
    )
    rows = client.get("/api/notifications").json()
    assert len(rows) == 1
    assert (
        client.post(
            "/api/notifications/" + str(rows[0]["id"]) + "/read", json={}, headers=h
        ).status_code
        == 200
    )


def test_offline_sync_and_calibration(client, db, monkeypatch):
    monkeypatch.delenv("FOOTBALL_API_KEY", raising=False)
    h = login(client)
    assert (
        client.post("/api/admin/sync", json={}, headers=h).json()["source"] == "sample"
    )
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    snapshot = get_prediction(db, m).payload
    result = client.post("/api/admin/retrain", json={}, headers=h)
    assert result.status_code == 200 and result.json()["validation_matches"] > 0
    assert get_prediction(db, m).payload == snapshot


def test_catalog_crud_and_settings(client):
    h = login(client)
    r = client.post(
        "/api/admin/leagues",
        json={"name": "Uganda Test League", "code": "UG_TEST"},
        headers=h,
    )
    assert r.status_code == 201
    lid = r.json()["id"]
    r = client.post(
        "/api/admin/teams",
        json={"name": "Kabale Test Team", "league_id": lid},
        headers=h,
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    assert client.delete("/api/admin/leagues/" + str(lid), headers=h).status_code == 409
    assert (
        client.put(
            "/api/admin/teams/" + str(tid),
            json={"name": "Kabale Renamed", "league_id": lid},
            headers=h,
        ).status_code
        == 200
    )
    assert client.delete("/api/admin/teams/" + str(tid), headers=h).status_code == 200
    assert client.delete("/api/admin/leagues/" + str(lid), headers=h).status_code == 200
    assert (
        client.put(
            "/api/admin/settings",
            json={"site_name": "PredictPro Uganda", "maintenance": True},
            headers=h,
        ).status_code
        == 200
    )
    h, u = signup(client, "other")
    assert client.get("/api/matches").status_code == 503


def test_live_ingestion_and_filters(client, monkeypatch):
    from datetime import datetime, timezone

    h = login(client)
    monkeypatch.setenv("FOOTBALL_API_KEY", "test-api-key")
    monkeypatch.setenv("FOOTBALL_COMPETITIONS", "PL")
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "competition": {"name": "Premier League"},
        "matches": [
            {
                "id": 900001,
                "utcDate": future,
                "status": "TIMED",
                "homeTeam": {"id": 10001, "name": "Live Home"},
                "awayTeam": {"id": 10002, "name": "Live Away"},
                "score": {"fullTime": {"home": None, "away": None}},
            }
        ],
    }
    monkeypatch.setattr(
        "backend.services.football.fetch_competition", lambda *args, **kwargs: payload
    )
    assert client.post("/api/admin/sync", json={}, headers=h).json()["synced"] == 1
    assert client.post("/api/admin/sync", json={}, headers=h).json()["synced"] == 1
    rows = client.get("/api/matches?search=Live%20Home").json()["items"]
    assert len(rows) == 1 and rows[0]["source"] == "live" and rows[0]["eligible"]
    tid = rows[0]["home_id"]
    lid = rows[0]["league_id"]
    assert len(client.get(f"/api/matches?team={tid}&league={lid}").json()["items"]) == 1
    assert client.get("/api/matches?date=" + future[:10]).json()["total"] >= 1


def test_live_failure_retains_offline_data(client, monkeypatch):
    import httpx

    h = login(client)
    monkeypatch.setenv("FOOTBALL_API_KEY", "unavailable-key")
    monkeypatch.setenv("FOOTBALL_COMPETITIONS", "PL")

    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr("backend.services.football.fetch_competition", unavailable)
    result = client.post("/api/admin/sync", json={}, headers=h)
    assert result.status_code == 200 and result.json()["source"] == "sample"
    assert client.get("/api/matches").json()["total"] == 12
````

## backend/tests/test_security.py

````python
from datetime import timedelta
from sqlalchemy import select
from conftest import login, signup
from backend.models.entities import User, Audit, Reset, now
from backend.utils.security import hash_password, verify


def test_admin_hash_and_forced_change(client, db):
    u = db.scalar(select(User).where(User.username == "admin"))
    assert u.password_hash != "benard" and verify("benard", u.password_hash)
    r = client.post("/api/auth/login", json={"login": "admin", "password": "benard"})
    assert (
        "HttpOnly" in r.headers["set-cookie"]
        and "SameSite=strict" in r.headers["set-cookie"]
    )
    assert client.get("/api/admin/overview").status_code == 403
    login(client)
    assert client.get("/api/admin/overview").status_code == 200


def test_auth_role_and_csrf(client):
    assert client.get("/api/matches").status_code == 401
    headers, u = signup(client)
    assert client.get("/api/admin/users").status_code == 403
    assert (
        client.put(
            "/api/auth/profile",
            json={"name": "X X", "email": "x@example.com", "username": "xxx"},
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/api/auth/profile",
            json={"name": "X X", "email": "x@example.com", "username": "xxx"},
            headers={**headers, "origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout", json={}, headers=headers).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_input_and_sql_injection(client):
    h, u = signup(client)
    assert client.get("/api/matches?search=%27%20OR%201%3D1%20--").status_code == 200
    bad = client.put(
        "/api/auth/profile",
        json={
            "name": "<script>alert(1)</script>",
            "email": "x@example.com",
            "username": "xxx",
        },
        headers=h,
    )
    assert bad.status_code == 422
    assert client.get("/api/matches?limit=999999").status_code == 422


def test_lock_and_rate_limit(client):
    signup(client)
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/login", json={"login": "benard", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login",
            json={"login": "benard", "password": "Test-password-2026!"},
        ).status_code
        == 403
    )
    for _ in range(21):
        r = client.post("/api/auth/login", json={"login": "unknown", "password": "bad"})
    assert r.status_code == 429


def test_recovery_is_one_time_and_revokes_sessions(client, monkeypatch):
    h, u = signup(client)
    links = []
    monkeypatch.setattr(
        "backend.routes.auth.send_reset", lambda email, link: links.append(link)
    )
    assert (
        client.post(
            "/api/auth/forgot", json={"email": "benard@example.com"}
        ).status_code
        == 200
    )
    token = links[0].split("token=")[1]
    r = client.post(
        "/api/auth/reset", json={"token": token, "password": "New-password-2026!"}
    )
    assert r.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/reset", json={"token": token, "password": "New-password-2026!"}
        ).status_code
        == 400
    )


def test_admin_recovery_suspend_unlock_and_audit(client, db):
    h, u = signup(client)
    admin = login(client)
    assert (
        client.post(
            f"/api/admin/users/{u['id']}/state", json={"suspended": True}, headers=admin
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"login": "benard", "password": "Test-password-2026!"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/users/{u['id']}/state",
            json={"suspended": False},
            headers=admin,
        ).status_code
        == 200
    )
    r = client.post(
        f"/api/admin/users/{u['id']}/temporary-password", json={}, headers=admin
    )
    temp = r.json()["temporary_password"]
    assert len(temp) >= 15
    logs = client.get("/api/admin/audit").json()
    assert any(x["action"] == "TEMPORARY_PASSWORD" and x["ip"] for x in logs)
    assert temp not in str(logs)
    r = client.post("/api/auth/login", json={"login": "benard", "password": temp})
    assert r.json()["user"]["must_change"] is True
    assert client.get("/api/matches").status_code == 403


def test_impersonation_boundary_and_return(client):
    h, u = signup(client)
    admin = login(client)
    r = client.post(f"/api/admin/users/{u['id']}/impersonate", json={}, headers=admin)
    assert r.status_code == 200, r.text
    h = {"x-csrf-token": r.json()["csrf"]}
    assert client.get("/api/auth/me").json()["impersonating"] is True
    assert client.get("/api/admin/users").status_code == 403
    assert (
        client.post(
            "/api/auth/password",
            json={
                "current_password": "Test-password-2026!",
                "password": "Should-not-work!",
            },
            headers=h,
        ).status_code
        == 403
    )
    r = client.post("/api/admin/return", json={}, headers=h)
    assert r.status_code == 200 and r.json()["user"]["role"] == "ADMIN"
    actions = [x["action"] for x in client.get("/api/admin/audit").json()]
    assert "IMPERSONATE_START" in actions and "IMPERSONATE_END" in actions


def test_cannot_delete_self_or_final_admin(client):
    h = login(client)
    u = client.get("/api/auth/me").json()["user"]
    assert (
        client.delete("/api/admin/users/" + str(u["id"]), headers=h).status_code == 409
    )


def test_expired_reset(client, db):
    from backend.services.recovery import create_reset

    h, u = signup(client)
    obj = db.get(User, u["id"])
    url = create_reset(db, obj)
    db.flush()
    reset = db.scalar(select(Reset).where(Reset.user_id == u["id"]))
    reset.expires_at = now() - timedelta(seconds=1)
    db.commit()
    assert (
        client.post(
            "/api/auth/reset",
            json={"token": url.split("token=")[1], "password": "New-password-2026!"},
        ).status_code
        == 400
    )


def test_user_management_profile_favorites_and_reset_link(client):
    h = login(client)
    payload = {
        "name": "Test Person",
        "email": "person@example.com",
        "username": "person",
        "password": "Initial-password-2026!",
        "role": "USER",
    }
    r = client.post("/api/admin/users", json=payload, headers=h)
    assert r.status_code == 201, r.text
    uid = r.json()["user"]["id"]
    assert len(client.get("/api/admin/users?q=person").json()) == 1
    assert client.get(f"/api/admin/users/{uid}").json()["username"] == "person"
    profile = {
        "name": "Changed Person",
        "email": "person@example.com",
        "username": "person",
        "role": "USER",
    }
    assert (
        client.put(f"/api/admin/users/{uid}", json=profile, headers=h).status_code
        == 200
    )
    link = client.post(f"/api/admin/users/{uid}/reset", json={}, headers=h).json()[
        "reset_link"
    ]
    assert (
        client.post(
            "/api/auth/reset",
            json={"token": link.split("token=")[1], "password": "Reset-password-2026!"},
        ).status_code
        == 200
    )
    r = client.post(
        "/api/auth/login", json={"login": "person", "password": "Reset-password-2026!"}
    )
    ph = {"x-csrf-token": r.json()["csrf"]}
    assert (
        client.put(
            "/api/auth/profile",
            json={k: v for k, v in profile.items() if k != "role"},
            headers=ph,
        ).status_code
        == 200
    )
    tid = client.get("/api/catalog").json()["teams"][0]["id"]
    assert (
        client.post("/api/favorites/" + str(tid), json={}, headers=ph).status_code
        == 200
    )
    assert (
        next(t for t in client.get("/api/catalog").json()["teams"] if t["id"] == tid)[
            "favorite"
        ]
        is True
    )
    assert client.get("/api/history").status_code == 200
    assert client.get("/api/leaderboard").status_code == 200
    h = login(client, password="Admin-secure-2026!")
    assert client.delete("/api/admin/users/" + str(uid), headers=h).status_code == 200
    assert client.get("/api/admin/users/" + str(uid)).status_code == 404


def test_static_assets_security_headers_and_validation_redaction(client):
    index = client.get("/")
    assert index.status_code == 200 and "PredictPro" in index.text
    assert "script-src 'self'" in index.headers["content-security-policy"]
    assert index.headers["x-frame-options"] == "DENY"
    assert client.get("/assets/vendor/chart.umd.js").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    result = client.post(
        "/api/auth/signup",
        json={
            "name": "A",
            "email": "bad",
            "username": "x",
            "password": "private-value",
        },
    )
    assert result.status_code == 422 and "private-value" not in result.text
````

## backend/utils/__init__.py

````python
"""PredictPro application package."""
````

## backend/utils/security.py

````python
import hashlib
import secrets
from datetime import timedelta
import bcrypt
import jwt
from fastapi import HTTPException, Request, Response
from sqlalchemy import select, update
from backend.config import SECRET, COOKIE, SECURE
from backend.models.entities import Session, User, RateBucket, now


def hash_password(value):
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify(value, hashed):
    return len(value.encode()) <= 72 and bcrypt.checkpw(value.encode(), hashed.encode())


def password_check(value):
    if len(value) < 10 or len(value.encode()) > 72:
        raise HTTPException(
            422, "Password must have at least 10 characters and at most 72 UTF-8 bytes."
        )
    return value


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def rate(db, key, limit=10, seconds=900):
    # SQLite serializes writers; the atomic increment is shared by all workers.
    from sqlalchemy.dialects.sqlite import insert

    db.execute(
        insert(RateBucket)
        .values(key=key, count=0, started=now())
        .on_conflict_do_nothing()
    )
    db.execute(
        update(RateBucket)
        .where(
            RateBucket.key == key,
            RateBucket.started < now() - timedelta(seconds=seconds),
        )
        .values(count=0, started=now())
    )
    count = db.execute(
        update(RateBucket)
        .where(RateBucket.key == key)
        .values(count=RateBucket.count + 1)
        .returning(RateBucket.count)
    ).scalar_one()
    db.commit()
    if count > limit:
        raise HTTPException(
            429,
            "Too many attempts. Try again later.",
            headers={"Retry-After": str(seconds)},
        )


def issue(db, user, response: Response, actor=None, parent=None):
    sid, csrf = secrets.token_hex(24), secrets.token_hex(24)
    expiry = now() + timedelta(hours=8)
    session = Session(id=sid, user_id=user.id, csrf=csrf, expires_at=expiry)
    db.add(session)
    claims = {
        "sub": str(user.id),
        "ver": user.version,
        "jti": sid,
        "exp": expiry,
        "iat": now(),
    }
    if actor:
        claims.update(actor=actor.id, actor_ver=actor.version, parent=parent)
    token = jwt.encode(claims, SECRET, algorithm="HS256")
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=SECURE,
        samesite="strict",
        max_age=28800,
        path="/",
    )
    return csrf


def decode(request: Request):
    try:
        return jwt.decode(
            request.cookies.get(COOKIE, ""),
            SECRET,
            algorithms=["HS256"],
            options={"require": ["sub", "ver", "jti", "exp", "iat"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Please sign in.")


def revoke_all(db, user):
    user.version += 1
    db.execute(update(Session).where(Session.user_id == user.id).values(revoked=True))


def public_user(user):
    return {
        k: getattr(user, k)
        for k in (
            "id",
            "name",
            "email",
            "username",
            "role",
            "suspended",
            "must_change",
            "created_at",
            "last_active",
            "failed",
            "locked_until",
        )
    }
````

## backend/worker.py

````python
"""Run manually or as a single scheduled process; no secret is logged."""

import argparse
import logging
import time
from backend.db import SessionLocal
from backend.services.football import refresh

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronize football results and notify followers."
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=900)
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("Minimum interval is 60 seconds.")
    while True:
        try:
            with SessionLocal() as db:
                report = refresh(db)
                db.commit()
                print(report, flush=True)
        except Exception:
            logging.exception("Sync failed. Existing data is retained.")
        if args.once:
            break
        time.sleep(args.interval)
````

## frontend/app.js

````javascript
import {api,send,token} from './services/api.js';
import {state,go,destroyCharts} from './hooks/state.js';
import {layout} from './components/layout.js';
import {toast,empty,esc} from './components/ui.js';
import {authPage} from './pages/auth.js';
import {dashboard} from './pages/dashboard.js';
import {matchPage} from './pages/match.js';
import {historyPage,favoritesPage,leaderboardPage,notificationsPage} from './pages/community.js';
import {profilePage} from './pages/profile.js';
import {adminOverview,adminUsers,adminAudit,adminSettings,adminCatalog} from './pages/admin.js';

window.toggleTheme=()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('predictpro-theme',next);}catch(e){/* Theme still changes in private storage modes. */}};
try{document.documentElement.dataset.theme=localStorage.getItem('predictpro-theme')||'dark';}catch(e){/* Default theme is usable without local storage. */}
window.showError=e=>toast(e.message,true);
document.querySelector('#dialog-close').onclick=()=>document.querySelector('#dialog').close();
let rendering=false,queued=false;
async function route(){
 if(rendering){queued=true;return;}rendering=true;
 try{
  const path=location.hash.slice(1)||'dashboard';destroyCharts();document.querySelector('#dialog').close();
  const metadata=await api('/site');state.siteName=metadata.site_name;document.title=metadata.site_name+' · Football intelligence';
  if(['login','signup','forgot','reset'].includes(path.split('?')[0])){authPage(path);return;}
  const session=await api('/auth/me');state.user=session.user;state.impersonating=session.impersonating;
  if(state.user.must_change&&path!=='profile'){go('profile');return;}
  if(path.startsWith('admin')&&state.user.role!=='ADMIN'){go('dashboard');return;}
  document.querySelector('#app').innerHTML=layout(path);
  document.querySelector('#theme').onclick=()=>window.toggleTheme();
  document.querySelector('#menu').onclick=e=>{const open=document.querySelector('#sidebar').classList.toggle('open');e.currentTarget.setAttribute('aria-expanded',open);};
  document.querySelector('#logout').onclick=async()=>{try{await send('/auth/logout');state.user=null;token('');go('login');}catch(e){toast(e.message,true);}};
  if(state.impersonating)document.querySelector('#return-admin').onclick=async()=>{try{const s=await send('/admin/return');state.user=s.user;state.impersonating=false;go('admin');}catch(e){toast(e.message,true);}};
  const main=document.querySelector('#main');main.innerHTML='<div class="skeleton"></div><div class="match-grid"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
  if(!state.user.must_change)state.catalog=await api('/catalog');
  const pages={'dashboard':dashboard,'history':historyPage,'favorites':favoritesPage,'leaderboard':leaderboardPage,'notifications':notificationsPage,'profile':profilePage,'admin':adminOverview,'admin/users':adminUsers,'admin/audit':adminAudit,'admin/settings':adminSettings,'admin/catalog':adminCatalog};
  if(path.startsWith('match/'))await matchPage(main,Number(path.split('/')[1]));
  else if(pages[path])await pages[path](main);
  else main.innerHTML=empty('Page not found','Choose a page from the navigation.');
  main.focus({preventScroll:true});
  if(!state.user.must_change){const notifications=await api('/notifications');const unread=notifications.filter(n=>!n.read).length;document.querySelector('#notification-count').textContent=unread||'';}
 }catch(e){
  if(e.status===401){state.user=null;go('login');}
  else{const root=document.querySelector('#main')||document.querySelector('#app');root.innerHTML=empty('Unable to load this view',e.message);toast(e.message,true);}
 }finally{rendering=false;if(queued){queued=false;route();}}
}
window.addEventListener('hashchange',route);
window.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelector('#sidebar')?.classList.remove('open');document.querySelector('#menu')?.setAttribute('aria-expanded','false');}});
setInterval(async()=>{if(!state.user||state.user.must_change||rendering)return;try{const rows=await api('/notifications');const el=document.querySelector('#notification-count');if(el)el.textContent=rows.filter(n=>!n.read).length||'';if(location.hash==='#notifications')route();}catch(e){if(e.status===401)go('login');}},60000);
route();
````

## frontend/components/layout.js

````javascript
import {state} from '../hooks/state.js';
import {esc} from './ui.js';
export function layout(path){
 const nav=[['dashboard','◈','Match center'],['history','◷','Prediction history'],['favorites','☆','Favorite teams'],['leaderboard','♜','Leaderboard'],['notifications','◉','Notifications'],['profile','⚙','My profile']];
 if(state.user.role==='ADMIN')nav.push(['admin','▦','Admin overview'],['admin/users','♙','Manage users'],['admin/catalog','▤','Football data'],['admin/audit','≡','Audit log'],['admin/settings','⚙','Site settings']);
 return `<div class="app-shell"><aside id="sidebar"><a class="brand" href="#dashboard"><span class="brand-mark">P<span>↗</span></span>${esc(state.siteName)}</a><p class="nav-label">YOUR WORKSPACE</p><nav aria-label="Main">${nav.map(([url,icon,label])=>`<a href="#${url}" class="${path===url?'active':''}" ${path===url?'aria-current="page"':''}><span aria-hidden="true">${icon}</span>${label}</a>`).join('')}</nav><div class="sidebar-bottom"><div class="model-status"><i class="dot"></i><div>Explainable intelligence<small>Poisson + Elo + recent form</small></div></div><p>Statistical estimates, not guarantees.<br>Not betting advice.</p></div></aside><div class="workspace"><header class="topbar"><button id="menu" class="icon-button" aria-label="Toggle navigation" aria-expanded="false">☰</button><span class="topbar-label">FOOTBALL INTELLIGENCE <span class="live-dot">●</span></span><div class="top-actions"><button id="theme" class="icon-button" aria-label="Toggle light and dark theme">◐</button><a href="#notifications" aria-label="Notifications" class="icon-button">♧ <span id="notification-count"></span></a><span class="avatar">${esc(state.user.name.slice(0,1).toUpperCase())}</span><div class="user-label"><b>${esc(state.user.name)}</b><small>${esc(state.user.role)}</small></div><button id="logout" class="icon-button" aria-label="Sign out">↪</button></div></header>${state.impersonating?`<div class="impersonation" role="alert">You are viewing as ${esc(state.user.username)} <button id="return-admin" class="button secondary">Return to admin</button></div>`:''}<main id="main" tabindex="-1"></main><footer>PredictPro · Independent statistical football analysis. Predictions are statistical estimates, not guarantees, and not betting advice.</footer></div></div>`;
}
````

## frontend/components/ui.js

````javascript
import {state} from '../hooks/state.js';
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const pct=value=>`${Math.round((value||0)*100)}%`;
export const date=value=>new Date(String(value).endsWith('Z')?value:value+'Z').toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
export function toast(message,error=false){const el=document.createElement('div');el.className='toast'+(error?' error':'');el.textContent=message;document.querySelector('#toasts').append(el);setTimeout(()=>el.remove(),6500);}
export function empty(title,body='Try another filter or check back after the next data sync.'){return `<div class="empty"><span class="empty-icon">◇</span><h3>${esc(title)}</h3><p>${esc(body)}</p></div>`;}
export function heading(kicker,title,description='',actions=''){return `<header class="page-heading"><div><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p class="muted">${esc(description)}</p></div>${actions}</header>`;}
export function field(label,name,type='text',value='',extra=''){return `<label>${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}" ${extra}></label>`;}
export function select(label,name,options,value=''){return `<label>${esc(label)}<select name="${esc(name)}">${options.map(([id,text])=>`<option value="${esc(id)}" ${String(id)===String(value)?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;}
export function formError(form,error){const el=form.querySelector('.form-error');if(el)el.textContent=error.message;toast(error.message,true);}
export function formAction(form,fn){form.addEventListener('submit',async e=>{e.preventDefault();const button=form.querySelector('[type="submit"]');button.disabled=true;const error=form.querySelector('.form-error');if(error)error.textContent='';try{await fn(Object.fromEntries(new FormData(form)));}catch(e){formError(form,e);}finally{button.disabled=false;}});}
export function dialog(title,html){document.querySelector('#dialog-content').innerHTML=`<h2 id="dialog-title">${esc(title)}</h2>${html}`;document.querySelector('#dialog').showModal();}
export async function confirmAction(title,description){
  dialog(title,`<p>${esc(description)}</p><div class="actions"><button id="confirm-yes" class="button danger">Confirm</button><button id="confirm-no" class="button secondary">Cancel</button></div>`);
  return new Promise(resolve=>{
    const d=document.querySelector('#dialog');let done=false;
    const finish=result=>{if(done)return;done=true;d.close();d.removeEventListener('close',closed);resolve(result);};
    const closed=()=>finish(false);d.addEventListener('close',closed);
    document.querySelector('#confirm-yes').onclick=()=>finish(true);document.querySelector('#confirm-no').onclick=()=>finish(false);
  });
}
export function chart(id,type,labels,values,label='Probability'){
  const canvas=document.getElementById(id);if(!canvas)return;
  if(!window.Chart){canvas.outerHTML=empty('Chart unavailable','Numerical results are shown alongside the chart.');return;}
  const isLine=type==='line';
  const chart=new window.Chart(canvas,{type,data:{labels,datasets:[{label,data:values,backgroundColor:isLine?'rgba(16,185,129,.13)':['#10b981','#e4b453','#5d8ee8'],borderColor:'#10b981',borderWidth:isLine?2:0,borderRadius:6,fill:isLine,tension:.3}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${label}: ${Number(c.raw).toFixed(1)}`}}},scales:{x:{grid:{display:false},ticks:{color:'#8d9db4'}},y:{beginAtZero:true,ticks:{color:'#8d9db4'},grid:{color:'rgba(145,165,185,.1)'}}}}});state.charts.push(chart);
}
export function formGuide(values=[]){return `<div class="form-guide" aria-label="Last five results, oldest first">${values.map(x=>`<span class="form-${x}">${x}</span>`).join('')||'<span class="muted">No previous matches</span>'}</div>`;}
export function matchCard(m){const p=m.prediction;return `<article class="match-card">
 <div class="card-meta"><span>${esc(m.league)}</span><span class="pill ${m.source==='sample'?'amber':''}">${esc(m.source==='sample'?'SYNTHETIC DEMO':m.status)}</span></div>
 <a class="match-link" href="#match/${m.id}"><div class="teams"><div><span class="team-badge">${esc(m.home.slice(0,2).toUpperCase())}</span><strong>${esc(m.home)}</strong></div><span class="versus">${m.status==='FINISHED'?`${m.home_goals} : ${m.away_goals}`:'VS'}</span><div><span class="team-badge away">${esc(m.away.slice(0,2).toUpperCase())}</span><strong>${esc(m.away)}</strong></div></div></a>
 <p class="match-time">${date(m.kickoff)}</p>
 ${p?`<div class="prob-row"><span>Home <b>${pct(p.probabilities.Home)}</b></span><span>Draw <b>${pct(p.probabilities.Draw)}</b></span><span>Away <b>${pct(p.probabilities.Away)}</b></span></div><div class="prob-strip" aria-hidden="true"><i style="width:${p.probabilities.Home*100}%"></i><i style="width:${p.probabilities.Draw*100}%"></i><i style="width:${p.probabilities.Away*100}%"></i></div><div class="card-foot"><span><i class="dot"></i> ${esc(p.outcome)} · ${esc(p.confidence)} confidence</span><a href="#match/${m.id}">Analysis ↗</a></div>`:'<p class="muted">No pre-match prediction recorded.</p>'}
 </article>`;}
export function metricsCards(metrics){const groups=Object.entries(metrics.groups);return groups.length?groups.map(([name,g])=>`<article class="stat"><span>${esc(name)}</span><strong>${pct(g.accuracy)}</strong><small>${g.correct}/${g.total} correct · Brier ${g.brier.toFixed(3)}</small></article>`).join(''):empty('Accuracy starts with results','No eligible completed matches yet. Sync results after fixtures finish.');}
````

## frontend/hooks/state.js

````javascript
export const state={siteName:"PredictPro",user:null,impersonating:false,catalog:{teams:[],leagues:[]},charts:[],page:0};
export function destroyCharts(){for(const chart of state.charts)chart.destroy();state.charts=[];}
export function go(path){if(location.hash==='#'+path)window.dispatchEvent(new HashChangeEvent('hashchange'));else location.hash=path;}
````

## frontend/index.html

````html
<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="PredictPro: explainable football probabilities, match insights and community picks.">
<title>PredictPro · Football intelligence</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='12' fill='%2310b981'/%3E%3Ctext x='10' y='29' font-size='28' fill='%23081722'%3EP%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="/assets/styles/main.css">
<script src="/assets/vendor/chart.umd.js" defer></script>
<script type="module" src="/assets/app.js"></script>
</head>
<body><a class="skip" href="#main">Skip to content</a><div id="app"></div><div id="toasts" role="status" aria-live="polite"></div>
<dialog id="dialog" aria-labelledby="dialog-title"><div id="dialog-content"></div><button id="dialog-close" class="button secondary">Close</button></dialog>
</body></html>
````

## frontend/pages/admin.js

````javascript
import {api,send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {heading,esc,field,select,formAction,toast,dialog,confirmAction,empty,date,pct,chart,metricsCards} from '../components/ui.js';

export async function adminOverview(root){
 const d=await api('/admin/overview');
 root.innerHTML=heading('ADMINISTRATION','The control room.','Monitor the platform, maintain your data, and keep the model accountable.',`<div class="actions"><button id="sync" class="button secondary">↻ Sync football data</button><button id="retrain" class="button">Calibrate model</button></div>`)+
 `<div class="stats-grid"><article class="stat"><span>Total users</span><strong>${d.total_users}</strong><small>Registered accounts</small></article><article class="stat"><span>Active users</span><strong>${d.active_users}</strong><small>Active in last 30 days, unsuspended</small></article><article class="stat"><span>Stored predictions</span><strong>${d.predictions}</strong><small>Includes labeled backtests</small></article></div><div class="section-label"><h2>Prediction performance</h2></div><div class="stats-grid">${metricsCards(d.metrics)}</div><div class="two-col"><section class="panel"><h2>Administrative activity</h2>${d.daily.length?'<div class="chart-container"><canvas id="activity" role="img" aria-label="Daily admin activity count"></canvas></div>':empty('No activity yet')}</section><section class="panel"><h2>Recent audit events</h2>${d.recent.map(a=>`<div class="activity-row"><i class="dot"></i><div><b>${esc(a.action)}</b><small>${esc(a.actor)} → ${esc(a.target)}<br>${date(a.created_at)}</small></div></div>`).join('')||empty('No audit events')}</section></div>`;
 if(d.daily.length)chart('activity','line',d.daily.map(x=>x.date),d.daily.map(x=>x.count),'Admin actions');
 for(const [id,path] of [['sync','sync'],['retrain','retrain']])document.getElementById(id).onclick=async e=>{const b=e.currentTarget;b.disabled=true;try{const result=await send('/admin/'+path);dialog(path==='sync'?'Data sync report':'Model calibration report',`<pre class="report">${esc(JSON.stringify(result,null,2))}</pre>`);}catch(e){toast(e.message,true);}finally{b.disabled=false;}};
}
function userForm(u={}){return `<form id="user-editor">${field('Full name','name','text',u.name||'','required minlength="2" maxlength="80"')}${field('Email','email','email',u.email||'','required')}${field('Username','username','text',u.username||'','required pattern="[a-zA-Z0-9_]{3,30}"')}${select('Role','role',[['USER','User'],['ADMIN','Administrator']],u.role||'USER')}${u.id?'':field('Initial password','password','password','','required minlength="10" autocomplete="new-password"')}<p class="form-error" role="alert"></p><button class="button" type="submit">Save user</button></form>`;}
export async function adminUsers(root){
 root.innerHTML=heading('ACCOUNT OPERATIONS','People & permissions.','Recover accounts, manage access, and support users with an audit trail.','<button id="create-user" class="button">＋ Create user</button>')+`<form id="user-search" class="filters">${field('Search name, email or username','q','search','','placeholder="Find a user…"')}<button class="button secondary" type="submit">Search</button></form><section class="panel"><div id="users-table"></div><div class="pager"><button id="prev-users" class="button secondary">← Previous</button><button id="next-users" class="button secondary">Next →</button></div></section>`;
 let rows=[],offset=0,query='';
 async function load(){rows=await api('/admin/users?q='+encodeURIComponent(query)+'&offset='+offset);document.querySelector('#users-table').innerHTML=`<div class="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last active</th><th>Actions</th></tr></thead><tbody>${rows.map(u=>`<tr><td><b>${esc(u.name)}</b><small>@${esc(u.username)} · ${esc(u.email)}</small></td><td>${esc(u.role)}</td><td><span class="pill ${u.suspended?'amber':''}">${u.suspended?'Suspended':u.locked_until&&new Date(u.locked_until+'Z')>new Date()?'Locked':'Active'}</span>${u.must_change?'<small>Password change required</small>':''}</td><td>${date(u.last_active)}</td><td><div class="table-actions"><button data-action="view" data-id="${u.id}">View</button><button data-action="edit" data-id="${u.id}">Edit</button><button data-action="state" data-id="${u.id}">${u.suspended?'Activate / unlock':'Suspend'}</button><button data-action="unlock" data-id="${u.id}">Unlock</button><button data-action="reset" data-id="${u.id}">Reset link</button><button data-action="temporary-password" data-id="${u.id}">Temporary password</button><button data-action="impersonate" data-id="${u.id}">Log in as</button><button data-action="delete" data-id="${u.id}" class="text-danger">Delete</button></div></td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('No users found')}`;document.querySelector('#prev-users').disabled=offset===0;document.querySelector('#next-users').disabled=rows.length<50;}
 function edit(u){dialog(u.id?'Edit user':'Create user',userForm(u));formAction(document.querySelector('#user-editor'),async data=>{const result=await send('/admin/users'+(u.id?'/'+u.id:''),data,u.id?'PUT':'POST');toast(result.message);document.querySelector('#dialog').close();await load();});}
 document.querySelector('#create-user').onclick=()=>edit({});
 formAction(document.querySelector('#user-search'),async data=>{query=data.q;offset=0;await load();});
 document.querySelector('#prev-users').onclick=async()=>{offset=Math.max(0,offset-50);try{await load();}catch(e){toast(e.message,true);}};
 document.querySelector('#next-users').onclick=async()=>{offset+=50;try{await load();}catch(e){toast(e.message,true);}};
 document.querySelector('#users-table').onclick=async e=>{
  const b=e.target.closest('[data-action]');if(!b)return;const u=rows.find(x=>x.id==b.dataset.id),action=b.dataset.action;
  try{
    if(action==='edit'){edit(u);return;}
    if(action==='view'){const data=await api('/admin/users/'+u.id);dialog('Account details',`<dl class="details">${Object.entries(data).map(([k,v])=>`<dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`);return;}
    if(!await confirmAction(`${action.replaceAll('-',' ')}: @${u.username}`,action==='delete'?'This permanently deletes this user and their picks, favorites and notifications. Audit records are retained.':'This action will be recorded with your administrator identity and IP address.'))return;
    if(action==='impersonate'){const result=await send(`/admin/users/${u.id}/impersonate`);state.user=result.user;state.impersonating=true;go('dashboard');return;}
    const result=action==='delete'?await send('/admin/users/'+u.id,{},'DELETE'):await send(`/admin/users/${u.id}/${action==='state'||action==='unlock'?'state':action}`,action==='state'?{suspended:!u.suspended}:action==='unlock'?{suspended:false}:{});
    if(result.reset_link||result.temporary_password)dialog('Account recovery · sensitive',`<p>${esc(result.message)}</p><label>${result.reset_link?'One-time reset link':'Temporary password'}<textarea readonly rows="4">${esc(result.reset_link||result.temporary_password)}</textarea></label><p class="fine-print">Visible once here. Share through a secure channel.</p>`);
    else toast(result.message);
    await load();
  }catch(error){toast(error.message,true);}
 };
 await load();
}
export async function adminAudit(root){
 let offset=0;root.innerHTML=heading('ACCOUNTABILITY','The audit trail.','Sensitive admin actions record who acted, what changed, when, and the request IP.')+`<section class="panel"><div id="audit-table"></div><div class="pager"><button id="prev-audit" class="button secondary">← Previous</button><span id="audit-page"></span><button id="next-audit" class="button secondary">Next →</button></div></section>`;
 async function load(){const rows=await api('/admin/audit?offset='+offset);document.querySelector('#audit-table').innerHTML=`<div class="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Target</th><th>IP address</th></tr></thead><tbody>${rows.map(a=>`<tr><td>${date(a.created_at)}</td><td>${esc(a.actor)}</td><td><span class="pill">${esc(a.action)}</span></td><td>${esc(a.target)}</td><td>${esc(a.ip)}</td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('No audit entries')}`;document.querySelector('#prev-audit').disabled=offset===0;document.querySelector('#next-audit').disabled=rows.length<100;document.querySelector('#audit-page').textContent=`Page ${offset/100+1}`;}
 document.querySelector('#prev-audit').onclick=async()=>{offset=Math.max(0,offset-100);try{await load();}catch(e){toast(e.message,true);}};document.querySelector('#next-audit').onclick=async()=>{offset+=100;try{await load();}catch(e){toast(e.message,true);}};await load();
}
export async function adminSettings(root){
 const d=await api('/admin/settings');
 root.innerHTML=heading('PLATFORM CONFIGURATION','Set the ground rules.','Change the site identity, configure data access, or pause user access.')+`<section class="panel narrow"><form id="settings-form">${field('Site name','site_name','text',d.site_name,'required minlength="2" maxlength="60"')}${field('Football-data.org API key','api_key','password','','autocomplete="off" placeholder="Leave blank to retain current key"')}<p class="muted">${d.api_key_configured?'An API key is configured.':'No key configured: synthetic offline data is available.'}</p><label class="checkbox"><input type="checkbox" name="clear_api">Remove saved API key (disables live sync)</label><label class="checkbox"><input type="checkbox" name="maintenance" ${d.maintenance?'checked':''}>Maintenance mode · administrators retain access</label><p class="form-error" role="alert"></p><button class="button" type="submit">Save settings</button></form><p class="fine-print">SMTP and JWT secrets belong in the environment. API keys saved here are never exposed to users or returned by the API. Encrypt production disks and backups.</p></section>`;
 formAction(document.querySelector('#settings-form'),async data=>{const body={site_name:data.site_name,maintenance:data.maintenance==='on'};if(data.clear_api==='on')body.api_key='';else if(data.api_key)body.api_key=data.api_key;toast((await send('/admin/settings',body,'PUT')).message);go('admin/settings');});
}
export async function adminCatalog(root){
 let kind='matches',rows=[],offset=0;
 root.innerHTML=heading('FOOTBALL OPERATIONS','Fixtures, teams & leagues.','Maintain records and enter final results. Sample data is clearly identified.','<button id="create-record" class="button">＋ Add record</button>')+`<div class="tabs" role="group" aria-label="Data type"><button data-kind="matches" class="active">Matches</button><button data-kind="teams">Teams</button><button data-kind="leagues">Leagues</button></div><section class="panel"><div id="catalog-table"></div><div class="pager"><button id="prev-data" class="button secondary">← Previous</button><button id="next-data" class="button secondary">Next →</button></div></section>`;
 const leagues=()=>state.catalog.leagues.map(x=>[x.id,x.name]),teams=()=>state.catalog.teams.map(x=>[x.id,x.name]);
 async function load(){state.catalog=await api('/catalog');if(kind==='matches')rows=(await api('/matches?status=ALL&limit=50&offset='+offset)).items;else rows=state.catalog[kind];
  document.querySelector('#catalog-table').innerHTML=`<div class="table-wrap"><table><thead><tr><th>ID</th><th>${kind==='matches'?'Match':'Name'}</th><th>Details</th><th>Actions</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.id}</td><td>${esc(kind==='matches'?r.home+' vs '+r.away:r.name)}</td><td>${kind==='matches'?`${date(r.kickoff)}<small>${esc(r.status)} · ${esc(r.source)} ${r.status==='FINISHED'?r.home_goals+'–'+r.away_goals:''}</small>`:esc(r.code||state.catalog.leagues.find(l=>l.id===r.league_id)?.name)}</td><td><div class="table-actions"><button data-edit="${r.id}">Edit</button><button class="text-danger" data-delete="${r.id}">Delete</button></div></td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('No records')}`;document.querySelector('#prev-data').disabled=kind!=='matches'||offset===0;document.querySelector('#next-data').disabled=kind!=='matches'||rows.length<50;}
 function editor(r={}){
  let fields=kind==='leagues'?field('League name','name','text',r.name||'','required')+field('Code','code','text',r.code||'','required pattern="[A-Z0-9_]{2,12}"'):kind==='teams'?field('Team name','name','text',r.name||'','required')+select('League','league_id',leagues(),r.league_id):select('League','league_id',leagues(),r.league_id)+select('Home team','home_id',teams(),r.home_id)+select('Away team','away_id',teams(),r.away_id)+field('Kickoff (UTC)','kickoff','datetime-local',r.kickoff?.slice(0,16)||'','required')+select('Status','status',[['SCHEDULED','Scheduled'],['FINISHED','Finished'],['POSTPONED','Postponed'],['CANCELLED','Cancelled']],r.status||'SCHEDULED')+field('Home goals (finished only)','home_goals','number',r.home_goals??'','min="0" max="50" step="1"')+field('Away goals (finished only)','away_goals','number',r.away_goals??'','min="0" max="50" step="1"');
  dialog(`${r.id?'Edit':'Create'} ${kind.slice(0,-1)}`,`<form id="record-editor">${fields}<p class="form-error" role="alert"></p><button class="button" type="submit">Save record</button></form>`);
  formAction(document.querySelector('#record-editor'),async data=>{for(const key of ['league_id','home_id','away_id'])if(key in data)data[key]=Number(data[key]);if(kind==='matches'){data.kickoff+=':00Z';for(const key of ['home_goals','away_goals'])data[key]=data[key]===''?null:Number(data[key]);}const result=await send('/admin/'+kind+(r.id?'/'+r.id:''),data,r.id?'PUT':'POST');toast(result.message);document.querySelector('#dialog').close();await load();});
 }
 document.querySelector('#create-record').onclick=()=>editor();
 document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=async()=>{kind=b.dataset.kind;offset=0;document.querySelectorAll('[data-kind]').forEach(x=>x.classList.toggle('active',x===b));try{await load();}catch(e){toast(e.message,true);}});
 document.querySelector('#catalog-table').onclick=async e=>{const edit=e.target.closest('[data-edit]'),del=e.target.closest('[data-delete]');try{if(edit)editor(rows.find(r=>r.id==edit.dataset.edit));if(del&&await confirmAction('Delete record?','Match deletion also removes related picks and predictions. Referenced teams and leagues cannot be deleted.')){toast((await send('/admin/'+kind+'/'+del.dataset.delete,{},'DELETE')).message);await load();}}catch(e){toast(e.message,true);}};
 document.querySelector('#prev-data').onclick=async()=>{offset=Math.max(0,offset-50);try{await load();}catch(e){toast(e.message,true);}};document.querySelector('#next-data').onclick=async()=>{offset+=50;try{await load();}catch(e){toast(e.message,true);}};await load();
}
````

## frontend/pages/auth.js

````javascript
import {send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {esc,field,formAction,toast} from '../components/ui.js';
export function authPage(path){
 const mode=path.split('?')[0],signup=mode==='signup',forgot=mode==='forgot',reset=mode==='reset';
 const title=signup?'Your next insight starts here.':forgot?'Get back in the game.':reset?'Choose a new password.':'See the game differently.';
 document.querySelector('#app').innerHTML=`<div class="auth-layout"><section class="auth-story"><a class="brand" href="#login"><span class="brand-mark">P↗</span>${esc(state.siteName)}</a><div><p class="eyebrow">FOOTBALL. UNDERSTOOD.</p><h1>Less guesswork.<br>More <em>insight.</em></h1><p>Discover the numbers behind every match. Transparent models, meaningful probabilities, and your own football instincts.</p><div class="pitch-art" aria-hidden="true"><div class="pitch-circle"></div><div class="pitch-line"></div><span class="pitch-chip">1.84 <small>EXPECTED GOALS</small></span><span class="pitch-chip second">61% <small>HOME ADVANTAGE</small></span></div><small>Illustrative figures · Statistical estimates, not betting advice</small></div><p class="muted">EXPLAINABLE MODELS. BETTER QUESTIONS.</p></section><section class="auth-panel"><button id="auth-theme" class="icon-button" aria-label="Toggle theme">◐</button><div class="auth-form-wrap"><p class="eyebrow">WELCOME TO PREDICTPRO</p><h2>${title}</h2><p class="muted">${signup?'Create a free account to follow matches and challenge the model.':forgot?'We’ll send a one-time password reset link.':reset?'Use at least 10 characters.':'Sign in to your football intelligence workspace.'}</p><form id="auth-form">
 ${signup?field('Full name','name','text','','required minlength="2" maxlength="80" autocomplete="name"')+field('Email','email','email','','required autocomplete="email"')+field('Username','username','text','','required pattern="[a-zA-Z0-9_]{3,30}" autocomplete="username"'):forgot?field('Email','email','email','','required autocomplete="email"'):reset?'':field('Email or username','login','text','','required autocomplete="username"')}
 ${forgot?'':field(reset?'New password':'Password','password','password','','required '+(signup||reset?'minlength="10" autocomplete="new-password"':'autocomplete="current-password"'))}
 <p class="form-error" role="alert"></p><button class="button full" type="submit">${signup?'Create account':forgot?'Send reset link':reset?'Reset password':'Sign in'} <span>↗</span></button></form>
 <div class="auth-links">${mode==='login'?'<a href="#forgot">Forgot password?</a><p>New here? <a href="#signup">Create an account</a></p>':'<a href="#login">Back to sign in</a>'}</div><div class="auth-note">Built for understanding football. No model can guarantee an outcome.</div></div></section></div>`;
 document.querySelector('#auth-theme').onclick=()=>window.toggleTheme();
 formAction(document.querySelector('#auth-form'),async data=>{
   if(reset){data.token=new URLSearchParams(path.split('?')[1]).get('token')||'';const result=await send('/auth/reset',data);toast(result.message);go('login');return;}
   const result=await send('/auth/'+(signup?'signup':forgot?'forgot':'login'),data);
   if(forgot){toast(result.message);return;}
   state.user=result.user;state.impersonating=false;go(result.user.must_change?'profile':'dashboard');
 });
}
````

## frontend/pages/community.js

````javascript
import {api,send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {heading,esc,date,pct,empty,matchCard,toast,metricsCards,chart} from '../components/ui.js';
export async function historyPage(root){
 const metrics=await api('/metrics');let offset=0;
 root.innerHTML=heading('PREDICTION ARCHIVE','A model should show its work.','Frozen predictions, final scores, and honest performance measurement.')+`<div class="stats-grid">${metricsCards(metrics)}</div><section class="panel"><h2>Prospective accuracy over time</h2><div id="accuracy-content"></div><p class="fine-print">${esc(metrics.note)}</p></section><div id="history-list" class="match-grid"></div><div class="pager"><button id="prev-history" class="button secondary">← Previous</button><span id="history-page"></span><button id="next-history" class="button secondary">Next →</button></div>`;
 if(metrics.trend.length){document.querySelector('#accuracy-content').innerHTML='<div class="chart-container"><canvas id="accuracy" aria-label="Cumulative prediction accuracy" role="img"></canvas></div>';const trend=metrics.trend.filter(x=>x.source==='live');if(trend.length){let hits=0;chart('accuracy','line',trend.map(x=>x.date),trend.map((x,i)=>{hits+=x.correct;return hits/(i+1)*100;}),'Live accuracy (%)');}else document.querySelector('#accuracy-content').innerHTML=empty('No live result history','Synthetic or manual results do not establish real-world model performance.');}
 else document.querySelector('#accuracy-content').innerHTML=empty('No prospective results yet','The chart begins when a pre-kickoff prediction is evaluated after a result.');
 async function load(){const data=await api('/history?offset='+offset);document.querySelector('#history-list').innerHTML=data.items.map(matchCard).join('')||empty('No predictions');document.querySelector('#prev-history').disabled=offset===0;document.querySelector('#next-history').disabled=data.items.length<50;document.querySelector('#history-page').textContent=`Page ${offset/50+1}`;}
 document.querySelector('#prev-history').onclick=async()=>{offset=Math.max(0,offset-50);try{await load();}catch(e){toast(e.message,true);}};
 document.querySelector('#next-history').onclick=async()=>{offset+=50;try{await load();}catch(e){toast(e.message,true);}};await load();
}
export async function favoritesPage(root){
 root.innerHTML=heading('YOUR CLUBS','Keep your teams close.','Save favorite teams to your account and manage your club list.')+`<div class="team-grid">${state.catalog.teams.map(t=>`<article class="panel team-panel"><span class="team-badge">${esc(t.name.slice(0,2))}</span><h3>${esc(t.name)}</h3><button class="button ${t.favorite?'':'secondary'} favorite" data-id="${t.id}" aria-pressed="${t.favorite}">${t.favorite?'★ Favorited':'☆ Add favorite'}</button></article>`).join('')||empty('No teams available')}</div>`;
 document.querySelectorAll('.favorite').forEach(b=>b.onclick=async()=>{try{toast((await send('/favorites/'+b.dataset.id)).message);state.catalog=await api('/catalog');go('favorites');}catch(e){toast(e.message,true);}});
}
export async function leaderboardPage(root){
 const rows=await api('/leaderboard');
 root.innerHTML=heading('THE COMMUNITY','Football instincts, measured.','3 points per correct pick. Rankings reflect both participation and accuracy.')+`<section class="panel"><div class="table-wrap"><table><thead><tr><th>Rank</th><th>Player / Model</th><th>Correct</th><th>Completed picks</th><th>Accuracy</th><th>Points</th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td><td><b>${esc(r.name)}</b> ${r.kind==='AI'?'<span class="pill">AI</span>':''}</td><td>${r.correct}</td><td>${r.total}</td><td>${pct(r.accuracy)}</td><td class="emerald">${r.points}</td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('The table is open','Make a pick on an upcoming match. It is scored after the result is recorded.')}<p class="fine-print">AI rows are separated by data source. Participants may choose different matches; this is a points game, not a controlled model benchmark.</p></section>`;
}
export async function notificationsPage(root){
 const rows=await api('/notifications');
 root.innerHTML=heading('FULL-TIME UPDATES','Stay in the loop.','Results for the matches you follow. Updates refresh every 60 seconds.')+`<section class="panel">${rows.map(n=>`<article class="notification ${n.read?'read':''}"><div><span class="pill">${n.read?'READ':'NEW'}</span><h3><a href="#match/${n.match_id}">${esc(n.text)}</a></h3><p class="muted">${date(n.created_at)}</p></div>${n.read?'':`<button class="button secondary mark-read" data-id="${n.id}">Mark read</button>`}</article>`).join('')||empty('All quiet for now','Follow upcoming matches to receive in-app notifications when results are synced or recorded.')}</section>`;
 document.querySelectorAll('.mark-read').forEach(b=>b.onclick=async()=>{try{await send('/notifications/'+b.dataset.id+'/read');go('notifications');}catch(e){toast(e.message,true);}});
}
````

## frontend/pages/dashboard.js

````javascript
import {api} from '../services/api.js';
import {state} from '../hooks/state.js';
import {heading,esc,select,field,formAction,matchCard,empty,pct,metricsCards,chart} from '../components/ui.js';
export async function dashboard(root){
 const metrics=await api('/metrics');
 root.innerHTML=heading('THE MATCH CENTER','Every match. A clearer picture.','Explore upcoming fixtures, understand the probabilities, and make your call.','<a href="#history" class="button secondary">View results ↗</a>')+
 `<section class="hero-band"><div><span class="pill">MODEL INSIGHTS</span><h2>Football has patterns.<br>Find your edge in understanding.</h2><p>Poisson goal distributions meet Elo strength and recent form.<br>Every prediction comes with its reasoning.</p><div class="hero-tags"><span>✓ Explainable probabilities</span><span>✓ No outcome guarantees</span></div></div><div class="hero-motif" aria-hidden="true"><div>90<span>minutes.<br>many possibilities.</span></div></div></section><div class="section-label"><h2>Explore fixtures</h2><span class="muted">Times shown in your local timezone · date filter uses UTC</span></div><form id="filters" class="filters">${field('Search teams','search','search','','placeholder="Search a team…"')}${select('League','league',[['','All leagues'],...state.catalog.leagues.map(x=>[x.id,x.name])])}${field('Match date (UTC)','date','date')}${select('Team','team',[['','All teams'],...state.catalog.teams.map(x=>[x.id,x.name])])}${select('Status','status',[['SCHEDULED','Upcoming'],['FINISHED','Finished'],['ALL','All matches']])}<button class="button" type="submit">Apply filters</button></form><p id="match-count" class="muted"></p><div id="matches" class="match-grid"></div><div class="pager"><button class="button secondary" id="previous">← Previous</button><span id="page-number"></span><button class="button secondary" id="next">Next →</button></div><div class="section-label"><h2>Model performance</h2><a href="#history">Explore history ↗</a></div><div class="stats-grid">${metricsCards(metrics)}</div><p class="fine-print">${esc(metrics.note)} Bundled data is synthetic and never represented as real fixtures.</p>`;
 let current={},offset=0,total=0;
 async function load(){const query=new URLSearchParams({...current,offset,limit:12});const data=await api('/matches?'+query);total=data.total;document.querySelector('#matches').innerHTML=data.items.map(matchCard).join('')||empty('No matches found');document.querySelector('#match-count').textContent=`${total} matches`;document.querySelector('#previous').disabled=offset===0;document.querySelector('#next').disabled=offset+12>=total;document.querySelector('#page-number').textContent=`Page ${Math.floor(offset/12)+1}`;}
 formAction(document.querySelector('#filters'),async data=>{current=Object.fromEntries(Object.entries(data).filter(([,v])=>v));offset=0;await load();});
 document.querySelector('#previous').onclick=async()=>{offset=Math.max(0,offset-12);try{await load();}catch(e){window.showError(e);}};
 document.querySelector('#next').onclick=async()=>{offset+=12;try{await load();}catch(e){window.showError(e);}};
 await load();
}
````

## frontend/pages/match.js

````javascript
import {api,send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {heading,esc,date,pct,chart,formGuide,select,formAction,toast,empty} from '../components/ui.js';
export async function matchPage(root,id){
 const m=await api('/matches/'+id),p=m.prediction;
 root.innerHTML=`<a class="back-link" href="#dashboard">← Back to match center</a>`+heading(m.league,`${m.home} vs ${m.away}`,`${date(m.kickoff)} · ${m.source==='sample'?'Synthetic demonstration fixture':m.source+' data'}`,`<button id="follow" class="button secondary">${m.following?'✓ Following':'＋ Follow match'}</button>`)+
 `<section class="match-hero"><div><span class="team-badge large">${esc(m.home.slice(0,2))}</span><h2>${esc(m.home)}</h2>${formGuide(p?.home_form)}</div><div class="score-block"><span class="pill">${esc(m.status)}</span><strong>${m.status==='FINISHED'?`${m.home_goals} – ${m.away_goals}`:p?esc(p.scoreline):'VS'}</strong><small>${m.status==='FINISHED'?'Final score':'Most likely scoreline'}</small></div><div><span class="team-badge large away">${esc(m.away.slice(0,2))}</span><h2>${esc(m.away)}</h2>${formGuide(p?.away_form)}</div></section>`+
 (p?`<div class="two-col"><section class="panel"><div class="section-label"><h2>Outcome probabilities</h2><span class="pill">${esc(p.confidence)} confidence</span></div><div class="chart-container"><canvas id="prob-chart" role="img" aria-label="Outcome probability bar chart"></canvas></div><div class="prob-row">${Object.entries(p.probabilities).map(([k,v])=>`<span>${k}<b>${pct(v)}</b></span>`).join('')}</div><p class="fine-print">The largest probability can still be below 50%. All three outcomes remain possible.</p></section><section class="panel"><h2>Inside the numbers</h2><div class="insight-grid"><div><small>Expected home goals</small><strong>${p.expected_goals.home.toFixed(2)}</strong></div><div><small>Expected away goals</small><strong>${p.expected_goals.away.toFixed(2)}</strong></div><div><small>Over / Under 2.5</small><strong>${pct(p.over25)} / ${pct(p.under25)}</strong></div><div><small>Both teams score · Yes</small><strong>${pct(p.btts)}</strong></div></div><p class="muted">Elo: ${p.elo.home} / ${p.elo.away} · ${p.sample_sizes.league} prior league matches</p></section></div><section class="panel why"><p class="eyebrow">TRANSPARENT BY DESIGN</p><h2>Why this prediction?</h2>${p.explanation.map(x=>`<p>${esc(x)}</p>`).join('')}<p class="fine-print">${esc(p.assumptions)}<br>Model ${esc(m.model_version)} · Recorded ${date(m.prediction_created_at)} · ${m.eligible?'Pre-kickoff snapshot':'Retrospective / unscored snapshot'}</p></section>`:empty('No prediction recorded','This match has no stored pre-match snapshot. Results are never backfilled into live accuracy.'))+
 `<div class="two-col"><section class="panel"><h2>Your call vs the model</h2><p class="muted">3 points for the correct outcome. Picks close at kickoff.</p>${m.status==='SCHEDULED'&&new Date(m.kickoff+'Z')>new Date()&&!state.impersonating?`<form id="pick-form">${select('Match outcome','outcome',[['Home',m.home+' win'],['Draw','Draw'],['Away',m.away+' win']],m.pick||'Home')}<p class="form-error" role="alert"></p><button class="button" type="submit">${m.pick?'Update pick':'Save pick'}</button></form>`:`<p>${m.pick?'Your pick: '+esc(m.pick):'Picks are closed or unavailable while impersonating.'}</p>`}</section><section class="panel"><h2>Earlier meetings</h2>${m.head_to_head.length?m.head_to_head.map(x=>`<div class="h2h-row"><span>${date(x.date)}<small>${esc(x.home)} vs ${esc(x.away)}</small></span><b>${esc(x.score)}</b></div>`).join(''):empty('No earlier meetings recorded')}</section></div>`;
 if(p)chart('prob-chart','bar',['Home','Draw','Away'],Object.values(p.probabilities).map(x=>x*100),'Probability (%)');
 document.querySelector('#follow').onclick=async()=>{try{const result=await send('/matches/'+id+'/follow');toast(result.message);go('match/'+id);}catch(e){toast(e.message,true);}};
 const form=document.querySelector('#pick-form');if(form)formAction(form,async data=>{toast((await send('/matches/'+id+'/pick',data)).message);go('match/'+id);});
}
````

## frontend/pages/profile.js

````javascript
import {send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {heading,field,formAction,toast} from '../components/ui.js';
export async function profilePage(root){const u=state.user;
 root.innerHTML=heading('YOUR ACCOUNT','Make it yours.','Manage your details and protect your account.')+
 (u.must_change?'<div class="notice" role="alert"><b>Password change required.</b> Set a new password before accessing the rest of PredictPro. Use your current initial or temporary password below.</div>':'')+
 `<div class="two-col"><section class="panel"><h2>Profile details</h2><form id="profile-form">${field('Full name','name','text',u.name,'required minlength="2" maxlength="80"')}${field('Email','email','email',u.email,'required')}${field('Username','username','text',u.username,'required pattern="[a-zA-Z0-9_]{3,30}"')}<p class="form-error" role="alert"></p><button class="button" type="submit" ${u.must_change?'disabled':''}>Save details</button></form></section><section class="panel"><h2>Change password</h2><p class="muted">At least 10 characters; at most 72 UTF-8 bytes. Other sessions will be signed out.</p>${state.impersonating?'<p class="notice">Return to admin to change your own password. Account credentials cannot be changed while impersonating.</p>':`<form id="password-form">${field('Current password','current_password','password','','required autocomplete="current-password"')}${field('New password','password','password','','required minlength="10" autocomplete="new-password"')}${field('Confirm new password','confirm','password','','required minlength="10" autocomplete="new-password"')}<p class="form-error" role="alert"></p><button class="button" type="submit">Update password</button></form>`}</section></div>`;
 formAction(document.querySelector('#profile-form'),async data=>{const result=await send('/auth/profile',data,'PUT');state.user=result.user;toast(result.message);go('profile');});
 const password=document.querySelector('#password-form');if(password)formAction(password,async data=>{if(data.password!==data.confirm)throw new Error('New passwords do not match.');delete data.confirm;const result=await send('/auth/password',data);state.user=result.user;toast(result.message);go('dashboard');});
}
````

## frontend/services/api.js

````javascript
let csrf='';
export function token(value){csrf=value||'';}
export async function api(path, options={}) {
  const headers={'Content-Type':'application/json',...options.headers};
  if(csrf) headers['X-CSRF-Token']=csrf;
  const response=await fetch('/api'+path,{credentials:'same-origin',...options,headers});
  const data=await response.json().catch(()=>({detail:'Server returned an unreadable response.'}));
  if(!response.ok){
    const error=new Error(Array.isArray(data.detail)?data.detail.map(x=>`${x.loc?.slice(1).join('.')}: ${x.msg}`).join('; '):data.detail||'Request failed.');
    error.status=response.status;throw error;
  }
  if(data.csrf) token(data.csrf);
  return data;
}
export const send=(path,body={},method='POST')=>api(path,{method,body:JSON.stringify(body)});
````

## frontend/styles/main.css

````css
@import url('./typography.css');
:root{color-scheme:dark;--bg:#09121f;--panel:#101e2e;--panel2:#142436;--text:#edf3fb;--muted:#94a6bc;--line:#233448;--green:#20d29a;--green-dark:#073d32;--shadow:0 12px 35px #0002;--sidebar:#0b1725;--amber:#e5b963;--red:#ff929e;--blue:#779ff5;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px}
:root[data-theme=light]{color-scheme:light;--bg:#f3f6fa;--panel:#fff;--panel2:#eaf0f7;--text:#172638;--muted:#52667d;--line:#d7e1eb;--green:#087f5e;--green-dark:#d7f5e9;--shadow:0 10px 30px #28415e0b;--sidebar:#fff;--amber:#8a5900;--red:#c0394b;--blue:#3964b8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}a{color:inherit;text-decoration:none}a:hover{color:var(--green)}button,input,select,textarea{font:inherit}button,a,input,select,textarea{touch-action:manipulation}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.45}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--green);outline-offset:3px}h1,h2,h3,p{margin-top:0}h1{font-size:clamp(1.8rem,2.6vw,2.65rem);font-weight:650;letter-spacing:-1.1px;margin-bottom:12px;line-height:1.2}h2{font-size:1.25rem;letter-spacing:-.3px}h3{font-size:1.04rem}p{line-height:1.7}small{display:block;color:var(--muted);font-size:.8rem;line-height:1.6}.muted{color:var(--muted)}.emerald{color:var(--green);font-weight:650}.eyebrow{font-size:.71rem;letter-spacing:2px;font-weight:700;color:var(--green);margin-bottom:14px}.button{border:1px solid transparent;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;gap:12px;background:var(--green);color:#061c19;font-weight:700;min-height:43px;padding:11px 19px;transition:transform .15s,filter .15s;white-space:nowrap}.button:hover{filter:brightness(1.08);color:#061c19;transform:translateY(-1px)}[data-theme=light] .button{color:#fff}.button.secondary{background:var(--panel2);color:var(--text);border-color:var(--line)}.button.danger{background:#b52d43;color:white}.full{width:100%;justify-content:space-between}.icon-button{min-width:38px;min-height:38px;display:inline-flex;align-items:center;justify-content:center;gap:4px;border:1px solid var(--line);color:var(--muted);border-radius:8px;background:transparent;font-size:1.2rem}.icon-button:hover{color:var(--green);background:var(--panel2)}.app-shell{display:flex;min-height:100vh}#sidebar{width:246px;background:var(--sidebar);border-right:1px solid var(--line);position:fixed;inset:0 auto 0 0;padding:30px 20px 22px;display:flex;flex-direction:column;z-index:20;overflow-y:auto}.brand{font-size:1.7rem;font-weight:750;display:flex;align-items:center;letter-spacing:-.8px;gap:0;white-space:nowrap}.brand>span:last-child{color:var(--green)}.brand-mark{width:38px;height:40px;background:var(--green);color:#05291f;border-radius:10px;font-size:1.55rem;margin-right:10px;display:inline-flex;align-items:center;justify-content:center;position:relative;font-weight:800}.brand-mark span{font-size:.9rem;position:absolute;top:1px;right:3px}.nav-label{font-size:.64rem;letter-spacing:1.7px;color:var(--muted);margin:46px 10px 15px}nav{display:flex;flex-direction:column;gap:5px}nav a{display:flex;align-items:center;gap:12px;padding:12px 13px;border-radius:7px;color:var(--muted);font-size:.89rem;font-weight:550}nav a>span{font-size:1.25rem;min-width:20px}nav a:hover{background:var(--panel2)}nav a.active{color:var(--green);background:var(--green-dark);box-shadow:inset 3px 0 var(--green)}.sidebar-bottom{margin-top:auto;padding-top:32px}.sidebar-bottom p{font-size:.72rem;color:var(--muted);margin:16px 7px 0}.model-status{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:8px;padding:14px 10px;font-size:.74rem}.model-status small{font-size:.65rem}.dot{width:6px;height:6px;border-radius:50%;display:inline-block;background:var(--green);flex-shrink:0}.workspace{margin-left:246px;width:calc(100% - 246px);min-width:0}.topbar{height:82px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 40px;background:var(--bg)}.topbar-label{font-size:.66rem;color:var(--muted);letter-spacing:2px;font-weight:650}.live-dot{color:var(--green);font-size:9px;margin-left:10px}.top-actions{display:flex;align-items:center;gap:15px}.avatar{height:35px;width:35px;display:grid;place-items:center;border-radius:50%;background:var(--green-dark);color:var(--green);font-weight:700}.user-label b{font-size:.82rem}.user-label small{font-size:.62rem;letter-spacing:1px}#notification-count{font-size:.67rem;color:var(--green)}#menu{display:none}main{padding:35px 40px 45px;max-width:1580px;margin:auto;outline:none}.page-heading{display:flex;gap:24px;align-items:center;justify-content:space-between;margin-bottom:28px}.page-heading .muted{font-size:.92rem;margin:0;max-width:680px}.page-heading .eyebrow{margin-bottom:9px}.hero-band{border:1px solid #255244;border-radius:13px;background:radial-gradient(ellipse at 80% 30%,#154b41 0,transparent 60%),linear-gradient(115deg,#0f292b,#0c202d);color:#edf7f3;padding:32px 35px;display:flex;justify-content:space-between;position:relative;overflow:hidden;min-height:245px;margin-bottom:32px}.hero-band h2{font-size:2.05rem;font-weight:600;line-height:1.28;margin:16px 0 12px;letter-spacing:-.8px}.hero-band p{color:#a2bdbb;font-size:.87rem}.pill{display:inline-flex;align-items:center;gap:5px;color:var(--green);border:1px solid #20d29a35;background:#20d29a0d;padding:4px 8px;border-radius:5px;font-size:.62rem;font-weight:650;letter-spacing:.5px;line-height:1.4}.hero-band .pill{color:#6ce3b6;border-color:#6ce3b64d}.pill.amber{color:var(--amber);background:#e5b9630b;border-color:#e5b96333}.hero-tags{display:flex;gap:20px;font-size:.7rem;color:#a3c9bc;margin-top:22px}.hero-motif{width:225px;height:225px;border:1px solid #76c7aa33;border-radius:50%;align-self:center;display:grid;place-items:center;box-shadow:0 0 0 35px #66cda20a,0 0 0 70px #66cda207;margin-right:25px}.hero-motif>div{font-size:6.1rem;letter-spacing:-7px;color:#99d8c5;font-weight:300}.hero-motif span{font-size:.75rem;letter-spacing:1px;display:block;line-height:1.6;text-align:center;color:#abd4c8}.section-label{display:flex;align-items:center;justify-content:space-between;gap:15px;margin:28px 0 18px}.section-label h2{margin:0}.section-label>span,.section-label>a{font-size:.74rem}.filters{display:flex;align-items:end;gap:12px;padding:17px;background:var(--panel);border:1px solid var(--line);border-radius:10px;margin-bottom:18px;flex-wrap:wrap}.filters label{flex:1;min-width:130px;margin:0;font-size:.68rem}.filters label:first-child{flex:1.4}.filters input,.filters select{margin-top:7px;min-height:40px;font-size:.8rem}.filters .button{min-height:40px;padding:10px 15px;font-size:.8rem}label{display:block;font-size:.83rem;font-weight:550;color:var(--text);margin-bottom:19px}input,select,textarea{width:100%;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:7px;padding:11px 12px;margin-top:8px;min-height:43px;max-width:100%}input::placeholder,textarea::placeholder{color:var(--muted);opacity:.7}select{padding-right:25px}input[type=checkbox]{width:18px;min-height:18px;margin:0;accent-color:var(--green)}.checkbox{display:flex;gap:10px;align-items:center;line-height:1.7}.match-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.match-card{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:17px 18px;box-shadow:var(--shadow);transition:transform .2s,border .2s}.match-card:hover{transform:translateY(-3px);border-color:#3a655b}.card-meta{display:flex;align-items:center;gap:6px;justify-content:space-between;font-size:.65rem;color:var(--muted)}.card-meta>span:first-child{max-width:60%}.teams{display:grid;grid-template-columns:1fr 30px 1fr;gap:5px;text-align:center;align-items:center;padding:24px 0 10px}.teams>div{display:flex;flex-direction:column;align-items:center;gap:10px}.teams strong{font-size:.81rem;line-height:1.4;min-height:32px;font-weight:600}.team-badge{width:41px;height:45px;display:inline-grid;place-items:center;background:linear-gradient(135deg,#193b38,#0b3b35);border:1px solid #3f7163;color:#9de4cf;border-radius:11px 11px 17px 17px;font-size:.95rem;font-weight:750;letter-spacing:1px}.team-badge.away{background:linear-gradient(135deg,#2d3152,#202a45);border-color:#4e527c;color:#b3c3eb}.team-badge.large{width:65px;height:72px;font-size:1.6rem}.versus{font-size:.72rem;color:var(--muted)}.match-time{text-align:center;font-size:.69rem;color:var(--muted);margin-bottom:20px}.prob-row{display:flex;gap:12px;justify-content:space-between;font-size:.74rem;color:var(--muted)}.prob-row span{flex:1}.prob-row span:nth-child(2){text-align:center}.prob-row span:last-child{text-align:right}.prob-row b{display:block;color:var(--text);font-size:.9rem;margin-top:6px;font-weight:600}.prob-strip{display:flex;height:5px;gap:3px;margin:13px 0 18px;border-radius:8px;overflow:hidden}.prob-strip i:first-child{background:#10b981}.prob-strip i:nth-child(2){background:#e4b453}.prob-strip i:last-child{background:#5d8ee8}.card-foot{display:flex;justify-content:space-between;gap:7px;padding-top:13px;border-top:1px solid var(--line);font-size:.64rem;color:var(--muted)}.card-foot a{color:var(--green);font-weight:600}.card-foot .dot{width:4px;height:4px;margin-right:3px}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:17px;margin-bottom:24px}.stat{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:23px;box-shadow:var(--shadow)}.stat>span{color:var(--muted);font-size:.77rem;text-transform:capitalize}.stat>strong{display:block;font-size:2rem;font-weight:600;letter-spacing:-1px;margin:12px 0 6px}.stat small{font-size:.7rem}.panel{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:25px;margin-bottom:22px;box-shadow:var(--shadow)}.panel .section-label{margin-top:0}.two-col{display:grid;grid-template-columns:1.1fr 1fr;gap:22px;margin-top:22px}.two-col .panel{margin:0}.chart-container{height:250px;position:relative;margin:15px 0 22px}.fine-print{font-size:.74rem;color:var(--muted);line-height:1.7;margin:20px 0 0}.empty{padding:35px 20px;text-align:center;grid-column:1/-1;background:var(--panel);border-radius:9px;color:var(--muted);width:100%}.empty p{max-width:480px;margin:0 auto;font-size:.85rem}.empty h3{color:var(--text)}.empty-icon{font-size:2rem;display:block;margin-bottom:15px;color:var(--green)}.pager{display:flex;gap:15px;justify-content:center;align-items:center;margin:24px 0;font-size:.8rem;color:var(--muted)}.pager .button{font-size:.77rem}.back-link{font-size:.8rem;color:var(--muted);display:block;margin-bottom:20px}.match-hero{display:grid;grid-template-columns:1fr 180px 1fr;align-items:center;gap:20px;text-align:center;padding:30px;background:var(--panel);border:1px solid var(--line);border-radius:11px}.match-hero h2{margin:16px 0;font-size:1.25rem}.score-block strong{display:block;font-size:3.5rem;margin:16px 0 8px;letter-spacing:-2px}.form-guide{display:flex;justify-content:center;gap:5px}.form-guide span:not(.muted){font-size:.7rem;display:grid;place-items:center;width:24px;height:24px;border-radius:4px;font-weight:650}.form-W{color:#51dbaa;background:#164b39}.form-D{color:#e5c568;background:#524526}.form-L{color:#ff9aa0;background:#552a34}.insight-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:27px 0}.insight-grid strong{display:block;font-size:1.6rem;color:var(--green);margin-top:8px}.why{margin-top:22px}.why>p:not(.eyebrow):not(.fine-print){font-size:.9rem;color:var(--muted);padding-left:18px;border-left:2px solid var(--green-dark)}.h2h-row{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid var(--line);padding:15px 0;font-size:.8rem}.h2h-row small{margin-top:5px}.notice{padding:18px;background:#e5b96314;border:1px solid #e5b96345;color:var(--amber);border-radius:8px;margin:20px 0;font-size:.85rem}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:.8rem}th{color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.7px;font-weight:600;padding:15px;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:17px 15px;border-bottom:1px solid var(--line);line-height:1.6}td small{margin-top:3px;font-size:.7rem;max-width:280px}tbody tr:hover{background:var(--panel2)}.table-actions{display:flex;flex-wrap:wrap;gap:7px;min-width:210px}.table-actions button{border:1px solid var(--line);border-radius:5px;padding:5px 9px;color:var(--muted);background:transparent;font-size:.72rem;white-space:nowrap}.table-actions button:hover{color:var(--green);border-color:var(--green)}.text-danger{color:var(--red)!important}.tabs{display:flex;gap:8px;margin-bottom:20px}.tabs button{padding:10px 22px;background:var(--panel);border:1px solid var(--line);color:var(--muted);border-radius:7px}.tabs button.active{color:var(--green);border-color:var(--green)}.narrow{max-width:670px}.activity-row{display:flex;gap:14px;padding:13px 0;border-bottom:1px solid var(--line);font-size:.78rem}.activity-row .dot{margin-top:6px}.notification{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:22px 0;border-bottom:1px solid var(--line)}.notification h3{margin:12px 0 7px;line-height:1.5}.notification p{font-size:.75rem;margin-bottom:0}.notification.read{opacity:.7}.team-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}.team-panel{text-align:center;margin-bottom:0}.team-panel h3{margin:19px 0}.actions{display:flex;gap:10px;flex-wrap:wrap}footer{padding:23px 40px;font-size:.7rem;color:var(--muted);border-top:1px solid var(--line);line-height:1.6}.impersonation{display:flex;justify-content:space-between;align-items:center;gap:15px;background:#8b5f12;color:white;padding:12px 40px;position:sticky;top:0;z-index:10;font-weight:650}.auth-layout{min-height:100vh;display:grid;grid-template-columns:1fr 1fr}.auth-story{background:radial-gradient(circle at 40% 60%,#12483955,transparent 65%),#0b1928;color:#eff7f3;padding:45px 10%;display:flex;flex-direction:column;justify-content:space-between;min-height:100vh;overflow:hidden}.auth-story>div{max-width:530px;margin:60px 0 35px}.auth-story h1{font-size:clamp(2.5rem,4.2vw,4.8rem);font-weight:550;letter-spacing:-2.5px;line-height:1.13;margin:25px 0}.auth-story em{font-style:normal;color:#43d7a5}.auth-story p{font-size:.93rem;color:#9fb4bd;max-width:420px}.auth-story small{font-size:.66rem}.auth-story .eyebrow{color:#49d5ab;font-size:.7rem}.auth-story>.muted{font-size:.65rem;letter-spacing:2px}.auth-panel{padding:40px 12%;display:flex;align-items:center;justify-content:center;position:relative}.auth-panel>.icon-button{position:absolute;right:30px;top:30px}.auth-form-wrap{width:100%;max-width:390px}.auth-form-wrap h2{font-size:2rem;line-height:1.25;letter-spacing:-1px}.auth-form-wrap>.muted{font-size:.88rem;margin-bottom:30px}.auth-form-wrap form{margin-top:25px}.auth-links{text-align:center;margin:22px 0;font-size:.82rem;color:var(--muted)}.auth-links a{color:var(--green)}.auth-links p{margin-top:16px}.auth-note{font-size:.7rem;color:var(--muted);border-top:1px solid var(--line);padding-top:24px;text-align:center;line-height:1.8}.pitch-art{position:relative;height:180px;border:1px solid #45847555;border-radius:7px;transform:perspective(400px) rotateX(20deg) rotate(-7deg);margin:50px 15px 25px;background:repeating-linear-gradient(90deg,#1a5d421c 0 50px,transparent 50px 100px)}.pitch-circle{border:1px solid #45847566;border-radius:50%;width:90px;height:90px;position:absolute;left:calc(50% - 45px);top:calc(50% - 45px)}.pitch-line{position:absolute;left:50%;top:0;bottom:0;border-left:1px solid #45847566}.pitch-chip{position:absolute;top:15px;left:15px;border:1px solid #408f7966;border-radius:8px;background:#102b2c;padding:15px;font-size:1.8rem;color:#79ebbf}.pitch-chip small{font-size:.5rem;letter-spacing:1px;color:#9bb5b5}.pitch-chip.second{top:auto;bottom:-12px;left:auto;right:16px}.form-error{font-size:.8rem;color:var(--red);min-height:1em;line-height:1.5}.form-error:empty{margin:0 0 12px;min-height:0}#toasts{position:fixed;bottom:24px;right:24px;z-index:200;display:flex;flex-direction:column;gap:10px;max-width:min(450px,90vw)}.toast{background:var(--panel2);border:1px solid var(--green);box-shadow:0 12px 40px #0004;border-radius:9px;padding:16px 22px;font-size:.85rem;line-height:1.6;animation:slide-in .2s}.toast.error{border-color:var(--red)}dialog{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:13px;max-width:620px;width:calc(100% - 32px);padding:28px;max-height:90vh;box-shadow:0 25px 90px #0008}dialog::backdrop{background:#020b16b8;backdrop-filter:blur(4px)}#dialog-close{margin-top:20px}.report{font-size:.8rem;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere;padding:15px;background:var(--bg);border-radius:7px}.details{display:grid;grid-template-columns:1fr 2fr;gap:15px;font-size:.85rem;overflow-wrap:anywhere}.details dt{color:var(--muted);text-transform:capitalize}.details dd{margin:0}.skeleton{min-height:220px;background:linear-gradient(90deg,var(--panel),var(--panel2),var(--panel));background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:10px;margin-bottom:20px}.skip{position:fixed;top:-80px;left:20px;padding:12px;background:var(--green);color:#05291f;z-index:300}.skip:focus{top:12px}@keyframes shimmer{to{background-position:-200% 0}}@keyframes slide-in{from{transform:translateY(8px);opacity:0}to{transform:translateY(0);opacity:1}}
@media(min-width:1600px){.match-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:1200px){#sidebar{width:216px;padding-left:14px;padding-right:14px}.workspace{margin-left:216px;width:calc(100% - 216px)}main{padding:28px 25px}.topbar{padding:0 25px}.match-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hero-motif{width:175px;height:175px;margin-right:5px}.hero-motif>div{font-size:5rem}.page-heading{align-items:flex-start}.page-heading .actions{justify-content:flex-end}.auth-story{padding:35px 9%}.auth-panel{padding:40px 9%}}
@media(max-width:900px){#sidebar{transform:translateX(-100%);transition:transform .2s;width:246px;box-shadow:20px 0 90px #0006}#sidebar.open{transform:translateX(0)}.workspace{margin-left:0;width:100%}#menu{display:inline-flex}.topbar{height:70px;gap:12px}.topbar-label{margin-right:auto;font-size:.6rem;letter-spacing:1px}.two-col{grid-template-columns:1fr 1fr}.page-heading h1{font-size:2rem}.page-heading .button{font-size:.75rem}.auth-layout{grid-template-columns:.9fr 1fr}.auth-story{padding:35px 25px}.auth-panel{padding:35px}.auth-story h1{font-size:3rem}}
@media(max-width:650px){main{padding:25px 17px}.topbar{padding:0 17px}.topbar-label{display:none}.top-actions{margin-left:auto;gap:9px}.user-label{display:none}.page-heading{display:block;margin-bottom:23px}.page-heading>div+*{margin-top:18px}.page-heading .muted{font-size:.85rem}.hero-band{padding:24px;min-height:0}.hero-band h2{font-size:1.65rem}.hero-band p{font-size:.8rem}.hero-motif{display:none}.hero-tags{flex-wrap:wrap;gap:10px;font-size:.65rem}.section-label{align-items:flex-start}.section-label>span{max-width:140px;text-align:right;line-height:1.6}.match-grid{grid-template-columns:1fr}.match-card{padding:20px}.teams{padding:22px 10px 12px}.teams strong{font-size:.9rem}.card-meta{font-size:.7rem}.card-foot{font-size:.73rem}.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.stat{padding:18px}.stat>strong{font-size:1.7rem}.stat>span{font-size:.7rem}.stat small{font-size:.64rem}.filters{gap:12px;padding:14px}.filters label:first-child{flex:1 0 100%}.filters label{flex:1 0 40%;min-width:0}.filters .button{width:100%}.two-col{grid-template-columns:1fr;gap:16px}.panel{padding:21px}.match-hero{grid-template-columns:1fr 90px 1fr;padding:23px 12px;gap:6px}.match-hero h2{font-size:.86rem;line-height:1.6}.team-badge.large{width:48px;height:54px;font-size:1.2rem}.score-block strong{font-size:2.2rem}.score-block small{font-size:.62rem}.score-block .pill{font-size:.53rem}.form-guide{gap:3px}.form-guide span:not(.muted){width:20px;height:21px;font-size:.6rem}.chart-container{height:220px}.insight-grid strong{font-size:1.4rem}.notification{align-items:flex-start;flex-direction:column;gap:10px}.impersonation{padding:12px 17px;font-size:.8rem}.impersonation .button{padding:8px;font-size:.7rem}.auth-layout{display:block}.auth-story{min-height:0;padding:25px}.auth-story>div,.auth-story>.muted{display:none}.auth-panel{padding:70px 25px 40px;min-height:calc(100vh - 90px);align-items:flex-start}.auth-panel>.icon-button{top:20px;right:25px}.auth-form-wrap h2{font-size:1.8rem}.team-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.team-panel{padding:18px 10px}.team-panel .button{font-size:.7rem;padding:8px}.team-panel h3{font-size:.85rem}footer{padding:22px 17px}.tabs button{padding:10px 17px}#toasts{bottom:15px;right:15px}.details{grid-template-columns:1fr 1.5fr}.actions{justify-content:flex-start!important}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
````

## frontend/styles/typography.css

````css
/* System-font fallback keeps the application fully functional offline.
   Inter is used when installed locally; no remote font request or tracking. */
@font-face{font-family:Inter;src:local('Inter');font-display:swap}
````

## frontend/vendor/LICENSE-Chart.js.txt

````text
The MIT License (MIT)

Copyright (c) 2014-2025 Chart.js Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Vendored distribution: Chart.js 4.4.8
Original distribution: https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.js
Project: https://github.com/chartjs/Chart.js
````

## frontend/vendor/chart.umd.js

````javascript
/*!
 * Chart.js v4.4.8
 * https://www.chartjs.org
 * (c) 2025 Chart.js Contributors
 * Released under the MIT License
 */
!function(t,e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define(e):(t="undefined"!=typeof globalThis?globalThis:t||self).Chart=e()}(this,(function(){"use strict";var t=Object.freeze({__proto__:null,get Colors(){return Go},get Decimation(){return Qo},get Filler(){return ma},get Legend(){return ya},get SubTitle(){return ka},get Title(){return Ma},get Tooltip(){return Ba}});function e(){}const i=(()=>{let t=0;return()=>t++})();function s(t){return null==t}function n(t){if(Array.isArray&&Array.isArray(t))return!0;const e=Object.prototype.toString.call(t);return"[object"===e.slice(0,7)&&"Array]"===e.slice(-6)}function o(t){return null!==t&&"[object Object]"===Object.prototype.toString.call(t)}function a(t){return("number"==typeof t||t instanceof Number)&&isFinite(+t)}function r(t,e){return a(t)?t:e}function l(t,e){return void 0===t?e:t}const h=(t,e)=>"string"==typeof t&&t.endsWith("%")?parseFloat(t)/100:+t/e,c=(t,e)=>"string"==typeof t&&t.endsWith("%")?parseFloat(t)/100*e:+t;function d(t,e,i){if(t&&"function"==typeof t.call)return t.apply(i,e)}function u(t,e,i,s){let a,r,l;if(n(t))if(r=t.length,s)for(a=r-1;a>=0;a--)e.call(i,t[a],a);else for(a=0;a<r;a++)e.call(i,t[a],a);else if(o(t))for(l=Object.keys(t),r=l.length,a=0;a<r;a++)e.call(i,t[l[a]],l[a])}function f(t,e){let i,s,n,o;if(!t||!e||t.length!==e.length)return!1;for(i=0,s=t.length;i<s;++i)if(n=t[i],o=e[i],n.datasetIndex!==o.datasetIndex||n.index!==o.index)return!1;return!0}function g(t){if(n(t))return t.map(g);if(o(t)){const e=Object.create(null),i=Object.keys(t),s=i.length;let n=0;for(;n<s;++n)e[i[n]]=g(t[i[n]]);return e}return t}function p(t){return-1===["__proto__","prototype","constructor"].indexOf(t)}function m(t,e,i,s){if(!p(t))return;const n=e[t],a=i[t];o(n)&&o(a)?x(n,a,s):e[t]=g(a)}function x(t,e,i){const s=n(e)?e:[e],a=s.length;if(!o(t))return t;const r=(i=i||{}).merger||m;let l;for(let e=0;e<a;++e){if(l=s[e],!o(l))continue;const n=Object.keys(l);for(let e=0,s=n.length;e<s;++e)r(n[e],t,l,i)}return t}function b(t,e){return x(t,e,{merger:_})}function _(t,e,i){if(!p(t))return;const s=e[t],n=i[t];o(s)&&o(n)?b(s,n):Object.prototype.hasOwnProperty.call(e,t)||(e[t]=g(n))}const y={"":t=>t,x:t=>t.x,y:t=>t.y};function v(t){const e=t.split("."),i=[];let s="";for(const t of e)s+=t,s.endsWith("\\")?s=s.slice(0,-1)+".":(i.push(s),s="");return i}function M(t,e){const i=y[e]||(y[e]=function(t){const e=v(t);return t=>{for(const i of e){if(""===i)break;t=t&&t[i]}return t}}(e));return i(t)}function w(t){return t.charAt(0).toUpperCase()+t.slice(1)}const k=t=>void 0!==t,S=t=>"function"==typeof t,P=(t,e)=>{if(t.size!==e.size)return!1;for(const i of t)if(!e.has(i))return!1;return!0};function D(t){return"mouseup"===t.type||"click"===t.type||"contextmenu"===t.type}const C=Math.PI,O=2*C,A=O+C,T=Number.POSITIVE_INFINITY,L=C/180,E=C/2,R=C/4,I=2*C/3,z=Math.log10,F=Math.sign;function V(t,e,i){return Math.abs(t-e)<i}function B(t){const e=Math.round(t);t=V(t,e,t/1e3)?e:t;const i=Math.pow(10,Math.floor(z(t))),s=t/i;return(s<=1?1:s<=2?2:s<=5?5:10)*i}function W(t){const e=[],i=Math.sqrt(t);let s;for(s=1;s<i;s++)t%s==0&&(e.push(s),e.push(t/s));return i===(0|i)&&e.push(i),e.sort(((t,e)=>t-e)).pop(),e}function N(t){return!function(t){return"symbol"==typeof t||"object"==typeof t&&null!==t&&!(Symbol.toPrimitive in t||"toString"in t||"valueOf"in t)}(t)&&!isNaN(parseFloat(t))&&isFinite(t)}function H(t,e){const i=Math.round(t);return i-e<=t&&i+e>=t}function j(t,e,i){let s,n,o;for(s=0,n=t.length;s<n;s++)o=t[s][i],isNaN(o)||(e.min=Math.min(e.min,o),e.max=Math.max(e.max,o))}function $(t){return t*(C/180)}function Y(t){return t*(180/C)}function U(t){if(!a(t))return;let e=1,i=0;for(;Math.round(t*e)/e!==t;)e*=10,i++;return i}function X(t,e){const i=e.x-t.x,s=e.y-t.y,n=Math.sqrt(i*i+s*s);let o=Math.atan2(s,i);return o<-.5*C&&(o+=O),{angle:o,distance:n}}function q(t,e){return Math.sqrt(Math.pow(e.x-t.x,2)+Math.pow(e.y-t.y,2))}function K(t,e){return(t-e+A)%O-C}function G(t){return(t%O+O)%O}function Z(t,e,i,s){const n=G(t),o=G(e),a=G(i),r=G(o-n),l=G(a-n),h=G(n-o),c=G(n-a);return n===o||n===a||s&&o===a||r>l&&h<c}function J(t,e,i){return Math.max(e,Math.min(i,t))}function Q(t){return J(t,-32768,32767)}function tt(t,e,i,s=1e-6){return t>=Math.min(e,i)-s&&t<=Math.max(e,i)+s}function et(t,e,i){i=i||(i=>t[i]<e);let s,n=t.length-1,o=0;for(;n-o>1;)s=o+n>>1,i(s)?o=s:n=s;return{lo:o,hi:n}}const it=(t,e,i,s)=>et(t,i,s?s=>{const n=t[s][e];return n<i||n===i&&t[s+1][e]===i}:s=>t[s][e]<i),st=(t,e,i)=>et(t,i,(s=>t[s][e]>=i));function nt(t,e,i){let s=0,n=t.length;for(;s<n&&t[s]<e;)s++;for(;n>s&&t[n-1]>i;)n--;return s>0||n<t.length?t.slice(s,n):t}const ot=["push","pop","shift","splice","unshift"];function at(t,e){t._chartjs?t._chartjs.listeners.push(e):(Object.defineProperty(t,"_chartjs",{configurable:!0,enumerable:!1,value:{listeners:[e]}}),ot.forEach((e=>{const i="_onData"+w(e),s=t[e];Object.defineProperty(t,e,{configurable:!0,enumerable:!1,value(...e){const n=s.apply(this,e);return t._chartjs.listeners.forEach((t=>{"function"==typeof t[i]&&t[i](...e)})),n}})})))}function rt(t,e){const i=t._chartjs;if(!i)return;const s=i.listeners,n=s.indexOf(e);-1!==n&&s.splice(n,1),s.length>0||(ot.forEach((e=>{delete t[e]})),delete t._chartjs)}function lt(t){const e=new Set(t);return e.size===t.length?t:Array.from(e)}const ht="undefined"==typeof window?function(t){return t()}:window.requestAnimationFrame;function ct(t,e){let i=[],s=!1;return function(...n){i=n,s||(s=!0,ht.call(window,(()=>{s=!1,t.apply(e,i)})))}}function dt(t,e){let i;return function(...s){return e?(clearTimeout(i),i=setTimeout(t,e,s)):t.apply(this,s),e}}const ut=t=>"start"===t?"left":"end"===t?"right":"center",ft=(t,e,i)=>"start"===t?e:"end"===t?i:(e+i)/2,gt=(t,e,i,s)=>t===(s?"left":"right")?i:"center"===t?(e+i)/2:e;function pt(t,e,i){const n=e.length;let o=0,a=n;if(t._sorted){const{iScale:r,vScale:l,_parsed:h}=t,c=t.dataset&&t.dataset.options?t.dataset.options.spanGaps:null,d=r.axis,{min:u,max:f,minDefined:g,maxDefined:p}=r.getUserBounds();if(g){if(o=Math.min(it(h,d,u).lo,i?n:it(e,d,r.getPixelForValue(u)).lo),c){const t=h.slice(0,o+1).reverse().findIndex((t=>!s(t[l.axis])));o-=Math.max(0,t)}o=J(o,0,n-1)}if(p){let t=Math.max(it(h,r.axis,f,!0).hi+1,i?0:it(e,d,r.getPixelForValue(f),!0).hi+1);if(c){const e=h.slice(t-1).findIndex((t=>!s(t[l.axis])));t+=Math.max(0,e)}a=J(t,o,n)-o}else a=n-o}return{start:o,count:a}}function mt(t){const{xScale:e,yScale:i,_scaleRanges:s}=t,n={xmin:e.min,xmax:e.max,ymin:i.min,ymax:i.max};if(!s)return t._scaleRanges=n,!0;const o=s.xmin!==e.min||s.xmax!==e.max||s.ymin!==i.min||s.ymax!==i.max;return Object.assign(s,n),o}class xt{constructor(){this._request=null,this._charts=new Map,this._running=!1,this._lastDate=void 0}_notify(t,e,i,s){const n=e.listeners[s],o=e.duration;n.forEach((s=>s({chart:t,initial:e.initial,numSteps:o,currentStep:Math.min(i-e.start,o)})))}_refresh(){this._request||(this._running=!0,this._request=ht.call(window,(()=>{this._update(),this._request=null,this._running&&this._refresh()})))}_update(t=Date.now()){let e=0;this._charts.forEach(((i,s)=>{if(!i.running||!i.items.length)return;const n=i.items;let o,a=n.length-1,r=!1;for(;a>=0;--a)o=n[a],o._active?(o._total>i.duration&&(i.duration=o._total),o.tick(t),r=!0):(n[a]=n[n.length-1],n.pop());r&&(s.draw(),this._notify(s,i,t,"progress")),n.length||(i.running=!1,this._notify(s,i,t,"complete"),i.initial=!1),e+=n.length})),this._lastDate=t,0===e&&(this._running=!1)}_getAnims(t){const e=this._charts;let i=e.get(t);return i||(i={running:!1,initial:!0,items:[],listeners:{complete:[],progress:[]}},e.set(t,i)),i}listen(t,e,i){this._getAnims(t).listeners[e].push(i)}add(t,e){e&&e.length&&this._getAnims(t).items.push(...e)}has(t){return this._getAnims(t).items.length>0}start(t){const e=this._charts.get(t);e&&(e.running=!0,e.start=Date.now(),e.duration=e.items.reduce(((t,e)=>Math.max(t,e._duration)),0),this._refresh())}running(t){if(!this._running)return!1;const e=this._charts.get(t);return!!(e&&e.running&&e.items.length)}stop(t){const e=this._charts.get(t);if(!e||!e.items.length)return;const i=e.items;let s=i.length-1;for(;s>=0;--s)i[s].cancel();e.items=[],this._notify(t,e,Date.now(),"complete")}remove(t){return this._charts.delete(t)}}var bt=new xt;
/*!
 * @kurkle/color v0.3.2
 * https://github.com/kurkle/color#readme
 * (c) 2023 Jukka Kurkela
 * Released under the MIT License
 */function _t(t){return t+.5|0}const yt=(t,e,i)=>Math.max(Math.min(t,i),e);function vt(t){return yt(_t(2.55*t),0,255)}function Mt(t){return yt(_t(255*t),0,255)}function wt(t){return yt(_t(t/2.55)/100,0,1)}function kt(t){return yt(_t(100*t),0,100)}const St={0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,A:10,B:11,C:12,D:13,E:14,F:15,a:10,b:11,c:12,d:13,e:14,f:15},Pt=[..."0123456789ABCDEF"],Dt=t=>Pt[15&t],Ct=t=>Pt[(240&t)>>4]+Pt[15&t],Ot=t=>(240&t)>>4==(15&t);function At(t){var e=(t=>Ot(t.r)&&Ot(t.g)&&Ot(t.b)&&Ot(t.a))(t)?Dt:Ct;return t?"#"+e(t.r)+e(t.g)+e(t.b)+((t,e)=>t<255?e(t):"")(t.a,e):void 0}const Tt=/^(hsla?|hwb|hsv)\(\s*([-+.e\d]+)(?:deg)?[\s,]+([-+.e\d]+)%[\s,]+([-+.e\d]+)%(?:[\s,]+([-+.e\d]+)(%)?)?\s*\)$/;function Lt(t,e,i){const s=e*Math.min(i,1-i),n=(e,n=(e+t/30)%12)=>i-s*Math.max(Math.min(n-3,9-n,1),-1);return[n(0),n(8),n(4)]}function Et(t,e,i){const s=(s,n=(s+t/60)%6)=>i-i*e*Math.max(Math.min(n,4-n,1),0);return[s(5),s(3),s(1)]}function Rt(t,e,i){const s=Lt(t,1,.5);let n;for(e+i>1&&(n=1/(e+i),e*=n,i*=n),n=0;n<3;n++)s[n]*=1-e-i,s[n]+=e;return s}function It(t){const e=t.r/255,i=t.g/255,s=t.b/255,n=Math.max(e,i,s),o=Math.min(e,i,s),a=(n+o)/2;let r,l,h;return n!==o&&(h=n-o,l=a>.5?h/(2-n-o):h/(n+o),r=function(t,e,i,s,n){return t===n?(e-i)/s+(e<i?6:0):e===n?(i-t)/s+2:(t-e)/s+4}(e,i,s,h,n),r=60*r+.5),[0|r,l||0,a]}function zt(t,e,i,s){return(Array.isArray(e)?t(e[0],e[1],e[2]):t(e,i,s)).map(Mt)}function Ft(t,e,i){return zt(Lt,t,e,i)}function Vt(t){return(t%360+360)%360}function Bt(t){const e=Tt.exec(t);let i,s=255;if(!e)return;e[5]!==i&&(s=e[6]?vt(+e[5]):Mt(+e[5]));const n=Vt(+e[2]),o=+e[3]/100,a=+e[4]/100;return i="hwb"===e[1]?function(t,e,i){return zt(Rt,t,e,i)}(n,o,a):"hsv"===e[1]?function(t,e,i){return zt(Et,t,e,i)}(n,o,a):Ft(n,o,a),{r:i[0],g:i[1],b:i[2],a:s}}const Wt={x:"dark",Z:"light",Y:"re",X:"blu",W:"gr",V:"medium",U:"slate",A:"ee",T:"ol",S:"or",B:"ra",C:"lateg",D:"ights",R:"in",Q:"turquois",E:"hi",P:"ro",O:"al",N:"le",M:"de",L:"yello",F:"en",K:"ch",G:"arks",H:"ea",I:"ightg",J:"wh"},Nt={OiceXe:"f0f8ff",antiquewEte:"faebd7",aqua:"ffff",aquamarRe:"7fffd4",azuY:"f0ffff",beige:"f5f5dc",bisque:"ffe4c4",black:"0",blanKedOmond:"ffebcd",Xe:"ff",XeviTet:"8a2be2",bPwn:"a52a2a",burlywood:"deb887",caMtXe:"5f9ea0",KartYuse:"7fff00",KocTate:"d2691e",cSO:"ff7f50",cSnflowerXe:"6495ed",cSnsilk:"fff8dc",crimson:"dc143c",cyan:"ffff",xXe:"8b",xcyan:"8b8b",xgTMnPd:"b8860b",xWay:"a9a9a9",xgYF:"6400",xgYy:"a9a9a9",xkhaki:"bdb76b",xmagFta:"8b008b",xTivegYF:"556b2f",xSange:"ff8c00",xScEd:"9932cc",xYd:"8b0000",xsOmon:"e9967a",xsHgYF:"8fbc8f",xUXe:"483d8b",xUWay:"2f4f4f",xUgYy:"2f4f4f",xQe:"ced1",xviTet:"9400d3",dAppRk:"ff1493",dApskyXe:"bfff",dimWay:"696969",dimgYy:"696969",dodgerXe:"1e90ff",fiYbrick:"b22222",flSOwEte:"fffaf0",foYstWAn:"228b22",fuKsia:"ff00ff",gaRsbSo:"dcdcdc",ghostwEte:"f8f8ff",gTd:"ffd700",gTMnPd:"daa520",Way:"808080",gYF:"8000",gYFLw:"adff2f",gYy:"808080",honeyMw:"f0fff0",hotpRk:"ff69b4",RdianYd:"cd5c5c",Rdigo:"4b0082",ivSy:"fffff0",khaki:"f0e68c",lavFMr:"e6e6fa",lavFMrXsh:"fff0f5",lawngYF:"7cfc00",NmoncEffon:"fffacd",ZXe:"add8e6",ZcSO:"f08080",Zcyan:"e0ffff",ZgTMnPdLw:"fafad2",ZWay:"d3d3d3",ZgYF:"90ee90",ZgYy:"d3d3d3",ZpRk:"ffb6c1",ZsOmon:"ffa07a",ZsHgYF:"20b2aa",ZskyXe:"87cefa",ZUWay:"778899",ZUgYy:"778899",ZstAlXe:"b0c4de",ZLw:"ffffe0",lime:"ff00",limegYF:"32cd32",lRF:"faf0e6",magFta:"ff00ff",maPon:"800000",VaquamarRe:"66cdaa",VXe:"cd",VScEd:"ba55d3",VpurpN:"9370db",VsHgYF:"3cb371",VUXe:"7b68ee",VsprRggYF:"fa9a",VQe:"48d1cc",VviTetYd:"c71585",midnightXe:"191970",mRtcYam:"f5fffa",mistyPse:"ffe4e1",moccasR:"ffe4b5",navajowEte:"ffdead",navy:"80",Tdlace:"fdf5e6",Tive:"808000",TivedBb:"6b8e23",Sange:"ffa500",SangeYd:"ff4500",ScEd:"da70d6",pOegTMnPd:"eee8aa",pOegYF:"98fb98",pOeQe:"afeeee",pOeviTetYd:"db7093",papayawEp:"ffefd5",pHKpuff:"ffdab9",peru:"cd853f",pRk:"ffc0cb",plum:"dda0dd",powMrXe:"b0e0e6",purpN:"800080",YbeccapurpN:"663399",Yd:"ff0000",Psybrown:"bc8f8f",PyOXe:"4169e1",saddNbPwn:"8b4513",sOmon:"fa8072",sandybPwn:"f4a460",sHgYF:"2e8b57",sHshell:"fff5ee",siFna:"a0522d",silver:"c0c0c0",skyXe:"87ceeb",UXe:"6a5acd",UWay:"708090",UgYy:"708090",snow:"fffafa",sprRggYF:"ff7f",stAlXe:"4682b4",tan:"d2b48c",teO:"8080",tEstN:"d8bfd8",tomato:"ff6347",Qe:"40e0d0",viTet:"ee82ee",JHt:"f5deb3",wEte:"ffffff",wEtesmoke:"f5f5f5",Lw:"ffff00",LwgYF:"9acd32"};let Ht;function jt(t){Ht||(Ht=function(){const t={},e=Object.keys(Nt),i=Object.keys(Wt);let s,n,o,a,r;for(s=0;s<e.length;s++){for(a=r=e[s],n=0;n<i.length;n++)o=i[n],r=r.replace(o,Wt[o]);o=parseInt(Nt[a],16),t[r]=[o>>16&255,o>>8&255,255&o]}return t}(),Ht.transparent=[0,0,0,0]);const e=Ht[t.toLowerCase()];return e&&{r:e[0],g:e[1],b:e[2],a:4===e.length?e[3]:255}}const $t=/^rgba?\(\s*([-+.\d]+)(%)?[\s,]+([-+.e\d]+)(%)?[\s,]+([-+.e\d]+)(%)?(?:[\s,/]+([-+.e\d]+)(%)?)?\s*\)$/;const Yt=t=>t<=.0031308?12.92*t:1.055*Math.pow(t,1/2.4)-.055,Ut=t=>t<=.04045?t/12.92:Math.pow((t+.055)/1.055,2.4);function Xt(t,e,i){if(t){let s=It(t);s[e]=Math.max(0,Math.min(s[e]+s[e]*i,0===e?360:1)),s=Ft(s),t.r=s[0],t.g=s[1],t.b=s[2]}}function qt(t,e){return t?Object.assign(e||{},t):t}function Kt(t){var e={r:0,g:0,b:0,a:255};return Array.isArray(t)?t.length>=3&&(e={r:t[0],g:t[1],b:t[2],a:255},t.length>3&&(e.a=Mt(t[3]))):(e=qt(t,{r:0,g:0,b:0,a:1})).a=Mt(e.a),e}function Gt(t){return"r"===t.charAt(0)?function(t){const e=$t.exec(t);let i,s,n,o=255;if(e){if(e[7]!==i){const t=+e[7];o=e[8]?vt(t):yt(255*t,0,255)}return i=+e[1],s=+e[3],n=+e[5],i=255&(e[2]?vt(i):yt(i,0,255)),s=255&(e[4]?vt(s):yt(s,0,255)),n=255&(e[6]?vt(n):yt(n,0,255)),{r:i,g:s,b:n,a:o}}}(t):Bt(t)}class Zt{constructor(t){if(t instanceof Zt)return t;const e=typeof t;let i;var s,n,o;"object"===e?i=Kt(t):"string"===e&&(o=(s=t).length,"#"===s[0]&&(4===o||5===o?n={r:255&17*St[s[1]],g:255&17*St[s[2]],b:255&17*St[s[3]],a:5===o?17*St[s[4]]:255}:7!==o&&9!==o||(n={r:St[s[1]]<<4|St[s[2]],g:St[s[3]]<<4|St[s[4]],b:St[s[5]]<<4|St[s[6]],a:9===o?St[s[7]]<<4|St[s[8]]:255})),i=n||jt(t)||Gt(t)),this._rgb=i,this._valid=!!i}get valid(){return this._valid}get rgb(){var t=qt(this._rgb);return t&&(t.a=wt(t.a)),t}set rgb(t){this._rgb=Kt(t)}rgbString(){return this._valid?(t=this._rgb)&&(t.a<255?`rgba(${t.r}, ${t.g}, ${t.b}, ${wt(t.a)})`:`rgb(${t.r}, ${t.g}, ${t.b})`):void 0;var t}hexString(){return this._valid?At(this._rgb):void 0}hslString(){return this._valid?function(t){if(!t)return;const e=It(t),i=e[0],s=kt(e[1]),n=kt(e[2]);return t.a<255?`hsla(${i}, ${s}%, ${n}%, ${wt(t.a)})`:`hsl(${i}, ${s}%, ${n}%)`}(this._rgb):void 0}mix(t,e){if(t){const i=this.rgb,s=t.rgb;let n;const o=e===n?.5:e,a=2*o-1,r=i.a-s.a,l=((a*r==-1?a:(a+r)/(1+a*r))+1)/2;n=1-l,i.r=255&l*i.r+n*s.r+.5,i.g=255&l*i.g+n*s.g+.5,i.b=255&l*i.b+n*s.b+.5,i.a=o*i.a+(1-o)*s.a,this.rgb=i}return this}interpolate(t,e){return t&&(this._rgb=function(t,e,i){const s=Ut(wt(t.r)),n=Ut(wt(t.g)),o=Ut(wt(t.b));return{r:Mt(Yt(s+i*(Ut(wt(e.r))-s))),g:Mt(Yt(n+i*(Ut(wt(e.g))-n))),b:Mt(Yt(o+i*(Ut(wt(e.b))-o))),a:t.a+i*(e.a-t.a)}}(this._rgb,t._rgb,e)),this}clone(){return new Zt(this.rgb)}alpha(t){return this._rgb.a=Mt(t),this}clearer(t){return this._rgb.a*=1-t,this}greyscale(){const t=this._rgb,e=_t(.3*t.r+.59*t.g+.11*t.b);return t.r=t.g=t.b=e,this}opaquer(t){return this._rgb.a*=1+t,this}negate(){const t=this._rgb;return t.r=255-t.r,t.g=255-t.g,t.b=255-t.b,this}lighten(t){return Xt(this._rgb,2,t),this}darken(t){return Xt(this._rgb,2,-t),this}saturate(t){return Xt(this._rgb,1,t),this}desaturate(t){return Xt(this._rgb,1,-t),this}rotate(t){return function(t,e){var i=It(t);i[0]=Vt(i[0]+e),i=Ft(i),t.r=i[0],t.g=i[1],t.b=i[2]}(this._rgb,t),this}}function Jt(t){if(t&&"object"==typeof t){const e=t.toString();return"[object CanvasPattern]"===e||"[object CanvasGradient]"===e}return!1}function Qt(t){return Jt(t)?t:new Zt(t)}function te(t){return Jt(t)?t:new Zt(t).saturate(.5).darken(.1).hexString()}const ee=["x","y","borderWidth","radius","tension"],ie=["color","borderColor","backgroundColor"];const se=new Map;function ne(t,e,i){return function(t,e){e=e||{};const i=t+JSON.stringify(e);let s=se.get(i);return s||(s=new Intl.NumberFormat(t,e),se.set(i,s)),s}(e,i).format(t)}const oe={values:t=>n(t)?t:""+t,numeric(t,e,i){if(0===t)return"0";const s=this.chart.options.locale;let n,o=t;if(i.length>1){const e=Math.max(Math.abs(i[0].value),Math.abs(i[i.length-1].value));(e<1e-4||e>1e15)&&(n="scientific"),o=function(t,e){let i=e.length>3?e[2].value-e[1].value:e[1].value-e[0].value;Math.abs(i)>=1&&t!==Math.floor(t)&&(i=t-Math.floor(t));return i}(t,i)}const a=z(Math.abs(o)),r=isNaN(a)?1:Math.max(Math.min(-1*Math.floor(a),20),0),l={notation:n,minimumFractionDigits:r,maximumFractionDigits:r};return Object.assign(l,this.options.ticks.format),ne(t,s,l)},logarithmic(t,e,i){if(0===t)return"0";const s=i[e].significand||t/Math.pow(10,Math.floor(z(t)));return[1,2,3,5,10,15].includes(s)||e>.8*i.length?oe.numeric.call(this,t,e,i):""}};var ae={formatters:oe};const re=Object.create(null),le=Object.create(null);function he(t,e){if(!e)return t;const i=e.split(".");for(let e=0,s=i.length;e<s;++e){const s=i[e];t=t[s]||(t[s]=Object.create(null))}return t}function ce(t,e,i){return"string"==typeof e?x(he(t,e),i):x(he(t,""),e)}class de{constructor(t,e){this.animation=void 0,this.backgroundColor="rgba(0,0,0,0.1)",this.borderColor="rgba(0,0,0,0.1)",this.color="#666",this.datasets={},this.devicePixelRatio=t=>t.chart.platform.getDevicePixelRatio(),this.elements={},this.events=["mousemove","mouseout","click","touchstart","touchmove"],this.font={family:"'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",size:12,style:"normal",lineHeight:1.2,weight:null},this.hover={},this.hoverBackgroundColor=(t,e)=>te(e.backgroundColor),this.hoverBorderColor=(t,e)=>te(e.borderColor),this.hoverColor=(t,e)=>te(e.color),this.indexAxis="x",this.interaction={mode:"nearest",intersect:!0,includeInvisible:!1},this.maintainAspectRatio=!0,this.onHover=null,this.onClick=null,this.parsing=!0,this.plugins={},this.responsive=!0,this.scale=void 0,this.scales={},this.showLine=!0,this.drawActiveElementsOnTop=!0,this.describe(t),this.apply(e)}set(t,e){return ce(this,t,e)}get(t){return he(this,t)}describe(t,e){return ce(le,t,e)}override(t,e){return ce(re,t,e)}route(t,e,i,s){const n=he(this,t),a=he(this,i),r="_"+e;Object.defineProperties(n,{[r]:{value:n[e],writable:!0},[e]:{enumerable:!0,get(){const t=this[r],e=a[s];return o(t)?Object.assign({},e,t):l(t,e)},set(t){this[r]=t}}})}apply(t){t.forEach((t=>t(this)))}}var ue=new de({_scriptable:t=>!t.startsWith("on"),_indexable:t=>"events"!==t,hover:{_fallback:"interaction"},interaction:{_scriptable:!1,_indexable:!1}},[function(t){t.set("animation",{delay:void 0,duration:1e3,easing:"easeOutQuart",fn:void 0,from:void 0,loop:void 0,to:void 0,type:void 0}),t.describe("animation",{_fallback:!1,_indexable:!1,_scriptable:t=>"onProgress"!==t&&"onComplete"!==t&&"fn"!==t}),t.set("animations",{colors:{type:"color",properties:ie},numbers:{type:"number",properties:ee}}),t.describe("animations",{_fallback:"animation"}),t.set("transitions",{active:{animation:{duration:400}},resize:{animation:{duration:0}},show:{animations:{colors:{from:"transparent"},visible:{type:"boolean",duration:0}}},hide:{animations:{colors:{to:"transparent"},visible:{type:"boolean",easing:"linear",fn:t=>0|t}}}})},function(t){t.set("layout",{autoPadding:!0,padding:{top:0,right:0,bottom:0,left:0}})},function(t){t.set("scale",{display:!0,offset:!1,reverse:!1,beginAtZero:!1,bounds:"ticks",clip:!0,grace:0,grid:{display:!0,lineWidth:1,drawOnChartArea:!0,drawTicks:!0,tickLength:8,tickWidth:(t,e)=>e.lineWidth,tickColor:(t,e)=>e.color,offset:!1},border:{display:!0,dash:[],dashOffset:0,width:1},title:{display:!1,text:"",padding:{top:4,bottom:4}},ticks:{minRotation:0,maxRotation:50,mirror:!1,textStrokeWidth:0,textStrokeColor:"",padding:3,display:!0,autoSkip:!0,autoSkipPadding:3,labelOffset:0,callback:ae.formatters.values,minor:{},major:{},align:"center",crossAlign:"near",showLabelBackdrop:!1,backdropColor:"rgba(255, 255, 255, 0.75)",backdropPadding:2}}),t.route("scale.ticks","color","","color"),t.route("scale.grid","color","","borderColor"),t.route("scale.border","color","","borderColor"),t.route("scale.title","color","","color"),t.describe("scale",{_fallback:!1,_scriptable:t=>!t.startsWith("before")&&!t.startsWith("after")&&"callback"!==t&&"parser"!==t,_indexable:t=>"borderDash"!==t&&"tickBorderDash"!==t&&"dash"!==t}),t.describe("scales",{_fallback:"scale"}),t.describe("scale.ticks",{_scriptable:t=>"backdropPadding"!==t&&"callback"!==t,_indexable:t=>"backdropPadding"!==t})}]);function fe(){return"undefined"!=typeof window&&"undefined"!=typeof document}function ge(t){let e=t.parentNode;return e&&"[object ShadowRoot]"===e.toString()&&(e=e.host),e}function pe(t,e,i){let s;return"string"==typeof t?(s=parseInt(t,10),-1!==t.indexOf("%")&&(s=s/100*e.parentNode[i])):s=t,s}const me=t=>t.ownerDocument.defaultView.getComputedStyle(t,null);function xe(t,e){return me(t).getPropertyValue(e)}const be=["top","right","bottom","left"];function _e(t,e,i){const s={};i=i?"-"+i:"";for(let n=0;n<4;n++){const o=be[n];s[o]=parseFloat(t[e+"-"+o+i])||0}return s.width=s.left+s.right,s.height=s.top+s.bottom,s}const ye=(t,e,i)=>(t>0||e>0)&&(!i||!i.shadowRoot);function ve(t,e){if("native"in t)return t;const{canvas:i,currentDevicePixelRatio:s}=e,n=me(i),o="border-box"===n.boxSizing,a=_e(n,"padding"),r=_e(n,"border","width"),{x:l,y:h,box:c}=function(t,e){const i=t.touches,s=i&&i.length?i[0]:t,{offsetX:n,offsetY:o}=s;let a,r,l=!1;if(ye(n,o,t.target))a=n,r=o;else{const t=e.getBoundingClientRect();a=s.clientX-t.left,r=s.clientY-t.top,l=!0}return{x:a,y:r,box:l}}(t,i),d=a.left+(c&&r.left),u=a.top+(c&&r.top);let{width:f,height:g}=e;return o&&(f-=a.width+r.width,g-=a.height+r.height),{x:Math.round((l-d)/f*i.width/s),y:Math.round((h-u)/g*i.height/s)}}const Me=t=>Math.round(10*t)/10;function we(t,e,i,s){const n=me(t),o=_e(n,"margin"),a=pe(n.maxWidth,t,"clientWidth")||T,r=pe(n.maxHeight,t,"clientHeight")||T,l=function(t,e,i){let s,n;if(void 0===e||void 0===i){const o=t&&ge(t);if(o){const t=o.getBoundingClientRect(),a=me(o),r=_e(a,"border","width"),l=_e(a,"padding");e=t.width-l.width-r.width,i=t.height-l.height-r.height,s=pe(a.maxWidth,o,"clientWidth"),n=pe(a.maxHeight,o,"clientHeight")}else e=t.clientWidth,i=t.clientHeight}return{width:e,height:i,maxWidth:s||T,maxHeight:n||T}}(t,e,i);let{width:h,height:c}=l;if("content-box"===n.boxSizing){const t=_e(n,"border","width"),e=_e(n,"padding");h-=e.width+t.width,c-=e.height+t.height}h=Math.max(0,h-o.width),c=Math.max(0,s?h/s:c-o.height),h=Me(Math.min(h,a,l.maxWidth)),c=Me(Math.min(c,r,l.maxHeight)),h&&!c&&(c=Me(h/2));return(void 0!==e||void 0!==i)&&s&&l.height&&c>l.height&&(c=l.height,h=Me(Math.floor(c*s))),{width:h,height:c}}function ke(t,e,i){const s=e||1,n=Math.floor(t.height*s),o=Math.floor(t.width*s);t.height=Math.floor(t.height),t.width=Math.floor(t.width);const a=t.canvas;return a.style&&(i||!a.style.height&&!a.style.width)&&(a.style.height=`${t.height}px`,a.style.width=`${t.width}px`),(t.currentDevicePixelRatio!==s||a.height!==n||a.width!==o)&&(t.currentDevicePixelRatio=s,a.height=n,a.width=o,t.ctx.setTransform(s,0,0,s,0,0),!0)}const Se=function(){let t=!1;try{const e={get passive(){return t=!0,!1}};fe()&&(window.addEventListener("test",null,e),window.removeEventListener("test",null,e))}catch(t){}return t}();function Pe(t,e){const i=xe(t,e),s=i&&i.match(/^(\d+)(\.\d+)?px$/);return s?+s[1]:void 0}function De(t){return!t||s(t.size)||s(t.family)?null:(t.style?t.style+" ":"")+(t.weight?t.weight+" ":"")+t.size+"px "+t.family}function Ce(t,e,i,s,n){let o=e[n];return o||(o=e[n]=t.measureText(n).width,i.push(n)),o>s&&(s=o),s}function Oe(t,e,i,s){let o=(s=s||{}).data=s.data||{},a=s.garbageCollect=s.garbageCollect||[];s.font!==e&&(o=s.data={},a=s.garbageCollect=[],s.font=e),t.save(),t.font=e;let r=0;const l=i.length;let h,c,d,u,f;for(h=0;h<l;h++)if(u=i[h],null==u||n(u)){if(n(u))for(c=0,d=u.length;c<d;c++)f=u[c],null==f||n(f)||(r=Ce(t,o,a,r,f))}else r=Ce(t,o,a,r,u);t.restore();const g=a.length/2;if(g>i.length){for(h=0;h<g;h++)delete o[a[h]];a.splice(0,g)}return r}function Ae(t,e,i){const s=t.currentDevicePixelRatio,n=0!==i?Math.max(i/2,.5):0;return Math.round((e-n)*s)/s+n}function Te(t,e){(e||t)&&((e=e||t.getContext("2d")).save(),e.resetTransform(),e.clearRect(0,0,t.width,t.height),e.restore())}function Le(t,e,i,s){Ee(t,e,i,s,null)}function Ee(t,e,i,s,n){let o,a,r,l,h,c,d,u;const f=e.pointStyle,g=e.rotation,p=e.radius;let m=(g||0)*L;if(f&&"object"==typeof f&&(o=f.toString(),"[object HTMLImageElement]"===o||"[object HTMLCanvasElement]"===o))return t.save(),t.translate(i,s),t.rotate(m),t.drawImage(f,-f.width/2,-f.height/2,f.width,f.height),void t.restore();if(!(isNaN(p)||p<=0)){switch(t.beginPath(),f){default:n?t.ellipse(i,s,n/2,p,0,0,O):t.arc(i,s,p,0,O),t.closePath();break;case"triangle":c=n?n/2:p,t.moveTo(i+Math.sin(m)*c,s-Math.cos(m)*p),m+=I,t.lineTo(i+Math.sin(m)*c,s-Math.cos(m)*p),m+=I,t.lineTo(i+Math.sin(m)*c,s-Math.cos(m)*p),t.closePath();break;case"rectRounded":h=.516*p,l=p-h,a=Math.cos(m+R)*l,d=Math.cos(m+R)*(n?n/2-h:l),r=Math.sin(m+R)*l,u=Math.sin(m+R)*(n?n/2-h:l),t.arc(i-d,s-r,h,m-C,m-E),t.arc(i+u,s-a,h,m-E,m),t.arc(i+d,s+r,h,m,m+E),t.arc(i-u,s+a,h,m+E,m+C),t.closePath();break;case"rect":if(!g){l=Math.SQRT1_2*p,c=n?n/2:l,t.rect(i-c,s-l,2*c,2*l);break}m+=R;case"rectRot":d=Math.cos(m)*(n?n/2:p),a=Math.cos(m)*p,r=Math.sin(m)*p,u=Math.sin(m)*(n?n/2:p),t.moveTo(i-d,s-r),t.lineTo(i+u,s-a),t.lineTo(i+d,s+r),t.lineTo(i-u,s+a),t.closePath();break;case"crossRot":m+=R;case"cross":d=Math.cos(m)*(n?n/2:p),a=Math.cos(m)*p,r=Math.sin(m)*p,u=Math.sin(m)*(n?n/2:p),t.moveTo(i-d,s-r),t.lineTo(i+d,s+r),t.moveTo(i+u,s-a),t.lineTo(i-u,s+a);break;case"star":d=Math.cos(m)*(n?n/2:p),a=Math.cos(m)*p,r=Math.sin(m)*p,u=Math.sin(m)*(n?n/2:p),t.moveTo(i-d,s-r),t.lineTo(i+d,s+r),t.moveTo(i+u,s-a),t.lineTo(i-u,s+a),m+=R,d=Math.cos(m)*(n?n/2:p),a=Math.cos(m)*p,r=Math.sin(m)*p,u=Math.sin(m)*(n?n/2:p),t.moveTo(i-d,s-r),t.lineTo(i+d,s+r),t.moveTo(i+u,s-a),t.lineTo(i-u,s+a);break;case"line":a=n?n/2:Math.cos(m)*p,r=Math.sin(m)*p,t.moveTo(i-a,s-r),t.lineTo(i+a,s+r);break;case"dash":t.moveTo(i,s),t.lineTo(i+Math.cos(m)*(n?n/2:p),s+Math.sin(m)*p);break;case!1:t.closePath()}t.fill(),e.borderWidth>0&&t.stroke()}}function Re(t,e,i){return i=i||.5,!e||t&&t.x>e.left-i&&t.x<e.right+i&&t.y>e.top-i&&t.y<e.bottom+i}function Ie(t,e){t.save(),t.beginPath(),t.rect(e.left,e.top,e.right-e.left,e.bottom-e.top),t.clip()}function ze(t){t.restore()}function Fe(t,e,i,s,n){if(!e)return t.lineTo(i.x,i.y);if("middle"===n){const s=(e.x+i.x)/2;t.lineTo(s,e.y),t.lineTo(s,i.y)}else"after"===n!=!!s?t.lineTo(e.x,i.y):t.lineTo(i.x,e.y);t.lineTo(i.x,i.y)}function Ve(t,e,i,s){if(!e)return t.lineTo(i.x,i.y);t.bezierCurveTo(s?e.cp1x:e.cp2x,s?e.cp1y:e.cp2y,s?i.cp2x:i.cp1x,s?i.cp2y:i.cp1y,i.x,i.y)}function Be(t,e,i,s,n){if(n.strikethrough||n.underline){const o=t.measureText(s),a=e-o.actualBoundingBoxLeft,r=e+o.actualBoundingBoxRight,l=i-o.actualBoundingBoxAscent,h=i+o.actualBoundingBoxDescent,c=n.strikethrough?(l+h)/2:h;t.strokeStyle=t.fillStyle,t.beginPath(),t.lineWidth=n.decorationWidth||2,t.moveTo(a,c),t.lineTo(r,c),t.stroke()}}function We(t,e){const i=t.fillStyle;t.fillStyle=e.color,t.fillRect(e.left,e.top,e.width,e.height),t.fillStyle=i}function Ne(t,e,i,o,a,r={}){const l=n(e)?e:[e],h=r.strokeWidth>0&&""!==r.strokeColor;let c,d;for(t.save(),t.font=a.string,function(t,e){e.translation&&t.translate(e.translation[0],e.translation[1]),s(e.rotation)||t.rotate(e.rotation),e.color&&(t.fillStyle=e.color),e.textAlign&&(t.textAlign=e.textAlign),e.textBaseline&&(t.textBaseline=e.textBaseline)}(t,r),c=0;c<l.length;++c)d=l[c],r.backdrop&&We(t,r.backdrop),h&&(r.strokeColor&&(t.strokeStyle=r.strokeColor),s(r.strokeWidth)||(t.lineWidth=r.strokeWidth),t.strokeText(d,i,o,r.maxWidth)),t.fillText(d,i,o,r.maxWidth),Be(t,i,o,d,r),o+=Number(a.lineHeight);t.restore()}function He(t,e){const{x:i,y:s,w:n,h:o,radius:a}=e;t.arc(i+a.topLeft,s+a.topLeft,a.topLeft,1.5*C,C,!0),t.lineTo(i,s+o-a.bottomLeft),t.arc(i+a.bottomLeft,s+o-a.bottomLeft,a.bottomLeft,C,E,!0),t.lineTo(i+n-a.bottomRight,s+o),t.arc(i+n-a.bottomRight,s+o-a.bottomRight,a.bottomRight,E,0,!0),t.lineTo(i+n,s+a.topRight),t.arc(i+n-a.topRight,s+a.topRight,a.topRight,0,-E,!0),t.lineTo(i+a.topLeft,s)}function je(t,e=[""],i,s,n=(()=>t[0])){const o=i||t;void 0===s&&(s=ti("_fallback",t));const a={[Symbol.toStringTag]:"Object",_cacheable:!0,_scopes:t,_rootScopes:o,_fallback:s,_getTarget:n,override:i=>je([i,...t],e,o,s)};return new Proxy(a,{deleteProperty:(e,i)=>(delete e[i],delete e._keys,delete t[0][i],!0),get:(i,s)=>qe(i,s,(()=>function(t,e,i,s){let n;for(const o of e)if(n=ti(Ue(o,t),i),void 0!==n)return Xe(t,n)?Je(i,s,t,n):n}(s,e,t,i))),getOwnPropertyDescriptor:(t,e)=>Reflect.getOwnPropertyDescriptor(t._scopes[0],e),getPrototypeOf:()=>Reflect.getPrototypeOf(t[0]),has:(t,e)=>ei(t).includes(e),ownKeys:t=>ei(t),set(t,e,i){const s=t._storage||(t._storage=n());return t[e]=s[e]=i,delete t._keys,!0}})}function $e(t,e,i,s){const a={_cacheable:!1,_proxy:t,_context:e,_subProxy:i,_stack:new Set,_descriptors:Ye(t,s),setContext:e=>$e(t,e,i,s),override:n=>$e(t.override(n),e,i,s)};return new Proxy(a,{deleteProperty:(e,i)=>(delete e[i],delete t[i],!0),get:(t,e,i)=>qe(t,e,(()=>function(t,e,i){const{_proxy:s,_context:a,_subProxy:r,_descriptors:l}=t;let h=s[e];S(h)&&l.isScriptable(e)&&(h=function(t,e,i,s){const{_proxy:n,_context:o,_subProxy:a,_stack:r}=i;if(r.has(t))throw new Error("Recursion detected: "+Array.from(r).join("->")+"->"+t);r.add(t);let l=e(o,a||s);r.delete(t),Xe(t,l)&&(l=Je(n._scopes,n,t,l));return l}(e,h,t,i));n(h)&&h.length&&(h=function(t,e,i,s){const{_proxy:n,_context:a,_subProxy:r,_descriptors:l}=i;if(void 0!==a.index&&s(t))return e[a.index%e.length];if(o(e[0])){const i=e,s=n._scopes.filter((t=>t!==i));e=[];for(const o of i){const i=Je(s,n,t,o);e.push($e(i,a,r&&r[t],l))}}return e}(e,h,t,l.isIndexable));Xe(e,h)&&(h=$e(h,a,r&&r[e],l));return h}(t,e,i))),getOwnPropertyDescriptor:(e,i)=>e._descriptors.allKeys?Reflect.has(t,i)?{enumerable:!0,configurable:!0}:void 0:Reflect.getOwnPropertyDescriptor(t,i),getPrototypeOf:()=>Reflect.getPrototypeOf(t),has:(e,i)=>Reflect.has(t,i),ownKeys:()=>Reflect.ownKeys(t),set:(e,i,s)=>(t[i]=s,delete e[i],!0)})}function Ye(t,e={scriptable:!0,indexable:!0}){const{_scriptable:i=e.scriptable,_indexable:s=e.indexable,_allKeys:n=e.allKeys}=t;return{allKeys:n,scriptable:i,indexable:s,isScriptable:S(i)?i:()=>i,isIndexable:S(s)?s:()=>s}}const Ue=(t,e)=>t?t+w(e):e,Xe=(t,e)=>o(e)&&"adapters"!==t&&(null===Object.getPrototypeOf(e)||e.constructor===Object);function qe(t,e,i){if(Object.prototype.hasOwnProperty.call(t,e)||"constructor"===e)return t[e];const s=i();return t[e]=s,s}function Ke(t,e,i){return S(t)?t(e,i):t}const Ge=(t,e)=>!0===t?e:"string"==typeof t?M(e,t):void 0;function Ze(t,e,i,s,n){for(const o of e){const e=Ge(i,o);if(e){t.add(e);const o=Ke(e._fallback,i,n);if(void 0!==o&&o!==i&&o!==s)return o}else if(!1===e&&void 0!==s&&i!==s)return null}return!1}function Je(t,e,i,s){const a=e._rootScopes,r=Ke(e._fallback,i,s),l=[...t,...a],h=new Set;h.add(s);let c=Qe(h,l,i,r||i,s);return null!==c&&((void 0===r||r===i||(c=Qe(h,l,r,c,s),null!==c))&&je(Array.from(h),[""],a,r,(()=>function(t,e,i){const s=t._getTarget();e in s||(s[e]={});const a=s[e];if(n(a)&&o(i))return i;return a||{}}(e,i,s))))}function Qe(t,e,i,s,n){for(;i;)i=Ze(t,e,i,s,n);return i}function ti(t,e){for(const i of e){if(!i)continue;const e=i[t];if(void 0!==e)return e}}function ei(t){let e=t._keys;return e||(e=t._keys=function(t){const e=new Set;for(const i of t)for(const t of Object.keys(i).filter((t=>!t.startsWith("_"))))e.add(t);return Array.from(e)}(t._scopes)),e}function ii(t,e,i,s){const{iScale:n}=t,{key:o="r"}=this._parsing,a=new Array(s);let r,l,h,c;for(r=0,l=s;r<l;++r)h=r+i,c=e[h],a[r]={r:n.parse(M(c,o),h)};return a}const si=Number.EPSILON||1e-14,ni=(t,e)=>e<t.length&&!t[e].skip&&t[e],oi=t=>"x"===t?"y":"x";function ai(t,e,i,s){const n=t.skip?e:t,o=e,a=i.skip?e:i,r=q(o,n),l=q(a,o);let h=r/(r+l),c=l/(r+l);h=isNaN(h)?0:h,c=isNaN(c)?0:c;const d=s*h,u=s*c;return{previous:{x:o.x-d*(a.x-n.x),y:o.y-d*(a.y-n.y)},next:{x:o.x+u*(a.x-n.x),y:o.y+u*(a.y-n.y)}}}function ri(t,e="x"){const i=oi(e),s=t.length,n=Array(s).fill(0),o=Array(s);let a,r,l,h=ni(t,0);for(a=0;a<s;++a)if(r=l,l=h,h=ni(t,a+1),l){if(h){const t=h[e]-l[e];n[a]=0!==t?(h[i]-l[i])/t:0}o[a]=r?h?F(n[a-1])!==F(n[a])?0:(n[a-1]+n[a])/2:n[a-1]:n[a]}!function(t,e,i){const s=t.length;let n,o,a,r,l,h=ni(t,0);for(let c=0;c<s-1;++c)l=h,h=ni(t,c+1),l&&h&&(V(e[c],0,si)?i[c]=i[c+1]=0:(n=i[c]/e[c],o=i[c+1]/e[c],r=Math.pow(n,2)+Math.pow(o,2),r<=9||(a=3/Math.sqrt(r),i[c]=n*a*e[c],i[c+1]=o*a*e[c])))}(t,n,o),function(t,e,i="x"){const s=oi(i),n=t.length;let o,a,r,l=ni(t,0);for(let h=0;h<n;++h){if(a=r,r=l,l=ni(t,h+1),!r)continue;const n=r[i],c=r[s];a&&(o=(n-a[i])/3,r[`cp1${i}`]=n-o,r[`cp1${s}`]=c-o*e[h]),l&&(o=(l[i]-n)/3,r[`cp2${i}`]=n+o,r[`cp2${s}`]=c+o*e[h])}}(t,o,e)}function li(t,e,i){return Math.max(Math.min(t,i),e)}function hi(t,e,i,s,n){let o,a,r,l;if(e.spanGaps&&(t=t.filter((t=>!t.skip))),"monotone"===e.cubicInterpolationMode)ri(t,n);else{let i=s?t[t.length-1]:t[0];for(o=0,a=t.length;o<a;++o)r=t[o],l=ai(i,r,t[Math.min(o+1,a-(s?0:1))%a],e.tension),r.cp1x=l.previous.x,r.cp1y=l.previous.y,r.cp2x=l.next.x,r.cp2y=l.next.y,i=r}e.capBezierPoints&&function(t,e){let i,s,n,o,a,r=Re(t[0],e);for(i=0,s=t.length;i<s;++i)a=o,o=r,r=i<s-1&&Re(t[i+1],e),o&&(n=t[i],a&&(n.cp1x=li(n.cp1x,e.left,e.right),n.cp1y=li(n.cp1y,e.top,e.bottom)),r&&(n.cp2x=li(n.cp2x,e.left,e.right),n.cp2y=li(n.cp2y,e.top,e.bottom)))}(t,i)}const ci=t=>0===t||1===t,di=(t,e,i)=>-Math.pow(2,10*(t-=1))*Math.sin((t-e)*O/i),ui=(t,e,i)=>Math.pow(2,-10*t)*Math.sin((t-e)*O/i)+1,fi={linear:t=>t,easeInQuad:t=>t*t,easeOutQuad:t=>-t*(t-2),easeInOutQuad:t=>(t/=.5)<1?.5*t*t:-.5*(--t*(t-2)-1),easeInCubic:t=>t*t*t,easeOutCubic:t=>(t-=1)*t*t+1,easeInOutCubic:t=>(t/=.5)<1?.5*t*t*t:.5*((t-=2)*t*t+2),easeInQuart:t=>t*t*t*t,easeOutQuart:t=>-((t-=1)*t*t*t-1),easeInOutQuart:t=>(t/=.5)<1?.5*t*t*t*t:-.5*((t-=2)*t*t*t-2),easeInQuint:t=>t*t*t*t*t,easeOutQuint:t=>(t-=1)*t*t*t*t+1,easeInOutQuint:t=>(t/=.5)<1?.5*t*t*t*t*t:.5*((t-=2)*t*t*t*t+2),easeInSine:t=>1-Math.cos(t*E),easeOutSine:t=>Math.sin(t*E),easeInOutSine:t=>-.5*(Math.cos(C*t)-1),easeInExpo:t=>0===t?0:Math.pow(2,10*(t-1)),easeOutExpo:t=>1===t?1:1-Math.pow(2,-10*t),easeInOutExpo:t=>ci(t)?t:t<.5?.5*Math.pow(2,10*(2*t-1)):.5*(2-Math.pow(2,-10*(2*t-1))),easeInCirc:t=>t>=1?t:-(Math.sqrt(1-t*t)-1),easeOutCirc:t=>Math.sqrt(1-(t-=1)*t),easeInOutCirc:t=>(t/=.5)<1?-.5*(Math.sqrt(1-t*t)-1):.5*(Math.sqrt(1-(t-=2)*t)+1),easeInElastic:t=>ci(t)?t:di(t,.075,.3),easeOutElastic:t=>ci(t)?t:ui(t,.075,.3),easeInOutElastic(t){const e=.1125;return ci(t)?t:t<.5?.5*di(2*t,e,.45):.5+.5*ui(2*t-1,e,.45)},easeInBack(t){const e=1.70158;return t*t*((e+1)*t-e)},easeOutBack(t){const e=1.70158;return(t-=1)*t*((e+1)*t+e)+1},easeInOutBack(t){let e=1.70158;return(t/=.5)<1?t*t*((1+(e*=1.525))*t-e)*.5:.5*((t-=2)*t*((1+(e*=1.525))*t+e)+2)},easeInBounce:t=>1-fi.easeOutBounce(1-t),easeOutBounce(t){const e=7.5625,i=2.75;return t<1/i?e*t*t:t<2/i?e*(t-=1.5/i)*t+.75:t<2.5/i?e*(t-=2.25/i)*t+.9375:e*(t-=2.625/i)*t+.984375},easeInOutBounce:t=>t<.5?.5*fi.easeInBounce(2*t):.5*fi.easeOutBounce(2*t-1)+.5};function gi(t,e,i,s){return{x:t.x+i*(e.x-t.x),y:t.y+i*(e.y-t.y)}}function pi(t,e,i,s){return{x:t.x+i*(e.x-t.x),y:"middle"===s?i<.5?t.y:e.y:"after"===s?i<1?t.y:e.y:i>0?e.y:t.y}}function mi(t,e,i,s){const n={x:t.cp2x,y:t.cp2y},o={x:e.cp1x,y:e.cp1y},a=gi(t,n,i),r=gi(n,o,i),l=gi(o,e,i),h=gi(a,r,i),c=gi(r,l,i);return gi(h,c,i)}const xi=/^(normal|(\d+(?:\.\d+)?)(px|em|%)?)$/,bi=/^(normal|italic|initial|inherit|unset|(oblique( -?[0-9]?[0-9]deg)?))$/;function _i(t,e){const i=(""+t).match(xi);if(!i||"normal"===i[1])return 1.2*e;switch(t=+i[2],i[3]){case"px":return t;case"%":t/=100}return e*t}const yi=t=>+t||0;function vi(t,e){const i={},s=o(e),n=s?Object.keys(e):e,a=o(t)?s?i=>l(t[i],t[e[i]]):e=>t[e]:()=>t;for(const t of n)i[t]=yi(a(t));return i}function Mi(t){return vi(t,{top:"y",right:"x",bottom:"y",left:"x"})}function wi(t){return vi(t,["topLeft","topRight","bottomLeft","bottomRight"])}function ki(t){const e=Mi(t);return e.width=e.left+e.right,e.height=e.top+e.bottom,e}function Si(t,e){t=t||{},e=e||ue.font;let i=l(t.size,e.size);"string"==typeof i&&(i=parseInt(i,10));let s=l(t.style,e.style);s&&!(""+s).match(bi)&&(console.warn('Invalid font style specified: "'+s+'"'),s=void 0);const n={family:l(t.family,e.family),lineHeight:_i(l(t.lineHeight,e.lineHeight),i),size:i,style:s,weight:l(t.weight,e.weight),string:""};return n.string=De(n),n}function Pi(t,e,i,s){let o,a,r,l=!0;for(o=0,a=t.length;o<a;++o)if(r=t[o],void 0!==r&&(void 0!==e&&"function"==typeof r&&(r=r(e),l=!1),void 0!==i&&n(r)&&(r=r[i%r.length],l=!1),void 0!==r))return s&&!l&&(s.cacheable=!1),r}function Di(t,e,i){const{min:s,max:n}=t,o=c(e,(n-s)/2),a=(t,e)=>i&&0===t?0:t+e;return{min:a(s,-Math.abs(o)),max:a(n,o)}}function Ci(t,e){return Object.assign(Object.create(t),e)}function Oi(t,e,i){return t?function(t,e){return{x:i=>t+t+e-i,setWidth(t){e=t},textAlign:t=>"center"===t?t:"right"===t?"left":"right",xPlus:(t,e)=>t-e,leftForLtr:(t,e)=>t-e}}(e,i):{x:t=>t,setWidth(t){},textAlign:t=>t,xPlus:(t,e)=>t+e,leftForLtr:(t,e)=>t}}function Ai(t,e){let i,s;"ltr"!==e&&"rtl"!==e||(i=t.canvas.style,s=[i.getPropertyValue("direction"),i.getPropertyPriority("direction")],i.setProperty("direction",e,"important"),t.prevTextDirection=s)}function Ti(t,e){void 0!==e&&(delete t.prevTextDirection,t.canvas.style.setProperty("direction",e[0],e[1]))}function Li(t){return"angle"===t?{between:Z,compare:K,normalize:G}:{between:tt,compare:(t,e)=>t-e,normalize:t=>t}}function Ei({start:t,end:e,count:i,loop:s,style:n}){return{start:t%i,end:e%i,loop:s&&(e-t+1)%i==0,style:n}}function Ri(t,e,i){if(!i)return[t];const{property:s,start:n,end:o}=i,a=e.length,{compare:r,between:l,normalize:h}=Li(s),{start:c,end:d,loop:u,style:f}=function(t,e,i){const{property:s,start:n,end:o}=i,{between:a,normalize:r}=Li(s),l=e.length;let h,c,{start:d,end:u,loop:f}=t;if(f){for(d+=l,u+=l,h=0,c=l;h<c&&a(r(e[d%l][s]),n,o);++h)d--,u--;d%=l,u%=l}return u<d&&(u+=l),{start:d,end:u,loop:f,style:t.style}}(t,e,i),g=[];let p,m,x,b=!1,_=null;const y=()=>b||l(n,x,p)&&0!==r(n,x),v=()=>!b||0===r(o,p)||l(o,x,p);for(let t=c,i=c;t<=d;++t)m=e[t%a],m.skip||(p=h(m[s]),p!==x&&(b=l(p,n,o),null===_&&y()&&(_=0===r(p,n)?t:i),null!==_&&v()&&(g.push(Ei({start:_,end:t,loop:u,count:a,style:f})),_=null),i=t,x=p));return null!==_&&g.push(Ei({start:_,end:d,loop:u,count:a,style:f})),g}function Ii(t,e){const i=[],s=t.segments;for(let n=0;n<s.length;n++){const o=Ri(s[n],t.points,e);o.length&&i.push(...o)}return i}function zi(t,e){const i=t.points,s=t.options.spanGaps,n=i.length;if(!n)return[];const o=!!t._loop,{start:a,end:r}=function(t,e,i,s){let n=0,o=e-1;if(i&&!s)for(;n<e&&!t[n].skip;)n++;for(;n<e&&t[n].skip;)n++;for(n%=e,i&&(o+=n);o>n&&t[o%e].skip;)o--;return o%=e,{start:n,end:o}}(i,n,o,s);if(!0===s)return Fi(t,[{start:a,end:r,loop:o}],i,e);return Fi(t,function(t,e,i,s){const n=t.length,o=[];let a,r=e,l=t[e];for(a=e+1;a<=i;++a){const i=t[a%n];i.skip||i.stop?l.skip||(s=!1,o.push({start:e%n,end:(a-1)%n,loop:s}),e=r=i.stop?a:null):(r=a,l.skip&&(e=a)),l=i}return null!==r&&o.push({start:e%n,end:r%n,loop:s}),o}(i,a,r<a?r+n:r,!!t._fullLoop&&0===a&&r===n-1),i,e)}function Fi(t,e,i,s){return s&&s.setContext&&i?function(t,e,i,s){const n=t._chart.getContext(),o=Vi(t.options),{_datasetIndex:a,options:{spanGaps:r}}=t,l=i.length,h=[];let c=o,d=e[0].start,u=d;function f(t,e,s,n){const o=r?-1:1;if(t!==e){for(t+=l;i[t%l].skip;)t-=o;for(;i[e%l].skip;)e+=o;t%l!=e%l&&(h.push({start:t%l,end:e%l,loop:s,style:n}),c=n,d=e%l)}}for(const t of e){d=r?d:t.start;let e,o=i[d%l];for(u=d+1;u<=t.end;u++){const r=i[u%l];e=Vi(s.setContext(Ci(n,{type:"segment",p0:o,p1:r,p0DataIndex:(u-1)%l,p1DataIndex:u%l,datasetIndex:a}))),Bi(e,c)&&f(d,u-1,t.loop,c),o=r,c=e}d<u-1&&f(d,u-1,t.loop,c)}return h}(t,e,i,s):e}function Vi(t){return{backgroundColor:t.backgroundColor,borderCapStyle:t.borderCapStyle,borderDash:t.borderDash,borderDashOffset:t.borderDashOffset,borderJoinStyle:t.borderJoinStyle,borderWidth:t.borderWidth,borderColor:t.borderColor}}function Bi(t,e){if(!e)return!1;const i=[],s=function(t,e){return Jt(e)?(i.includes(e)||i.push(e),i.indexOf(e)):e};return JSON.stringify(t,s)!==JSON.stringify(e,s)}var Wi=Object.freeze({__proto__:null,HALF_PI:E,INFINITY:T,PI:C,PITAU:A,QUARTER_PI:R,RAD_PER_DEG:L,TAU:O,TWO_THIRDS_PI:I,_addGrace:Di,_alignPixel:Ae,_alignStartEnd:ft,_angleBetween:Z,_angleDiff:K,_arrayUnique:lt,_attachContext:$e,_bezierCurveTo:Ve,_bezierInterpolation:mi,_boundSegment:Ri,_boundSegments:Ii,_capitalize:w,_computeSegments:zi,_createResolver:je,_decimalPlaces:U,_deprecated:function(t,e,i,s){void 0!==e&&console.warn(t+': "'+i+'" is deprecated. Please use "'+s+'" instead')},_descriptors:Ye,_elementsEqual:f,_factorize:W,_filterBetween:nt,_getParentNode:ge,_getStartAndCountOfVisiblePoints:pt,_int16Range:Q,_isBetween:tt,_isClickEvent:D,_isDomSupported:fe,_isPointInArea:Re,_limitValue:J,_longestText:Oe,_lookup:et,_lookupByKey:it,_measureText:Ce,_merger:m,_mergerIf:_,_normalizeAngle:G,_parseObjectDataRadialScale:ii,_pointInLine:gi,_readValueToProps:vi,_rlookupByKey:st,_scaleRangesChanged:mt,_setMinAndMaxByKey:j,_splitKey:v,_steppedInterpolation:pi,_steppedLineTo:Fe,_textX:gt,_toLeftRightCenter:ut,_updateBezierControlPoints:hi,addRoundedRectPath:He,almostEquals:V,almostWhole:H,callback:d,clearCanvas:Te,clipArea:Ie,clone:g,color:Qt,createContext:Ci,debounce:dt,defined:k,distanceBetweenPoints:q,drawPoint:Le,drawPointLegend:Ee,each:u,easingEffects:fi,finiteOrDefault:r,fontString:function(t,e,i){return e+" "+t+"px "+i},formatNumber:ne,getAngleFromPoint:X,getHoverColor:te,getMaximumSize:we,getRelativePosition:ve,getRtlAdapter:Oi,getStyle:xe,isArray:n,isFinite:a,isFunction:S,isNullOrUndef:s,isNumber:N,isObject:o,isPatternOrGradient:Jt,listenArrayEvents:at,log10:z,merge:x,mergeIf:b,niceNum:B,noop:e,overrideTextDirection:Ai,readUsedSize:Pe,renderText:Ne,requestAnimFrame:ht,resolve:Pi,resolveObjectKey:M,restoreTextDirection:Ti,retinaScale:ke,setsEqual:P,sign:F,splineCurve:ai,splineCurveMonotone:ri,supportsEventListenerOptions:Se,throttled:ct,toDegrees:Y,toDimension:c,toFont:Si,toFontString:De,toLineHeight:_i,toPadding:ki,toPercentage:h,toRadians:$,toTRBL:Mi,toTRBLCorners:wi,uid:i,unclipArea:ze,unlistenArrayEvents:rt,valueOrDefault:l});function Ni(t,e,i,n){const{controller:o,data:a,_sorted:r}=t,l=o._cachedMeta.iScale,h=t.dataset&&t.dataset.options?t.dataset.options.spanGaps:null;if(l&&e===l.axis&&"r"!==e&&r&&a.length){const r=l._reversePixels?st:it;if(!n){const n=r(a,e,i);if(h){const{vScale:e}=o._cachedMeta,{_parsed:i}=t,a=i.slice(0,n.lo+1).reverse().findIndex((t=>!s(t[e.axis])));n.lo-=Math.max(0,a);const r=i.slice(n.hi).findIndex((t=>!s(t[e.axis])));n.hi+=Math.max(0,r)}return n}if(o._sharedOptions){const t=a[0],s="function"==typeof t.getRange&&t.getRange(e);if(s){const t=r(a,e,i-s),n=r(a,e,i+s);return{lo:t.lo,hi:n.hi}}}}return{lo:0,hi:a.length-1}}function Hi(t,e,i,s,n){const o=t.getSortedVisibleDatasetMetas(),a=i[e];for(let t=0,i=o.length;t<i;++t){const{index:i,data:r}=o[t],{lo:l,hi:h}=Ni(o[t],e,a,n);for(let t=l;t<=h;++t){const e=r[t];e.skip||s(e,i,t)}}}function ji(t,e,i,s,n){const o=[];if(!n&&!t.isPointInArea(e))return o;return Hi(t,i,e,(function(i,a,r){(n||Re(i,t.chartArea,0))&&i.inRange(e.x,e.y,s)&&o.push({element:i,datasetIndex:a,index:r})}),!0),o}function $i(t,e,i,s,n,o){let a=[];const r=function(t){const e=-1!==t.indexOf("x"),i=-1!==t.indexOf("y");return function(t,s){const n=e?Math.abs(t.x-s.x):0,o=i?Math.abs(t.y-s.y):0;return Math.sqrt(Math.pow(n,2)+Math.pow(o,2))}}(i);let l=Number.POSITIVE_INFINITY;return Hi(t,i,e,(function(i,h,c){const d=i.inRange(e.x,e.y,n);if(s&&!d)return;const u=i.getCenterPoint(n);if(!(!!o||t.isPointInArea(u))&&!d)return;const f=r(e,u);f<l?(a=[{element:i,datasetIndex:h,index:c}],l=f):f===l&&a.push({element:i,datasetIndex:h,index:c})})),a}function Yi(t,e,i,s,n,o){return o||t.isPointInArea(e)?"r"!==i||s?$i(t,e,i,s,n,o):function(t,e,i,s){let n=[];return Hi(t,i,e,(function(t,i,o){const{startAngle:a,endAngle:r}=t.getProps(["startAngle","endAngle"],s),{angle:l}=X(t,{x:e.x,y:e.y});Z(l,a,r)&&n.push({element:t,datasetIndex:i,index:o})})),n}(t,e,i,n):[]}function Ui(t,e,i,s,n){const o=[],a="x"===i?"inXRange":"inYRange";let r=!1;return Hi(t,i,e,((t,s,l)=>{t[a]&&t[a](e[i],n)&&(o.push({element:t,datasetIndex:s,index:l}),r=r||t.inRange(e.x,e.y,n))})),s&&!r?[]:o}var Xi={evaluateInteractionItems:Hi,modes:{index(t,e,i,s){const n=ve(e,t),o=i.axis||"x",a=i.includeInvisible||!1,r=i.intersect?ji(t,n,o,s,a):Yi(t,n,o,!1,s,a),l=[];return r.length?(t.getSortedVisibleDatasetMetas().forEach((t=>{const e=r[0].index,i=t.data[e];i&&!i.skip&&l.push({element:i,datasetIndex:t.index,index:e})})),l):[]},dataset(t,e,i,s){const n=ve(e,t),o=i.axis||"xy",a=i.includeInvisible||!1;let r=i.intersect?ji(t,n,o,s,a):Yi(t,n,o,!1,s,a);if(r.length>0){const e=r[0].datasetIndex,i=t.getDatasetMeta(e).data;r=[];for(let t=0;t<i.length;++t)r.push({element:i[t],datasetIndex:e,index:t})}return r},point:(t,e,i,s)=>ji(t,ve(e,t),i.axis||"xy",s,i.includeInvisible||!1),nearest(t,e,i,s){const n=ve(e,t),o=i.axis||"xy",a=i.includeInvisible||!1;return Yi(t,n,o,i.intersect,s,a)},x:(t,e,i,s)=>Ui(t,ve(e,t),"x",i.intersect,s),y:(t,e,i,s)=>Ui(t,ve(e,t),"y",i.intersect,s)}};const qi=["left","top","right","bottom"];function Ki(t,e){return t.filter((t=>t.pos===e))}function Gi(t,e){return t.filter((t=>-1===qi.indexOf(t.pos)&&t.box.axis===e))}function Zi(t,e){return t.sort(((t,i)=>{const s=e?i:t,n=e?t:i;return s.weight===n.weight?s.index-n.index:s.weight-n.weight}))}function Ji(t,e){const i=function(t){const e={};for(const i of t){const{stack:t,pos:s,stackWeight:n}=i;if(!t||!qi.includes(s))continue;const o=e[t]||(e[t]={count:0,placed:0,weight:0,size:0});o.count++,o.weight+=n}return e}(t),{vBoxMaxWidth:s,hBoxMaxHeight:n}=e;let o,a,r;for(o=0,a=t.length;o<a;++o){r=t[o];const{fullSize:a}=r.box,l=i[r.stack],h=l&&r.stackWeight/l.weight;r.horizontal?(r.width=h?h*s:a&&e.availableWidth,r.height=n):(r.width=s,r.height=h?h*n:a&&e.availableHeight)}return i}function Qi(t,e,i,s){return Math.max(t[i],e[i])+Math.max(t[s],e[s])}function ts(t,e){t.top=Math.max(t.top,e.top),t.left=Math.max(t.left,e.left),t.bottom=Math.max(t.bottom,e.bottom),t.right=Math.max(t.right,e.right)}function es(t,e,i,s){const{pos:n,box:a}=i,r=t.maxPadding;if(!o(n)){i.size&&(t[n]-=i.size);const e=s[i.stack]||{size:0,count:1};e.size=Math.max(e.size,i.horizontal?a.height:a.width),i.size=e.size/e.count,t[n]+=i.size}a.getPadding&&ts(r,a.getPadding());const l=Math.max(0,e.outerWidth-Qi(r,t,"left","right")),h=Math.max(0,e.outerHeight-Qi(r,t,"top","bottom")),c=l!==t.w,d=h!==t.h;return t.w=l,t.h=h,i.horizontal?{same:c,other:d}:{same:d,other:c}}function is(t,e){const i=e.maxPadding;function s(t){const s={left:0,top:0,right:0,bottom:0};return t.forEach((t=>{s[t]=Math.max(e[t],i[t])})),s}return s(t?["left","right"]:["top","bottom"])}function ss(t,e,i,s){const n=[];let o,a,r,l,h,c;for(o=0,a=t.length,h=0;o<a;++o){r=t[o],l=r.box,l.update(r.width||e.w,r.height||e.h,is(r.horizontal,e));const{same:a,other:d}=es(e,i,r,s);h|=a&&n.length,c=c||d,l.fullSize||n.push(r)}return h&&ss(n,e,i,s)||c}function ns(t,e,i,s,n){t.top=i,t.left=e,t.right=e+s,t.bottom=i+n,t.width=s,t.height=n}function os(t,e,i,s){const n=i.padding;let{x:o,y:a}=e;for(const r of t){const t=r.box,l=s[r.stack]||{count:1,placed:0,weight:1},h=r.stackWeight/l.weight||1;if(r.horizontal){const s=e.w*h,o=l.size||t.height;k(l.start)&&(a=l.start),t.fullSize?ns(t,n.left,a,i.outerWidth-n.right-n.left,o):ns(t,e.left+l.placed,a,s,o),l.start=a,l.placed+=s,a=t.bottom}else{const s=e.h*h,a=l.size||t.width;k(l.start)&&(o=l.start),t.fullSize?ns(t,o,n.top,a,i.outerHeight-n.bottom-n.top):ns(t,o,e.top+l.placed,a,s),l.start=o,l.placed+=s,o=t.right}}e.x=o,e.y=a}var as={addBox(t,e){t.boxes||(t.boxes=[]),e.fullSize=e.fullSize||!1,e.position=e.position||"top",e.weight=e.weight||0,e._layers=e._layers||function(){return[{z:0,draw(t){e.draw(t)}}]},t.boxes.push(e)},removeBox(t,e){const i=t.boxes?t.boxes.indexOf(e):-1;-1!==i&&t.boxes.splice(i,1)},configure(t,e,i){e.fullSize=i.fullSize,e.position=i.position,e.weight=i.weight},update(t,e,i,s){if(!t)return;const n=ki(t.options.layout.padding),o=Math.max(e-n.width,0),a=Math.max(i-n.height,0),r=function(t){const e=function(t){const e=[];let i,s,n,o,a,r;for(i=0,s=(t||[]).length;i<s;++i)n=t[i],({position:o,options:{stack:a,stackWeight:r=1}}=n),e.push({index:i,box:n,pos:o,horizontal:n.isHorizontal(),weight:n.weight,stack:a&&o+a,stackWeight:r});return e}(t),i=Zi(e.filter((t=>t.box.fullSize)),!0),s=Zi(Ki(e,"left"),!0),n=Zi(Ki(e,"right")),o=Zi(Ki(e,"top"),!0),a=Zi(Ki(e,"bottom")),r=Gi(e,"x"),l=Gi(e,"y");return{fullSize:i,leftAndTop:s.concat(o),rightAndBottom:n.concat(l).concat(a).concat(r),chartArea:Ki(e,"chartArea"),vertical:s.concat(n).concat(l),horizontal:o.concat(a).concat(r)}}(t.boxes),l=r.vertical,h=r.horizontal;u(t.boxes,(t=>{"function"==typeof t.beforeLayout&&t.beforeLayout()}));const c=l.reduce(((t,e)=>e.box.options&&!1===e.box.options.display?t:t+1),0)||1,d=Object.freeze({outerWidth:e,outerHeight:i,padding:n,availableWidth:o,availableHeight:a,vBoxMaxWidth:o/2/c,hBoxMaxHeight:a/2}),f=Object.assign({},n);ts(f,ki(s));const g=Object.assign({maxPadding:f,w:o,h:a,x:n.left,y:n.top},n),p=Ji(l.concat(h),d);ss(r.fullSize,g,d,p),ss(l,g,d,p),ss(h,g,d,p)&&ss(l,g,d,p),function(t){const e=t.maxPadding;function i(i){const s=Math.max(e[i]-t[i],0);return t[i]+=s,s}t.y+=i("top"),t.x+=i("left"),i("right"),i("bottom")}(g),os(r.leftAndTop,g,d,p),g.x+=g.w,g.y+=g.h,os(r.rightAndBottom,g,d,p),t.chartArea={left:g.left,top:g.top,right:g.left+g.w,bottom:g.top+g.h,height:g.h,width:g.w},u(r.chartArea,(e=>{const i=e.box;Object.assign(i,t.chartArea),i.update(g.w,g.h,{left:0,top:0,right:0,bottom:0})}))}};class rs{acquireContext(t,e){}releaseContext(t){return!1}addEventListener(t,e,i){}removeEventListener(t,e,i){}getDevicePixelRatio(){return 1}getMaximumSize(t,e,i,s){return e=Math.max(0,e||t.width),i=i||t.height,{width:e,height:Math.max(0,s?Math.floor(e/s):i)}}isAttached(t){return!0}updateConfig(t){}}class ls extends rs{acquireContext(t){return t&&t.getContext&&t.getContext("2d")||null}updateConfig(t){t.options.animation=!1}}const hs="$chartjs",cs={touchstart:"mousedown",touchmove:"mousemove",touchend:"mouseup",pointerenter:"mouseenter",pointerdown:"mousedown",pointermove:"mousemove",pointerup:"mouseup",pointerleave:"mouseout",pointerout:"mouseout"},ds=t=>null===t||""===t;const us=!!Se&&{passive:!0};function fs(t,e,i){t&&t.canvas&&t.canvas.removeEventListener(e,i,us)}function gs(t,e){for(const i of t)if(i===e||i.contains(e))return!0}function ps(t,e,i){const s=t.canvas,n=new MutationObserver((t=>{let e=!1;for(const i of t)e=e||gs(i.addedNodes,s),e=e&&!gs(i.removedNodes,s);e&&i()}));return n.observe(document,{childList:!0,subtree:!0}),n}function ms(t,e,i){const s=t.canvas,n=new MutationObserver((t=>{let e=!1;for(const i of t)e=e||gs(i.removedNodes,s),e=e&&!gs(i.addedNodes,s);e&&i()}));return n.observe(document,{childList:!0,subtree:!0}),n}const xs=new Map;let bs=0;function _s(){const t=window.devicePixelRatio;t!==bs&&(bs=t,xs.forEach(((e,i)=>{i.currentDevicePixelRatio!==t&&e()})))}function ys(t,e,i){const s=t.canvas,n=s&&ge(s);if(!n)return;const o=ct(((t,e)=>{const s=n.clientWidth;i(t,e),s<n.clientWidth&&i()}),window),a=new ResizeObserver((t=>{const e=t[0],i=e.contentRect.width,s=e.contentRect.height;0===i&&0===s||o(i,s)}));return a.observe(n),function(t,e){xs.size||window.addEventListener("resize",_s),xs.set(t,e)}(t,o),a}function vs(t,e,i){i&&i.disconnect(),"resize"===e&&function(t){xs.delete(t),xs.size||window.removeEventListener("resize",_s)}(t)}function Ms(t,e,i){const s=t.canvas,n=ct((e=>{null!==t.ctx&&i(function(t,e){const i=cs[t.type]||t.type,{x:s,y:n}=ve(t,e);return{type:i,chart:e,native:t,x:void 0!==s?s:null,y:void 0!==n?n:null}}(e,t))}),t);return function(t,e,i){t&&t.addEventListener(e,i,us)}(s,e,n),n}class ws extends rs{acquireContext(t,e){const i=t&&t.getContext&&t.getContext("2d");return i&&i.canvas===t?(function(t,e){const i=t.style,s=t.getAttribute("height"),n=t.getAttribute("width");if(t[hs]={initial:{height:s,width:n,style:{display:i.display,height:i.height,width:i.width}}},i.display=i.display||"block",i.boxSizing=i.boxSizing||"border-box",ds(n)){const e=Pe(t,"width");void 0!==e&&(t.width=e)}if(ds(s))if(""===t.style.height)t.height=t.width/(e||2);else{const e=Pe(t,"height");void 0!==e&&(t.height=e)}}(t,e),i):null}releaseContext(t){const e=t.canvas;if(!e[hs])return!1;const i=e[hs].initial;["height","width"].forEach((t=>{const n=i[t];s(n)?e.removeAttribute(t):e.setAttribute(t,n)}));const n=i.style||{};return Object.keys(n).forEach((t=>{e.style[t]=n[t]})),e.width=e.width,delete e[hs],!0}addEventListener(t,e,i){this.removeEventListener(t,e);const s=t.$proxies||(t.$proxies={}),n={attach:ps,detach:ms,resize:ys}[e]||Ms;s[e]=n(t,e,i)}removeEventListener(t,e){const i=t.$proxies||(t.$proxies={}),s=i[e];if(!s)return;({attach:vs,detach:vs,resize:vs}[e]||fs)(t,e,s),i[e]=void 0}getDevicePixelRatio(){return window.devicePixelRatio}getMaximumSize(t,e,i,s){return we(t,e,i,s)}isAttached(t){const e=t&&ge(t);return!(!e||!e.isConnected)}}function ks(t){return!fe()||"undefined"!=typeof OffscreenCanvas&&t instanceof OffscreenCanvas?ls:ws}var Ss=Object.freeze({__proto__:null,BasePlatform:rs,BasicPlatform:ls,DomPlatform:ws,_detectPlatform:ks});const Ps="transparent",Ds={boolean:(t,e,i)=>i>.5?e:t,color(t,e,i){const s=Qt(t||Ps),n=s.valid&&Qt(e||Ps);return n&&n.valid?n.mix(s,i).hexString():e},number:(t,e,i)=>t+(e-t)*i};class Cs{constructor(t,e,i,s){const n=e[i];s=Pi([t.to,s,n,t.from]);const o=Pi([t.from,n,s]);this._active=!0,this._fn=t.fn||Ds[t.type||typeof o],this._easing=fi[t.easing]||fi.linear,this._start=Math.floor(Date.now()+(t.delay||0)),this._duration=this._total=Math.floor(t.duration),this._loop=!!t.loop,this._target=e,this._prop=i,this._from=o,this._to=s,this._promises=void 0}active(){return this._active}update(t,e,i){if(this._active){this._notify(!1);const s=this._target[this._prop],n=i-this._start,o=this._duration-n;this._start=i,this._duration=Math.floor(Math.max(o,t.duration)),this._total+=n,this._loop=!!t.loop,this._to=Pi([t.to,e,s,t.from]),this._from=Pi([t.from,s,e])}}cancel(){this._active&&(this.tick(Date.now()),this._active=!1,this._notify(!1))}tick(t){const e=t-this._start,i=this._duration,s=this._prop,n=this._from,o=this._loop,a=this._to;let r;if(this._active=n!==a&&(o||e<i),!this._active)return this._target[s]=a,void this._notify(!0);e<0?this._target[s]=n:(r=e/i%2,r=o&&r>1?2-r:r,r=this._easing(Math.min(1,Math.max(0,r))),this._target[s]=this._fn(n,a,r))}wait(){const t=this._promises||(this._promises=[]);return new Promise(((e,i)=>{t.push({res:e,rej:i})}))}_notify(t){const e=t?"res":"rej",i=this._promises||[];for(let t=0;t<i.length;t++)i[t][e]()}}class Os{constructor(t,e){this._chart=t,this._properties=new Map,this.configure(e)}configure(t){if(!o(t))return;const e=Object.keys(ue.animation),i=this._properties;Object.getOwnPropertyNames(t).forEach((s=>{const a=t[s];if(!o(a))return;const r={};for(const t of e)r[t]=a[t];(n(a.properties)&&a.properties||[s]).forEach((t=>{t!==s&&i.has(t)||i.set(t,r)}))}))}_animateOptions(t,e){const i=e.options,s=function(t,e){if(!e)return;let i=t.options;if(!i)return void(t.options=e);i.$shared&&(t.options=i=Object.assign({},i,{$shared:!1,$animations:{}}));return i}(t,i);if(!s)return[];const n=this._createAnimations(s,i);return i.$shared&&function(t,e){const i=[],s=Object.keys(e);for(let e=0;e<s.length;e++){const n=t[s[e]];n&&n.active()&&i.push(n.wait())}return Promise.all(i)}(t.options.$animations,i).then((()=>{t.options=i}),(()=>{})),n}_createAnimations(t,e){const i=this._properties,s=[],n=t.$animations||(t.$animations={}),o=Object.keys(e),a=Date.now();let r;for(r=o.length-1;r>=0;--r){const l=o[r];if("$"===l.charAt(0))continue;if("options"===l){s.push(...this._animateOptions(t,e));continue}const h=e[l];let c=n[l];const d=i.get(l);if(c){if(d&&c.active()){c.update(d,h,a);continue}c.cancel()}d&&d.duration?(n[l]=c=new Cs(d,t,l,h),s.push(c)):t[l]=h}return s}update(t,e){if(0===this._properties.size)return void Object.assign(t,e);const i=this._createAnimations(t,e);return i.length?(bt.add(this._chart,i),!0):void 0}}function As(t,e){const i=t&&t.options||{},s=i.reverse,n=void 0===i.min?e:0,o=void 0===i.max?e:0;return{start:s?o:n,end:s?n:o}}function Ts(t,e){const i=[],s=t._getSortedDatasetMetas(e);let n,o;for(n=0,o=s.length;n<o;++n)i.push(s[n].index);return i}function Ls(t,e,i,s={}){const n=t.keys,o="single"===s.mode;let r,l,h,c;if(null===e)return;let d=!1;for(r=0,l=n.length;r<l;++r){if(h=+n[r],h===i){if(d=!0,s.all)continue;break}c=t.values[h],a(c)&&(o||0===e||F(e)===F(c))&&(e+=c)}return d||s.all?e:0}function Es(t,e){const i=t&&t.options.stacked;return i||void 0===i&&void 0!==e.stack}function Rs(t,e,i){const s=t[e]||(t[e]={});return s[i]||(s[i]={})}function Is(t,e,i,s){for(const n of e.getMatchingVisibleMetas(s).reverse()){const e=t[n.index];if(i&&e>0||!i&&e<0)return n.index}return null}function zs(t,e){const{chart:i,_cachedMeta:s}=t,n=i._stacks||(i._stacks={}),{iScale:o,vScale:a,index:r}=s,l=o.axis,h=a.axis,c=function(t,e,i){return`${t.id}.${e.id}.${i.stack||i.type}`}(o,a,s),d=e.length;let u;for(let t=0;t<d;++t){const i=e[t],{[l]:o,[h]:d}=i;u=(i._stacks||(i._stacks={}))[h]=Rs(n,c,o),u[r]=d,u._top=Is(u,a,!0,s.type),u._bottom=Is(u,a,!1,s.type);(u._visualValues||(u._visualValues={}))[r]=d}}function Fs(t,e){const i=t.scales;return Object.keys(i).filter((t=>i[t].axis===e)).shift()}function Vs(t,e){const i=t.controller.index,s=t.vScale&&t.vScale.axis;if(s){e=e||t._parsed;for(const t of e){const e=t._stacks;if(!e||void 0===e[s]||void 0===e[s][i])return;delete e[s][i],void 0!==e[s]._visualValues&&void 0!==e[s]._visualValues[i]&&delete e[s]._visualValues[i]}}}const Bs=t=>"reset"===t||"none"===t,Ws=(t,e)=>e?t:Object.assign({},t);class Ns{static defaults={};static datasetElementType=null;static dataElementType=null;constructor(t,e){this.chart=t,this._ctx=t.ctx,this.index=e,this._cachedDataOpts={},this._cachedMeta=this.getMeta(),this._type=this._cachedMeta.type,this.options=void 0,this._parsing=!1,this._data=void 0,this._objectData=void 0,this._sharedOptions=void 0,this._drawStart=void 0,this._drawCount=void 0,this.enableOptionSharing=!1,this.supportsDecimation=!1,this.$context=void 0,this._syncList=[],this.datasetElementType=new.target.datasetElementType,this.dataElementType=new.target.dataElementType,this.initialize()}initialize(){const t=this._cachedMeta;this.configure(),this.linkScales(),t._stacked=Es(t.vScale,t),this.addElements(),this.options.fill&&!this.chart.isPluginEnabled("filler")&&console.warn("Tried to use the 'fill' option without the 'Filler' plugin enabled. Please import and register the 'Filler' plugin and make sure it is not disabled in the options")}updateIndex(t){this.index!==t&&Vs(this._cachedMeta),this.index=t}linkScales(){const t=this.chart,e=this._cachedMeta,i=this.getDataset(),s=(t,e,i,s)=>"x"===t?e:"r"===t?s:i,n=e.xAxisID=l(i.xAxisID,Fs(t,"x")),o=e.yAxisID=l(i.yAxisID,Fs(t,"y")),a=e.rAxisID=l(i.rAxisID,Fs(t,"r")),r=e.indexAxis,h=e.iAxisID=s(r,n,o,a),c=e.vAxisID=s(r,o,n,a);e.xScale=this.getScaleForId(n),e.yScale=this.getScaleForId(o),e.rScale=this.getScaleForId(a),e.iScale=this.getScaleForId(h),e.vScale=this.getScaleForId(c)}getDataset(){return this.chart.data.datasets[this.index]}getMeta(){return this.chart.getDatasetMeta(this.index)}getScaleForId(t){return this.chart.scales[t]}_getOtherScale(t){const e=this._cachedMeta;return t===e.iScale?e.vScale:e.iScale}reset(){this._update("reset")}_destroy(){const t=this._cachedMeta;this._data&&rt(this._data,this),t._stacked&&Vs(t)}_dataCheck(){const t=this.getDataset(),e=t.data||(t.data=[]),i=this._data;if(o(e)){const t=this._cachedMeta;this._data=function(t,e){const{iScale:i,vScale:s}=e,n="x"===i.axis?"x":"y",o="x"===s.axis?"x":"y",a=Object.keys(t),r=new Array(a.length);let l,h,c;for(l=0,h=a.length;l<h;++l)c=a[l],r[l]={[n]:c,[o]:t[c]};return r}(e,t)}else if(i!==e){if(i){rt(i,this);const t=this._cachedMeta;Vs(t),t._parsed=[]}e&&Object.isExtensible(e)&&at(e,this),this._syncList=[],this._data=e}}addElements(){const t=this._cachedMeta;this._dataCheck(),this.datasetElementType&&(t.dataset=new this.datasetElementType)}buildOrUpdateElements(t){const e=this._cachedMeta,i=this.getDataset();let s=!1;this._dataCheck();const n=e._stacked;e._stacked=Es(e.vScale,e),e.stack!==i.stack&&(s=!0,Vs(e),e.stack=i.stack),this._resyncElements(t),(s||n!==e._stacked)&&(zs(this,e._parsed),e._stacked=Es(e.vScale,e))}configure(){const t=this.chart.config,e=t.datasetScopeKeys(this._type),i=t.getOptionScopes(this.getDataset(),e,!0);this.options=t.createResolver(i,this.getContext()),this._parsing=this.options.parsing,this._cachedDataOpts={}}parse(t,e){const{_cachedMeta:i,_data:s}=this,{iScale:a,_stacked:r}=i,l=a.axis;let h,c,d,u=0===t&&e===s.length||i._sorted,f=t>0&&i._parsed[t-1];if(!1===this._parsing)i._parsed=s,i._sorted=!0,d=s;else{d=n(s[t])?this.parseArrayData(i,s,t,e):o(s[t])?this.parseObjectData(i,s,t,e):this.parsePrimitiveData(i,s,t,e);const a=()=>null===c[l]||f&&c[l]<f[l];for(h=0;h<e;++h)i._parsed[h+t]=c=d[h],u&&(a()&&(u=!1),f=c);i._sorted=u}r&&zs(this,d)}parsePrimitiveData(t,e,i,s){const{iScale:n,vScale:o}=t,a=n.axis,r=o.axis,l=n.getLabels(),h=n===o,c=new Array(s);let d,u,f;for(d=0,u=s;d<u;++d)f=d+i,c[d]={[a]:h||n.parse(l[f],f),[r]:o.parse(e[f],f)};return c}parseArrayData(t,e,i,s){const{xScale:n,yScale:o}=t,a=new Array(s);let r,l,h,c;for(r=0,l=s;r<l;++r)h=r+i,c=e[h],a[r]={x:n.parse(c[0],h),y:o.parse(c[1],h)};return a}parseObjectData(t,e,i,s){const{xScale:n,yScale:o}=t,{xAxisKey:a="x",yAxisKey:r="y"}=this._parsing,l=new Array(s);let h,c,d,u;for(h=0,c=s;h<c;++h)d=h+i,u=e[d],l[h]={x:n.parse(M(u,a),d),y:o.parse(M(u,r),d)};return l}getParsed(t){return this._cachedMeta._parsed[t]}getDataElement(t){return this._cachedMeta.data[t]}applyStack(t,e,i){const s=this.chart,n=this._cachedMeta,o=e[t.axis];return Ls({keys:Ts(s,!0),values:e._stacks[t.axis]._visualValues},o,n.index,{mode:i})}updateRangeFromParsed(t,e,i,s){const n=i[e.axis];let o=null===n?NaN:n;const a=s&&i._stacks[e.axis];s&&a&&(s.values=a,o=Ls(s,n,this._cachedMeta.index)),t.min=Math.min(t.min,o),t.max=Math.max(t.max,o)}getMinMax(t,e){const i=this._cachedMeta,s=i._parsed,n=i._sorted&&t===i.iScale,o=s.length,r=this._getOtherScale(t),l=((t,e,i)=>t&&!e.hidden&&e._stacked&&{keys:Ts(i,!0),values:null})(e,i,this.chart),h={min:Number.POSITIVE_INFINITY,max:Number.NEGATIVE_INFINITY},{min:c,max:d}=function(t){const{min:e,max:i,minDefined:s,maxDefined:n}=t.getUserBounds();return{min:s?e:Number.NEGATIVE_INFINITY,max:n?i:Number.POSITIVE_INFINITY}}(r);let u,f;function g(){f=s[u];const e=f[r.axis];return!a(f[t.axis])||c>e||d<e}for(u=0;u<o&&(g()||(this.updateRangeFromParsed(h,t,f,l),!n));++u);if(n)for(u=o-1;u>=0;--u)if(!g()){this.updateRangeFromParsed(h,t,f,l);break}return h}getAllParsedValues(t){const e=this._cachedMeta._parsed,i=[];let s,n,o;for(s=0,n=e.length;s<n;++s)o=e[s][t.axis],a(o)&&i.push(o);return i}getMaxOverflow(){return!1}getLabelAndValue(t){const e=this._cachedMeta,i=e.iScale,s=e.vScale,n=this.getParsed(t);return{label:i?""+i.getLabelForValue(n[i.axis]):"",value:s?""+s.getLabelForValue(n[s.axis]):""}}_update(t){const e=this._cachedMeta;this.update(t||"default"),e._clip=function(t){let e,i,s,n;return o(t)?(e=t.top,i=t.right,s=t.bottom,n=t.left):e=i=s=n=t,{top:e,right:i,bottom:s,left:n,disabled:!1===t}}(l(this.options.clip,function(t,e,i){if(!1===i)return!1;const s=As(t,i),n=As(e,i);return{top:n.end,right:s.end,bottom:n.start,left:s.start}}(e.xScale,e.yScale,this.getMaxOverflow())))}update(t){}draw(){const t=this._ctx,e=this.chart,i=this._cachedMeta,s=i.data||[],n=e.chartArea,o=[],a=this._drawStart||0,r=this._drawCount||s.length-a,l=this.options.drawActiveElementsOnTop;let h;for(i.dataset&&i.dataset.draw(t,n,a,r),h=a;h<a+r;++h){const e=s[h];e.hidden||(e.active&&l?o.push(e):e.draw(t,n))}for(h=0;h<o.length;++h)o[h].draw(t,n)}getStyle(t,e){const i=e?"active":"default";return void 0===t&&this._cachedMeta.dataset?this.resolveDatasetElementOptions(i):this.resolveDataElementOptions(t||0,i)}getContext(t,e,i){const s=this.getDataset();let n;if(t>=0&&t<this._cachedMeta.data.length){const e=this._cachedMeta.data[t];n=e.$context||(e.$context=function(t,e,i){return Ci(t,{active:!1,dataIndex:e,parsed:void 0,raw:void 0,element:i,index:e,mode:"default",type:"data"})}(this.getContext(),t,e)),n.parsed=this.getParsed(t),n.raw=s.data[t],n.index=n.dataIndex=t}else n=this.$context||(this.$context=function(t,e){return Ci(t,{active:!1,dataset:void 0,datasetIndex:e,index:e,mode:"default",type:"dataset"})}(this.chart.getContext(),this.index)),n.dataset=s,n.index=n.datasetIndex=this.index;return n.active=!!e,n.mode=i,n}resolveDatasetElementOptions(t){return this._resolveElementOptions(this.datasetElementType.id,t)}resolveDataElementOptions(t,e){return this._resolveElementOptions(this.dataElementType.id,e,t)}_resolveElementOptions(t,e="default",i){const s="active"===e,n=this._cachedDataOpts,o=t+"-"+e,a=n[o],r=this.enableOptionSharing&&k(i);if(a)return Ws(a,r);const l=this.chart.config,h=l.datasetElementScopeKeys(this._type,t),c=s?[`${t}Hover`,"hover",t,""]:[t,""],d=l.getOptionScopes(this.getDataset(),h),u=Object.keys(ue.elements[t]),f=l.resolveNamedOptions(d,u,(()=>this.getContext(i,s,e)),c);return f.$shared&&(f.$shared=r,n[o]=Object.freeze(Ws(f,r))),f}_resolveAnimations(t,e,i){const s=this.chart,n=this._cachedDataOpts,o=`animation-${e}`,a=n[o];if(a)return a;let r;if(!1!==s.options.animation){const s=this.chart.config,n=s.datasetAnimationScopeKeys(this._type,e),o=s.getOptionScopes(this.getDataset(),n);r=s.createResolver(o,this.getContext(t,i,e))}const l=new Os(s,r&&r.animations);return r&&r._cacheable&&(n[o]=Object.freeze(l)),l}getSharedOptions(t){if(t.$shared)return this._sharedOptions||(this._sharedOptions=Object.assign({},t))}includeOptions(t,e){return!e||Bs(t)||this.chart._animationsDisabled}_getSharedOptions(t,e){const i=this.resolveDataElementOptions(t,e),s=this._sharedOptions,n=this.getSharedOptions(i),o=this.includeOptions(e,n)||n!==s;return this.updateSharedOptions(n,e,i),{sharedOptions:n,includeOptions:o}}updateElement(t,e,i,s){Bs(s)?Object.assign(t,i):this._resolveAnimations(e,s).update(t,i)}updateSharedOptions(t,e,i){t&&!Bs(e)&&this._resolveAnimations(void 0,e).update(t,i)}_setStyle(t,e,i,s){t.active=s;const n=this.getStyle(e,s);this._resolveAnimations(e,i,s).update(t,{options:!s&&this.getSharedOptions(n)||n})}removeHoverStyle(t,e,i){this._setStyle(t,i,"active",!1)}setHoverStyle(t,e,i){this._setStyle(t,i,"active",!0)}_removeDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!1)}_setDatasetHoverStyle(){const t=this._cachedMeta.dataset;t&&this._setStyle(t,void 0,"active",!0)}_resyncElements(t){const e=this._data,i=this._cachedMeta.data;for(const[t,e,i]of this._syncList)this[t](e,i);this._syncList=[];const s=i.length,n=e.length,o=Math.min(n,s);o&&this.parse(0,o),n>s?this._insertElements(s,n-s,t):n<s&&this._removeElements(n,s-n)}_insertElements(t,e,i=!0){const s=this._cachedMeta,n=s.data,o=t+e;let a;const r=t=>{for(t.length+=e,a=t.length-1;a>=o;a--)t[a]=t[a-e]};for(r(n),a=t;a<o;++a)n[a]=new this.dataElementType;this._parsing&&r(s._parsed),this.parse(t,e),i&&this.updateElements(n,t,e,"reset")}updateElements(t,e,i,s){}_removeElements(t,e){const i=this._cachedMeta;if(this._parsing){const s=i._parsed.splice(t,e);i._stacked&&Vs(i,s)}i.data.splice(t,e)}_sync(t){if(this._parsing)this._syncList.push(t);else{const[e,i,s]=t;this[e](i,s)}this.chart._dataChanges.push([this.index,...t])}_onDataPush(){const t=arguments.length;this._sync(["_insertElements",this.getDataset().data.length-t,t])}_onDataPop(){this._sync(["_removeElements",this._cachedMeta.data.length-1,1])}_onDataShift(){this._sync(["_removeElements",0,1])}_onDataSplice(t,e){e&&this._sync(["_removeElements",t,e]);const i=arguments.length-2;i&&this._sync(["_insertElements",t,i])}_onDataUnshift(){this._sync(["_insertElements",0,arguments.length])}}class Hs{static defaults={};static defaultRoutes=void 0;x;y;active=!1;options;$animations;tooltipPosition(t){const{x:e,y:i}=this.getProps(["x","y"],t);return{x:e,y:i}}hasValue(){return N(this.x)&&N(this.y)}getProps(t,e){const i=this.$animations;if(!e||!i)return this;const s={};return t.forEach((t=>{s[t]=i[t]&&i[t].active()?i[t]._to:this[t]})),s}}function js(t,e){const i=t.options.ticks,n=function(t){const e=t.options.offset,i=t._tickSize(),s=t._length/i+(e?0:1),n=t._maxLength/i;return Math.floor(Math.min(s,n))}(t),o=Math.min(i.maxTicksLimit||n,n),a=i.major.enabled?function(t){const e=[];let i,s;for(i=0,s=t.length;i<s;i++)t[i].major&&e.push(i);return e}(e):[],r=a.length,l=a[0],h=a[r-1],c=[];if(r>o)return function(t,e,i,s){let n,o=0,a=i[0];for(s=Math.ceil(s),n=0;n<t.length;n++)n===a&&(e.push(t[n]),o++,a=i[o*s])}(e,c,a,r/o),c;const d=function(t,e,i){const s=function(t){const e=t.length;let i,s;if(e<2)return!1;for(s=t[0],i=1;i<e;++i)if(t[i]-t[i-1]!==s)return!1;return s}(t),n=e.length/i;if(!s)return Math.max(n,1);const o=W(s);for(let t=0,e=o.length-1;t<e;t++){const e=o[t];if(e>n)return e}return Math.max(n,1)}(a,e,o);if(r>0){let t,i;const n=r>1?Math.round((h-l)/(r-1)):null;for($s(e,c,d,s(n)?0:l-n,l),t=0,i=r-1;t<i;t++)$s(e,c,d,a[t],a[t+1]);return $s(e,c,d,h,s(n)?e.length:h+n),c}return $s(e,c,d),c}function $s(t,e,i,s,n){const o=l(s,0),a=Math.min(l(n,t.length),t.length);let r,h,c,d=0;for(i=Math.ceil(i),n&&(r=n-s,i=r/Math.floor(r/i)),c=o;c<0;)d++,c=Math.round(o+d*i);for(h=Math.max(o,0);h<a;h++)h===c&&(e.push(t[h]),d++,c=Math.round(o+d*i))}const Ys=(t,e,i)=>"top"===e||"left"===e?t[e]+i:t[e]-i,Us=(t,e)=>Math.min(e||t,t);function Xs(t,e){const i=[],s=t.length/e,n=t.length;let o=0;for(;o<n;o+=s)i.push(t[Math.floor(o)]);return i}function qs(t,e,i){const s=t.ticks.length,n=Math.min(e,s-1),o=t._startPixel,a=t._endPixel,r=1e-6;let l,h=t.getPixelForTick(n);if(!(i&&(l=1===s?Math.max(h-o,a-h):0===e?(t.getPixelForTick(1)-h)/2:(h-t.getPixelForTick(n-1))/2,h+=n<e?l:-l,h<o-r||h>a+r)))return h}function Ks(t){return t.drawTicks?t.tickLength:0}function Gs(t,e){if(!t.display)return 0;const i=Si(t.font,e),s=ki(t.padding);return(n(t.text)?t.text.length:1)*i.lineHeight+s.height}function Zs(t,e,i){let s=ut(t);return(i&&"right"!==e||!i&&"right"===e)&&(s=(t=>"left"===t?"right":"right"===t?"left":t)(s)),s}class Js extends Hs{constructor(t){super(),this.id=t.id,this.type=t.type,this.options=void 0,this.ctx=t.ctx,this.chart=t.chart,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this._margins={left:0,right:0,top:0,bottom:0},this.maxWidth=void 0,this.maxHeight=void 0,this.paddingTop=void 0,this.paddingBottom=void 0,this.paddingLeft=void 0,this.paddingRight=void 0,this.axis=void 0,this.labelRotation=void 0,this.min=void 0,this.max=void 0,this._range=void 0,this.ticks=[],this._gridLineItems=null,this._labelItems=null,this._labelSizes=null,this._length=0,this._maxLength=0,this._longestTextCache={},this._startPixel=void 0,this._endPixel=void 0,this._reversePixels=!1,this._userMax=void 0,this._userMin=void 0,this._suggestedMax=void 0,this._suggestedMin=void 0,this._ticksLength=0,this._borderValue=0,this._cache={},this._dataLimitsCached=!1,this.$context=void 0}init(t){this.options=t.setContext(this.getContext()),this.axis=t.axis,this._userMin=this.parse(t.min),this._userMax=this.parse(t.max),this._suggestedMin=this.parse(t.suggestedMin),this._suggestedMax=this.parse(t.suggestedMax)}parse(t,e){return t}getUserBounds(){let{_userMin:t,_userMax:e,_suggestedMin:i,_suggestedMax:s}=this;return t=r(t,Number.POSITIVE_INFINITY),e=r(e,Number.NEGATIVE_INFINITY),i=r(i,Number.POSITIVE_INFINITY),s=r(s,Number.NEGATIVE_INFINITY),{min:r(t,i),max:r(e,s),minDefined:a(t),maxDefined:a(e)}}getMinMax(t){let e,{min:i,max:s,minDefined:n,maxDefined:o}=this.getUserBounds();if(n&&o)return{min:i,max:s};const a=this.getMatchingVisibleMetas();for(let r=0,l=a.length;r<l;++r)e=a[r].controller.getMinMax(this,t),n||(i=Math.min(i,e.min)),o||(s=Math.max(s,e.max));return i=o&&i>s?s:i,s=n&&i>s?i:s,{min:r(i,r(s,i)),max:r(s,r(i,s))}}getPadding(){return{left:this.paddingLeft||0,top:this.paddingTop||0,right:this.paddingRight||0,bottom:this.paddingBottom||0}}getTicks(){return this.ticks}getLabels(){const t=this.chart.data;return this.options.labels||(this.isHorizontal()?t.xLabels:t.yLabels)||t.labels||[]}getLabelItems(t=this.chart.chartArea){return this._labelItems||(this._labelItems=this._computeLabelItems(t))}beforeLayout(){this._cache={},this._dataLimitsCached=!1}beforeUpdate(){d(this.options.beforeUpdate,[this])}update(t,e,i){const{beginAtZero:s,grace:n,ticks:o}=this.options,a=o.sampleSize;this.beforeUpdate(),this.maxWidth=t,this.maxHeight=e,this._margins=i=Object.assign({left:0,right:0,top:0,bottom:0},i),this.ticks=null,this._labelSizes=null,this._gridLineItems=null,this._labelItems=null,this.beforeSetDimensions(),this.setDimensions(),this.afterSetDimensions(),this._maxLength=this.isHorizontal()?this.width+i.left+i.right:this.height+i.top+i.bottom,this._dataLimitsCached||(this.beforeDataLimits(),this.determineDataLimits(),this.afterDataLimits(),this._range=Di(this,n,s),this._dataLimitsCached=!0),this.beforeBuildTicks(),this.ticks=this.buildTicks()||[],this.afterBuildTicks();const r=a<this.ticks.length;this._convertTicksToLabels(r?Xs(this.ticks,a):this.ticks),this.configure(),this.beforeCalculateLabelRotation(),this.calculateLabelRotation(),this.afterCalculateLabelRotation(),o.display&&(o.autoSkip||"auto"===o.source)&&(this.ticks=js(this,this.ticks),this._labelSizes=null,this.afterAutoSkip()),r&&this._convertTicksToLabels(this.ticks),this.beforeFit(),this.fit(),this.afterFit(),this.afterUpdate()}configure(){let t,e,i=this.options.reverse;this.isHorizontal()?(t=this.left,e=this.right):(t=this.top,e=this.bottom,i=!i),this._startPixel=t,this._endPixel=e,this._reversePixels=i,this._length=e-t,this._alignToPixels=this.options.alignToPixels}afterUpdate(){d(this.options.afterUpdate,[this])}beforeSetDimensions(){d(this.options.beforeSetDimensions,[this])}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=0,this.right=this.width):(this.height=this.maxHeight,this.top=0,this.bottom=this.height),this.paddingLeft=0,this.paddingTop=0,this.paddingRight=0,this.paddingBottom=0}afterSetDimensions(){d(this.options.afterSetDimensions,[this])}_callHooks(t){this.chart.notifyPlugins(t,this.getContext()),d(this.options[t],[this])}beforeDataLimits(){this._callHooks("beforeDataLimits")}determineDataLimits(){}afterDataLimits(){this._callHooks("afterDataLimits")}beforeBuildTicks(){this._callHooks("beforeBuildTicks")}buildTicks(){return[]}afterBuildTicks(){this._callHooks("afterBuildTicks")}beforeTickToLabelConversion(){d(this.options.beforeTickToLabelConversion,[this])}generateTickLabels(t){const e=this.options.ticks;let i,s,n;for(i=0,s=t.length;i<s;i++)n=t[i],n.label=d(e.callback,[n.value,i,t],this)}afterTickToLabelConversion(){d(this.options.afterTickToLabelConversion,[this])}beforeCalculateLabelRotation(){d(this.options.beforeCalculateLabelRotation,[this])}calculateLabelRotation(){const t=this.options,e=t.ticks,i=Us(this.ticks.length,t.ticks.maxTicksLimit),s=e.minRotation||0,n=e.maxRotation;let o,a,r,l=s;if(!this._isVisible()||!e.display||s>=n||i<=1||!this.isHorizontal())return void(this.labelRotation=s);const h=this._getLabelSizes(),c=h.widest.width,d=h.highest.height,u=J(this.chart.width-c,0,this.maxWidth);o=t.offset?this.maxWidth/i:u/(i-1),c+6>o&&(o=u/(i-(t.offset?.5:1)),a=this.maxHeight-Ks(t.grid)-e.padding-Gs(t.title,this.chart.options.font),r=Math.sqrt(c*c+d*d),l=Y(Math.min(Math.asin(J((h.highest.height+6)/o,-1,1)),Math.asin(J(a/r,-1,1))-Math.asin(J(d/r,-1,1)))),l=Math.max(s,Math.min(n,l))),this.labelRotation=l}afterCalculateLabelRotation(){d(this.options.afterCalculateLabelRotation,[this])}afterAutoSkip(){}beforeFit(){d(this.options.beforeFit,[this])}fit(){const t={width:0,height:0},{chart:e,options:{ticks:i,title:s,grid:n}}=this,o=this._isVisible(),a=this.isHorizontal();if(o){const o=Gs(s,e.options.font);if(a?(t.width=this.maxWidth,t.height=Ks(n)+o):(t.height=this.maxHeight,t.width=Ks(n)+o),i.display&&this.ticks.length){const{first:e,last:s,widest:n,highest:o}=this._getLabelSizes(),r=2*i.padding,l=$(this.labelRotation),h=Math.cos(l),c=Math.sin(l);if(a){const e=i.mirror?0:c*n.width+h*o.height;t.height=Math.min(this.maxHeight,t.height+e+r)}else{const e=i.mirror?0:h*n.width+c*o.height;t.width=Math.min(this.maxWidth,t.width+e+r)}this._calculatePadding(e,s,c,h)}}this._handleMargins(),a?(this.width=this._length=e.width-this._margins.left-this._margins.right,this.height=t.height):(this.width=t.width,this.height=this._length=e.height-this._margins.top-this._margins.bottom)}_calculatePadding(t,e,i,s){const{ticks:{align:n,padding:o},position:a}=this.options,r=0!==this.labelRotation,l="top"!==a&&"x"===this.axis;if(this.isHorizontal()){const a=this.getPixelForTick(0)-this.left,h=this.right-this.getPixelForTick(this.ticks.length-1);let c=0,d=0;r?l?(c=s*t.width,d=i*e.height):(c=i*t.height,d=s*e.width):"start"===n?d=e.width:"end"===n?c=t.width:"inner"!==n&&(c=t.width/2,d=e.width/2),this.paddingLeft=Math.max((c-a+o)*this.width/(this.width-a),0),this.paddingRight=Math.max((d-h+o)*this.width/(this.width-h),0)}else{let i=e.height/2,s=t.height/2;"start"===n?(i=0,s=t.height):"end"===n&&(i=e.height,s=0),this.paddingTop=i+o,this.paddingBottom=s+o}}_handleMargins(){this._margins&&(this._margins.left=Math.max(this.paddingLeft,this._margins.left),this._margins.top=Math.max(this.paddingTop,this._margins.top),this._margins.right=Math.max(this.paddingRight,this._margins.right),this._margins.bottom=Math.max(this.paddingBottom,this._margins.bottom))}afterFit(){d(this.options.afterFit,[this])}isHorizontal(){const{axis:t,position:e}=this.options;return"top"===e||"bottom"===e||"x"===t}isFullSize(){return this.options.fullSize}_convertTicksToLabels(t){let e,i;for(this.beforeTickToLabelConversion(),this.generateTickLabels(t),e=0,i=t.length;e<i;e++)s(t[e].label)&&(t.splice(e,1),i--,e--);this.afterTickToLabelConversion()}_getLabelSizes(){let t=this._labelSizes;if(!t){const e=this.options.ticks.sampleSize;let i=this.ticks;e<i.length&&(i=Xs(i,e)),this._labelSizes=t=this._computeLabelSizes(i,i.length,this.options.ticks.maxTicksLimit)}return t}_computeLabelSizes(t,e,i){const{ctx:o,_longestTextCache:a}=this,r=[],l=[],h=Math.floor(e/Us(e,i));let c,d,f,g,p,m,x,b,_,y,v,M=0,w=0;for(c=0;c<e;c+=h){if(g=t[c].label,p=this._resolveTickFontOptions(c),o.font=m=p.string,x=a[m]=a[m]||{data:{},gc:[]},b=p.lineHeight,_=y=0,s(g)||n(g)){if(n(g))for(d=0,f=g.length;d<f;++d)v=g[d],s(v)||n(v)||(_=Ce(o,x.data,x.gc,_,v),y+=b)}else _=Ce(o,x.data,x.gc,_,g),y=b;r.push(_),l.push(y),M=Math.max(_,M),w=Math.max(y,w)}!function(t,e){u(t,(t=>{const i=t.gc,s=i.length/2;let n;if(s>e){for(n=0;n<s;++n)delete t.data[i[n]];i.splice(0,s)}}))}(a,e);const k=r.indexOf(M),S=l.indexOf(w),P=t=>({width:r[t]||0,height:l[t]||0});return{first:P(0),last:P(e-1),widest:P(k),highest:P(S),widths:r,heights:l}}getLabelForValue(t){return t}getPixelForValue(t,e){return NaN}getValueForPixel(t){}getPixelForTick(t){const e=this.ticks;return t<0||t>e.length-1?null:this.getPixelForValue(e[t].value)}getPixelForDecimal(t){this._reversePixels&&(t=1-t);const e=this._startPixel+t*this._length;return Q(this._alignToPixels?Ae(this.chart,e,0):e)}getDecimalForPixel(t){const e=(t-this._startPixel)/this._length;return this._reversePixels?1-e:e}getBasePixel(){return this.getPixelForValue(this.getBaseValue())}getBaseValue(){const{min:t,max:e}=this;return t<0&&e<0?e:t>0&&e>0?t:0}getContext(t){const e=this.ticks||[];if(t>=0&&t<e.length){const i=e[t];return i.$context||(i.$context=function(t,e,i){return Ci(t,{tick:i,index:e,type:"tick"})}(this.getContext(),t,i))}return this.$context||(this.$context=Ci(this.chart.getContext(),{scale:this,type:"scale"}))}_tickSize(){const t=this.options.ticks,e=$(this.labelRotation),i=Math.abs(Math.cos(e)),s=Math.abs(Math.sin(e)),n=this._getLabelSizes(),o=t.autoSkipPadding||0,a=n?n.widest.width+o:0,r=n?n.highest.height+o:0;return this.isHorizontal()?r*i>a*s?a/i:r/s:r*s<a*i?r/i:a/s}_isVisible(){const t=this.options.display;return"auto"!==t?!!t:this.getMatchingVisibleMetas().length>0}_computeGridLineItems(t){const e=this.axis,i=this.chart,s=this.options,{grid:n,position:a,border:r}=s,h=n.offset,c=this.isHorizontal(),d=this.ticks.length+(h?1:0),u=Ks(n),f=[],g=r.setContext(this.getContext()),p=g.display?g.width:0,m=p/2,x=function(t){return Ae(i,t,p)};let b,_,y,v,M,w,k,S,P,D,C,O;if("top"===a)b=x(this.bottom),w=this.bottom-u,S=b-m,D=x(t.top)+m,O=t.bottom;else if("bottom"===a)b=x(this.top),D=t.top,O=x(t.bottom)-m,w=b+m,S=this.top+u;else if("left"===a)b=x(this.right),M=this.right-u,k=b-m,P=x(t.left)+m,C=t.right;else if("right"===a)b=x(this.left),P=t.left,C=x(t.right)-m,M=b+m,k=this.left+u;else if("x"===e){if("center"===a)b=x((t.top+t.bottom)/2+.5);else if(o(a)){const t=Object.keys(a)[0],e=a[t];b=x(this.chart.scales[t].getPixelForValue(e))}D=t.top,O=t.bottom,w=b+m,S=w+u}else if("y"===e){if("center"===a)b=x((t.left+t.right)/2);else if(o(a)){const t=Object.keys(a)[0],e=a[t];b=x(this.chart.scales[t].getPixelForValue(e))}M=b-m,k=M-u,P=t.left,C=t.right}const A=l(s.ticks.maxTicksLimit,d),T=Math.max(1,Math.ceil(d/A));for(_=0;_<d;_+=T){const t=this.getContext(_),e=n.setContext(t),s=r.setContext(t),o=e.lineWidth,a=e.color,l=s.dash||[],d=s.dashOffset,u=e.tickWidth,g=e.tickColor,p=e.tickBorderDash||[],m=e.tickBorderDashOffset;y=qs(this,_,h),void 0!==y&&(v=Ae(i,y,o),c?M=k=P=C=v:w=S=D=O=v,f.push({tx1:M,ty1:w,tx2:k,ty2:S,x1:P,y1:D,x2:C,y2:O,width:o,color:a,borderDash:l,borderDashOffset:d,tickWidth:u,tickColor:g,tickBorderDash:p,tickBorderDashOffset:m}))}return this._ticksLength=d,this._borderValue=b,f}_computeLabelItems(t){const e=this.axis,i=this.options,{position:s,ticks:a}=i,r=this.isHorizontal(),l=this.ticks,{align:h,crossAlign:c,padding:d,mirror:u}=a,f=Ks(i.grid),g=f+d,p=u?-d:g,m=-$(this.labelRotation),x=[];let b,_,y,v,M,w,k,S,P,D,C,O,A="middle";if("top"===s)w=this.bottom-p,k=this._getXAxisLabelAlignment();else if("bottom"===s)w=this.top+p,k=this._getXAxisLabelAlignment();else if("left"===s){const t=this._getYAxisLabelAlignment(f);k=t.textAlign,M=t.x}else if("right"===s){const t=this._getYAxisLabelAlignment(f);k=t.textAlign,M=t.x}else if("x"===e){if("center"===s)w=(t.top+t.bottom)/2+g;else if(o(s)){const t=Object.keys(s)[0],e=s[t];w=this.chart.scales[t].getPixelForValue(e)+g}k=this._getXAxisLabelAlignment()}else if("y"===e){if("center"===s)M=(t.left+t.right)/2-g;else if(o(s)){const t=Object.keys(s)[0],e=s[t];M=this.chart.scales[t].getPixelForValue(e)}k=this._getYAxisLabelAlignment(f).textAlign}"y"===e&&("start"===h?A="top":"end"===h&&(A="bottom"));const T=this._getLabelSizes();for(b=0,_=l.length;b<_;++b){y=l[b],v=y.label;const t=a.setContext(this.getContext(b));S=this.getPixelForTick(b)+a.labelOffset,P=this._resolveTickFontOptions(b),D=P.lineHeight,C=n(v)?v.length:1;const e=C/2,i=t.color,o=t.textStrokeColor,h=t.textStrokeWidth;let d,f=k;if(r?(M=S,"inner"===k&&(f=b===_-1?this.options.reverse?"left":"right":0===b?this.options.reverse?"right":"left":"center"),O="top"===s?"near"===c||0!==m?-C*D+D/2:"center"===c?-T.highest.height/2-e*D+D:-T.highest.height+D/2:"near"===c||0!==m?D/2:"center"===c?T.highest.height/2-e*D:T.highest.height-C*D,u&&(O*=-1),0===m||t.showLabelBackdrop||(M+=D/2*Math.sin(m))):(w=S,O=(1-C)*D/2),t.showLabelBackdrop){const e=ki(t.backdropPadding),i=T.heights[b],s=T.widths[b];let n=O-e.top,o=0-e.left;switch(A){case"middle":n-=i/2;break;case"bottom":n-=i}switch(k){case"center":o-=s/2;break;case"right":o-=s;break;case"inner":b===_-1?o-=s:b>0&&(o-=s/2)}d={left:o,top:n,width:s+e.width,height:i+e.height,color:t.backdropColor}}x.push({label:v,font:P,textOffset:O,options:{rotation:m,color:i,strokeColor:o,strokeWidth:h,textAlign:f,textBaseline:A,translation:[M,w],backdrop:d}})}return x}_getXAxisLabelAlignment(){const{position:t,ticks:e}=this.options;if(-$(this.labelRotation))return"top"===t?"left":"right";let i="center";return"start"===e.align?i="left":"end"===e.align?i="right":"inner"===e.align&&(i="inner"),i}_getYAxisLabelAlignment(t){const{position:e,ticks:{crossAlign:i,mirror:s,padding:n}}=this.options,o=t+n,a=this._getLabelSizes().widest.width;let r,l;return"left"===e?s?(l=this.right+n,"near"===i?r="left":"center"===i?(r="center",l+=a/2):(r="right",l+=a)):(l=this.right-o,"near"===i?r="right":"center"===i?(r="center",l-=a/2):(r="left",l=this.left)):"right"===e?s?(l=this.left+n,"near"===i?r="right":"center"===i?(r="center",l-=a/2):(r="left",l-=a)):(l=this.left+o,"near"===i?r="left":"center"===i?(r="center",l+=a/2):(r="right",l=this.right)):r="right",{textAlign:r,x:l}}_computeLabelArea(){if(this.options.ticks.mirror)return;const t=this.chart,e=this.options.position;return"left"===e||"right"===e?{top:0,left:this.left,bottom:t.height,right:this.right}:"top"===e||"bottom"===e?{top:this.top,left:0,bottom:this.bottom,right:t.width}:void 0}drawBackground(){const{ctx:t,options:{backgroundColor:e},left:i,top:s,width:n,height:o}=this;e&&(t.save(),t.fillStyle=e,t.fillRect(i,s,n,o),t.restore())}getLineWidthForValue(t){const e=this.options.grid;if(!this._isVisible()||!e.display)return 0;const i=this.ticks.findIndex((e=>e.value===t));if(i>=0){return e.setContext(this.getContext(i)).lineWidth}return 0}drawGrid(t){const e=this.options.grid,i=this.ctx,s=this._gridLineItems||(this._gridLineItems=this._computeGridLineItems(t));let n,o;const a=(t,e,s)=>{s.width&&s.color&&(i.save(),i.lineWidth=s.width,i.strokeStyle=s.color,i.setLineDash(s.borderDash||[]),i.lineDashOffset=s.borderDashOffset,i.beginPath(),i.moveTo(t.x,t.y),i.lineTo(e.x,e.y),i.stroke(),i.restore())};if(e.display)for(n=0,o=s.length;n<o;++n){const t=s[n];e.drawOnChartArea&&a({x:t.x1,y:t.y1},{x:t.x2,y:t.y2},t),e.drawTicks&&a({x:t.tx1,y:t.ty1},{x:t.tx2,y:t.ty2},{color:t.tickColor,width:t.tickWidth,borderDash:t.tickBorderDash,borderDashOffset:t.tickBorderDashOffset})}}drawBorder(){const{chart:t,ctx:e,options:{border:i,grid:s}}=this,n=i.setContext(this.getContext()),o=i.display?n.width:0;if(!o)return;const a=s.setContext(this.getContext(0)).lineWidth,r=this._borderValue;let l,h,c,d;this.isHorizontal()?(l=Ae(t,this.left,o)-o/2,h=Ae(t,this.right,a)+a/2,c=d=r):(c=Ae(t,this.top,o)-o/2,d=Ae(t,this.bottom,a)+a/2,l=h=r),e.save(),e.lineWidth=n.width,e.strokeStyle=n.color,e.beginPath(),e.moveTo(l,c),e.lineTo(h,d),e.stroke(),e.restore()}drawLabels(t){if(!this.options.ticks.display)return;const e=this.ctx,i=this._computeLabelArea();i&&Ie(e,i);const s=this.getLabelItems(t);for(const t of s){const i=t.options,s=t.font;Ne(e,t.label,0,t.textOffset,s,i)}i&&ze(e)}drawTitle(){const{ctx:t,options:{position:e,title:i,reverse:s}}=this;if(!i.display)return;const a=Si(i.font),r=ki(i.padding),l=i.align;let h=a.lineHeight/2;"bottom"===e||"center"===e||o(e)?(h+=r.bottom,n(i.text)&&(h+=a.lineHeight*(i.text.length-1))):h+=r.top;const{titleX:c,titleY:d,maxWidth:u,rotation:f}=function(t,e,i,s){const{top:n,left:a,bottom:r,right:l,chart:h}=t,{chartArea:c,scales:d}=h;let u,f,g,p=0;const m=r-n,x=l-a;if(t.isHorizontal()){if(f=ft(s,a,l),o(i)){const t=Object.keys(i)[0],s=i[t];g=d[t].getPixelForValue(s)+m-e}else g="center"===i?(c.bottom+c.top)/2+m-e:Ys(t,i,e);u=l-a}else{if(o(i)){const t=Object.keys(i)[0],s=i[t];f=d[t].getPixelForValue(s)-x+e}else f="center"===i?(c.left+c.right)/2-x+e:Ys(t,i,e);g=ft(s,r,n),p="left"===i?-E:E}return{titleX:f,titleY:g,maxWidth:u,rotation:p}}(this,h,e,l);Ne(t,i.text,0,0,a,{color:i.color,maxWidth:u,rotation:f,textAlign:Zs(l,e,s),textBaseline:"middle",translation:[c,d]})}draw(t){this._isVisible()&&(this.drawBackground(),this.drawGrid(t),this.drawBorder(),this.drawTitle(),this.drawLabels(t))}_layers(){const t=this.options,e=t.ticks&&t.ticks.z||0,i=l(t.grid&&t.grid.z,-1),s=l(t.border&&t.border.z,0);return this._isVisible()&&this.draw===Js.prototype.draw?[{z:i,draw:t=>{this.drawBackground(),this.drawGrid(t),this.drawTitle()}},{z:s,draw:()=>{this.drawBorder()}},{z:e,draw:t=>{this.drawLabels(t)}}]:[{z:e,draw:t=>{this.draw(t)}}]}getMatchingVisibleMetas(t){const e=this.chart.getSortedVisibleDatasetMetas(),i=this.axis+"AxisID",s=[];let n,o;for(n=0,o=e.length;n<o;++n){const o=e[n];o[i]!==this.id||t&&o.type!==t||s.push(o)}return s}_resolveTickFontOptions(t){return Si(this.options.ticks.setContext(this.getContext(t)).font)}_maxDigits(){const t=this._resolveTickFontOptions(0).lineHeight;return(this.isHorizontal()?this.width:this.height)/t}}class Qs{constructor(t,e,i){this.type=t,this.scope=e,this.override=i,this.items=Object.create(null)}isForType(t){return Object.prototype.isPrototypeOf.call(this.type.prototype,t.prototype)}register(t){const e=Object.getPrototypeOf(t);let i;(function(t){return"id"in t&&"defaults"in t})(e)&&(i=this.register(e));const s=this.items,n=t.id,o=this.scope+"."+n;if(!n)throw new Error("class does not have id: "+t);return n in s||(s[n]=t,function(t,e,i){const s=x(Object.create(null),[i?ue.get(i):{},ue.get(e),t.defaults]);ue.set(e,s),t.defaultRoutes&&function(t,e){Object.keys(e).forEach((i=>{const s=i.split("."),n=s.pop(),o=[t].concat(s).join("."),a=e[i].split("."),r=a.pop(),l=a.join(".");ue.route(o,n,l,r)}))}(e,t.defaultRoutes);t.descriptors&&ue.describe(e,t.descriptors)}(t,o,i),this.override&&ue.override(t.id,t.overrides)),o}get(t){return this.items[t]}unregister(t){const e=this.items,i=t.id,s=this.scope;i in e&&delete e[i],s&&i in ue[s]&&(delete ue[s][i],this.override&&delete re[i])}}class tn{constructor(){this.controllers=new Qs(Ns,"datasets",!0),this.elements=new Qs(Hs,"elements"),this.plugins=new Qs(Object,"plugins"),this.scales=new Qs(Js,"scales"),this._typedRegistries=[this.controllers,this.scales,this.elements]}add(...t){this._each("register",t)}remove(...t){this._each("unregister",t)}addControllers(...t){this._each("register",t,this.controllers)}addElements(...t){this._each("register",t,this.elements)}addPlugins(...t){this._each("register",t,this.plugins)}addScales(...t){this._each("register",t,this.scales)}getController(t){return this._get(t,this.controllers,"controller")}getElement(t){return this._get(t,this.elements,"element")}getPlugin(t){return this._get(t,this.plugins,"plugin")}getScale(t){return this._get(t,this.scales,"scale")}removeControllers(...t){this._each("unregister",t,this.controllers)}removeElements(...t){this._each("unregister",t,this.elements)}removePlugins(...t){this._each("unregister",t,this.plugins)}removeScales(...t){this._each("unregister",t,this.scales)}_each(t,e,i){[...e].forEach((e=>{const s=i||this._getRegistryForType(e);i||s.isForType(e)||s===this.plugins&&e.id?this._exec(t,s,e):u(e,(e=>{const s=i||this._getRegistryForType(e);this._exec(t,s,e)}))}))}_exec(t,e,i){const s=w(t);d(i["before"+s],[],i),e[t](i),d(i["after"+s],[],i)}_getRegistryForType(t){for(let e=0;e<this._typedRegistries.length;e++){const i=this._typedRegistries[e];if(i.isForType(t))return i}return this.plugins}_get(t,e,i){const s=e.get(t);if(void 0===s)throw new Error('"'+t+'" is not a registered '+i+".");return s}}var en=new tn;class sn{constructor(){this._init=[]}notify(t,e,i,s){"beforeInit"===e&&(this._init=this._createDescriptors(t,!0),this._notify(this._init,t,"install"));const n=s?this._descriptors(t).filter(s):this._descriptors(t),o=this._notify(n,t,e,i);return"afterDestroy"===e&&(this._notify(n,t,"stop"),this._notify(this._init,t,"uninstall")),o}_notify(t,e,i,s){s=s||{};for(const n of t){const t=n.plugin;if(!1===d(t[i],[e,s,n.options],t)&&s.cancelable)return!1}return!0}invalidate(){s(this._cache)||(this._oldCache=this._cache,this._cache=void 0)}_descriptors(t){if(this._cache)return this._cache;const e=this._cache=this._createDescriptors(t);return this._notifyStateChanges(t),e}_createDescriptors(t,e){const i=t&&t.config,s=l(i.options&&i.options.plugins,{}),n=function(t){const e={},i=[],s=Object.keys(en.plugins.items);for(let t=0;t<s.length;t++)i.push(en.getPlugin(s[t]));const n=t.plugins||[];for(let t=0;t<n.length;t++){const s=n[t];-1===i.indexOf(s)&&(i.push(s),e[s.id]=!0)}return{plugins:i,localIds:e}}(i);return!1!==s||e?function(t,{plugins:e,localIds:i},s,n){const o=[],a=t.getContext();for(const r of e){const e=r.id,l=nn(s[e],n);null!==l&&o.push({plugin:r,options:on(t.config,{plugin:r,local:i[e]},l,a)})}return o}(t,n,s,e):[]}_notifyStateChanges(t){const e=this._oldCache||[],i=this._cache,s=(t,e)=>t.filter((t=>!e.some((e=>t.plugin.id===e.plugin.id))));this._notify(s(e,i),t,"stop"),this._notify(s(i,e),t,"start")}}function nn(t,e){return e||!1!==t?!0===t?{}:t:null}function on(t,{plugin:e,local:i},s,n){const o=t.pluginScopeKeys(e),a=t.getOptionScopes(s,o);return i&&e.defaults&&a.push(e.defaults),t.createResolver(a,n,[""],{scriptable:!1,indexable:!1,allKeys:!0})}function an(t,e){const i=ue.datasets[t]||{};return((e.datasets||{})[t]||{}).indexAxis||e.indexAxis||i.indexAxis||"x"}function rn(t){if("x"===t||"y"===t||"r"===t)return t}function ln(t,...e){if(rn(t))return t;for(const s of e){const e=s.axis||("top"===(i=s.position)||"bottom"===i?"x":"left"===i||"right"===i?"y":void 0)||t.length>1&&rn(t[0].toLowerCase());if(e)return e}var i;throw new Error(`Cannot determine type of '${t}' axis. Please provide 'axis' or 'position' option.`)}function hn(t,e,i){if(i[e+"AxisID"]===t)return{axis:e}}function cn(t,e){const i=re[t.type]||{scales:{}},s=e.scales||{},n=an(t.type,e),a=Object.create(null);return Object.keys(s).forEach((e=>{const r=s[e];if(!o(r))return console.error(`Invalid scale configuration for scale: ${e}`);if(r._proxy)return console.warn(`Ignoring resolver passed as options for scale: ${e}`);const l=ln(e,r,function(t,e){if(e.data&&e.data.datasets){const i=e.data.datasets.filter((e=>e.xAxisID===t||e.yAxisID===t));if(i.length)return hn(t,"x",i[0])||hn(t,"y",i[0])}return{}}(e,t),ue.scales[r.type]),h=function(t,e){return t===e?"_index_":"_value_"}(l,n),c=i.scales||{};a[e]=b(Object.create(null),[{axis:l},r,c[l],c[h]])})),t.data.datasets.forEach((i=>{const n=i.type||t.type,o=i.indexAxis||an(n,e),r=(re[n]||{}).scales||{};Object.keys(r).forEach((t=>{const e=function(t,e){let i=t;return"_index_"===t?i=e:"_value_"===t&&(i="x"===e?"y":"x"),i}(t,o),n=i[e+"AxisID"]||e;a[n]=a[n]||Object.create(null),b(a[n],[{axis:e},s[n],r[t]])}))})),Object.keys(a).forEach((t=>{const e=a[t];b(e,[ue.scales[e.type],ue.scale])})),a}function dn(t){const e=t.options||(t.options={});e.plugins=l(e.plugins,{}),e.scales=cn(t,e)}function un(t){return(t=t||{}).datasets=t.datasets||[],t.labels=t.labels||[],t}const fn=new Map,gn=new Set;function pn(t,e){let i=fn.get(t);return i||(i=e(),fn.set(t,i),gn.add(i)),i}const mn=(t,e,i)=>{const s=M(e,i);void 0!==s&&t.add(s)};class xn{constructor(t){this._config=function(t){return(t=t||{}).data=un(t.data),dn(t),t}(t),this._scopeCache=new Map,this._resolverCache=new Map}get platform(){return this._config.platform}get type(){return this._config.type}set type(t){this._config.type=t}get data(){return this._config.data}set data(t){this._config.data=un(t)}get options(){return this._config.options}set options(t){this._config.options=t}get plugins(){return this._config.plugins}update(){const t=this._config;this.clearCache(),dn(t)}clearCache(){this._scopeCache.clear(),this._resolverCache.clear()}datasetScopeKeys(t){return pn(t,(()=>[[`datasets.${t}`,""]]))}datasetAnimationScopeKeys(t,e){return pn(`${t}.transition.${e}`,(()=>[[`datasets.${t}.transitions.${e}`,`transitions.${e}`],[`datasets.${t}`,""]]))}datasetElementScopeKeys(t,e){return pn(`${t}-${e}`,(()=>[[`datasets.${t}.elements.${e}`,`datasets.${t}`,`elements.${e}`,""]]))}pluginScopeKeys(t){const e=t.id;return pn(`${this.type}-plugin-${e}`,(()=>[[`plugins.${e}`,...t.additionalOptionScopes||[]]]))}_cachedScopes(t,e){const i=this._scopeCache;let s=i.get(t);return s&&!e||(s=new Map,i.set(t,s)),s}getOptionScopes(t,e,i){const{options:s,type:n}=this,o=this._cachedScopes(t,i),a=o.get(e);if(a)return a;const r=new Set;e.forEach((e=>{t&&(r.add(t),e.forEach((e=>mn(r,t,e)))),e.forEach((t=>mn(r,s,t))),e.forEach((t=>mn(r,re[n]||{},t))),e.forEach((t=>mn(r,ue,t))),e.forEach((t=>mn(r,le,t)))}));const l=Array.from(r);return 0===l.length&&l.push(Object.create(null)),gn.has(e)&&o.set(e,l),l}chartOptionScopes(){const{options:t,type:e}=this;return[t,re[e]||{},ue.datasets[e]||{},{type:e},ue,le]}resolveNamedOptions(t,e,i,s=[""]){const o={$shared:!0},{resolver:a,subPrefixes:r}=bn(this._resolverCache,t,s);let l=a;if(function(t,e){const{isScriptable:i,isIndexable:s}=Ye(t);for(const o of e){const e=i(o),a=s(o),r=(a||e)&&t[o];if(e&&(S(r)||_n(r))||a&&n(r))return!0}return!1}(a,e)){o.$shared=!1;l=$e(a,i=S(i)?i():i,this.createResolver(t,i,r))}for(const t of e)o[t]=l[t];return o}createResolver(t,e,i=[""],s){const{resolver:n}=bn(this._resolverCache,t,i);return o(e)?$e(n,e,void 0,s):n}}function bn(t,e,i){let s=t.get(e);s||(s=new Map,t.set(e,s));const n=i.join();let o=s.get(n);if(!o){o={resolver:je(e,i),subPrefixes:i.filter((t=>!t.toLowerCase().includes("hover")))},s.set(n,o)}return o}const _n=t=>o(t)&&Object.getOwnPropertyNames(t).some((e=>S(t[e])));const yn=["top","bottom","left","right","chartArea"];function vn(t,e){return"top"===t||"bottom"===t||-1===yn.indexOf(t)&&"x"===e}function Mn(t,e){return function(i,s){return i[t]===s[t]?i[e]-s[e]:i[t]-s[t]}}function wn(t){const e=t.chart,i=e.options.animation;e.notifyPlugins("afterRender"),d(i&&i.onComplete,[t],e)}function kn(t){const e=t.chart,i=e.options.animation;d(i&&i.onProgress,[t],e)}function Sn(t){return fe()&&"string"==typeof t?t=document.getElementById(t):t&&t.length&&(t=t[0]),t&&t.canvas&&(t=t.canvas),t}const Pn={},Dn=t=>{const e=Sn(t);return Object.values(Pn).filter((t=>t.canvas===e)).pop()};function Cn(t,e,i){const s=Object.keys(t);for(const n of s){const s=+n;if(s>=e){const o=t[n];delete t[n],(i>0||s>e)&&(t[s+i]=o)}}}function On(t,e,i){return t.options.clip?t[i]:e[i]}class An{static defaults=ue;static instances=Pn;static overrides=re;static registry=en;static version="4.4.8";static getChart=Dn;static register(...t){en.add(...t),Tn()}static unregister(...t){en.remove(...t),Tn()}constructor(t,e){const s=this.config=new xn(e),n=Sn(t),o=Dn(n);if(o)throw new Error("Canvas is already in use. Chart with ID '"+o.id+"' must be destroyed before the canvas with ID '"+o.canvas.id+"' can be reused.");const a=s.createResolver(s.chartOptionScopes(),this.getContext());this.platform=new(s.platform||ks(n)),this.platform.updateConfig(s);const r=this.platform.acquireContext(n,a.aspectRatio),l=r&&r.canvas,h=l&&l.height,c=l&&l.width;this.id=i(),this.ctx=r,this.canvas=l,this.width=c,this.height=h,this._options=a,this._aspectRatio=this.aspectRatio,this._layers=[],this._metasets=[],this._stacks=void 0,this.boxes=[],this.currentDevicePixelRatio=void 0,this.chartArea=void 0,this._active=[],this._lastEvent=void 0,this._listeners={},this._responsiveListeners=void 0,this._sortedMetasets=[],this.scales={},this._plugins=new sn,this.$proxies={},this._hiddenIndices={},this.attached=!1,this._animationsDisabled=void 0,this.$context=void 0,this._doResize=dt((t=>this.update(t)),a.resizeDelay||0),this._dataChanges=[],Pn[this.id]=this,r&&l?(bt.listen(this,"complete",wn),bt.listen(this,"progress",kn),this._initialize(),this.attached&&this.update()):console.error("Failed to create chart: can't acquire context from the given item")}get aspectRatio(){const{options:{aspectRatio:t,maintainAspectRatio:e},width:i,height:n,_aspectRatio:o}=this;return s(t)?e&&o?o:n?i/n:null:t}get data(){return this.config.data}set data(t){this.config.data=t}get options(){return this._options}set options(t){this.config.options=t}get registry(){return en}_initialize(){return this.notifyPlugins("beforeInit"),this.options.responsive?this.resize():ke(this,this.options.devicePixelRatio),this.bindEvents(),this.notifyPlugins("afterInit"),this}clear(){return Te(this.canvas,this.ctx),this}stop(){return bt.stop(this),this}resize(t,e){bt.running(this)?this._resizeBeforeDraw={width:t,height:e}:this._resize(t,e)}_resize(t,e){const i=this.options,s=this.canvas,n=i.maintainAspectRatio&&this.aspectRatio,o=this.platform.getMaximumSize(s,t,e,n),a=i.devicePixelRatio||this.platform.getDevicePixelRatio(),r=this.width?"resize":"attach";this.width=o.width,this.height=o.height,this._aspectRatio=this.aspectRatio,ke(this,a,!0)&&(this.notifyPlugins("resize",{size:o}),d(i.onResize,[this,o],this),this.attached&&this._doResize(r)&&this.render())}ensureScalesHaveIDs(){u(this.options.scales||{},((t,e)=>{t.id=e}))}buildOrUpdateScales(){const t=this.options,e=t.scales,i=this.scales,s=Object.keys(i).reduce(((t,e)=>(t[e]=!1,t)),{});let n=[];e&&(n=n.concat(Object.keys(e).map((t=>{const i=e[t],s=ln(t,i),n="r"===s,o="x"===s;return{options:i,dposition:n?"chartArea":o?"bottom":"left",dtype:n?"radialLinear":o?"category":"linear"}})))),u(n,(e=>{const n=e.options,o=n.id,a=ln(o,n),r=l(n.type,e.dtype);void 0!==n.position&&vn(n.position,a)===vn(e.dposition)||(n.position=e.dposition),s[o]=!0;let h=null;if(o in i&&i[o].type===r)h=i[o];else{h=new(en.getScale(r))({id:o,type:r,ctx:this.ctx,chart:this}),i[h.id]=h}h.init(n,t)})),u(s,((t,e)=>{t||delete i[e]})),u(i,(t=>{as.configure(this,t,t.options),as.addBox(this,t)}))}_updateMetasets(){const t=this._metasets,e=this.data.datasets.length,i=t.length;if(t.sort(((t,e)=>t.index-e.index)),i>e){for(let t=e;t<i;++t)this._destroyDatasetMeta(t);t.splice(e,i-e)}this._sortedMetasets=t.slice(0).sort(Mn("order","index"))}_removeUnreferencedMetasets(){const{_metasets:t,data:{datasets:e}}=this;t.length>e.length&&delete this._stacks,t.forEach(((t,i)=>{0===e.filter((e=>e===t._dataset)).length&&this._destroyDatasetMeta(i)}))}buildOrUpdateControllers(){const t=[],e=this.data.datasets;let i,s;for(this._removeUnreferencedMetasets(),i=0,s=e.length;i<s;i++){const s=e[i];let n=this.getDatasetMeta(i);const o=s.type||this.config.type;if(n.type&&n.type!==o&&(this._destroyDatasetMeta(i),n=this.getDatasetMeta(i)),n.type=o,n.indexAxis=s.indexAxis||an(o,this.options),n.order=s.order||0,n.index=i,n.label=""+s.label,n.visible=this.isDatasetVisible(i),n.controller)n.controller.updateIndex(i),n.controller.linkScales();else{const e=en.getController(o),{datasetElementType:s,dataElementType:a}=ue.datasets[o];Object.assign(e,{dataElementType:en.getElement(a),datasetElementType:s&&en.getElement(s)}),n.controller=new e(this,i),t.push(n.controller)}}return this._updateMetasets(),t}_resetElements(){u(this.data.datasets,((t,e)=>{this.getDatasetMeta(e).controller.reset()}),this)}reset(){this._resetElements(),this.notifyPlugins("reset")}update(t){const e=this.config;e.update();const i=this._options=e.createResolver(e.chartOptionScopes(),this.getContext()),s=this._animationsDisabled=!i.animation;if(this._updateScales(),this._checkEventBindings(),this._updateHiddenIndices(),this._plugins.invalidate(),!1===this.notifyPlugins("beforeUpdate",{mode:t,cancelable:!0}))return;const n=this.buildOrUpdateControllers();this.notifyPlugins("beforeElementsUpdate");let o=0;for(let t=0,e=this.data.datasets.length;t<e;t++){const{controller:e}=this.getDatasetMeta(t),i=!s&&-1===n.indexOf(e);e.buildOrUpdateElements(i),o=Math.max(+e.getMaxOverflow(),o)}o=this._minPadding=i.layout.autoPadding?o:0,this._updateLayout(o),s||u(n,(t=>{t.reset()})),this._updateDatasets(t),this.notifyPlugins("afterUpdate",{mode:t}),this._layers.sort(Mn("z","_idx"));const{_active:a,_lastEvent:r}=this;r?this._eventHandler(r,!0):a.length&&this._updateHoverStyles(a,a,!0),this.render()}_updateScales(){u(this.scales,(t=>{as.removeBox(this,t)})),this.ensureScalesHaveIDs(),this.buildOrUpdateScales()}_checkEventBindings(){const t=this.options,e=new Set(Object.keys(this._listeners)),i=new Set(t.events);P(e,i)&&!!this._responsiveListeners===t.responsive||(this.unbindEvents(),this.bindEvents())}_updateHiddenIndices(){const{_hiddenIndices:t}=this,e=this._getUniformDataChanges()||[];for(const{method:i,start:s,count:n}of e){Cn(t,s,"_removeElements"===i?-n:n)}}_getUniformDataChanges(){const t=this._dataChanges;if(!t||!t.length)return;this._dataChanges=[];const e=this.data.datasets.length,i=e=>new Set(t.filter((t=>t[0]===e)).map(((t,e)=>e+","+t.splice(1).join(",")))),s=i(0);for(let t=1;t<e;t++)if(!P(s,i(t)))return;return Array.from(s).map((t=>t.split(","))).map((t=>({method:t[1],start:+t[2],count:+t[3]})))}_updateLayout(t){if(!1===this.notifyPlugins("beforeLayout",{cancelable:!0}))return;as.update(this,this.width,this.height,t);const e=this.chartArea,i=e.width<=0||e.height<=0;this._layers=[],u(this.boxes,(t=>{i&&"chartArea"===t.position||(t.configure&&t.configure(),this._layers.push(...t._layers()))}),this),this._layers.forEach(((t,e)=>{t._idx=e})),this.notifyPlugins("afterLayout")}_updateDatasets(t){if(!1!==this.notifyPlugins("beforeDatasetsUpdate",{mode:t,cancelable:!0})){for(let t=0,e=this.data.datasets.length;t<e;++t)this.getDatasetMeta(t).controller.configure();for(let e=0,i=this.data.datasets.length;e<i;++e)this._updateDataset(e,S(t)?t({datasetIndex:e}):t);this.notifyPlugins("afterDatasetsUpdate",{mode:t})}}_updateDataset(t,e){const i=this.getDatasetMeta(t),s={meta:i,index:t,mode:e,cancelable:!0};!1!==this.notifyPlugins("beforeDatasetUpdate",s)&&(i.controller._update(e),s.cancelable=!1,this.notifyPlugins("afterDatasetUpdate",s))}render(){!1!==this.notifyPlugins("beforeRender",{cancelable:!0})&&(bt.has(this)?this.attached&&!bt.running(this)&&bt.start(this):(this.draw(),wn({chart:this})))}draw(){let t;if(this._resizeBeforeDraw){const{width:t,height:e}=this._resizeBeforeDraw;this._resizeBeforeDraw=null,this._resize(t,e)}if(this.clear(),this.width<=0||this.height<=0)return;if(!1===this.notifyPlugins("beforeDraw",{cancelable:!0}))return;const e=this._layers;for(t=0;t<e.length&&e[t].z<=0;++t)e[t].draw(this.chartArea);for(this._drawDatasets();t<e.length;++t)e[t].draw(this.chartArea);this.notifyPlugins("afterDraw")}_getSortedDatasetMetas(t){const e=this._sortedMetasets,i=[];let s,n;for(s=0,n=e.length;s<n;++s){const n=e[s];t&&!n.visible||i.push(n)}return i}getSortedVisibleDatasetMetas(){return this._getSortedDatasetMetas(!0)}_drawDatasets(){if(!1===this.notifyPlugins("beforeDatasetsDraw",{cancelable:!0}))return;const t=this.getSortedVisibleDatasetMetas();for(let e=t.length-1;e>=0;--e)this._drawDataset(t[e]);this.notifyPlugins("afterDatasetsDraw")}_drawDataset(t){const e=this.ctx,i=t._clip,s=!i.disabled,n=function(t,e){const{xScale:i,yScale:s}=t;return i&&s?{left:On(i,e,"left"),right:On(i,e,"right"),top:On(s,e,"top"),bottom:On(s,e,"bottom")}:e}(t,this.chartArea),o={meta:t,index:t.index,cancelable:!0};!1!==this.notifyPlugins("beforeDatasetDraw",o)&&(s&&Ie(e,{left:!1===i.left?0:n.left-i.left,right:!1===i.right?this.width:n.right+i.right,top:!1===i.top?0:n.top-i.top,bottom:!1===i.bottom?this.height:n.bottom+i.bottom}),t.controller.draw(),s&&ze(e),o.cancelable=!1,this.notifyPlugins("afterDatasetDraw",o))}isPointInArea(t){return Re(t,this.chartArea,this._minPadding)}getElementsAtEventForMode(t,e,i,s){const n=Xi.modes[e];return"function"==typeof n?n(this,t,i,s):[]}getDatasetMeta(t){const e=this.data.datasets[t],i=this._metasets;let s=i.filter((t=>t&&t._dataset===e)).pop();return s||(s={type:null,data:[],dataset:null,controller:null,hidden:null,xAxisID:null,yAxisID:null,order:e&&e.order||0,index:t,_dataset:e,_parsed:[],_sorted:!1},i.push(s)),s}getContext(){return this.$context||(this.$context=Ci(null,{chart:this,type:"chart"}))}getVisibleDatasetCount(){return this.getSortedVisibleDatasetMetas().length}isDatasetVisible(t){const e=this.data.datasets[t];if(!e)return!1;const i=this.getDatasetMeta(t);return"boolean"==typeof i.hidden?!i.hidden:!e.hidden}setDatasetVisibility(t,e){this.getDatasetMeta(t).hidden=!e}toggleDataVisibility(t){this._hiddenIndices[t]=!this._hiddenIndices[t]}getDataVisibility(t){return!this._hiddenIndices[t]}_updateVisibility(t,e,i){const s=i?"show":"hide",n=this.getDatasetMeta(t),o=n.controller._resolveAnimations(void 0,s);k(e)?(n.data[e].hidden=!i,this.update()):(this.setDatasetVisibility(t,i),o.update(n,{visible:i}),this.update((e=>e.datasetIndex===t?s:void 0)))}hide(t,e){this._updateVisibility(t,e,!1)}show(t,e){this._updateVisibility(t,e,!0)}_destroyDatasetMeta(t){const e=this._metasets[t];e&&e.controller&&e.controller._destroy(),delete this._metasets[t]}_stop(){let t,e;for(this.stop(),bt.remove(this),t=0,e=this.data.datasets.length;t<e;++t)this._destroyDatasetMeta(t)}destroy(){this.notifyPlugins("beforeDestroy");const{canvas:t,ctx:e}=this;this._stop(),this.config.clearCache(),t&&(this.unbindEvents(),Te(t,e),this.platform.releaseContext(e),this.canvas=null,this.ctx=null),delete Pn[this.id],this.notifyPlugins("afterDestroy")}toBase64Image(...t){return this.canvas.toDataURL(...t)}bindEvents(){this.bindUserEvents(),this.options.responsive?this.bindResponsiveEvents():this.attached=!0}bindUserEvents(){const t=this._listeners,e=this.platform,i=(i,s)=>{e.addEventListener(this,i,s),t[i]=s},s=(t,e,i)=>{t.offsetX=e,t.offsetY=i,this._eventHandler(t)};u(this.options.events,(t=>i(t,s)))}bindResponsiveEvents(){this._responsiveListeners||(this._responsiveListeners={});const t=this._responsiveListeners,e=this.platform,i=(i,s)=>{e.addEventListener(this,i,s),t[i]=s},s=(i,s)=>{t[i]&&(e.removeEventListener(this,i,s),delete t[i])},n=(t,e)=>{this.canvas&&this.resize(t,e)};let o;const a=()=>{s("attach",a),this.attached=!0,this.resize(),i("resize",n),i("detach",o)};o=()=>{this.attached=!1,s("resize",n),this._stop(),this._resize(0,0),i("attach",a)},e.isAttached(this.canvas)?a():o()}unbindEvents(){u(this._listeners,((t,e)=>{this.platform.removeEventListener(this,e,t)})),this._listeners={},u(this._responsiveListeners,((t,e)=>{this.platform.removeEventListener(this,e,t)})),this._responsiveListeners=void 0}updateHoverStyle(t,e,i){const s=i?"set":"remove";let n,o,a,r;for("dataset"===e&&(n=this.getDatasetMeta(t[0].datasetIndex),n.controller["_"+s+"DatasetHoverStyle"]()),a=0,r=t.length;a<r;++a){o=t[a];const e=o&&this.getDatasetMeta(o.datasetIndex).controller;e&&e[s+"HoverStyle"](o.element,o.datasetIndex,o.index)}}getActiveElements(){return this._active||[]}setActiveElements(t){const e=this._active||[],i=t.map((({datasetIndex:t,index:e})=>{const i=this.getDatasetMeta(t);if(!i)throw new Error("No dataset found at index "+t);return{datasetIndex:t,element:i.data[e],index:e}}));!f(i,e)&&(this._active=i,this._lastEvent=null,this._updateHoverStyles(i,e))}notifyPlugins(t,e,i){return this._plugins.notify(this,t,e,i)}isPluginEnabled(t){return 1===this._plugins._cache.filter((e=>e.plugin.id===t)).length}_updateHoverStyles(t,e,i){const s=this.options.hover,n=(t,e)=>t.filter((t=>!e.some((e=>t.datasetIndex===e.datasetIndex&&t.index===e.index)))),o=n(e,t),a=i?t:n(t,e);o.length&&this.updateHoverStyle(o,s.mode,!1),a.length&&s.mode&&this.updateHoverStyle(a,s.mode,!0)}_eventHandler(t,e){const i={event:t,replay:e,cancelable:!0,inChartArea:this.isPointInArea(t)},s=e=>(e.options.events||this.options.events).includes(t.native.type);if(!1===this.notifyPlugins("beforeEvent",i,s))return;const n=this._handleEvent(t,e,i.inChartArea);return i.cancelable=!1,this.notifyPlugins("afterEvent",i,s),(n||i.changed)&&this.render(),this}_handleEvent(t,e,i){const{_active:s=[],options:n}=this,o=e,a=this._getActiveElements(t,s,i,o),r=D(t),l=function(t,e,i,s){return i&&"mouseout"!==t.type?s?e:t:null}(t,this._lastEvent,i,r);i&&(this._lastEvent=null,d(n.onHover,[t,a,this],this),r&&d(n.onClick,[t,a,this],this));const h=!f(a,s);return(h||e)&&(this._active=a,this._updateHoverStyles(a,s,e)),this._lastEvent=l,h}_getActiveElements(t,e,i,s){if("mouseout"===t.type)return[];if(!i)return e;const n=this.options.hover;return this.getElementsAtEventForMode(t,n.mode,n,s)}}function Tn(){return u(An.instances,(t=>t._plugins.invalidate()))}function Ln(){throw new Error("This method is not implemented: Check that a complete date adapter is provided.")}class En{static override(t){Object.assign(En.prototype,t)}options;constructor(t){this.options=t||{}}init(){}formats(){return Ln()}parse(){return Ln()}format(){return Ln()}add(){return Ln()}diff(){return Ln()}startOf(){return Ln()}endOf(){return Ln()}}var Rn={_date:En};function In(t){const e=t.iScale,i=function(t,e){if(!t._cache.$bar){const i=t.getMatchingVisibleMetas(e);let s=[];for(let e=0,n=i.length;e<n;e++)s=s.concat(i[e].controller.getAllParsedValues(t));t._cache.$bar=lt(s.sort(((t,e)=>t-e)))}return t._cache.$bar}(e,t.type);let s,n,o,a,r=e._length;const l=()=>{32767!==o&&-32768!==o&&(k(a)&&(r=Math.min(r,Math.abs(o-a)||r)),a=o)};for(s=0,n=i.length;s<n;++s)o=e.getPixelForValue(i[s]),l();for(a=void 0,s=0,n=e.ticks.length;s<n;++s)o=e.getPixelForTick(s),l();return r}function zn(t,e,i,s){return n(t)?function(t,e,i,s){const n=i.parse(t[0],s),o=i.parse(t[1],s),a=Math.min(n,o),r=Math.max(n,o);let l=a,h=r;Math.abs(a)>Math.abs(r)&&(l=r,h=a),e[i.axis]=h,e._custom={barStart:l,barEnd:h,start:n,end:o,min:a,max:r}}(t,e,i,s):e[i.axis]=i.parse(t,s),e}function Fn(t,e,i,s){const n=t.iScale,o=t.vScale,a=n.getLabels(),r=n===o,l=[];let h,c,d,u;for(h=i,c=i+s;h<c;++h)u=e[h],d={},d[n.axis]=r||n.parse(a[h],h),l.push(zn(u,d,o,h));return l}function Vn(t){return t&&void 0!==t.barStart&&void 0!==t.barEnd}function Bn(t,e,i,s){let n=e.borderSkipped;const o={};if(!n)return void(t.borderSkipped=o);if(!0===n)return void(t.borderSkipped={top:!0,right:!0,bottom:!0,left:!0});const{start:a,end:r,reverse:l,top:h,bottom:c}=function(t){let e,i,s,n,o;return t.horizontal?(e=t.base>t.x,i="left",s="right"):(e=t.base<t.y,i="bottom",s="top"),e?(n="end",o="start"):(n="start",o="end"),{start:i,end:s,reverse:e,top:n,bottom:o}}(t);"middle"===n&&i&&(t.enableBorderRadius=!0,(i._top||0)===s?n=h:(i._bottom||0)===s?n=c:(o[Wn(c,a,r,l)]=!0,n=h)),o[Wn(n,a,r,l)]=!0,t.borderSkipped=o}function Wn(t,e,i,s){var n,o,a;return s?(a=i,t=Nn(t=(n=t)===(o=e)?a:n===a?o:n,i,e)):t=Nn(t,e,i),t}function Nn(t,e,i){return"start"===t?e:"end"===t?i:t}function Hn(t,{inflateAmount:e},i){t.inflateAmount="auto"===e?1===i?.33:0:e}class jn extends Ns{static id="doughnut";static defaults={datasetElementType:!1,dataElementType:"arc",animation:{animateRotate:!0,animateScale:!1},animations:{numbers:{type:"number",properties:["circumference","endAngle","innerRadius","outerRadius","startAngle","x","y","offset","borderWidth","spacing"]}},cutout:"50%",rotation:0,circumference:360,radius:"100%",spacing:0,indexAxis:"r"};static descriptors={_scriptable:t=>"spacing"!==t,_indexable:t=>"spacing"!==t&&!t.startsWith("borderDash")&&!t.startsWith("hoverBorderDash")};static overrides={aspectRatio:1,plugins:{legend:{labels:{generateLabels(t){const e=t.data;if(e.labels.length&&e.datasets.length){const{labels:{pointStyle:i,color:s}}=t.legend.options;return e.labels.map(((e,n)=>{const o=t.getDatasetMeta(0).controller.getStyle(n);return{text:e,fillStyle:o.backgroundColor,strokeStyle:o.borderColor,fontColor:s,lineWidth:o.borderWidth,pointStyle:i,hidden:!t.getDataVisibility(n),index:n}}))}return[]}},onClick(t,e,i){i.chart.toggleDataVisibility(e.index),i.chart.update()}}}};constructor(t,e){super(t,e),this.enableOptionSharing=!0,this.innerRadius=void 0,this.outerRadius=void 0,this.offsetX=void 0,this.offsetY=void 0}linkScales(){}parse(t,e){const i=this.getDataset().data,s=this._cachedMeta;if(!1===this._parsing)s._parsed=i;else{let n,a,r=t=>+i[t];if(o(i[t])){const{key:t="value"}=this._parsing;r=e=>+M(i[e],t)}for(n=t,a=t+e;n<a;++n)s._parsed[n]=r(n)}}_getRotation(){return $(this.options.rotation-90)}_getCircumference(){return $(this.options.circumference)}_getRotationExtents(){let t=O,e=-O;for(let i=0;i<this.chart.data.datasets.length;++i)if(this.chart.isDatasetVisible(i)&&this.chart.getDatasetMeta(i).type===this._type){const s=this.chart.getDatasetMeta(i).controller,n=s._getRotation(),o=s._getCircumference();t=Math.min(t,n),e=Math.max(e,n+o)}return{rotation:t,circumference:e-t}}update(t){const e=this.chart,{chartArea:i}=e,s=this._cachedMeta,n=s.data,o=this.getMaxBorderWidth()+this.getMaxOffset(n)+this.options.spacing,a=Math.max((Math.min(i.width,i.height)-o)/2,0),r=Math.min(h(this.options.cutout,a),1),l=this._getRingWeight(this.index),{circumference:d,rotation:u}=this._getRotationExtents(),{ratioX:f,ratioY:g,offsetX:p,offsetY:m}=function(t,e,i){let s=1,n=1,o=0,a=0;if(e<O){const r=t,l=r+e,h=Math.cos(r),c=Math.sin(r),d=Math.cos(l),u=Math.sin(l),f=(t,e,s)=>Z(t,r,l,!0)?1:Math.max(e,e*i,s,s*i),g=(t,e,s)=>Z(t,r,l,!0)?-1:Math.min(e,e*i,s,s*i),p=f(0,h,d),m=f(E,c,u),x=g(C,h,d),b=g(C+E,c,u);s=(p-x)/2,n=(m-b)/2,o=-(p+x)/2,a=-(m+b)/2}return{ratioX:s,ratioY:n,offsetX:o,offsetY:a}}(u,d,r),x=(i.width-o)/f,b=(i.height-o)/g,_=Math.max(Math.min(x,b)/2,0),y=c(this.options.radius,_),v=(y-Math.max(y*r,0))/this._getVisibleDatasetWeightTotal();this.offsetX=p*y,this.offsetY=m*y,s.total=this.calculateTotal(),this.outerRadius=y-v*this._getRingWeightOffset(this.index),this.innerRadius=Math.max(this.outerRadius-v*l,0),this.updateElements(n,0,n.length,t)}_circumference(t,e){const i=this.options,s=this._cachedMeta,n=this._getCircumference();return e&&i.animation.animateRotate||!this.chart.getDataVisibility(t)||null===s._parsed[t]||s.data[t].hidden?0:this.calculateCircumference(s._parsed[t]*n/O)}updateElements(t,e,i,s){const n="reset"===s,o=this.chart,a=o.chartArea,r=o.options.animation,l=(a.left+a.right)/2,h=(a.top+a.bottom)/2,c=n&&r.animateScale,d=c?0:this.innerRadius,u=c?0:this.outerRadius,{sharedOptions:f,includeOptions:g}=this._getSharedOptions(e,s);let p,m=this._getRotation();for(p=0;p<e;++p)m+=this._circumference(p,n);for(p=e;p<e+i;++p){const e=this._circumference(p,n),i=t[p],o={x:l+this.offsetX,y:h+this.offsetY,startAngle:m,endAngle:m+e,circumference:e,outerRadius:u,innerRadius:d};g&&(o.options=f||this.resolveDataElementOptions(p,i.active?"active":s)),m+=e,this.updateElement(i,p,o,s)}}calculateTotal(){const t=this._cachedMeta,e=t.data;let i,s=0;for(i=0;i<e.length;i++){const n=t._parsed[i];null===n||isNaN(n)||!this.chart.getDataVisibility(i)||e[i].hidden||(s+=Math.abs(n))}return s}calculateCircumference(t){const e=this._cachedMeta.total;return e>0&&!isNaN(t)?O*(Math.abs(t)/e):0}getLabelAndValue(t){const e=this._cachedMeta,i=this.chart,s=i.data.labels||[],n=ne(e._parsed[t],i.options.locale);return{label:s[t]||"",value:n}}getMaxBorderWidth(t){let e=0;const i=this.chart;let s,n,o,a,r;if(!t)for(s=0,n=i.data.datasets.length;s<n;++s)if(i.isDatasetVisible(s)){o=i.getDatasetMeta(s),t=o.data,a=o.controller;break}if(!t)return 0;for(s=0,n=t.length;s<n;++s)r=a.resolveDataElementOptions(s),"inner"!==r.borderAlign&&(e=Math.max(e,r.borderWidth||0,r.hoverBorderWidth||0));return e}getMaxOffset(t){let e=0;for(let i=0,s=t.length;i<s;++i){const t=this.resolveDataElementOptions(i);e=Math.max(e,t.offset||0,t.hoverOffset||0)}return e}_getRingWeightOffset(t){let e=0;for(let i=0;i<t;++i)this.chart.isDatasetVisible(i)&&(e+=this._getRingWeight(i));return e}_getRingWeight(t){return Math.max(l(this.chart.data.datasets[t].weight,1),0)}_getVisibleDatasetWeightTotal(){return this._getRingWeightOffset(this.chart.data.datasets.length)||1}}class $n extends Ns{static id="polarArea";static defaults={dataElementType:"arc",animation:{animateRotate:!0,animateScale:!0},animations:{numbers:{type:"number",properties:["x","y","startAngle","endAngle","innerRadius","outerRadius"]}},indexAxis:"r",startAngle:0};static overrides={aspectRatio:1,plugins:{legend:{labels:{generateLabels(t){const e=t.data;if(e.labels.length&&e.datasets.length){const{labels:{pointStyle:i,color:s}}=t.legend.options;return e.labels.map(((e,n)=>{const o=t.getDatasetMeta(0).controller.getStyle(n);return{text:e,fillStyle:o.backgroundColor,strokeStyle:o.borderColor,fontColor:s,lineWidth:o.borderWidth,pointStyle:i,hidden:!t.getDataVisibility(n),index:n}}))}return[]}},onClick(t,e,i){i.chart.toggleDataVisibility(e.index),i.chart.update()}}},scales:{r:{type:"radialLinear",angleLines:{display:!1},beginAtZero:!0,grid:{circular:!0},pointLabels:{display:!1},startAngle:0}}};constructor(t,e){super(t,e),this.innerRadius=void 0,this.outerRadius=void 0}getLabelAndValue(t){const e=this._cachedMeta,i=this.chart,s=i.data.labels||[],n=ne(e._parsed[t].r,i.options.locale);return{label:s[t]||"",value:n}}parseObjectData(t,e,i,s){return ii.bind(this)(t,e,i,s)}update(t){const e=this._cachedMeta.data;this._updateRadius(),this.updateElements(e,0,e.length,t)}getMinMax(){const t=this._cachedMeta,e={min:Number.POSITIVE_INFINITY,max:Number.NEGATIVE_INFINITY};return t.data.forEach(((t,i)=>{const s=this.getParsed(i).r;!isNaN(s)&&this.chart.getDataVisibility(i)&&(s<e.min&&(e.min=s),s>e.max&&(e.max=s))})),e}_updateRadius(){const t=this.chart,e=t.chartArea,i=t.options,s=Math.min(e.right-e.left,e.bottom-e.top),n=Math.max(s/2,0),o=(n-Math.max(i.cutoutPercentage?n/100*i.cutoutPercentage:1,0))/t.getVisibleDatasetCount();this.outerRadius=n-o*this.index,this.innerRadius=this.outerRadius-o}updateElements(t,e,i,s){const n="reset"===s,o=this.chart,a=o.options.animation,r=this._cachedMeta.rScale,l=r.xCenter,h=r.yCenter,c=r.getIndexAngle(0)-.5*C;let d,u=c;const f=360/this.countVisibleElements();for(d=0;d<e;++d)u+=this._computeAngle(d,s,f);for(d=e;d<e+i;d++){const e=t[d];let i=u,g=u+this._computeAngle(d,s,f),p=o.getDataVisibility(d)?r.getDistanceFromCenterForValue(this.getParsed(d).r):0;u=g,n&&(a.animateScale&&(p=0),a.animateRotate&&(i=g=c));const m={x:l,y:h,innerRadius:0,outerRadius:p,startAngle:i,endAngle:g,options:this.resolveDataElementOptions(d,e.active?"active":s)};this.updateElement(e,d,m,s)}}countVisibleElements(){const t=this._cachedMeta;let e=0;return t.data.forEach(((t,i)=>{!isNaN(this.getParsed(i).r)&&this.chart.getDataVisibility(i)&&e++})),e}_computeAngle(t,e,i){return this.chart.getDataVisibility(t)?$(this.resolveDataElementOptions(t,e).angle||i):0}}var Yn=Object.freeze({__proto__:null,BarController:class extends Ns{static id="bar";static defaults={datasetElementType:!1,dataElementType:"bar",categoryPercentage:.8,barPercentage:.9,grouped:!0,animations:{numbers:{type:"number",properties:["x","y","base","width","height"]}}};static overrides={scales:{_index_:{type:"category",offset:!0,grid:{offset:!0}},_value_:{type:"linear",beginAtZero:!0}}};parsePrimitiveData(t,e,i,s){return Fn(t,e,i,s)}parseArrayData(t,e,i,s){return Fn(t,e,i,s)}parseObjectData(t,e,i,s){const{iScale:n,vScale:o}=t,{xAxisKey:a="x",yAxisKey:r="y"}=this._parsing,l="x"===n.axis?a:r,h="x"===o.axis?a:r,c=[];let d,u,f,g;for(d=i,u=i+s;d<u;++d)g=e[d],f={},f[n.axis]=n.parse(M(g,l),d),c.push(zn(M(g,h),f,o,d));return c}updateRangeFromParsed(t,e,i,s){super.updateRangeFromParsed(t,e,i,s);const n=i._custom;n&&e===this._cachedMeta.vScale&&(t.min=Math.min(t.min,n.min),t.max=Math.max(t.max,n.max))}getMaxOverflow(){return 0}getLabelAndValue(t){const e=this._cachedMeta,{iScale:i,vScale:s}=e,n=this.getParsed(t),o=n._custom,a=Vn(o)?"["+o.start+", "+o.end+"]":""+s.getLabelForValue(n[s.axis]);return{label:""+i.getLabelForValue(n[i.axis]),value:a}}initialize(){this.enableOptionSharing=!0,super.initialize();this._cachedMeta.stack=this.getDataset().stack}update(t){const e=this._cachedMeta;this.updateElements(e.data,0,e.data.length,t)}updateElements(t,e,i,n){const o="reset"===n,{index:a,_cachedMeta:{vScale:r}}=this,l=r.getBasePixel(),h=r.isHorizontal(),c=this._getRuler(),{sharedOptions:d,includeOptions:u}=this._getSharedOptions(e,n);for(let f=e;f<e+i;f++){const e=this.getParsed(f),i=o||s(e[r.axis])?{base:l,head:l}:this._calculateBarValuePixels(f),g=this._calculateBarIndexPixels(f,c),p=(e._stacks||{})[r.axis],m={horizontal:h,base:i.base,enableBorderRadius:!p||Vn(e._custom)||a===p._top||a===p._bottom,x:h?i.head:g.center,y:h?g.center:i.head,height:h?g.size:Math.abs(i.size),width:h?Math.abs(i.size):g.size};u&&(m.options=d||this.resolveDataElementOptions(f,t[f].active?"active":n));const x=m.options||t[f].options;Bn(m,x,p,a),Hn(m,x,c.ratio),this.updateElement(t[f],f,m,n)}}_getStacks(t,e){const{iScale:i}=this._cachedMeta,n=i.getMatchingVisibleMetas(this._type).filter((t=>t.controller.options.grouped)),o=i.options.stacked,a=[],r=this._cachedMeta.controller.getParsed(e),l=r&&r[i.axis],h=t=>{const e=t._parsed.find((t=>t[i.axis]===l)),n=e&&e[t.vScale.axis];if(s(n)||isNaN(n))return!0};for(const i of n)if((void 0===e||!h(i))&&((!1===o||-1===a.indexOf(i.stack)||void 0===o&&void 0===i.stack)&&a.push(i.stack),i.index===t))break;return a.length||a.push(void 0),a}_getStackCount(t){return this._getStacks(void 0,t).length}_getStackIndex(t,e,i){const s=this._getStacks(t,i),n=void 0!==e?s.indexOf(e):-1;return-1===n?s.length-1:n}_getRuler(){const t=this.options,e=this._cachedMeta,i=e.iScale,s=[];let n,o;for(n=0,o=e.data.length;n<o;++n)s.push(i.getPixelForValue(this.getParsed(n)[i.axis],n));const a=t.barThickness;return{min:a||In(e),pixels:s,start:i._startPixel,end:i._endPixel,stackCount:this._getStackCount(),scale:i,grouped:t.grouped,ratio:a?1:t.categoryPercentage*t.barPercentage}}_calculateBarValuePixels(t){const{_cachedMeta:{vScale:e,_stacked:i,index:n},options:{base:o,minBarLength:a}}=this,r=o||0,l=this.getParsed(t),h=l._custom,c=Vn(h);let d,u,f=l[e.axis],g=0,p=i?this.applyStack(e,l,i):f;p!==f&&(g=p-f,p=f),c&&(f=h.barStart,p=h.barEnd-h.barStart,0!==f&&F(f)!==F(h.barEnd)&&(g=0),g+=f);const m=s(o)||c?g:o;let x=e.getPixelForValue(m);if(d=this.chart.getDataVisibility(t)?e.getPixelForValue(g+p):x,u=d-x,Math.abs(u)<a){u=function(t,e,i){return 0!==t?F(t):(e.isHorizontal()?1:-1)*(e.min>=i?1:-1)}(u,e,r)*a,f===r&&(x-=u/2);const t=e.getPixelForDecimal(0),s=e.getPixelForDecimal(1),o=Math.min(t,s),h=Math.max(t,s);x=Math.max(Math.min(x,h),o),d=x+u,i&&!c&&(l._stacks[e.axis]._visualValues[n]=e.getValueForPixel(d)-e.getValueForPixel(x))}if(x===e.getPixelForValue(r)){const t=F(u)*e.getLineWidthForValue(r)/2;x+=t,u-=t}return{size:u,base:x,head:d,center:d+u/2}}_calculateBarIndexPixels(t,e){const i=e.scale,n=this.options,o=n.skipNull,a=l(n.maxBarThickness,1/0);let r,h;if(e.grouped){const i=o?this._getStackCount(t):e.stackCount,l="flex"===n.barThickness?function(t,e,i,s){const n=e.pixels,o=n[t];let a=t>0?n[t-1]:null,r=t<n.length-1?n[t+1]:null;const l=i.categoryPercentage;null===a&&(a=o-(null===r?e.end-e.start:r-o)),null===r&&(r=o+o-a);const h=o-(o-Math.min(a,r))/2*l;return{chunk:Math.abs(r-a)/2*l/s,ratio:i.barPercentage,start:h}}(t,e,n,i):function(t,e,i,n){const o=i.barThickness;let a,r;return s(o)?(a=e.min*i.categoryPercentage,r=i.barPercentage):(a=o*n,r=1),{chunk:a/n,ratio:r,start:e.pixels[t]-a/2}}(t,e,n,i),c=this._getStackIndex(this.index,this._cachedMeta.stack,o?t:void 0);r=l.start+l.chunk*c+l.chunk/2,h=Math.min(a,l.chunk*l.ratio)}else r=i.getPixelForValue(this.getParsed(t)[i.axis],t),h=Math.min(a,e.min*e.ratio);return{base:r-h/2,head:r+h/2,center:r,size:h}}draw(){const t=this._cachedMeta,e=t.vScale,i=t.data,s=i.length;let n=0;for(;n<s;++n)null===this.getParsed(n)[e.axis]||i[n].hidden||i[n].draw(this._ctx)}},BubbleController:class extends Ns{static id="bubble";static defaults={datasetElementType:!1,dataElementType:"point",animations:{numbers:{type:"number",properties:["x","y","borderWidth","radius"]}}};static overrides={scales:{x:{type:"linear"},y:{type:"linear"}}};initialize(){this.enableOptionSharing=!0,super.initialize()}parsePrimitiveData(t,e,i,s){const n=super.parsePrimitiveData(t,e,i,s);for(let t=0;t<n.length;t++)n[t]._custom=this.resolveDataElementOptions(t+i).radius;return n}parseArrayData(t,e,i,s){const n=super.parseArrayData(t,e,i,s);for(let t=0;t<n.length;t++){const s=e[i+t];n[t]._custom=l(s[2],this.resolveDataElementOptions(t+i).radius)}return n}parseObjectData(t,e,i,s){const n=super.parseObjectData(t,e,i,s);for(let t=0;t<n.length;t++){const s=e[i+t];n[t]._custom=l(s&&s.r&&+s.r,this.resolveDataElementOptions(t+i).radius)}return n}getMaxOverflow(){const t=this._cachedMeta.data;let e=0;for(let i=t.length-1;i>=0;--i)e=Math.max(e,t[i].size(this.resolveDataElementOptions(i))/2);return e>0&&e}getLabelAndValue(t){const e=this._cachedMeta,i=this.chart.data.labels||[],{xScale:s,yScale:n}=e,o=this.getParsed(t),a=s.getLabelForValue(o.x),r=n.getLabelForValue(o.y),l=o._custom;return{label:i[t]||"",value:"("+a+", "+r+(l?", "+l:"")+")"}}update(t){const e=this._cachedMeta.data;this.updateElements(e,0,e.length,t)}updateElements(t,e,i,s){const n="reset"===s,{iScale:o,vScale:a}=this._cachedMeta,{sharedOptions:r,includeOptions:l}=this._getSharedOptions(e,s),h=o.axis,c=a.axis;for(let d=e;d<e+i;d++){const e=t[d],i=!n&&this.getParsed(d),u={},f=u[h]=n?o.getPixelForDecimal(.5):o.getPixelForValue(i[h]),g=u[c]=n?a.getBasePixel():a.getPixelForValue(i[c]);u.skip=isNaN(f)||isNaN(g),l&&(u.options=r||this.resolveDataElementOptions(d,e.active?"active":s),n&&(u.options.radius=0)),this.updateElement(e,d,u,s)}}resolveDataElementOptions(t,e){const i=this.getParsed(t);let s=super.resolveDataElementOptions(t,e);s.$shared&&(s=Object.assign({},s,{$shared:!1}));const n=s.radius;return"active"!==e&&(s.radius=0),s.radius+=l(i&&i._custom,n),s}},DoughnutController:jn,LineController:class extends Ns{static id="line";static defaults={datasetElementType:"line",dataElementType:"point",showLine:!0,spanGaps:!1};static overrides={scales:{_index_:{type:"category"},_value_:{type:"linear"}}};initialize(){this.enableOptionSharing=!0,this.supportsDecimation=!0,super.initialize()}update(t){const e=this._cachedMeta,{dataset:i,data:s=[],_dataset:n}=e,o=this.chart._animationsDisabled;let{start:a,count:r}=pt(e,s,o);this._drawStart=a,this._drawCount=r,mt(e)&&(a=0,r=s.length),i._chart=this.chart,i._datasetIndex=this.index,i._decimated=!!n._decimated,i.points=s;const l=this.resolveDatasetElementOptions(t);this.options.showLine||(l.borderWidth=0),l.segment=this.options.segment,this.updateElement(i,void 0,{animated:!o,options:l},t),this.updateElements(s,a,r,t)}updateElements(t,e,i,n){const o="reset"===n,{iScale:a,vScale:r,_stacked:l,_dataset:h}=this._cachedMeta,{sharedOptions:c,includeOptions:d}=this._getSharedOptions(e,n),u=a.axis,f=r.axis,{spanGaps:g,segment:p}=this.options,m=N(g)?g:Number.POSITIVE_INFINITY,x=this.chart._animationsDisabled||o||"none"===n,b=e+i,_=t.length;let y=e>0&&this.getParsed(e-1);for(let i=0;i<_;++i){const g=t[i],_=x?g:{};if(i<e||i>=b){_.skip=!0;continue}const v=this.getParsed(i),M=s(v[f]),w=_[u]=a.getPixelForValue(v[u],i),k=_[f]=o||M?r.getBasePixel():r.getPixelForValue(l?this.applyStack(r,v,l):v[f],i);_.skip=isNaN(w)||isNaN(k)||M,_.stop=i>0&&Math.abs(v[u]-y[u])>m,p&&(_.parsed=v,_.raw=h.data[i]),d&&(_.options=c||this.resolveDataElementOptions(i,g.active?"active":n)),x||this.updateElement(g,i,_,n),y=v}}getMaxOverflow(){const t=this._cachedMeta,e=t.dataset,i=e.options&&e.options.borderWidth||0,s=t.data||[];if(!s.length)return i;const n=s[0].size(this.resolveDataElementOptions(0)),o=s[s.length-1].size(this.resolveDataElementOptions(s.length-1));return Math.max(i,n,o)/2}draw(){const t=this._cachedMeta;t.dataset.updateControlPoints(this.chart.chartArea,t.iScale.axis),super.draw()}},PieController:class extends jn{static id="pie";static defaults={cutout:0,rotation:0,circumference:360,radius:"100%"}},PolarAreaController:$n,RadarController:class extends Ns{static id="radar";static defaults={datasetElementType:"line",dataElementType:"point",indexAxis:"r",showLine:!0,elements:{line:{fill:"start"}}};static overrides={aspectRatio:1,scales:{r:{type:"radialLinear"}}};getLabelAndValue(t){const e=this._cachedMeta.vScale,i=this.getParsed(t);return{label:e.getLabels()[t],value:""+e.getLabelForValue(i[e.axis])}}parseObjectData(t,e,i,s){return ii.bind(this)(t,e,i,s)}update(t){const e=this._cachedMeta,i=e.dataset,s=e.data||[],n=e.iScale.getLabels();if(i.points=s,"resize"!==t){const e=this.resolveDatasetElementOptions(t);this.options.showLine||(e.borderWidth=0);const o={_loop:!0,_fullLoop:n.length===s.length,options:e};this.updateElement(i,void 0,o,t)}this.updateElements(s,0,s.length,t)}updateElements(t,e,i,s){const n=this._cachedMeta.rScale,o="reset"===s;for(let a=e;a<e+i;a++){const e=t[a],i=this.resolveDataElementOptions(a,e.active?"active":s),r=n.getPointPositionForValue(a,this.getParsed(a).r),l=o?n.xCenter:r.x,h=o?n.yCenter:r.y,c={x:l,y:h,angle:r.angle,skip:isNaN(l)||isNaN(h),options:i};this.updateElement(e,a,c,s)}}},ScatterController:class extends Ns{static id="scatter";static defaults={datasetElementType:!1,dataElementType:"point",showLine:!1,fill:!1};static overrides={interaction:{mode:"point"},scales:{x:{type:"linear"},y:{type:"linear"}}};getLabelAndValue(t){const e=this._cachedMeta,i=this.chart.data.labels||[],{xScale:s,yScale:n}=e,o=this.getParsed(t),a=s.getLabelForValue(o.x),r=n.getLabelForValue(o.y);return{label:i[t]||"",value:"("+a+", "+r+")"}}update(t){const e=this._cachedMeta,{data:i=[]}=e,s=this.chart._animationsDisabled;let{start:n,count:o}=pt(e,i,s);if(this._drawStart=n,this._drawCount=o,mt(e)&&(n=0,o=i.length),this.options.showLine){this.datasetElementType||this.addElements();const{dataset:n,_dataset:o}=e;n._chart=this.chart,n._datasetIndex=this.index,n._decimated=!!o._decimated,n.points=i;const a=this.resolveDatasetElementOptions(t);a.segment=this.options.segment,this.updateElement(n,void 0,{animated:!s,options:a},t)}else this.datasetElementType&&(delete e.dataset,this.datasetElementType=!1);this.updateElements(i,n,o,t)}addElements(){const{showLine:t}=this.options;!this.datasetElementType&&t&&(this.datasetElementType=this.chart.registry.getElement("line")),super.addElements()}updateElements(t,e,i,n){const o="reset"===n,{iScale:a,vScale:r,_stacked:l,_dataset:h}=this._cachedMeta,c=this.resolveDataElementOptions(e,n),d=this.getSharedOptions(c),u=this.includeOptions(n,d),f=a.axis,g=r.axis,{spanGaps:p,segment:m}=this.options,x=N(p)?p:Number.POSITIVE_INFINITY,b=this.chart._animationsDisabled||o||"none"===n;let _=e>0&&this.getParsed(e-1);for(let c=e;c<e+i;++c){const e=t[c],i=this.getParsed(c),p=b?e:{},y=s(i[g]),v=p[f]=a.getPixelForValue(i[f],c),M=p[g]=o||y?r.getBasePixel():r.getPixelForValue(l?this.applyStack(r,i,l):i[g],c);p.skip=isNaN(v)||isNaN(M)||y,p.stop=c>0&&Math.abs(i[f]-_[f])>x,m&&(p.parsed=i,p.raw=h.data[c]),u&&(p.options=d||this.resolveDataElementOptions(c,e.active?"active":n)),b||this.updateElement(e,c,p,n),_=i}this.updateSharedOptions(d,n,c)}getMaxOverflow(){const t=this._cachedMeta,e=t.data||[];if(!this.options.showLine){let t=0;for(let i=e.length-1;i>=0;--i)t=Math.max(t,e[i].size(this.resolveDataElementOptions(i))/2);return t>0&&t}const i=t.dataset,s=i.options&&i.options.borderWidth||0;if(!e.length)return s;const n=e[0].size(this.resolveDataElementOptions(0)),o=e[e.length-1].size(this.resolveDataElementOptions(e.length-1));return Math.max(s,n,o)/2}}});function Un(t,e,i,s){const n=vi(t.options.borderRadius,["outerStart","outerEnd","innerStart","innerEnd"]);const o=(i-e)/2,a=Math.min(o,s*e/2),r=t=>{const e=(i-Math.min(o,t))*s/2;return J(t,0,Math.min(o,e))};return{outerStart:r(n.outerStart),outerEnd:r(n.outerEnd),innerStart:J(n.innerStart,0,a),innerEnd:J(n.innerEnd,0,a)}}function Xn(t,e,i,s){return{x:i+t*Math.cos(e),y:s+t*Math.sin(e)}}function qn(t,e,i,s,n,o){const{x:a,y:r,startAngle:l,pixelMargin:h,innerRadius:c}=e,d=Math.max(e.outerRadius+s+i-h,0),u=c>0?c+s+i+h:0;let f=0;const g=n-l;if(s){const t=((c>0?c-s:0)+(d>0?d-s:0))/2;f=(g-(0!==t?g*t/(t+s):g))/2}const p=(g-Math.max(.001,g*d-i/C)/d)/2,m=l+p+f,x=n-p-f,{outerStart:b,outerEnd:_,innerStart:y,innerEnd:v}=Un(e,u,d,x-m),M=d-b,w=d-_,k=m+b/M,S=x-_/w,P=u+y,D=u+v,O=m+y/P,A=x-v/D;if(t.beginPath(),o){const e=(k+S)/2;if(t.arc(a,r,d,k,e),t.arc(a,r,d,e,S),_>0){const e=Xn(w,S,a,r);t.arc(e.x,e.y,_,S,x+E)}const i=Xn(D,x,a,r);if(t.lineTo(i.x,i.y),v>0){const e=Xn(D,A,a,r);t.arc(e.x,e.y,v,x+E,A+Math.PI)}const s=(x-v/u+(m+y/u))/2;if(t.arc(a,r,u,x-v/u,s,!0),t.arc(a,r,u,s,m+y/u,!0),y>0){const e=Xn(P,O,a,r);t.arc(e.x,e.y,y,O+Math.PI,m-E)}const n=Xn(M,m,a,r);if(t.lineTo(n.x,n.y),b>0){const e=Xn(M,k,a,r);t.arc(e.x,e.y,b,m-E,k)}}else{t.moveTo(a,r);const e=Math.cos(k)*d+a,i=Math.sin(k)*d+r;t.lineTo(e,i);const s=Math.cos(S)*d+a,n=Math.sin(S)*d+r;t.lineTo(s,n)}t.closePath()}function Kn(t,e,i,s,n){const{fullCircles:o,startAngle:a,circumference:r,options:l}=e,{borderWidth:h,borderJoinStyle:c,borderDash:d,borderDashOffset:u}=l,f="inner"===l.borderAlign;if(!h)return;t.setLineDash(d||[]),t.lineDashOffset=u,f?(t.lineWidth=2*h,t.lineJoin=c||"round"):(t.lineWidth=h,t.lineJoin=c||"bevel");let g=e.endAngle;if(o){qn(t,e,i,s,g,n);for(let e=0;e<o;++e)t.stroke();isNaN(r)||(g=a+(r%O||O))}f&&function(t,e,i){const{startAngle:s,pixelMargin:n,x:o,y:a,outerRadius:r,innerRadius:l}=e;let h=n/r;t.beginPath(),t.arc(o,a,r,s-h,i+h),l>n?(h=n/l,t.arc(o,a,l,i+h,s-h,!0)):t.arc(o,a,n,i+E,s-E),t.closePath(),t.clip()}(t,e,g),o||(qn(t,e,i,s,g,n),t.stroke())}function Gn(t,e,i=e){t.lineCap=l(i.borderCapStyle,e.borderCapStyle),t.setLineDash(l(i.borderDash,e.borderDash)),t.lineDashOffset=l(i.borderDashOffset,e.borderDashOffset),t.lineJoin=l(i.borderJoinStyle,e.borderJoinStyle),t.lineWidth=l(i.borderWidth,e.borderWidth),t.strokeStyle=l(i.borderColor,e.borderColor)}function Zn(t,e,i){t.lineTo(i.x,i.y)}function Jn(t,e,i={}){const s=t.length,{start:n=0,end:o=s-1}=i,{start:a,end:r}=e,l=Math.max(n,a),h=Math.min(o,r),c=n<a&&o<a||n>r&&o>r;return{count:s,start:l,loop:e.loop,ilen:h<l&&!c?s+h-l:h-l}}function Qn(t,e,i,s){const{points:n,options:o}=e,{count:a,start:r,loop:l,ilen:h}=Jn(n,i,s),c=function(t){return t.stepped?Fe:t.tension||"monotone"===t.cubicInterpolationMode?Ve:Zn}(o);let d,u,f,{move:g=!0,reverse:p}=s||{};for(d=0;d<=h;++d)u=n[(r+(p?h-d:d))%a],u.skip||(g?(t.moveTo(u.x,u.y),g=!1):c(t,f,u,p,o.stepped),f=u);return l&&(u=n[(r+(p?h:0))%a],c(t,f,u,p,o.stepped)),!!l}function to(t,e,i,s){const n=e.points,{count:o,start:a,ilen:r}=Jn(n,i,s),{move:l=!0,reverse:h}=s||{};let c,d,u,f,g,p,m=0,x=0;const b=t=>(a+(h?r-t:t))%o,_=()=>{f!==g&&(t.lineTo(m,g),t.lineTo(m,f),t.lineTo(m,p))};for(l&&(d=n[b(0)],t.moveTo(d.x,d.y)),c=0;c<=r;++c){if(d=n[b(c)],d.skip)continue;const e=d.x,i=d.y,s=0|e;s===u?(i<f?f=i:i>g&&(g=i),m=(x*m+e)/++x):(_(),t.lineTo(e,i),u=s,x=0,f=g=i),p=i}_()}function eo(t){const e=t.options,i=e.borderDash&&e.borderDash.length;return!(t._decimated||t._loop||e.tension||"monotone"===e.cubicInterpolationMode||e.stepped||i)?to:Qn}const io="function"==typeof Path2D;function so(t,e,i,s){io&&!e.options.segment?function(t,e,i,s){let n=e._path;n||(n=e._path=new Path2D,e.path(n,i,s)&&n.closePath()),Gn(t,e.options),t.stroke(n)}(t,e,i,s):function(t,e,i,s){const{segments:n,options:o}=e,a=eo(e);for(const r of n)Gn(t,o,r.style),t.beginPath(),a(t,e,r,{start:i,end:i+s-1})&&t.closePath(),t.stroke()}(t,e,i,s)}class no extends Hs{static id="line";static defaults={borderCapStyle:"butt",borderDash:[],borderDashOffset:0,borderJoinStyle:"miter",borderWidth:3,capBezierPoints:!0,cubicInterpolationMode:"default",fill:!1,spanGaps:!1,stepped:!1,tension:0};static defaultRoutes={backgroundColor:"backgroundColor",borderColor:"borderColor"};static descriptors={_scriptable:!0,_indexable:t=>"borderDash"!==t&&"fill"!==t};constructor(t){super(),this.animated=!0,this.options=void 0,this._chart=void 0,this._loop=void 0,this._fullLoop=void 0,this._path=void 0,this._points=void 0,this._segments=void 0,this._decimated=!1,this._pointsUpdated=!1,this._datasetIndex=void 0,t&&Object.assign(this,t)}updateControlPoints(t,e){const i=this.options;if((i.tension||"monotone"===i.cubicInterpolationMode)&&!i.stepped&&!this._pointsUpdated){const s=i.spanGaps?this._loop:this._fullLoop;hi(this._points,i,t,s,e),this._pointsUpdated=!0}}set points(t){this._points=t,delete this._segments,delete this._path,this._pointsUpdated=!1}get points(){return this._points}get segments(){return this._segments||(this._segments=zi(this,this.options.segment))}first(){const t=this.segments,e=this.points;return t.length&&e[t[0].start]}last(){const t=this.segments,e=this.points,i=t.length;return i&&e[t[i-1].end]}interpolate(t,e){const i=this.options,s=t[e],n=this.points,o=Ii(this,{property:e,start:s,end:s});if(!o.length)return;const a=[],r=function(t){return t.stepped?pi:t.tension||"monotone"===t.cubicInterpolationMode?mi:gi}(i);let l,h;for(l=0,h=o.length;l<h;++l){const{start:h,end:c}=o[l],d=n[h],u=n[c];if(d===u){a.push(d);continue}const f=r(d,u,Math.abs((s-d[e])/(u[e]-d[e])),i.stepped);f[e]=t[e],a.push(f)}return 1===a.length?a[0]:a}pathSegment(t,e,i){return eo(this)(t,this,e,i)}path(t,e,i){const s=this.segments,n=eo(this);let o=this._loop;e=e||0,i=i||this.points.length-e;for(const a of s)o&=n(t,this,a,{start:e,end:e+i-1});return!!o}draw(t,e,i,s){const n=this.options||{};(this.points||[]).length&&n.borderWidth&&(t.save(),so(t,this,i,s),t.restore()),this.animated&&(this._pointsUpdated=!1,this._path=void 0)}}function oo(t,e,i,s){const n=t.options,{[i]:o}=t.getProps([i],s);return Math.abs(e-o)<n.radius+n.hitRadius}function ao(t,e){const{x:i,y:s,base:n,width:o,height:a}=t.getProps(["x","y","base","width","height"],e);let r,l,h,c,d;return t.horizontal?(d=a/2,r=Math.min(i,n),l=Math.max(i,n),h=s-d,c=s+d):(d=o/2,r=i-d,l=i+d,h=Math.min(s,n),c=Math.max(s,n)),{left:r,top:h,right:l,bottom:c}}function ro(t,e,i,s){return t?0:J(e,i,s)}function lo(t){const e=ao(t),i=e.right-e.left,s=e.bottom-e.top,n=function(t,e,i){const s=t.options.borderWidth,n=t.borderSkipped,o=Mi(s);return{t:ro(n.top,o.top,0,i),r:ro(n.right,o.right,0,e),b:ro(n.bottom,o.bottom,0,i),l:ro(n.left,o.left,0,e)}}(t,i/2,s/2),a=function(t,e,i){const{enableBorderRadius:s}=t.getProps(["enableBorderRadius"]),n=t.options.borderRadius,a=wi(n),r=Math.min(e,i),l=t.borderSkipped,h=s||o(n);return{topLeft:ro(!h||l.top||l.left,a.topLeft,0,r),topRight:ro(!h||l.top||l.right,a.topRight,0,r),bottomLeft:ro(!h||l.bottom||l.left,a.bottomLeft,0,r),bottomRight:ro(!h||l.bottom||l.right,a.bottomRight,0,r)}}(t,i/2,s/2);return{outer:{x:e.left,y:e.top,w:i,h:s,radius:a},inner:{x:e.left+n.l,y:e.top+n.t,w:i-n.l-n.r,h:s-n.t-n.b,radius:{topLeft:Math.max(0,a.topLeft-Math.max(n.t,n.l)),topRight:Math.max(0,a.topRight-Math.max(n.t,n.r)),bottomLeft:Math.max(0,a.bottomLeft-Math.max(n.b,n.l)),bottomRight:Math.max(0,a.bottomRight-Math.max(n.b,n.r))}}}}function ho(t,e,i,s){const n=null===e,o=null===i,a=t&&!(n&&o)&&ao(t,s);return a&&(n||tt(e,a.left,a.right))&&(o||tt(i,a.top,a.bottom))}function co(t,e){t.rect(e.x,e.y,e.w,e.h)}function uo(t,e,i={}){const s=t.x!==i.x?-e:0,n=t.y!==i.y?-e:0,o=(t.x+t.w!==i.x+i.w?e:0)-s,a=(t.y+t.h!==i.y+i.h?e:0)-n;return{x:t.x+s,y:t.y+n,w:t.w+o,h:t.h+a,radius:t.radius}}var fo=Object.freeze({__proto__:null,ArcElement:class extends Hs{static id="arc";static defaults={borderAlign:"center",borderColor:"#fff",borderDash:[],borderDashOffset:0,borderJoinStyle:void 0,borderRadius:0,borderWidth:2,offset:0,spacing:0,angle:void 0,circular:!0};static defaultRoutes={backgroundColor:"backgroundColor"};static descriptors={_scriptable:!0,_indexable:t=>"borderDash"!==t};circumference;endAngle;fullCircles;innerRadius;outerRadius;pixelMargin;startAngle;constructor(t){super(),this.options=void 0,this.circumference=void 0,this.startAngle=void 0,this.endAngle=void 0,this.innerRadius=void 0,this.outerRadius=void 0,this.pixelMargin=0,this.fullCircles=0,t&&Object.assign(this,t)}inRange(t,e,i){const s=this.getProps(["x","y"],i),{angle:n,distance:o}=X(s,{x:t,y:e}),{startAngle:a,endAngle:r,innerRadius:h,outerRadius:c,circumference:d}=this.getProps(["startAngle","endAngle","innerRadius","outerRadius","circumference"],i),u=(this.options.spacing+this.options.borderWidth)/2,f=l(d,r-a),g=Z(n,a,r)&&a!==r,p=f>=O||g,m=tt(o,h+u,c+u);return p&&m}getCenterPoint(t){const{x:e,y:i,startAngle:s,endAngle:n,innerRadius:o,outerRadius:a}=this.getProps(["x","y","startAngle","endAngle","innerRadius","outerRadius"],t),{offset:r,spacing:l}=this.options,h=(s+n)/2,c=(o+a+l+r)/2;return{x:e+Math.cos(h)*c,y:i+Math.sin(h)*c}}tooltipPosition(t){return this.getCenterPoint(t)}draw(t){const{options:e,circumference:i}=this,s=(e.offset||0)/4,n=(e.spacing||0)/2,o=e.circular;if(this.pixelMargin="inner"===e.borderAlign?.33:0,this.fullCircles=i>O?Math.floor(i/O):0,0===i||this.innerRadius<0||this.outerRadius<0)return;t.save();const a=(this.startAngle+this.endAngle)/2;t.translate(Math.cos(a)*s,Math.sin(a)*s);const r=s*(1-Math.sin(Math.min(C,i||0)));t.fillStyle=e.backgroundColor,t.strokeStyle=e.borderColor,function(t,e,i,s,n){const{fullCircles:o,startAngle:a,circumference:r}=e;let l=e.endAngle;if(o){qn(t,e,i,s,l,n);for(let e=0;e<o;++e)t.fill();isNaN(r)||(l=a+(r%O||O))}qn(t,e,i,s,l,n),t.fill()}(t,this,r,n,o),Kn(t,this,r,n,o),t.restore()}},BarElement:class extends Hs{static id="bar";static defaults={borderSkipped:"start",borderWidth:0,borderRadius:0,inflateAmount:"auto",pointStyle:void 0};static defaultRoutes={backgroundColor:"backgroundColor",borderColor:"borderColor"};constructor(t){super(),this.options=void 0,this.horizontal=void 0,this.base=void 0,this.width=void 0,this.height=void 0,this.inflateAmount=void 0,t&&Object.assign(this,t)}draw(t){const{inflateAmount:e,options:{borderColor:i,backgroundColor:s}}=this,{inner:n,outer:o}=lo(this),a=(r=o.radius).topLeft||r.topRight||r.bottomLeft||r.bottomRight?He:co;var r;t.save(),o.w===n.w&&o.h===n.h||(t.beginPath(),a(t,uo(o,e,n)),t.clip(),a(t,uo(n,-e,o)),t.fillStyle=i,t.fill("evenodd")),t.beginPath(),a(t,uo(n,e)),t.fillStyle=s,t.fill(),t.restore()}inRange(t,e,i){return ho(this,t,e,i)}inXRange(t,e){return ho(this,t,null,e)}inYRange(t,e){return ho(this,null,t,e)}getCenterPoint(t){const{x:e,y:i,base:s,horizontal:n}=this.getProps(["x","y","base","horizontal"],t);return{x:n?(e+s)/2:e,y:n?i:(i+s)/2}}getRange(t){return"x"===t?this.width/2:this.height/2}},LineElement:no,PointElement:class extends Hs{static id="point";parsed;skip;stop;static defaults={borderWidth:1,hitRadius:1,hoverBorderWidth:1,hoverRadius:4,pointStyle:"circle",radius:3,rotation:0};static defaultRoutes={backgroundColor:"backgroundColor",borderColor:"borderColor"};constructor(t){super(),this.options=void 0,this.parsed=void 0,this.skip=void 0,this.stop=void 0,t&&Object.assign(this,t)}inRange(t,e,i){const s=this.options,{x:n,y:o}=this.getProps(["x","y"],i);return Math.pow(t-n,2)+Math.pow(e-o,2)<Math.pow(s.hitRadius+s.radius,2)}inXRange(t,e){return oo(this,t,"x",e)}inYRange(t,e){return oo(this,t,"y",e)}getCenterPoint(t){const{x:e,y:i}=this.getProps(["x","y"],t);return{x:e,y:i}}size(t){let e=(t=t||this.options||{}).radius||0;e=Math.max(e,e&&t.hoverRadius||0);return 2*(e+(e&&t.borderWidth||0))}draw(t,e){const i=this.options;this.skip||i.radius<.1||!Re(this,e,this.size(i)/2)||(t.strokeStyle=i.borderColor,t.lineWidth=i.borderWidth,t.fillStyle=i.backgroundColor,Le(t,i,this.x,this.y))}getRange(){const t=this.options||{};return t.radius+t.hitRadius}}});function go(t,e,i,s){const n=t.indexOf(e);if(-1===n)return((t,e,i,s)=>("string"==typeof e?(i=t.push(e)-1,s.unshift({index:i,label:e})):isNaN(e)&&(i=null),i))(t,e,i,s);return n!==t.lastIndexOf(e)?i:n}function po(t){const e=this.getLabels();return t>=0&&t<e.length?e[t]:t}function mo(t,e,{horizontal:i,minRotation:s}){const n=$(s),o=(i?Math.sin(n):Math.cos(n))||.001,a=.75*e*(""+t).length;return Math.min(e/o,a)}class xo extends Js{constructor(t){super(t),this.start=void 0,this.end=void 0,this._startValue=void 0,this._endValue=void 0,this._valueRange=0}parse(t,e){return s(t)||("number"==typeof t||t instanceof Number)&&!isFinite(+t)?null:+t}handleTickRangeOptions(){const{beginAtZero:t}=this.options,{minDefined:e,maxDefined:i}=this.getUserBounds();let{min:s,max:n}=this;const o=t=>s=e?s:t,a=t=>n=i?n:t;if(t){const t=F(s),e=F(n);t<0&&e<0?a(0):t>0&&e>0&&o(0)}if(s===n){let e=0===n?1:Math.abs(.05*n);a(n+e),t||o(s-e)}this.min=s,this.max=n}getTickLimit(){const t=this.options.ticks;let e,{maxTicksLimit:i,stepSize:s}=t;return s?(e=Math.ceil(this.max/s)-Math.floor(this.min/s)+1,e>1e3&&(console.warn(`scales.${this.id}.ticks.stepSize: ${s} would result generating up to ${e} ticks. Limiting to 1000.`),e=1e3)):(e=this.computeTickLimit(),i=i||11),i&&(e=Math.min(i,e)),e}computeTickLimit(){return Number.POSITIVE_INFINITY}buildTicks(){const t=this.options,e=t.ticks;let i=this.getTickLimit();i=Math.max(2,i);const n=function(t,e){const i=[],{bounds:n,step:o,min:a,max:r,precision:l,count:h,maxTicks:c,maxDigits:d,includeBounds:u}=t,f=o||1,g=c-1,{min:p,max:m}=e,x=!s(a),b=!s(r),_=!s(h),y=(m-p)/(d+1);let v,M,w,k,S=B((m-p)/g/f)*f;if(S<1e-14&&!x&&!b)return[{value:p},{value:m}];k=Math.ceil(m/S)-Math.floor(p/S),k>g&&(S=B(k*S/g/f)*f),s(l)||(v=Math.pow(10,l),S=Math.ceil(S*v)/v),"ticks"===n?(M=Math.floor(p/S)*S,w=Math.ceil(m/S)*S):(M=p,w=m),x&&b&&o&&H((r-a)/o,S/1e3)?(k=Math.round(Math.min((r-a)/S,c)),S=(r-a)/k,M=a,w=r):_?(M=x?a:M,w=b?r:w,k=h-1,S=(w-M)/k):(k=(w-M)/S,k=V(k,Math.round(k),S/1e3)?Math.round(k):Math.ceil(k));const P=Math.max(U(S),U(M));v=Math.pow(10,s(l)?P:l),M=Math.round(M*v)/v,w=Math.round(w*v)/v;let D=0;for(x&&(u&&M!==a?(i.push({value:a}),M<a&&D++,V(Math.round((M+D*S)*v)/v,a,mo(a,y,t))&&D++):M<a&&D++);D<k;++D){const t=Math.round((M+D*S)*v)/v;if(b&&t>r)break;i.push({value:t})}return b&&u&&w!==r?i.length&&V(i[i.length-1].value,r,mo(r,y,t))?i[i.length-1].value=r:i.push({value:r}):b&&w!==r||i.push({value:w}),i}({maxTicks:i,bounds:t.bounds,min:t.min,max:t.max,precision:e.precision,step:e.stepSize,count:e.count,maxDigits:this._maxDigits(),horizontal:this.isHorizontal(),minRotation:e.minRotation||0,includeBounds:!1!==e.includeBounds},this._range||this);return"ticks"===t.bounds&&j(n,this,"value"),t.reverse?(n.reverse(),this.start=this.max,this.end=this.min):(this.start=this.min,this.end=this.max),n}configure(){const t=this.ticks;let e=this.min,i=this.max;if(super.configure(),this.options.offset&&t.length){const s=(i-e)/Math.max(t.length-1,1)/2;e-=s,i+=s}this._startValue=e,this._endValue=i,this._valueRange=i-e}getLabelForValue(t){return ne(t,this.chart.options.locale,this.options.ticks.format)}}class bo extends xo{static id="linear";static defaults={ticks:{callback:ae.formatters.numeric}};determineDataLimits(){const{min:t,max:e}=this.getMinMax(!0);this.min=a(t)?t:0,this.max=a(e)?e:1,this.handleTickRangeOptions()}computeTickLimit(){const t=this.isHorizontal(),e=t?this.width:this.height,i=$(this.options.ticks.minRotation),s=(t?Math.sin(i):Math.cos(i))||.001,n=this._resolveTickFontOptions(0);return Math.ceil(e/Math.min(40,n.lineHeight/s))}getPixelForValue(t){return null===t?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getValueForPixel(t){return this._startValue+this.getDecimalForPixel(t)*this._valueRange}}const _o=t=>Math.floor(z(t)),yo=(t,e)=>Math.pow(10,_o(t)+e);function vo(t){return 1===t/Math.pow(10,_o(t))}function Mo(t,e,i){const s=Math.pow(10,i),n=Math.floor(t/s);return Math.ceil(e/s)-n}function wo(t,{min:e,max:i}){e=r(t.min,e);const s=[],n=_o(e);let o=function(t,e){let i=_o(e-t);for(;Mo(t,e,i)>10;)i++;for(;Mo(t,e,i)<10;)i--;return Math.min(i,_o(t))}(e,i),a=o<0?Math.pow(10,Math.abs(o)):1;const l=Math.pow(10,o),h=n>o?Math.pow(10,n):0,c=Math.round((e-h)*a)/a,d=Math.floor((e-h)/l/10)*l*10;let u=Math.floor((c-d)/Math.pow(10,o)),f=r(t.min,Math.round((h+d+u*Math.pow(10,o))*a)/a);for(;f<i;)s.push({value:f,major:vo(f),significand:u}),u>=10?u=u<15?15:20:u++,u>=20&&(o++,u=2,a=o>=0?1:a),f=Math.round((h+d+u*Math.pow(10,o))*a)/a;const g=r(t.max,f);return s.push({value:g,major:vo(g),significand:u}),s}class ko extends Js{static id="logarithmic";static defaults={ticks:{callback:ae.formatters.logarithmic,major:{enabled:!0}}};constructor(t){super(t),this.start=void 0,this.end=void 0,this._startValue=void 0,this._valueRange=0}parse(t,e){const i=xo.prototype.parse.apply(this,[t,e]);if(0!==i)return a(i)&&i>0?i:null;this._zero=!0}determineDataLimits(){const{min:t,max:e}=this.getMinMax(!0);this.min=a(t)?Math.max(0,t):null,this.max=a(e)?Math.max(0,e):null,this.options.beginAtZero&&(this._zero=!0),this._zero&&this.min!==this._suggestedMin&&!a(this._userMin)&&(this.min=t===yo(this.min,0)?yo(this.min,-1):yo(this.min,0)),this.handleTickRangeOptions()}handleTickRangeOptions(){const{minDefined:t,maxDefined:e}=this.getUserBounds();let i=this.min,s=this.max;const n=e=>i=t?i:e,o=t=>s=e?s:t;i===s&&(i<=0?(n(1),o(10)):(n(yo(i,-1)),o(yo(s,1)))),i<=0&&n(yo(s,-1)),s<=0&&o(yo(i,1)),this.min=i,this.max=s}buildTicks(){const t=this.options,e=wo({min:this._userMin,max:this._userMax},this);return"ticks"===t.bounds&&j(e,this,"value"),t.reverse?(e.reverse(),this.start=this.max,this.end=this.min):(this.start=this.min,this.end=this.max),e}getLabelForValue(t){return void 0===t?"0":ne(t,this.chart.options.locale,this.options.ticks.format)}configure(){const t=this.min;super.configure(),this._startValue=z(t),this._valueRange=z(this.max)-z(t)}getPixelForValue(t){return void 0!==t&&0!==t||(t=this.min),null===t||isNaN(t)?NaN:this.getPixelForDecimal(t===this.min?0:(z(t)-this._startValue)/this._valueRange)}getValueForPixel(t){const e=this.getDecimalForPixel(t);return Math.pow(10,this._startValue+e*this._valueRange)}}function So(t){const e=t.ticks;if(e.display&&t.display){const t=ki(e.backdropPadding);return l(e.font&&e.font.size,ue.font.size)+t.height}return 0}function Po(t,e,i,s,n){return t===s||t===n?{start:e-i/2,end:e+i/2}:t<s||t>n?{start:e-i,end:e}:{start:e,end:e+i}}function Do(t){const e={l:t.left+t._padding.left,r:t.right-t._padding.right,t:t.top+t._padding.top,b:t.bottom-t._padding.bottom},i=Object.assign({},e),s=[],o=[],a=t._pointLabels.length,r=t.options.pointLabels,l=r.centerPointLabels?C/a:0;for(let u=0;u<a;u++){const a=r.setContext(t.getPointLabelContext(u));o[u]=a.padding;const f=t.getPointPosition(u,t.drawingArea+o[u],l),g=Si(a.font),p=(h=t.ctx,c=g,d=n(d=t._pointLabels[u])?d:[d],{w:Oe(h,c.string,d),h:d.length*c.lineHeight});s[u]=p;const m=G(t.getIndexAngle(u)+l),x=Math.round(Y(m));Co(i,e,m,Po(x,f.x,p.w,0,180),Po(x,f.y,p.h,90,270))}var h,c,d;t.setCenterPoint(e.l-i.l,i.r-e.r,e.t-i.t,i.b-e.b),t._pointLabelItems=function(t,e,i){const s=[],n=t._pointLabels.length,o=t.options,{centerPointLabels:a,display:r}=o.pointLabels,l={extra:So(o)/2,additionalAngle:a?C/n:0};let h;for(let o=0;o<n;o++){l.padding=i[o],l.size=e[o];const n=Oo(t,o,l);s.push(n),"auto"===r&&(n.visible=Ao(n,h),n.visible&&(h=n))}return s}(t,s,o)}function Co(t,e,i,s,n){const o=Math.abs(Math.sin(i)),a=Math.abs(Math.cos(i));let r=0,l=0;s.start<e.l?(r=(e.l-s.start)/o,t.l=Math.min(t.l,e.l-r)):s.end>e.r&&(r=(s.end-e.r)/o,t.r=Math.max(t.r,e.r+r)),n.start<e.t?(l=(e.t-n.start)/a,t.t=Math.min(t.t,e.t-l)):n.end>e.b&&(l=(n.end-e.b)/a,t.b=Math.max(t.b,e.b+l))}function Oo(t,e,i){const s=t.drawingArea,{extra:n,additionalAngle:o,padding:a,size:r}=i,l=t.getPointPosition(e,s+n+a,o),h=Math.round(Y(G(l.angle+E))),c=function(t,e,i){90===i||270===i?t-=e/2:(i>270||i<90)&&(t-=e);return t}(l.y,r.h,h),d=function(t){if(0===t||180===t)return"center";if(t<180)return"left";return"right"}(h),u=function(t,e,i){"right"===i?t-=e:"center"===i&&(t-=e/2);return t}(l.x,r.w,d);return{visible:!0,x:l.x,y:c,textAlign:d,left:u,top:c,right:u+r.w,bottom:c+r.h}}function Ao(t,e){if(!e)return!0;const{left:i,top:s,right:n,bottom:o}=t;return!(Re({x:i,y:s},e)||Re({x:i,y:o},e)||Re({x:n,y:s},e)||Re({x:n,y:o},e))}function To(t,e,i){const{left:n,top:o,right:a,bottom:r}=i,{backdropColor:l}=e;if(!s(l)){const i=wi(e.borderRadius),s=ki(e.backdropPadding);t.fillStyle=l;const h=n-s.left,c=o-s.top,d=a-n+s.width,u=r-o+s.height;Object.values(i).some((t=>0!==t))?(t.beginPath(),He(t,{x:h,y:c,w:d,h:u,radius:i}),t.fill()):t.fillRect(h,c,d,u)}}function Lo(t,e,i,s){const{ctx:n}=t;if(i)n.arc(t.xCenter,t.yCenter,e,0,O);else{let i=t.getPointPosition(0,e);n.moveTo(i.x,i.y);for(let o=1;o<s;o++)i=t.getPointPosition(o,e),n.lineTo(i.x,i.y)}}class Eo extends xo{static id="radialLinear";static defaults={display:!0,animate:!0,position:"chartArea",angleLines:{display:!0,lineWidth:1,borderDash:[],borderDashOffset:0},grid:{circular:!1},startAngle:0,ticks:{showLabelBackdrop:!0,callback:ae.formatters.numeric},pointLabels:{backdropColor:void 0,backdropPadding:2,display:!0,font:{size:10},callback:t=>t,padding:5,centerPointLabels:!1}};static defaultRoutes={"angleLines.color":"borderColor","pointLabels.color":"color","ticks.color":"color"};static descriptors={angleLines:{_fallback:"grid"}};constructor(t){super(t),this.xCenter=void 0,this.yCenter=void 0,this.drawingArea=void 0,this._pointLabels=[],this._pointLabelItems=[]}setDimensions(){const t=this._padding=ki(So(this.options)/2),e=this.width=this.maxWidth-t.width,i=this.height=this.maxHeight-t.height;this.xCenter=Math.floor(this.left+e/2+t.left),this.yCenter=Math.floor(this.top+i/2+t.top),this.drawingArea=Math.floor(Math.min(e,i)/2)}determineDataLimits(){const{min:t,max:e}=this.getMinMax(!1);this.min=a(t)&&!isNaN(t)?t:0,this.max=a(e)&&!isNaN(e)?e:0,this.handleTickRangeOptions()}computeTickLimit(){return Math.ceil(this.drawingArea/So(this.options))}generateTickLabels(t){xo.prototype.generateTickLabels.call(this,t),this._pointLabels=this.getLabels().map(((t,e)=>{const i=d(this.options.pointLabels.callback,[t,e],this);return i||0===i?i:""})).filter(((t,e)=>this.chart.getDataVisibility(e)))}fit(){const t=this.options;t.display&&t.pointLabels.display?Do(this):this.setCenterPoint(0,0,0,0)}setCenterPoint(t,e,i,s){this.xCenter+=Math.floor((t-e)/2),this.yCenter+=Math.floor((i-s)/2),this.drawingArea-=Math.min(this.drawingArea/2,Math.max(t,e,i,s))}getIndexAngle(t){return G(t*(O/(this._pointLabels.length||1))+$(this.options.startAngle||0))}getDistanceFromCenterForValue(t){if(s(t))return NaN;const e=this.drawingArea/(this.max-this.min);return this.options.reverse?(this.max-t)*e:(t-this.min)*e}getValueForDistanceFromCenter(t){if(s(t))return NaN;const e=t/(this.drawingArea/(this.max-this.min));return this.options.reverse?this.max-e:this.min+e}getPointLabelContext(t){const e=this._pointLabels||[];if(t>=0&&t<e.length){const i=e[t];return function(t,e,i){return Ci(t,{label:i,index:e,type:"pointLabel"})}(this.getContext(),t,i)}}getPointPosition(t,e,i=0){const s=this.getIndexAngle(t)-E+i;return{x:Math.cos(s)*e+this.xCenter,y:Math.sin(s)*e+this.yCenter,angle:s}}getPointPositionForValue(t,e){return this.getPointPosition(t,this.getDistanceFromCenterForValue(e))}getBasePosition(t){return this.getPointPositionForValue(t||0,this.getBaseValue())}getPointLabelPosition(t){const{left:e,top:i,right:s,bottom:n}=this._pointLabelItems[t];return{left:e,top:i,right:s,bottom:n}}drawBackground(){const{backgroundColor:t,grid:{circular:e}}=this.options;if(t){const i=this.ctx;i.save(),i.beginPath(),Lo(this,this.getDistanceFromCenterForValue(this._endValue),e,this._pointLabels.length),i.closePath(),i.fillStyle=t,i.fill(),i.restore()}}drawGrid(){const t=this.ctx,e=this.options,{angleLines:i,grid:s,border:n}=e,o=this._pointLabels.length;let a,r,l;if(e.pointLabels.display&&function(t,e){const{ctx:i,options:{pointLabels:s}}=t;for(let n=e-1;n>=0;n--){const e=t._pointLabelItems[n];if(!e.visible)continue;const o=s.setContext(t.getPointLabelContext(n));To(i,o,e);const a=Si(o.font),{x:r,y:l,textAlign:h}=e;Ne(i,t._pointLabels[n],r,l+a.lineHeight/2,a,{color:o.color,textAlign:h,textBaseline:"middle"})}}(this,o),s.display&&this.ticks.forEach(((t,e)=>{if(0!==e||0===e&&this.min<0){r=this.getDistanceFromCenterForValue(t.value);const i=this.getContext(e),a=s.setContext(i),l=n.setContext(i);!function(t,e,i,s,n){const o=t.ctx,a=e.circular,{color:r,lineWidth:l}=e;!a&&!s||!r||!l||i<0||(o.save(),o.strokeStyle=r,o.lineWidth=l,o.setLineDash(n.dash||[]),o.lineDashOffset=n.dashOffset,o.beginPath(),Lo(t,i,a,s),o.closePath(),o.stroke(),o.restore())}(this,a,r,o,l)}})),i.display){for(t.save(),a=o-1;a>=0;a--){const s=i.setContext(this.getPointLabelContext(a)),{color:n,lineWidth:o}=s;o&&n&&(t.lineWidth=o,t.strokeStyle=n,t.setLineDash(s.borderDash),t.lineDashOffset=s.borderDashOffset,r=this.getDistanceFromCenterForValue(e.reverse?this.min:this.max),l=this.getPointPosition(a,r),t.beginPath(),t.moveTo(this.xCenter,this.yCenter),t.lineTo(l.x,l.y),t.stroke())}t.restore()}}drawBorder(){}drawLabels(){const t=this.ctx,e=this.options,i=e.ticks;if(!i.display)return;const s=this.getIndexAngle(0);let n,o;t.save(),t.translate(this.xCenter,this.yCenter),t.rotate(s),t.textAlign="center",t.textBaseline="middle",this.ticks.forEach(((s,a)=>{if(0===a&&this.min>=0&&!e.reverse)return;const r=i.setContext(this.getContext(a)),l=Si(r.font);if(n=this.getDistanceFromCenterForValue(this.ticks[a].value),r.showLabelBackdrop){t.font=l.string,o=t.measureText(s.label).width,t.fillStyle=r.backdropColor;const e=ki(r.backdropPadding);t.fillRect(-o/2-e.left,-n-l.size/2-e.top,o+e.width,l.size+e.height)}Ne(t,s.label,0,-n,l,{color:r.color,strokeColor:r.textStrokeColor,strokeWidth:r.textStrokeWidth})})),t.restore()}drawTitle(){}}const Ro={millisecond:{common:!0,size:1,steps:1e3},second:{common:!0,size:1e3,steps:60},minute:{common:!0,size:6e4,steps:60},hour:{common:!0,size:36e5,steps:24},day:{common:!0,size:864e5,steps:30},week:{common:!1,size:6048e5,steps:4},month:{common:!0,size:2628e6,steps:12},quarter:{common:!1,size:7884e6,steps:4},year:{common:!0,size:3154e7}},Io=Object.keys(Ro);function zo(t,e){return t-e}function Fo(t,e){if(s(e))return null;const i=t._adapter,{parser:n,round:o,isoWeekday:r}=t._parseOpts;let l=e;return"function"==typeof n&&(l=n(l)),a(l)||(l="string"==typeof n?i.parse(l,n):i.parse(l)),null===l?null:(o&&(l="week"!==o||!N(r)&&!0!==r?i.startOf(l,o):i.startOf(l,"isoWeek",r)),+l)}function Vo(t,e,i,s){const n=Io.length;for(let o=Io.indexOf(t);o<n-1;++o){const t=Ro[Io[o]],n=t.steps?t.steps:Number.MAX_SAFE_INTEGER;if(t.common&&Math.ceil((i-e)/(n*t.size))<=s)return Io[o]}return Io[n-1]}function Bo(t,e,i){if(i){if(i.length){const{lo:s,hi:n}=et(i,e);t[i[s]>=e?i[s]:i[n]]=!0}}else t[e]=!0}function Wo(t,e,i){const s=[],n={},o=e.length;let a,r;for(a=0;a<o;++a)r=e[a],n[r]=a,s.push({value:r,major:!1});return 0!==o&&i?function(t,e,i,s){const n=t._adapter,o=+n.startOf(e[0].value,s),a=e[e.length-1].value;let r,l;for(r=o;r<=a;r=+n.add(r,1,s))l=i[r],l>=0&&(e[l].major=!0);return e}(t,s,n,i):s}class No extends Js{static id="time";static defaults={bounds:"data",adapters:{},time:{parser:!1,unit:!1,round:!1,isoWeekday:!1,minUnit:"millisecond",displayFormats:{}},ticks:{source:"auto",callback:!1,major:{enabled:!1}}};constructor(t){super(t),this._cache={data:[],labels:[],all:[]},this._unit="day",this._majorUnit=void 0,this._offsets={},this._normalized=!1,this._parseOpts=void 0}init(t,e={}){const i=t.time||(t.time={}),s=this._adapter=new Rn._date(t.adapters.date);s.init(e),b(i.displayFormats,s.formats()),this._parseOpts={parser:i.parser,round:i.round,isoWeekday:i.isoWeekday},super.init(t),this._normalized=e.normalized}parse(t,e){return void 0===t?null:Fo(this,t)}beforeLayout(){super.beforeLayout(),this._cache={data:[],labels:[],all:[]}}determineDataLimits(){const t=this.options,e=this._adapter,i=t.time.unit||"day";let{min:s,max:n,minDefined:o,maxDefined:r}=this.getUserBounds();function l(t){o||isNaN(t.min)||(s=Math.min(s,t.min)),r||isNaN(t.max)||(n=Math.max(n,t.max))}o&&r||(l(this._getLabelBounds()),"ticks"===t.bounds&&"labels"===t.ticks.source||l(this.getMinMax(!1))),s=a(s)&&!isNaN(s)?s:+e.startOf(Date.now(),i),n=a(n)&&!isNaN(n)?n:+e.endOf(Date.now(),i)+1,this.min=Math.min(s,n-1),this.max=Math.max(s+1,n)}_getLabelBounds(){const t=this.getLabelTimestamps();let e=Number.POSITIVE_INFINITY,i=Number.NEGATIVE_INFINITY;return t.length&&(e=t[0],i=t[t.length-1]),{min:e,max:i}}buildTicks(){const t=this.options,e=t.time,i=t.ticks,s="labels"===i.source?this.getLabelTimestamps():this._generate();"ticks"===t.bounds&&s.length&&(this.min=this._userMin||s[0],this.max=this._userMax||s[s.length-1]);const n=this.min,o=nt(s,n,this.max);return this._unit=e.unit||(i.autoSkip?Vo(e.minUnit,this.min,this.max,this._getLabelCapacity(n)):function(t,e,i,s,n){for(let o=Io.length-1;o>=Io.indexOf(i);o--){const i=Io[o];if(Ro[i].common&&t._adapter.diff(n,s,i)>=e-1)return i}return Io[i?Io.indexOf(i):0]}(this,o.length,e.minUnit,this.min,this.max)),this._majorUnit=i.major.enabled&&"year"!==this._unit?function(t){for(let e=Io.indexOf(t)+1,i=Io.length;e<i;++e)if(Ro[Io[e]].common)return Io[e]}(this._unit):void 0,this.initOffsets(s),t.reverse&&o.reverse(),Wo(this,o,this._majorUnit)}afterAutoSkip(){this.options.offsetAfterAutoskip&&this.initOffsets(this.ticks.map((t=>+t.value)))}initOffsets(t=[]){let e,i,s=0,n=0;this.options.offset&&t.length&&(e=this.getDecimalForValue(t[0]),s=1===t.length?1-e:(this.getDecimalForValue(t[1])-e)/2,i=this.getDecimalForValue(t[t.length-1]),n=1===t.length?i:(i-this.getDecimalForValue(t[t.length-2]))/2);const o=t.length<3?.5:.25;s=J(s,0,o),n=J(n,0,o),this._offsets={start:s,end:n,factor:1/(s+1+n)}}_generate(){const t=this._adapter,e=this.min,i=this.max,s=this.options,n=s.time,o=n.unit||Vo(n.minUnit,e,i,this._getLabelCapacity(e)),a=l(s.ticks.stepSize,1),r="week"===o&&n.isoWeekday,h=N(r)||!0===r,c={};let d,u,f=e;if(h&&(f=+t.startOf(f,"isoWeek",r)),f=+t.startOf(f,h?"day":o),t.diff(i,e,o)>1e5*a)throw new Error(e+" and "+i+" are too far apart with stepSize of "+a+" "+o);const g="data"===s.ticks.source&&this.getDataTimestamps();for(d=f,u=0;d<i;d=+t.add(d,a,o),u++)Bo(c,d,g);return d!==i&&"ticks"!==s.bounds&&1!==u||Bo(c,d,g),Object.keys(c).sort(zo).map((t=>+t))}getLabelForValue(t){const e=this._adapter,i=this.options.time;return i.tooltipFormat?e.format(t,i.tooltipFormat):e.format(t,i.displayFormats.datetime)}format(t,e){const i=this.options.time.displayFormats,s=this._unit,n=e||i[s];return this._adapter.format(t,n)}_tickFormatFunction(t,e,i,s){const n=this.options,o=n.ticks.callback;if(o)return d(o,[t,e,i],this);const a=n.time.displayFormats,r=this._unit,l=this._majorUnit,h=r&&a[r],c=l&&a[l],u=i[e],f=l&&c&&u&&u.major;return this._adapter.format(t,s||(f?c:h))}generateTickLabels(t){let e,i,s;for(e=0,i=t.length;e<i;++e)s=t[e],s.label=this._tickFormatFunction(s.value,e,t)}getDecimalForValue(t){return null===t?NaN:(t-this.min)/(this.max-this.min)}getPixelForValue(t){const e=this._offsets,i=this.getDecimalForValue(t);return this.getPixelForDecimal((e.start+i)*e.factor)}getValueForPixel(t){const e=this._offsets,i=this.getDecimalForPixel(t)/e.factor-e.end;return this.min+i*(this.max-this.min)}_getLabelSize(t){const e=this.options.ticks,i=this.ctx.measureText(t).width,s=$(this.isHorizontal()?e.maxRotation:e.minRotation),n=Math.cos(s),o=Math.sin(s),a=this._resolveTickFontOptions(0).size;return{w:i*n+a*o,h:i*o+a*n}}_getLabelCapacity(t){const e=this.options.time,i=e.displayFormats,s=i[e.unit]||i.millisecond,n=this._tickFormatFunction(t,0,Wo(this,[t],this._majorUnit),s),o=this._getLabelSize(n),a=Math.floor(this.isHorizontal()?this.width/o.w:this.height/o.h)-1;return a>0?a:1}getDataTimestamps(){let t,e,i=this._cache.data||[];if(i.length)return i;const s=this.getMatchingVisibleMetas();if(this._normalized&&s.length)return this._cache.data=s[0].controller.getAllParsedValues(this);for(t=0,e=s.length;t<e;++t)i=i.concat(s[t].controller.getAllParsedValues(this));return this._cache.data=this.normalize(i)}getLabelTimestamps(){const t=this._cache.labels||[];let e,i;if(t.length)return t;const s=this.getLabels();for(e=0,i=s.length;e<i;++e)t.push(Fo(this,s[e]));return this._cache.labels=this._normalized?t:this.normalize(t)}normalize(t){return lt(t.sort(zo))}}function Ho(t,e,i){let s,n,o,a,r=0,l=t.length-1;i?(e>=t[r].pos&&e<=t[l].pos&&({lo:r,hi:l}=it(t,"pos",e)),({pos:s,time:o}=t[r]),({pos:n,time:a}=t[l])):(e>=t[r].time&&e<=t[l].time&&({lo:r,hi:l}=it(t,"time",e)),({time:s,pos:o}=t[r]),({time:n,pos:a}=t[l]));const h=n-s;return h?o+(a-o)*(e-s)/h:o}var jo=Object.freeze({__proto__:null,CategoryScale:class extends Js{static id="category";static defaults={ticks:{callback:po}};constructor(t){super(t),this._startValue=void 0,this._valueRange=0,this._addedLabels=[]}init(t){const e=this._addedLabels;if(e.length){const t=this.getLabels();for(const{index:i,label:s}of e)t[i]===s&&t.splice(i,1);this._addedLabels=[]}super.init(t)}parse(t,e){if(s(t))return null;const i=this.getLabels();return((t,e)=>null===t?null:J(Math.round(t),0,e))(e=isFinite(e)&&i[e]===t?e:go(i,t,l(e,t),this._addedLabels),i.length-1)}determineDataLimits(){const{minDefined:t,maxDefined:e}=this.getUserBounds();let{min:i,max:s}=this.getMinMax(!0);"ticks"===this.options.bounds&&(t||(i=0),e||(s=this.getLabels().length-1)),this.min=i,this.max=s}buildTicks(){const t=this.min,e=this.max,i=this.options.offset,s=[];let n=this.getLabels();n=0===t&&e===n.length-1?n:n.slice(t,e+1),this._valueRange=Math.max(n.length-(i?0:1),1),this._startValue=this.min-(i?.5:0);for(let i=t;i<=e;i++)s.push({value:i});return s}getLabelForValue(t){return po.call(this,t)}configure(){super.configure(),this.isHorizontal()||(this._reversePixels=!this._reversePixels)}getPixelForValue(t){return"number"!=typeof t&&(t=this.parse(t)),null===t?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}getPixelForTick(t){const e=this.ticks;return t<0||t>e.length-1?null:this.getPixelForValue(e[t].value)}getValueForPixel(t){return Math.round(this._startValue+this.getDecimalForPixel(t)*this._valueRange)}getBasePixel(){return this.bottom}},LinearScale:bo,LogarithmicScale:ko,RadialLinearScale:Eo,TimeScale:No,TimeSeriesScale:class extends No{static id="timeseries";static defaults=No.defaults;constructor(t){super(t),this._table=[],this._minPos=void 0,this._tableRange=void 0}initOffsets(){const t=this._getTimestampsForTable(),e=this._table=this.buildLookupTable(t);this._minPos=Ho(e,this.min),this._tableRange=Ho(e,this.max)-this._minPos,super.initOffsets(t)}buildLookupTable(t){const{min:e,max:i}=this,s=[],n=[];let o,a,r,l,h;for(o=0,a=t.length;o<a;++o)l=t[o],l>=e&&l<=i&&s.push(l);if(s.length<2)return[{time:e,pos:0},{time:i,pos:1}];for(o=0,a=s.length;o<a;++o)h=s[o+1],r=s[o-1],l=s[o],Math.round((h+r)/2)!==l&&n.push({time:l,pos:o/(a-1)});return n}_generate(){const t=this.min,e=this.max;let i=super.getDataTimestamps();return i.includes(t)&&i.length||i.splice(0,0,t),i.includes(e)&&1!==i.length||i.push(e),i.sort(((t,e)=>t-e))}_getTimestampsForTable(){let t=this._cache.all||[];if(t.length)return t;const e=this.getDataTimestamps(),i=this.getLabelTimestamps();return t=e.length&&i.length?this.normalize(e.concat(i)):e.length?e:i,t=this._cache.all=t,t}getDecimalForValue(t){return(Ho(this._table,t)-this._minPos)/this._tableRange}getValueForPixel(t){const e=this._offsets,i=this.getDecimalForPixel(t)/e.factor-e.end;return Ho(this._table,i*this._tableRange+this._minPos,!0)}}});const $o=["rgb(54, 162, 235)","rgb(255, 99, 132)","rgb(255, 159, 64)","rgb(255, 205, 86)","rgb(75, 192, 192)","rgb(153, 102, 255)","rgb(201, 203, 207)"],Yo=$o.map((t=>t.replace("rgb(","rgba(").replace(")",", 0.5)")));function Uo(t){return $o[t%$o.length]}function Xo(t){return Yo[t%Yo.length]}function qo(t){let e=0;return(i,s)=>{const n=t.getDatasetMeta(s).controller;n instanceof jn?e=function(t,e){return t.backgroundColor=t.data.map((()=>Uo(e++))),e}(i,e):n instanceof $n?e=function(t,e){return t.backgroundColor=t.data.map((()=>Xo(e++))),e}(i,e):n&&(e=function(t,e){return t.borderColor=Uo(e),t.backgroundColor=Xo(e),++e}(i,e))}}function Ko(t){let e;for(e in t)if(t[e].borderColor||t[e].backgroundColor)return!0;return!1}var Go={id:"colors",defaults:{enabled:!0,forceOverride:!1},beforeLayout(t,e,i){if(!i.enabled)return;const{data:{datasets:s},options:n}=t.config,{elements:o}=n,a=Ko(s)||(r=n)&&(r.borderColor||r.backgroundColor)||o&&Ko(o)||"rgba(0,0,0,0.1)"!==ue.borderColor||"rgba(0,0,0,0.1)"!==ue.backgroundColor;var r;if(!i.forceOverride&&a)return;const l=qo(t);s.forEach(l)}};function Zo(t){if(t._decimated){const e=t._data;delete t._decimated,delete t._data,Object.defineProperty(t,"data",{configurable:!0,enumerable:!0,writable:!0,value:e})}}function Jo(t){t.data.datasets.forEach((t=>{Zo(t)}))}var Qo={id:"decimation",defaults:{algorithm:"min-max",enabled:!1},beforeElementsUpdate:(t,e,i)=>{if(!i.enabled)return void Jo(t);const n=t.width;t.data.datasets.forEach(((e,o)=>{const{_data:a,indexAxis:r}=e,l=t.getDatasetMeta(o),h=a||e.data;if("y"===Pi([r,t.options.indexAxis]))return;if(!l.controller.supportsDecimation)return;const c=t.scales[l.xAxisID];if("linear"!==c.type&&"time"!==c.type)return;if(t.options.parsing)return;let{start:d,count:u}=function(t,e){const i=e.length;let s,n=0;const{iScale:o}=t,{min:a,max:r,minDefined:l,maxDefined:h}=o.getUserBounds();return l&&(n=J(it(e,o.axis,a).lo,0,i-1)),s=h?J(it(e,o.axis,r).hi+1,n,i)-n:i-n,{start:n,count:s}}(l,h);if(u<=(i.threshold||4*n))return void Zo(e);let f;switch(s(a)&&(e._data=h,delete e.data,Object.defineProperty(e,"data",{configurable:!0,enumerable:!0,get:function(){return this._decimated},set:function(t){this._data=t}})),i.algorithm){case"lttb":f=function(t,e,i,s,n){const o=n.samples||s;if(o>=i)return t.slice(e,e+i);const a=[],r=(i-2)/(o-2);let l=0;const h=e+i-1;let c,d,u,f,g,p=e;for(a[l++]=t[p],c=0;c<o-2;c++){let s,n=0,o=0;const h=Math.floor((c+1)*r)+1+e,m=Math.min(Math.floor((c+2)*r)+1,i)+e,x=m-h;for(s=h;s<m;s++)n+=t[s].x,o+=t[s].y;n/=x,o/=x;const b=Math.floor(c*r)+1+e,_=Math.min(Math.floor((c+1)*r)+1,i)+e,{x:y,y:v}=t[p];for(u=f=-1,s=b;s<_;s++)f=.5*Math.abs((y-n)*(t[s].y-v)-(y-t[s].x)*(o-v)),f>u&&(u=f,d=t[s],g=s);a[l++]=d,p=g}return a[l++]=t[h],a}(h,d,u,n,i);break;case"min-max":f=function(t,e,i,n){let o,a,r,l,h,c,d,u,f,g,p=0,m=0;const x=[],b=e+i-1,_=t[e].x,y=t[b].x-_;for(o=e;o<e+i;++o){a=t[o],r=(a.x-_)/y*n,l=a.y;const e=0|r;if(e===h)l<f?(f=l,c=o):l>g&&(g=l,d=o),p=(m*p+a.x)/++m;else{const i=o-1;if(!s(c)&&!s(d)){const e=Math.min(c,d),s=Math.max(c,d);e!==u&&e!==i&&x.push({...t[e],x:p}),s!==u&&s!==i&&x.push({...t[s],x:p})}o>0&&i!==u&&x.push(t[i]),x.push(a),h=e,m=0,f=g=l,c=d=u=o}}return x}(h,d,u,n);break;default:throw new Error(`Unsupported decimation algorithm '${i.algorithm}'`)}e._decimated=f}))},destroy(t){Jo(t)}};function ta(t,e,i,s){if(s)return;let n=e[t],o=i[t];return"angle"===t&&(n=G(n),o=G(o)),{property:t,start:n,end:o}}function ea(t,e,i){for(;e>t;e--){const t=i[e];if(!isNaN(t.x)&&!isNaN(t.y))break}return e}function ia(t,e,i,s){return t&&e?s(t[i],e[i]):t?t[i]:e?e[i]:0}function sa(t,e){let i=[],s=!1;return n(t)?(s=!0,i=t):i=function(t,e){const{x:i=null,y:s=null}=t||{},n=e.points,o=[];return e.segments.forEach((({start:t,end:e})=>{e=ea(t,e,n);const a=n[t],r=n[e];null!==s?(o.push({x:a.x,y:s}),o.push({x:r.x,y:s})):null!==i&&(o.push({x:i,y:a.y}),o.push({x:i,y:r.y}))})),o}(t,e),i.length?new no({points:i,options:{tension:0},_loop:s,_fullLoop:s}):null}function na(t){return t&&!1!==t.fill}function oa(t,e,i){let s=t[e].fill;const n=[e];let o;if(!i)return s;for(;!1!==s&&-1===n.indexOf(s);){if(!a(s))return s;if(o=t[s],!o)return!1;if(o.visible)return s;n.push(s),s=o.fill}return!1}function aa(t,e,i){const s=function(t){const e=t.options,i=e.fill;let s=l(i&&i.target,i);void 0===s&&(s=!!e.backgroundColor);if(!1===s||null===s)return!1;if(!0===s)return"origin";return s}(t);if(o(s))return!isNaN(s.value)&&s;let n=parseFloat(s);return a(n)&&Math.floor(n)===n?function(t,e,i,s){"-"!==t&&"+"!==t||(i=e+i);if(i===e||i<0||i>=s)return!1;return i}(s[0],e,n,i):["origin","start","end","stack","shape"].indexOf(s)>=0&&s}function ra(t,e,i){const s=[];for(let n=0;n<i.length;n++){const o=i[n],{first:a,last:r,point:l}=la(o,e,"x");if(!(!l||a&&r))if(a)s.unshift(l);else if(t.push(l),!r)break}t.push(...s)}function la(t,e,i){const s=t.interpolate(e,i);if(!s)return{};const n=s[i],o=t.segments,a=t.points;let r=!1,l=!1;for(let t=0;t<o.length;t++){const e=o[t],s=a[e.start][i],h=a[e.end][i];if(tt(n,s,h)){r=n===s,l=n===h;break}}return{first:r,last:l,point:s}}class ha{constructor(t){this.x=t.x,this.y=t.y,this.radius=t.radius}pathSegment(t,e,i){const{x:s,y:n,radius:o}=this;return e=e||{start:0,end:O},t.arc(s,n,o,e.end,e.start,!0),!i.bounds}interpolate(t){const{x:e,y:i,radius:s}=this,n=t.angle;return{x:e+Math.cos(n)*s,y:i+Math.sin(n)*s,angle:n}}}function ca(t){const{chart:e,fill:i,line:s}=t;if(a(i))return function(t,e){const i=t.getDatasetMeta(e),s=i&&t.isDatasetVisible(e);return s?i.dataset:null}(e,i);if("stack"===i)return function(t){const{scale:e,index:i,line:s}=t,n=[],o=s.segments,a=s.points,r=function(t,e){const i=[],s=t.getMatchingVisibleMetas("line");for(let t=0;t<s.length;t++){const n=s[t];if(n.index===e)break;n.hidden||i.unshift(n.dataset)}return i}(e,i);r.push(sa({x:null,y:e.bottom},s));for(let t=0;t<o.length;t++){const e=o[t];for(let t=e.start;t<=e.end;t++)ra(n,a[t],r)}return new no({points:n,options:{}})}(t);if("shape"===i)return!0;const n=function(t){const e=t.scale||{};if(e.getPointPositionForValue)return function(t){const{scale:e,fill:i}=t,s=e.options,n=e.getLabels().length,a=s.reverse?e.max:e.min,r=function(t,e,i){let s;return s="start"===t?i:"end"===t?e.options.reverse?e.min:e.max:o(t)?t.value:e.getBaseValue(),s}(i,e,a),l=[];if(s.grid.circular){const t=e.getPointPositionForValue(0,a);return new ha({x:t.x,y:t.y,radius:e.getDistanceFromCenterForValue(r)})}for(let t=0;t<n;++t)l.push(e.getPointPositionForValue(t,r));return l}(t);return function(t){const{scale:e={},fill:i}=t,s=function(t,e){let i=null;return"start"===t?i=e.bottom:"end"===t?i=e.top:o(t)?i=e.getPixelForValue(t.value):e.getBasePixel&&(i=e.getBasePixel()),i}(i,e);if(a(s)){const t=e.isHorizontal();return{x:t?s:null,y:t?null:s}}return null}(t)}(t);return n instanceof ha?n:sa(n,s)}function da(t,e,i){const s=ca(e),{line:n,scale:o,axis:a}=e,r=n.options,l=r.fill,h=r.backgroundColor,{above:c=h,below:d=h}=l||{};s&&n.points.length&&(Ie(t,i),function(t,e){const{line:i,target:s,above:n,below:o,area:a,scale:r}=e,l=i._loop?"angle":e.axis;t.save(),"x"===l&&o!==n&&(ua(t,s,a.top),fa(t,{line:i,target:s,color:n,scale:r,property:l}),t.restore(),t.save(),ua(t,s,a.bottom));fa(t,{line:i,target:s,color:o,scale:r,property:l}),t.restore()}(t,{line:n,target:s,above:c,below:d,area:i,scale:o,axis:a}),ze(t))}function ua(t,e,i){const{segments:s,points:n}=e;let o=!0,a=!1;t.beginPath();for(const r of s){const{start:s,end:l}=r,h=n[s],c=n[ea(s,l,n)];o?(t.moveTo(h.x,h.y),o=!1):(t.lineTo(h.x,i),t.lineTo(h.x,h.y)),a=!!e.pathSegment(t,r,{move:a}),a?t.closePath():t.lineTo(c.x,i)}t.lineTo(e.first().x,i),t.closePath(),t.clip()}function fa(t,e){const{line:i,target:s,property:n,color:o,scale:a}=e,r=function(t,e,i){const s=t.segments,n=t.points,o=e.points,a=[];for(const t of s){let{start:s,end:r}=t;r=ea(s,r,n);const l=ta(i,n[s],n[r],t.loop);if(!e.segments){a.push({source:t,target:l,start:n[s],end:n[r]});continue}const h=Ii(e,l);for(const e of h){const s=ta(i,o[e.start],o[e.end],e.loop),r=Ri(t,n,s);for(const t of r)a.push({source:t,target:e,start:{[i]:ia(l,s,"start",Math.max)},end:{[i]:ia(l,s,"end",Math.min)}})}}return a}(i,s,n);for(const{source:e,target:l,start:h,end:c}of r){const{style:{backgroundColor:r=o}={}}=e,d=!0!==s;t.save(),t.fillStyle=r,ga(t,a,d&&ta(n,h,c)),t.beginPath();const u=!!i.pathSegment(t,e);let f;if(d){u?t.closePath():pa(t,s,c,n);const e=!!s.pathSegment(t,l,{move:u,reverse:!0});f=u&&e,f||pa(t,s,h,n)}t.closePath(),t.fill(f?"evenodd":"nonzero"),t.restore()}}function ga(t,e,i){const{top:s,bottom:n}=e.chart.chartArea,{property:o,start:a,end:r}=i||{};"x"===o&&(t.beginPath(),t.rect(a,s,r-a,n-s),t.clip())}function pa(t,e,i,s){const n=e.interpolate(i,s);n&&t.lineTo(n.x,n.y)}var ma={id:"filler",afterDatasetsUpdate(t,e,i){const s=(t.data.datasets||[]).length,n=[];let o,a,r,l;for(a=0;a<s;++a)o=t.getDatasetMeta(a),r=o.dataset,l=null,r&&r.options&&r instanceof no&&(l={visible:t.isDatasetVisible(a),index:a,fill:aa(r,a,s),chart:t,axis:o.controller.options.indexAxis,scale:o.vScale,line:r}),o.$filler=l,n.push(l);for(a=0;a<s;++a)l=n[a],l&&!1!==l.fill&&(l.fill=oa(n,a,i.propagate))},beforeDraw(t,e,i){const s="beforeDraw"===i.drawTime,n=t.getSortedVisibleDatasetMetas(),o=t.chartArea;for(let e=n.length-1;e>=0;--e){const i=n[e].$filler;i&&(i.line.updateControlPoints(o,i.axis),s&&i.fill&&da(t.ctx,i,o))}},beforeDatasetsDraw(t,e,i){if("beforeDatasetsDraw"!==i.drawTime)return;const s=t.getSortedVisibleDatasetMetas();for(let e=s.length-1;e>=0;--e){const i=s[e].$filler;na(i)&&da(t.ctx,i,t.chartArea)}},beforeDatasetDraw(t,e,i){const s=e.meta.$filler;na(s)&&"beforeDatasetDraw"===i.drawTime&&da(t.ctx,s,t.chartArea)},defaults:{propagate:!0,drawTime:"beforeDatasetDraw"}};const xa=(t,e)=>{let{boxHeight:i=e,boxWidth:s=e}=t;return t.usePointStyle&&(i=Math.min(i,e),s=t.pointStyleWidth||Math.min(s,e)),{boxWidth:s,boxHeight:i,itemHeight:Math.max(e,i)}};class ba extends Hs{constructor(t){super(),this._added=!1,this.legendHitBoxes=[],this._hoveredItem=null,this.doughnutMode=!1,this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this.legendItems=void 0,this.columnSizes=void 0,this.lineWidths=void 0,this.maxHeight=void 0,this.maxWidth=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.height=void 0,this.width=void 0,this._margins=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,e,i){this.maxWidth=t,this.maxHeight=e,this._margins=i,this.setDimensions(),this.buildLabels(),this.fit()}setDimensions(){this.isHorizontal()?(this.width=this.maxWidth,this.left=this._margins.left,this.right=this.width):(this.height=this.maxHeight,this.top=this._margins.top,this.bottom=this.height)}buildLabels(){const t=this.options.labels||{};let e=d(t.generateLabels,[this.chart],this)||[];t.filter&&(e=e.filter((e=>t.filter(e,this.chart.data)))),t.sort&&(e=e.sort(((e,i)=>t.sort(e,i,this.chart.data)))),this.options.reverse&&e.reverse(),this.legendItems=e}fit(){const{options:t,ctx:e}=this;if(!t.display)return void(this.width=this.height=0);const i=t.labels,s=Si(i.font),n=s.size,o=this._computeTitleHeight(),{boxWidth:a,itemHeight:r}=xa(i,n);let l,h;e.font=s.string,this.isHorizontal()?(l=this.maxWidth,h=this._fitRows(o,n,a,r)+10):(h=this.maxHeight,l=this._fitCols(o,s,a,r)+10),this.width=Math.min(l,t.maxWidth||this.maxWidth),this.height=Math.min(h,t.maxHeight||this.maxHeight)}_fitRows(t,e,i,s){const{ctx:n,maxWidth:o,options:{labels:{padding:a}}}=this,r=this.legendHitBoxes=[],l=this.lineWidths=[0],h=s+a;let c=t;n.textAlign="left",n.textBaseline="middle";let d=-1,u=-h;return this.legendItems.forEach(((t,f)=>{const g=i+e/2+n.measureText(t.text).width;(0===f||l[l.length-1]+g+2*a>o)&&(c+=h,l[l.length-(f>0?0:1)]=0,u+=h,d++),r[f]={left:0,top:u,row:d,width:g,height:s},l[l.length-1]+=g+a})),c}_fitCols(t,e,i,s){const{ctx:n,maxHeight:o,options:{labels:{padding:a}}}=this,r=this.legendHitBoxes=[],l=this.columnSizes=[],h=o-t;let c=a,d=0,u=0,f=0,g=0;return this.legendItems.forEach(((t,o)=>{const{itemWidth:p,itemHeight:m}=function(t,e,i,s,n){const o=function(t,e,i,s){let n=t.text;n&&"string"!=typeof n&&(n=n.reduce(((t,e)=>t.length>e.length?t:e)));return e+i.size/2+s.measureText(n).width}(s,t,e,i),a=function(t,e,i){let s=t;"string"!=typeof e.text&&(s=_a(e,i));return s}(n,s,e.lineHeight);return{itemWidth:o,itemHeight:a}}(i,e,n,t,s);o>0&&u+m+2*a>h&&(c+=d+a,l.push({width:d,height:u}),f+=d+a,g++,d=u=0),r[o]={left:f,top:u,col:g,width:p,height:m},d=Math.max(d,p),u+=m+a})),c+=d,l.push({width:d,height:u}),c}adjustHitBoxes(){if(!this.options.display)return;const t=this._computeTitleHeight(),{legendHitBoxes:e,options:{align:i,labels:{padding:s},rtl:n}}=this,o=Oi(n,this.left,this.width);if(this.isHorizontal()){let n=0,a=ft(i,this.left+s,this.right-this.lineWidths[n]);for(const r of e)n!==r.row&&(n=r.row,a=ft(i,this.left+s,this.right-this.lineWidths[n])),r.top+=this.top+t+s,r.left=o.leftForLtr(o.x(a),r.width),a+=r.width+s}else{let n=0,a=ft(i,this.top+t+s,this.bottom-this.columnSizes[n].height);for(const r of e)r.col!==n&&(n=r.col,a=ft(i,this.top+t+s,this.bottom-this.columnSizes[n].height)),r.top=a,r.left+=this.left+s,r.left=o.leftForLtr(o.x(r.left),r.width),a+=r.height+s}}isHorizontal(){return"top"===this.options.position||"bottom"===this.options.position}draw(){if(this.options.display){const t=this.ctx;Ie(t,this),this._draw(),ze(t)}}_draw(){const{options:t,columnSizes:e,lineWidths:i,ctx:s}=this,{align:n,labels:o}=t,a=ue.color,r=Oi(t.rtl,this.left,this.width),h=Si(o.font),{padding:c}=o,d=h.size,u=d/2;let f;this.drawTitle(),s.textAlign=r.textAlign("left"),s.textBaseline="middle",s.lineWidth=.5,s.font=h.string;const{boxWidth:g,boxHeight:p,itemHeight:m}=xa(o,d),x=this.isHorizontal(),b=this._computeTitleHeight();f=x?{x:ft(n,this.left+c,this.right-i[0]),y:this.top+c+b,line:0}:{x:this.left+c,y:ft(n,this.top+b+c,this.bottom-e[0].height),line:0},Ai(this.ctx,t.textDirection);const _=m+c;this.legendItems.forEach(((y,v)=>{s.strokeStyle=y.fontColor,s.fillStyle=y.fontColor;const M=s.measureText(y.text).width,w=r.textAlign(y.textAlign||(y.textAlign=o.textAlign)),k=g+u+M;let S=f.x,P=f.y;r.setWidth(this.width),x?v>0&&S+k+c>this.right&&(P=f.y+=_,f.line++,S=f.x=ft(n,this.left+c,this.right-i[f.line])):v>0&&P+_>this.bottom&&(S=f.x=S+e[f.line].width+c,f.line++,P=f.y=ft(n,this.top+b+c,this.bottom-e[f.line].height));if(function(t,e,i){if(isNaN(g)||g<=0||isNaN(p)||p<0)return;s.save();const n=l(i.lineWidth,1);if(s.fillStyle=l(i.fillStyle,a),s.lineCap=l(i.lineCap,"butt"),s.lineDashOffset=l(i.lineDashOffset,0),s.lineJoin=l(i.lineJoin,"miter"),s.lineWidth=n,s.strokeStyle=l(i.strokeStyle,a),s.setLineDash(l(i.lineDash,[])),o.usePointStyle){const a={radius:p*Math.SQRT2/2,pointStyle:i.pointStyle,rotation:i.rotation,borderWidth:n},l=r.xPlus(t,g/2);Ee(s,a,l,e+u,o.pointStyleWidth&&g)}else{const o=e+Math.max((d-p)/2,0),a=r.leftForLtr(t,g),l=wi(i.borderRadius);s.beginPath(),Object.values(l).some((t=>0!==t))?He(s,{x:a,y:o,w:g,h:p,radius:l}):s.rect(a,o,g,p),s.fill(),0!==n&&s.stroke()}s.restore()}(r.x(S),P,y),S=gt(w,S+g+u,x?S+k:this.right,t.rtl),function(t,e,i){Ne(s,i.text,t,e+m/2,h,{strikethrough:i.hidden,textAlign:r.textAlign(i.textAlign)})}(r.x(S),P,y),x)f.x+=k+c;else if("string"!=typeof y.text){const t=h.lineHeight;f.y+=_a(y,t)+c}else f.y+=_})),Ti(this.ctx,t.textDirection)}drawTitle(){const t=this.options,e=t.title,i=Si(e.font),s=ki(e.padding);if(!e.display)return;const n=Oi(t.rtl,this.left,this.width),o=this.ctx,a=e.position,r=i.size/2,l=s.top+r;let h,c=this.left,d=this.width;if(this.isHorizontal())d=Math.max(...this.lineWidths),h=this.top+l,c=ft(t.align,c,this.right-d);else{const e=this.columnSizes.reduce(((t,e)=>Math.max(t,e.height)),0);h=l+ft(t.align,this.top,this.bottom-e-t.labels.padding-this._computeTitleHeight())}const u=ft(a,c,c+d);o.textAlign=n.textAlign(ut(a)),o.textBaseline="middle",o.strokeStyle=e.color,o.fillStyle=e.color,o.font=i.string,Ne(o,e.text,u,h,i)}_computeTitleHeight(){const t=this.options.title,e=Si(t.font),i=ki(t.padding);return t.display?e.lineHeight+i.height:0}_getLegendItemAt(t,e){let i,s,n;if(tt(t,this.left,this.right)&&tt(e,this.top,this.bottom))for(n=this.legendHitBoxes,i=0;i<n.length;++i)if(s=n[i],tt(t,s.left,s.left+s.width)&&tt(e,s.top,s.top+s.height))return this.legendItems[i];return null}handleEvent(t){const e=this.options;if(!function(t,e){if(("mousemove"===t||"mouseout"===t)&&(e.onHover||e.onLeave))return!0;if(e.onClick&&("click"===t||"mouseup"===t))return!0;return!1}(t.type,e))return;const i=this._getLegendItemAt(t.x,t.y);if("mousemove"===t.type||"mouseout"===t.type){const o=this._hoveredItem,a=(n=i,null!==(s=o)&&null!==n&&s.datasetIndex===n.datasetIndex&&s.index===n.index);o&&!a&&d(e.onLeave,[t,o,this],this),this._hoveredItem=i,i&&!a&&d(e.onHover,[t,i,this],this)}else i&&d(e.onClick,[t,i,this],this);var s,n}}function _a(t,e){return e*(t.text?t.text.length:0)}var ya={id:"legend",_element:ba,start(t,e,i){const s=t.legend=new ba({ctx:t.ctx,options:i,chart:t});as.configure(t,s,i),as.addBox(t,s)},stop(t){as.removeBox(t,t.legend),delete t.legend},beforeUpdate(t,e,i){const s=t.legend;as.configure(t,s,i),s.options=i},afterUpdate(t){const e=t.legend;e.buildLabels(),e.adjustHitBoxes()},afterEvent(t,e){e.replay||t.legend.handleEvent(e.event)},defaults:{display:!0,position:"top",align:"center",fullSize:!0,reverse:!1,weight:1e3,onClick(t,e,i){const s=e.datasetIndex,n=i.chart;n.isDatasetVisible(s)?(n.hide(s),e.hidden=!0):(n.show(s),e.hidden=!1)},onHover:null,onLeave:null,labels:{color:t=>t.chart.options.color,boxWidth:40,padding:10,generateLabels(t){const e=t.data.datasets,{labels:{usePointStyle:i,pointStyle:s,textAlign:n,color:o,useBorderRadius:a,borderRadius:r}}=t.legend.options;return t._getSortedDatasetMetas().map((t=>{const l=t.controller.getStyle(i?0:void 0),h=ki(l.borderWidth);return{text:e[t.index].label,fillStyle:l.backgroundColor,fontColor:o,hidden:!t.visible,lineCap:l.borderCapStyle,lineDash:l.borderDash,lineDashOffset:l.borderDashOffset,lineJoin:l.borderJoinStyle,lineWidth:(h.width+h.height)/4,strokeStyle:l.borderColor,pointStyle:s||l.pointStyle,rotation:l.rotation,textAlign:n||l.textAlign,borderRadius:a&&(r||l.borderRadius),datasetIndex:t.index}}),this)}},title:{color:t=>t.chart.options.color,display:!1,position:"center",text:""}},descriptors:{_scriptable:t=>!t.startsWith("on"),labels:{_scriptable:t=>!["generateLabels","filter","sort"].includes(t)}}};class va extends Hs{constructor(t){super(),this.chart=t.chart,this.options=t.options,this.ctx=t.ctx,this._padding=void 0,this.top=void 0,this.bottom=void 0,this.left=void 0,this.right=void 0,this.width=void 0,this.height=void 0,this.position=void 0,this.weight=void 0,this.fullSize=void 0}update(t,e){const i=this.options;if(this.left=0,this.top=0,!i.display)return void(this.width=this.height=this.right=this.bottom=0);this.width=this.right=t,this.height=this.bottom=e;const s=n(i.text)?i.text.length:1;this._padding=ki(i.padding);const o=s*Si(i.font).lineHeight+this._padding.height;this.isHorizontal()?this.height=o:this.width=o}isHorizontal(){const t=this.options.position;return"top"===t||"bottom"===t}_drawArgs(t){const{top:e,left:i,bottom:s,right:n,options:o}=this,a=o.align;let r,l,h,c=0;return this.isHorizontal()?(l=ft(a,i,n),h=e+t,r=n-i):("left"===o.position?(l=i+t,h=ft(a,s,e),c=-.5*C):(l=n-t,h=ft(a,e,s),c=.5*C),r=s-e),{titleX:l,titleY:h,maxWidth:r,rotation:c}}draw(){const t=this.ctx,e=this.options;if(!e.display)return;const i=Si(e.font),s=i.lineHeight/2+this._padding.top,{titleX:n,titleY:o,maxWidth:a,rotation:r}=this._drawArgs(s);Ne(t,e.text,0,0,i,{color:e.color,maxWidth:a,rotation:r,textAlign:ut(e.align),textBaseline:"middle",translation:[n,o]})}}var Ma={id:"title",_element:va,start(t,e,i){!function(t,e){const i=new va({ctx:t.ctx,options:e,chart:t});as.configure(t,i,e),as.addBox(t,i),t.titleBlock=i}(t,i)},stop(t){const e=t.titleBlock;as.removeBox(t,e),delete t.titleBlock},beforeUpdate(t,e,i){const s=t.titleBlock;as.configure(t,s,i),s.options=i},defaults:{align:"center",display:!1,font:{weight:"bold"},fullSize:!0,padding:10,position:"top",text:"",weight:2e3},defaultRoutes:{color:"color"},descriptors:{_scriptable:!0,_indexable:!1}};const wa=new WeakMap;var ka={id:"subtitle",start(t,e,i){const s=new va({ctx:t.ctx,options:i,chart:t});as.configure(t,s,i),as.addBox(t,s),wa.set(t,s)},stop(t){as.removeBox(t,wa.get(t)),wa.delete(t)},beforeUpdate(t,e,i){const s=wa.get(t);as.configure(t,s,i),s.options=i},defaults:{align:"center",display:!1,font:{weight:"normal"},fullSize:!0,padding:0,position:"top",text:"",weight:1500},defaultRoutes:{color:"color"},descriptors:{_scriptable:!0,_indexable:!1}};const Sa={average(t){if(!t.length)return!1;let e,i,s=new Set,n=0,o=0;for(e=0,i=t.length;e<i;++e){const i=t[e].element;if(i&&i.hasValue()){const t=i.tooltipPosition();s.add(t.x),n+=t.y,++o}}if(0===o||0===s.size)return!1;return{x:[...s].reduce(((t,e)=>t+e))/s.size,y:n/o}},nearest(t,e){if(!t.length)return!1;let i,s,n,o=e.x,a=e.y,r=Number.POSITIVE_INFINITY;for(i=0,s=t.length;i<s;++i){const s=t[i].element;if(s&&s.hasValue()){const t=q(e,s.getCenterPoint());t<r&&(r=t,n=s)}}if(n){const t=n.tooltipPosition();o=t.x,a=t.y}return{x:o,y:a}}};function Pa(t,e){return e&&(n(e)?Array.prototype.push.apply(t,e):t.push(e)),t}function Da(t){return("string"==typeof t||t instanceof String)&&t.indexOf("\n")>-1?t.split("\n"):t}function Ca(t,e){const{element:i,datasetIndex:s,index:n}=e,o=t.getDatasetMeta(s).controller,{label:a,value:r}=o.getLabelAndValue(n);return{chart:t,label:a,parsed:o.getParsed(n),raw:t.data.datasets[s].data[n],formattedValue:r,dataset:o.getDataset(),dataIndex:n,datasetIndex:s,element:i}}function Oa(t,e){const i=t.chart.ctx,{body:s,footer:n,title:o}=t,{boxWidth:a,boxHeight:r}=e,l=Si(e.bodyFont),h=Si(e.titleFont),c=Si(e.footerFont),d=o.length,f=n.length,g=s.length,p=ki(e.padding);let m=p.height,x=0,b=s.reduce(((t,e)=>t+e.before.length+e.lines.length+e.after.length),0);if(b+=t.beforeBody.length+t.afterBody.length,d&&(m+=d*h.lineHeight+(d-1)*e.titleSpacing+e.titleMarginBottom),b){m+=g*(e.displayColors?Math.max(r,l.lineHeight):l.lineHeight)+(b-g)*l.lineHeight+(b-1)*e.bodySpacing}f&&(m+=e.footerMarginTop+f*c.lineHeight+(f-1)*e.footerSpacing);let _=0;const y=function(t){x=Math.max(x,i.measureText(t).width+_)};return i.save(),i.font=h.string,u(t.title,y),i.font=l.string,u(t.beforeBody.concat(t.afterBody),y),_=e.displayColors?a+2+e.boxPadding:0,u(s,(t=>{u(t.before,y),u(t.lines,y),u(t.after,y)})),_=0,i.font=c.string,u(t.footer,y),i.restore(),x+=p.width,{width:x,height:m}}function Aa(t,e,i,s){const{x:n,width:o}=i,{width:a,chartArea:{left:r,right:l}}=t;let h="center";return"center"===s?h=n<=(r+l)/2?"left":"right":n<=o/2?h="left":n>=a-o/2&&(h="right"),function(t,e,i,s){const{x:n,width:o}=s,a=i.caretSize+i.caretPadding;return"left"===t&&n+o+a>e.width||"right"===t&&n-o-a<0||void 0}(h,t,e,i)&&(h="center"),h}function Ta(t,e,i){const s=i.yAlign||e.yAlign||function(t,e){const{y:i,height:s}=e;return i<s/2?"top":i>t.height-s/2?"bottom":"center"}(t,i);return{xAlign:i.xAlign||e.xAlign||Aa(t,e,i,s),yAlign:s}}function La(t,e,i,s){const{caretSize:n,caretPadding:o,cornerRadius:a}=t,{xAlign:r,yAlign:l}=i,h=n+o,{topLeft:c,topRight:d,bottomLeft:u,bottomRight:f}=wi(a);let g=function(t,e){let{x:i,width:s}=t;return"right"===e?i-=s:"center"===e&&(i-=s/2),i}(e,r);const p=function(t,e,i){let{y:s,height:n}=t;return"top"===e?s+=i:s-="bottom"===e?n+i:n/2,s}(e,l,h);return"center"===l?"left"===r?g+=h:"right"===r&&(g-=h):"left"===r?g-=Math.max(c,u)+n:"right"===r&&(g+=Math.max(d,f)+n),{x:J(g,0,s.width-e.width),y:J(p,0,s.height-e.height)}}function Ea(t,e,i){const s=ki(i.padding);return"center"===e?t.x+t.width/2:"right"===e?t.x+t.width-s.right:t.x+s.left}function Ra(t){return Pa([],Da(t))}function Ia(t,e){const i=e&&e.dataset&&e.dataset.tooltip&&e.dataset.tooltip.callbacks;return i?t.override(i):t}const za={beforeTitle:e,title(t){if(t.length>0){const e=t[0],i=e.chart.data.labels,s=i?i.length:0;if(this&&this.options&&"dataset"===this.options.mode)return e.dataset.label||"";if(e.label)return e.label;if(s>0&&e.dataIndex<s)return i[e.dataIndex]}return""},afterTitle:e,beforeBody:e,beforeLabel:e,label(t){if(this&&this.options&&"dataset"===this.options.mode)return t.label+": "+t.formattedValue||t.formattedValue;let e=t.dataset.label||"";e&&(e+=": ");const i=t.formattedValue;return s(i)||(e+=i),e},labelColor(t){const e=t.chart.getDatasetMeta(t.datasetIndex).controller.getStyle(t.dataIndex);return{borderColor:e.borderColor,backgroundColor:e.backgroundColor,borderWidth:e.borderWidth,borderDash:e.borderDash,borderDashOffset:e.borderDashOffset,borderRadius:0}},labelTextColor(){return this.options.bodyColor},labelPointStyle(t){const e=t.chart.getDatasetMeta(t.datasetIndex).controller.getStyle(t.dataIndex);return{pointStyle:e.pointStyle,rotation:e.rotation}},afterLabel:e,afterBody:e,beforeFooter:e,footer:e,afterFooter:e};function Fa(t,e,i,s){const n=t[e].call(i,s);return void 0===n?za[e].call(i,s):n}class Va extends Hs{static positioners=Sa;constructor(t){super(),this.opacity=0,this._active=[],this._eventPosition=void 0,this._size=void 0,this._cachedAnimations=void 0,this._tooltipItems=[],this.$animations=void 0,this.$context=void 0,this.chart=t.chart,this.options=t.options,this.dataPoints=void 0,this.title=void 0,this.beforeBody=void 0,this.body=void 0,this.afterBody=void 0,this.footer=void 0,this.xAlign=void 0,this.yAlign=void 0,this.x=void 0,this.y=void 0,this.height=void 0,this.width=void 0,this.caretX=void 0,this.caretY=void 0,this.labelColors=void 0,this.labelPointStyles=void 0,this.labelTextColors=void 0}initialize(t){this.options=t,this._cachedAnimations=void 0,this.$context=void 0}_resolveAnimations(){const t=this._cachedAnimations;if(t)return t;const e=this.chart,i=this.options.setContext(this.getContext()),s=i.enabled&&e.options.animation&&i.animations,n=new Os(this.chart,s);return s._cacheable&&(this._cachedAnimations=Object.freeze(n)),n}getContext(){return this.$context||(this.$context=(t=this.chart.getContext(),e=this,i=this._tooltipItems,Ci(t,{tooltip:e,tooltipItems:i,type:"tooltip"})));var t,e,i}getTitle(t,e){const{callbacks:i}=e,s=Fa(i,"beforeTitle",this,t),n=Fa(i,"title",this,t),o=Fa(i,"afterTitle",this,t);let a=[];return a=Pa(a,Da(s)),a=Pa(a,Da(n)),a=Pa(a,Da(o)),a}getBeforeBody(t,e){return Ra(Fa(e.callbacks,"beforeBody",this,t))}getBody(t,e){const{callbacks:i}=e,s=[];return u(t,(t=>{const e={before:[],lines:[],after:[]},n=Ia(i,t);Pa(e.before,Da(Fa(n,"beforeLabel",this,t))),Pa(e.lines,Fa(n,"label",this,t)),Pa(e.after,Da(Fa(n,"afterLabel",this,t))),s.push(e)})),s}getAfterBody(t,e){return Ra(Fa(e.callbacks,"afterBody",this,t))}getFooter(t,e){const{callbacks:i}=e,s=Fa(i,"beforeFooter",this,t),n=Fa(i,"footer",this,t),o=Fa(i,"afterFooter",this,t);let a=[];return a=Pa(a,Da(s)),a=Pa(a,Da(n)),a=Pa(a,Da(o)),a}_createItems(t){const e=this._active,i=this.chart.data,s=[],n=[],o=[];let a,r,l=[];for(a=0,r=e.length;a<r;++a)l.push(Ca(this.chart,e[a]));return t.filter&&(l=l.filter(((e,s,n)=>t.filter(e,s,n,i)))),t.itemSort&&(l=l.sort(((e,s)=>t.itemSort(e,s,i)))),u(l,(e=>{const i=Ia(t.callbacks,e);s.push(Fa(i,"labelColor",this,e)),n.push(Fa(i,"labelPointStyle",this,e)),o.push(Fa(i,"labelTextColor",this,e))})),this.labelColors=s,this.labelPointStyles=n,this.labelTextColors=o,this.dataPoints=l,l}update(t,e){const i=this.options.setContext(this.getContext()),s=this._active;let n,o=[];if(s.length){const t=Sa[i.position].call(this,s,this._eventPosition);o=this._createItems(i),this.title=this.getTitle(o,i),this.beforeBody=this.getBeforeBody(o,i),this.body=this.getBody(o,i),this.afterBody=this.getAfterBody(o,i),this.footer=this.getFooter(o,i);const e=this._size=Oa(this,i),a=Object.assign({},t,e),r=Ta(this.chart,i,a),l=La(i,a,r,this.chart);this.xAlign=r.xAlign,this.yAlign=r.yAlign,n={opacity:1,x:l.x,y:l.y,width:e.width,height:e.height,caretX:t.x,caretY:t.y}}else 0!==this.opacity&&(n={opacity:0});this._tooltipItems=o,this.$context=void 0,n&&this._resolveAnimations().update(this,n),t&&i.external&&i.external.call(this,{chart:this.chart,tooltip:this,replay:e})}drawCaret(t,e,i,s){const n=this.getCaretPosition(t,i,s);e.lineTo(n.x1,n.y1),e.lineTo(n.x2,n.y2),e.lineTo(n.x3,n.y3)}getCaretPosition(t,e,i){const{xAlign:s,yAlign:n}=this,{caretSize:o,cornerRadius:a}=i,{topLeft:r,topRight:l,bottomLeft:h,bottomRight:c}=wi(a),{x:d,y:u}=t,{width:f,height:g}=e;let p,m,x,b,_,y;return"center"===n?(_=u+g/2,"left"===s?(p=d,m=p-o,b=_+o,y=_-o):(p=d+f,m=p+o,b=_-o,y=_+o),x=p):(m="left"===s?d+Math.max(r,h)+o:"right"===s?d+f-Math.max(l,c)-o:this.caretX,"top"===n?(b=u,_=b-o,p=m-o,x=m+o):(b=u+g,_=b+o,p=m+o,x=m-o),y=b),{x1:p,x2:m,x3:x,y1:b,y2:_,y3:y}}drawTitle(t,e,i){const s=this.title,n=s.length;let o,a,r;if(n){const l=Oi(i.rtl,this.x,this.width);for(t.x=Ea(this,i.titleAlign,i),e.textAlign=l.textAlign(i.titleAlign),e.textBaseline="middle",o=Si(i.titleFont),a=i.titleSpacing,e.fillStyle=i.titleColor,e.font=o.string,r=0;r<n;++r)e.fillText(s[r],l.x(t.x),t.y+o.lineHeight/2),t.y+=o.lineHeight+a,r+1===n&&(t.y+=i.titleMarginBottom-a)}}_drawColorBox(t,e,i,s,n){const a=this.labelColors[i],r=this.labelPointStyles[i],{boxHeight:l,boxWidth:h}=n,c=Si(n.bodyFont),d=Ea(this,"left",n),u=s.x(d),f=l<c.lineHeight?(c.lineHeight-l)/2:0,g=e.y+f;if(n.usePointStyle){const e={radius:Math.min(h,l)/2,pointStyle:r.pointStyle,rotation:r.rotation,borderWidth:1},i=s.leftForLtr(u,h)+h/2,o=g+l/2;t.strokeStyle=n.multiKeyBackground,t.fillStyle=n.multiKeyBackground,Le(t,e,i,o),t.strokeStyle=a.borderColor,t.fillStyle=a.backgroundColor,Le(t,e,i,o)}else{t.lineWidth=o(a.borderWidth)?Math.max(...Object.values(a.borderWidth)):a.borderWidth||1,t.strokeStyle=a.borderColor,t.setLineDash(a.borderDash||[]),t.lineDashOffset=a.borderDashOffset||0;const e=s.leftForLtr(u,h),i=s.leftForLtr(s.xPlus(u,1),h-2),r=wi(a.borderRadius);Object.values(r).some((t=>0!==t))?(t.beginPath(),t.fillStyle=n.multiKeyBackground,He(t,{x:e,y:g,w:h,h:l,radius:r}),t.fill(),t.stroke(),t.fillStyle=a.backgroundColor,t.beginPath(),He(t,{x:i,y:g+1,w:h-2,h:l-2,radius:r}),t.fill()):(t.fillStyle=n.multiKeyBackground,t.fillRect(e,g,h,l),t.strokeRect(e,g,h,l),t.fillStyle=a.backgroundColor,t.fillRect(i,g+1,h-2,l-2))}t.fillStyle=this.labelTextColors[i]}drawBody(t,e,i){const{body:s}=this,{bodySpacing:n,bodyAlign:o,displayColors:a,boxHeight:r,boxWidth:l,boxPadding:h}=i,c=Si(i.bodyFont);let d=c.lineHeight,f=0;const g=Oi(i.rtl,this.x,this.width),p=function(i){e.fillText(i,g.x(t.x+f),t.y+d/2),t.y+=d+n},m=g.textAlign(o);let x,b,_,y,v,M,w;for(e.textAlign=o,e.textBaseline="middle",e.font=c.string,t.x=Ea(this,m,i),e.fillStyle=i.bodyColor,u(this.beforeBody,p),f=a&&"right"!==m?"center"===o?l/2+h:l+2+h:0,y=0,M=s.length;y<M;++y){for(x=s[y],b=this.labelTextColors[y],e.fillStyle=b,u(x.before,p),_=x.lines,a&&_.length&&(this._drawColorBox(e,t,y,g,i),d=Math.max(c.lineHeight,r)),v=0,w=_.length;v<w;++v)p(_[v]),d=c.lineHeight;u(x.after,p)}f=0,d=c.lineHeight,u(this.afterBody,p),t.y-=n}drawFooter(t,e,i){const s=this.footer,n=s.length;let o,a;if(n){const r=Oi(i.rtl,this.x,this.width);for(t.x=Ea(this,i.footerAlign,i),t.y+=i.footerMarginTop,e.textAlign=r.textAlign(i.footerAlign),e.textBaseline="middle",o=Si(i.footerFont),e.fillStyle=i.footerColor,e.font=o.string,a=0;a<n;++a)e.fillText(s[a],r.x(t.x),t.y+o.lineHeight/2),t.y+=o.lineHeight+i.footerSpacing}}drawBackground(t,e,i,s){const{xAlign:n,yAlign:o}=this,{x:a,y:r}=t,{width:l,height:h}=i,{topLeft:c,topRight:d,bottomLeft:u,bottomRight:f}=wi(s.cornerRadius);e.fillStyle=s.backgroundColor,e.strokeStyle=s.borderColor,e.lineWidth=s.borderWidth,e.beginPath(),e.moveTo(a+c,r),"top"===o&&this.drawCaret(t,e,i,s),e.lineTo(a+l-d,r),e.quadraticCurveTo(a+l,r,a+l,r+d),"center"===o&&"right"===n&&this.drawCaret(t,e,i,s),e.lineTo(a+l,r+h-f),e.quadraticCurveTo(a+l,r+h,a+l-f,r+h),"bottom"===o&&this.drawCaret(t,e,i,s),e.lineTo(a+u,r+h),e.quadraticCurveTo(a,r+h,a,r+h-u),"center"===o&&"left"===n&&this.drawCaret(t,e,i,s),e.lineTo(a,r+c),e.quadraticCurveTo(a,r,a+c,r),e.closePath(),e.fill(),s.borderWidth>0&&e.stroke()}_updateAnimationTarget(t){const e=this.chart,i=this.$animations,s=i&&i.x,n=i&&i.y;if(s||n){const i=Sa[t.position].call(this,this._active,this._eventPosition);if(!i)return;const o=this._size=Oa(this,t),a=Object.assign({},i,this._size),r=Ta(e,t,a),l=La(t,a,r,e);s._to===l.x&&n._to===l.y||(this.xAlign=r.xAlign,this.yAlign=r.yAlign,this.width=o.width,this.height=o.height,this.caretX=i.x,this.caretY=i.y,this._resolveAnimations().update(this,l))}}_willRender(){return!!this.opacity}draw(t){const e=this.options.setContext(this.getContext());let i=this.opacity;if(!i)return;this._updateAnimationTarget(e);const s={width:this.width,height:this.height},n={x:this.x,y:this.y};i=Math.abs(i)<.001?0:i;const o=ki(e.padding),a=this.title.length||this.beforeBody.length||this.body.length||this.afterBody.length||this.footer.length;e.enabled&&a&&(t.save(),t.globalAlpha=i,this.drawBackground(n,t,s,e),Ai(t,e.textDirection),n.y+=o.top,this.drawTitle(n,t,e),this.drawBody(n,t,e),this.drawFooter(n,t,e),Ti(t,e.textDirection),t.restore())}getActiveElements(){return this._active||[]}setActiveElements(t,e){const i=this._active,s=t.map((({datasetIndex:t,index:e})=>{const i=this.chart.getDatasetMeta(t);if(!i)throw new Error("Cannot find a dataset at index "+t);return{datasetIndex:t,element:i.data[e],index:e}})),n=!f(i,s),o=this._positionChanged(s,e);(n||o)&&(this._active=s,this._eventPosition=e,this._ignoreReplayEvents=!0,this.update(!0))}handleEvent(t,e,i=!0){if(e&&this._ignoreReplayEvents)return!1;this._ignoreReplayEvents=!1;const s=this.options,n=this._active||[],o=this._getActiveElements(t,n,e,i),a=this._positionChanged(o,t),r=e||!f(o,n)||a;return r&&(this._active=o,(s.enabled||s.external)&&(this._eventPosition={x:t.x,y:t.y},this.update(!0,e))),r}_getActiveElements(t,e,i,s){const n=this.options;if("mouseout"===t.type)return[];if(!s)return e.filter((t=>this.chart.data.datasets[t.datasetIndex]&&void 0!==this.chart.getDatasetMeta(t.datasetIndex).controller.getParsed(t.index)));const o=this.chart.getElementsAtEventForMode(t,n.mode,n,i);return n.reverse&&o.reverse(),o}_positionChanged(t,e){const{caretX:i,caretY:s,options:n}=this,o=Sa[n.position].call(this,t,e);return!1!==o&&(i!==o.x||s!==o.y)}}var Ba={id:"tooltip",_element:Va,positioners:Sa,afterInit(t,e,i){i&&(t.tooltip=new Va({chart:t,options:i}))},beforeUpdate(t,e,i){t.tooltip&&t.tooltip.initialize(i)},reset(t,e,i){t.tooltip&&t.tooltip.initialize(i)},afterDraw(t){const e=t.tooltip;if(e&&e._willRender()){const i={tooltip:e};if(!1===t.notifyPlugins("beforeTooltipDraw",{...i,cancelable:!0}))return;e.draw(t.ctx),t.notifyPlugins("afterTooltipDraw",i)}},afterEvent(t,e){if(t.tooltip){const i=e.replay;t.tooltip.handleEvent(e.event,i,e.inChartArea)&&(e.changed=!0)}},defaults:{enabled:!0,external:null,position:"average",backgroundColor:"rgba(0,0,0,0.8)",titleColor:"#fff",titleFont:{weight:"bold"},titleSpacing:2,titleMarginBottom:6,titleAlign:"left",bodyColor:"#fff",bodySpacing:2,bodyFont:{},bodyAlign:"left",footerColor:"#fff",footerSpacing:2,footerMarginTop:6,footerFont:{weight:"bold"},footerAlign:"left",padding:6,caretPadding:2,caretSize:5,cornerRadius:6,boxHeight:(t,e)=>e.bodyFont.size,boxWidth:(t,e)=>e.bodyFont.size,multiKeyBackground:"#fff",displayColors:!0,boxPadding:0,borderColor:"rgba(0,0,0,0)",borderWidth:0,animation:{duration:400,easing:"easeOutQuart"},animations:{numbers:{type:"number",properties:["x","y","width","height","caretX","caretY"]},opacity:{easing:"linear",duration:200}},callbacks:za},defaultRoutes:{bodyFont:"font",footerFont:"font",titleFont:"font"},descriptors:{_scriptable:t=>"filter"!==t&&"itemSort"!==t&&"external"!==t,_indexable:!1,callbacks:{_scriptable:!1,_indexable:!1},animation:{_fallback:!1},animations:{_fallback:"animation"}},additionalOptionScopes:["interaction"]};return An.register(Yn,jo,fo,t),An.helpers={...Wi},An._adapters=Rn,An.Animation=Cs,An.Animations=Os,An.animator=bt,An.controllers=en.controllers.items,An.DatasetController=Ns,An.Element=Hs,An.elements=fo,An.Interaction=Xi,An.layouts=as,An.platforms=Ss,An.Scale=Js,An.Ticks=ae,Object.assign(An,Yn,jo,fo,t,Ss),An.Chart=An,"undefined"!=typeof window&&(window.Chart=An),An}));
````

## package.json

````json
{"name":"predictpro","version":"1.0.0","private":true,"type":"module","scripts":{"dev":"python -m backend.preview","check":"python scripts/check_frontend.py","test":"python -m pytest backend/tests -q"}}
````

## requirements.txt

````text
fastapi==0.162.0
uvicorn==0.54.0
SQLAlchemy==2.1.6
alembic==1.20.1
PyJWT==2.15.1
bcrypt==5.0.0
python-dotenv==1.2.4
httpx[socks]==0.28.1
email-validator==2.3.0
pytest==9.2.0
````

## scripts/check_frontend.py

````python
"""Syntax-check all first-party browser modules using Node 20+ (optional)."""

import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = [p for p in (root / "frontend").rglob("*.js") if "vendor" not in p.parts]
for p in files:
    subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=p.read_text(),
        text=True,
        check=True,
    )
print(f"{len(files)} JavaScript modules passed syntax checks.")
````

## scripts/init_env.py

````python
"""Create local configuration once without overwriting existing secrets."""

from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env already exists; leaving it unchanged.")
else:
    content = (
        (root / ".env.example")
        .read_text()
        .replace("JWT_SECRET=\n", "JWT_SECRET=" + secrets.token_hex(32) + "\n")
    )
    target.write_text(content)
    target.chmod(0o600)
    print(
        "Created .env with a fresh signing secret. Review configuration before production."
    )
````
