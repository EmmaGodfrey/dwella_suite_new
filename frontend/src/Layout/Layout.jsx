import React, { useContext, useEffect, useMemo, useState } from "react";
import { Avatar, Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Text, Title2 } from "@fluentui/react-components";
import {
  Alert24Regular,
  Building24Regular,
  ChevronDown24Regular,
  Dismiss24Regular,
  DocumentText24Regular,
  Home24Regular,
  PanelLeft24Regular,
  Payment24Regular,
  People24Regular,
  Person24Regular,
  Settings24Regular,
  Shield24Regular,
  SignOut24Regular,
  WeatherMoon24Regular,
  WeatherSunny24Regular,
  Wrench24Regular,
} from "@fluentui/react-icons";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { DwellaThemeContext } from "../App";
import { getApiBaseUrl } from "../Services/apiClient";
import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import { useCurrentUserQuery } from "../Services/queries";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: Home24Regular },
  { to: "/properties", label: "Properties", icon: Building24Regular },
  { to: "/tenants", label: "Tenants", icon: People24Regular },
  { to: "/leases", label: "Leases", icon: DocumentText24Regular },
  { to: "/billing", label: "Billing", icon: Payment24Regular },
  { to: "/maintenance", label: "Maintenance", icon: Wrench24Regular },
  { to: "/reports", label: "Reports", icon: Settings24Regular },
];

const pageMeta = {
  "/dashboard": ["Dashboard", "Portfolio health, occupancy, rent roll, and current work."],
  "/properties": ["Properties", "Search, filter, and grow the property portfolio."],
  "/tenants": ["Tenants", "Tenant CRM, occupancy records, and communication history."],
  "/leases": ["Leases", "Lease terms, renewals, deposits, and documents."],
  "/billing": ["Billing", "Rent invoices, collections, balances, and payment tracking."],
  "/maintenance": ["Maintenance", "Work orders, vendors, approvals, and service tracking."],
  "/reports": ["Reports", "Portfolio, arrears, occupancy, and owner reporting."],
  "/profile": ["Profile", "Account details, identity verification, and profile photo."],
  "/security": ["Security", "Two-factor authentication and account protection."],
};

const getCachedUser = () => {
  try {
    return JSON.parse(localStorage.getItem("dwella_user") || "null");
  } catch {
    return null;
  }
};

const initialsFor = (user) => {
  const source = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "DS";
  return source.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
};

const resolveMediaUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${getApiBaseUrl().replace(/\/api\/v1$/, "")}${value.startsWith("/") ? value : `/${value}`}`;
};

const AppLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const cachedUser = getCachedUser();
  const { data: user = cachedUser } = useCurrentUserQuery({ staleTime: 60_000 });
  const { darkMode, setDarkMode } = useContext(DwellaThemeContext);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("dwella_sidebar_collapsed") === "true");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("dwella_sidebar_collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const meta = pageMeta[location.pathname] || ["Dwella Suite", "Property operations workspace."];
  const avatarUrl = resolveMediaUrl(user?.profile?.avatar_url || user?.profile?.avatar || user?.avatar_url || user?.avatar);
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "Dwella Admin";
  const verificationStatus = user?.identity_verification?.status || "not_submitted";
  const shellClass = useMemo(
    () => ["dwella-app-shell", collapsed ? "is-collapsed" : "", mobileOpen ? "nav-open" : ""].filter(Boolean).join(" "),
    [collapsed, mobileOpen]
  );

  const handleLogout = () => {
    logout();
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  return (
    <div className={shellClass}>
      <aside className="dwella-sidebar">
        <div className="dwella-sidebar-brand">
          <Link to="/dashboard" aria-label="Dwella Suite dashboard">
            <span className="dwella-brand-mark"><img src="/assets/images/logo/dwella-icon.png" alt="" /></span>
            <span className="dwella-brand-copy"><strong>Dwella Suite</strong><small>Property OS</small></span>
          </Link>
          <Button className="dwella-sidebar-close" appearance="subtle" icon={<Dismiss24Regular />} onClick={() => setMobileOpen(false)} aria-label="Close navigation" />
        </div>

        <nav className="dwella-sidebar-nav" aria-label="Main navigation">
          <Text className="dwella-nav-section">Workspace</Text>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `dwella-nav-item${isActive ? " active" : ""}`} title={collapsed ? label : undefined}>
              <Icon />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="dwella-sidebar-footer">
          <div className="dwella-plan-card">
            <Text>Active workspace</Text>
            <strong>Dwella operations</strong>
            <small>Core property tools enabled</small>
          </div>
          <Button className="dwella-collapse-button" appearance="subtle" icon={<PanelLeft24Regular />} onClick={() => setCollapsed((value) => !value)}>
            <span>{collapsed ? "Expand" : "Collapse"} sidebar</span>
          </Button>
        </div>
      </aside>

      {mobileOpen ? <button className="dwella-nav-scrim" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation" /> : null}

      <div className="dwella-main-frame">
        <header className="dwella-topbar">
          <Button className="dwella-mobile-menu" appearance="subtle" icon={<PanelLeft24Regular />} onClick={() => setMobileOpen(true)} aria-label="Open navigation" />
          <div className="dwella-page-title">
            <Text>Dwella Suite</Text>
            <Title2 as="h1">{meta[0]}</Title2>
            <Text>{meta[1]}</Text>
          </div>
          <div className="dwella-topbar-actions">
            <Button className="dwella-icon-action" appearance="subtle" icon={<Alert24Regular />} aria-label="Notifications" />
            <Button className="dwella-icon-action" appearance="subtle" icon={darkMode ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />} onClick={() => setDarkMode((value) => !value)} aria-label="Toggle theme" />
            <Menu positioning="below-end">
              <MenuTrigger disableButtonEnhancement>
                <Button className="dwella-user-trigger" appearance="subtle">
                  <Avatar name={fullName} image={avatarUrl ? { src: avatarUrl } : undefined} initials={initialsFor(user)} size={32} />
                  <span><strong>{fullName}</strong><small>{verificationStatus === "approved" ? "Verified admin" : "Profile verification"}</small></span>
                  <ChevronDown24Regular />
                </Button>
              </MenuTrigger>
              <MenuPopover className="dwella-user-dropdown">
                <MenuList>
                  <MenuItem icon={<Person24Regular />} onClick={() => navigate("/profile")}>Profile</MenuItem>
                  <MenuItem icon={<Shield24Regular />} onClick={() => navigate("/security")}>Security</MenuItem>
                  <MenuItem icon={<SignOut24Regular />} onClick={handleLogout}>Log out</MenuItem>
                </MenuList>
              </MenuPopover>
            </Menu>
          </div>
        </header>

        <main className="dwella-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
