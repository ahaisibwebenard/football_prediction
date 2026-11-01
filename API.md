# PredictPro API reference

Base path `/api`. JSON request and response bodies. Cookies are same-origin and httpOnly. Login/signup responses and `GET /auth/me` return a session-bound `csrf` token. Send it in `X-CSRF-Token` for every authenticated POST, PUT or DELETE. Use the exact configured Origin if sending an Origin header. Public authentication writes require `Content-Type: application/json`.

Errors use `{"detail":"message"}` or a validation array of `loc`/`msg`. Status codes: 201 created; 400 invalid recovery/current password; 401 unauthenticated; 403 role/CSRF/account restriction; 404 missing record; 409 conflict/deadline/foreign key; 413 oversized declared body; 415 wrong content type; 422 validation; 429 rate limited; 503 maintenance.

## Public and authentication

| Method | Path | Request / purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/site` | Site name and whether live football data is configured; no secrets |
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
| GET | `/catalog` | Country-sorted leagues (with country), teams and account's favorite flags |
| GET | `/matches` | Filters: `league`, `date` (UTC YYYY-MM-DD), `team`, `search`, `status` (SCHEDULED/FINISHED/ALL), `limit` (1–100), `offset`; returns `{items,total}` |
| GET | `/matches/{id}` | Match, stored prediction and prior head-to-head |
| GET | `/predictions/top` | Top 10 upcoming provider-sourced fixtures, ranked by each fixture's strongest estimated result/goals market |
| POST | `/matches/{id}/pick` | `{outcome:"Home"}` or Draw/Away; update until kickoff |
| POST | `/matches/{id}/follow` | Toggle following; new follows close at kickoff |
| POST | `/favorites/{team_id}` | Toggle favorite |
| GET | `/history` | Stored predictions; 50 per page, `offset` |
| GET | `/leaderboard` | 3 points per correct completed outcome; AI source rows separate |
| GET | `/notifications` | Latest 100 account notifications |
| POST | `/notifications/{id}/read` | Mark an owned notification read |
| GET | `/metrics` | Source-separated accuracy, Brier loss and prospective trend |

Match timestamps returned by the API are UTC without an offset suffix; the supplied frontend appends `Z` before converting to local time. Match writes require an explicit timezone, such as `2026-11-01T15:00:00Z`. Form guides are oldest-to-newest. Probability fields are numbers in [0,1], not percentages. Stored forecasts include 1X2, expected goals, modal score probability, goal lines, and both-teams-to-score probabilities. Corner probabilities are not available because the configured provider does not supply historical corner counts. Notifications are generated during result ingestion or administrator result entry.

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
| POST | `/admin/sync` | Import configured competitions; reports unavailable data without synthetic fallback |
| POST | `/admin/retrain` | Walk-forward Elo multiplier calibration |
| GET | `/admin/settings` | Site name, maintenance, API-key configured flag |
| PUT | `/admin/settings` | `{site_name,maintenance,api_key?}`; omit key to retain, empty string to disable |
| POST / PUT | `/admin/leagues` / `/admin/leagues/{id}` | `{name,code,country?}` |
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
