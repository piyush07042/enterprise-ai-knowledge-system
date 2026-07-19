import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import CitationCard from "../components/CitationCard";
import "./SearchPage.css";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const inputRef = useRef(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    // Support both button click and Enter key
    if (e && e.type === "keydown" && e.key !== "Enter") return;

    const trimmed = query.trim();
    if (!trimmed || loading) return;

    try {
      setLoading(true);
      setAnswer("");
      setSources([]);
      setMetrics(null);

      const token = localStorage.getItem("token");

      const res = await api.post(
        "/search",
        { query: trimmed },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // API now returns { answer: "...", sources: [...], metrics: {...} }
      setAnswer(res.data.answer || "");
      setSources(Array.isArray(res.data.sources) ? res.data.sources : []);
      setMetrics(res.data.metrics || null);
      setHasSearched(true);
    } catch (err) {
      setAnswer("Search failed. Please try again.");
      setSources([]);
      setMetrics(null);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch(e);
    }
  };

  return (
    <div className="page-container">
      <header className="page-topbar">
        <button className="page-back-btn" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <div className="page-title-group">
          <h1>AI Search</h1>
          <p>Powered by RAG + Groq LLM</p>
        </div>
      </header>

      <main className="page-content">
        <div className="search-hero" style={{ textAlign: "center", marginBottom: "40px" }}>
          <h1 style={{ fontSize: "36px", margin: "0 0 10px 0" }}>Ask Your Knowledge Base</h1>
          <p style={{ color: "#94a3b8", fontSize: "16px" }}>Get precise answers from your uploaded documents with source citations</p>
        </div>

        {/* Search form */}
        <div className="search-form">
          <div className="search-input-wrap">
            <span className="search-input-icon">🔍</span>
            <input
              ref={inputRef}
              className="search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything from your documents…"
              disabled={loading}
              autoFocus
            />
          </div>
          <button
            className="search-submit"
            onClick={handleSearch}
            disabled={loading || !query.trim()}
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        {/* Result area */}
        {loading ? (
          <div className="search-loading">
            <div className="search-loading-spinner" />
            <p>Searching your documents…</p>
          </div>
        ) : hasSearched ? (
          <div className="search-result">
            {/* Answer card */}
            <div className="search-answer-card">
              <div className="search-answer-header">
                <span className="search-answer-icon">🤖</span>
                <span className="search-answer-label">AI Response</span>
              </div>
              <div className="search-answer-body">{answer}</div>
            </div>

            {/* Citation card — renders only when sources exist */}
            <CitationCard sources={sources} />

            {/* Metrics & Confidence */}
            {metrics && (
              <div className="search-metrics-panel" style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "15px",
                marginTop: "15px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                borderRadius: "14px",
                padding: "15px"
              }}>
                <div>
                  <h4 style={{ margin: "0 0 5px 0", color: "#94a3b8", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Performance Metrics</h4>
                  <div style={{ fontSize: "13px", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "3px" }}>
                    <div>Retrieval: <strong>{metrics.retrieval_time}s</strong></div>
                    <div>Generation: <strong>{metrics.generation_time}s</strong></div>
                    <div>Total: <strong>{metrics.total_time}s</strong></div>
                  </div>
                </div>
                {sources && sources.length > 0 && (
                  <div>
                    <h4 style={{ margin: "0 0 5px 0", color: "#94a3b8", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Confidence Analysis</h4>
                    {(() => {
                      const validScores = sources.map(s => s.score).filter(s => s !== null && s !== undefined);
                      if (validScores.length === 0) return <div style={{ fontSize: "13px", color: "#94a3b8" }}>No scores available</div>;
                      const avgConf = (validScores.reduce((a, b) => a + b, 0) / validScores.length * 100).toFixed(1);
                      const maxConf = (Math.max(...validScores) * 100).toFixed(1);
                      const bestSource = sources.reduce((prev, current) => ((prev.score || 0) > (current.score || 0)) ? prev : current, sources[0]);
                      return (
                        <div style={{ fontSize: "13px", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "3px" }}>
                          <div>Average: <strong>{avgConf}%</strong></div>
                          <div>Maximum: <strong>{maxConf}%</strong></div>
                          <div>Best Match: <strong>{bestSource.filename} (Chunk #{bestSource.chunk_index})</strong></div>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="search-placeholder">
            <span className="search-placeholder-icon">📚</span>
            <p>Your answer will appear here</p>
            <small>Upload documents first, then ask questions</small>
          </div>
        )}
      </main>
    </div>
  );
}