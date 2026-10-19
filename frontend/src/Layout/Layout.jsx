import React, { useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import { useCurrentUserQuery } from "../Services/queries";
import { AppSideNav, AppTopbar } from "../shared/components";
import { canAccessPath, getPageMeta, getSelectedNavValue } from "../shared/navigation";

const getCachedUser = () => {
  try {
    return JSON.parse(localStorage.getItem("dwella_user") || "null");
  } catch {
    return null;
  }
};

const AppLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const cachedUser = getCachedUser();
  const { data: user = cachedUser, isLoading: userLoading } = useCurrentUserQuery({ staleTime: 60_000 });
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("dwella_sidebar_collapsed") === "true");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("dwella_sidebar_collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!userLoading && user && !canAccessPath(location.pathname, user)) {
      navigate("/dashboard", { replace: true });
    }
  }, [location.pathname, navigate, user, userLoading]);

  const meta = getPageMeta(location.pathname, user);
  const selectedNavValue = getSelectedNavValue(location.pathname, user);
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
      <AppSideNav
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        selectedValue={selectedNavValue}
        onCollapseToggle={() => setCollapsed((value) => !value)}
        onMobileClose={() => setMobileOpen(false)}
        onLogout={handleLogout}
        user={user}
      />

      {mobileOpen ? <button className="dwella-nav-scrim" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation" /> : null}

      <div className="dwella-main-frame">
        <AppTopbar title={meta[0]} description={meta[1]} onMobileOpen={() => setMobileOpen(true)} />

        <main className="dwella-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
