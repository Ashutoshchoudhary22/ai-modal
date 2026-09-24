import { create } from "zustand";

export interface Notification {
  id: string;
  type: "success" | "info" | "warning" | "error";
  message: string;
}

interface NotificationStore {
  notifications: Notification[];
  notify: (type: Notification["type"], message: string) => void;
  dismiss: (id: string) => void;
}

let counter = 0;

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],

  notify: (type, message) => {
    const id = `notif-${++counter}`;
    set((state) => ({
      notifications: [...state.notifications, { id, type, message }],
    }));
    setTimeout(() => {
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      }));
    }, 5000);
  },

  dismiss: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
