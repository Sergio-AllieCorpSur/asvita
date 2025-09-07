from sqlalchemy import String, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TableNameFromClassMixin


class Folder(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TableNameFromClassMixin, db.Model):
    """Carpetas anidadas por adjacency list; únicas por nombre dentro del mismo padre."""
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    dataroom_id = mapped_column(
        ForeignKey("dataroom.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Materialized path simple para consultas rápidas (ej. "root/child/grandchild")
    path: Mapped[str] = mapped_column(String(2048), nullable=False, default="")

    # Relaciones
    dataroom = relationship("Dataroom", back_populates="folders")
    parent = relationship("Folder", remote_side="Folder.id",
                          back_populates="children")
    children = relationship(
        "Folder",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    files = relationship(
        "File",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # evita nombres duplicados en el mismo padre dentro del mismo dataroom
        UniqueConstraint("dataroom_id", "parent_id", "name",
                         name="uq_folder_sibling_name"),
        # evita self-parenting
        CheckConstraint("id IS NULL OR id <> parent_id",
                        name="ck_folder_not_self_parent"),
        Index("ix_folder_dataroom_parent", "dataroom_id", "parent_id"),
        Index("ix_folder_path", "path", postgresql_using="btree"),
    )
