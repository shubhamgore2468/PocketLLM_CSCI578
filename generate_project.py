import os

files = {
    "backend/app/__init__.py": "",
    
    "backend/app/main.py": """from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import time
from .database import get_db, init_db
from .models import *
from .auth import create_token, verify_token, hash_password, verify_password
from .cache import cache
from .inference import mock_inference

app = FastAPI(title="PocketLLM Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.on_event("startup")
def startup():
    init_db()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# AUTH
@app.post("/api/auth/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username exists")
    new_user = User(username=user.username, password=hash_password(user.password), role="user")
    db.add(new_user)
    db.commit()
    token = create_token({"user_id": new_user.id, "username": new_user.username, "role": new_user.role})
    return {"token": token, "username": new_user.username, "role": new_user.role}

@app.post("/api/auth/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"user_id": db_user.id, "username": db_user.username, "role": db_user.role})
    return {"token": token, "username": db_user.username, "role": db_user.role}

# CHAT
@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cache_key = f"{req.prompt}:{req.max_tokens}"
    cached = cache.get(cache_key)
    if cached:
        return {"response": cached, "cached": True}
    
    response = mock_inference(req.prompt, req.max_tokens)
    cache.set(cache_key, response)
    
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first() if req.session_id else None
    if not session:
        session = ChatSession(user_id=current_user["user_id"], title=req.prompt[:50])
        db.add(session)
        db.commit()
        db.refresh(session)
    
    msg = Message(session_id=session.id, role="user", content=req.prompt)
    db.add(msg)
    msg_resp = Message(session_id=session.id, role="assistant", content=response)
    db.add(msg_resp)
    db.commit()
    
    return {"response": response, "cached": False, "session_id": session.id}

# SESSIONS
@app.get("/api/v1/sessions", response_model=List[SessionResponse])
def get_sessions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user["user_id"]).all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in sessions]

@app.get("/api/v1/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user["user_id"]).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "messages": [{"role": m.role, "content": m.content} for m in messages]
    }

# ADMIN
@app.get("/admin/metrics")
def get_metrics(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    total_sessions = db.query(ChatSession).count()
    total_messages = db.query(Message).count()
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "cache_size": cache.size(),
        "cpu_percent": 45.2,
        "memory_mb": 512
    }

@app.post("/admin/cache/clear")
def clear_cache(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    cache.clear()
    return {"status": "cleared"}

@app.get("/health")
def health():
    return {"status": "ok"}""",

    "backend/app/models.py": """from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")

class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    username: str
    role: str

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    session_id: int = None

class ChatResponse(BaseModel):
    response: str
    cached: bool = False
    session_id: int = None

class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: str

class MessageResponse(BaseModel):
    role: str
    content: str

class SessionDetail(BaseModel):
    id: int
    title: str
    created_at: str
    messages: list[MessageResponse]""",

    "backend/app/database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User
from .auth import hash_password

DATABASE_URL = "sqlite:///./pocketllm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", password=hash_password("admin123"), role="admin")
        db.add(admin)
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()""",

    "backend/app/auth.py": """import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None""",

    "backend/app/cache.py": """from collections import OrderedDict

class SimpleCache:
    def __init__(self, max_size=256):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()
    
    def size(self):
        return len(self.cache)

cache = SimpleCache()""",

    "backend/app/inference.py": """import time

