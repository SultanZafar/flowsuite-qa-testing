// Demo-only auth middleware. Base64 token (NOT a real JWT, NOT secure) to
// keep the project dependency-light for QA practice.
module.exports = function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = Buffer.from(token, 'base64').toString('utf8');
    const userId = Number(decoded.split(':')[1]);
    if (!userId) throw new Error('bad token');
    req.userId = userId;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};
