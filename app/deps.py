"""Dépendances FastAPI : utilisateur courant, contrôle par rôle.

Hiérarchie des rôles : user < editor < admin. require_role("editor")
accepte donc "editor" et "admin", pas "user".
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_LEVEL = {"user": 0, "editor": 1, "admin": 2}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(models.User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_role(minimum_role: str):
    """Fabrique une dépendance qui exige au moins le rôle donné.

    Le rôle est revérifié en base (via get_current_user), pas seulement lu
    dans le jeton : une rétrogradation de rôle prend donc effet immédiatement,
    même si l'ancien jeton n'est pas encore expiré.
    """

    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if ROLE_LEVEL.get(user.role, -1) < ROLE_LEVEL[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nécessite le rôle '{minimum_role}' ou supérieur",
            )
        return user

    return checker
