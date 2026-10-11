# Construction scope assistant

An InQI-inspired standalone engineering interview demonstration. React, TypeScript and Vite frontend; FastAPI backend; official MCP Python SDK; persistent PostgreSQL for deployment. Three fictional projects have different users and synthetic documents. No actual InQI integration or independently verified live AI is claimed.

**Deployment status: not deployed.** Security changes have local verification; PostgreSQL and deployed checks are still required. See [DEPLOYMENT.md](DEPLOYMENT.md) for exact gates, Vercel/Render configuration and remaining limitations.

## Local setup

Python 3.12 and Node 22 recommended. From the project directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock.txt
python backend/generate_secrets.py
python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

The generator writes private `.env` and `.demo-access.json` files, refuses overwrites and prints no credentials. Retrieve your Alice/Bob/Carol invitation codes privately from `.demo-access.json`. They are not bundled into the frontend or included in downloadable archives.

In a second terminal:

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

UI: http://127.0.0.1:5173. Local API docs: http://127.0.0.1:8000/docs. Public deployment disables API docs. Set PostgreSQL `DATABASE_URL` to test deployment storage locally; otherwise SQLite remains available solely for offline development/tests. The public backend refuses SQLite.

## Verification

```sh
python -m pytest backend -q
pip check
pip-audit -r backend/requirements.lock.txt
cd frontend
pnpm audit
pnpm build
```

For full tests with a disposable PostgreSQL database:

```sh
TEST_DATABASE_URL=postgresql://... python -m pytest backend -q
```

Use a trusted test connection string, not production credentials in shared shell history. Per-test schemas are created and removed. GitHub CI provisions PostgreSQL 16 automatically. `TEST_POSTGRES=1` can start a temporary Unix-socket PostgreSQL via the optional `pgserver` test package on an unrestricted non-root macOS host; the current sandbox blocks its required shared-memory operation. PostgreSQL tests have not passed here yet.

## Demo script

1. Sign in using Alice's private invitation code. Select Harbor; only Harbor is authorized.
2. Review synthetic scope/drawing notes: electrical feeder upgrade is excluded by scope and required by the drawing.
3. Generate the review. Verify prominent fixture labeling and document IDs. Save remains disabled.
4. Approve through the authenticated human UI; save; click Retry save. The report ID stays the same.
5. Sign out and use Bob's code. Only Cedar is listed. Carol sees only Quarry. Explain that forged project IDs are rejected server-side.
6. Show backend test results, including the real MCP stdio exchange and concurrent idempotency checks.

## MCP

Four tools: `list_authorized_projects`, `retrieve_project_documents`, `generate_scope_review`, `save_approved_report`. Configure a trusted stdio host to run `.venv/bin/python backend/mcp_server.py` with an individual `MCP_DEMO_TOKEN`, matching backend `MCP_ACCESS_HASHES_JSON`, and the same `DATABASE_URL`. Run from the project directory or pass absolute paths. Tokens come from the private generator file. Human access codes and MCP tokens are distinct. Human approval is absent from the tool schema. A process must represent one trusted identity; no public remote MCP endpoint is exposed.

## AI labeling

The public configuration enforces `AI_PROVIDER=fixture`: deterministic synthetic-data results, explicitly labeled as not AI-generated. In development, `AI_PROVIDER=openai` with `OPENAI_API_KEY`, or `AI_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`, selects real provider adapters. Missing keys return an error and provider failures never substitute fixtures. Those adapters have mocked verification only; live calls are not verified. Model outputs are rendered as text rather than HTML.

See [VERIFICATION.md](VERIFICATION.md) for executed results, [SECURITY.md](SECURITY.md) for controls and open gates, and [DEPLOYMENT.md](DEPLOYMENT.md) for deployment steps. Runtime dependencies are pinned and locked; audits must be rerun before each release.
