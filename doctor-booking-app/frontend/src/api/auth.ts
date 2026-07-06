import { apiClient } from "./client";
import type { Me } from "./types";

export const authApi = {
  me: () => apiClient.get<Me>("/auth/me"),
  staffLogin: (email: string, password: string) => apiClient.post<Me>("/auth/staff/login", { email, password }),
  logout: () => apiClient.post<{ ok: boolean }>("/auth/logout"),
};
