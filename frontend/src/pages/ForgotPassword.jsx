import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./LoginPage.css"; // Reuse the landing page styles

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!email.trim()) {
      setError("Email is required");
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/forgot-password", { email });
      // move to verify view, keep email in state
      navigate("/verify-otp", { state: { email } });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send OTP");
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
          <h1>Password Recovery.</h1>
          <p className="lp-tag">
            We will send a secure One-Time Password to your email to verify your identity.
          </p>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <div className="lp-card-header">
            <p className="lp-card-kicker">Security</p>
            <h2>Forgot Password</h2>
            <p>Enter your email to receive an OTP.</p>
          </div>

          {error && <div className="lp-alert">{error}</div>}
          {message && <div className="lp-alert" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.2)'}}>{message}</div>}

          <form onSubmit={submit}>
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

            <div className="lp-row">
              <button
                type="button"
                className="lp-link-btn"
                onClick={() => navigate("/login")}
              >
                ← Back to Login
              </button>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Sending..." : "Send OTP"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
