# Current verification — public-demo preparation, 11 October 2026

**Status: NOT DEPLOYED. PostgreSQL/deployed gates are incomplete. No live URLs exist.**

Executed against the updated source:

- Entire offline backend suite: **21 passed in 1.72s**, including real MCP stdio protocol calls, authorization denial, membership revocation, human approval, concurrent save retries, session expiry/tampering, credential separation, persistent rate limits, generation quota, streamed-body limits and production configuration rejection.
- One upstream Pydantic Settings warning about MCP's lifespan annotation; MCP initialization and tools still pass.
- `pip check`: no broken requirements.
- Backend locked-dependency audit: **no known vulnerabilities found**. Output: `python-audit-final.json`.
- Frontend dependency audit: **zero advisories**. Output: `frontend-audit-final.json`.
- TypeScript + Vite 6.4.3 production build: **passed**, 28 modules, 571ms.
- Backend upgraded to patched MCP 1.28.1, FastAPI 0.143.0, Starlette 1.7.0, PyJWT 2.15.1 and current locked compatible dependencies. Original vulnerable pins are superseded.
- Local browser executed private login as Alice, project selection, document review, fixture generation, human-channel approval, save and same-key retry. Report f5af0653-011e-4892-82c1-bdb7d3bf8371 stayed unchanged. Retry after backend restart also preserved this ID.
- Screenshot `secure-local-demo.jpg` shows **localhost only**. No deployed-browser result is claimed.
- Local source/build/staged-file scan found none of the generated access codes, signing secret or credential hashes in the tracked deliverables. Private `.env`, `.demo-access.json` and databases are excluded from Git/archive.

Outstanding gates:

- Local PostgreSQL startup could not run: the macOS execution sandbox denied PostgreSQL's `shmget` shared-memory operation. PostgreSQL tests therefore have **not passed**. The suite can run through `TEST_DATABASE_URL` and GitHub CI's PostgreSQL 16 service; both remain unexecuted here.
- GitHub, Vercel and Render integrations were confirmed not installed/connected. A local Git repository was initialized and prepared, but no remote repository was created/pushed.
- Render blueprint and Vercel config are prepared but not provisioned or accepted by the providers.
- Remote API smoke checks, deployed-browser workflow, live URLs, edge/TLS configuration and persistent Render storage remain unverified.
- No real InQI integration or live AI provider calls are verified. Public configuration is fixture-only.

Local URLs: http://127.0.0.1:5173/ and http://127.0.0.1:8000/health. These are not public deployment URLs. Details and deployment gates: `DEPLOYMENT.md`.

## GitHub PostgreSQL verification — 2026-10-11

Commit `1b0c7b0187def302e860148a94e245b595c16db4`: PostgreSQL 16 backend suite **21 passed, 2 warnings in 4.88s**. Dependency consistency passed; no known Python vulnerabilities found. Frontend frozen installation, audit, and build passed.

Run: https://github.com/TerezaZellerova/construction-scope-demo/actions/runs/38152774621

Free temporary Render PostgreSQL created, expires November 10, 2026. Vercel project created; neither application deployment nor deployed end-to-end workflow verified yet.
