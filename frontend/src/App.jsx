import React, { createContext, useEffect, useMemo, useState } from "react";
import { FluentProvider, mergeClasses } from "@fluentui/react-components";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastContainer } from "react-toastify";
import Routers from "./Route";
import { installHandyAgent } from "./Services/handyAgent";
import { queryClient } from "./Services/queryClient";
import "./shared/components/environmentBanner.scss";
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
  const isTest = import.meta.env.VITE_BASE_PATH === "/test/";
  const [darkMode, setDarkMode] = useState(getStoredThemeMode);
  const themeContext = useMemo(() => ({ darkMode, setDarkMode }), [darkMode]);

  useEffect(() => {
    applyThemeMode(darkMode);
  }, [darkMode]);

  useEffect(() => installHandyAgent(), []);

  return (
    <div className={isTest ? "App is-test-environment" : "App"}>
      <QueryClientProvider client={queryClient}>
        <DwellaThemeContext.Provider value={themeContext}>
          <FluentProvider theme={darkMode ? dwellaDarkTheme : dwellaLightTheme} customStyleHooks_unstable={customStyleHooks}>
            {isTest ? <aside className="dwella-environment-banner" aria-label="Test environment"><strong>TEST</strong><span>Separate test data. Changes here do not affect production.</span></aside> : null}
            <Routers />
            <ToastContainer position="top-right" newestOnTop />
          </FluentProvider>
        </DwellaThemeContext.Provider>
        {import.meta.env.DEV ? <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" /> : null}
      </QueryClientProvider>
    </div>
  );
};

export default App;
