from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from Base.BaseModel import Base
from sqlalchemy.orm import relationship


class ChainUser(Base):
    __tablename__ = 'ChainUser'
    id: int = Column(Integer, primary_key=True)
    party_id: int = Column(Integer, ForeignKey('Party.id', ondelete='CASCADE'), nullable=False)
    name: str = Column(String, nullable=False)
    dead: bool = Column(Boolean, default=False)
    next_user_id: int = Column(Integer, ForeignKey('ChainUser.id', ondelete='CASCADE'), nullable=True, default=None)
    image: str = Column(String, nullable=False)
    num_killed = Column(Integer, default=0)
    # party = relationship('Party')