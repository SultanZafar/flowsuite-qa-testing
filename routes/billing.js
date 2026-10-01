const express = require('express');
const router = express.Router();
const db = require('../db/db');
const requireAuth = require('../middleware/auth');
const requireOrgMembership = require('../middleware/orgMembership');

router.use(requireAuth);

const PLAN_PRICES = { FREE: 0, PRO: 29, ENTERPRISE: 99 };

// NOTE (intentional bug, BUG-01 pattern continues): missing requireOrgMembership.
router.get('/:orgId/subscription', (req, res) => {
  const orgId = Number(req.params.orgId);
  const sub = db.prepare('SELECT * FROM Subscriptions WHERE org_id = ?').get(orgId);
  if (!sub) return res.status(404).json({ error: 'No subscription found' });
  res.json(sub);
});

// NOTE (intentional bug, BUG-01 pattern continues): missing requireOrgMembership.
router.get('/:orgId/invoices', (req, res) => {
  const orgId = Number(req.params.orgId);
  const invoices = db.prepare('SELECT * FROM Invoices WHERE org_id = ? ORDER BY created_at DESC').all(orgId);
  res.json({ invoices });
});

router.post('/:orgId/subscription/upgrade', requireOrgMembership, (req, res) => {
  const orgId = Number(req.params.orgId);
  const { plan } = req.body || {};

  if (!['FREE', 'PRO', 'ENTERPRISE'].includes(plan)) {
    return res.status(400).json({ error: 'Invalid plan' });
  }

  db.prepare("UPDATE Subscriptions SET plan = ?, status = 'ACTIVE', updated_at = CURRENT_TIMESTAMP WHERE org_id = ?").run(plan, orgId);

  // NOTE (intentional bug for QA practice, BUG-06): the invoice is always
  // created using the PRO price, regardless of which plan was actually
  // selected — upgrading to ENTERPRISE ($99) still generates a $29 invoice.
  const amount = PLAN_PRICES.PRO;
  db.prepare('INSERT INTO Invoices (org_id, plan, amount, status) VALUES (?, ?, ?, ?)').run(orgId, plan, amount, 'PAID');

  res.json({ success: true, plan, amountCharged: amount });
});

router.post('/:orgId/subscription/cancel', requireOrgMembership, (req, res) => {
  const orgId = Number(req.params.orgId);

  // NOTE (intentional bug for QA practice, BUG-07): this only flips the
  // status to CANCELED. Nowhere else in the app (see routes/orgs.js) does
  // any endpoint check subscription.status before allowing project/task
  // creation — so a "canceled" org keeps full, unrestricted product access
  // forever, exactly as if it were still ACTIVE.
  db.prepare("UPDATE Subscriptions SET status = 'CANCELED', updated_at = CURRENT_TIMESTAMP WHERE org_id = ?").run(orgId);
  res.json({ success: true });
});

module.exports = router;