def mock_inference(prompt: str, max_tokens: int = 100) -> str:
    time.sleep(0.5)
    responses = {
        "hello": "Hello! I'm PocketLLM. How can I help you today?",
        "what": "I'm a lightweight language model running on CPU. I can answer questions and have conversations.",
        "how": "I use quantized models to run efficiently on limited resources."
    }
    
    prompt_lower = prompt.lower()
    for key, response in responses.items():
        if key in prompt_lower:
            return response
    
    return f"I received your message: '{prompt[:50]}...' This is a mock response. Real inference will be added later.\"""",

    "backend/requirements.txt": """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
PyJWT==2.8.0""",

    "backend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]""",

    "frontend/src/App.jsx": """import React, { useState, useEffect } from 'react';
import ChatPage from './ChatPage';
import HistoryPage from './HistoryPage';
import AdminPage from './AdminPage';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [page, setPage] = useState('chat');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);

  const handleAuth = async (e) => {
    e.preventDefault();
    const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
    const res = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify({ username: data.username, role: data.role }));
      setToken(data.token);
      setUser({ username: data.username, role: data.role });
    } else {
      alert('Auth failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  if (!token) {
    return (
      <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px', border: '1px solid #ddd' }}>
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        <form onSubmit={handleAuth}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
          />
          <button type="submit" style={{ width: '100%', padding: '10px', background: '#007bff', color: 'white', border: 'none' }}>
            {isLogin ? 'Login' : 'Register'}
          </button>
        </form>
        <button onClick={() => setIsLogin(!isLogin)} style={{ marginTop: '10px', background: 'none', border: 'none', color: '#007bff' }}>
          {isLogin ? 'Need an account?' : 'Have an account?'}
        </button>
        <p style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
          Default admin: username=admin, password=admin123
        </p>
      </div>
    );
  }

  return (
    <div>
      <nav style={{ background: '#333', padding: '10px', color: 'white', display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <button onClick={() => setPage('chat')} style={{ marginRight: '10px', background: page === 'chat' ? '#555' : '#333', color: 'white', border: 'none', padding: '5px 10px' }}>Chat</button>
          <button onClick={() => setPage('history')} style={{ marginRight: '10px', background: page === 'history' ? '#555' : '#333', color: 'white', border: 'none', padding: '5px 10px' }}>History</button>
          {user?.role === 'admin' && (
            <button onClick={() => setPage('admin')} style={{ marginRight: '10px', background: page === 'admin' ? '#555' : '#333', color: 'white', border: 'none', padding: '5px 10px' }}>Admin</button>
          )}
        </div>
        <div>
          <span style={{ marginRight: '15px' }}>{user?.username}</span>
          <button onClick={logout} style={{ background: '#d9534f', color: 'white', border: 'none', padding: '5px 10px' }}>Logout</button>
        </div>
      </nav>
      <div style={{ padding: '20px' }}>
        {page === 'chat' && <ChatPage token={token} />}
        {page === 'history' && <HistoryPage token={token} />}
        {page === 'admin' && <AdminPage token={token} />}
      </div>
    </div>
  );
}

export default App;""",

    "frontend/src/ChatPage.jsx": """import React, { useState } from 'react';

function ChatPage({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [maxTokens, setMaxTokens] = useState(100);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages([...messages, userMsg]);
    setLoading(true);
    setInput('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: input,
          max_tokens: maxTokens,
          session_id: sessionId
        })
      });
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response, cached: data.cached }]);
      if (data.session_id) setSessionId(data.session_id);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + err.message }]);
    }
    
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>Chat</h2>
      <div style={{ marginBottom: '10px' }}>
        <label>Max Tokens: </label>
        <input
          type="number"
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          style={{ width: '80px', padding: '5px' }}
        />
        <button onClick={() => { setMessages([]); setSessionId(null); }} style={{ marginLeft: '10px', padding: '5px 10px' }}>
          New Chat
        </button>
      </div>
      
      <div style={{ border: '1px solid #ddd', padding: '15px', minHeight: '400px', maxHeight: '400px', overflowY: 'auto', marginBottom: '10px', background: '#f9f9f9' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '15px', padding: '10px', background: msg.role === 'user' ? '#e3f2fd' : '#fff', borderRadius: '5px' }}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.content}
            {msg.cached && <span style={{ marginLeft: '10px', fontSize: '12px', color: '#28a745' }}>(cached)</span>}
          </div>
        ))}
        {loading && <div style={{ color: '#666' }}>Thinking...</div>}
      </div>
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          style={{ flex: 1, padding: '10px', border: '1px solid #ddd' }}
        />
        <button onClick={sendMessage} disabled={loading} style={{ padding: '10px 20px', background: '#007bff', color: 'white', border: 'none' }}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatPage;""",

    "frontend/src/HistoryPage.jsx": """import React, { useState, useEffect } from 'react';

function HistoryPage({ token }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    const res = await fetch('http://localhost:8000/api/v1/sessions', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    setSessions(data);
  };

  const viewSession = async (id) => {
    const res = await fetch(`http://localhost:8000/api/v1/sessions/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    setSelectedSession(data);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', gap: '20px' }}>
      <div style={{ flex: '1', border: '1px solid #ddd', padding: '15px' }}>
        <h3>Sessions</h3>
        {sessions.length === 0 && <p>No sessions yet</p>}
        {sessions.map(s => (
          <div
            key={s.id}
            onClick={() => viewSession(s.id)}
            style={{ padding: '10px', margin: '5px 0', background: '#f0f0f0', cursor: 'pointer', borderRadius: '5px' }}
          >
            <div><strong>{s.title}</strong></div>
            <div style={{ fontSize: '12px', color: '#666' }}>{new Date(s.created_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
      
      <div style={{ flex: '2', border: '1px solid #ddd', padding: '15px' }}>
        <h3>Messages</h3>
        {!selectedSession && <p>Select a session to view messages</p>}
        {selectedSession && (
          <div>
            <h4>{selectedSession.title}</h4>
            {selectedSession.messages.map((msg, idx) => (
              <div key={idx} style={{ marginBottom: '15px', padding: '10px', background: msg.role === 'user' ? '#e3f2fd' : '#fff', borderRadius: '5px' }}>
                <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.content}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;""",

    "frontend/src/AdminPage.jsx": """import React, { useState, useEffect } from 'react';

function AdminPage({ token }) {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    const res = await fetch('http://localhost:8000/admin/metrics', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    setMetrics(data);
  };

  const clearCache = async () => {
    await fetch('http://localhost:8000/admin/cache/clear', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    alert('Cache cleared');
    fetchMetrics();
  };

  if (!metrics) return <div>Loading...</div>;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>Admin Console</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h3>System Metrics</h3>
          <p><strong>CPU:</strong> {metrics.cpu_percent}%</p>
          <p><strong>Memory:</strong> {metrics.memory_mb} MB</p>
        </div>
        
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h3>Database Stats</h3>
          <p><strong>Total Sessions:</strong> {metrics.total_sessions}</p>
          <p><strong>Total Messages:</strong> {metrics.total_messages}</p>
        </div>
      </div>
      
      <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
        <h3>Cache Management</h3>
        <p><strong>Cache Size:</strong> {metrics.cache_size} entries</p>
        <button onClick={clearCache} style={{ padding: '10px 20px', background: '#dc3545', color: 'white', border: 'none', marginTop: '10px' }}>
          Clear Cache
        </button>
      </div>
    </div>
  );
}

export default AdminPage;""",

    "frontend/src/index.js": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);""",

    "frontend/public/index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PocketLLM Portal</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>""",

    "frontend/package.json": """{
  "name": "pocketllm-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "eslintConfig": {
    "extends": ["react-app"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}""",

    "frontend/Dockerfile": """FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY public ./public
COPY src ./src

CMD ["npm", "start"]""",

    "docker-compose.yml": """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - db-data:/app
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - CHOKIDAR_USEPOLLING=true

volumes:
  db-data:""",

    "README.md": """# PocketLLM Portal MVP

Minimal working prototype implementing core features from Assignment 3.

## Quick Start

```bash
# Run the application
docker-compose up --build

# Access at http://localhost:3000
```

**Default admin**: username=`admin`, password=`admin123`

## Features
- User authentication (register/login)
- Chat interface with mock LLM
- Session history
- Admin console (metrics, cache management)
- JWT authentication
- SQLite database

## Project Structure
```
pocketllm-mvp/
├── backend/          # FastAPI application
├── frontend/         # React application  
├── docker-compose.yml
└── README.md
```

See full documentation in artifacts."""
}

def create_project():
    print("Creating PocketLLM Portal MVP...")
    
    for filepath, content in files.items():
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created {filepath}")
    
    print("\n✅ All files created successfully!")
    print("\nNext steps:")
    print("1. cd into the project directory")
    print("2. Run: docker-compose up --build")
    print("3. Open: http://localhost:3000")
    print("\nDefault admin: username=admin, password=admin123")

if __name__ == "__main__":
    create_project()