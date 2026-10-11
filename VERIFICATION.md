# Executed verification — October 11, 2026

## Live environment

- Frontend: https://construction-scope-demo.vercel.app
- Backend health: https://construction-scope-demo-api.onrender.com/health
- Render service: `srv-db5rl24s728c738qdfhg`, Frankfurt, free plan.
- PostgreSQL 16: `dpg-db5r0a8473hc73c41m70-a`, free plan, private connections only; expires November 10, 2026.
- Application commit: `6095624e5039c3c6db70356fdc0941e381a52682`.
- Vercel deployment: `dpl_B1UfjJb8K3mMurKcQghCh3bvyipD`, READY.
- Render deployment: `dep-db5rlsvg0jfs73bkhvbg`, live.

## Automated verification

The exact application commit passed GitHub CI: https://github.com/TerezaZellerova/construction-scope-demo/actions/runs/38153077979

Backend: 21 tests against PostgreSQL 16, including real official MCP SDK stdio initialization and tool calls, cross-project denials, human-approval gating, and concurrent idempotent saves. The preceding identical backend run recorded 21 passed, 2 warnings in 4.88s. Dependency consistency and Python vulnerability audit passed. Frontend frozen dependency install, audit, TypeScript check and Vite build passed.

The deployed `checks/deployed_api.py` passed: fixture/synthetic health metadata; unauthenticated access denied; Alice sees only Harbor; Cedar/Quarry reads denied; document retrieval; fixture generation; save blocked before approval; human approval; same-key save retry returns identical report; changed-key duplicate rejected; production docs disabled; no-store response headers.

## Real deployed browser workflow

Signed in using private Alice code. Selected Harbor Library Retrofit, inspected both documents, generated the explicitly labeled fixture report. Confirmed Save was disabled before approval; approved through the human interface, saved and retried the same key. Report ID remained `626c1cca-67c6-4390-85df-bff4f4042929`. Screenshot: `deployed-demo.png` in the local deliverable.

A separate browser session signed in as Bob and showed only Cedar Primary School Extension. The first Alice browser attempt caught a CORS configuration update still deploying; it was rerun successfully after Render reported live.

No Render error-level logs were returned after verification. Direct SQL inspection through the hosted connector was blocked by the intentionally empty database IP allowlist; it was not widened. Same-report API/browser receipts and PostgreSQL concurrency tests establish retry behavior; direct production row counting was not performed.

## Honest limits

Fixture mode uses deterministic synthetic output, not a live AI response. OpenAI/Anthropic adapters have mocked tests but no independently verified live calls. No real InQI integration. MCP is verified stdio, with no public MCP HTTP endpoint or deployed ChatGPT/Claude app integration. Free backend sleeps after inactivity; free PostgreSQL expires November 10, 2026. No production SLA, automated backup/restore verification, or load testing. Invitation credentials represent fictional users; approval is not a verified legal signature.
