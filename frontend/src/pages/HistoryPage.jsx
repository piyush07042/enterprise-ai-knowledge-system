import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/history", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setHistory(res.data);
    } catch (err) {
      console.log(err);
    }
  };

  return (
    <div style={{ padding: "40px", background: "#081226", color: "white", minHeight: "100vh" }}>
      <button onClick={() => navigate("/dashboard")}>← Back</button>

      <h1>Search History</h1>

      {history.length === 0 ? (
        <p>No history found</p>
      ) : (
        history.map((item) => (
          <div
            key={item.id}
            style={{
              marginTop: "20px",
              background: "#1e293b",
              padding: "20px",
              borderRadius: "12px"
            }}
          >
            <h3>Query:</h3>
            <p>{item.query}</p>

            <h3>Answer:</h3>
            <p>{item.answer}</p>
          </div>
        ))
      )}
    </div>
  );
}