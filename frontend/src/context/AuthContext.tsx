import {
  createContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
} from "react";
import type { AuthContextType, LoginRequest, Props, User } from "../types/frontedTypes/auth";
import { getCSRFToken, getCurrentUser, login, logout } from "../api/auth";
import {
  authChannel,
  handleAuthfailure,
  notifyAuthFailure,
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
      const data = await getCurrentUser();
      setUser(data);
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

  const logoutUser = useCallback(
    async ()=> {
      await logout()
      notifyAuthFailure()
    },
    []
  )

  // the value that every page uses
  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: user !== null,
      isParent: user !== null && user.isParent,
      loginUser,
      logoutUser,
    }),
    [user, loading, loginUser, logoutUser],
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
