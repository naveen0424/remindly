from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
import app.models  # noqa: F401 — registers all models with SQLAlchemy

from app.routers import auth, reminders
# from app.routers import groups, notifications  ← coming next

app = FastAPI(
    title="Remindly API",
    description="Group & personal reminder notes app",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reminders.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Remindly API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
