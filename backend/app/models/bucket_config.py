from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class BucketConfig(Base):
    __tablename__ = "bucket_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), nullable=True)

    name = Column(String(255), nullable=False)
    summary_type = Column(String(100), nullable=False)

    bucket_config = Column(JSONB, nullable=False)
    target_field = Column(String(255), nullable=False)
    target_field_is_json = Column(Boolean, default=False)

    is_default = Column(Boolean, default=False)
    description = Column(Text)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())