# FlowSuite - QA Test Suite Documentation

A full-spectrum QA testing project covering UI, API, RBAC, Multi-Tenancy,
Billing, Database, and Security testing on a multi-tenant SaaS application.

## Test Suite Summary

| Metric | Result |
|---|---|
| Total tests | 100 |
| Passed | 75 |
| Failed | 25 |
| Errored | 0 |
| Distinct confirmed bugs | 15 |
| Runtime | ~35 seconds |

Full bug details: see `BUGS_REPORT.md`.

## Test Breakdown by Category

| Category | File(s) | Result |
|---|---|---|
| UI — Login/Logout | test_login.py, test_logout.py | All passed |
| UI — Projects | test_projects.py | All passed |
| UI — Members | test_members.py | All passed |
| UI — Billing | test_billing.py | All passed |
| UI — Org Switching | test_org_switch.py | All passed |
| API — RBAC | test_rbac.py | 4 failed (BUG-02, BUG-03), 2 passed |
| API — Multi-Tenancy | test_multi_tenancy.py | 6 failed (BUG-01, BUG-05), 2 passed |
| API — Billing | test_billing_api.py, test_billing_extra.py | 3 failed (BUG-04, BUG-07, BUG-12), 5 passed |
| API — Security | test_security.py, test_security_extra.py | 3 failed (BUG-06, BUG-08, BUG-17), 4 passed |
| API — Edge Cases | test_api_edge_cases.py, test_api_more_edge_cases.py | 5 failed (BUG-09, BUG-10, BUG-16, BUG-19), 16 passed |
| Database Integrity | test_database.py | 2 failed (BUG-02 and BUG-05, confirmed at DB level), 7 passed |

## How to Run

```powershell
# 1. Reset the database to a clean state
del db\app.db
npm start

# 2. In a new terminal, run the full suite
python -m pytest tests -v --html=full_report.html --self-contained-html
```

To run a single category:
```powershell
python -m pytest tests/test_rbac.py -v
```

## Tools Used

- **Playwright** (Python) — UI/functional and regression testing
- **Pytest** — test runner and assertions across all layers
- **requests** — API testing (replacing Postman for automation)
- **SQLite3 (Python stdlib)** — direct database integrity checks
- **pytest-html** — HTML test reports

## Notes on Test Data

Several billing and RBAC tests (invite-as-owner, cross-org task
assignment) succeed because of the bugs they're testing for, which leaves
extra data in the database (e.g. extra OWNER rows, cross-org task
assignments). This is expected and is itself part of the evidence — see
BUG-02 and BUG-05 in `BUGS_REPORT.md` for how the database-level checks
(test_tc59, test_tc60) independently confirm the same bugs found at the
API level. Reset the database (`del db\app.db`) before a fresh run if you
want a clean baseline.