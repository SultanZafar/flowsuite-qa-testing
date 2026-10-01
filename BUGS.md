# Intentional Bugs — Answer Key

Try to find these yourself first (using the categories in README.md), then
check this list. Practice writing each one up as a proper Jira bug report:
steps to reproduce, expected vs actual, severity, priority.

---

### BUG-01: Multi-tenancy data leak (IDOR) on every read endpoint ⭐ (the big one)
**Layer:** API / Security / Multi-Tenancy
**Where:** `GET /api/orgs/:orgId/projects`, `.../tasks`, `/api/orgs/:orgId/members`,
`/api/orgs/:orgId/subscription`, `/api/orgs/:orgId/invoices`
**Steps:** Log in as any user (e.g. `owner@acme.test`), then call any of the
above endpoints using a **different** organization's `orgId` (e.g. Globex's).
**Actual:** Full data returned — projects, tasks, member list, subscription
plan, and invoice history of an organization you don't belong to.
**Expected:** 403 Forbidden — you should only ever see your own org's data.
**Severity:** Critical. **Root cause:** `requireOrgMembership` middleware
exists and works correctly, but was never applied to these GET routes.

### BUG-02: Any member can invite someone as ADMIN or OWNER
**Layer:** API / RBAC
**Where:** `POST /api/orgs/:orgId/members/invite`
**Steps:** Log in as a MEMBER-role user (e.g. `member@globex.test`), invite a
new person with `role: "OWNER"`.
**Actual:** Succeeds — a brand-new OWNER is created by a plain member.
**Expected:** Only OWNER/ADMIN should be able to invite, and only OWNER
should be able to grant OWNER.

### BUG-03: Privilege escalation via role-change endpoint
**Layer:** API / RBAC / Security
**Where:** `PATCH /api/orgs/:orgId/members/:userId/role`
**Steps:** Log in as a MEMBER, call this endpoint targeting your own
`userId` with `{ "role": "OWNER" }`.
**Actual:** Succeeds — you just promoted yourself to Owner of the organization.
**Expected:** Should require the requester to already be an OWNER.

### BUG-04: FREE plan project limit is defined but never enforced
**Layer:** API / Billing
**Where:** `POST /api/orgs/:orgId/projects`
**Steps:** As a FREE-plan org (Acme), create more than 3 projects.
**Actual:** Unlimited projects can be created.
**Expected:** Should be blocked (or prompted to upgrade) past the plan's limit.

### BUG-05: Tasks can be assigned to users outside the organization
**Layer:** API / Database Integrity / Multi-Tenancy
**Where:** `POST /api/orgs/:orgId/projects/:projectId/tasks`
**Steps:** Find a user ID that belongs to a different org, pass it as
`assigneeId` when creating a task in your own org's project.
**Actual:** Task is created with that cross-org assignee.
**Expected:** Should validate the assignee is actually a member of the same org.
**How to catch it in SQL:**
```sql
SELECT t.task_id, t.assignee_id, p.org_id AS project_org, m.org_id AS assignee_org
FROM Tasks t
JOIN Projects p ON t.project_id = p.project_id
LEFT JOIN Memberships m ON t.assignee_id = m.user_id AND m.org_id = p.org_id
WHERE t.assignee_id IS NOT NULL AND m.membership_id IS NULL;
-- Any rows returned = a task assigned to someone outside that project's org
```

### BUG-06: Upgrading to any plan always charges the PRO price
**Layer:** API / Billing / Database Integrity
**Where:** `POST /api/orgs/:orgId/subscription/upgrade`
**Steps:** Upgrade an org to `ENTERPRISE` (should be $99).
**Actual:** Invoice is created for $29 (the PRO price) regardless of the
plan chosen.
**Expected:** Invoice amount should match the selected plan's price.
**How to catch it in SQL:**
```sql
SELECT invoice_id, org_id, plan, amount FROM Invoices
WHERE (plan = 'PRO' AND amount <> 29.0)
   OR (plan = 'ENTERPRISE' AND amount <> 99.0)
   OR (plan = 'FREE' AND amount <> 0.0);
```

### BUG-07: Canceled subscriptions keep full product access
**Layer:** API / Billing
**Where:** `POST /api/orgs/:orgId/subscription/cancel`, and the absence of
any check in `routes/orgs.js`
**Steps:** Cancel an org's subscription, then keep creating projects/tasks
as normal.
**Actual:** Everything still works — status is CANCELED in the database but
nothing anywhere checks it before allowing actions.
**Expected:** A canceled org should lose access to paid features (or be
downgraded to FREE-tier limits).

### BUG-08: No rate limiting on login (brute-force possible)
**Layer:** API / Security
**Where:** `POST /api/auth/login`
**Steps:** Send many rapid login requests with wrong passwords for the same
email.
**Actual:** No lockout, no delay, no CAPTCHA — unlimited attempts.
**Expected:** Should lock the account or add exponential backoff after a
handful of failed attempts.

---

**Bonus (not a bug, but worth noting for your report):** Auth tokens here
are plain base64, not real JWTs, and there's no token expiry. This is
intentional to keep the project dependency-light for teaching — never use
this auth approach in a real production app.
