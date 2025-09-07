from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin


class Dataroom(UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin, db.Model):
    """Unidad raíz de contenido (similar a 'Drive')."""
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))

    # Relaciones
    folders = relationship(
        "Folder",
        back_populates="dataroom",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    files = relationship(
        "File",
        back_populates="dataroom",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_dataroom_name", "name", postgresql_using="btree"),
    )
