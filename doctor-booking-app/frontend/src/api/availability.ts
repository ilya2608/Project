import { apiClient } from "./client";
import type { AvailabilityException, WeeklyRule } from "./types";

export const availabilityApi = {
  listRules: (doctorId: string) => apiClient.get<WeeklyRule[]>(`/doctors/${doctorId}/availability/rules`),
  createRule: (doctorId: string, rule: Omit<WeeklyRule, "id" | "doctor_id">) =>
    apiClient.post<WeeklyRule>(`/doctors/${doctorId}/availability/rules`, rule),
  deleteRule: (doctorId: string, ruleId: string) =>
    apiClient.delete<void>(`/doctors/${doctorId}/availability/rules/${ruleId}`),

  listExceptions: (doctorId: string) =>
    apiClient.get<AvailabilityException[]>(`/doctors/${doctorId}/availability/exceptions`),
  createException: (doctorId: string, exception: Omit<AvailabilityException, "id" | "doctor_id">) =>
    apiClient.post<AvailabilityException>(`/doctors/${doctorId}/availability/exceptions`, exception),
  deleteException: (doctorId: string, exceptionId: string) =>
    apiClient.delete<void>(`/doctors/${doctorId}/availability/exceptions/${exceptionId}`),
};
