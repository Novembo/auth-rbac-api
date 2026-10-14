"""Ressources protégées : démontre le cloisonnement par rôle et par propriétaire.

Règles :
  - "user"   : peut créer, lire et modifier SES PROPRES ressources uniquement.
  - "editor" : peut lire toutes les ressources, et modifier les siennes.
  - "admin"  : peut tout lire et tout supprimer.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("", response_model=schemas.ResourceOut, status_code=201)
def create_resource(
    payload: schemas.ResourceCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    resource = models.Resource(title=payload.title, content=payload.content, owner_id=user.id)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("", response_model=list[schemas.ResourceOut])
def list_resources(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.Resource)
    if user.role == "user":
        # Un simple utilisateur ne voit que ses propres ressources.
        query = query.filter(models.Resource.owner_id == user.id)
    # editor et admin voient tout.
    return query.order_by(models.Resource.id).all()


def _get_owned_or_403(resource_id: int, db: Session, user: models.User) -> models.Resource:
    resource = db.get(models.Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    if user.role != "admin" and resource.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Tu n'es pas propriétaire de cette ressource")
    return resource


@router.put("/{resource_id}", response_model=schemas.ResourceOut)
def update_resource(
    resource_id: int,
    payload: schemas.ResourceCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    resource = _get_owned_or_403(resource_id, db, user)
    resource.title = payload.title
    resource.content = payload.content
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=204)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin")),
):
    """Seul un admin peut supprimer — démonstration volontairement stricte de require_role."""
    resource = db.get(models.Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Ressource introuvable")
    db.delete(resource)
    db.commit()
