import React, { useState, useEffect, useCallback } from "react";

function HistoryPage({ token }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/sessions", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setSessions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const viewSession = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/sessions/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setSelectedSession(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "1000px",
        margin: "0 auto",
        display: "flex",
        gap: "20px",
      }}
    >
      <div style={{ flex: "1", border: "1px solid #ddd", padding: "15px" }}>
        <h3>Sessions</h3>
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: "red" }}>Error: {error}</p>}
        {!loading && !error && sessions.length === 0 && <p>No sessions yet</p>}
        {!loading &&
          !error &&
          sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => viewSession(s.id)}
              style={{
                padding: "10px",
                margin: "5px 0",
                background: "#f0f0f0",
                cursor: "pointer",
                borderRadius: "5px",
              }}
            >
              <div>
                <strong>{s.title}</strong>
              </div>
              <div style={{ fontSize: "12px", color: "#666" }}>
                {new Date(s.created_at).toLocaleString()}
              </div>
            </div>
          ))}
      </div>

      <div style={{ flex: "2", border: "1px solid #ddd", padding: "15px" }}>
        <h3>Messages</h3>
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: "red" }}>Error: {error}</p>}
        {!loading && !error && !selectedSession && (
          <p>Select a session to view messages</p>
        )}
        {!loading && !error && selectedSession && (
          <div>
            <h4>{selectedSession.title}</h4>
            {selectedSession.messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: "15px",
                  padding: "10px",
                  background: msg.role === "user" ? "#e3f2fd" : "#fff",
                  borderRadius: "5px",
                }}
              >
                <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>{" "}
                {msg.content}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;
