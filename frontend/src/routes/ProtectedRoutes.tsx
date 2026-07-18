import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Props } from "../types/frontedTypes/auth";

export function ProtectedRoutes({ children }: Props) {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return <p>Loading...</p>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}
