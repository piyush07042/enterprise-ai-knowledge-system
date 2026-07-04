import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function SettingsPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/settings", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setUsername(res.data.username);
      setEmail(res.data.email);
    } catch (err) {
      console.log(err);
    }
  };

  const saveChanges = async () => {
    try {
      const token = localStorage.getItem("token");

      await api.put(
        "/settings",
        {
          username,
          email,
          password,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      localStorage.setItem("email", email);

      alert("Updated successfully");
      navigate("/dashboard");
    } catch (err) {
      alert("Update failed");
    }
  };

  return (
    <div
      style={{
        padding: "40px",
        background: "#081226",
        minHeight: "100vh",
        color: "white"
      }}
    >
      <button onClick={() => navigate("/dashboard")}>
        ← Back
      </button>

      <h1>Settings</h1>

      <div style={{ marginTop: "20px" }}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={{ display: "block", margin: "15px 0", padding: "15px", width: "300px" }}
        />

        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          style={{ display: "block", margin: "15px 0", padding: "15px", width: "300px" }}
        />

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="New Password"
          style={{ display: "block", margin: "15px 0", padding: "15px", width: "300px" }}
        />

        <button onClick={saveChanges}>
          Save Changes
        </button>
      </div>
    </div>
  );
}