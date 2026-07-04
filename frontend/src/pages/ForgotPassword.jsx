import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import "./SettingsPage.css";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    if (!email) {
      setMessage("Email is required");
      return;
    }

    try {
      setLoading(true);
      const res = await api.post("/forgot-password", { email });
      setMessage(res.data.message || "If the email exists, an OTP was sent.");
      // move to verify view, keep email in state
      navigate("/verify-otp", { state: { email } });
    } catch (err) {
      setMessage(err.response?.data?.detail || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingScreen />;

  return (
    <div className="settings-page">
      <div className="settings-shell">
        <div className="settings-topbar">
          <button className="settings-back" onClick={() => navigate(-1)}>
            ← Back
          </button>
          <div>
            <p className="settings-eyebrow">Password</p>
            <h1>Forgot Password</h1>
          </div>
        </div>

        {message && <div className="settings-alert">{message}</div>}

        <div className="settings-grid">
          <section className="settings-card settings-form-card">
            <div className="settings-field">
              <label>Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>

            <button className="save-btn" onClick={submit}>
              Send OTP
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
