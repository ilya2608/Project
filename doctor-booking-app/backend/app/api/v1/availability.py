import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_self_or_admin
from app.db.base import get_db
from app.db.models import AvailabilityException, User, WeeklyAvailabilityRule
from app.schemas.availability import ExceptionCreate, ExceptionOut, WeeklyRuleCreate, WeeklyRuleOut

router = APIRouter(prefix="/doctors/{doctor_id}/availability", tags=["availability"])


@router.get("/rules", response_model=list[WeeklyRuleOut])
def list_rules(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> list[WeeklyAvailabilityRule]:
    return (
        db.query(WeeklyAvailabilityRule)
        .filter(WeeklyAvailabilityRule.doctor_id == doctor_id)
        .order_by(WeeklyAvailabilityRule.weekday, WeeklyAvailabilityRule.start_time)
        .all()
    )


@router.post("/rules", response_model=WeeklyRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    doctor_id: uuid.UUID,
    payload: WeeklyRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> WeeklyAvailabilityRule:
    if not (0 <= payload.weekday <= 6):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weekday must be 0 (Mon) .. 6 (Sun)")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    rule = WeeklyAvailabilityRule(doctor_id=doctor_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=WeeklyRuleOut)
def update_rule(
    doctor_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: WeeklyRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> WeeklyAvailabilityRule:
    rule = _get_rule_or_404(db, doctor_id, rule_id)
    for field, value in payload.model_dump().items():
        setattr(rule, field, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    doctor_id: uuid.UUID,
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> None:
    rule = _get_rule_or_404(db, doctor_id, rule_id)
    db.delete(rule)
    db.commit()


@router.get("/exceptions", response_model=list[ExceptionOut])
def list_exceptions(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> list[AvailabilityException]:
    return (
        db.query(AvailabilityException)
        .filter(AvailabilityException.doctor_id == doctor_id)
        .order_by(AvailabilityException.date)
        .all()
    )


@router.post("/exceptions", response_model=ExceptionOut, status_code=status.HTTP_201_CREATED)
def create_exception(
    doctor_id: uuid.UUID,
    payload: ExceptionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> AvailabilityException:
    exception = AvailabilityException(doctor_id=doctor_id, **payload.model_dump())
    db.add(exception)
    db.commit()
    db.refresh(exception)
    return exception


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(
    doctor_id: uuid.UUID,
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_self_or_admin),
) -> None:
    exception = (
        db.query(AvailabilityException)
        .filter(AvailabilityException.id == exception_id, AvailabilityException.doctor_id == doctor_id)
        .first()
    )
    if exception is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
    db.delete(exception)
    db.commit()


def _get_rule_or_404(db: Session, doctor_id: uuid.UUID, rule_id: uuid.UUID) -> WeeklyAvailabilityRule:
    rule = (
        db.query(WeeklyAvailabilityRule)
        .filter(WeeklyAvailabilityRule.id == rule_id, WeeklyAvailabilityRule.doctor_id == doctor_id)
        .first()
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule
