from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str = "170467319151-s0su35c94tsuqqgfippe7b9o4hvl7uqk.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    class config:
        env_file = ".env"

settings = Settings()

