import React, { createContext, useEffect, useMemo, useState } from "react";
import { FluentProvider, webDarkTheme, webLightTheme } from "@fluentui/react-components";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastContainer } from "react-toastify";
import Routers from "./Route";
import { queryClient } from "./Services/queryClient";

export const DwellaThemeContext = createContext({
  darkMode: false,
  setDarkMode: () => {},
});

const dwellaLightTheme = {
  ...webLightTheme,
  colorBrandBackground: "#1c493f",
  colorBrandBackgroundHover: "#173e35",
  colorBrandForeground1: "#1c493f",
  colorBrandForeground2: "#1c493f",
  colorBrandStroke1: "#1c493f",
  colorCompoundBrandForeground1: "#1c493f",
  colorCompoundBrandStroke: "#1c493f",
};

const dwellaDarkTheme = {
  ...webDarkTheme,
  colorBrandBackground: "#dfa63a",
  colorBrandBackgroundHover: "#c99027",
  colorBrandForeground1: "#dfa63a",
  colorBrandForeground2: "#f2d18d",
  colorBrandStroke1: "#dfa63a",
  colorCompoundBrandForeground1: "#dfa63a",
  colorCompoundBrandStroke: "#dfa63a",
};

const App = () => {
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("dwella_theme") === "dark");
  const themeContext = useMemo(() => ({ darkMode, setDarkMode }), [darkMode]);

  useEffect(() => {
    document.body.classList.toggle("dark-only", darkMode);
    localStorage.setItem("dwella_theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  return (
    <div className="App">
      <QueryClientProvider client={queryClient}>
        <DwellaThemeContext.Provider value={themeContext}>
          <FluentProvider theme={darkMode ? dwellaDarkTheme : dwellaLightTheme}>
            <Routers />
            <ToastContainer position="top-right" newestOnTop />
          </FluentProvider>
        </DwellaThemeContext.Provider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </div>
  );
};

export default App;
