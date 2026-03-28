// routes/auth.js — All authentication endpoints

const router   = require('express').Router();
const bcrypt   = require('bcryptjs');
const crypto   = require('crypto');
const jwt      = require('jsonwebtoken');
const passport = require('passport');
const { body, validationResult } = require('express-validator');
const { userQueries, tokenQueries } = require('../db');

const SALT_ROUNDS    = 12;
const ACCESS_EXPIRY  = '15m';           // short-lived access token
const REFRESH_EXPIRY = '30d';           // long-lived refresh token
const REFRESH_EXPIRY_MS = 30 * 24 * 60 * 60 * 1000;

const JWT_SECRET     = process.env.JWT_SECRET;
const JWT_REFRESH    = process.env.JWT_REFRESH_SECRET;
const CLIENT_URL     = process.env.CLIENT_URL || 'http://localhost:3000';

if (!JWT_SECRET || !JWT_REFRESH) {
  throw new Error('JWT_SECRET and JWT_REFRESH_SECRET must be set in .env');
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function safeUser(u) {
  return { id: u.id, firstName: u.first_name, lastName: u.last_name,
           email: u.email, avatarUrl: u.avatar_url, provider: u.provider };
}

function issueAccessToken(user) {
  return jwt.sign({ sub: user.id, email: user.email }, JWT_SECRET,
    { expiresIn: ACCESS_EXPIRY, issuer: 'resume-matcher' });
}

async function issueRefreshToken(userId) {
  const raw       = crypto.randomBytes(40).toString('hex');
  const hash      = crypto.createHash('sha256').update(raw).digest('hex');
  const expiresAt = new Date(Date.now() + REFRESH_EXPIRY_MS).toISOString();
  tokenQueries.insert.run(userId, hash, expiresAt);
  return raw;                            // return plain — only hash stored in DB
}

function sendTokens(res, user, rememberMe = false) {
  const accessToken  = issueAccessToken(user);
  const store = rememberMe ? 'localStorage' : 'sessionStorage';
  return { accessToken, store };
}

// ─── Validation chains ────────────────────────────────────────────────────────
const registerValidation = [
  body('firstName').trim().isLength({ min: 2, max: 50 }).withMessage('First name must be 2–50 chars'),
  body('lastName').trim().isLength({ min: 1, max: 50 }).withMessage('Last name must be 1–50 chars'),
  body('email').isEmail().normalizeEmail().withMessage('Invalid email address'),
  body('password')
    .isLength({ min: 8 }).withMessage('Password must be at least 8 characters')
    .matches(/[A-Z]/).withMessage('Password must contain an uppercase letter')
    .matches(/[0-9]/).withMessage('Password must contain a number'),
];

const loginValidation = [
  body('email').isEmail().normalizeEmail().withMessage('Invalid email'),
  body('password').notEmpty().withMessage('Password required'),
];

// ─── POST /api/auth/register ─────────────────────────────────────────────────
router.post('/register', registerValidation, async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty())
    return res.status(422).json({ message: errors.array()[0].msg });

  const { firstName, lastName, email, password } = req.body;
  try {
    if (userQueries.findByEmail.get(email))
      return res.status(409).json({ message: 'An account with this email already exists.' });

    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);
    userQueries.create.run({
      firstName, lastName,
      email: email.toLowerCase(),
      passwordHash,
      provider: 'local',
      providerId: null,
      avatarUrl: null,
      isVerified: 0,
    });

    return res.status(201).json({ message: 'Account created. Please sign in.' });
  } catch(err) {
    console.error('Register error:', err);
    return res.status(500).json({ message: 'Server error. Please try again.' });
  }
});

