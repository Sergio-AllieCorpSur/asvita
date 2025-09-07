from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, TableNameFromClassMixin, db.Model):
    """Membresía de usuario a un Dataroom con rol (viewer, editor, owner)."""
    user_id = mapped_column(ForeignKey(
        "user.id", ondelete="CASCADE"), nullable=False, index=True)
    dataroom_id = mapped_column(ForeignKey(
        "dataroom.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="viewer")

    user = relationship("User")
    dataroom = relationship("Dataroom")

    __table_args__ = (
        UniqueConstraint("user_id", "dataroom_id",
                         name="uq_membership_user_dataroom"),
    )
