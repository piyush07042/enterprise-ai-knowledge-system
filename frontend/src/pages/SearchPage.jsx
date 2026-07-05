import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import CitationCard from "../components/CitationCard";
import "./SearchPage.css";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
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

      const token = localStorage.getItem("token");

      const res = await api.post(
        "/search",
        { query: trimmed },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // API now returns { answer: "...", sources: [...] }
      setAnswer(res.data.answer || "");
      setSources(Array.isArray(res.data.sources) ? res.data.sources : []);
      setHasSearched(true);
    } catch (err) {
      setAnswer("Search failed. Please try again.");
      setSources([]);
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
    <div className="search-page">
      {/* Top bar */}
      <header className="search-topbar">
        <button className="search-back" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <span className="search-topbar-title">AI Search</span>
        <span className="search-topbar-sub">Powered by RAG + Groq LLM</span>
      </header>

      {/* Main content */}
      <div className="search-content">
        {/* Hero */}
        <div className="search-hero">
          <h1>Ask Your Knowledge Base</h1>
          <p>Get precise answers from your uploaded documents with source citations</p>
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
          </div>
        ) : (
          <div className="search-placeholder">
            <span className="search-placeholder-icon">📚</span>
            <p>Your answer will appear here</p>
            <small>Upload documents first, then ask questions</small>
          </div>
        )}
      </div>
    </div>
  );
}