// ─── POST /api/auth/login ─────────────────────────────────────────────────────
router.post('/login', loginValidation, async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty())
    return res.status(422).json({ message: errors.array()[0].msg });

  const { email, password, rememberMe } = req.body;
  try {
    const user = userQueries.findByEmail.get(email);

    // Use same timing even for missing users to prevent user enumeration
    const dummyHash = '$2a$12$KIXoVhDQjKHJ4u1W8XBjEuoVkF2LzVXfRXWRmUeZBKhqMwKjLV4OK';
    const hash      = user?.password_hash || dummyHash;
    const match     = await bcrypt.compare(password, hash);

    if (!user || !match)
      return res.status(401).json({ message: 'Invalid email or password.' });

    if (!user.password_hash)
      return res.status(401).json({
        message: `This account uses ${user.provider} sign-in. Please use that instead.`
      });

    const accessToken  = issueAccessToken(user);
    const refreshToken = await issueRefreshToken(user.id);

    console.log(`✅ Login: ${user.email}`);
    return res.json({
      message: 'Login successful.',
      token: accessToken,
      refreshToken,
      rememberMe: !!rememberMe,
      user: safeUser(user),
    });
  } catch(err) {
    console.error('Login error:', err);
    return res.status(500).json({ message: 'Server error. Please try again.' });
  }
});

// ─── POST /api/auth/refresh ───────────────────────────────────────────────────
router.post('/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  if (!refreshToken) return res.status(401).json({ message: 'No refresh token.' });

  try {
    // Verify JWT signature first
    const payload = jwt.verify(refreshToken, JWT_REFRESH);
    const hash    = crypto.createHash('sha256').update(refreshToken).digest('hex');
    const stored  = tokenQueries.findHash.get(hash);

    if (!stored || new Date(stored.expires_at) < new Date()) {
      if (stored) tokenQueries.deleteById.run(stored.id);
      return res.status(401).json({ message: 'Refresh token expired or invalid.' });
    }

    const user = userQueries.findById.get(payload.sub);
    if (!user) return res.status(401).json({ message: 'User not found.' });

    // Rotate: delete old, issue new
    tokenQueries.deleteById.run(stored.id);
    const newAccess  = issueAccessToken(user);
    const newRefresh = await issueRefreshToken(user.id);

    return res.json({ token: newAccess, refreshToken: newRefresh });
  } catch(err) {
    return res.status(401).json({ message: 'Invalid refresh token.' });
  }
});

// ─── POST /api/auth/logout ────────────────────────────────────────────────────
router.post('/logout', (req, res) => {
  const { refreshToken } = req.body;
  if (refreshToken) {
    const hash = crypto.createHash('sha256').update(refreshToken).digest('hex');
    const row  = tokenQueries.findHash.get(hash);
    if (row) tokenQueries.deleteById.run(row.id);
  }
  return res.json({ message: 'Logged out.' });
});

// ─── Google OAuth ─────────────────────────────────────────────────────────────
router.get('/google', passport.authenticate('google', { scope: ['profile', 'email'] }));

router.get('/google/callback',
  passport.authenticate('google', { failureRedirect: '/?error=google_failed', session: false }),
  async (req, res) => {
    try {
      const user         = req.user;
      const accessToken  = issueAccessToken(user);
      const refreshToken = await issueRefreshToken(user.id);
      // Pass tokens to frontend via query string (or use httpOnly cookie in production)
      res.redirect(`${CLIENT_URL}/?token=${accessToken}&refreshToken=${refreshToken}`);
    } catch(err) {
      res.redirect(`${CLIENT_URL}/?error=${encodeURIComponent(err.message)}`);
    }
  }
);

// ─── GitHub OAuth ─────────────────────────────────────────────────────────────
router.get('/github', passport.authenticate('github', { scope: ['user:email'] }));

router.get('/github/callback',
  passport.authenticate('github', { failureRedirect: '/?error=github_failed', session: false }),
  async (req, res) => {
    try {
      const user         = req.user;
      const accessToken  = issueAccessToken(user);
      const refreshToken = await issueRefreshToken(user.id);
      res.redirect(`${CLIENT_URL}/?token=${accessToken}&refreshToken=${refreshToken}`);
    } catch(err) {
      res.redirect(`${CLIENT_URL}/?error=${encodeURIComponent(err.message)}`);
    }
  }
);

module.exports = router;
