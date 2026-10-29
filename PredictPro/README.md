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
