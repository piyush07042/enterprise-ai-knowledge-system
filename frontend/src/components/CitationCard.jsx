import React, { useCallback } from "react";
import api from "../services/api";
import "./CitationCard.css";

// ── Confidence helpers ──────────────────────────────────────────────────────

/**
 * Derive a confidence label and CSS modifier from a numeric score.
 *
 * Score thresholds (per spec):
 *   High   >= 0.90
 *   Medium  0.70 – 0.89
 *   Low    < 0.70
 *   null   → "All Documents" (no vector similarity was computed)
 */
function getConfidence(score) {
  if (score === null || score === undefined) {
    return { label: "All Documents", modifier: "all-docs", dot: "◈" };
  }
  if (score >= 0.90) {
    return { label: "High", modifier: "high", dot: "●" };
  }
  if (score >= 0.70) {
    return { label: "Medium", modifier: "medium", dot: "●" };
  }
  return { label: "Low", modifier: "low", dot: "●" };
}

function formatScore(score) {
  if (score === null || score === undefined) return null;
  return `${Math.round(score * 100)}%`;
}

function getFileIcon(filename) {
  const ext = (filename || "").split(".").pop().toLowerCase();
  if (ext === "pdf") return "📄";
  if (ext === "txt") return "📝";
  return "📁";
}

// ── SourceItem ──────────────────────────────────────────────────────────────

function SourceItem({ source }) {
  const { filename, chunk_index, score, preview } = source;
  const confidence = getConfidence(score);
  const scoreLabel = formatScore(score);
  const fileIcon = getFileIcon(filename);

  // Open the file via the existing preview endpoint (blob URL in a new tab)
  const handleOpen = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await api.get(
        `/documents/${encodeURIComponent(filename)}/preview`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: "blob",
        }
      );
      const url = URL.createObjectURL(res.data);
      window.open(url, "_blank", "noopener,noreferrer");
      // Revoke after a short delay so the new tab has time to load
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch {
      // File may not be previewable — fail silently
    }
  }, [filename]);

  return (
    <div
      className="citation-source"
      onClick={handleOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && handleOpen()}
      title={`Open ${filename}`}
    >
      {/* Top row: icon + filename + badge + chunk + score */}
      <div className="citation-source__top">
        <span className="citation-source__filename">
          <span className="citation-source__filename-icon">{fileIcon}</span>
          {filename}
        </span>

        <span className={`citation-badge citation-badge--${confidence.modifier}`}>
          <span className="citation-badge__dot" />
          {confidence.label}
        </span>

        {scoreLabel && (
          <span className="citation-source__score">{scoreLabel}</span>
        )}

        <span className="citation-source__chunk">
          Chunk #{chunk_index}
        </span>
      </div>

      {/* Preview text */}
      {preview ? (
        <p className="citation-source__preview">{preview}</p>
      ) : (
        <p className="citation-source__no-preview">No preview available</p>
      )}

      {/* Hover hint */}
      <span className="citation-source__open-hint">
        ↗ Click to open file
      </span>
    </div>
  );
}

// ── CitationCard ────────────────────────────────────────────────────────────

/**
 * CitationCard
 *
 * Renders a "Sources Used" panel below an AI response.
 *
 * Props:
 *   sources  — array of source objects from the API:
 *              { filename, chunk_index, score, preview }
 *
 * Returns null when sources is empty or not provided.
 */
export default function CitationCard({ sources }) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="citation-card">
      <div className="citation-card__header">
        <span className="citation-card__icon">🔗</span>
        <span className="citation-card__title">Sources Used</span>
        <span className="citation-card__count">
          {sources.length} source{sources.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="citation-card__list">
        {sources.map((source, index) => (
          <SourceItem
            key={`${source.filename}-${source.chunk_index}-${index}`}
            source={source}
          />
        ))}
      </div>
    </div>
  );
}
