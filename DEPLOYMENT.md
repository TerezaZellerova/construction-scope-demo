# Public demonstration preparation

Status: **not deployed**. No live URLs are available yet. Do not publish the application until all gates below pass. This is an InQI-inspired standalone technical demonstration, with no real InQI connection. Public deployment is restricted to synthetic data and deterministic, clearly labeled fixture output. No live AI functionality is claimed.

## Accounts and repository

The requested owner is `TerezaZellerova`; proposed new repository name: `construction-scope-demo`. Authenticated GitHub, Render and Vercel account access is required to create/push the repository and provision services. The account URL alone is not authentication. Keep the repository private while validating deployment. Git ignores `.env`, `.demo-access.json`, SQLite files, build caches and Vercel local metadata; never push those files.

## Security controls implemented

- PostgreSQL is mandatory when `APP_ENV=production`. Render's private database connection is used; external database access is disabled by `ipAllowList: []`.
- Three different random human access codes. Backend environment stores only SHA256 hashes; the browser bundle contains no access credentials. Codes are high-entropy invitation credentials, not passwords chosen by users.
- Session tokens expire after 30 minutes, are restricted to HS256, issuer and audience, and remain in browser memory. Sign-out removes the token locally; rotating the session secret revokes all tokens. Hash rotation disables future logins but existing sessions live until expiry unless the signing secret is also rotated.
- Separate MCP credentials cannot log in to HTTP or approve a review. Human approval has no MCP tool. Trusted stdio processes use the same PostgreSQL database and authorization service; no public MCP HTTP endpoint is mounted.
- Every project operation checks authenticated identity against server membership. Reviews are bound to the creator/project; report content is persisted and immutable through the API.
- Atomic save transactions and database uniqueness prevent retries from duplicating reports. PostgreSQL uses a shared transaction advisory lock; SQLite's locking is only an offline test fallback.
- Persistent fixed-window limits: 300 API requests/minute globally; 20 login attempts/minute globally; 120 tool operations/minute per identity; 10 generations/hour per identity. Generation storage is capped at 100 reviews per user, including failed-to-approve drafts. The global caps intentionally favor a small invited demonstration and cannot be bypassed using spoofed proxy headers.
- Request bodies limited to 4 KiB, extra login/save fields rejected, exact HTTPS CORS origins, no cookie authentication, no wildcard credentials, generic server error responses, no access logs, no production OpenAPI/docs.
- Security headers for frontend/API; backend code fails startup for unsafe public configuration. Public mode rejects OpenAI/Anthropic configuration to keep cost and live-integration claims bounded.
- Patched dependencies and scans are recorded in the verification file. Automatic deployment is disabled; verification must precede publishing.

## Generate private configuration

