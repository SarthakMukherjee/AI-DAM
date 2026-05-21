import { createContext, useState, useEffect } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);
export default AuthContext;
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // -----------------------------------
  // CHECK SESSION ON APP LOAD
  // calls /auth/me using the cookie
  // if cookie exists and valid → sets user
  // if not → user stays null
  // -----------------------------------

  useEffect(() => {
    const checkSession = async () => {
      try {
        const res = await api.get("/auth/me");
        setUser(res.data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkSession();
  }, []);

  // -----------------------------------
  // LOGIN
  // -----------------------------------

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    setUser({
      id: res.data.id,
      email: res.data.email,
      full_name: res.data.full_name,
      role: res.data.role,
    });
    return res.data;
  };

  // -----------------------------------
  // LOGOUT
  // -----------------------------------

  const logout = async () => {
    await api.post("/auth/logout");
    setUser(null);
  };

  // -----------------------------------
  // REGISTER
  // -----------------------------------

  const register = async (email, full_name, password) => {
    const res = await api.post("/auth/register", {
      email,
      full_name,
      password,
    });
    return res.data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

// export const useAuth = () => useContext(AuthContext);
