import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import "./SettingsPage.css";

export default function VerifyOTP() {
  const nav = useNavigate();
  const location = useLocation();
  const initialEmail = location.state?.email || "";

  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    if (!email || !otp) {
      setMessage("Email and OTP required");
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
      setMessage(err.response?.data?.detail || "OTP verification failed");
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
            <h1>Verify OTP</h1>
          </div>
        </div>

        {message && <div className="settings-alert">{message}</div>}

        <div className="settings-grid">
          <section className="settings-card settings-form-card">
            <div className="settings-field">
              <label>Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>

            <div className="settings-field">
              <label>OTP</label>
              <input value={otp} onChange={(e) => setOtp(e.target.value)} />
            </div>

            <button className="save-btn" onClick={submit}>
              Verify OTP
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
