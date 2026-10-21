import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Input,
  Radio,
  RadioGroup,
} from "@fluentui/react-components";
import { Add20Regular, Receipt24Regular, ReceiptAdd20Regular, Search20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useGenerateInvoicesMutation } from "../../Services/mutations";
import { useBillingSummaryQuery, useCurrentUserQuery, useInvoicesQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { invoiceBadgeProps, invoiceViews, periodLabel } from "../../shared/billing";
import { EmptyState, SegmentedFilter, PageActions, StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import ChargeDrawer from "./ChargeDrawer";
import "../../shared/records.scss";
import "./billing.scss";

const PAGE_SIZE = 20;
const monthValue = (offset) => {
  const today = new Date();
  const date = new Date(today.getFullYear(), today.getMonth() + offset, 1);
  return { value: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`, label: date.toLocaleDateString("en-GB", { month: "long", year: "numeric" }) };
};

function SummaryStrip() {
  const summary = useBillingSummaryQuery();
  const data = summary.data;
  const stat = (label, value, note, tone) => (
    <div className="dwella-stat">
      <span>{label}</span>
      {summary.isLoading ? <span className="dwella-skeleton" style={{ height: 24, width: 110 }} /> : <strong className={tone}>{value}</strong>}
      {note ? <small className={tone}>{note}</small> : null}
    </div>
  );
  if (summary.isError) return null;
  const month = data ? periodLabel(data.month) : "";
  return (
    <div className="dwella-stat-strip">
      {stat(`Billed · ${month}`, formatMoney(data?.billed_this_month, { whole: true }), data ? `${data.invoices_this_month} invoices` : null)}
      {stat(`Collected · ${month}`, formatMoney(data?.collected_this_month, { whole: true }), null, "is-positive")}
      {stat("Outstanding", formatMoney(data?.outstanding, { whole: true }), "Across all unpaid invoices")}
      {stat("Overdue", formatMoney(data?.overdue, { whole: true }), data ? `${data.overdue_count} ${data.overdue_count === 1 ? "invoice" : "invoices"}` : null, Number(data?.overdue) > 0 ? "is-negative" : undefined)}
    </div>
  );
}

function GenerateDialog({ onClose }) {
  const options = [monthValue(0), monthValue(1)];
  const [period, setPeriod] = useState(options[0].value);
  const mutation = useGenerateInvoicesMutation({
    onSuccess: (data) => {
      const parts = [`${data.created} new ${data.created === 1 ? "invoice" : "invoices"}`];
      if (data.already_billed) parts.push(`${data.already_billed} already billed`);
      if (data.late_fees_added) parts.push(`${data.late_fees_added} late ${data.late_fees_added === 1 ? "fee" : "fees"} added`);
      toast.success(parts.join(" · "));
      onClose();
    },
    onError: (error) => toast.error(error.message || "Could not generate invoices."),
  });
  return (
    <Dialog open onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Generate rent invoices</DialogTitle>
          <DialogContent className="dwella-dialog-copy">
            <p>Every active lease gets one rent invoice for the month. Leases already billed are skipped, so this is safe to run again. Late fees that have fallen due are added at the same time.</p>
            <RadioGroup value={period} onChange={(_, data) => setPeriod(data.value)}>
              {options.map((option) => <Radio key={option.value} value={option.value} label={option.label} />)}
            </RadioGroup>
          </DialogContent>
          <DialogActions>
            <Button disabled={mutation.isPending} onClick={onClose}>Cancel</Button>
            <Button appearance="primary" disabled={mutation.isPending} onClick={() => mutation.mutate({ period })}>
              {mutation.isPending ? "Generating…" : "Generate"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

function TableSkeleton() {
  return [0, 1, 2, 3, 4].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      {[70, 140, 150, 110, 80, 80, 80, 90].map((width, index) => (
        <td key={index}><span className="dwella-skeleton" style={{ height: 12, width }} /></td>
      ))}
    </tr>
  ));
}

export default function Billing() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const [view, setView] = useState(() => params.get("view") || "all");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState({ search: "", page: 1 });
  const [dialog, setDialog] = useState(null); // null | "generate" | "charge"
  const tenantFilter = params.get("tenant") || "";

  useEffect(() => {
    const timeout = setTimeout(() => setQuery((current) => (current.search === search ? current : { search, page: 1 })), 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const filters = {
    ...(invoiceViews.find((item) => item.value === view)?.filters || {}),
    ...(tenantFilter ? { tenant: tenantFilter } : {}),
    search: query.search,
    page: query.page,
    page_size: PAGE_SIZE,
    ordering: "-issue_date",
  };
  const listQuery = useInvoicesQuery(filters, { placeholderData: (previous) => previous, staleTime: 30_000 });
  const invoices = listQuery.data?.results || [];
  const pagination = listQuery.data?.pagination;
  const filtered = Boolean(query.search || view !== "all" || tenantFilter);
  const clearFilters = () => {
    setSearch("");
    setView("all");
    setQuery({ search: "", page: 1 });
    if (tenantFilter) setParams({}, { replace: true });
  };
  const open = (id) => navigate(`/billing/invoices/${id}`);

  return (
    <div className="dwella-billing-page">
      <SummaryStrip />

      <div className="dwella-page-toolbar">
        <Button onClick={() => navigate("/billing/receipts")}>Receipts</Button>
        <SegmentedFilter
          label="Filter invoices"
          options={invoiceViews}
          value={view}
          onChange={(value) => {
            setView(value);
            setQuery((current) => ({ ...current, page: 1 }));
          }}
        />
        {tenantFilter ? (
          <Button size="small" appearance="secondary" onClick={() => setParams({}, { replace: true })}>
            One tenant · show all
          </Button>
        ) : null}
        <Input
          className="dwella-toolbar-search"
          aria-label="Search invoices"
          contentBefore={<Search20Regular />}
          placeholder="Search invoice, tenant, unit"
          value={search}
          onChange={(_, data) => setSearch(data.value)}
        />
        {canManage ? (
          <PageActions>
            <Button icon={<Add20Regular />} onClick={() => setDialog("charge")}>New charge</Button>
            <Button appearance="primary" icon={<ReceiptAdd20Regular />} onClick={() => setDialog("generate")}>Generate rent invoices</Button>
          </PageActions>
        ) : null}
      </div>

      {listQuery.isError ? (
        <div className="dwella-alert danger">
          Unable to load invoices. <Button size="small" onClick={() => listQuery.refetch()}>Retry</Button>
        </div>
      ) : null}

      {listQuery.isError && !invoices.length ? null : !listQuery.isLoading && !invoices.length ? (
        <EmptyState
          icon={<Receipt24Regular />}
          title={filtered ? "No matching invoices" : "No invoices yet"}
          description={
            filtered
              ? "Try another search or filter."
              : canManage
                ? "Generate this month's rent invoices from your active leases, or issue a one-off charge."
                : "Invoices will appear once the landlord bills rent."
          }
          actionLabel={filtered ? "Clear filters" : canManage ? "Generate rent invoices" : undefined}
          onAction={filtered ? clearFilters : canManage ? () => setDialog("generate") : undefined}
        />
      ) : (
        <div className="dwella-table-card" aria-busy={listQuery.isFetching}>
          <table className="dwella-table">
            <thead>
              <tr>
                <th scope="col">Invoice</th>
                <th scope="col">Tenant</th>
                <th scope="col">Unit</th>
                <th scope="col">For</th>
                <th scope="col">Due</th>
                <th scope="col" className="is-numeric">Amount</th>
                <th scope="col" className="is-numeric">Balance</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.isLoading ? <TableSkeleton /> : null}
              {invoices.map((invoice) => {
                const owing = Number(invoice.balance) > 0 && invoice.status !== "void";
                return (
                  <tr key={invoice.id} tabIndex={0} onClick={() => open(invoice.id)} onKeyDown={(event) => event.key === "Enter" && open(invoice.id)}>
                    <td><strong>{invoice.reference}</strong></td>
                    <td>{invoice.tenant_name}</td>
                    <td>{invoice.unit_name ? `${invoice.unit_name} · ${invoice.property_name}` : "—"}</td>
                    <td>{invoice.period_start ? periodLabel(invoice.period_start) : invoice.lines[0]?.description || "Charge"}</td>
                    <td>{formatDate(invoice.due_date)}</td>
                    <td className="is-numeric">{formatMoney(invoice.total)}</td>
                    <td className={`is-numeric ${owing ? (invoice.days_overdue > 0 ? "is-negative" : "") : "is-muted"}`}>
                      {invoice.status === "void" ? "—" : formatMoney(invoice.balance)}
                    </td>
                    <td><StatusBadge {...invoiceBadgeProps(invoice)} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {pagination ? (
            <footer className="dwella-table-footer">
              <span>Showing {invoices.length} of {pagination.count} {pagination.count === 1 ? "invoice" : "invoices"}</span>
              {pagination.total_pages > 1 ? (
                <span className="dwella-table-pager">
                  <Button size="small" disabled={!pagination.previous} onClick={() => setQuery((q) => ({ ...q, page: q.page - 1 }))}>Previous</Button>
                  <Button size="small" disabled={!pagination.next} onClick={() => setQuery((q) => ({ ...q, page: q.page + 1 }))}>Next</Button>
                </span>
              ) : null}
            </footer>
          ) : null}
        </div>
      )}

      {dialog === "generate" ? <GenerateDialog onClose={() => setDialog(null)} /> : null}
      {dialog === "charge" ? <ChargeDrawer tenantId={tenantFilter} onClose={() => setDialog(null)} onSaved={(invoice) => open(invoice.id)} /> : null}
    </div>
  );
}
