import {
  createContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
} from "react";
import type { AuthContextType, LoginRequest, Props, User } from "../types/auth";
import { getCSRFToken, getCurrentUser, login } from "../api/auth";
import {
  authChannel,
  handleAuthfailure,
  registerAuthFailureHandler,
} from "../auth/events";
import { useNavigate } from "react-router-dom";

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: Props) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // this calls auth/user and set user
  const loadUser = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getCurrentUser();
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // make login request and set user
  const loginUser = useCallback(
    async (data: LoginRequest) => {
      await login(data);
      await loadUser();
    },
    [loadUser],
  );

  // the value that every page uses
  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: user !== null,
      isParent: user !== null && user.is_parent,
      plan: user?.subscription?.subscription_plan?.tier ?? "None",
      loginUser,
    }),
    [user, loading, loginUser],
  );

  useEffect(() => {
    void getCSRFToken();
  }, []);

  // linter issue
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    registerAuthFailureHandler(() => {
      setUser(null);
      navigate("/", { replace: true });
    });
  }, [navigate]);

  useEffect(() => {
    authChannel.onmessage = (event) => {
      switch (event.data.type) {
        case "logout":
          handleAuthfailure();
          break;
      }
    };
    return () => {
      authChannel.onmessage = null;
    };
  }, []);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
