import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Input } from "@fluentui/react-components";
import { Search20Regular } from "@fluentui/react-icons";
import { usePaymentsQuery } from "../../Services/queries";
import { paymentMethodLabel } from "../../shared/billing";
import { formatDate, formatMoney } from "../../shared/format";
import { SegmentedFilter, StatusBadge } from "../../shared/components";
import "../../shared/records.scss";

export default function Receipts() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [view, setView] = useState("all");
  const [page, setPage] = useState(1);
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery(search);
      setPage(1);
    }, 250);
    return () => clearTimeout(timer);
  }, [search]);
  const result = usePaymentsQuery({
    search: query,
    reversed: view === "all" ? undefined : view === "reversed",
    page,
    page_size: 25,
  });
  const rows = result.data?.results || [];
  const pagination = result.data?.pagination;
  return (
    <div>
      <header className="dwella-detail-header">
        <div>
          <h1>Receipts</h1>
          <p>Find recorded payments and print a receipt for your tenant.</p>
        </div>
      </header>
      <div className="dwella-page-toolbar">
        <Link to="/billing">← Invoices</Link>
        <SegmentedFilter
          label="Filter receipts"
          options={[
            { value: "all", label: "All receipts" },
            { value: "active", label: "Active" },
            { value: "reversed", label: "Reversed" },
          ]}
          value={view}
          onChange={(value) => {
            setView(value);
            setPage(1);
          }}
        />
        <Input
          aria-label="Search receipts"
          className="dwella-toolbar-search"
          contentBefore={<Search20Regular />}
          placeholder="Receipt, tenant or reference"
          value={search}
          onChange={(_, data) => setSearch(data.value)}
        />
      </div>
      {result.isLoading ? (
        <p role="status">Loading receipts…</p>
      ) : result.isError ? (
        <div role="alert">
          <p>Could not load receipts.</p>
          <Button onClick={() => result.refetch()}>Retry</Button>
        </div>
      ) : !rows.length ? (
        <div className="dwella-surface">
          <h2>No receipts found</h2>
          <p>
            Record a payment on an invoice to create a numbered receipt, or try
            another filter.
          </p>
        </div>
      ) : (
        <div className="dwella-table-card">
          <div style={{ overflowX: "auto" }}>
            <table className="dwella-table">
              <caption className="dwella-visually-hidden">
                Recorded payments and receipts
              </caption>
              <thead>
                <tr>
                  {[
                    "Receipt",
                    "Tenant",
                    "Invoice",
                    "Date paid",
                    "Method",
                    "Status",
                    "Amount",
                  ].map((label) => (
                    <th key={label} scope="col">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link to={`/billing/receipts/${row.id}`}>
                        <strong>{row.receipt_number}</strong>
                      </Link>
                    </td>
                    <td>{row.tenant_name}</td>
                    <td>
                      <Link to={`/billing/invoices/${row.invoice_id}`}>
                        {row.invoice_reference}
                      </Link>
                    </td>
                    <td>{formatDate(row.paid_on)}</td>
                    <td>{paymentMethodLabel(row.method)}</td>
                    <td>
                      <StatusBadge
                        value={row.reversed_at ? "reversed" : "received"}
                        color={row.reversed_at ? "danger" : "success"}
                      />
                    </td>
                    <td className="is-numeric">{formatMoney(row.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {pagination ? (
        <div className="dwella-page-toolbar" style={{ marginTop: 16 }}>
          <span>
            Page {page} of {pagination.total_pages || 1} · {pagination.count}{" "}
            receipts
          </span>
          <Button
            disabled={page <= 1 || result.isFetching}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <Button
            disabled={!pagination.next || result.isFetching}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}
