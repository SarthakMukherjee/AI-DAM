import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AuthContext, { AuthProvider } from "./context/AuthContext";
import { useContext } from "react";
import RoleGuard from "./utils/roleGuard";

import Login from "./pages/Login";
import Register from "./pages/Register";

import AssetBrowser from "./pages/user/AssetBrowser";
import AssetDetail from "./pages/user/AssetDetail";

import AdminDashboard from "./pages/admin/AdminDashboard";
import UploadAsset from "./pages/admin/UploadAsset";

import ReviewQueue from "./pages/reviewer/ReviewQueue";

import SuperAdminDashboard from "./pages/superadmin/SuperAdminDashboard";
import UserManagement from "./pages/superadmin/UserManagement";

import Analytics from "./pages/shared/Analytics";

import "./styles/global.css";

// -----------------------------------
// ROOT REDIRECT
// sends user to their dashboard
// based on role after login
// -----------------------------------

const RootRedirect = () => {
  const { user, loading } = useContext(AuthContext);

  if (loading)
    return (
      <div className="loader-screen">
        <div className="loader" />
      </div>
    );

  if (!user) return <Navigate to="/login" replace />;

  const roleHome = {
    user: "/browse",
    admin: "/admin",
    reviewer: "/reviewer",
    super_admin: "/super-admin",
    marketing_manager: "/browse",
    designer: "/browse",
    content_lead: "/browse",
    sales_user: "/browse",
    website_team: "/browse",
    external_partner: "/browse",
  };

  return <Navigate to={roleHome[user.role] || "/login"} replace />;
};

const AppRoutes = () => {
  return (
    <Routes>
      {/* PUBLIC */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<RootRedirect />} />

      {/* USER + CONTENT TEAM — Browse */}
      <Route
        path="/browse"
        element={
          <RoleGuard allowedRoles={["user", "sales_user", "external_partner", "marketing_manager", "designer", "content_lead", "website_team"]}>
            <AssetBrowser />
          </RoleGuard>
        }
      />

      {/* ASSET DETAIL — accessible to all authenticated roles */}
      <Route
        path="/assets/:assetId"
        element={
          <RoleGuard allowedRoles={["user", "admin", "reviewer", "super_admin", "sales_user", "external_partner", "marketing_manager", "designer", "content_lead", "website_team"]}>
            <AssetDetail />
          </RoleGuard>
        }
      />

      {/* ADMIN */}
      <Route
        path="/admin"
        element={
          <RoleGuard allowedRoles={["admin", "super_admin"]}>
            <AdminDashboard />
          </RoleGuard>
        }
      />
      <Route
        path="/admin/upload"
        element={
          <RoleGuard allowedRoles={["admin", "super_admin"]}>
            <UploadAsset />
          </RoleGuard>
        }
      />

      {/* REVIEWER */}
      <Route
        path="/reviewer"
        element={
          <RoleGuard allowedRoles={["reviewer", "super_admin"]}>
            <ReviewQueue />
          </RoleGuard>
        }
      />

      {/* SUPER ADMIN */}
      <Route
        path="/super-admin"
        element={
          <RoleGuard allowedRoles={["super_admin"]}>
            <SuperAdminDashboard />
          </RoleGuard>
        }
      />
      <Route
        path="/super-admin/users"
        element={
          <RoleGuard allowedRoles={["super_admin"]}>
            <UserManagement />
          </RoleGuard>
        }
      />

      {/* ANALYTICS - shared */}
      <Route
        path="/analytics"
        element={
          <RoleGuard allowedRoles={["admin", "reviewer", "super_admin"]}>
            <Analytics />
          </RoleGuard>
        }
      />

      {/* FALLBACK */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
