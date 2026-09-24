import { useEffect, useRef, useState } from "react";
import { MenuDropdown } from "./MenuDropdown";
import { useFileMenuActions } from "./useFileMenuActions";
import {
  buildEditMenu,
  buildFileMenu,
  buildHelpMenu,
  buildViewMenu,
  buildWindowMenu,
} from "./buildMenus";
import "./menubar.css";

export function MenuBar() {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const barRef = useRef<HTMLDivElement>(null);
  const actions = useFileMenuActions();

  const menus = [
    buildFileMenu(actions),
    buildEditMenu(actions),
    buildViewMenu(),
    buildWindowMenu(actions),
    buildHelpMenu(),
  ];

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!barRef.current?.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenMenu(null);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div className="menubar" ref={barRef}>
      {menus.map((menu) => (
        <div key={menu.id} style={{ position: "relative" }}>
          <button
            type="button"
            className={`menubar-item${openMenu === menu.id ? " active" : ""}`}
            onClick={() => setOpenMenu((prev) => (prev === menu.id ? null : menu.id))}
            onMouseEnter={() => {
              if (openMenu) setOpenMenu(menu.id);
            }}
          >
            {menu.label}
          </button>
          {openMenu === menu.id && (
            <MenuDropdown
              items={menu.items}
              onClose={() => setOpenMenu(null)}
              alignRight={menu.id === "help"}
            />
          )}
        </div>
      ))}
    </div>
  );
}
