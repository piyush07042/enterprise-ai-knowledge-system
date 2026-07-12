
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
    <div className="upload-page">
      <button className="upload-back" onClick={() => navigate("/dashboard")}>
        ← Back
      </button>
      <div className="upload-card">
        <h1>Upload Documents</h1>
        <p>Add files to your Enterprise AI knowledge base</p>

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
          Supported: PDF, DOCX, TXT
        </div>

        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>

        {message && (
          <div className="upload-message">
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
