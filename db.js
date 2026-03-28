// db.js — SQLite database initialisation
// Uses better-sqlite3 (synchronous, zero-config, perfect for local/small-team apps)
// Swap with PostgreSQL / MongoDB for larger scale

const Database = require('better-sqlite3');
const path     = require('path');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'auth.db');

// Ensure the data directory exists
const fs = require('fs');
const dir = path.dirname(DB_PATH);
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

const db = new Database(DB_PATH);

// Enable WAL mode for better concurrency
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

// ─── Schema ──────────────────────────────────────────────────────────────────
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT,                           -- NULL for OAuth-only users
    provider        TEXT    NOT NULL DEFAULT 'local', -- 'local' | 'google' | 'github'
    provider_id     TEXT,                           -- OAuth provider user ID
    avatar_url      TEXT,
    is_verified     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT    NOT NULL UNIQUE,            -- we store hash, not plain token
    expires_at  TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
  );

  CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email);
  CREATE INDEX IF NOT EXISTS idx_refresh_user_id  ON refresh_tokens(user_id);
  CREATE INDEX IF NOT EXISTS idx_refresh_token    ON refresh_tokens(token_hash);
`);

// ─── User helpers ─────────────────────────────────────────────────────────────
const userQueries = {
  findById:    db.prepare('SELECT * FROM users WHERE id = ?'),
  findByEmail: db.prepare('SELECT * FROM users WHERE email = ? COLLATE NOCASE'),
  findByProvider: db.prepare('SELECT * FROM users WHERE provider = ? AND provider_id = ?'),

  create: db.prepare(`
    INSERT INTO users (first_name, last_name, email, password_hash, provider, provider_id, avatar_url, is_verified)
    VALUES (@firstName, @lastName, @email, @passwordHash, @provider, @providerId, @avatarUrl, @isVerified)
  `),

  updateAvatar: db.prepare('UPDATE users SET avatar_url = ?, updated_at = datetime("now") WHERE id = ?'),
};

// ─── Refresh token helpers ────────────────────────────────────────────────────
const tokenQueries = {
  insert:    db.prepare('INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)'),
  findHash:  db.prepare('SELECT * FROM refresh_tokens WHERE token_hash = ?'),
  deleteById:db.prepare('DELETE FROM refresh_tokens WHERE id = ?'),
  deleteByUser: db.prepare('DELETE FROM refresh_tokens WHERE user_id = ?'),
  cleanup:   db.prepare("DELETE FROM refresh_tokens WHERE expires_at < datetime('now')"),
};

// Auto-clean expired tokens every hour
setInterval(() => tokenQueries.cleanup.run(), 60 * 60 * 1000);

module.exports = { db, userQueries, tokenQueries };
