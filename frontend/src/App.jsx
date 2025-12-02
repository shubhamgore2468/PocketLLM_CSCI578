"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");
    const urlUsername = urlParams.get("username");
    const urlRole = urlParams.get("role");
    if(urlToken && urlUsername && urlRole) {
      localStorage.setItem("token", urlToken);
      localStorage.setItem("user", JSON.stringify({ username: urlUsername, role: urlRole }));
      setToken(urlToken);
      setUser({ username: urlUsername, role: urlRole });
      window.history.replaceState({}, document.title, "/");
    }
  }, []);

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

  const handleAuthGoogle = () => {
    window.location.href = "http://localhost:8000/api/auth/google";
  }

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl shadow-2xl p-8">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-white mb-2">
              {isLogin ? "Welcome back" : "Create account"}
            </h1>
            <p className="text-slate-400">
              {isLogin ? "Sign in to continue" : "Get started today"}
            </p>
          </div>
          <form onSubmit={handleAuth} className="space-y-6">
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800"
            >
              {isLogin ? "Sign in" : "Create account"}
            </button>
          </form>
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="w-full mt-4 py-2 text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            {isLogin
              ? "Don't have an account? Sign up"
              : "Already have an account? Sign in"}
          </button>
          <div className="mt-6 pt-6 border-t border-slate-700 text-center">
            <p className="text-s text-slate-400">Or</p>
            <button onClick={handleAuthGoogle} className="flex items-center gap-3 w-full mt-4 px-4 py-2 rounded-lg font-medium bg-gray-900 text-white hover:bg-gray-800 border border-gray-700">
              <img src="/google-logo.svg" alt="Google Logo" className="w-5 h-5 invert"/>
              <span>Continue With Google</span>
            </button>
          </div>
          <div className="mt-6 pt-6 border-t border-slate-700 text-center">
            <p className="text-xs text-slate-400 mb-2">
              Default admin credentials:
            </p>
            <code className="text-xs bg-slate-900/70 text-blue-400 px-3 py-1 rounded">
              username: admin | password: admin123
            </code>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-blue-500"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span className="text-xl font-bold text-white">ChatApp</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage("chat")}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  page === "chat"
                    ? "bg-slate-800 text-blue-400"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setPage("history")}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  page === "history"
                    ? "bg-slate-800 text-blue-400"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                History
              </button>
              {user?.role === "admin" && (
                <button
                  onClick={() => setPage("admin")}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    page === "admin"
                      ? "bg-slate-800 text-blue-400"
                      : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                  }`}
                >
                  Admin
                </button>
              )}
            </div>
            <div className="flex items-center gap-4">
              <span className="text-slate-300 font-medium">
                {user?.username}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto p-6">
        {page === "chat" && <ChatPage token={token} />}
        {page === "history" && <HistoryPage token={token} />}
        {page === "admin" && <AdminPage token={token} />}
      </main>
    </div>
  );
}

export default App;
