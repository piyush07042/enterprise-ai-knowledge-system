import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

import "./HistoryPage.css";

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
    <div className="page-container">
      <header className="page-topbar">
        <button className="page-back-btn" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <div className="page-title-group">
          <h1>Search History</h1>
          <p>Review your past queries and AI answers</p>
        </div>
      </header>

      <main className="page-content">
        {history.length === 0 ? (
          <div className="history-empty">
            <p>No history found</p>
          </div>
        ) : (
          <div className="history-grid">
            {history.map((item) => (
              <div key={item.id} className="history-card">
                {item.timestamp && (
                  <div className="history-timestamp">{item.timestamp}</div>
                )}

                <h3 className="history-section-title query">Query</h3>
                <p className="history-query-text">{item.query}</p>

                <h3 className="history-section-title answer">AI Answer</h3>
                <p className="history-answer-text">{item.answer}</p>

                <div className="history-metrics">
                  {item.latency !== null && item.latency !== undefined && (
                    <div>
                      Latency: <span className="history-metric-val">{item.latency}s</span>
                    </div>
                  )}
                  {item.confidence !== null && item.confidence !== undefined && (
                    <div>
                      Confidence: <span className="history-metric-val">{item.confidence}%</span>
                    </div>
                  )}
                  {item.retrieved_docs && item.retrieved_docs.length > 0 && (
                    <div className="history-docs-list">
                      Retrieved Documents:
                      {item.retrieved_docs.map((doc, idx) => (
                        <span key={idx} className="history-doc-tag">
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
      </main>
    </div>
  );
}