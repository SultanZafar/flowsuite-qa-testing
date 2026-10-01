# FlowSuite — Multi-Tenant SaaS App (Full-Spectrum QA Practice Project)

A real, working project-management SaaS (like a mini Trello/Asana) built so you
can practice **every** major SQA discipline on a project you fully control —
including the ones you can never legally do on a real production SaaS product
(load testing, security/penetration testing, multi-tenancy isolation attacks).

## 1. Setup

Requires [Node.js](https://nodejs.org) **v22.5 or higher** (v24 LTS
recommended). This project uses Node's built-in `node:sqlite` module, so
there's nothing to compile — no Visual Studio Build Tools, no Python, no
native dependencies. Just `npm install` and go.

```bash
npm install
npm start
```

Open **http://localhost:3001**. The database seeds itself automatically on
first run with 2 organizations, ready for multi-tenancy testing:

| Organization | Login | Password | Plan |
|---|---|---|---|
| **Acme Inc** | owner@acme.test | password123 | FREE (trialing) |
| Acme Inc | admin@acme.test | password123 | FREE (trialing) |
| **Globex Corp** | owner@globex.test | password123 | PRO (active) |
| Globex Corp | member@globex.test | password123 | PRO (active) |

To reset: delete `db/app.db` and run `npm start` again.

## 2. Project Structure

```
flowsuite/
├── server.js
├── db/
│   ├── schema.sql        # Users, Organizations, Memberships, Projects, Tasks, Subscriptions, Invoices
│   ├── db.js
│   ├── seed.js
│   └── password.js       # scrypt password hashing (built into Node, no extra deps)
├── middleware/
│   ├── auth.js            # Bearer token check
│   └── orgMembership.js   # Org membership check (NOT applied everywhere — see BUGS.md)
├── routes/
│   ├── auth.js             # signup, login
│   ├── orgs.js               # orgs, projects, tasks
│   ├── members.js             # invite, role management
│   └── billing.js               # subscription, invoices
└── public/                # Frontend dashboard
```

## 3. How Each Testing Category Maps to This Project

### ✅ Functional (UI) Testing
Use Playwright against `http://localhost:3001`. Every interactive element
has a `data-testid`. Test flows: signup → create org → create project → add
tasks → move task through statuses → invite a member.

### ✅ API Testing
Base URL: `http://localhost:3001/api`. Key endpoints:
- `POST /api/auth/signup`, `POST /api/auth/login`
- `GET/POST /api/orgs/:orgId/projects`
- `GET/POST /api/orgs/:orgId/projects/:projectId/tasks`
- `PATCH/DELETE /api/orgs/:orgId/tasks/:taskId`
- `GET /api/orgs/:orgId/members`, `POST /api/orgs/:orgId/members/invite`
- `PATCH /api/orgs/:orgId/members/:userId/role`
- `GET /api/orgs/:orgId/subscription`, `POST /api/orgs/:orgId/subscription/upgrade`, `.../cancel`
- `GET /api/orgs/:orgId/invoices`

Get a token from `/auth/login`, then send it as `Authorization: Bearer <token>`.

### ✅ Role-Based Access (RBAC) Testing
Log in as a MEMBER (e.g. `member@globex.test`) and try admin-only actions
(inviting someone as OWNER, changing another member's role). See BUG-02 and
BUG-03 in `BUGS.md` — this app has real RBAC holes to find.

### ✅ Subscription / Billing Testing
Log in as `owner@acme.test` (FREE plan), try creating more than 3 projects.
Upgrade to ENTERPRISE and check the invoice amount charged. Cancel a
subscription and check whether access is actually revoked.

### ✅ Multi-Tenancy Isolation Testing (the headline feature)
1. Log in as `owner@acme.test`, note Acme's `org_id` from the URL/API response.
2. Log in as `owner@globex.test` (a different browser tab/incognito window),
   note Globex's `org_id`.
3. While logged in as the Acme user, call
   `GET /api/orgs/<globex_org_id>/projects` directly (Postman or browser
   console `fetch`). See what comes back. This is a real, common SaaS
   vulnerability class (IDOR) — see BUG-01.

### ✅ Performance / Load Testing (JMeter)
Since this runs on your own machine, load-testing it is completely legal.
Good targets: `POST /api/auth/login`, `GET /api/orgs/:orgId/projects`,
`POST /api/orgs/:orgId/subscription/upgrade`. Run Load, Spike, and Soak
scenarios exactly as you would against a real backend.

### ✅ Security / Penetration Testing
Also fully legal here since it's your own local app. Things worth probing:
- IDOR on every `GET` endpoint (try swapping `orgId` values)
- Privilege escalation via the role-change endpoint
- Brute-force login (no rate limiting — try many wrong passwords rapidly)
- SQL injection attempts on query params (the app uses parameterized
  queries throughout, so this one *should* fail — good for confirming secure
  coding practices too)

### ✅ Database Testing
Real SQLite file at `db/app.db` — open with any SQLite client or the CLI:
```bash
sqlite3 db/app.db
.tables
SELECT * FROM Memberships;
```
Good integrity checks: orphaned memberships, invoice amounts vs. plan
prices, tasks assigned to users outside their org (BUG-05).

## 4. Bugs

This app has **8 intentional bugs** spanning security, RBAC, and billing.
Try to find them yourself first, then check `BUGS.md` for the full list —
great practice for writing real Jira bug reports afterward.
