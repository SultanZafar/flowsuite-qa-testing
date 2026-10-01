const express = require('express');
const router = express.Router();
const db = require('../db/db');
const requireAuth = require('../middleware/auth');
const requireOrgMembership = require('../middleware/orgMembership');

router.use(requireAuth);

// NOTE (intentional bug, BUG-01 pattern continues): missing requireOrgMembership.
router.get('/:orgId/members', (req, res) => {
  const orgId = Number(req.params.orgId);
  const members = db
    .prepare(
      `SELECT u.user_id, u.name, u.email, m.role, m.joined_at
       FROM Memberships m JOIN Users u ON m.user_id = u.user_id
       WHERE m.org_id = ?`
    )
    .all(orgId);
  res.json({ members });
});

// NOTE (intentional bug for QA practice, BUG-02): this route checks that the
// requester is a member of the org (requireOrgMembership), but never checks
// their ROLE. A plain MEMBER can invite someone as ADMIN or even OWNER,
// which should be restricted to OWNER/ADMIN only.
router.post('/:orgId/members/invite', requireOrgMembership, (req, res) => {
  const orgId = Number(req.params.orgId);
  const { name, email, role } = req.body || {};

  if (!name || !email || !role) {
    return res.status(400).json({ error: 'name, email and role are required' });
  }

  let user = db.prepare('SELECT * FROM Users WHERE email = ?').get(email);
  if (!user) {
    // Demo-only: invited users get a throwaway random password hash since
    // there's no real email/invite-accept flow in this practice app.
    const { hashPassword } = require('../db/password');
    const { hash, salt } = hashPassword(Math.random().toString(36));
    const info = db.prepare('INSERT INTO Users (name, email, password_hash, password_salt) VALUES (?, ?, ?, ?)').run(name, email, hash, salt);
    user = { user_id: info.lastInsertRowid };
  }

  try {
    db.prepare('INSERT INTO Memberships (user_id, org_id, role) VALUES (?, ?, ?)').run(user.user_id, orgId, role);
  } catch (e) {
    return res.status(409).json({ error: 'User is already a member of this organization' });
  }

  res.status(201).json({ success: true });
});

// NOTE (intentional bug for QA practice, BUG-03 — privilege escalation):
// this route checks org membership, but never checks that the REQUESTER is
// an OWNER before letting them change someone's role. Any member can PATCH
// their own role (or anyone else's) to OWNER.
router.patch('/:orgId/members/:userId/role', requireOrgMembership, (req, res) => {
  const orgId = Number(req.params.orgId);
  const targetUserId = Number(req.params.userId);
  const { role } = req.body || {};

  if (!['OWNER', 'ADMIN', 'MEMBER'].includes(role)) {
    return res.status(400).json({ error: 'Invalid role' });
  }

  const membership = db.prepare('SELECT * FROM Memberships WHERE user_id = ? AND org_id = ?').get(targetUserId, orgId);
  if (!membership) return res.status(404).json({ error: 'Membership not found' });

  db.prepare('UPDATE Memberships SET role = ? WHERE membership_id = ?').run(role, membership.membership_id);
  res.json({ success: true });
});

module.exports = router;
