export const queryKeys = {
  health: ["health"],
  currentUser: ["accounts", "me"],
  dashboardSummary: ["properties", "dashboard"],
  organizations: ["organizations"],
  properties: (filters = {}) => ["properties", filters],
  propertyOwners: (filters = {}) => ["properties", "owners", filters],
  units: (filters = {}) => ["properties", "units", filters],
};
