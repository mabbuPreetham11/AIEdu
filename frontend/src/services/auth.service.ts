import { api } from "./api";
import type { User } from "../types";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  first_name: string;
  last_name: string;
  role: "teacher" | "student";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>("/auth/login", payload);
    localStorage.setItem("accessToken", data.access_token);
    return data;
  },
  async register(payload: RegisterPayload) {
    const { data } = await api.post<User>("/auth/register", payload);
    return data;
  },
  async me() {
    const { data } = await api.get<User>("/auth/me");
    return data;
  },
  async logout() {
    await api.post("/auth/logout");
    localStorage.removeItem("accessToken");
  },
};
