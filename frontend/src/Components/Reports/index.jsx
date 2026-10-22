import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Field, Select } from "@fluentui/react-components";
import { ArrowDownload20Regular } from "@fluentui/react-icons";
import { usePropertiesQuery, useReportQuery } from "../../Services/queries";
import { useExportReportMutation } from "../../Services/mutations";
import { SegmentedFilter, PageActions } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import "../../shared/records.scss";
import "./reports.scss";

export default function Reports() {
  const [report, setReport] = useState("rent-roll");
  const [property, setProperty] = useState("");
  const [page, setPage] = useState(1);
  const properties = usePropertiesQuery({ page_size: 200 });
  const query = useReportQuery(report, { property, page });
  const download = useExportReportMutation();
  const data = query.data;
  const arrears = report === "arrears";
  const columns = arrears
    ? [
        "Invoice / tenant",
        "Property / unit",
        "Due date",
        "Days overdue",
        "Balance",
      ]
    : [
        "Property / unit",
        "Tenant",
        "Status",
        "Rent due day",
        "Lease ends",
        "Monthly rent",
        "Outstanding",
      ];
  const totals = data?.totals || {};
  const stats = arrears
    ? [
        ["Total overdue", totals.balance],
        ["1–30 days", totals.days_1_30],
        ["31–60 days", totals.days_31_60],
        ["61–90 days", totals.days_61_90],
        ["91+ days", totals.days_91_plus],
      ]
    : [
        ["Monthly rent", totals.monthly_rent],
        ["Outstanding", totals.balance],
      ];
  return (
    <div>
      <PageActions>
        <Button
          icon={<ArrowDownload20Regular />}
          disabled={query.isLoading || query.isError || download.isPending}
          onClick={() => download.mutate({ report, property })}
        >
          {download.isPending ? "Exporting…" : "Export CSV"}
        </Button>
      </PageActions>
      <div className="dwella-page-toolbar">
        <SegmentedFilter
          label="Choose report"
          options={[
            { value: "rent-roll", label: "Rent roll" },
            { value: "arrears", label: "Arrears" },
          ]}
          value={report}
          onChange={(value) => {
            setReport(value);
            setPage(1);
          }}
        />
        <Field label="Property">
          <Select
            value={property}
            onChange={(_, event) => {
              setProperty(event.value);
              setPage(1);
            }}
          >
            <option value="">All properties</option>
            {(properties.data?.results || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <p className="dwella-muted-copy">
        {arrears
          ? "Unpaid invoices past their due date. Includes rent and other charges; invoices due today are not overdue."
          : "Active lease rent and current balances for each unit. Outstanding includes invoices for current and previous tenants."}
        {data ? ` As of ${formatDate(data.as_of)}.` : ""}
      </p>
      {query.isLoading ? (
        <p role="status">Loading report…</p>
      ) : query.isError ? (
        <div role="alert">
          <p>Could not load this report.</p>
          <Button onClick={() => query.refetch()}>Retry</Button>
        </div>
      ) : (
        <>
          <div
            className={`dwella-stat-strip dwella-report-stats ${arrears ? "is-arrears" : ""}`}
          >
            {stats.map(([label, value]) => (
              <div key={label} className="dwella-stat">
                <span>{label}</span>
                <strong>{formatMoney(value)}</strong>
              </div>
            ))}
            {!arrears ? (
              <div className="dwella-stat">
                <span>Units with active leases</span>
                <strong>
                  {totals.occupied} / {totals.units}
                </strong>
              </div>
            ) : null}
          </div>
          {!data.rows.length ? (
            <div className="dwella-surface">
              <h2>
                {arrears ? "No overdue invoices" : "No units to report on"}
              </h2>
              <p>
                {arrears
                  ? "There are no unpaid invoices past their due date for this selection."
                  : "Add a property and its units to start your rent roll."}
              </p>
              <Link to={arrears ? "/billing" : "/properties"}>
                {arrears ? "View billing" : "View properties"}
              </Link>
            </div>
          ) : (
            <div className="dwella-table-card">
              <div style={{ overflowX: "auto" }}>
                <table className="dwella-table">
                  <thead>
                    <tr>
                      {columns.map((label) => (
                        <th key={label} scope="col">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((row, index) => (
                      <tr key={row.invoice_id || row.lease_id || index}>
                        {arrears ? (
                          <>
                            <td>
                              <Link to={`/billing/invoices/${row.invoice_id}`}>
                                <strong>{row.invoice}</strong>
                              </Link>
                              <div>{row.tenant}</div>
                            </td>
                            <td>
                              {row.property}
                              <div className="dwella-muted-copy">
                                {row.unit || "—"}
                              </div>
                            </td>
                            <td>{formatDate(row.due_date)}</td>
                            <td>{row.days_overdue}</td>
                            <td className="is-numeric is-negative">
                              {formatMoney(row.balance)}
                            </td>
                          </>
                        ) : (
                          <>
                            <td>
                              <strong>{row.property}</strong>
                              <div>{row.unit}</div>
                            </td>
                            <td>
                              {row.lease_id ? (
                                <Link to={`/leases/${row.lease_id}`}>
                                  {row.tenant}
                                </Link>
                              ) : (
                                "No active lease"
                              )}
                            </td>
                            <td>{row.status.replaceAll("_", " ")}</td>
                            <td>{row.rent_due_day || "—"}</td>
                            <td>{formatDate(row.lease_end)}</td>
                            <td className="is-numeric">
                              {formatMoney(row.monthly_rent)}
                            </td>
                            <td className="is-numeric">
                              {formatMoney(row.balance)}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <footer className="dwella-table-footer">
                <span>
                  {data.total_rows} {arrears ? "invoices" : "units"} · Page{" "}
                  {page} of {data.total_pages}
                </span>
                <div className="dwella-table-pager">
                  <Button
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    disabled={page >= data.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              </footer>
            </div>
          )}
        </>
      )}
      {download.isError ? (
        <p role="alert">Could not export the report. Please try again.</p>
      ) : null}
    </div>
  );
}
