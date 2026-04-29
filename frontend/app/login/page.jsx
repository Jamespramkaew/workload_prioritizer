'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const url = `${API_URL}/auth/${mode === 'login' ? 'login' : 'register'}`;
    const body = mode === 'login'
      ? { email, password }
      : { email, password, display_name: displayName };

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg = data.message || data.detail || `Request failed (${res.status})`;
        setError(typeof msg === 'string' ? msg : 'Validation failed');
        return;
      }

      router.push('/');
    } catch (err) {
      setError('Cannot reach the server. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const toggle = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
  };

  return (
    <div className="auth">
      <div className="auth-card">
        <div className="auth-mark" />
        <h1>{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
        <p className="auth-tagline">
          {mode === 'login'
            ? 'See your week before it sees you.'
            : 'Plan your week, smarter.'}
        </p>

        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <div className="auth-field">
              <label>Display name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="James"
                required
                autoComplete="name"
                autoFocus
              />
            </div>
          )}

          <div className="auth-field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
              autoFocus={mode === 'login'}
            />
          </div>

          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              required
              minLength={6}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading
              ? '...'
              : mode === 'login'
                ? 'Sign in →'
                : 'Create account →'}
          </button>
        </form>

        <button type="button" className="auth-toggle" onClick={toggle}>
          {mode === 'login'
            ? "Don't have an account? Sign up"
            : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  );
}
