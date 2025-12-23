# models.py
from sqlalchemy import Column, Integer, Text, Boolean, TIMESTAMP, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class MappingProfile(Base):
    __tablename__ = "mapping_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    is_global = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    profile_json = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Added hvb @ 02/12/2025 for filetype of dataset
    file_type = Column(String(150), nullable=True)

    sheets = relationship("MappingSheet", back_populates="profile", cascade="all,delete")
    column_mappings = relationship("SheetColumnMapping", back_populates="profile", cascade="all,delete")
    relations = relationship("SheetRelation", back_populates="profile", cascade="all,delete")

class MappingSheet(Base):
    __tablename__ = "mapping_sheets"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("mapping_profiles.id", ondelete="CASCADE"))
    sheet_index = Column(Integer, nullable=False)
    sheet_alias = Column(Text)
    header_row = Column(Integer, default=-1)
    skip_rows = Column(Integer, default=0)
    cols_to_read = Column(Text, nullable=True)
    key_columns = Column(JSON, nullable=True)

    profile = relationship("MappingProfile", back_populates="sheets")
    extra_columns = relationship("SheetExtraColumn", cascade="all,delete")
    cleanup_rules = relationship("SheetCleanup", cascade="all,delete")

class SheetExtraColumn(Base):
    __tablename__ = "sheet_extra_columns"
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("mapping_sheets.id", ondelete="CASCADE"))
    source_col = Column(Text, nullable=False)
    target_name = Column(Text, nullable=False)

class SheetCleanup(Base):
    __tablename__ = "sheet_cleanup"
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("mapping_sheets.id", ondelete="CASCADE"))
    rules = Column(JSON, nullable=False)

class SheetColumnMapping(Base):
    __tablename__ = "sheet_column_mappings"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("mapping_profiles.id", ondelete="CASCADE"))
    sheet_index = Column(Integer, nullable=False)
    source_col = Column(Text, nullable=False)
    target_column = Column(Text, nullable=False)

    profile = relationship("MappingProfile", back_populates="column_mappings")

class SheetRelation(Base):
    __tablename__ = "sheet_relations"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("mapping_profiles.id", ondelete="CASCADE"))
    left_sheet = Column(Integer, nullable=False)
    right_sheet = Column(Integer, nullable=False)
    left_col = Column(Text, nullable=False)
    right_col = Column(Text, nullable=False)
    how = Column(Text, default="left")

    profile = relationship("MappingProfile", back_populates="relations")
