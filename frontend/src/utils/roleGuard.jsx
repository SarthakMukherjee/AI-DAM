import { useContext } from "react";
import { Navigate } from "react-router-dom";
import AuthContext from "../context/AuthContext";

const ROLE_HOME = {
  user: "/browse",
  admin: "/admin",
  reviewer: "/reviewer",
  super_admin: "/super-admin",
};

const RoleGuard = ({ children, allowedRoles }) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) return null;

  if (!user) return <Navigate to="/login" replace />;

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={ROLE_HOME[user.role] || "/login"} replace />;
  }

  return children;
};

export default RoleGuard;
