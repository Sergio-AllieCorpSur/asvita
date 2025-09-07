from sqlalchemy import String, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TableNameFromClassMixin


class File(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TableNameFromClassMixin, db.Model):
    """Archivo (PDF). Guarda metadata y ruta física en disco/objeto."""
    # nombre visible (puede cambiar), y nombre original del upload
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="application/pdf")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ruta absoluta/relativa en el servidor (o clave de blob en S3, etc.)
    storage_path: Mapped[str] = mapped_column(String(2048), nullable=False)

    # útil para deduplicar/subir versiones: hash de contenido
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    folder_id = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataroom_id = mapped_column(
        ForeignKey("dataroom.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # (opcional) tracking de usuario
    uploaded_by_id = mapped_column(ForeignKey(
        "user.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relaciones
    folder = relationship("Folder", back_populates="files")
    dataroom = relationship("Dataroom", back_populates="files")
    uploaded_by = relationship("User", back_populates="uploaded_files")

    __table_args__ = (
        # evita archivos con el mismo nombre en la misma carpeta
        UniqueConstraint("folder_id", "name", name="uq_file_name_per_folder"),
        Index("ix_file_dataroom_folder", "dataroom_id", "folder_id"),
    )
