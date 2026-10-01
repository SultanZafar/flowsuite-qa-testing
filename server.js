const express = require('express');
const cors = require('cors');
const path = require('path');

require('./db/db');
require('./db/seed');

const authRoutes = require('./routes/auth');
const orgRoutes = require('./routes/orgs');
const memberRoutes = require('./routes/members');
const billingRoutes = require('./routes/billing');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/api/auth', authRoutes);
app.use('/api/orgs', orgRoutes);
app.use('/api/orgs', memberRoutes);
app.use('/api/orgs', billingRoutes);

app.get('/health', (req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`FlowSuite server running at http://localhost:${PORT}`);
});
