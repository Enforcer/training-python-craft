from sqlalchemy.orm import Mapped, mapped_column

from subscriptions.shared.sqlalchemy import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    tenant_id: Mapped[int]
