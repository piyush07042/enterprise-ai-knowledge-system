import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import "./LoginPage.css";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("Email required");
      return;
    }

    if (!password.trim()) {
      setError("Password required");
      return;
    }

    setLoading(true);

    try {
      const response = await api.post("/login", { email, password });

      const token =
        response.data.access_token ||
        response.data.token ||
        response.data.jwt;

      if (token) {
        localStorage.setItem("token", token);
        localStorage.setItem("email", email);
        navigate("/dashboard");
      } else {
        setError("Token not received");
        setLoading(false);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Login failed"
      );
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className="lp-root">
      <div className="lp-orb lp-orb-a"></div>
      <div className="lp-orb lp-orb-b"></div>

      <aside className="lp-side">
        <div className="lp-brand">
          <div className="lp-logo">EA</div>
          <p className="lp-eyebrow">Enterprise AI Knowledge System</p>
          <h1>Secure documents. Faster answers.</h1>
          <p className="lp-tag">
            Centralize files, search with AI, and keep every knowledge asset
            tied to the right user and audit trail.
          </p>

          <div className="lp-points">
            <div className="lp-point">
              <span>01</span>
              <div>
                <strong>Private uploads</strong>
                <p>PDF and text files indexed per user.</p>
              </div>
            </div>
            <div className="lp-point">
              <span>02</span>
              <div>
                <strong>Semantic search</strong>
                <p>Ask natural-language questions across your library.</p>
              </div>
            </div>
            <div className="lp-point">
              <span>03</span>
              <div>
                <strong>History and analytics</strong>
                <p>Track usage and recent retrievals from the dashboard.</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <div className="lp-card-header">
            <p className="lp-card-kicker">Welcome back</p>
            <h2>Sign in to continue</h2>
            <p>Access your workspace, documents, and AI search tools.</p>
          </div>

          {error && <div className="lp-alert">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="input-wrap">
              <label>Email address</label>
              <input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="input-wrap password-wrap">
              <label>Password</label>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />

              <button
                type="button"
                className="eye-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>

            <div className="lp-row">
              <p className="lp-remember">Session secured with JWT auth</p>
              <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
                <button
                  type="button"
                  className="lp-link-btn"
                  onClick={() => navigate("/signup")}
                >
                  Create account
                </button>

                <button
                  type="button"
                  className="lp-link-btn"
                  onClick={() => navigate("/forgot-password")}
                >
                  Forgot Password?
                </button>
              </div>
            </div>

            <button type="submit" className="login-btn">
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}