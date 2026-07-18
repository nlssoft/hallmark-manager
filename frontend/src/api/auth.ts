import { mapUser } from "../mappers/userMapper";
import type { LoginRequest } from "../types/frontedTypes/auth";
import { api, authApi } from "./axios";

export function getCSRFToken() {
  return api.get("/csrf/");
}

export async function login(data: LoginRequest) {
  return api.post("auth/login/", data);
}

export function logout() {
  return api.post("auth/logout/");
}

export function refresh() {
  return authApi.post("auth/token/refresh/");
}

export async function getCurrentUser() {
  const {data}= await api.get("auth/user/");
  return mapUser(data)
}
