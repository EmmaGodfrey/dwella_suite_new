const cell = (value) => {
  let text = String(value ?? "");
  if (/^[\s]*[=+@\-\t\r]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
};
export function correctionCsv(rows) {
  const selected = rows.filter(row => row.status !== "ready" || row.missing_details?.length);
  const columns = [...new Set(selected.flatMap(row => Object.keys(row.values || {})))];
  return [columns.map(cell).join(","), ...selected.map(row => columns.map(key => cell(row.values?.[key])).join(","))].join("\r\n");
}
