# FlowSuite - Bug Report (Final)

**Test run summary:** 100 automated tests (Playwright UI + Pytest API/DB/Security)
**Result:** 75 passed, 25 failed, 0 errors
**Confirmed bugs:** 15 distinct issues

---

## CRITICAL

### BUG-01 — Broken cross-tenant authorization
**Endpoints:** GET /api/orgs/{orgId}/projects, /projects/{id}/tasks, /members, /subscription, /invoices
**Description:** Any logged-in user can read another organization's data
simply by changing the orgId in the URL. No server-side check confirms the
user belongs to that org.
**Evidence:** test_tc35, test_tc36, test_tc37, test_tc38, test_tc39 (all
returned HTTP 200 instead of 403)
**Impact:** Any customer can read any other customer's projects, tasks,
team, billing plan, and invoices.

### BUG-02 — Missing role check on invite endpoint
**Endpoint:** POST /api/orgs/{orgId}/members/invite
**Description:** A plain MEMBER can invite a new user as ADMIN or OWNER.
**Evidence:** test_tc29, test_tc30 (HTTP 201 instead of 403). Confirmed
again at the database level by test_tc59 — Globex ended up with 3 OWNER
rows instead of 1, a direct consequence of this bug being exploited
repeatedly across test runs.
**Impact:** Any member can grant themselves or an accomplice full admin rights.

### BUG-03 — Missing role check on role-change endpoint
**Endpoint:** PATCH /api/orgs/{orgId}/members/{userId}/role
**Description:** A MEMBER can promote themselves to OWNER, or change
anyone else's role.
**Evidence:** test_tc31, test_tc32 (HTTP 200 instead of 403)
**Impact:** Full privilege escalation to organization owner.

### BUG-06 — Authentication token is not cryptographically signed
**Description:** The auth token is simply base64("user:<id>") — unsigned,
with no server-side session validation. Anyone can compute a valid token
for any user ID without ever logging in.
**Evidence:** test_tc43 — a hand-made token for user_id=1 returned real
data (HTTP 200 instead of 401/403)
**Impact:** Complete authentication bypass / account takeover for any user.

### BUG-19 — IDOR: project ID not scoped to the org in the URL
**Endpoint:** GET /api/orgs/{orgId}/projects/{projectId}/tasks
**Description:** Even when the orgId in the URL is the user's own
organization, a projectId belonging to a DIFFERENT org still returns that
project's tasks. The server looks up the project by ID alone and never
checks it belongs to the org in the path.
**Evidence:** test_tc91 (HTTP 200 instead of 403/404)
**Impact:** Worse than BUG-01 — an attacker doesn't even need to know
another org's ID, just a guessable project ID, to read data across the
entire system.

---

## HIGH

### BUG-04 — FREE plan project limit not enforced
**Endpoint:** POST /api/orgs/{orgId}/projects
**Description:** The product defines a 3-project limit on the FREE plan,
but the API allows unlimited project creation.
**Evidence:** test_tc49 — 4th project created successfully (HTTP 201)
**Impact:** Revenue leakage — free users get unlimited usage.

### BUG-05 — Task assignee not validated against the project's organization
**Endpoint:** POST /api/orgs/{orgId}/projects/{projectId}/tasks
**Description:** A task can be assigned to a user who does not belong to
the project's organization.
**Evidence:** test_tc41 (API, HTTP 201 instead of 400/403) and test_tc60
(database check — found a real task assigned across organizations:
`task_id: 8, assignee_id: 3, project_org: 1`)

### BUG-07 — Canceled subscriptions keep full product access
**Endpoint:** POST /api/orgs/{orgId}/subscription/cancel, and the absence
of any enforcement elsewhere
**Description:** Cancelling a subscription correctly sets its status to
CANCELED, but nothing in the project/task creation endpoints ever checks
subscription status — a canceled org can keep using the product exactly
as if it were still active.
**Evidence:** test_tc101 — a project was created successfully (HTTP 201)
immediately after cancellation, instead of being blocked
**Impact:** Customers can cancel billing and keep full product access
indefinitely — direct revenue loss.

### BUG-08 — Internal stack trace leaked on malformed request
**Endpoint:** POST /api/auth/login
**Description:** Sending a non-JSON body returns a raw error page
containing internal server detail instead of a clean JSON error.
**Evidence:** test_tc46
**Impact:** Reveals server internals to an attacker, which can help them
plan further attacks.

### BUG-12 — Invoice amount does not match the plan's price
**Description:** Invoices are being recorded with an amount that doesn't
match their plan's actual price (seen: a FREE plan invoice charged $29.00,
which is the PRO price).
**Evidence:** test_tc74 (direct database check)
**Impact:** Customers may be billed incorrectly; breaks accounting/audit trust.

### BUG-17 — No rate limiting or lockout on repeated failed logins
**Endpoint:** POST /api/auth/login
**Description:** 30 consecutive wrong-password attempts against the same
account all return a normal 401 — no lockout, delay, or CAPTCHA kicks in
at any point.
**Evidence:** test_tc100 — all 30 attempts returned HTTP 401, no 429/423
**Impact:** Enables automated brute-force password guessing against any
account with no built-in defense.

---

## MEDIUM

### BUG-09 — org_id parameter not validated
**Endpoint:** GET /api/orgs/{orgId}/projects
**Description:** A non-numeric org_id ("not-a-number"), a negative org_id
(-1), or a non-existent org_id all return HTTP 200 with data instead of
400/403/404.
**Evidence:** test_tc50, test_tc84, test_tc98

### BUG-10 — Non-existent project returns 200, not 404
**Endpoint:** GET /api/orgs/{orgId}/projects/{projectId}/tasks
**Description:** Requesting tasks for a project ID that doesn't exist
returns an empty 200 response instead of 404 Not Found.
**Evidence:** test_tc51

### BUG-14 — Missing standard security headers
**Description:** Responses are missing `X-Content-Type-Options` and
`X-Frame-Options` headers, used to prevent MIME-sniffing and clickjacking.
**Evidence:** test_tc69

---

## LOW

### BUG-16 — Whitespace-only project name accepted
**Endpoint:** POST /api/orgs/{orgId}/projects
**Description:** A project name consisting only of spaces ("   ") is
accepted (HTTP 201) instead of rejected.
**Evidence:** test_tc81

---

## Confirmed Working Correctly (for balance in the report)

- Passwords are stored as salted hashes, not plaintext (test_tc57)
- SQL-injection-style input in the login email field is rejected (test_tc45)
- Password hashes are never exposed in the members list API (test_tc67)
- Creating a project directly in another org via POST is correctly blocked (test_tc40)
- Changing or cancelling another org's subscription is correctly blocked (test_tc47, test_tc48)
- The org list correctly shows only the user's own organization (test_tc42)
- Plan downgrade and invalid-plan rejection work correctly (test_tc70, test_tc72, test_tc73)
- No orphaned projects or memberships at the database level (test_tc58, test_tc64)
- No duplicate user emails (test_tc62)
- XSS payload in a project name does not crash the app (test_tc66)
- Requests with no token, or a garbage token, are correctly rejected (test_tc44 and related)
- Full UI regression suite (login, logout, projects, members, billing,
  org switching) — all passing

---

## Summary Table

| Severity | Count | Bug IDs |
|---|---|---|
| Critical | 5 | BUG-01, BUG-02, BUG-03, BUG-06, BUG-19 |
| High | 6 | BUG-04, BUG-05, BUG-07, BUG-08, BUG-12, BUG-17 |
| Medium | 3 | BUG-09, BUG-10, BUG-14 |
| Low | 1 | BUG-16 |
| **Total** | **15** | |