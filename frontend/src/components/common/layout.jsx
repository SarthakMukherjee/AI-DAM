import { useState } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

const Layout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <Navbar onToggleSidebar={() => setCollapsed((c) => !c)} />
      <div className="page-layout">
        <Sidebar collapsed={collapsed} />
        <main
          className={`page-content ${collapsed ? "sidebar-collapsed" : ""}`}
        >
          {children}
        </main>
      </div>
    </>
  );
};

export default Layout;
