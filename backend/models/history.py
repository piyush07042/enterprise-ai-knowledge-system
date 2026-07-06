from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from database.db import Base


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    latency = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    retrieved_docs = Column(Text, nullable=True)