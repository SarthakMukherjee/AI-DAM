import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true, // sends httpOnly cookie automatically
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
