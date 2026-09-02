import React, { createContext, useEffect, useMemo, useState } from "react";
import { FluentProvider } from "@fluentui/react-components";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastContainer } from "react-toastify";
import Routers from "./Route";
import { queryClient } from "./Services/queryClient";
import { applyThemeMode, dwellaDarkTheme, dwellaLightTheme, getStoredThemeMode } from "./theme/dwellaTheme";

export const DwellaThemeContext = createContext({
  darkMode: false,
  setDarkMode: () => {},
});

const App = () => {
  const [darkMode, setDarkMode] = useState(getStoredThemeMode);
  const themeContext = useMemo(() => ({ darkMode, setDarkMode }), [darkMode]);

  useEffect(() => {
    applyThemeMode(darkMode);
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
