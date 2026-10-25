import React from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  OverlayDrawer,
} from "@fluentui/react-components";
import { ArrowDownload20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { downloadPortalFile, usePortalInvoice, usePortalInvoices, usePortalPayments } from "../../Services/portal";
import { invoiceBadgeProps, lineKinds, paymentMethodLabel, periodLabel } from "../../shared/billing";
import { SegmentedFilter, StatusBadge } from "../../shared/components";
import { formatDate, formatMoney } from "../../shared/format";
import RentCheckout from "./RentCheckout";
import PortalState from "./PortalState";

const views = [
  { value: "unpaid", label: "Unpaid" },
  { value: "all", label: "All invoices" },
];
const kindLabel = (kind) => lineKinds.find((item) => item.value === kind)?.label || kind;

function InvoiceDrawer({ id, onClose }) {
  const query = usePortalInvoice(id);
  const invoice = query.data;
  const download = () =>
    downloadPortalFile(`invoices/${id}/pdf/`, `${invoice.reference}.pdf`).catch((error) =>
      toast.error(error.message || "Could not download the invoice."),
    );
  return (
    <OverlayDrawer open position="end" size="medium" className="dwella-drawer" onOpenChange={(_, data) => !data.open && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />} aria-label="Close" onClick={onClose} />}>
          {invoice ? `Invoice ${invoice.reference}` : "Invoice"}
        </DrawerHeaderTitle>
        {invoice ? <p className="dwella-drawer-note">{periodLabel(invoice.period_start)} · {invoice.property_name} · {invoice.unit_name}</p> : null}
      </DrawerHeader>
      <DrawerBody>
        {query.isLoading ? <span className="dwella-skeleton" style={{ height: 200, width: "100%" }} /> : null}
        {query.isError ? <p role="alert">Could not load the invoice. <Button size="small" onClick={() => query.refetch()}>Retry</Button></p> : null}
        {invoice ? (
          <div className="dwella-portal">
            <div className="dwella-portal-heading">
              <StatusBadge {...invoiceBadgeProps(invoice)} />
              <span className="dwella-muted-copy">Issued {formatDate(invoice.issue_date)} · due {formatDate(invoice.due_date)}</span>
            </div>
            <dl className="dwella-detail-list">
              {invoice.lines.map((line, index) => (
                <div key={index}><dt>{line.description || kindLabel(line.kind)}</dt><dd>{formatMoney(line.amount)}</dd></div>
              ))}
              <div><dt>Total</dt><dd>{formatMoney(invoice.total)}</dd></div>
              <div><dt>Paid</dt><dd>{formatMoney(invoice.amount_paid)}</dd></div>
              <div><dt><strong>Balance</strong></dt><dd><strong>{formatMoney(invoice.balance)}</strong></dd></div>
            </dl>
            <section>
              <h3>Payments</h3>
              {invoice.payments.length ? (
                <ul className="dwella-portal-list">
                  {invoice.payments.map((payment) => (
                    <li key={payment.id}>
                      <span>
                        <Link to={`/billing/receipts/${payment.id}`}>{payment.receipt_number}</Link>
                        <small>{formatDate(payment.paid_on)} · {paymentMethodLabel(payment.method)}</small>
                      </span>
                      <span className="dwella-badge-row">
                        {payment.reversed ? <StatusBadge color="subtle">Reversed</StatusBadge> : null}
                        <strong>{formatMoney(payment.amount)}</strong>
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="dwella-muted-copy">No payments recorded yet.</p>
              )}
            </section>
            <RentCheckout key={invoice.id} invoice={invoice} />
          </div>
        ) : null}
      </DrawerBody>
      <DrawerFooter className="dwella-drawer-footer">
        <Button onClick={onClose}>Close</Button>
        <Button appearance="primary" icon={<ArrowDownload20Regular />} disabled={!invoice} onClick={download}>Download PDF</Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}

function PaymentsList() {
  const query = usePortalPayments({ page_size: 20 });
  const payments = query.data?.results || [];
  return (
    <section className="dwella-surface">
      <h3>Payments and receipts</h3>
      {query.isLoading ? <span className="dwella-skeleton" style={{ height: 80, width: "100%" }} /> : null}
      {query.isError ? <p role="alert">Could not load payments. <Button size="small" onClick={() => query.refetch()}>Retry</Button></p> : null}
      {!query.isLoading && !query.isError && !payments.length ? (
        <p className="dwella-muted-copy">Payments your property manager records will appear here with a receipt.</p>
      ) : (
        <ul className="dwella-portal-list">
          {payments.map((payment) => (
            <li key={payment.id}>
              <span>
                <Link to={`/billing/receipts/${payment.id}`}>{payment.receipt_number}</Link>
                <small>{formatDate(payment.paid_on)} · {paymentMethodLabel(payment.method)} · {payment.invoice_reference}</small>
              </span>
              <span className="dwella-badge-row">
                {payment.reversed ? <StatusBadge color="subtle">Reversed</StatusBadge> : null}
                <strong>{formatMoney(payment.amount)}</strong>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function PortalPayments() {
  // /billing/invoices/<id> opens that invoice; /billing?invoice=<id> too.
  const { id: routeInvoice } = useParams();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const view = params.get("view") || "unpaid";
  const openId = routeInvoice || params.get("invoice");
  const query = usePortalInvoices({ page_size: 50, ...(view === "unpaid" ? { unpaid: "true" } : {}) }, { placeholderData: (previous) => previous });
  const setParam = (name, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    setParams(next, { replace: true });
  };
  const close = () => (routeInvoice ? navigate("/billing") : setParam("invoice", null));
  return (
    <PortalState query={query} label="your invoices">
      {(data) => {
        const invoices = data.results || [];
        return (
          <div className="dwella-portal">
            <div className="dwella-page-toolbar">
              <SegmentedFilter label="Filter invoices" options={views} value={view} onChange={(value) => setParam("view", value === "unpaid" ? null : value)} />
            </div>
            {invoices.length ? (
              <div className="dwella-table-card">
                <table className="dwella-table dwella-portal-table">
                  <thead>
                    <tr>
                      <th scope="col">Invoice</th>
                      <th scope="col">Period</th>
                      <th scope="col">Due</th>
                      <th scope="col" className="is-numeric">Balance</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((invoice) => (
                      <tr
                        key={invoice.id}
                        tabIndex={0}
                        onClick={() => setParam("invoice", invoice.id)}
                        onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && (event.preventDefault(), setParam("invoice", invoice.id))}
                      >
                        <td><strong>{invoice.reference}</strong></td>
                        <td>{periodLabel(invoice.period_start)}</td>
                        <td>{formatDate(invoice.due_date)}</td>
                        <td className="is-numeric">{formatMoney(invoice.balance)}</td>
                        <td><StatusBadge {...invoiceBadgeProps(invoice)} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="dwella-muted-copy">{view === "unpaid" ? "Nothing to pay right now." : "No invoices yet."}</p>
            )}
            <PaymentsList />
            {openId ? <InvoiceDrawer id={openId} onClose={close} /> : null}
          </div>
        );
      }}
    </PortalState>
  );
}
