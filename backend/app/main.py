from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager
import time
import threading
from .database import get_db, init_db
from .models import *
from .auth import create_token, verify_token, hash_password, verify_password
from .cache import cache
from .inference import mock_inference, ensure_model_pulled

def pull_model_in_background():
    """Pull the model in a background thread so it doesn't block server startup."""
    try:
        ensure_model_pulled()
    except Exception as e:
        print(f"Note: Ollama model check/pull failed: {e}. Will use fallback if needed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    # Pull Ollama model in background (non-blocking)
    model_thread = threading.Thread(target=pull_model_in_background, daemon=True)
    model_thread.start()
    yield
    # Shutdown (if needed)

app = FastAPI(title="PocketLLM Portal", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# AUTH
@app.post("/api/auth/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username exists")
        new_user = User(username=user.username, password=hash_password(user.password), role="user")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        token = create_token({"user_id": new_user.id, "username": new_user.username, "role": new_user.role})
        return {"token": token, "username": new_user.username, "role": new_user.role}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

@app.post("/api/auth/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if not db_user or not verify_password(user.password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token({"user_id": db_user.id, "username": db_user.username, "role": db_user.role})
        return {"token": token, "username": db_user.username, "role": db_user.role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

# CHAT
@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        cache_key = f"{req.prompt}:{req.max_tokens}"
        cached = cache.get(cache_key)
        if cached:
            return {"response": cached, "cached": True}
        
        response = mock_inference(req.prompt, req.max_tokens)
        cache.set(cache_key, response)
        
        session = None
        if req.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.id == req.session_id,
                ChatSession.user_id == current_user["user_id"]
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or access denied")
        
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
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

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
    return {"status": "ok"}