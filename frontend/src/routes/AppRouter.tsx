import { BrowserRouter, Routes, Route } from "react-router-dom";

import LoginPage from "../pages/login";
import Dashboard from "../pages/Dashboard";
import { ProtectedRoutes } from "./ProtectedRoutes";
import { GuestRoutes } from "./GuestRoutes";
import { AuthProvider } from "../context/AuthContext";

function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route
            path="/"
            element={
              <GuestRoutes>
                <LoginPage />
              </GuestRoutes>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoutes>
                <Dashboard />
              </ProtectedRoutes>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default AppRouter;
