import React from "react";
import "./dashboard.scss";
import { useNavigate } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import {
  ArrowRight20Regular,
  Calendar20Regular,
  ChevronRight20Regular,
  DocumentText24Regular,
  DoorArrowLeft20Regular,
  Home24Regular,
  Payment24Regular,
  Warning20Regular,
  Wrench24Regular,
} from "@fluentui/react-icons";

import {
  useBillingSummaryQuery,
  useCurrentUserQuery,
  useDashboardSummaryQuery,
  useInvoicesQuery,
  useLeasesQuery,
  usePaymentsQuery,
} from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { paymentMethodLabel } from "../../shared/billing";
import { daysUntil, formatDate, toIsoDate } from "../../shared/format";

const money = new Intl.NumberFormat("en-ZM", {
  style: "currency",
  currency: "ZMW",
  maximumFractionDigits: 0,
});
const number = new Intl.NumberFormat("en-ZM");
const formatMoney = (value) => money.format(Number(value || 0));
const formatNumber = (value) => number.format(Number(value || 0));
const axisMoney = (value) =>
  value >= 1_000_000 ? `K${+(value / 1_000_000).toFixed(1)}m` : value >= 1000 ? `K${+(value / 1000).toFixed(1)}k` : `K${value}`;
const unitCount = (value) => `${formatNumber(value)} ${Number(value) === 1 ? "unit" : "units"}`;
const monthName = (iso, style = "long") => {
  const [year, month] = iso.split("-").map(Number);
  const name = new Date(year, month - 1, 1).toLocaleDateString("en-GB", { month: style === "short" ? "long" : style });
  return style === "short" ? name.slice(0, 3) : name;
};
const listJoin = (items) =>
  items.length > 1 ? `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}` : items[0] || "";
const emptySummary = {
  access: null,
  organization: null,
  platform: null,
  properties: { total: 0, managed: 0, by_status: [], by_type: [] },
  units: { total: 0, occupied: 0, vacant: 0, occupancy_rate: 0, by_status: [] },
  finance: {
    monthly_rent_roll: 0,
    occupied_rent_roll: 0,
    vacancy_loss: 0,
    average_unit_rent: 0,
  },
  portfolio: { towns_count: 0, towns: [], average_units_per_property: 0 },
  recent_properties: [],
  top_units: [],
};

function TenantDashboard({ navigate }) {
  return (
    <div className="dwella-screen dwella-dashboard-v2 dwella-tenant-dashboard">
      <header className="dwella-dashboard-intro">
        <div>
          <span className="dwella-dashboard-kicker">Tenant workspace</span>
          <h1>Your home at a glance</h1>
        </div>
      </header>
      <section className="dwella-tenant-status">
        <Home24Regular />
        <div>
          <strong>No active tenancy linked</strong>
          <p>Your lease and balance will appear after a landlord links your account to a unit.</p>
        </div>
      </section>
      <div className="dwella-tenant-actions">
        <button type="button" onClick={() => navigate("/leases")}>
          <DocumentText24Regular />
          <strong>My lease</strong>
          <span>Terms, documents, and renewal details</span>
        </button>
        <button type="button" onClick={() => navigate("/billing")}>
          <Payment24Regular />
          <strong>Payments</strong>
          <span>Charges, receipts, and payment history</span>
        </button>
        <button type="button" onClick={() => navigate("/maintenance")}>
          <Wrench24Regular />
          <strong>Maintenance</strong>
          <span>Report and follow up on an issue</span>
        </button>
      </div>
    </div>
  );
}

// A figure reserves its own height while loading, so the band does not change
// size when the request lands.
function Figure({ loading, children, width = "5ch" }) {
  if (!loading) return children;
  return (
    <span className="dwella-skeleton dwella-figure-skeleton" style={{ width }} aria-hidden="true" />
  );
}

function PulseStat({ label, value, note, loading }) {
  return (
    <div className="dwella-pulse-stat">
      <dt>{label}</dt>
      <dd>
        <strong>
          <Figure loading={loading} width="3ch">
            {value}
          </Figure>
        </strong>
        {note ? <small>{note}</small> : null}
      </dd>
    </div>
  );
}

