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
| Outcome probabilities, xG, exact scoreline probability, goal lines and BTTS | Yes | Probability normalization/bounds tested; numbers accompany charts |
| Confidence labels and plain-English explanations | Yes | Service tests verify explanation and sparse-data confidence |
| Provider ingestion without synthetic fallback | Yes | Mocked live import/deduplication and unavailable-provider tests; no live credentials used |
| Stored predictions and honest accuracy history | Yes | Frozen snapshot, eligibility and source separation tests |
| Football-data disclaimers | Yes | Auth, navigation, footer, match explanations and README |
| Dashboard league/date/team/search filters | Yes | API filters tested; browser interaction unverified |
| Country-labeled competitions | Yes | Country/area imported from provider, persisted through migration, shown in filters and admin catalogue |
| Hottest 10 live prediction page | Yes | Ranked from upcoming provider fixtures and strongest model markets; browser visual check pending |
| Match details, Chart.js chart, form and H2H | Yes | Data service covered; chart syntax/assets checked, browser rendering unverified |
| Prediction history | Yes | History endpoint covered; 50-record pagination |
| Favorite teams | Yes | Toggle and persistence tested |
| System-only match and goals forecasts | Yes | Daily top-ten endpoint ranks unique fixtures and shows result, goal-line, BTTS and score probabilities |
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
| Automated auth/role/model tests | Yes | See VERIFICATION.md for confirmed focused checks and the full-suite command |
| Deployment instructions | Yes | Render/Railway persistent-volume instructions; Vercel limitation explained; no deployment created |

## Local browser walkthrough

1. Start the app using README instructions. At http://localhost:8000 sign in as admin/benard and confirm access is blocked until the password changes.
2. Set a new administrator password. Open Match center. Switch theme, resize to phone/tablet/desktop widths and operate the mobile menu using keyboard and pointer.
3. After configuring the football-data.org API key and waiting for sync, filter by country, live league, team and UTC date. Open a match and compare the numerical probabilities with its Chart.js bars. Inspect goal lines, form, earlier meetings and the full explanation.
4. Open **Hottest 10**. Verify only upcoming provider fixtures appear, inspect the strongest market rankings, and confirm the corner-data limitation is visible.
5. Create a USER account. Follow an upcoming match and favorite a team. Reload to confirm persistence. Edit profile and change password; users view system forecasts and do not submit picks.
6. Test Forgot password. Open the new development email under backend/outbox, follow its link, reset, then confirm the link cannot be reused.
7. As admin, search/view/edit the user. Generate a recovery link or temporary password. Suspend the user and verify they cannot continue; activate/unlock and verify access returns.
8. Log in as the active normal user. Confirm the banner, denied admin routes, blocked password changes, then Return to admin. Inspect audit entries.
9. Create a manual league, two teams and a fixture with kickoff a few minutes ahead. As USER, follow it. After kickoff, enter a final score as admin, retaining its kickoff and participant IDs. Return as USER; verify the notification and prediction history. Never adjust a past kickoff to create a prospective forecast.
10. Exercise admin match/team/league create/edit/delete. A referenced team/league delete should return a clear conflict. Read the confirmation before permanently deleting a match and its picks.
11. Enable maintenance. USER features should show maintenance; admin retains controls. Disable it. Change the site name and reload to verify the header and document title.
12. Configure a valid provider key. Verify the automatic sync imports real fixtures with source `live`; review provider-plan errors in the admin sync report. Calibrate and inspect its walk-forward report; existing match predictions must remain frozen.
13. Before a real deployment, verify actual SMTP delivery, HTTPS Secure cookies, host/origin configuration, database backups and device/keyboard behavior with your hosting configuration.

## Known verification limits

The authoring environment's managed browser-preview process could not access its Python runtime. Consequently, no claim is made that browser screenshots, responsive rendering, keyboard navigation or Chart.js rendering were visually tested. Backend tests and JavaScript syntax checks are independent of that limitation. The model is not externally validated on a real prospective football dataset; only provider-sourced results can establish that performance.
