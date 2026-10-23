// Three account types: super admins (platform), landlords and tenants.
const MANAGEMENT_ROLES = new Set(["landlord"]);
const PORTFOLIO_ROLES = new Set(["landlord"]);

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
    persona: role === "tenant" ? "tenant" : role ? "landlord" : "unassigned",
    role: role || "unassigned",
    can_view_portfolio: PORTFOLIO_ROLES.has(role),
    can_manage_properties: MANAGEMENT_ROLES.has(role),
    can_view_reports: PORTFOLIO_ROLES.has(role),
  };
}

export function accessLabel(user) {
  const { persona, role } = getUserAccess(user);
  if (persona === "platform_admin") return "Super admin";
  if (persona === "tenant") return "Tenant";
  if (role === "landlord") return "Landlord";
  return "Access pending";
}
