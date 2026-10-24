import React, { useContext } from "react";
import { Button, Tooltip } from "@fluentui/react-components";
import { Navigation24Regular, WeatherMoon20Regular, WeatherSunny20Regular } from "@fluentui/react-icons";

import { DwellaThemeContext } from "../../App";
import { AppBreadcrumbs } from "./AppBreadcrumbs";
import { NotificationBell } from "./NotificationBell";

// Where you are and the theme switch. The page's own title lives in the page
// header, so the bar reads the same on every screen.
export const AppTopbar = ({ onMobileOpen, tour }) => {
  const { darkMode, setDarkMode } = useContext(DwellaThemeContext);
  const themeLabel = darkMode ? "Switch to light theme" : "Switch to dark theme";

  return (
    <header className="dwella-topbar">
      <Button className="dwella-mobile-menu" appearance="subtle" icon={<Navigation24Regular />} onClick={onMobileOpen} aria-label="Open navigation" />

      <AppBreadcrumbs />

      <div className="dwella-topbar-actions">
        {tour}
        <NotificationBell />
        <Tooltip content={themeLabel} relationship="label">
          <Button
            className="dwella-icon-action"
            appearance="subtle"
            icon={darkMode ? <WeatherSunny20Regular /> : <WeatherMoon20Regular />}
            onClick={() => setDarkMode((value) => !value)}
          />
        </Tooltip>
      </div>
    </header>
  );
};
