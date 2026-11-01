# Verification record

Verified on 29 October 2026 using Python 3.12 and Node.js 24.22.1.

## Live-only prediction update (1 November 2026)

- `python -m pytest backend/tests/test_prediction.py::test_poisson_distribution -q`: **passed**.
- `python -m pytest backend/tests/test_prediction.py::test_live_ingestion_and_filters -q`: **passed**, including provider country metadata and the top-predictions response.
- `python scripts/check_frontend.py`: **12 first-party JavaScript modules passed syntax checks**.
- `python -m alembic current`: **002 (head)**.
- Browser smoke check: `/api/health` returned `ok`; OpenAPI contains `/api/predictions/top`; `/api/site` correctly reported `live_data_configured: false` because no provider key is configured locally.
- A complete backend test run was started, but the terminal did not return its final summary. The full suite is therefore not claimed as passing in this update.
- No live provider request was made: a football-data.org API key was not configured. Corners are not predicted because this provider feed does not supply historical corner counts.

- `python -m pytest backend/tests -q`: **19 passed**, one upstream Starlette TestClient deprecation warning, no test failures.
- `python scripts/check_frontend.py`: **11 first-party JavaScript modules passed syntax checks**.
- `python -m compileall -q backend scripts`: passed.
- A fresh temporary SQLite database migrated successfully with `python -m alembic upgrade head`.
- Running the seed twice created 192 matches and one administrator on the first run, then added zero matches on the second run. The administrator password column contained no plaintext initial password.
- Production-mode ASGI smoke checks verified a `__Host-predictpro` cookie with Secure and HttpOnly flags and confirmed that developer docs and the OpenAPI schema are disabled.
- Chart.js is bundled locally, and static-file responses and security headers were checked through the application.

Provider HTTP responses and recovery email delivery were substituted in tests. Real football-data.org credentials and SMTP delivery were not exercised. Browser preview could not launch because its separate runtime could not access Python, so responsive layout, visual appearance, chart rendering and keyboard behavior remain unverified in a real browser. The manual acceptance walkthrough is in FEATURE_CHECKLIST.md.

No real-match accuracy claim is made. Bundled schedules/results are synthetic; retrospective backtests are separated from prospective forecasts. No hosted deployment was created.
