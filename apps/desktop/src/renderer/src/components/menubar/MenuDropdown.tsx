import type { MenuItem } from "./menuTypes";

interface MenuDropdownProps {
  items: MenuItem[];
  onClose: () => void;
  alignRight?: boolean;
}

function runItem(item: MenuItem, onClose: () => void) {
  if (item.disabled || item.separator) return;
  if (item.submenu) return;
  void item.action?.();
  onClose();
}

export function MenuDropdown({ items, onClose, alignRight }: MenuDropdownProps) {
  return (
    <div className={`menu-dropdown${alignRight ? " right" : ""}`} onClick={(e) => e.stopPropagation()}>
      {items.map((item, i) => {
        if (item.separator) {
          return <div key={`sep-${i}`} className="menu-dropdown-separator" />;
        }
        return (
          <button
            key={item.id}
            type="button"
            className={`menu-dropdown-item${item.checked ? " checked" : ""}${item.submenu ? " has-submenu" : ""}`}
            disabled={item.disabled}
            onClick={() => runItem(item, onClose)}
          >
            <span>{item.label}</span>
            {item.shortcut && <span className="menu-dropdown-shortcut">{item.shortcut}</span>}
            {item.submenu && (
              <div className="menu-submenu">
                {item.submenu.map((sub, j) => {
                  if (sub.separator) {
                    return <div key={`sub-sep-${j}`} className="menu-dropdown-separator" />;
                  }
                  return (
                    <button
                      key={sub.id}
                      type="button"
                      className={`menu-dropdown-item${sub.checked ? " checked" : ""}`}
                      disabled={sub.disabled}
                      onClick={() => runItem(sub, onClose)}
                    >
                      <span>{sub.label}</span>
                      {sub.shortcut && <span className="menu-dropdown-shortcut">{sub.shortcut}</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
