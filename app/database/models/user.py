from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin, db.Model):
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200))

    uploaded_files = relationship("File", back_populates="uploaded_by")

    __table_args__ = (
        Index("ix_user_email", "email"),
    )
