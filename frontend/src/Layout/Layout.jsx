import React, { useEffect, useMemo, useState } from "react";
import {
  Bell,
  Briefcase,
  ChevronDown,
  CreditCard,
  FileText,
  Home,
  LogOut,
  Menu,
  Moon,
  Settings,
  Shield,
  Sun,
  Tool,
  User,
  Users,
  X,
} from "react-feather";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { getApiBaseUrl } from "../Services/apiClient";
import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import { useCurrentUserQuery } from "../Services/queries";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/properties", label: "Properties", icon: Briefcase },
  { to: "/tenants", label: "Tenants", icon: Users },
  { to: "/leases", label: "Leases", icon: FileText },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/maintenance", label: "Maintenance", icon: Tool },
  { to: "/reports", label: "Reports", icon: Settings },
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
  return source
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
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
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("dwella_sidebar_collapsed") === "true");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("dwella_theme") === "dark");

  useEffect(() => {
    document.body.classList.toggle("dark-only", darkMode);
    localStorage.setItem("dwella_theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    localStorage.setItem("dwella_sidebar_collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    setMobileOpen(false);
    setAccountOpen(false);
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
            <span className="dwella-brand-mark">
              <img src="/assets/images/logo/dwella-icon.png" alt="" />
            </span>
            <span className="dwella-brand-copy">
              <strong>Dwella Suite</strong>
              <small>Property OS</small>
            </span>
          </Link>
          <button className="dwella-sidebar-close" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>

        <nav className="dwella-sidebar-nav" aria-label="Main navigation">
          <span className="dwella-nav-section">Workspace</span>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `dwella-nav-item${isActive ? " active" : ""}`} title={collapsed ? label : undefined}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="dwella-sidebar-footer">
          <div className="dwella-plan-card">
            <span>Active workspace</span>
            <strong>Dwella operations</strong>
            <small>Core property tools enabled</small>
          </div>
          <button className="dwella-collapse-button" type="button" onClick={() => setCollapsed((value) => !value)}>
            <Menu size={17} />
            <span>{collapsed ? "Expand" : "Collapse"} sidebar</span>
          </button>
        </div>
      </aside>

      {mobileOpen ? <button className="dwella-nav-scrim" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation" /> : null}

      <div className="dwella-main-frame">
        <header className="dwella-topbar">
          <button className="dwella-mobile-menu" type="button" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div className="dwella-page-title">
            <span>Dwella Suite</span>
            <h1>{meta[0]}</h1>
            <p>{meta[1]}</p>
          </div>
          <div className="dwella-topbar-actions">
            <button className="dwella-icon-action" type="button" aria-label="Notifications">
              <Bell size={18} />
              <i />
            </button>
            <button className="dwella-icon-action" type="button" onClick={() => setDarkMode((value) => !value)} aria-label="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="dwella-user-menu">
              <button className="dwella-user-trigger" type="button" onClick={() => setAccountOpen((value) => !value)}>
                <span className="dwella-user-avatar">{avatarUrl ? <img src={avatarUrl} alt={fullName} /> : initialsFor(user)}</span>
                <span>
                  <strong>{fullName}</strong>
                  <small>{verificationStatus === "approved" ? "Verified admin" : "Profile verification"}</small>
                </span>
                <ChevronDown size={15} />
              </button>
              {accountOpen ? (
                <div className="dwella-user-dropdown">
                  <Link to="/profile">
                    <User size={16} />
                    Profile
                  </Link>
                  <Link to="/security">
                    <Shield size={16} />
                    Security
                  </Link>
                  <button type="button" onClick={handleLogout}>
                    <LogOut size={16} />
                    Log out
                  </button>
                </div>
              ) : null}
            </div>
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
