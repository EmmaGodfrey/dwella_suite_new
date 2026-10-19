export const queryKeys = {
  health: ["health"],
  currentUser: ["accounts", "me"],
  dashboardSummary: ["properties", "dashboard"],
  organizations: ["organizations"],
  properties: (filters = {}) => ["properties", filters],
  property: (id) => ["properties", "detail", id],
  propertyOwners: (filters = {}) => ["properties", "owners", filters],
  units: (filters = {}) => ["properties", "units", filters],
};
