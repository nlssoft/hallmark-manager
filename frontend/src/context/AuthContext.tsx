import { createContext, useState, useEffect, useMemo } from "react";
import type { AuthContextType, Props, User } from "../types/auth";
import { getCurrentUser } from "../api/auth";
import { registerAuthFailureHandler } from "../auth/event";
import { useNavigate } from "react-router-dom";

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: Props) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: user !== null,
    }),
    [user, loading],
  );

  useEffect(() => {
    async function loadUser() {
      try {
        const response = await getCurrentUser();
        setUser(response.data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  useEffect(() => {
    registerAuthFailureHandler(() => {
      setUser(null);
      navigate("/", { replace: true });
    });
  }, [navigate]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