function SectionHeading({ title, note, action }) {
  return (
    <header className="dwella-dashboard-section-heading">
      <div>
        <h3>{title}</h3>
        {note ? <p>{note}</p> : null}
      </div>
      {action}
    </header>
  );
}

function LinkButton({ children, onClick }) {
  return (
    <Button
      appearance="transparent"
      className="dwella-link-button"
      icon={<ArrowRight20Regular />}
      iconPosition="after"
      onClick={onClick}
    >
      {children}
    </Button>
  );
}

// Collected rent leads once anything is billed this month. Before the first
// invoice run the band falls back to what the portfolio could earn, split by
// occupied units and vacancy.
function MonthAtAGlance({ data, billing, loading, isPlatformAdmin }) {
  const today = new Date();
  const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  const daysLeft = monthEnd.getDate() - today.getDate();
  const month = today.toLocaleDateString("en-GB", { month: "long" });
  const split = billing?.month_breakdown;
  const billed = Number(split?.billed || 0);
  const hasBilling = Boolean(split) && billed > 0;
  const occupancy = Number(data.units.occupancy_rate || 0);
  const parts = hasBilling
    ? [
        { key: "paid", value: Number(split.paid), label: `${Math.round((Number(split.paid) / billed) * 100)}% collected` },
        { key: "due", value: Number(split.not_yet_due), label: `${formatMoney(split.not_yet_due)} not yet due` },
        { key: "overdue", value: Number(split.overdue), label: `${formatMoney(split.overdue)} overdue` },
      ]
    : [
        { key: "paid", value: Number(data.finance.occupied_rent_roll), label: `${formatMoney(data.finance.occupied_rent_roll)} from occupied units` },
        {
          key: "due",
          value: Number(data.finance.vacancy_loss),
          label: `${formatMoney(data.finance.vacancy_loss)} lost to vacancy · ${unitCount(data.units.vacant)} vacant`,
        },
      ];

  return (
    <section className="dwella-portfolio-pulse" aria-label="Month at a glance">
      <div className="dwella-pulse-lead">
        <span>
          {hasBilling ? `Collected so far in ${month}` : isPlatformAdmin ? "Managed rent roll per month" : "Monthly rent roll"}
        </span>
        <div className="dwella-pulse-figure">
          <strong>
            <Figure loading={loading} width="7ch">
              {formatMoney(hasBilling ? split.paid : data.finance.monthly_rent_roll)}
            </Figure>
          </strong>
          <small>{hasBilling ? `of ${formatMoney(billed)} billed` : `across ${unitCount(data.units.total)}`}</small>
        </div>
        <div className="dwella-pulse-bar" role="img" aria-label={parts.map((part) => part.label).join(", ")}>
          {parts.map((part) => (
            <span key={part.key} className={`is-${part.key}`} style={{ flexGrow: part.value }} />
          ))}
        </div>
        <ul className="dwella-pulse-legend">
          {parts
            .filter((part) => part.key !== "overdue" || part.value > 0)
            .map((part) => (
              <li key={part.key} className={`is-${part.key}`}>
                {part.label}
              </li>
            ))}
        </ul>
      </div>

      <dl className="dwella-pulse-stats">
        <PulseStat
          label="Occupancy"
          loading={loading}
          value={`${occupancy}%`}
          note={`${formatNumber(data.units.occupied)} of ${unitCount(data.units.total)}`}
        />
        {isPlatformAdmin ? (
          <>
            <PulseStat label="Organizations" loading={loading} value={formatNumber(data.platform?.organizations)} />
            <PulseStat label="Landlords" loading={loading} value={formatNumber(data.platform?.landlords)} />
          </>
        ) : (
          <>
            <PulseStat label="Rent roll" loading={loading} value={formatMoney(data.finance.monthly_rent_roll)} note="per month" />
            <PulseStat
              label="Days left"
              loading={loading}
              value={formatNumber(daysLeft)}
              note={`until ${monthEnd.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`}
            />
          </>
        )}
      </dl>
    </section>
  );
}

