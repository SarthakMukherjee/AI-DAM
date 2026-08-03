import { Component } from "react";

// -----------------------------------
// ERROR BOUNDARY
// Catches JavaScript errors in child
// components and shows a fallback UI
// instead of crashing the whole page
// -----------------------------------

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "60vh",
            padding: "2rem",
            textAlign: "center",
            color: "#a1a1aa",
            fontFamily: "var(--font, system-ui, sans-serif)",
          }}
        >
          <h2 style={{ color: "#ef4444", marginBottom: "0.5rem", fontSize: "1.3rem" }}>
            Something went wrong
          </h2>
          <p style={{ marginBottom: "1.5rem", maxWidth: "400px", lineHeight: 1.6 }}>
            An unexpected error occurred. Please try again or refresh the page.
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: "0.6rem 1.5rem",
              background: "linear-gradient(135deg, #8b5cf6, #3b82f6)",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: 500,
              fontSize: "0.9rem",
            }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
