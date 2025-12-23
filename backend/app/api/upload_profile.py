# routes/mapping_profiles.py
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.models import models
from app.services.mapping_config_builder import get_full_profile_config

from app.models.upload_profile import (
    MappingProfile, MappingSheet, SheetExtraColumn, SheetCleanup,
    SheetColumnMapping, SheetRelation
)
from app.schemas.schemas import (
    MappingProfileCreateSchema, MappingProfileOutSchema,
    MappingProfileUpdateSchema, ColumnInfo
)
from app.services.record_fields_service import get_table_columns

router = APIRouter()

# Helper: verify profile edit permission
def can_edit_profile(profile: MappingProfile, user):
    if user is None:
        return False
    return user.is_superuser or (profile.created_by == user.id)

def can_view_config(user):
    if user is None:
        return False
    return user.is_superuser

#shifted to service hvb @ 04/12/2025
# def get_table_columns(db: Session, table_name: str, exclude: list[str], compulsoryCols: list[str]):
#     sql = """
#         SELECT
#             column_name,
#             is_nullable,
#             data_type
#         FROM information_schema.columns
#         WHERE table_name = :table_name
#         AND column_name NOT IN :exclude
#         ORDER BY ordinal_position;
#     """
#
#     if not compulsoryCols:
#         compulsoryCols = []
#
#     # SQLAlchemy needs tuple for IN
#     exclude_tuple = tuple(exclude) if exclude else tuple([""])
#
#     rows = db.execute(
#         sqlalchemy.text(sql),
#         {"table_name": table_name, "exclude": exclude_tuple}
#     ).fetchall()
#
#
#
#     result = []
#     for r in rows:
#         result.append({
#             "column_name": r.column_name,
#             # "is_compulsory": (r.is_nullable == "NO"),
#             "is_compulsory": (r.column_name in compulsoryCols),
#             "data_type": r.data_type
#         })
#
#     return result

@router.get("/health")
async def health_check():
    """Simple health check endpoint to verify the router is accessible"""
    return {"status": "ok", "router": "upload_profile"}

