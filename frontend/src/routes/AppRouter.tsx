import { BrowserRouter, Routes, Route } from "react-router-dom";

import LoginPage from "../pages/loginPage";
import DashboardPage from "../pages/DashboardPage";
import { ProtectedRoutes } from "./ProtectedRoutes";
import { GuestRoutes } from "./GuestRoutes";
import { AuthProvider } from "../context/AuthContext";
import CustomerPage from "../pages/CustomerPage";
import ScrollToTop from "../components/ScrollToTop";

function AppRouter() {
    return (
        <BrowserRouter>
            <ScrollToTop />
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
                                <DashboardPage />
                            </ProtectedRoutes>
                        }
                    />
                    <Route
                        path="/customers"
                        element={
                            <ProtectedRoutes>
                                <CustomerPage />
                            </ProtectedRoutes>
                        }
                    />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default AppRouter;
