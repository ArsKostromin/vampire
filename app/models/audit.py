from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    table_name = Column(Text, nullable=False)
    operation = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True))
    username = Column(Text)
    old_record = Column(JSONB)
    new_record = Column(JSONB)
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    extra = Column(Text) 