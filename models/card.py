from typing import List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    effect: Mapped[str]
    cost: Mapped[str]
    type: Mapped[str]
    supertype: Mapped[str]
    might: Mapped[str]
    set_name: Mapped[str]
    rarity: Mapped[str]
    image: Mapped[str]
    color: Mapped[List[str]] = mapped_column(ARRAY(String))
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    code: Mapped[str]
