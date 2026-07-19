import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import "./LoginPage.css"; // Reuse the landing page styles

export default function VerifyOTP() {
  const nav = useNavigate();
  const location = useLocation();
  const initialEmail = location.state?.email || "";

  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!email.trim() || !otp.trim()) {
      setError("Email and OTP required");
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/verify-otp", { email, otp });
      const token = res.data.reset_token;
      if (token) {
        // navigate to reset page with token
        nav("/reset-password", { state: { reset_token: token, email } });
      } else {
        setMessage("OTP verified");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "OTP verification failed");
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
          <h1>Verify OTP.</h1>
          <p className="lp-tag">
            Enter the 6-digit code sent to your email to verify your identity.
          </p>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <div className="lp-card-header">
            <p className="lp-card-kicker">Security</p>
            <h2>Verify Identity</h2>
            <p>Enter your email and the verification code.</p>
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

            <div className="input-wrap">
              <label>One-Time Password (OTP)</label>
              <input
                type="text"
                placeholder="123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
              />
            </div>

            <div className="lp-row">
              <button
                type="button"
                className="lp-link-btn"
                onClick={() => nav("/login")}
              >
                ← Back to Login
              </button>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
