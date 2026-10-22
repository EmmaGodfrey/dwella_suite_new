const MANAGEMENT_ROLES = new Set(["owner", "admin", "manager"]);
const PORTFOLIO_ROLES = new Set(["owner", "admin", "manager", "staff", "viewer"]);

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
  if (persona === "platform_admin") return "Platform administrator";
  if (persona === "tenant") return "Tenant";
  if (role === "owner") return "Landlord";
  if (role === "manager") return "Property manager";
  if (role === "admin") return "Organization administrator";
  if (role === "staff") return "Property staff";
  if (role === "viewer") return "Portfolio viewer";
  return "Access pending";
}
