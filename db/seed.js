const db = require('./db');
const { hashPassword } = require('./password');

const userCount = db.prepare('SELECT COUNT(*) as c FROM Users').get().c;

if (userCount === 0) {
  console.log('Seeding FlowSuite database...');

  const insertUser = db.prepare('INSERT INTO Users (name, email, password_hash, password_salt) VALUES (?, ?, ?, ?)');
  const insertOrg = db.prepare('INSERT INTO Organizations (name) VALUES (?)');
  const insertMembership = db.prepare('INSERT INTO Memberships (user_id, org_id, role) VALUES (?, ?, ?)');
  const insertProject = db.prepare('INSERT INTO Projects (org_id, name) VALUES (?, ?)');
  const insertTask = db.prepare('INSERT INTO Tasks (project_id, title, status, assignee_id) VALUES (?, ?, ?, ?)');
  const insertSub = db.prepare('INSERT INTO Subscriptions (org_id, plan, status, trial_ends_at) VALUES (?, ?, ?, ?)');
  const insertInvoice = db.prepare('INSERT INTO Invoices (org_id, plan, amount, status) VALUES (?, ?, ?, ?)');

  // ---- Org 1: Acme Inc — Free plan, trialing ----
  const aliPw = hashPassword('password123');
  const aliId = insertUser.run('Ali Raza', 'owner@acme.test', aliPw.hash, aliPw.salt).lastInsertRowid;

  const zaraPw = hashPassword('password123');
  const zaraId = insertUser.run('Zara Malik', 'admin@acme.test', zaraPw.hash, zaraPw.salt).lastInsertRowid;

  const acmeId = insertOrg.run('Acme Inc').lastInsertRowid;
  insertMembership.run(aliId, acmeId, 'OWNER');
  insertMembership.run(zaraId, acmeId, 'ADMIN');

  const trialEnd = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString();
  insertSub.run(acmeId, 'FREE', 'TRIALING', trialEnd);

  const acmeP1 = insertProject.run(acmeId, 'Website Redesign').lastInsertRowid;
  const acmeP2 = insertProject.run(acmeId, 'Mobile App Launch').lastInsertRowid;
  insertTask.run(acmeP1, 'Design homepage mockup', 'DONE', aliId);
  insertTask.run(acmeP1, 'Implement responsive nav', 'IN_PROGRESS', zaraId);
  insertTask.run(acmeP2, 'Draft App Store listing', 'TODO', null);

  // ---- Org 2: Globex Corp — Pro plan, active ----
  const saraPw = hashPassword('password123');
  const saraId = insertUser.run('Sara Ahmed', 'owner@globex.test', saraPw.hash, saraPw.salt).lastInsertRowid;

  const usmanPw = hashPassword('password123');
  const usmanId = insertUser.run('Usman Tariq', 'member@globex.test', usmanPw.hash, usmanPw.salt).lastInsertRowid;

  const globexId = insertOrg.run('Globex Corp').lastInsertRowid;
  insertMembership.run(saraId, globexId, 'OWNER');
  insertMembership.run(usmanId, globexId, 'MEMBER');

  insertSub.run(globexId, 'PRO', 'ACTIVE', null);
  insertInvoice.run(globexId, 'PRO', 29.0, 'PAID');

  const globexP1 = insertProject.run(globexId, 'Q4 Marketing Campaign').lastInsertRowid;
  insertTask.run(globexP1, 'Finalize campaign budget', 'DONE', saraId);
  insertTask.run(globexP1, 'Book ad placements', 'TODO', usmanId);

  console.log('Seed complete.');
  console.log('  Acme Inc  -> owner@acme.test / password123   (FREE trial)');
  console.log('             -> admin@acme.test / password123');
  console.log('  Globex Corp -> owner@globex.test / password123 (PRO active)');
  console.log('             -> member@globex.test / password123');
} else {
  console.log('Database already seeded. Skipping.');
}
