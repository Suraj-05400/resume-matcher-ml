// config/passport.js — Google & GitHub OAuth2 strategies

const GoogleStrategy = require('passport-google-oauth20').Strategy;
const GitHubStrategy = require('passport-github2').Strategy;
const { userQueries } = require('../db');

module.exports = (passport) => {

  // Passport only needs to serialise/deserialise for the brief OAuth session
  passport.serializeUser((user, done) => done(null, user.id));
  passport.deserializeUser((id, done) => {
    try { done(null, userQueries.findById.get(id) || false); }
    catch(e) { done(e); }
  });

  // ─── Google Strategy ───────────────────────────────────────────────────────
  passport.use(new GoogleStrategy({
    clientID:     process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL:  process.env.GOOGLE_CALLBACK_URL || '/api/auth/google/callback',
    scope: ['profile', 'email'],
  }, async (_accessToken, _refreshToken, profile, done) => {
    try {
      const email     = profile.emails?.[0]?.value?.toLowerCase();
      const avatarUrl = profile.photos?.[0]?.value;
      const firstName = profile.name?.givenName || profile.displayName?.split(' ')[0] || 'User';
      const lastName  = profile.name?.familyName || profile.displayName?.split(' ').slice(1).join(' ') || '';

      // 1. Try find by Google provider ID
      let user = userQueries.findByProvider.get('google', profile.id);

      // 2. Try find by email (account may exist with password)
      if (!user && email) user = userQueries.findByEmail.get(email);

      // 3. Create new user
      if (!user) {
        const result = userQueries.create.run({
          firstName, lastName, email,
          passwordHash: null,
          provider: 'google',
          providerId: profile.id,
          avatarUrl,
          isVerified: 1,
        });
        user = userQueries.findById.get(result.lastInsertRowid);
      } else {
        // Update avatar if missing
        if (!user.avatar_url && avatarUrl) userQueries.updateAvatar.run(avatarUrl, user.id);
      }

      return done(null, user);
    } catch(err) {
      return done(err);
    }
  }));

  // ─── GitHub Strategy ──────────────────────────────────────────────────────
  passport.use(new GitHubStrategy({
    clientID:     process.env.GITHUB_CLIENT_ID,
    clientSecret: process.env.GITHUB_CLIENT_SECRET,
    callbackURL:  process.env.GITHUB_CALLBACK_URL || '/api/auth/github/callback',
    scope: ['user:email'],
  }, async (_accessToken, _refreshToken, profile, done) => {
    try {
      const email     = profile.emails?.[0]?.value?.toLowerCase();
      const avatarUrl = profile.photos?.[0]?.value;
      const nameParts = (profile.displayName || profile.username || 'User').split(' ');
      const firstName = nameParts[0];
      const lastName  = nameParts.slice(1).join(' ');

      let user = userQueries.findByProvider.get('github', profile.id.toString());

      if (!user && email) user = userQueries.findByEmail.get(email);

      if (!user) {
        const result = userQueries.create.run({
          firstName, lastName,
          email: email || `gh_${profile.id}@noemail.local`,
          passwordHash: null,
          provider: 'github',
          providerId: profile.id.toString(),
          avatarUrl,
          isVerified: 1,
        });
        user = userQueries.findById.get(result.lastInsertRowid);
      } else {
        if (!user.avatar_url && avatarUrl) userQueries.updateAvatar.run(avatarUrl, user.id);
      }

      return done(null, user);
    } catch(err) {
      return done(err);
    }
  }));
};
