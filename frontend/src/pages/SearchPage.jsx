import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import LoadingScreen from "../components/LoadingScreen";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleSearch = async () => {
    try {
      setLoading(true);

      const token = localStorage.getItem("token");

      const res = await api.post(
        "/search",
        { query },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setAnswer(res.data.answer);
      setLoading(false);
    } catch (err) {
      setAnswer("Search failed");
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div style={{ padding: "40px" }}>
      <button onClick={() => navigate("/dashboard")}>
        ← Back
      </button>

      <h1>AI Search</h1>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask AI..."
        style={{
          width: "70%",
          padding: "15px",
          marginTop: "20px"
        }}
      />

      <button
        onClick={handleSearch}
        style={{
          marginLeft: "15px",
          padding: "15px 25px"
        }}
      >
        Search
      </button>

      <div style={{ marginTop: "40px" }}>
        <h2>Response</h2>
        <p>{answer}</p>
      </div>
    </div>
  );
}