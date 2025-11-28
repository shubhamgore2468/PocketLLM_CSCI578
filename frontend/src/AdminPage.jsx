import React, { useState, useEffect, useCallback } from "react";

function AdminPage({ token }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/admin/metrics", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const clearCache = async () => {
    try {
      const res = await fetch("http://localhost:8000/admin/cache/clear", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      alert("Cache cleared");
      fetchMetrics();
    } catch (err) {
      alert("Error clearing cache: " + err.message);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: "red" }}>Error: {error}</div>;
  if (!metrics) return <div>No metrics available</div>;

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <h2>Admin Console</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "20px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "5px",
          }}
        >
          <h3>System Metrics</h3>
          <p>
            <strong>CPU:</strong> {metrics.cpu_percent}%
          </p>
          <p>
            <strong>Memory:</strong> {metrics.memory_mb} MB
          </p>
        </div>

        <div
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "5px",
          }}
        >
          <h3>Database Stats</h3>
          <p>
            <strong>Total Sessions:</strong> {metrics.total_sessions}
          </p>
          <p>
            <strong>Total Messages:</strong> {metrics.total_messages}
          </p>
        </div>
      </div>

      <div
        style={{
          border: "1px solid #ddd",
          padding: "15px",
          borderRadius: "5px",
        }}
      >
        <h3>Cache Management</h3>
        <p>
          <strong>Cache Size:</strong> {metrics.cache_size} entries
        </p>
        <button
          onClick={clearCache}
          style={{
            padding: "10px 20px",
            background: "#dc3545",
            color: "white",
            border: "none",
            marginTop: "10px",
          }}
        >
          Clear Cache
        </button>
      </div>
    </div>
  );
}

export default AdminPage;
