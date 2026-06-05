import axios from "axios";

const api = axios.create({
  // Hardcode your Hugging Face space URL directly as the ultimate fallback string
  baseURL: import.meta.env.VITE_API_URL || "https://monojitve-dam.hf.space",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
