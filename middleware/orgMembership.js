const db = require('../db/db');

// Verifies the authenticated user is actually a member of :orgId in the URL.
// NOTE FOR TESTERS: this middleware is applied consistently on write actions
// (create/update/delete) in this project, but it is intentionally MISSING on
// several read (GET) endpoints — see BUGS.md, BUG-01. This mirrors a very
// common real-world mistake: authorization checks added for writes but
// forgotten for reads.
module.exports = function requireOrgMembership(req, res, next) {
  const orgId = Number(req.params.orgId);
  const membership = db
    .prepare('SELECT * FROM Memberships WHERE user_id = ? AND org_id = ?')
    .get(req.userId, orgId);

  if (!membership) {
    return res.status(403).json({ error: 'You are not a member of this organization' });
  }

  req.membership = membership;
  next();
};
