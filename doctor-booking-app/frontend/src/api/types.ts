export type UserRole = "patient" | "doctor" | "admin";

export interface Me {
  id: string;
  role: UserRole;
  full_name: string;
  email: string | null;
}

export interface Specialty {
  id: string;
  name: string;
  slug: string;
}

export interface Doctor {
  id: string;
  full_name: string;
  bio: string | null;
  specialty: Specialty | null;
  slot_duration_minutes: number;
  is_accepting_bookings: boolean;
}

export interface Slot {
  start_at: string;
  end_at: string;
}

export interface SlotsByDate {
  date: string;
  slots: Slot[];
}

export type AppointmentStatus =
  | "booked"
  | "cancelled_by_patient"
  | "cancelled_by_doctor"
  | "completed"
  | "no_show";

export interface Appointment {
  id: string;
  doctor_id: string;
  patient_id: string;
  start_at: string;
  end_at: string;
  status: AppointmentStatus;
  reason_note: string | null;
}

export interface WeeklyRule {
  id: string;
  doctor_id: string;
  weekday: number;
  start_time: string;
  end_time: string;
  valid_from: string | null;
  valid_until: string | null;
}

export interface AvailabilityException {
  id: string;
  doctor_id: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  is_full_day_block: boolean;
  kind: "block" | "extra";
  reason: string | null;
}

export interface AdminAppointment extends Appointment {
  doctor_name: string;
  patient_name: string;
}
