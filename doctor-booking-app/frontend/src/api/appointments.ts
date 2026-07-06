import { apiClient } from "./client";
import type { Appointment } from "./types";

export const appointmentsApi = {
  book: (doctorId: string, startAt: string, reasonNote?: string) =>
    apiClient.post<Appointment>("/appointments", { doctor_id: doctorId, start_at: startAt, reason_note: reasonNote }),
  mine: () => apiClient.get<Appointment[]>("/appointments/mine"),
  doctorAgenda: (dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams();
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    const qs = params.toString();
    return apiClient.get<Appointment[]>(`/appointments/doctor/mine${qs ? `?${qs}` : ""}`);
  },
  cancel: (appointmentId: string) => apiClient.post<Appointment>(`/appointments/${appointmentId}/cancel`),
  reschedule: (appointmentId: string, newStartAt: string) =>
    apiClient.post<Appointment>(`/appointments/${appointmentId}/reschedule`, { new_start_at: newStartAt }),
};
