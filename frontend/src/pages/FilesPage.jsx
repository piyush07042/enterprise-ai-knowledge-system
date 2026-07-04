
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function FilesPage() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    fetchDocs();
  }, []);

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

  const previewFile = (filename) => {
    const token = localStorage.getItem("token");

    setSelectedFile(
      `http://127.0.0.1:8000/open-file/${encodeURIComponent(
        filename
      )}?token=${token}`
    );
  };

  const deleteFile = async (filename) => {
    try {
      const token = localStorage.getItem("token");

      await api.delete(`/delete-file/${filename}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setSelectedFile(null);
      fetchDocs();
    } catch (err) {
      console.log(err);
      alert("Delete failed");
    }
  };

  return (
    <div
      style={{
        padding: "30px",
        background: "#081226",
        color: "white",
        minHeight: "100vh",
      }}
    >
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          padding: "10px 20px",
          marginBottom: "20px",
          borderRadius: "10px",
          border: "none",
          cursor: "pointer",
        }}
      >
        ← Back
      </button>

      <h1>Your Files</h1>

      <div
        style={{
          display: "flex",
          gap: "20px",
          marginTop: "20px",
        }}
      >
        {/* LEFT SIDE */}
        <div
          style={{
            width: "35%",
          }}
        >
          {documents.length === 0 ? (
            <p>No files uploaded</p>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                style={{
                  background: "#1e293b",
                  padding: "15px",
                  borderRadius: "12px",
                  marginBottom: "12px",
                }}
              >
                <div
                  onClick={() => previewFile(doc.filename)}
                  style={{
                    cursor: "pointer",
                    marginBottom: "10px",
                    fontWeight: "bold",
                  }}
                >
                  📄 {doc.filename}
                </div>

                <button
                  onClick={() => deleteFile(doc.filename)}
                  style={{
                    background: "red",
                    color: "white",
                    border: "none",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    cursor: "pointer",
                  }}
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>

        {/* RIGHT SIDE PREVIEW */}
        <div
          style={{
            width: "65%",
            background: "#1e293b",
            borderRadius: "12px",
            padding: "10px",
            minHeight: "700px",
          }}
        >
          {selectedFile ? (
            <iframe
              src={selectedFile}
              title="PDF Preview"
              width="100%"
              height="700px"
              style={{
                border: "none",
                borderRadius: "12px",
              }}
            />
          ) : (
            <div
              style={{
                padding: "30px",
                color: "#94a3b8",
              }}
            >
              Select a file to preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
