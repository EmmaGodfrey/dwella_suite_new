import React, { useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { logout } from "../Services/auth";
import { queryClient } from "../Services/queryClient";
import { useCurrentUserQuery, useSetupQuery } from "../Services/queries";
import { getUserAccess } from "../shared/access";
import { AppSideNav, AppTopbar, PageActionsSlot, PageHeader } from "../shared/components";
import { canAccessPath, getPageMeta, getSelectedNavValue } from "../shared/navigation";
import { SupportAccessProvider, SupportBanner } from "../Components/Platform/SupportAccess";
import { toast } from "react-toastify";
import { USER_STORAGE_KEY } from "../shared/storage";

const getCachedUser = () => {
  try {
    return JSON.parse(localStorage.getItem(USER_STORAGE_KEY) || "null");
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
  const [actionsSlot, setActionsSlot] = useState(null);
  const persona = getUserAccess(user).persona;
  const setup = useSetupQuery({ enabled: Boolean(user) && ["landlord", "unassigned"].includes(persona) });

  useEffect(() => {
    if (setup.data?.needs_setup && location.pathname !== "/setup") navigate("/setup", { replace: true });
  }, [setup.data?.needs_setup, location.pathname, navigate]);

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
  // The dashboard leads with the organization's name instead, and detail pages
  // (`/leases/<id>`) carry their own title with a back link.
  const showHeader = location.pathname !== "/dashboard" && location.pathname.split("/").filter(Boolean).length < 2;
  const selectedNavValue = getSelectedNavValue(location.pathname, user);
  const shellClass = useMemo(
    () => ["dwella-app-shell", collapsed ? "is-collapsed" : "", mobileOpen ? "nav-open" : ""].filter(Boolean).join(" "),
    [collapsed, mobileOpen]
  );

  const handleLogout = async () => {
    if (queryClient.isMutating()) { toast.info("Wait for the current change to finish before signing out."); return; }
    try {
      await logout();
      await queryClient.cancelQueries();
      queryClient.clear();
      navigate("/login", { replace: true });
    } catch (error) { toast.error(`Couldn’t sign out: ${error.message}. Try again.`); }
  };

  return (
    <SupportAccessProvider user={user}><div className={shellClass}>
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
        <AppTopbar onMobileOpen={() => setMobileOpen(true)} />
        <SupportBanner />

        <main className="dwella-content">
          <PageActionsSlot.Provider value={showHeader ? actionsSlot : null}>
            {showHeader ? <PageHeader title={meta[0]} description={meta[1]} onSlot={setActionsSlot} /> : null}
            {getUserAccess(user).workspace_suspended ? <div role="status" className="admin-card"><h1>Workspace suspended</h1><p>Contact Dwella support to restore access to your workspace.</p></div> : <Outlet />}
          </PageActionsSlot.Provider>
        </main>
      </div>
    </div></SupportAccessProvider>
  );
};

export default AppLayout;
