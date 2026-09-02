import React from "react";
import { Button, Nav, NavDrawerBody, NavItem, Text, Tooltip } from "@fluentui/react-components";
import { Dismiss24Regular, Navigation24Regular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

import { navigationItems } from "../navigation";
import { BrandMark } from "./BrandMark";

export const AppSideNav = ({ collapsed, mobileOpen, selectedValue, onCollapseToggle, onMobileClose }) => {
  const navigate = useNavigate();

  return (
    <aside className="dwella-sidebar" aria-hidden={!mobileOpen ? undefined : false}>
      <div className="dwella-sidebar-brand">
        <BrandMark compact={collapsed} onClick={onMobileClose} />
        <Tooltip content={collapsed ? "Expand navigation" : "Collapse navigation"} relationship="label">
          <Button
            className="dwella-sidebar-toggle"
            appearance="subtle"
            icon={<Navigation24Regular />}
            onClick={onCollapseToggle}
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          />
        </Tooltip>
        <Button className="dwella-sidebar-close" appearance="subtle" icon={<Dismiss24Regular />} onClick={onMobileClose} aria-label="Close navigation" />
      </div>

      <Nav className="dwella-sidebar-nav" selectedValue={selectedValue}>
        <Text className="dwella-nav-section">Workspace</Text>
        <NavDrawerBody>
          {navigationItems.map((item) => (
            <NavItem
              key={item.value}
              value={item.value}
              icon={item.icon}
              onClick={() => navigate(item.to)}
              title={collapsed ? item.label : undefined}
            >
              {item.label}
            </NavItem>
          ))}
        </NavDrawerBody>
      </Nav>
    </aside>
  );
};
