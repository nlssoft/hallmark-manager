import type { LoginRequest } from "../types/auth";
import { api, authApi } from "./axios";

export function getCSRFToken() {
  return api.get("/csrf/");
}

export function login(data: LoginRequest) {
  return api.post("auth/login/", data);
}

export function logout() {
  return api.post("auth/logout/");
}

export function refresh() {
  return authApi.post("auth/token/refresh/");
}

export function getCurrentUser() {
  return api.get("auth/user/");
}
