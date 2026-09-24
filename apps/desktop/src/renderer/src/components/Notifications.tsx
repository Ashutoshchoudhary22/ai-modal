import { useNotificationStore } from "../state/notificationStore";

export function Notifications() {
  const notifications = useNotificationStore((s) => s.notifications);
  const dismiss = useNotificationStore((s) => s.dismiss);

  return (
    <>
      {notifications.map((n) => (
        <div key={n.id} className={`notification ${n.type}`} onClick={() => dismiss(n.id)}>
          {n.message}
        </div>
      ))}
    </>
  );
}
