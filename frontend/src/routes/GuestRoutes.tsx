import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Props } from "../types/frontedTypes/auth";

export function GuestRoutes({ children }: Props) {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return <p>Loading...</p>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