// Billed is drawn behind collected, so the grey cap above each green bar is
// what is still owed for that month.
function CollectionChart({ history, loading }) {
  const peak = Math.max(0, ...history.map((row) => Number(row.billed)));
  // Four equal steps of 1, 2, 2.5 or 5 × 10ⁿ, so the axis reads K50k, K100k…
  const rawStep = peak / 4;
  const magnitude = peak > 0 ? Math.pow(10, Math.floor(Math.log10(rawStep))) : 1;
  const step = peak > 0 ? [1, 2, 2.5, 5, 10].map((n) => n * magnitude).find((n) => n >= rawStep) : 1;
  const top = step * 4;
  const ticks = [4, 3, 2, 1, 0].map((index) => step * index);
  const height = (value) => `${(Number(value) / top) * 100}%`;
  const empty = !loading && peak === 0;

  return (
    <section className="dwella-dashboard-card dwella-collection-card">
      <SectionHeading
        title="Rent collection"
        note="Last 6 months · billed vs collected"
        action={
          <ul className="dwella-chart-legend" aria-hidden="true">
            <li className="is-billed">Billed</li>
            <li className="is-collected">Collected</li>
          </ul>
        }
      />
      <div className="dwella-collection-plot">
        <div className="dwella-collection-axis" aria-hidden="true">
          {ticks.map((tick) => (
            <span key={tick}>{peak > 0 ? axisMoney(tick) : ""}</span>
          ))}
        </div>
        <div className="dwella-collection-bars">
          <div className="dwella-collection-grid" aria-hidden="true">
            {ticks.map((tick) => (
              <i key={tick} />
            ))}
          </div>
          {history.map((row, index) => (
            <div
              key={row.month}
              className={`dwella-collection-month${index === history.length - 1 ? " is-current" : ""}`}
              role="img"
              aria-label={`${monthName(row.month)}: ${formatMoney(row.billed)} billed, ${formatMoney(row.collected)} collected`}
            >
              <div className="dwella-collection-stack">
                <span className="is-billed" style={{ height: height(row.billed) }} />
                <span className="is-collected" style={{ height: height(row.collected) }} />
              </div>
              <small>{monthName(row.month, "short")}</small>
            </div>
          ))}
          {empty ? (
            <p className="dwella-collection-empty">Collection history builds up as you bill rent each month.</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function AttentionItem({ tone, icon, title, detail, onClick }) {
  return (
    <li>
      <button type="button" className="dwella-attention-item" onClick={onClick}>
        <span className={`dwella-attention-chip is-${tone}`}>{icon}</span>
        <span className="dwella-attention-copy">
          <strong>{title}</strong>
          <small>{detail}</small>
        </span>
        <ChevronRight20Regular className="dwella-attention-arrow" />
      </button>
    </li>
  );
}

// Only decisions the product can back with real records: overdue invoices,
// leases running out within a month, and empty units.
function NeedsAttention({ data, navigate, enabled }) {
  const in30 = new Date();
  in30.setDate(in30.getDate() + 30);
  const overdueQuery = useInvoicesQuery(
    { overdue: "true", ordering: "due_date", page_size: 3 },
    { enabled, staleTime: 30_000 },
  );
  const endingQuery = useLeasesQuery(
    { status: "active", ends_before: toIsoDate(in30), ordering: "end_date", page_size: 2 },
    { enabled, staleTime: 60_000 },
  );
  const overdue = overdueQuery.data?.results || [];
  const ending = endingQuery.data?.results || [];
  const overdueCount = overdueQuery.data?.pagination?.count || 0;
  const vacant = Number(data.units.vacant || 0);
  const loading = !enabled || overdueQuery.isLoading || endingQuery.isLoading;
  const count = overdueCount + (endingQuery.data?.pagination?.count || 0) + (vacant ? 1 : 0);

  return (
    <section className="dwella-dashboard-card dwella-attention-card">
      <SectionHeading
        title="Needs attention"
        note={loading ? "Checking your portfolio…" : count ? `${count} ${count === 1 ? "item needs" : "items need"} a decision` : "You're all caught up"}
      />
      {loading ? (
        <ul className="dwella-attention-list" aria-hidden="true">
          {[0, 1, 2].map((row) => (
            <li key={row}>
              <span className="dwella-attention-item is-loading">
                <span className="dwella-skeleton dwella-attention-chip" />
                <span className="dwella-attention-copy">
                  <span className="dwella-skeleton" style={{ height: 12, width: "62%" }} />
                  <span className="dwella-skeleton" style={{ height: 10, width: "44%" }} />
                </span>
              </span>
            </li>
          ))}
        </ul>
      ) : count ? (
        <ul className="dwella-attention-list">
          {overdue.map((invoice) => (
            <AttentionItem
              key={invoice.id}
              tone="danger"
              icon={<Warning20Regular />}
              title={`Rent overdue${invoice.unit_name ? ` — ${invoice.unit_name}` : ""}`}
              detail={`${invoice.tenant_name} · ${formatMoney(invoice.balance)} · ${invoice.days_overdue} ${invoice.days_overdue === 1 ? "day" : "days"} late`}
              onClick={() => navigate(`/billing/invoices/${invoice.id}`)}
            />
          ))}
          {ending.map((lease) => {
            const days = daysUntil(lease.end_date);
            return (
              <AttentionItem
                key={lease.id}
                tone="warning"
                icon={<Calendar20Regular />}
                title={days <= 0 ? "Lease ends today" : `Lease ends in ${days} ${days === 1 ? "day" : "days"}`}
                detail={`${lease.tenant_name} · ${lease.property_name}, ${lease.unit_name}`}
                onClick={() => navigate(`/leases/${lease.id}`)}
              />
            );
          })}
          {vacant ? (
            <AttentionItem
              tone="info"
              icon={<DoorArrowLeft20Regular />}
              title={`${unitCount(vacant)} empty`}
              detail={`${formatMoney(data.finance.vacancy_loss)} a month not being earned`}
              onClick={() => navigate("/properties")}
            />
          ) : null}
        </ul>
      ) : (
        <p className="dwella-board-empty">No overdue rent, leases ending soon or empty units.</p>
      )}
      {overdueCount > overdue.length ? (
        <LinkButton onClick={() => navigate("/billing?view=overdue")}>All {overdueCount} overdue invoices</LinkButton>
      ) : null}
    </section>
  );
}

const unitStatusOrder = ["occupied", "vacant", "reserved", "maintenance"];

// How the units sit today. It reads the same for one block of 60 flats as for
// twelve houses, which a list of properties does not.
function UnitStatusCard({ data, loading, navigate }) {
  const total = Number(data.units.total || 0);
  const rows = unitStatusOrder
    .map((key) => (data.units.by_status || []).find((row) => row.key === key))
    .filter(Boolean);
  return (
    <section className="dwella-dashboard-card dwella-units-card">
      <SectionHeading
        title="Units"
        note={loading ? "Counting units…" : total ? `${unitCount(total)} · ${data.units.occupancy_rate}% occupied` : "No units yet"}
      />
      <div
        className="dwella-unit-split"
        role="img"
        aria-label={rows.map((row) => `${row.count} ${row.label.toLowerCase()}`).join(", ")}
      >
        {total
          ? rows.map((row) => <span key={row.key} className={`is-${row.key}`} style={{ flexGrow: row.count }} />)
          : null}
      </div>
      <dl className="dwella-unit-status-list">
        {rows.map((row) => (
          <div key={row.key} className={`is-${row.key}`}>
            <dt>{row.label}</dt>
            <dd>
              <strong>
                <Figure loading={loading} width="2ch">
                  {formatNumber(row.count)}
                </Figure>
              </strong>
              <small>{loading ? "" : `${row.percentage}%`}</small>
            </dd>
          </div>
        ))}
      </dl>
      <LinkButton onClick={() => navigate("/properties")}>View properties</LinkButton>
    </section>
  );
}

function RecentPayments({ navigate, enabled }) {
  const paymentsQuery = usePaymentsQuery({ ordering: "-paid_on", page_size: 5, reversed: false }, { enabled, staleTime: 30_000 });
  const payments = paymentsQuery.data?.results || [];
  const loading = !enabled || paymentsQuery.isLoading;
  return (
    <section className="dwella-dashboard-card dwella-payments-card">
      <SectionHeading
        title="Recent payments"
        note="Latest receipts recorded against rent"
        action={<LinkButton onClick={() => navigate("/billing")}>Go to billing</LinkButton>}
      />
      {loading ? (
        <ul className="dwella-payment-list" aria-hidden="true">
          {[0, 1, 2, 3].map((row) => (
            <li key={row}>
              <span className="dwella-payment-row is-loading">
                <span className="dwella-attention-copy">
                  <span className="dwella-skeleton" style={{ height: 12, width: "40%" }} />
                  <span className="dwella-skeleton" style={{ height: 10, width: "28%" }} />
                </span>
              </span>
            </li>
          ))}
        </ul>
      ) : payments.length ? (
        <ul className="dwella-payment-list">
          {payments.map((payment) => (
            <li key={payment.id}>
              <button type="button" className="dwella-payment-row" onClick={() => navigate(`/billing/invoices/${payment.invoice_id}`)}>
                <span className="dwella-attention-copy">
                  <strong>{payment.tenant_name}</strong>
                  <small>
                    {[payment.receipt_number, payment.invoice_reference, paymentMethodLabel(payment.method)].filter(Boolean).join(" · ")}
                  </small>
                </span>
                <span className="dwella-payment-amount">
                  <strong>{formatMoney(payment.amount)}</strong>
                  <small>{formatDate(payment.paid_on)}</small>
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="dwella-board-empty">No payments recorded yet. Receipts appear here as tenants pay.</p>
      )}
    </section>
  );
}

const lastSixMonths = () => {
  const today = new Date();
  return Array.from({ length: 6 }, (_, index) => ({
    month: toIsoDate(new Date(today.getFullYear(), today.getMonth() - 5 + index, 1)),
    billed: 0,
    collected: 0,
  }));
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const access = getUserAccess(user);
  const isPlatformAdmin = access.persona === "platform_admin" && !access.acting_workspace;
  const isTenant = access.persona === "tenant";
  const enabled = Boolean(user) && !isTenant;
  const { data = emptySummary, error, isLoading } = useDashboardSummaryQuery({ enabled });
  const billingQuery = useBillingSummaryQuery({ enabled });

  if (isTenant) return <TenantDashboard navigate={navigate} />;
  const organizationName =
    data.organization?.display_name ||
    data.organization?.name ||
    "No organization selected";
  const towns = data.portfolio.towns || [];
  const townList = towns.length > 3 ? [...towns.slice(0, 3), `${towns.length - 3} more`] : towns;
  const subtitle = [
    `Portfolio health for ${new Date().toLocaleDateString("en-GB", { month: "long", year: "numeric" })}`,
    data.properties.total
      ? `${formatNumber(data.properties.total)} ${data.properties.total === 1 ? "property" : "properties"}${townList.length ? ` across ${listJoin(townList)}` : ""}`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="dwella-screen dwella-dashboard-v2">
      {error ? (
        <div className="dwella-alert danger" role="alert">
          Unable to load dashboard data: {error.message}
        </div>
      ) : null}

      {/* The topbar already names this page, so the intro carries the one thing
          it cannot: which organization the figures below belong to. */}
      <header className="dwella-dashboard-intro">
        <div>
          {isPlatformAdmin ? <span className="dwella-dashboard-kicker">Platform oversight</span> : null}
          <h1>{isPlatformAdmin ? "Landlord portfolios" : organizationName}</h1>
          <p>{isLoading ? " " : subtitle}</p>
        </div>
      </header>

      <MonthAtAGlance
        data={data}
        billing={billingQuery.data}
        loading={isLoading || billingQuery.isLoading}
        isPlatformAdmin={isPlatformAdmin}
      />

      <div className="dwella-dashboard-row">
        <CollectionChart history={billingQuery.data?.history || lastSixMonths()} loading={billingQuery.isLoading} />
        <NeedsAttention data={data} navigate={navigate} enabled={enabled && !isLoading} />
      </div>

      <div className="dwella-dashboard-row is-top-aligned">
        <RecentPayments navigate={navigate} enabled={enabled} />
        <UnitStatusCard data={data} loading={isLoading} navigate={navigate} />
      </div>
    </div>
  );
};

export default Dashboard;
