"""
History model — stores each RAG query/answer with performance metadata.

Columns
-------
id             : primary key
query          : the user's question
answer         : the LLM-generated answer
user_id        : FK → users.id
latency        : total pipeline time in seconds
confidence     : average confidence score [0, 1]
retrieved_docs : comma-separated list of retrieved filenames
created_at     : timestamp when the query was made
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)