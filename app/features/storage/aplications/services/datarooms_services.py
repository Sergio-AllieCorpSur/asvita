# app/features/storage/applications/services/datarooms_services.py
from app.extensions import db
from app.database.models.dataroom import Dataroom


def create_dataroom(name: str, description: str | None = None) -> Dataroom:
    dr = Dataroom(name=name, description=description)
    db.session.add(dr)
    db.session.commit()
    return dr


def list_datarooms() -> list[Dataroom]:
    return Dataroom.query.order_by(Dataroom.created_at.desc()).all()


def get_dataroom(dataroom_id):
    return Dataroom.query.filter(Dataroom.id == dataroom_id).first()
