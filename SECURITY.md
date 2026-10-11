# Demonstration security review

This is a small invited fixture demonstration, not production construction software. No real InQI, client documents or live AI integration is used.

| Threat | Control | Verification |
|---|---|---|
| Model requests another project | Authenticated identity + server membership on every project tool | Cross-project HTTP and real MCP tests |
| Model approves its own work | Approval available only through human-session HTTP; separate MCP credentials | Unapproved save rejected; MCP credentials cannot approve |
| Retry creates duplicate report | Unique identity/request key and unique review ID, atomic transaction lock | Sequential and 16 concurrent retry tests; localhost browser |
| Public credential in bundle | No built-in codes; hashes stored in backend env; session only in browser memory | Source/build review; login test |
| Session forgery/reuse | HS256 allowlist, issuer/audience, required expiration, 30-minute lifetime | Tampering/expired-token tests |
| Unlimited writes/provider expense | Per-identity and global persistent rate limits, 100-review cap, fixture-only public mode | Rate-limit tests; configuration fails closed |
| CSRF/CORS abuse | No cookies, bearer sessions, exact allowed origins, extra input rejected | Origin and input validation tests |
| Oversized request | Bound streamed body before parsing, early content-length check | Fixed and streamed-body tests |
| Known vulnerable dependency | Upgraded pinned SDK/server/JWT/Vite dependencies | Final dependency audit outputs |
| Secrets in Git/archive | Ignored private config files, export allowlist excludes secrets/database | Packaging and staged-file scan |

Open publication gates: actual PostgreSQL suite, remote GitHub repository/CI, Render and Vercel provisioning/configuration, deployed API checks and real deployed-browser workflow. None should be represented as complete until executed.

Owner codes are shared invitation credentials for fictional users. Human-channel approval cannot prove an individual's real-world identity. Secret/code rotation is manual; all-session revocation requires signing-secret rotation. The global limiter intentionally reduces small-demo throughput; infrastructure edge protections and operational backups remain owner responsibilities. PostgreSQL advisory locking serializes demo write transactions and rate counters across workers/MCP processes. Shared-memory sandbox restrictions prevented local PostgreSQL verification.