# CREATE
@router.post("/", response_model=MappingProfileOutSchema, status_code=status.HTTP_201_CREATED)
def create_profile(payload: MappingProfileCreateSchema, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # duplicate name
    if db.query(MappingProfile).filter(MappingProfile.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Mapping profile name already exists")

    profile = MappingProfile(
        name=payload.name,
        description=payload.description,
        file_type=payload.file_type,
        is_global=payload.is_global,
        created_by=user.id,
        profile_json=payload.model_dump()  # store snapshot
    )
    db.add(profile)
    db.flush()

    # sheets
    for sh in payload.sheets:
        sheet = MappingSheet(
            profile_id=profile.id,
            sheet_index=sh.sheet_index,
            sheet_alias=sh.sheet_alias,
            header_row=sh.header_row,
            skip_rows=sh.skip_rows,
            cols_to_read=sh.cols_to_read,
            key_columns=sh.key_columns
        )
        db.add(sheet)
        db.flush()
        if sh.extra:
            for ex in sh.extra:
                db.add(SheetExtraColumn(sheet_id=sheet.id, source_col=ex.source_col, target_name=ex.target_name))
        if sh.cleanup:
            db.add(SheetCleanup(sheet_id=sheet.id, rules=[r.model_dump() for r in sh.cleanup]))

    # column mappings
    dataset_id_target_added = False
    for cm in payload.column_mappings or []:
        # check and remove mapping for dataset_id and fix it to hardcoded mapping of data_id
        if cm.target_column == "dataset_id":
            cm.source_col = "data_id"
            dataset_id_target_added = True

        db.add(SheetColumnMapping(profile_id=profile.id, sheet_index=cm.sheet_index,
                                  source_col=cm.source_col, target_column=cm.target_column))
    if not dataset_id_target_added:
        db.add(SheetColumnMapping(profile_id=profile.id, sheet_index=0,
                                  source_col="data_id", target_column="dataset_id"))

    # relations
    for rel in payload.relations or []:
        db.add(SheetRelation(profile_id=profile.id, left_sheet=rel.left_sheet, right_sheet=rel.right_sheet,
                             left_col=rel.left_col, right_col=rel.right_col, how=rel.how))
    db.commit()
    db.refresh(profile)
    return profile

# added hvb @ 02/12/2025
@router.get("/file-types")
def available_file_types(db: Session = Depends(get_db)):
    # get distinct file types from dataset
    result = (
        db.query(models.Dataset.file_type)
        .filter(models.Dataset.file_type.isnot(None))
        .distinct()
        .all()
    )
    return [r[0] for r in result]

@router.get("/target-fields",response_model=list[ColumnInfo])
def available_columns(
        db: Session = Depends(get_db)
):
    """
        Returns columns from information_schema.columns:
        - column_name
        - is_compulsory (nullable=NO)
        - data_type
        """
    rows = get_table_columns(db, "loan_records", ["id","dataset_id"],["dpd",
                        "dpd_as_per_string","dpd_as_on_31st_jan_2025","collection_12m","m12_collection",
                         "principal_os_amt","disbursement_amount","state","m6_collection"])
    return rows


# LIST (global + owned)
@router.get("/", response_model=List[MappingProfileOutSchema])
def list_profiles(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(MappingProfile).filter(
        (MappingProfile.is_global == True) | (MappingProfile.created_by == user.id)
    ).filter(MappingProfile.is_active == True).all()
    return rows

@router.get("/{profile_id}/config")
def fetch_full_mapping_config(profile_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not can_view_config(user):
        raise HTTPException(403, "Not authorized")
    config = get_full_profile_config(db, profile_id)

    if not config:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    return config

# GET full profile (nested)
@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = db.query(MappingProfile).filter(MappingProfile.id == profile_id, MappingProfile.is_active == True).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    # gather nested details
    sheets = db.query(MappingSheet).filter(MappingSheet.profile_id == profile.id).all()
    mappings = db.query(SheetColumnMapping).filter(SheetColumnMapping.profile_id == profile.id).all()
    extras = db.query(SheetExtraColumn).join(MappingSheet, SheetExtraColumn.sheet_id == MappingSheet.id).filter(MappingSheet.profile_id == profile.id).all()
    cleanup = db.query(SheetCleanup).join(MappingSheet, SheetCleanup.sheet_id == MappingSheet.id).filter(MappingSheet.profile_id == profile.id).all()
    relations = db.query(SheetRelation).filter(SheetRelation.profile_id == profile.id).all()

    # Build response JSON
    resp = {
        "id": profile.id, "name": profile.name, "description": profile.description,
        "file_type" : profile.file_type,
        "is_global": profile.is_global, "is_active": profile.is_active,
        "sheets": [], "column_mappings": [], "relations": []
    }
    # sheets with nested extras and cleanup
    sheet_map = {}
    for sh in sheets:
        sheet_map[sh.id] = {
            "id": sh.id,
            "sheet_index": sh.sheet_index,
            "sheet_alias": sh.sheet_alias,
            "header_row": sh.header_row,
            "skip_rows": sh.skip_rows,
            "cols_to_read": sh.cols_to_read,
            "key_columns": sh.key_columns,
            "extra": [],
            "cleanup": []
        }
    for ex in extras:
        sheet_map[ex.sheet_id]["extra"].append({"source_col": ex.source_col, "target_name": ex.target_name})
    for cu in cleanup:
        sheet_map[cu.sheet_id]["cleanup"].extend(cu.rules or [])

    resp["sheets"] = list(sheet_map.values())
    for m in mappings:
        resp["column_mappings"].append({
            "sheet_index": m.sheet_index,
            "source_col": m.source_col,
            "target_column": m.target_column
        })
    for r in relations:
        resp["relations"].append({
            "left_sheet": r.left_sheet,
            "right_sheet": r.right_sheet,
            "left_col": r.left_col,
            "right_col": r.right_col,
            "how": r.how
        })
    return resp

# UPDATE
@router.put("/{profile_id}")
def update_profile(profile_id: int, payload: MappingProfileUpdateSchema, db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = db.query(MappingProfile).filter(MappingProfile.id == profile_id, MappingProfile.is_active == True).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    if not can_edit_profile(profile, user):
        raise HTTPException(403, "Not authorized to edit this profile")

    # If name changed, ensure uniqueness
    if payload.name and payload.name != profile.name:
        if db.query(MappingProfile).filter(MappingProfile.name == payload.name).first():
            raise HTTPException(400, "Mapping profile name already exists")

    # Update basic fields
    for k,v in payload.model_dump().items():
        if k in ("name","description","is_global","file_type") and v is not None:
            setattr(profile, k, v)
    # If sheets or mappings sent, simplest approach: delete existing and recreate
    if payload.sheets is not None:
        # delete existing sheets (cascade will remove extras/cleanup)
        db.query(MappingSheet).filter(MappingSheet.profile_id == profile.id).delete()
        for sh in payload.sheets:
            sheet = MappingSheet(
                profile_id=profile.id,
                sheet_index=sh.sheet_index,
                sheet_alias=sh.sheet_alias,
                header_row=sh.header_row,
                skip_rows=sh.skip_rows,
                cols_to_read=sh.cols_to_read,
                key_columns=sh.key_columns
            )
            db.add(sheet); db.flush()
            if sh.extra:
                for ex in sh.extra:
                    db.add(SheetExtraColumn(sheet_id=sheet.id, source_col=ex.source_col, target_name=ex.target_name))
            if sh.cleanup:
                db.add(SheetCleanup(sheet_id=sheet.id, rules=[r.model_dump() for r in sh.cleanup]))

    dataset_id_target_added = False
    if payload.column_mappings is not None:
        db.query(SheetColumnMapping).filter(SheetColumnMapping.profile_id == profile.id).delete()
        for cm in payload.column_mappings:
            # check and remove mapping for dataset_id and fix it to hardcoded mapping of data_id
            if cm.target_column == "dataset_id":
                cm.source_col = "data_id"
                dataset_id_target_added = True
            db.add(SheetColumnMapping(profile_id=profile.id, sheet_index=cm.sheet_index, source_col=cm.source_col, target_column=cm.target_column))
    else:
        dataset_id_target_added = True #dataset_id will already be added during creation!

    if not dataset_id_target_added:
        db.add(SheetColumnMapping(profile_id=profile.id, sheet_index=0, source_col="data_id",
                                  target_column="dataset_id"))

    if payload.relations is not None:
        db.query(SheetRelation).filter(SheetRelation.profile_id == profile.id).delete()
        for rel in payload.relations:
            db.add(SheetRelation(profile_id=profile.id, left_sheet=rel.left_sheet, right_sheet=rel.right_sheet, left_col=rel.left_col, right_col=rel.right_col, how=rel.how))

    profile.profile_json = payload.model_dump()
    db.commit()
    db.refresh(profile)
    return {"ok": True, "id": profile.id}

# DELETE (soft-delete if used in uploads)
# We are not removing permanently as it might be getting used in upload
@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = db.query(MappingProfile).filter(MappingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    if not can_edit_profile(profile, user):
        raise HTTPException(403, "Not authorized")
    # TODO: check uploads table if any upload references this profile -> block or soft-delete
    # For now we soft-delete:
    profile.is_active = False
    db.commit()
    return {"ok": True}

# only admin can remove permanently
@router.delete("/{profile_id}/permanent")
def delete_profile(profile_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = db.query(MappingProfile).filter(MappingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    if not can_view_config(user):
        raise HTTPException(403, "Not authorized")
    # TODO: check uploads table if any upload references this profile -> block or soft-delete
    db.delete(profile)
    db.commit()
    return {"ok": True}