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
      <div className="bg-blur"></div>

      <aside className="lp-side">
        <div className="lp-brand">
          <div className="lp-logo">EA</div>
          <h1>Enterprise AI</h1>
          <p className="lp-tag">
            AI-powered enterprise knowledge management system
          </p>
          <p>
            New user? <span onClick={() => navigate("/signup")}>Create account</span>
          </p>
        </div>
      </aside>

      <main className="lp-main">
        <div className="lp-card">
          <h2>Welcome Back</h2>

          {error && <div className="lp-alert">{error}</div>}

          <form onSubmit={handleLogin}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button type="submit">Login</button>
          </form>
        </div>
      </main>
    </div>
  );
}