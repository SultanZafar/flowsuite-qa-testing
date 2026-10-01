const express = require('express');
const router = express.Router();
const db = require('../db/db');
const { hashPassword, verifyPassword } = require('../db/password');

function makeToken(userId) {
  return Buffer.from(`user:${userId}`).toString('base64');
}

// NOTE (intentional bug for QA practice, BUG-08): no rate limiting here at
// all, on either signup or login — both can be called as fast as the client
// wants, making brute-force login attempts possible.

router.post('/signup', (req, res) => {
  const { name, email, password, orgName } = req.body || {};

  if (!name || !email || !password || !orgName) {
    return res.status(400).json({ error: 'name, email, password and orgName are required' });
  }

  const existing = db.prepare('SELECT * FROM Users WHERE email = ?').get(email);
  if (existing) {
    return res.status(409).json({ error: 'An account with this email already exists' });
  }

  const { hash, salt } = hashPassword(password);
  const userId = db.prepare('INSERT INTO Users (name, email, password_hash, password_salt) VALUES (?, ?, ?, ?)').run(name, email, hash, salt).lastInsertRowid;

  const orgId = db.prepare('INSERT INTO Organizations (name) VALUES (?)').run(orgName).lastInsertRowid;
  db.prepare('INSERT INTO Memberships (user_id, org_id, role) VALUES (?, ?, ?)').run(userId, orgId, 'OWNER');

  const trialEnd = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString();
  db.prepare('INSERT INTO Subscriptions (org_id, plan, status, trial_ends_at) VALUES (?, ?, ?, ?)').run(orgId, 'FREE', 'TRIALING', trialEnd);

  const user = db.prepare('SELECT user_id, name, email FROM Users WHERE user_id = ?').get(userId);
  return res.status(201).json({ success: true, token: makeToken(userId), user, orgId });
});

router.post('/login', (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: 'email and password are required' });
  }

  const user = db.prepare('SELECT * FROM Users WHERE email = ?').get(email);
  if (!user || !verifyPassword(password, user.password_hash, user.password_salt)) {
    return res.status(401).json({ error: 'Invalid email or password' });
  }

  return res.status(200).json({
    success: true,
    token: makeToken(user.user_id),
    user: { user_id: user.user_id, name: user.name, email: user.email },
  });
});

module.exports = router;
