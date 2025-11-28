import React, { useState } from "react";
import ChatPage from "./ChatPage";
import HistoryPage from "./HistoryPage";
import AdminPage from "./AdminPage";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("user") || "null")
  );
  const [page, setPage] = useState("chat");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(true);

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.token);
        localStorage.setItem(
          "user",
          JSON.stringify({ username: data.username, role: data.role })
        );
        setToken(data.token);
        setUser({ username: data.username, role: data.role });
      } else {
        const errorData = await res
          .json()
          .catch(() => ({ detail: "Authentication failed" }));
        alert(errorData.detail || "Authentication failed");
      }
    } catch (err) {
      alert("Network error: " + err.message);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  if (!token) {
    return (
      <div
        style={{
          maxWidth: "400px",
          margin: "100px auto",
          padding: "20px",
          border: "1px solid #ddd",
        }}
      >
        <h2>{isLogin ? "Login" : "Register"}</h2>
        <form onSubmit={handleAuth}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", padding: "8px", marginBottom: "10px" }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: "8px", marginBottom: "10px" }}
          />
          <button
            type="submit"
            style={{
              width: "100%",
              padding: "10px",
              background: "#007bff",
              color: "white",
              border: "none",
            }}
          >
            {isLogin ? "Login" : "Register"}
          </button>
        </form>
        <button
          onClick={() => setIsLogin(!isLogin)}
          style={{
            marginTop: "10px",
            background: "none",
            border: "none",
            color: "#007bff",
          }}
        >
          {isLogin ? "Need an account?" : "Have an account?"}
        </button>
        <p style={{ marginTop: "20px", fontSize: "12px", color: "#666" }}>
          Default admin: username=admin, password=admin123
        </p>
      </div>
    );
  }

  return (
    <div>
      <nav
        style={{
          background: "#333",
          padding: "10px",
          color: "white",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <div>
          <button
            onClick={() => setPage("chat")}
            style={{
              marginRight: "10px",
              background: page === "chat" ? "#555" : "#333",
              color: "white",
              border: "none",
              padding: "5px 10px",
            }}
          >
            Chat
          </button>
          <button
            onClick={() => setPage("history")}
            style={{
              marginRight: "10px",
              background: page === "history" ? "#555" : "#333",
              color: "white",
              border: "none",
              padding: "5px 10px",
            }}
          >
            History
          </button>
          {user?.role === "admin" && (
            <button
              onClick={() => setPage("admin")}
              style={{
                marginRight: "10px",
                background: page === "admin" ? "#555" : "#333",
                color: "white",
                border: "none",
                padding: "5px 10px",
              }}
            >
              Admin
            </button>
          )}
        </div>
        <div>
          <span style={{ marginRight: "15px" }}>{user?.username}</span>
          <button
            onClick={logout}
            style={{
              background: "#d9534f",
              color: "white",
              border: "none",
              padding: "5px 10px",
            }}
          >
            Logout
          </button>
        </div>
      </nav>
      <div style={{ padding: "20px" }}>
        {page === "chat" && <ChatPage token={token} />}
        {page === "history" && <HistoryPage token={token} />}
        {page === "admin" && <AdminPage token={token} />}
      </div>
    </div>
  );
}

export default App;
