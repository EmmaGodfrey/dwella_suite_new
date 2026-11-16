// Super admins sit outside workspaces. Inside one, a property admin (stored as
// `landlord`) oversees everything, a property manager works on assigned
// properties, and tenants use the portal. Both management roles share the
// `landlord` persona; `role` tells them apart.
const MANAGEMENT_ROLES = new Set(["landlord", "manager"]);
const PORTFOLIO_ROLES = new Set(["landlord", "manager"]);

export function getUserAccess(user) {
  if (user?.access) return user.access;

  if (!user) {
    return {
      persona: "unassigned",
      role: "unassigned",
      can_view_portfolio: false,
      can_manage_properties: false,
      can_view_reports: false,
    };
  }

  if (user?.is_staff || user?.is_superuser) {
    return {
      persona: "platform_admin",
      role: "platform_admin",
      can_view_portfolio: false,
      can_manage_properties: false,
      can_view_reports: false,
    };
  }

  const role = user?.memberships?.find((membership) => membership.is_active)?.role;
  return {
    persona: role === "tenant" ? "tenant" : MANAGEMENT_ROLES.has(role) ? "landlord" : "unassigned",
    role: role || "unassigned",
    can_view_portfolio: PORTFOLIO_ROLES.has(role),
    can_manage_properties: MANAGEMENT_ROLES.has(role),
    can_view_reports: PORTFOLIO_ROLES.has(role),
  };
}

// Whoever may run the workspace itself: the team, payouts, receiving accounts,
// imports and workspace settings. The API enforces this; the app only hides
// what a property manager would be refused.
export function isWorkspaceAdmin(user) {
  const access = getUserAccess(user);
  return Boolean(access.can_manage_properties) && access.role !== "manager";
}

export function accessLabel(user) {
  const { persona, role } = getUserAccess(user);
  if (persona === "platform_admin") return "Super admin";
  if (persona === "tenant") return "Tenant";
  if (role === "manager") return "Property manager";
  if (role === "landlord") return "Property admin";
  return "Access pending";
}
