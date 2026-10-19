import { createDarkTheme, createLightTheme } from "@fluentui/react-components";

export const DWELLA_THEME_STORAGE_KEY = "dwella_theme";

// Fluent derives ~40 brand tokens from a 16-step ramp, so the whole ramp is
// built from the logo navy rather than patching a few tokens -- a partial
// patch is what once left progress bars on Fluent's default blue. Light mode
// reads its brand fill from step 80, which is pinned to the logo's #1D417E.
const navyRamp = {
  10: "#040a15",
  20: "#08142a",
  30: "#0c1d3b",
  40: "#10264d",
  50: "#132e5c",
  60: "#173568",
  70: "#1a3b73",
  80: "#1d417e",
  90: "#2f5a9c",
  100: "#3d68a8",
  110: "#4a74b3",
  120: "#5a82c4",
  130: "#7395d0",
  140: "#8aa8db",
  150: "#b3c5e3",
  160: "#d9e2f1",
};

// These mirror the `--fs-*`/`--lh-*` scale in index.scss step for step. Fluent
// sizes its own Badges, Buttons, Dropdowns and ProgressBars from these tokens,
// so letting the two scales drift is what produced 11px Fluent text sitting
// next to 13px product text in the same row.
export const dwellaTypography = {
  fontFamilyBase: '"Figtree", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  fontFamilyMonospace: '"Cascadia Mono", Consolas, "Courier New", monospace',
  fontSizeBase100: "11px",
  fontSizeBase200: "12px",
  fontSizeBase300: "13px",
  fontSizeBase400: "14px",
  fontSizeBase500: "15px",
  fontSizeBase600: "17px",
  fontSizeHero700: "20px",
  fontSizeHero800: "26px",
  lineHeightBase100: "16px",
  lineHeightBase200: "18px",
  lineHeightBase300: "20px",
  lineHeightBase400: "21px",
  lineHeightBase500: "22px",
  lineHeightBase600: "24px",
  lineHeightHero700: "28px",
  lineHeightHero800: "33px",
  fontWeightRegular: 400,
  fontWeightSemibold: 600,
  fontWeightBold: 700,
};

// Fluent's own neutrals are pure greys. Menus, popovers and inputs read from
// these, so they are tinted to the same navy-grey family as `--dwella-*` or a
// dropdown would sit visibly off-colour against the page in either theme.
const lightNeutrals = {
  colorNeutralForeground1: "#111a2b",
  colorNeutralForeground2: "#4b566c",
  colorNeutralForeground3: "#667189",
  colorNeutralStroke1: "#d5dce7",
  colorNeutralStroke2: "#e7ebf2",
  colorNeutralBackground2: "#f8fafc",
  colorNeutralBackground3: "#f3f5f9",
};

const darkNeutrals = {
  colorNeutralForeground1: "#f8fafc",
  colorNeutralForeground2: "#b6c0d0",
  colorNeutralForeground3: "#8c97ab",
  colorNeutralBackground1: "#0f1c33",
  colorNeutralBackground1Hover: "#152542",
  colorNeutralBackground1Pressed: "#1a2a45",
  colorNeutralBackground2: "#0a1426",
  colorNeutralBackground3: "#152542",
  colorNeutralStroke1: "#22324f",
  colorNeutralStroke2: "#1a2a45",
};

export const dwellaLightTheme = {
  ...createLightTheme(navyRamp),
  ...lightNeutrals,
  ...dwellaTypography,
};

export const dwellaDarkTheme = {
  ...createDarkTheme(navyRamp),
  ...darkNeutrals,
  ...dwellaTypography,
};

export function getStoredThemeMode() {
  return localStorage.getItem(DWELLA_THEME_STORAGE_KEY) === "dark";
}

export function applyThemeMode(darkMode) {
  document.body.classList.toggle("dark-only", darkMode);
  localStorage.setItem(DWELLA_THEME_STORAGE_KEY, darkMode ? "dark" : "light");
}
