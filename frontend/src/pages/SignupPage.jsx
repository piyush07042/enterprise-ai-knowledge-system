import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./LoginPage.css"; // Reuse the landing page styles

export default function SignupPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");

    if (!username.trim() || !email.trim() || !password.trim()) {
      setError("All fields are required");
      return;
    }

    try {
      setLoading(true);
      await api.post("/register", {
        username,
        email,
        password,
      });

      alert("Account created successfully. Please login.");
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lp-root">
      <div className="lp-orb lp-orb-a"></div>
      <div className="lp-orb lp-orb-b"></div>

      <aside className="lp-side">
        <div className="lp-brand">
          <div className="lp-logo">EA</div>
          <p className="lp-eyebrow">Enterprise AI Knowledge System</p>
          <h1>Join the workspace.</h1>
          <p className="lp-tag">
            Upload documents, extract knowledge, and streamline your workflow with AI.
          </p>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <div className="lp-card-header">
            <p className="lp-card-kicker">Create account</p>
            <h2>Get Started</h2>
            <p>Create a new account to access the platform.</p>
          </div>

          {error && <div className="lp-alert">{error}</div>}

          <form onSubmit={handleSignup}>
            <div className="input-wrap">
              <label>Username</label>
              <input
                type="text"
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>

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
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
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
              <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
                <span className="lp-remember" style={{marginRight: '8px'}}>Already have an account?</span>
                <button
                  type="button"
                  className="lp-link-btn"
                  onClick={() => navigate("/login")}
                >
                  Log in
                </button>
              </div>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Creating..." : "Create Account"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}