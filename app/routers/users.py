"""Gestion des utilisateurs — réservé aux administrateurs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import require_role

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_role("admin")),
):
    return db.query(models.User).order_by(models.User.id).all()


@router.patch("/{user_id}/role", response_model=schemas.UserOut)
def change_role(
    user_id: int,
    payload: schemas.UserUpdateRole,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Tu ne peux pas changer ton propre rôle")

    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
