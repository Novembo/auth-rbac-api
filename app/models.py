"""Modèles SQLAlchemy : utilisateurs, rôles, ressources.

Un utilisateur a un seul rôle (simple et suffisant pour la démonstration).
Trois rôles : "user" (par défaut), "editor", "admin".
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user | editor | admin
    is_active = Column(Integer, nullable=False, default=1)  # 1/0 : désactivation sans suppression
    created_at = Column(DateTime, nullable=False, default=now_utc)

    resources = relationship("Resource", back_populates="owner", cascade="all, delete-orphan")


class Resource(Base):
    """Ressource d'exemple appartenant à un utilisateur (démontre le cloisonnement par rôle)."""

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String(2000), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=now_utc)

    owner = relationship("User", back_populates="resources")
