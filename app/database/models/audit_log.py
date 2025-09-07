from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin, db.Model):
    """Audita acciones clave."""
    actor_id = mapped_column(ForeignKey(
        "user.id", ondelete="SET NULL"), nullable=True, index=True)
    dataroom_id = mapped_column(ForeignKey(
        "dataroom.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False)  # 'folder' | 'file'
    resource_id: Mapped[str] = mapped_column(
        String(64), nullable=False)    # guarda UUID como texto
    # 'create'|'update'|'delete'|'move'...
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(String(1024))

    actor = relationship("User")
    dataroom = relationship("Dataroom")
