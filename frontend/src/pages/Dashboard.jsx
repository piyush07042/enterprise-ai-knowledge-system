
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import "./Dashboard.css";

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [username, setUsername] = useState("User");
  const [lightMode, setLightMode] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  const [stats, setStats] = useState({
    documents: 0,
    vectors: 0,
    queries: 0,
    history: 0,
  });

  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      await fetchUser();
      await fetchDocuments();
      await fetchStats();
      setPageLoading(false);
    };

    loadData();
  }, []);

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setUsername(res.data.username || "User");
    } catch (err) {
      console.log(err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/documents", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setDocuments(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.log(err);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/dashboard-stats", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setStats(res.data);
    } catch (err) {
      console.log(err);
    }
  };

  const goToUpload = () => navigate("/upload");
  const goToSearch = () => navigate("/search");
  const goToFiles = () => navigate("/files");
  const goToSettings = () => navigate("/settings");
  const goToHistory = () => navigate("/history");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    navigate("/login");
  };

  const toggleTheme = () => {
    document.body.classList.toggle("light-mode");
    setLightMode(!lightMode);
  };

  if (pageLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div>
          <h2>Enterprise AI</h2>
          <p className="sidebar-subtitle">Knowledge Workspace</p>
        </div>

        <nav>
          <button onClick={goToUpload}>📤 Upload Documents</button>
          <button onClick={goToSearch}>🔍 AI Search</button>
          <button onClick={goToFiles}>📄 Files</button>
          <button onClick={goToHistory}>🕘 History</button>
          <button onClick={goToSettings}>⚙ Settings</button>
          <button onClick={handleLogout}>🚪 Logout</button>
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1 className="main-title">Dashboard</h1>
            <p>Welcome back, {username}</p>
          </div>

          <div className="top-actions">
            <button className="theme-btn" onClick={toggleTheme}>
              {lightMode ? "🌙" : "☀"}
            </button>

            <div className="avatar">
              {username.charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        <div className="stats">
          <div className="card">
            <h3>Documents</h3>
            <p className="stat-number">{stats.documents}</p>
          </div>

          <div className="card">
            <h3>Vectors</h3>
            <p className="stat-number">{stats.vectors}</p>
          </div>

          <div className="card">
            <h3>Queries</h3>
            <p className="stat-number">{stats.queries}</p>
          </div>

          <div className="card">
            <h3>History</h3>
            <p className="stat-number">{stats.history}</p>
          </div>
        </div>

        <div className="documents">
          <h2>Recent Documents</h2>

          {documents.length === 0 ? (
            <p>No documents uploaded yet</p>
          ) : (
            documents.slice(0, 5).map((doc) => (
              <div key={doc.id} className="doc-card">
                📄 {doc.filename}
              </div>
            ))
          )}
        </div>

        <div className="response-box">
          <h2>Quick Actions</h2>
          <p>
            Upload documents, ask AI questions, preview files,
            manage your account and view search history.
          </p>
        </div>
      </main>
    </div>
  );
}
