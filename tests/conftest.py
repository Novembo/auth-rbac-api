"""Base SQLite en mémoire, isolée par test, avec une fausse dépendance get_db."""

import os
import sys
from pathlib import Path

os.environ["SECRET_KEY"] = "WK-j43yi8Ziwtg7WAiTHFxLxlnoOE6WpRPo473vGH7w"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # une seule connexion partagée : la mémoire persiste entre les requêtes du test
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

PASSWORD = "motdepasse123"


@pytest.fixture()
def client():
    return TestClient(app)


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_user(client):
    """Crée un utilisateur (rôle "user" par défaut) et renvoie (token, headers, email)."""

    def _make(email="user@example.com"):
        client.post("/auth/register", json={"email": email, "password": PASSWORD})
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        token = r.json()["access_token"]
        return token, _auth_headers(token), email

    return _make


@pytest.fixture()
def make_admin(client, make_user):
    """Crée un utilisateur puis le promeut admin directement en base (aucune
    route ne permet de s'auto-promouvoir), puis se reconnecte pour obtenir
    un jeton dont le payload "role" est à jour."""

    def _make(email="admin@example.com"):
        make_user(email)
        db = TestingSessionLocal()
        user = db.query(models.User).filter(models.User.email == email).first()
        user.role = "admin"
        db.commit()
        db.close()
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        token = r.json()["access_token"]
        return token, _auth_headers(token), email

    return _make


@pytest.fixture()
def make_editor(client, make_admin):
    """Crée un utilisateur et le promeut "editor" via la route admin elle-même
    (contrairement à make_admin, ceci teste donc aussi PATCH /users/{id}/role)."""

    def _make(email="editor@example.com"):
        admin_token, admin_headers, _ = make_admin("bootstrap-admin@example.com")
        client.post("/auth/register", json={"email": email, "password": PASSWORD})
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        user_id = client.get("/auth/me", headers=_auth_headers(r.json()["access_token"])).json()["id"]
        client.patch(f"/users/{user_id}/role", json={"role": "editor"}, headers=admin_headers)
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        token = r.json()["access_token"]
        return token, _auth_headers(token), email

    return _make
