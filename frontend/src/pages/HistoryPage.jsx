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
    <div style={{ padding: "40px", background: "#081226", color: "white", minHeight: "100vh", fontFamily: "Inter, sans-serif" }}>
      <button 
        onClick={() => navigate("/dashboard")}
        style={{
          background: "rgba(255,255,255,0.07)",
          border: "1px solid rgba(255,255,255,0.1)",
          color: "#cbd5e1",
          padding: "8px 16px",
          borderRadius: "8px",
          cursor: "pointer",
          marginBottom: "20px"
        }}
      >
        ← Back to Dashboard
      </button>

      <h1 style={{ marginBottom: "30px", fontWeight: "700" }}>Search History</h1>

      {history.length === 0 ? (
        <p style={{ color: "#94a3b8" }}>No history found</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {history.map((item) => (
            <div
              key={item.id}
              style={{
                background: "#111827",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                padding: "24px",
                borderRadius: "16px",
                position: "relative"
              }}
            >
              {item.timestamp && (
                <div style={{
                  position: "absolute",
                  top: "24px",
                  right: "24px",
                  fontSize: "12px",
                  color: "#64748b"
                }}>
                  {item.timestamp}
                </div>
              )}

              <h3 style={{ margin: "0 0 8px 0", color: "#38bdf8", fontSize: "14px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Query</h3>
              <p style={{ margin: "0 0 20px 0", fontSize: "16px", color: "#f8fafc", fontWeight: "500" }}>{item.query}</p>

              <h3 style={{ margin: "0 0 8px 0", color: "#10b981", fontSize: "14px", textTransform: "uppercase", letterSpacing: "0.05em" }}>AI Answer</h3>
              <p style={{ margin: "0 0 20px 0", fontSize: "15px", color: "#cbd5e1", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>{item.answer}</p>

              <div style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "24px",
                paddingTop: "16px",
                borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                fontSize: "13px",
                color: "#94a3b8"
              }}>
                {item.latency !== null && item.latency !== undefined && (
                  <div>
                    Latency: <strong style={{ color: "#cbd5e1" }}>{item.latency}s</strong>
                  </div>
                )}
                {item.confidence !== null && item.confidence !== undefined && (
                  <div>
                    Confidence: <strong style={{ color: "#cbd5e1" }}>{item.confidence}%</strong>
                  </div>
                )}
                {item.retrieved_docs && item.retrieved_docs.length > 0 && (
                  <div style={{ width: "100%", marginTop: "8px" }}>
                    Retrieved Documents:{" "}
                    {item.retrieved_docs.map((doc, idx) => (
                      <span
                        key={idx}
                        style={{
                          background: "rgba(56, 189, 248, 0.1)",
                          color: "#38bdf8",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          marginLeft: "6px",
                          fontSize: "12px",
                          border: "1px solid rgba(56, 189, 248, 0.2)"
                        }}
                      >
                        📄 {doc}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}