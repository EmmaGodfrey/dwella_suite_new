import React, { useContext } from "react";
import { Button, Text, Title2 } from "@fluentui/react-components";
import { Alert24Regular, Navigation24Regular, WeatherMoon24Regular, WeatherSunny24Regular } from "@fluentui/react-icons";

import { DwellaThemeContext } from "../../App";
import { UserMenu } from "./UserMenu";

export const AppTopbar = ({ title, description, user, onLogout, onMobileOpen }) => {
  const { darkMode, setDarkMode } = useContext(DwellaThemeContext);

  return (
    <header className="dwella-topbar">
      <Button className="dwella-mobile-menu" appearance="subtle" icon={<Navigation24Regular />} onClick={onMobileOpen} aria-label="Open navigation" />
      <div className="dwella-page-title">
        <Text>Dwella Suite</Text>
        <Title2 as="h1">{title}</Title2>
        <Text>{description}</Text>
      </div>
      <div className="dwella-topbar-actions">
        <Button className="dwella-icon-action" appearance="subtle" icon={<Alert24Regular />} aria-label="Notifications" />
        <Button className="dwella-icon-action" appearance="subtle" icon={darkMode ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />} onClick={() => setDarkMode((value) => !value)} aria-label="Toggle theme" />
        <UserMenu user={user} onLogout={onLogout} />
      </div>
    </header>
  );
};