From a clean checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock.txt
python backend/generate_secrets.py
```

This creates `.env` and `.demo-access.json` with file mode 0600 without printing credentials. It refuses to overwrite existing files. Put only the backend configuration values into Render's secret environment settings. Share human codes privately with interview participants; configure MCP codes only in the trusted MCP host. Never use a `VITE_*` variable for secrets. Do not paste secrets into commits, tickets, screenshots or deployment logs.

## Verification gates before publishing

1. Run the GitHub `Verify before deployment` workflow. It creates an isolated PostgreSQL 16 database, runs the entire backend test suite, `pip check`, backend dependency audit, frontend audit and build. `TEST_DATABASE_URL` enables per-test isolated schemas and must refer to an isolated test database, never arbitrary user data.
2. Require successful CI for the exact commit being deployed. Local SQLite tests do not prove the PostgreSQL deployment path.
3. Validate production settings and schema with `python backend/preflight.py`. Render also runs backend tests against isolated temporary schemas in its database before switching to the new service version.
4. Keep Render/Vercel deployment access restricted while running deployed API and browser checks. Do not distribute the public demo URL before checks succeed. Keep existing CI/gates green on future deployments.

## Render

Use `render.yaml` at repository root to create a Python web service and a persistent Render PostgreSQL database. The blueprint proposes paid Starter/Basic plans for persistent operation; provisioning requires confirmed account/billing access. Confirm costs in Render before purchase. Set these environment values securely:

| Name | Value |
|---|---|
| `APP_ENV` | `production` |
| `AI_PROVIDER` | `fixture` |
| `DATABASE_URL` | Blueprint-provided private Postgres connection |
| `SESSION_SECRET` | Random value from generated `.env` (at least 48 characters) |
| `DEMO_ACCESS_HASHES_JSON` | Generated three human code hashes |
| `MCP_ACCESS_HASHES_JSON` | Generated separate MCP code hashes, or `{}` to disable MCP identities |
| `FRONTEND_ORIGINS` | Exact stable Vercel HTTPS origin, no trailing slash |

Only `/health` is unauthenticated and returns synthetic-data/mode metadata. Render start command binds `$PORT`; access logs and proxy-header trust are disabled. Use the internal database URL for services on Render. The schema and three synthetic projects initialize idempotently; no local SQLite data is uploaded. Do not put API provider keys into the public fixture deployment.

Render's documented [Blueprint format](https://render.com/docs/blueprint-spec) and [secret environment settings](https://render.com/docs/configure-environment-variables) are the deployment reference. The blueprint has not yet been accepted by Render or executed in this session.

## Vercel

Create a Vite project from the new repository with Root Directory `frontend`, install `pnpm install --frozen-lockfile`, build `pnpm build`, output `dist`. Set the sole application frontend environment variable:

```text
VITE_API_URL=https://<actual-render-service>.onrender.com
```

This is a public origin, not a secret. Vercel builds fail if it is missing or non-HTTPS. The Vercel headers limit network connections to same-origin and Render service hosts. If you later add a custom backend domain, update `connect-src` first. Configure Render `FRONTEND_ORIGINS` to the exact stable Vercel domain; unlisted preview domains cannot use the API. Do not broaden to wildcard origins to fix preview CORS.

Follow [Vercel's Vite deployment documentation](https://vercel.com/docs/frameworks/frontend/vite) and [environment variable settings](https://vercel.com/docs/environment-variables). No Vercel deployment was executed yet.

## Deployed checks

From a trusted terminal with the real HTTPS origin and a privately supplied Alice code in environment variables:

```sh
python checks/deployed_api.py
```

Required variables: `LIVE_API_URL`, `LIVE_ALICE_ACCESS_CODE`. The check makes bounded synthetic writes, rejects unauthenticated and cross-project access, generates a fixture, verifies approval gating, saves/retries the same key, rejects a new-key duplicate, and verifies production docs are disabled. It prints no credentials. It has not run against a deployed service yet.

Then use the actual Vercel URL in a real browser: sign in with Alice's code; select Harbor; inspect both documents; generate; verify fixture label; confirm Save disabled; click human approval; save; retry; record unchanged ID. Sign out, sign in as Bob, and verify only Cedar appears. Record the deployed screenshot, console/network errors and actual live URLs in `VERIFICATION.md`. The existing screenshot documents localhost only.

## MCP in deployment

MCP remains stdio, executed by a trusted host with an individual MCP token in `MCP_DEMO_TOKEN`. Configure `DATABASE_URL` and matching `MCP_ACCESS_HASHES_JSON` for the same PostgreSQL database. Prefer running the MCP process in the trusted Render environment to retain private database networking. Do not enable external database access for convenience or share a multi-user stdio process. Render's web service does not supply a remote stdio channel to desktop hosts; remote MCP transport and OAuth are outside this demonstration.

## Limitations

Shared invitation codes represent fictional users, not independently verified people. Approval is enforced as an authenticated human-channel action but this is not MFA or a regulated signature. No code upload or arbitrary document write endpoint exists. Limits protect a small demo, not internet-scale denial-of-service traffic; database-backed global locking reduces throughput intentionally. Streamed request bodies are bounded before parsing; hosting edge request/time limits still need verification. Backups, retention/reset, schema migrations, secret rotation and billing settings must be configured by the owner. Persisted data is synthetic only.

PostgreSQL execution and provider deployments remain unverified until gates run on an unrestricted test host or CI. Local macOS sandbox blocked PostgreSQL shared-memory startup. Live OpenAI/Anthropic calls and real InQI integration are not verified or enabled for public deployment.
