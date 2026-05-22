import { useState, useEffect, useRef } from "react";
import api from "../../api/axios";
import "../../styles/navbar.css";

const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // -----------------------------------
  // FETCH UNREAD NOTIFICATIONS
  // -----------------------------------

  const fetchNotifications = async () => {
    try {
      const res = await api.get("/admin/notifications");
      setNotifications(res.data);
    } catch {
      setNotifications([]);
    }
  };

  useEffect(() => {
    // slight delay so it doesn't fire synchronously
    const timer = setTimeout(fetchNotifications, 0);
    const interval = setInterval(fetchNotifications, 30000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  // -----------------------------------
  // CLOSE ON OUTSIDE CLICK
  // -----------------------------------

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // -----------------------------------
  // MARK AS READ
  // -----------------------------------

  const markRead = async (id) => {
    try {
      await api.patch(`/admin/notifications/${id}/read`);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch {
      // silent fail
    }
  };

  const markAllRead = async () => {
    try {
      await api.patch("/admin/notifications/read-all");
      setNotifications([]);
    } catch {
      // silent fail
    }
  };

  return (
    <div className="notif-wrapper" ref={ref}>
      {/* BELL BUTTON */}
      <button
        className="notif-bell"
        onClick={() => setOpen((o) => !o)}
        title="Notifications"
      >
        🔔
        {notifications.length > 0 && (
          <span className="notif-badge">{notifications.length}</span>
        )}
      </button>

      {/* DROPDOWN */}
      {open && (
        <div className="notif-dropdown">
          <div className="notif-header">
            <span>Notifications</span>
            {notifications.length > 0 && (
              <button className="notif-clear" onClick={markAllRead}>
                Mark all read
              </button>
            )}
          </div>

          <div className="notif-list">
            {notifications.length === 0 ? (
              <div className="notif-empty">No new notifications</div>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="notif-item">
                  <div className="notif-message">{n.message}</div>
                  {n.reason && (
                    <div className="notif-reason">Reason: {n.reason}</div>
                  )}
                  <button
                    className="notif-dismiss"
                    onClick={() => markRead(n.id)}
                  >
                    Dismiss
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
