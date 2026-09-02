import { webDarkTheme, webLightTheme } from "@fluentui/react-components";

export const DWELLA_THEME_STORAGE_KEY = "dwella_theme";

export const dwellaPalette = {
  evergreen: "#1c493f",
  evergreenDark: "#0a211d",
  evergreenHover: "#173e35",
  gold: "#dfa63a",
  goldHover: "#c99027",
  ink: "#12231f",
  muted: "#66756f",
  line: "#d6dfdb",
  wash: "#f7f9f8",
  paper: "#ffffff",
  danger: "#c84f4f",
};

export const dwellaTypography = {
  fontFamilyBase: '"Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  fontFamilyMonospace: '"Cascadia Mono", Consolas, "Courier New", monospace',
  fontSizeBase100: "11px",
  fontSizeBase200: "12px",
  fontSizeBase300: "13px",
  fontSizeBase400: "14px",
  fontSizeBase500: "16px",
  fontSizeBase600: "18px",
  fontSizeHero700: "30px",
  lineHeightBase200: "16px",
  lineHeightBase300: "18px",
  lineHeightBase400: "20px",
  lineHeightHero700: "38px",
  fontWeightRegular: 400,
  fontWeightSemibold: 600,
  fontWeightBold: 700,
};

export const dwellaLightTheme = {
  ...webLightTheme,
  ...dwellaTypography,
  colorBrandBackground: dwellaPalette.evergreen,
  colorBrandBackgroundHover: dwellaPalette.evergreenHover,
  colorBrandForeground1: dwellaPalette.evergreen,
  colorBrandForeground2: dwellaPalette.evergreen,
  colorBrandStroke1: dwellaPalette.evergreen,
  colorCompoundBrandForeground1: dwellaPalette.evergreen,
  colorCompoundBrandStroke: dwellaPalette.evergreen,
};

export const dwellaDarkTheme = {
  ...webDarkTheme,
  ...dwellaTypography,
  colorBrandBackground: dwellaPalette.gold,
  colorBrandBackgroundHover: dwellaPalette.goldHover,
  colorBrandForeground1: dwellaPalette.gold,
  colorBrandForeground2: "#f2d18d",
  colorBrandStroke1: dwellaPalette.gold,
  colorCompoundBrandForeground1: dwellaPalette.gold,
  colorCompoundBrandStroke: dwellaPalette.gold,
};

export function getStoredThemeMode() {
  return localStorage.getItem(DWELLA_THEME_STORAGE_KEY) === "dark";
}

export function applyThemeMode(darkMode) {
  document.body.classList.toggle("dark-only", darkMode);
  localStorage.setItem(DWELLA_THEME_STORAGE_KEY, darkMode ? "dark" : "light");
}
