import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://monojitve-dam.hf.space",
  headers: {
    "Content-Type": "application/json",
  },
  // withCredentials removed - no longer using cookies
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
