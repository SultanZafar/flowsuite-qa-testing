const express = require('express');
const router = express.Router();
const db = require('../db/db');
const requireAuth = require('../middleware/auth');
const requireOrgMembership = require('../middleware/orgMembership');

router.use(requireAuth);

const PLAN_PROJECT_LIMITS = { FREE: 3, PRO: 20, ENTERPRISE: Infinity };

// List organizations the current user belongs to
router.get('/', (req, res) => {
  const orgs = db
    .prepare(
      `SELECT o.org_id, o.name, m.role
       FROM Organizations o
       JOIN Memberships m ON o.org_id = m.org_id
       WHERE m.user_id = ?`
    )
    .all(req.userId);
  res.json({ orgs });
});

// NOTE (intentional bug for QA practice, BUG-01 — see BUGS.md):
// this route does NOT use requireOrgMembership. Any logged-in user can view
// ANY organization's projects just by changing :orgId in the URL, even if
// they are not a member of that organization. This is a classic multi-tenant
// data isolation / IDOR (Insecure Direct Object Reference) vulnerability.
router.get('/:orgId/projects', (req, res) => {
  const orgId = Number(req.params.orgId);
  const projects = db.prepare('SELECT * FROM Projects WHERE org_id = ? ORDER BY created_at DESC').all(orgId);
  res.json({ projects });
});

router.post('/:orgId/projects', requireOrgMembership, (req, res) => {
  const orgId = Number(req.params.orgId);
  const { name } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name is required' });

  // NOTE (intentional bug for QA practice, BUG-04): plan project limits are
  // defined (PLAN_PROJECT_LIMITS above) but never actually enforced here —
  // a FREE plan org can create unlimited projects despite the advertised cap.
  const info = db.prepare('INSERT INTO Projects (org_id, name) VALUES (?, ?)').run(orgId, name);
  res.status(201).json({ success: true, projectId: info.lastInsertRowid });
});

// Same missing-membership-check issue as GET /projects (BUG-01)
router.get('/:orgId/projects/:projectId/tasks', (req, res) => {
  const { projectId } = req.params;
  const tasks = db
    .prepare(
      `SELECT t.*, u.name as assignee_name FROM Tasks t
       LEFT JOIN Users u ON t.assignee_id = u.user_id
       WHERE t.project_id = ? ORDER BY t.created_at DESC`
    )
    .all(projectId);
  res.json({ tasks });
});

router.post('/:orgId/projects/:projectId/tasks', requireOrgMembership, (req, res) => {
  const { projectId, orgId } = req.params;
  const { title, assigneeId } = req.body || {};

  if (!title) return res.status(400).json({ error: 'title is required' });

  const project = db.prepare('SELECT * FROM Projects WHERE project_id = ?').get(projectId);
  if (!project || String(project.org_id) !== String(orgId)) {
    return res.status(404).json({ error: 'Project not found in this organization' });
  }

  // NOTE (intentional bug for QA practice, BUG-05): assigneeId is never
  // checked to make sure that user is actually a member of this org — a
  // task can be assigned to a user from a completely different organization.
  const info = db
    .prepare('INSERT INTO Tasks (project_id, title, assignee_id) VALUES (?, ?, ?)')
    .run(projectId, title, assigneeId || null);

  res.status(201).json({ success: true, taskId: info.lastInsertRowid });
});

router.patch('/:orgId/tasks/:taskId', requireOrgMembership, (req, res) => {
  const { status, title } = req.body || {};
  const fields = [];
  const values = [];
  if (status) { fields.push('status = ?'); values.push(status); }
  if (title) { fields.push('title = ?'); values.push(title); }
  if (fields.length === 0) return res.status(400).json({ error: 'Nothing to update' });

  values.push(req.params.taskId);
  db.prepare(`UPDATE Tasks SET ${fields.join(', ')} WHERE task_id = ?`).run(...values);
  res.json({ success: true });
});

router.delete('/:orgId/tasks/:taskId', requireOrgMembership, (req, res) => {
  db.prepare('DELETE FROM Tasks WHERE task_id = ?').run(req.params.taskId);
  res.json({ success: true });
});

module.exports = router;
