export interface MenuItem {
  id: string;
  label?: string;
  shortcut?: string;
  disabled?: boolean;
  checked?: boolean;
  separator?: boolean;
  submenu?: MenuItem[];
  action?: () => void | Promise<void>;
}

export interface MenuDefinition {
  id: string;
  label: string;
  items: MenuItem[];
}
