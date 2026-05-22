import Navbar from "./Navbar";

const UserLayout = ({ children }) => {
  return (
    <>
      <Navbar />
      <main style={{ paddingTop: "var(--navbar-height)" }}>
        <div style={{ padding: "2rem" }}>{children}</div>
      </main>
    </>
  );
};

export default UserLayout;
