import { useState, useContext } from "react";

import { Hexagon, ArrowRight } from "lucide-react";

import { useNavigate, Link } from "react-router-dom";

import AuthContext from "../context/AuthContext";

import "../styles/Login.css";

const Register = () => {
  const { register } = useContext(AuthContext);

  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });

    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");

      return;
    }

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");

      return;
    }

    setLoading(true);

    try {
      await register(form.email, form.full_name, form.password);

      navigate("/login", {
        state: {
          message: "Account created! Please sign in.",
        },
      });
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Registration failed. Try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      {/* LEFT PANEL */}

      <div className="auth-left">
        <div className="auth-brand">
          <span className="auth-brand-icon">
            <Hexagon size={22} />
          </span>

          <span className="auth-brand-name">AI-DAM</span>
        </div>

        <div className="auth-left-content">
          <h1>Join the platform</h1>

          <p>
            Create your account to access and discover AI-enriched digital
            assets curated for your team.
          </p>
        </div>

        <div className="auth-left-footer">
          Powered by AI enrichment pipelines
        </div>
      </div>

      {/* RIGHT PANEL */}

      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-header">
            <h2>Create account</h2>

            <p>Fill in the details below to get started</p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Full Name</label>

              <input
                type="text"
                name="full_name"
                placeholder="John Smith"
                value={form.full_name}
                onChange={handleChange}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label>Email</label>

              <input
                type="email"
                name="email"
                placeholder="you@company.com"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>

              <input
                type="password"
                name="password"
                placeholder="Min. 8 characters"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Confirm Password</label>

              <input
                type="password"
                name="confirm_password"
                placeholder="••••••••"
                value={form.confirm_password}
                onChange={handleChange}
                required
              />
            </div>

            {error && <div className="auth-error">{error}</div>}

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? (
                <span className="btn-loader" />
              ) : (
                <>
                  <span>Create account</span>

                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
