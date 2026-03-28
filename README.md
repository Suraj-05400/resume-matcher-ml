# AI Resume Matcher — Auth System

A production-grade authentication layer built for the **AI Resume Matcher** Streamlit app, featuring:
- Email/password login with **bcrypt** password hashing
- **JWT access tokens** (15 min) + **refresh tokens** (30 days) with rotation
- **Google OAuth 2.0** and **GitHub OAuth** via Passport.js
- **SQLite** database (swap for Postgres/Mongo in production)
- **Helmet** security headers, **CORS**, **rate limiting**
- Input validation with **express-validator**

---

## Project Structure

```
resume-auth/
├── public/
│   └── index.html          ← Login / Register frontend
├── routes/
│   └── auth.js             ← All auth endpoints
├── middleware/
│   └── authMiddleware.js   ← JWT verify middleware
├── config/
│   └── passport.js         ← Google & GitHub strategies
├── db.js                   ← SQLite setup & queries
├── server.js               ← Express app entry point
├── package.json
├── .env.example            ← Copy to .env and fill in
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
```bash
cp .env.example .env
```
Generate secure secrets:
```bash
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```
Run it twice — one for `JWT_SECRET`, one for `JWT_REFRESH_SECRET`.

### 3. Set up Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services → Credentials**
3. Click **Create Credentials → OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add Authorized redirect URI: `http://localhost:3000/api/auth/google/callback`
6. Copy **Client ID** and **Client Secret** into `.env`

### 4. Set up GitHub OAuth
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Set **Authorization callback URL**: `http://localhost:3000/api/auth/github/callback`
4. Copy **Client ID** and generate/copy **Client Secret** into `.env`

### 5. Start the server
```bash
node server.js
# or with auto-reload:
npm run dev
```

Open `http://localhost:3000` — the auth page is served automatically.

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | ❌ | Create account |
| POST | `/api/auth/login` | ❌ | Sign in, get tokens |
| POST | `/api/auth/refresh` | ❌ | Rotate refresh token |
| POST | `/api/auth/logout` | ❌ | Invalidate refresh token |
| GET | `/api/auth/google` | ❌ | Start Google OAuth |
| GET | `/api/auth/github` | ❌ | Start GitHub OAuth |
| GET | `/api/me` | ✅ Bearer | Get current user |

### Register
```json
POST /api/auth/register
{
  "firstName": "Jane",
  "lastName": "Doe",
  "email": "jane@example.com",
  "password": "MyPass123!"
}
→ 201: { "message": "Account created. Please sign in." }
```

### Login
```json
POST /api/auth/login
{
  "email": "jane@example.com",
  "password": "MyPass123!",
  "rememberMe": true
}
→ 200: {
    "token": "eyJ...",
    "refreshToken": "abc123...",
    "user": { "id": 1, "firstName": "Jane", ... }
  }
```

### Refresh Token
```json
POST /api/auth/refresh
{ "refreshToken": "abc123..." }
→ 200: { "token": "eyJ...", "refreshToken": "newtoken..." }
```

### Protected Route Example
```
GET /api/me
Authorization: Bearer eyJ...
→ 200: { "user": { "id": 1, "firstName": "Jane", ... } }
```

---

## Security Architecture

| Layer | Implementation |
|-------|---------------|
| Password hashing | bcrypt, 12 salt rounds |
| Access tokens | JWT, 15 min expiry, HS256 |
| Refresh tokens | SHA-256 hashed in DB, 30-day rotation |
| User enumeration | Constant-time compare on wrong email |
| Brute force | Rate limit: 20 req / 15 min on `/api/auth/*` |
| Headers | Helmet (CSP, HSTS, X-Frame-Options, etc.) |
| Input sanitization | express-validator on all inputs |
| Body size | 10KB limit (prevents large payload attacks) |
| OAuth sessions | Short-lived (10 min) — only for handshake |

---

## Connecting to the Streamlit App

After login, redirect users to your Streamlit app URL with the JWT in the URL or a session:
```javascript
// In index.html after successful login:
window.location.href = 'https://resume-matcher-ml-s4s4xeprcxhvvpneggeoc5.streamlit.app';
```

Or protect the Streamlit app behind a proxy that validates the JWT before forwarding requests.

---

## Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Use strong, unique `JWT_SECRET` and `JWT_REFRESH_SECRET`
- [ ] Restrict `CLIENT_URL` to your actual domain
- [ ] Switch from SQLite to PostgreSQL (`pg` + `knex` or `prisma`)
- [ ] Enable HTTPS (TLS termination via Nginx or your cloud provider)
- [ ] Set `cookie.secure = true` in session config
- [ ] Add email verification flow
- [ ] Add account lockout after N failed login attempts
- [ ] Store secrets in a vault (AWS Secrets Manager, Doppler, etc.)
- [ ] Set up logging (Winston / Pino)
- [ ] Update OAuth callback URLs to production domain
