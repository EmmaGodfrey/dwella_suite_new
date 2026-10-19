import React, { useContext } from "react";
import { Button, Tooltip } from "@fluentui/react-components";
import { Navigation24Regular, WeatherMoon24Regular, WeatherSunny24Regular } from "@fluentui/react-icons";

import { DwellaThemeContext } from "../../App";

// The account menu lives at the foot of the sidebar now, so the bar carries
// only the page's name and the theme switch.
export const AppTopbar = ({ title, description, onMobileOpen }) => {
  const { darkMode, setDarkMode } = useContext(DwellaThemeContext);
  const themeLabel = darkMode ? "Switch to light theme" : "Switch to dark theme";

  return (
    <header className="dwella-topbar">
      <Button className="dwella-mobile-menu" appearance="subtle" icon={<Navigation24Regular />} onClick={onMobileOpen} aria-label="Open navigation" />

      <div className="dwella-page-title">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      <div className="dwella-topbar-actions">
        <Tooltip content={themeLabel} relationship="label">
          <Button
            className="dwella-icon-action"
            appearance="subtle"
            icon={darkMode ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />}
            onClick={() => setDarkMode((value) => !value)}
          />
        </Tooltip>
      </div>
    </header>
  );
};
