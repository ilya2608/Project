import { apiClient } from "./client";
import type { AdminAppointment, Doctor, Specialty } from "./types";

export interface DoctorCreatePayload {
  email: string;
  full_name: string;
  password: string;
  specialty_id?: string;
  bio?: string;
  slot_duration_minutes?: number;
}

export const adminApi = {
  listDoctors: () => apiClient.get<Doctor[]>("/admin/doctors"),
  createDoctor: (payload: DoctorCreatePayload) => apiClient.post<Doctor>("/admin/doctors", payload),
  updateDoctor: (doctorId: string, payload: Partial<DoctorCreatePayload & { is_accepting_bookings: boolean }>) =>
    apiClient.put<Doctor>(`/admin/doctors/${doctorId}`, payload),
  createSpecialty: (name: string, slug: string) => apiClient.post<Specialty>("/admin/specialties", { name, slug }),
  listAppointments: (doctorId?: string) =>
    apiClient.get<AdminAppointment[]>(`/admin/appointments${doctorId ? `?doctor_id=${doctorId}` : ""}`),
};
