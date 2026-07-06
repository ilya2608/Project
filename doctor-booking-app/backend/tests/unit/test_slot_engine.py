from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.db.models import (
    Appointment,
    AppointmentStatus,
    AvailabilityException,
    ExceptionKind,
    WeeklyAvailabilityRule,
)
from app.services.slot_engine import compute_slots

TZ = "Europe/Brussels"
MONDAY = date(2026, 7, 6)  # confirmed Monday
TUESDAY = date(2026, 7, 7)
SATURDAY = date(2026, 7, 11)


def _slot_starts(day_slots, d):
    match = next(ds for ds in day_slots if ds.date == d)
    return [s.strftime("%H:%M") for s, _ in match.slots]


def test_single_weekly_rule_produces_evenly_spaced_slots(db_session, seed_doctor):
    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    starts = _slot_starts(day_slots, TUESDAY)
    assert starts[:4] == ["09:00", "09:30", "10:00", "10:30"]


def test_morning_and_afternoon_blocks_do_not_bleed_over_lunch_gap(db_session, seed_doctor):
    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    starts = _slot_starts(day_slots, TUESDAY)
    assert "12:00" not in starts
    assert "12:30" not in starts
    assert starts[-1] == "16:30"
    assert "13:00" in starts


def test_full_day_block_removes_all_slots(db_session, seed_doctor):
    db_session.add(
        AvailabilityException(doctor_id=seed_doctor.id, date=TUESDAY, kind=ExceptionKind.block, is_full_day_block=True)
    )
    db_session.commit()

    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    assert _slot_starts(day_slots, TUESDAY) == []


def test_partial_block_removes_only_overlapping_slots(db_session, seed_doctor):
    db_session.add(
        AvailabilityException(
            doctor_id=seed_doctor.id,
            date=TUESDAY,
            kind=ExceptionKind.block,
            is_full_day_block=False,
            start_time=time(10, 15),
            end_time=time(10, 45),
        )
    )
    db_session.commit()

    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    starts = _slot_starts(day_slots, TUESDAY)
    # The 10:00-10:30 slot partially overlaps the block and must be excluded entirely.
    # The free time after the block (10:45-12:00) re-anchors its own slot grid.
    assert "10:00" not in starts
    assert "09:30" in starts
    assert "10:45" in starts


def test_extra_exception_adds_slots_outside_weekly_hours(db_session, seed_doctor):
    db_session.add(
        AvailabilityException(
            doctor_id=seed_doctor.id,
            date=SATURDAY,
            kind=ExceptionKind.extra,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
    )
    db_session.commit()

    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, SATURDAY, SATURDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    assert _slot_starts(day_slots, SATURDAY) == ["10:00", "10:30"]


def test_existing_booking_removes_exactly_that_slot(db_session, seed_doctor, seed_patient):
    tz = ZoneInfo(TZ)
    start = datetime.combine(TUESDAY, time(10, 0), tzinfo=tz)
    db_session.add(
        Appointment(
            doctor_id=seed_doctor.id,
            patient_id=seed_patient.id,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            status=AppointmentStatus.booked,
        )
    )
    db_session.commit()

    day_slots = compute_slots(
        db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    starts = _slot_starts(day_slots, TUESDAY)
    assert "10:00" not in starts
    assert "09:30" in starts
    assert "10:30" in starts


def test_past_slots_excluded_future_slots_today_included(db_session, seed_doctor):
    tz = ZoneInfo(TZ)
    now = datetime(2026, 7, 7, 9, 45, tzinfo=tz)  # Tuesday, mid-morning
    day_slots = compute_slots(db_session, seed_doctor.id, 30, TUESDAY, TUESDAY, TZ, now=now)
    starts = _slot_starts(day_slots, TUESDAY)
    assert "09:00" not in starts
    assert "09:30" not in starts
    assert "10:00" in starts


def test_valid_from_valid_until_bounds_are_respected(db_session, seed_doctor):
    # Add a Saturday-only rule valid strictly within a two-week window.
    db_session.add(
        WeeklyAvailabilityRule(
            doctor_id=seed_doctor.id,
            weekday=SATURDAY.weekday(),
            start_time=time(8, 0),
            end_time=time(9, 0),
            valid_from=date(2026, 7, 10),
            valid_until=date(2026, 7, 12),
        )
    )
    db_session.commit()

    in_range = compute_slots(
        db_session, seed_doctor.id, 30, SATURDAY, SATURDAY, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    assert _slot_starts(in_range, SATURDAY) == ["08:00", "08:30"]

    out_of_range_day = date(2026, 7, 18)  # next Saturday, outside valid_until
    out_of_range = compute_slots(
        db_session, seed_doctor.id, 30, out_of_range_day, out_of_range_day, TZ, now=datetime(2026, 7, 1, tzinfo=ZoneInfo(TZ))
    )
    assert _slot_starts(out_of_range, out_of_range_day) == []
