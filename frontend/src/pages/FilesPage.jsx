
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./FilesPage.css";

export default function FilesPage() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    fetchDocs();
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const fetchDocs = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/documents", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setDocuments(res.data);
    } catch (err) {
      console.log(err);
    }
  };

  const previewFile = async (filename) => {
    try {
      const token = localStorage.getItem("token");

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      const res = await api.get(
        `/documents/${encodeURIComponent(filename)}/preview`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          responseType: "blob",
        }
      );

      const url = URL.createObjectURL(res.data);
      setPreviewUrl(url);
      setSelectedFile(url);
    } catch (err) {
      console.log(err);
      alert("Preview failed");
    }
  };

  const deleteFile = async (filename) => {
    try {
      const token = localStorage.getItem("token");

      await api.delete(`/delete-file/${encodeURIComponent(filename)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
      setSelectedFile(null);
      fetchDocs();
    } catch (err) {
      console.log(err);
      alert("Delete failed");
    }
  };

  return (
    <div className="page-container">
      <header className="page-topbar">
        <button className="page-back-btn" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <div className="page-title-group">
          <h1>Your Files</h1>
          <p>Manage and preview your uploaded documents</p>
        </div>
      </header>

      <main className="page-content">
        <div className="files-grid-container">
          {/* LEFT SIDE */}
          <div className="files-list-section">
            {documents.length === 0 ? (
              <div className="files-empty-state">
                <p>No files uploaded yet.</p>
              </div>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="file-card">
                  <div
                    className="file-card-title"
                    onClick={() => previewFile(doc.filename)}
                  >
                    📄 {doc.filename}
                  </div>
                  <div className="file-card-actions">
                    <button
                      className="file-delete-btn"
                      onClick={() => deleteFile(doc.filename)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* RIGHT SIDE PREVIEW */}
          <div className="files-preview-section">
            {selectedFile ? (
              <iframe
                src={selectedFile}
                title="PDF Preview"
                className="file-preview-iframe"
              />
            ) : (
              <div className="file-preview-placeholder">
                <p>Select a file to preview</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
