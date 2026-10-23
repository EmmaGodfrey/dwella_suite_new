/** Select the owning step for client rules or nested API field errors. */
export function firstErrorStep(data, groups, fallback = 0) {
  const names = [];
  const walk = (value, path = "") => {
    if (Array.isArray(value) || typeof value === "string") {
      if (value.length) names.push(path);
    } else if (value && typeof value === "object")
      Object.entries(value).forEach(([key, inner]) =>
        walk(inner, path ? `${path}.${key}` : key),
      );
  };
  walk(data);
  const index = groups.findIndex((group) =>
    names.some((name) => group.includes(name)),
  );
  return index < 0 ? fallback : index;
}

export function ruleErrors(rules) {
  return Object.fromEntries(
    Object.entries(rules)
      .map(([name, rule]) => [name, rule()])
      .filter(([, message]) => message),
  );
}
