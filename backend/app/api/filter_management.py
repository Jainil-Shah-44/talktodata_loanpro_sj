from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.models import Filter, FilterCondition
from app.models.FilterCriteriaItem import FilterCreate, FilterResponse,FilterCriteriaItem
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.models import models
from typing import List

router = APIRouter()

@router.post("/", response_model=FilterResponse)
def create_filter(filter_data: FilterCreate, db: Session = Depends(get_db),
                  #user=Depends(get_current_user)
                  user: models.User = Depends(get_current_user)
                  ):
    existing = db.query(Filter).filter(
        Filter.user_id == user.id,
        Filter.filter_name == filter_data.filter_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Filter name already exists.")

    new_filter = Filter(
        user_id=user.id,
        filter_name=filter_data.filter_name,
        join_type=filter_data.join_type.upper(),
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(new_filter)
    db.flush()

    for cond in filter_data.conditions:
        db.add(FilterCondition(
            filter_id=new_filter.id,
            field_name=cond.field,
            operator=cond.operator,
            value=str(cond.value) if cond.value else None,
            min_value=cond.min_value,
            max_value=cond.max_value,
            enabled=cond.enabled
        ))

    db.commit()
    db.refresh(new_filter)
    return new_filter

@router.get("/", response_model=List[FilterResponse])
def get_user_filters(
        db: Session = Depends(get_db),
        #user=Depends(get_current_user),
        user: models.User = Depends(get_current_user)
        ):
    return db.query(Filter).filter(Filter.user_id == user.id).all()

@router.get("/{filter_id}")
def get_filter_conditions(filter_id: int,
                          db: Session = Depends(get_db),
                          #user=Depends(get_current_user)
                           user: models.User = Depends(get_current_user)
                          ):
    filter_obj = db.query(Filter).filter(Filter.id == filter_id, Filter.user_id == user.id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found.")
    return {
        "filter": {
            "id": filter_obj.id,
            "filter_name": filter_obj.filter_name,
            "join_type": filter_obj.join_type
        },
        "conditions": filter_obj.conditions
    }

@router.delete("/{filter_id}")
def delete_filter(
        filter_id: int,
        db: Session = Depends(get_db),
        #user=Depends(get_current_user)
        user: models.User = Depends(get_current_user)
        ):
    filter_obj = db.query(Filter).filter(Filter.id == filter_id, Filter.user_id == user.id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found.")
    db.delete(filter_obj)
    db.commit()
    return {"message": "Filter deleted successfully."}

@router.put("/{filter_id}/last_used")
def mark_filter_as_last_used(
        filter_id: int,
        db: Session = Depends(get_db),
        #user=Depends(get_current_user)
        user: models.User = Depends(get_current_user)
        ):
    db.query(Filter).filter(Filter.user_id == user.id).update({Filter.last_used: False})
    target = db.query(Filter).filter(Filter.id == filter_id, Filter.user_id == user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Filter not found.")
    target.last_used = True
    db.commit()
    return {"message": "Last used filter updated."}


# -----------------------------
# Update filter name
# -----------------------------
@router.put("/{filter_id}/rename", response_model=FilterResponse)
def update_filter_name(filter_id: int,
                       new_name: str,
                       db: Session = Depends(get_db),
                       # user=Depends(get_current_user)
                       user: models.User = Depends(get_current_user)
                       ):
    filter_obj = db.query(Filter).filter(Filter.id == filter_id, Filter.user_id == user.id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found.")

    # Check duplicate
    duplicate = db.query(Filter).filter(
        Filter.user_id == user.id,
        Filter.filter_name == new_name,
        Filter.id != filter_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Another filter with this name exists.")

    filter_obj.filter_name = new_name
    filter_obj.updated_by = user.id
    db.commit()
    db.refresh(filter_obj)
    return filter_obj


# -----------------------------
# Update filter conditions
# -----------------------------
@router.put("/{filter_id}/conditions", response_model=FilterResponse)
def update_filter_conditions(
        filter_id: int,
        new_conditions: List[FilterCriteriaItem],
        db: Session = Depends(get_db),
        #user=Depends(get_current_user)
        user: models.User = Depends(get_current_user)
):
    filter_obj = db.query(Filter).filter(Filter.id == filter_id, Filter.user_id == user.id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found.")

    existing_conditions = db.query(FilterCondition).filter(FilterCondition.filter_id == filter_id).all()

    # Map existing by field+operator
    existing_map = {(c.field_name, c.operator): c for c in existing_conditions}
    new_map = {(c.field, c.operator): c for c in new_conditions}

    # ----------------
    # Delete conditions missing in payload
    # ----------------
    for key, cond in existing_map.items():
        if key not in new_map:
            db.delete(cond)

    # ----------------
    # Update existing conditions and add new
    # ----------------
    for key, cond_data in new_map.items():
        if key in existing_map:
            cond_obj = existing_map[key]
            cond_obj.value = str(cond_data.value) if cond_data.value is not None else None
            cond_obj.min_value = cond_data.min_value
            cond_obj.max_value = cond_data.max_value
            cond_obj.enabled = cond_data.enabled
        else:
            # Add new condition
            new_cond = FilterCondition(
                filter_id=filter_id,
                field_name=cond_data.field,
                operator=cond_data.operator,
                value=str(cond_data.value) if cond_data.value is not None else None,
                min_value=cond_data.min_value,
                max_value=cond_data.max_value,
                enabled=cond_data.enabled
            )
            db.add(new_cond)

    filter_obj.updated_by = user.id
    db.commit()
    db.refresh(filter_obj)
    return filter_obj