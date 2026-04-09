import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { Shell } from "../components/common/Shell";
import { useAuth } from "../hooks/useAuth";
import { loadCurrentUser } from "../store/slices/authSlice";
import { AssignmentsPage } from "../pages/AssignmentsPage";
import { ChatPage } from "../pages/ChatPage";
import { CoursesPage } from "../pages/CoursesPage";
import { DashboardPage } from "../pages/DashboardPage";
import { GradesPage } from "../pages/GradesPage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";

const ProtectedRoutes = () => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Shell />;
};

export const App = () => {
  const { dispatch, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      void dispatch(loadCurrentUser());
    }
  }, [dispatch, isAuthenticated]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<ProtectedRoutes />}>
        <Route index element={<DashboardPage />} />
        <Route path="courses" element={<CoursesPage />} />
        <Route path="assignments" element={<AssignmentsPage />} />
        <Route path="grades" element={<GradesPage />} />
        <Route path="chat" element={<ChatPage />} />
      </Route>
    </Routes>
  );
};
