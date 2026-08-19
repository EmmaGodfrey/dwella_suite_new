export interface Settings {
  layout_type: string;
  layout: string;
  sidebar_icon: string;
  sidebar_setting: string;
}

export interface Color {
  layout_version?: string;
  primary: string;
  secondary: string;
}

export interface AppConfig {
  settings: Settings;
  color: Color;
}

export interface LayoutOption {
  class: string;
}
export interface SidebarOption {
  type: string;
}
