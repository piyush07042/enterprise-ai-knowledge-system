import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import "./SettingsPage.css";

export default function ResetPassword() {
  const nav = useNavigate();
  const location = useLocation();
  const reset_token = location.state?.reset_token || "";
  const email = location.state?.email || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const validateStrength = (p) => {
    if (p.length < 8) return false;
    if (!/[A-Za-z]/.test(p)) return false;
    if (!/[0-9]/.test(p)) return false;
    return true;
  };

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    if (!reset_token) {
      setMessage("Missing reset token. Start the flow again.");
      return;
    }
    if (password !== confirm) {
      setMessage("Passwords do not match");
      return;
    }
    if (!validateStrength(password)) {
      setMessage("Password must be at least 8 chars and include letters and numbers");
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
      setMessage(err.response?.data?.detail || "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingScreen />;

  return (
    <div className="settings-page">
      <div className="settings-shell">
        <div className="settings-topbar">
          <button className="settings-back" onClick={() => nav(-1)}>
            ← Back
          </button>
          <div>
            <p className="settings-eyebrow">Password</p>
            <h1>Reset Password</h1>
          </div>
        </div>

        {message && <div className="settings-alert">{message}</div>}

        <div className="settings-grid">
          <section className="settings-card settings-form-card">
            <div className="settings-field">
              <label>New password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="settings-field">
              <label>Confirm password</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>

            <button className="save-btn" onClick={submit}>
              Reset password
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
