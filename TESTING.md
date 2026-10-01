# FlowSuite - Test Summary

**98 automated tests** across 6 layers, plus manual load testing (JMeter).

| Layer | Tests | Bugs found |
|---|---|---|
| UI (Playwright) | 28 | 2 |
| RBAC | 6 | 4 |
| Multi-Tenancy | 8 | 6 |
| Security | 8 | 3 |
| Billing/Subscription | 8 | 1 |
| API edge cases | 30 | 5 |
| Database (SQL) | 10 | — (cross-checks bugs above) |

**14 confirmed bugs** — 5 Critical, 2 High, 3 Medium, 4 Low.
Full details: see `BUGS.md`.

Most severe: **BUG-06** (forgeable, unsigned auth token — full account
takeover) and **BUG-01**/**BUG-19** (any user can read any other org's data).

---