import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import "./LoginPage.css"; // Reuse the landing page styles

export default function ResetPassword() {
  const nav = useNavigate();
  const location = useLocation();
  const reset_token = location.state?.reset_token || "";
  const email = location.state?.email || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const validateStrength = (p) => {
    if (p.length < 8) return false;
    if (!/[A-Za-z]/.test(p)) return false;
    if (!/[0-9]/.test(p)) return false;
    return true;
  };

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!reset_token) {
      setError("Missing reset token. Start the flow again.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (!validateStrength(password)) {
      setError("Password must be at least 8 chars and include letters and numbers");
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/reset-password", {
        reset_token,
        new_password: password,
      });

      setMessage(res.data.message || "Password reset successfully");
      // go to login
      setTimeout(() => nav("/login"), 1200);
    } catch (err) {
      setError(err.response?.data?.detail || "Reset failed");
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
          <h1>Secure your account.</h1>
          <p className="lp-tag">
            Choose a strong password to protect your knowledge assets.
          </p>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <div className="lp-card-header">
            <p className="lp-card-kicker">Security</p>
            <h2>Reset Password</h2>
            <p>Enter your new password below.</p>
          </div>

          {error && <div className="lp-alert">{error}</div>}
          {message && <div className="lp-alert" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.2)'}}>{message}</div>}

          <form onSubmit={submit}>
            <div className="input-wrap password-wrap">
              <label>New password</label>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Must be at least 8 characters"
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

            <div className="input-wrap password-wrap">
              <label>Confirm password</label>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Confirm your new password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
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
              {loading ? "Resetting..." : "Reset password"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
