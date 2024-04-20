from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from Base.BaseModel import Base
from sqlalchemy.orm import relationship

class Party(Base):
    __tablename__ = 'Party'
    id: int = Column(Integer, primary_key=True)
    started: bool = Column(Boolean, default=False)
    ended: bool = Column(Boolean, default=False)
    code: int = Column(String, unique=True)
    creator_id: int = Column(Integer, ForeignKey('ChainUser.id'), nullable=True, default=None)
    winner_id: int = Column(Integer, ForeignKey('ChainUser.id'), nullable=True, default=None)
    # users = relationship('ChainUser', foreign_keys=[home_id])