"""Computes bookable appointment slots for a doctor over a date range.

This is the single most important piece of business logic in the app —
see backend/tests/unit/test_slot_engine.py for the behaviors it must satisfy.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db.models import (
    Appointment,
    AppointmentStatus,
    AvailabilityException,
    ExceptionKind,
    WeeklyAvailabilityRule,
)

Interval = tuple[datetime, datetime]


@dataclass
class DaySlots:
    date: date
    slots: list[Interval]


def _subtract(intervals: list[Interval], remove: Interval) -> list[Interval]:
    """Removes `remove` from every interval in `intervals`, splitting as needed."""
    result: list[Interval] = []
    r_start, r_end = remove
    for start, end in intervals:
        if r_end <= start or r_start >= end:
            result.append((start, end))
            continue
        if r_start > start:
            result.append((start, r_start))
        if r_end < end:
            result.append((r_end, end))
    return result


def _slice(intervals: list[Interval], duration: timedelta) -> list[Interval]:
    slots: list[Interval] = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        cursor = start
        while cursor + duration <= end:
            slots.append((cursor, cursor + duration))
            cursor += duration
    return slots


def compute_slots(
    db: Session,
    doctor_id: uuid.UUID,
    slot_duration_minutes: int,
    date_from: date,
    date_to: date,
    clinic_timezone: str,
    now: datetime | None = None,
) -> list[DaySlots]:
    tz = ZoneInfo(clinic_timezone)
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)

    duration = timedelta(minutes=slot_duration_minutes)

    rules = (
        db.query(WeeklyAvailabilityRule)
        .filter(WeeklyAvailabilityRule.doctor_id == doctor_id)
        .all()
    )
    exceptions = (
        db.query(AvailabilityException)
        .filter(
            AvailabilityException.doctor_id == doctor_id,
            AvailabilityException.date >= date_from,
            AvailabilityException.date <= date_to,
        )
        .all()
    )
    range_start = datetime.combine(date_from, datetime.min.time(), tzinfo=tz)
    range_end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    booked_appointments = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatus.booked,
            Appointment.start_at < range_end,
            Appointment.end_at > range_start,
        )
        .all()
    )

    results: list[DaySlots] = []
    day_count = (date_to - date_from).days + 1
    for offset in range(day_count):
        d = date_from + timedelta(days=offset)
        weekday = d.weekday()  # Monday=0 .. Sunday=6, matches WeeklyAvailabilityRule.weekday

        day_exceptions = [e for e in exceptions if e.date == d]
        if any(e.kind == ExceptionKind.block and e.is_full_day_block for e in day_exceptions):
            results.append(DaySlots(date=d, slots=[]))
            continue

        free: list[Interval] = [
            (
                datetime.combine(d, rule.start_time, tzinfo=tz),
                datetime.combine(d, rule.end_time, tzinfo=tz),
            )
            for rule in rules
            if rule.weekday == weekday
            and (rule.valid_from is None or rule.valid_from <= d)
            and (rule.valid_until is None or rule.valid_until >= d)
        ]

        for e in day_exceptions:
            if e.kind == ExceptionKind.extra and e.start_time and e.end_time:
                free.append((datetime.combine(d, e.start_time, tzinfo=tz), datetime.combine(d, e.end_time, tzinfo=tz)))

        for e in day_exceptions:
            if e.kind == ExceptionKind.block and not e.is_full_day_block and e.start_time and e.end_time:
                block = (datetime.combine(d, e.start_time, tzinfo=tz), datetime.combine(d, e.end_time, tzinfo=tz))
                free = _subtract(free, block)

        slots = _slice(free, duration)

        for appt in booked_appointments:
            slots = _subtract_slot_list(slots, (appt.start_at, appt.end_at))

        slots = [s for s in slots if s[0] >= now]

        results.append(DaySlots(date=d, slots=sorted(slots, key=lambda iv: iv[0])))

    return results


def _subtract_slot_list(slots: list[Interval], busy: Interval) -> list[Interval]:
    """Drops any whole slot that overlaps `busy` at all (slots are atomic booking units,
    unlike free-time intervals which can be split)."""
    b_start, b_end = busy
    return [s for s in slots if s[1] <= b_start or s[0] >= b_end]
