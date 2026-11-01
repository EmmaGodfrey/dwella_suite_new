// apiRequest retains pagination as { results, pagination }. Portfolio reports
// put rows, totals and page metadata together inside that results object.
export function portfolioReportData(response) {
  const data = response?.results;
  if (!data || !Array.isArray(data.rows)) {
    throw new Error("The report response is missing its rows.");
  }
  return data;
}
