import React, { useState } from "react";

function ChatPage({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [maxTokens, setMaxTokens] = useState(100);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const promptText = input.trim();
    const userMsg = { role: "user", content: promptText };
    setMessages([...messages, userMsg]);
    setLoading(true);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          prompt: promptText,
          max_tokens: maxTokens,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        const errorData = await res
          .json()
          .catch(() => ({ detail: "Unknown error" }));
        throw new Error(
          errorData.detail || `HTTP error! status: ${res.status}`
        );
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, cached: data.cached },
      ]);
      if (data.session_id) setSessionId(data.session_id);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: " + err.message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <h2>Chat</h2>
      <div style={{ marginBottom: "10px" }}>
        <label>Max Tokens: </label>
        <input
          type="number"
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          style={{ width: "80px", padding: "5px" }}
        />
        <button
          onClick={() => {
            setMessages([]);
            setSessionId(null);
          }}
          style={{ marginLeft: "10px", padding: "5px 10px" }}
        >
          New Chat
        </button>
      </div>

      <div
        style={{
          border: "1px solid #ddd",
          padding: "15px",
          minHeight: "400px",
          maxHeight: "400px",
          overflowY: "auto",
          marginBottom: "10px",
          background: "#f9f9f9",
        }}
      >
        {messages.map((msg, idx) => (
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
            {msg.cached && (
              <span
                style={{
                  marginLeft: "10px",
                  fontSize: "12px",
                  color: "#28a745",
                }}
              >
                (cached)
              </span>
            )}
          </div>
        ))}
        {loading && <div style={{ color: "#666" }}>Thinking...</div>}
      </div>

      <div style={{ display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message..."
          style={{ flex: 1, padding: "10px", border: "1px solid #ddd" }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            padding: "10px 20px",
            background: "#007bff",
            color: "white",
            border: "none",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatPage;
