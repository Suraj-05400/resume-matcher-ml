// middleware/authMiddleware.js — JWT verification for protected routes

const jwt = require('jsonwebtoken');
const { userQueries } = require('../db');

/**
 * requireAuth — attach req.user or return 401
 * Accepts token from:
 *   1. Authorization: Bearer <token>   (API clients)
 *   2. ?token=<token>                  (OAuth redirect — one-time use)
 */
function requireAuth(req, res, next) {
  let token = null;

  const authHeader = req.headers.authorization;
  if (authHeader?.startsWith('Bearer ')) {
    token = authHeader.split(' ')[1];
  }

  if (!token) return res.status(401).json({ message: 'Authentication required.' });

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET, {
      issuer: 'resume-matcher',
    });

    const user = userQueries.findById.get(payload.sub);
    if (!user) return res.status(401).json({ message: 'User no longer exists.' });

    req.user = {
      id:        user.id,
      firstName: user.first_name,
      lastName:  user.last_name,
      email:     user.email,
      avatarUrl: user.avatar_url,
      provider:  user.provider,
    };
    next();
  } catch(err) {
    if (err.name === 'TokenExpiredError')
      return res.status(401).json({ message: 'Token expired. Please refresh.' });
    return res.status(401).json({ message: 'Invalid token.' });
  }
}

/**
 * optionalAuth — like requireAuth but doesn't block unauthenticated requests.
 * Useful for routes that behave differently for logged-in users.
 */
function optionalAuth(req, _res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) return next();
  try {
    const payload = jwt.verify(authHeader.split(' ')[1], process.env.JWT_SECRET);
    req.user = userQueries.findById.get(payload.sub) || null;
  } catch { /* ignore */ }
  next();
}

module.exports = { requireAuth, optionalAuth };
