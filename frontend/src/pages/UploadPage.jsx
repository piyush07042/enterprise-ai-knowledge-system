
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./UploadPage.css";

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  const token = localStorage.getItem("token");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);

      const res = await api.post("/upload", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });

      setMessage(res.data.message || "Upload successful");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-container">
      <header className="page-topbar">
        <button className="page-back-btn" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <div className="page-title-group">
          <h1>Upload Documents</h1>
          <p>Add files to your Enterprise AI knowledge base</p>
        </div>
      </header>

      <main className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="upload-card">
          <h1>Upload Documents</h1>
          <p>Drag and drop your files here, or click to browse</p>

          <div className="drop-zone">
            <input
              type="file"
              id="fileInput"
              onChange={handleFileChange}
              hidden
            />

            <label htmlFor="fileInput" className="browse-btn">
              Browse Files
            </label>

            {file && (
              <div className="selected-file">
                Selected: {file.name}
              </div>
            )}
          </div>

          <div className="supported">
            Supported formats: PDF, DOCX, TXT
          </div>

          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? "Uploading..." : "Upload File"}
          </button>

          {message && (
            <div className="upload-message">
              {message}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
