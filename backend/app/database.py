import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User
from .auth import hash_password

# Use PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pocketllm.db")

if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL connection
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # SQLite connection (for local development)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(username="admin", password=hash_password("admin123"), role="admin")
                db.add(admin)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()