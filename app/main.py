"""Point d'entrée de l'API : authentification JWT + permissions par rôle (RBAC).

Lancer en local :
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Documentation interactive : http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, resources, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth RBAC API",
    description="Démonstration d'authentification JWT et de permissions par rôle (user / editor / admin).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resources.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
