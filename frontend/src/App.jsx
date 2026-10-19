import React, { createContext, useEffect, useMemo, useState } from "react";
import { FluentProvider, mergeClasses } from "@fluentui/react-components";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastContainer } from "react-toastify";
import Routers from "./Route";
import { queryClient } from "./Services/queryClient";
import { applyThemeMode, dwellaDarkTheme, dwellaLightTheme, getStoredThemeMode } from "./theme/dwellaTheme";

// Fluent renders no class for a Button's appearance, so the stylesheet could
// not tell a primary button from a subtle one. This hook tags each Button with
// `dwella-btn--<appearance>`, which is what gives primary and secondary buttons
// their raised edge in index.scss without touching every call site.
const customStyleHooks = {
  useButtonStyles_unstable: (state) => {
    state.root.className = mergeClasses(state.root.className, `dwella-btn--${state.appearance || "secondary"}`);
  },
};

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
          <FluentProvider theme={darkMode ? dwellaDarkTheme : dwellaLightTheme} customStyleHooks_unstable={customStyleHooks}>
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
