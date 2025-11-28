"use client";

import { useState, useEffect, useCallback } from "react";

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
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-120px)]">
      <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col">
        <div className="bg-slate-800/50 border-b border-slate-700 p-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Chat History</h3>
          <button
            onClick={fetchSessions}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            title="Refresh"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-slate-400"
            >
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3">
          {loading && sessions.length === 0 && (
            <div className="text-center py-8 text-slate-400">
              Loading sessions...
            </div>
          )}
          {error && (
            <div className="text-center py-8 text-red-400">Error: {error}</div>
          )}
          {!loading && !error && sessions.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="text-slate-600 mb-3"
              >
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
              <p className="text-slate-500">No chat history yet</p>
            </div>
          )}
          <div className="space-y-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => viewSession(s.id)}
                className={`w-full text-left p-3 rounded-lg transition-all ${
                  selectedSession?.id === s.id
                    ? "bg-blue-600/20 border border-blue-500/30"
                    : "bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="font-medium text-white text-sm mb-1 truncate">
                  {s.title}
                </div>
                <div className="text-xs text-slate-400">
                  {new Date(s.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col">
        <div className="bg-slate-800/50 border-b border-slate-700 p-4">
          <h3 className="text-lg font-bold text-white">Messages</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {loading && selectedSession && (
            <div className="text-center py-8 text-slate-400">
              Loading messages...
            </div>
          )}
          {error && (
            <div className="text-center py-8 text-red-400">Error: {error}</div>
          )}
          {!loading && !error && !selectedSession && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="text-slate-600 mb-4"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <h4 className="text-xl font-semibold text-slate-300 mb-2">
                Select a session
              </h4>
              <p className="text-slate-500">
                Choose a chat session from the left to view its messages
              </p>
            </div>
          )}
          {!loading && !error && selectedSession && (
            <div>
              <div className="mb-6 pb-4 border-b border-slate-800">
                <h4 className="text-xl font-bold text-white mb-2">
                  {selectedSession.title}
                </h4>
                <span className="text-sm text-slate-400">
                  {selectedSession.messages.length} messages
                </span>
              </div>
              <div className="space-y-4">
                {selectedSession.messages.map((msg, idx) => (
                  <div key={idx} className="flex gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                        msg.role === "user"
                          ? "bg-slate-700 text-slate-300"
                          : "bg-blue-600 text-white"
                      }`}
                    >
                      {msg.role === "user" ? "U" : "A"}
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-semibold mb-1 text-slate-400">
                        {msg.role === "user" ? "You" : "Assistant"}
                      </div>
                      <div
                        className={`rounded-lg px-4 py-3 ${
                          msg.role === "user"
                            ? "bg-slate-800 text-slate-100"
                            : "bg-slate-800/50 text-slate-100 border border-slate-700"
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;
