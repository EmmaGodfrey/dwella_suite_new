import React from "react";
import { Button, Nav, NavDrawerBody, NavDrawerFooter, NavItem, Text } from "@fluentui/react-components";
import { Dismiss24Regular, PanelLeft24Regular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

import { navigationItems } from "../navigation";
import { BrandMark } from "./BrandMark";

export const AppSideNav = ({ collapsed, mobileOpen, selectedValue, onCollapseToggle, onMobileClose }) => {
  const navigate = useNavigate();

  return (
    <aside className="dwella-sidebar" aria-hidden={!mobileOpen ? undefined : false}>
      <div className="dwella-sidebar-brand">
        <BrandMark compact={collapsed} onClick={onMobileClose} />
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

      <NavDrawerFooter className="dwella-sidebar-footer">
        <div className="dwella-plan-card">
          <Text>Active workspace</Text>
          <strong>Dwella operations</strong>
          <small>Core property tools enabled</small>
        </div>
        <Button className="dwella-collapse-button" appearance="subtle" icon={<PanelLeft24Regular />} onClick={onCollapseToggle}>
          <span>{collapsed ? "Expand" : "Collapse"} sidebar</span>
        </Button>
      </NavDrawerFooter>
    </aside>
  );
};
