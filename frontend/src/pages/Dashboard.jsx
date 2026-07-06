
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
  const [profilePictureSrc, setProfilePictureSrc] = useState(null);

const [stats, setStats] = useState({
  documents: 0,
  vectors: 0,
  queries: 0,
  history: 0,
  avg_latency: 0,
  avg_confidence: 0,
  most_searched_doc: "N/A",
  top_keyword: "N/A",
});

  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      await fetchUser();
      await fetchDocuments();
      await fetchStats();
      await fetchHistoryCount();
      setPageLoading(false);
    };

    loadData();
  }, []);

  useEffect(() => {
    return () => {
      if (profilePictureSrc) {
        URL.revokeObjectURL(profilePictureSrc);
      }
    };
  }, [profilePictureSrc]);

  const loadProfilePicture = async (profilePictureUrl) => {
    try {
      if (profilePictureSrc) {
        URL.revokeObjectURL(profilePictureSrc);
        setProfilePictureSrc(null);
      }

      const token = localStorage.getItem("token");
      const res = await api.get(profilePictureUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: "blob",
      });

      const objectUrl = URL.createObjectURL(res.data);
      setProfilePictureSrc(objectUrl);
    } catch (err) {
      console.log(err);
      setProfilePictureSrc(null);
    }
  };

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setUsername(res.data.username || "User");
      if (res.data.profile_picture_url) {
        await loadProfilePicture(res.data.profile_picture_url);
      } else {
        setProfilePictureSrc(null);
      }
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

    setStats({
      documents: Number(res.data.documents || 0),
      vectors: Number(res.data.vectors || 0),
      queries: Number(res.data.queries || 0),
      history: Number(res.data.history || 0),
      avg_latency: res.data.avg_latency || 0,
      avg_confidence: res.data.avg_confidence || 0,
      most_searched_doc: res.data.most_searched_doc || "N/A",
      top_keyword: res.data.top_keyword || "N/A",
    });
  } catch (err) {
    console.log(err);
  }
};
      
  try {
    const token = localStorage.getItem("token");

    const res = await api.get("/dashboard-stats", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    setStats({
      documents: Number(res.data.documents || 0),
      vectors: Number(res.data.vectors || 0),
      queries: Number(res.data.queries || 0),
      history: Number(res.data.history || 0),
      avg_latency: res.data.avg_latency || 0,
      avg_confidence: res.data.avg_confidence || 0,
      most_searched_doc: res.data.most_searched_doc || "N/A",
      top_keyword: res.data.top_keyword || "N/A",
    });
  } catch (err) {
    console.log(err);
  }
;

const fetchHistoryCount = async () => {
  try {

  const fetchHistoryCount = async () => {
  try {
    const token = localStorage.getItem("token");

    const res = await api.get("/history", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    setStats((prev) => ({
      ...prev,
      history: Array.isArray(res.data) ? res.data.length : 0,
    }));
  } catch (err) {
    console.log(err);
  }
};

  const goToUpload = () => navigate("/upload");
  const goToSearch = () => navigate("/search");
  const goToChat = () => navigate("/chat");
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
          <button onClick={goToChat}>Chat</button>
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

            {profilePictureSrc ? (
              <img
                className="avatar avatar-image"
                src={profilePictureSrc}
                alt="Profile"
              />
            ) : (
              <div className="avatar">
                {username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
        </header>

        <div className="card">
  <h3>Avg Latency</h3>
  <p className="stat-number">
    {stats.avg_latency.toFixed(2)} s
  </p>
</div>

<div className="card">
  <h3>Confidence</h3>
  <p className="stat-number">
    {stats.avg_confidence}%
  </p>
</div>

<div className="card">
  <h3>Top Document</h3>
  <p>{stats.most_searched_doc}</p>
</div>

<div className="card">
  <h3>Top Keyword</h3>
  <p>{stats.top_keyword}</p>
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