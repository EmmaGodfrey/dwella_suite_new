import React, { useEffect, useState } from "react";
import {
  Button,
  Hamburger,
  Nav,
  NavItem,
  NavCategory,
  NavSubItem,
  NavSubItemGroup,
  SplitNavItem,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  NavSectionHeader,
  Tooltip,
} from "@fluentui/react-components";
import { ChevronDown20Regular, ChevronRight20Regular, ChevronLeft24Regular, ChevronRight24Regular, Dismiss24Regular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

import { accessLabel, getUserAccess } from "../access";
import { getNavigationItems, navigationGroups } from "../navigation";
import { appHref } from "../storage";
import { BrandMark } from "./BrandMark";
import { UserMenu } from "./UserMenu";
import { useSupportAccess } from "../../Components/Platform/SupportAccess";
import "./appSideNav.scss";

// Ctrl/cmd/shift/alt-click and non-primary buttons must fall through to the
// browser so the anchors keep working as real links.
const opensOutsideTheApp = (event) =>
  event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || (event.button != null && event.button !== 0);

const workspaceFor = (user) => {
  const access = getUserAccess(user);
  if (access.persona === "platform_admin") return { name: access.acting_workspace?.name || "Platform", initials: "DW" };
  const membership =
    user?.memberships?.find((item) => item.is_active && item.organization?.id === access.organization_id) ||
    user?.memberships?.find((item) => item.is_active);
  const name = membership?.organization?.display_name || membership?.organization?.name || "Your workspace";
  const initials = name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
  return { name, initials };
};

export const AppSideNav = ({ collapsed, mobileOpen, selectedValue, onCollapseToggle, onMobileClose, onLogout, user }) => {
  const navigate = useNavigate();
  const showLabels = !collapsed || mobileOpen;
  const navigationItems = getNavigationItems(user);
  const activeModule = navigationItems.find(item => item.children?.some(child => child.value === selectedValue))?.value;
  const [openCategories, setOpenCategories] = useState(activeModule ? [activeModule] : []);
  useEffect(() => {
    setOpenCategories(activeModule ? [activeModule] : []);
  }, [activeModule, selectedValue]);
  const workspace = workspaceFor(user);
  const openWorkspace = useSupportAccess();
  const isAdmin = getUserAccess(user).persona === "platform_admin";
  const WorkspaceControl = isAdmin ? "button" : "div";

  const handleNavItemSelect = (event, data) => {
    const destination = navigationItems.flatMap(item => [item, ...item.children]).find((item) => item.value === data.value);

    if (!destination || opensOutsideTheApp(event)) {
      return;
    }

    event.preventDefault();
    navigate(destination.to);
    onMobileClose();
  };

  return (
    <>
      <aside className="dwella-sidebar">
        <div className="dwella-sidebar-brand">
          <BrandMark onClick={onMobileClose} showWordmark={showLabels} />
          <Button className="dwella-sidebar-close" appearance="subtle" icon={<Dismiss24Regular />} onClick={onMobileClose} aria-label="Close navigation" />
        </div>

        {/* Shows which organisation the figures belong to. It is a label, not a
            switcher: there is no second workspace to switch to yet. */}
        <WorkspaceControl type={isAdmin ? "button" : undefined} onClick={isAdmin ? () => openWorkspace() : undefined}
          className="dwella-workspace" title={!showLabels ? workspace.name : undefined} aria-label={isAdmin ? "Choose workspace" : undefined}>
          <span className="dwella-workspace-avatar" aria-hidden="true">{workspace.initials}</span>
          {showLabels ? (
            <span className="dwella-workspace-copy">
              <strong>{workspace.name}</strong>
              <small>{isAdmin ? getUserAccess(user).acting_workspace ? "Support session · 4h" : "Choose workspace" : accessLabel(user)}</small>
            </span>
          ) : null}
        </WorkspaceControl>

        <Nav
          role="navigation"
          aria-label="Primary"
          className="dwella-sidebar-nav"
          density="small"
          selectedValue={selectedValue}
          selectedCategoryValue={activeModule}
          openCategories={openCategories}
          multiple
          onNavItemSelect={handleNavItemSelect}
        >
          {navigationGroups.map((group) => {
            const items = navigationItems.filter((item) => item.group === group.value);
            if (!items.length) return null;

            return (
              <React.Fragment key={group.value}>
                {showLabels ? <NavSectionHeader className="dwella-nav-section">{group.label}</NavSectionHeader> : <span className="dwella-nav-divider" aria-hidden="true" />}
                {items.map((item) => item.children.length ? showLabels ? (
                  <React.Fragment key={item.value}>
                    <SplitNavItem className={`dwella-nav-module ${activeModule === item.value ? "is-active" : ""}`}
                      navItem={{ value: item.value, href: appHref(item.to), icon: { children: item.icon, className: "dwella-nav-item-icon" }, "data-tour": `nav-${item.value}` }}
                      actionButton={{
                        "aria-label": `${openCategories.includes(item.value) ? "Collapse" : "Expand"} ${item.label}`,
                        "aria-expanded": openCategories.includes(item.value),
                        "aria-controls": `nav-children-${item.value}`,
                        icon: openCategories.includes(item.value) ? <ChevronDown20Regular /> : <ChevronRight20Regular />,
                        onClick: () => setOpenCategories(current => current.includes(item.value) ? current.filter(value => value !== item.value) : [...current, item.value]),
                      }}>
                      {item.label}
                    </SplitNavItem>
                    <NavCategory value={item.value}>
                    <NavSubItemGroup id={`nav-children-${item.value}`} className="dwella-nav-children">
                      {item.children.map(child => <NavSubItem key={child.value} value={child.value} href={appHref(child.to)}>{child.label}</NavSubItem>)}
                    </NavSubItemGroup>
                    </NavCategory>
                  </React.Fragment>
                ) : (
                  <Menu key={item.value} positioning="after-top">
                    <MenuTrigger disableButtonEnhancement>
                      <Button className={`dwella-nav-flyout-trigger ${activeModule === item.value ? "is-active" : ""}`} appearance="transparent" icon={item.icon}
                        aria-label={`${item.label} sections`} data-tour={`nav-${item.value}`} />
                    </MenuTrigger>
                    <MenuPopover><MenuList aria-label={`${item.label} sections`}>
                      {item.children.map(child => <MenuItem as="a" key={child.value} href={appHref(child.to)} aria-current={selectedValue === child.value ? "page" : undefined}
                        onClick={event => handleNavItemSelect(event, { value: child.value })}>{child.label}</MenuItem>)}
                    </MenuList></MenuPopover>
                  </Menu>
                ) : (
                  <NavItem
                    aria-label={item.label}
                    key={item.value}
                    value={item.value}
                    data-tour={`nav-${item.value}`}
                    href={appHref(item.to)}
                    icon={{ children: item.icon, className: "dwella-nav-item-icon" }}
                    title={!showLabels ? item.label : undefined}
                  >
                    {showLabels ? item.label : null}
                  </NavItem>
                ))}
              </React.Fragment>
            );
          })}
        </Nav>

        <div className="dwella-sidebar-footer">
          {navigationItems.some((item) => item.group === "utility") ? (
            <Nav role="navigation" aria-label="Utility" className="dwella-sidebar-nav dwella-sidebar-utility-nav"
              density="small" selectedValue={selectedValue} onNavItemSelect={handleNavItemSelect}>
              {navigationItems.filter((item) => item.group === "utility").map((item) => (
                <NavItem key={item.value} value={item.value} href={appHref(item.to)} aria-label={item.label}
                  icon={{ children: item.icon, className: "dwella-nav-item-icon" }}
                  title={!showLabels ? item.label : undefined}>
                  {showLabels ? item.label : null}
                </NavItem>
              ))}
            </Nav>
          ) : null}
          <UserMenu user={user} onLogout={onLogout} compact={!showLabels} />
        </div>
      </aside>

      <Tooltip content={collapsed ? "Expand navigation" : "Collapse navigation"} relationship="label">
        <Hamburger
          className="dwella-sidebar-toggle"
          icon={collapsed ? <ChevronRight24Regular className="dwella-sidebar-toggle-glyph" /> : <ChevronLeft24Regular className="dwella-sidebar-toggle-glyph" />}
          onClick={onCollapseToggle}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-expanded={!collapsed}
          shape="circular"
          size="large"
        />
      </Tooltip>
    </>
  );
};
