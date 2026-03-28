// server.js — AI Resume Matcher Auth Backend
// Stack: Express · bcryptjs · JWT · Passport (Google & GitHub OAuth) · SQLite · Helmet · express-rate-limit

require('dotenv').config();
const express      = require('express');
const helmet       = require('helmet');
const cors         = require('cors');
const rateLimit    = require('express-rate-limit');
const session      = require('express-session');
const passport     = require('passport');
const path         = require('path');
const cookieParser = require('cookie-parser');

// Local modules
require('./config/passport')(passport);   // load strategies
const authRouter  = require('./routes/auth');
const { requireAuth } = require('./middleware/authMiddleware');

const app  = express();
const PORT = process.env.PORT || 3000;

// ─── Security Headers (Helmet) ────────────────────────────────────────────────
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc:  ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
      styleSrc:   ["'self'", "'unsafe-inline'", "fonts.googleapis.com", "fonts.gstatic.com"],
      fontSrc:    ["'self'", "fonts.gstatic.com"],
      imgSrc:     ["'self'", "data:", "*.googleusercontent.com", "avatars.githubusercontent.com"],
      connectSrc: ["'self'"],
    }
  }
}));

// ─── CORS ─────────────────────────────────────────────────────────────────────
app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET','POST','PUT','DELETE','OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// ─── Body / Cookie Parsing ────────────────────────────────────────────────────
app.use(express.json({ limit: '10kb' }));           // limit body size
app.use(express.urlencoded({ extended: true, limit: '10kb' }));
app.use(cookieParser(process.env.COOKIE_SECRET || 'cookie-secret'));

// ─── Session (needed for Passport OAuth flow only) ───────────────────────────
app.use(session({
  secret: process.env.SESSION_SECRET || 'session-secret-change-in-prod',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 10 * 60 * 1000  // 10 min — only for OAuth handshake
  }
}));

// ─── Passport init ────────────────────────────────────────────────────────────
app.use(passport.initialize());
app.use(passport.session());

// ─── Rate Limiting ────────────────────────────────────────────────────────────
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,   // 15 minutes
  max: 20,                     // max 20 requests per window
  message: { message: 'Too many requests, please try again in 15 minutes.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const generalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,
});

app.use(generalLimiter);
app.use('/api/auth', authLimiter);

// ─── Static frontend ─────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, 'public')));

// ─── API Routes ───────────────────────────────────────────────────────────────
app.use('/api/auth', authRouter);

// Protected example: get current user profile
app.get('/api/me', requireAuth, (req, res) => {
  res.json({ user: req.user });
});

// Dashboard — serve after auth (protected)
app.get('/dashboard', requireAuth, (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

// Catch-all → auth page
app.get('*', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ─── Global Error Handler ─────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error('Unhandled error:', err.message);
  res.status(err.status || 500).json({ message: err.message || 'Internal server error.' });
});

// ─── Start ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 Resume Matcher Auth Server running at http://localhost:${PORT}`);
  console.log(`\n   Auth Routes:`);
  console.log(`   POST   /api/auth/register`);
  console.log(`   POST   /api/auth/login`);
  console.log(`   POST   /api/auth/refresh`);
  console.log(`   POST   /api/auth/logout`);
  console.log(`   GET    /api/auth/google`);
  console.log(`   GET    /api/auth/github`);
  console.log(`   GET    /api/auth/google/callback`);
  console.log(`   GET    /api/auth/github/callback`);
  console.log(`   GET    /api/me   (protected)\n`);
});
