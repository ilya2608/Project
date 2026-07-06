import { apiClient } from "./client";
import type { Doctor, Specialty, SlotsByDate } from "./types";

export const doctorsApi = {
  listSpecialties: () => apiClient.get<Specialty[]>("/specialties"),
  listDoctors: (specialtyId?: string) =>
    apiClient.get<Doctor[]>(`/doctors${specialtyId ? `?specialty_id=${specialtyId}` : ""}`),
  getDoctor: (doctorId: string) => apiClient.get<Doctor>(`/doctors/${doctorId}`),
  getSlots: (doctorId: string, dateFrom: string, dateTo: string) =>
    apiClient.get<SlotsByDate[]>(`/doctors/${doctorId}/slots?date_from=${dateFrom}&date_to=${dateTo}`),
};
