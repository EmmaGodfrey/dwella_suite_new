import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  OverlayDrawer,
  Select,
  Tab,
  TabList,
} from "@fluentui/react-components";
import { Dismiss20Regular, Search20Regular } from "@fluentui/react-icons";
import {
  usePaymentRecord,
  usePlatformTransactions,
} from "../../Services/payments";
import { useSettingsResource } from "../../Services/settings";
import { StatusBadge } from "../../shared/components";
import { useRestoreFocus } from "../../shared/components/FormFlow";
import { AdminHeader, AdminState, AdminTable, when } from "./AdminUI";
import { SettingsRow, SettingsSection } from "../Settings";
import "./transactions.scss";

const labels = {
  pending: "Processing",
  successful: "Delivered",
  submitting: "Submitting",
  queued: "Queued",
  failed: "Failed",
  review: "Needs reconciliation",
  expired: "Expired",
};
const currency = (value, code = "ZMW") =>
  value === null || value === undefined
    ? "Unknown"
    : new Intl.NumberFormat("en-ZM", {
        style: "currency",
        currency: code,
      }).format(Number(value));
function State({ value, collection = false }) {
  const label =
    collection && value === "successful"
      ? "Paid"
      : collection && value === "pending"
        ? "Awaiting payment"
        : labels[value] || value?.replaceAll("_", " ") || "Not created";
  const color =
    value === "successful"
      ? "success"
      : ["failed", "review"].includes(value)
        ? "danger"
        : ["pending", "submitting", "queued"].includes(value)
          ? "warning"
          : "subtle";
  return <StatusBadge color={color}>{label}</StatusBadge>;
}

function GatewayBody({ id }) {
  const query = usePaymentRecord(id ? `exchanges/${id}/` : "");
  const [tab, setTab] = useState("response");
  return (
    <AdminState query={query}>
      {query.data && (
        <>
          <TabList
            aria-label="Gateway payload"
            selectedValue={tab}
            onTabSelect={(_, d) => setTab(d.value)}
          >
            <Tab value="request">Request</Tab>
            <Tab value="response">Response</Tab>
          </TabList>
          <pre
            className="gateway-json"
            tabIndex={0}
            aria-label={`Saved gateway ${tab}`}
          >
            {JSON.stringify(query.data[tab] ?? null, null, 2)}
          </pre>
        </>
      )}
    </AdminState>
  );
}

function Exchanges({ id }) {
  const [page, setPage] = useState(1);
  const [opened, setOpened] = useState(null);
  const query = usePaymentRecord(
    `collections/${id}/exchanges/?page=${page}&page_size=10`,
  );
  return (
    <section className="gateway-exchanges">
      <h3>Gateway exchanges</h3>
      <p>
        Saved responses, newest first. Opening evidence is recorded in the audit
        log.
      </p>
      <AdminState query={query}>
        {!query.data?.results?.length ? (
          <p>No gateway exchanges recorded.</p>
        ) : (
          query.data.results.map((row) => (
            <article key={row.id} className="gateway-exchange">
              <header>
                <strong>{row.operation}</strong>
                <span>{when(row.created_at)}</span>
                <StatusBadge color="subtle">
                  HTTP {row.http_status ?? "Unknown"}
                </StatusBadge>
              </header>
              {row.error && (
                <p role="status">{row.error.replaceAll("_", " ")}</p>
              )}
              <Button
                appearance="subtle"
                onClick={() => setOpened(opened === row.id ? null : row.id)}
              >
                {opened === row.id ? "Hide response" : "View response"}
              </Button>
              {opened === row.id && <GatewayBody id={row.id} />}
            </article>
          ))
        )}
        {query.data?.pagination && (
          <div className="dwella-table-pager">
            <Button
              disabled={!query.data.pagination.previous}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              disabled={!query.data.pagination.next}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </AdminState>
    </section>
  );
}

function TransactionDrawer({ selection, onClose }) {
  useRestoreFocus();
  const ledger = selection.kind === "ledger";
  const query = usePaymentRecord(ledger ? "" : `collections/${selection.id}/`);
  const row = query.data;
  return (
    <OverlayDrawer
      open
      position="end"
      size="medium"
      className="dwella-drawer transaction-drawer"
      onOpenChange={(_, d) => !d.open && onClose()}
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <Button
              aria-label="Close transaction details"
              appearance="subtle"
              icon={<Dismiss20Regular />}
              onClick={onClose}
            />
          }
        >
          {ledger ? "Gateway record" : "Transaction details"}
        </DrawerHeaderTitle>
      </DrawerHeader>
      <DrawerBody>
        {ledger ? (
          <>
            <p>
              Saved provider evidence. An imported record may have no linked
              Dwella invoice.
            </p>
            <GatewayBody id={selection.id} />
          </>
        ) : (
          <AdminState query={query}>
            {row && (
              <>
                <p className="transaction-reference">
                  {row.reference}
                  <br />
                  {row.invoice_reference} · {row.workspace}
                </p>
                <SettingsSection title="Payment summary">
                  <SettingsRow label="Environment">
                    <StatusBadge color="informative">
                      {row.environment}
                    </StatusBadge>
                  </SettingsRow>
                  <SettingsRow label="Collection">
                    <State value={row.status} collection />
                  </SettingsRow>
                  <SettingsRow label="Landlord payout">
                    <State value={row.payout?.status} />
                  </SettingsRow>
                  {[
                    ["Collected from tenant", row.amount],
                    ["Collection fee", row.fee],
                    ["Settled amount", row.settled_amount],
                    ["Payout amount", row.payout?.amount],
                    ["Payout fee", row.payout?.fee],
                  ].map(([label, value]) => (
                    <SettingsRow key={label} label={label}>
                      {currency(value, row.currency)}
                    </SettingsRow>
                  ))}
                  <SettingsRow label="Settlement confirmed">
                    {row.settled ? "Yes" : "No"}
                  </SettingsRow>
                  <SettingsRow label="Fee payer">Unknown</SettingsRow>
                  {row.destination && (
                    <SettingsRow label="Receiving account">
                      {row.destination.account_name} ·{" "}
                      {row.destination.operator} · {row.destination.phone}
                    </SettingsRow>
                  )}
                </SettingsSection>
                {(row.issue || row.payout?.issue) && (
                  <p className="dwella-alert" role="status">
                    {[row.issue, row.payout?.issue]
                      .filter(Boolean)
                      .map((v) => v.replaceAll("_", " "))
                      .join(" · ")}
                  </p>
                )}
                <p className="settings-note">
                  HTTP acceptance does not confirm payout delivery. The gateway
                  must confirm the final state.
                </p>
                <Exchanges id={row.id} />
              </>
            )}
          </AdminState>
        )}
      </DrawerBody>
      <DrawerFooter>
        <Button onClick={onClose}>Close</Button>
      </DrawerFooter>
    </OverlayDrawer>
  );
}

function Balance() {
  const query = useSettingsResource("balance");
  return (
    <AdminState query={query}>
      {query.data && (
        <SettingsSection
          title="Latest balance comparison"
          note={`${query.data.environment || "Environment unknown"} · ${query.data.checked_at ? `Last checked ${when(query.data.checked_at)}` : "No saved comparison time."}`}
          actions={
            <Button onClick={() => query.refetch()} disabled={query.isFetching}>
              Refresh saved balance
            </Button>
          }
        >
          {query.data.status === "not_synced" ? (
            <p>Provider transactions have not been synced yet.</p>
          ) : (
            <>
              <StatusBadge
                color={query.data.status === "matched" ? "success" : "warning"}
              >
                {query.data.status}
              </StatusBadge>
              <div className="transaction-balance">
                {[
                  ["Available", "available_balance"],
                  ["Expected", "expected_balance"],
                  ["Difference", "difference"],
                  ["Held for landlords", "held_for_landlords"],
                  ["Payout fees recorded", "payout_fees_total"],
                ].map(([label, key]) => (
                  <div key={key}>
                    <small>{label}</small>
                    <strong>{currency(query.data[key])}</strong>
                  </div>
                ))}
              </div>
            </>
          )}
        </SettingsSection>
      )}
    </AdminState>
  );
}

export default function Transactions() {
  const [params, setParams] = useSearchParams();
  const kind = ["collections", "payouts", "ledger"].includes(params.get("view"))
    ? params.get("view")
    : "collections";
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({
    page: 1,
    search: "",
    status: "",
    payout_status: "",
    environment: "",
    from_date: "",
    until_date: "",
  });
  const [selection, setSelection] = useState(null);
  useEffect(() => {
    const timer = setTimeout(
      () =>
        setFilters((v) =>
          v.search === search ? v : { ...v, search, page: 1 },
        ),
      300,
    );
    return () => clearTimeout(timer);
  }, [search]);
  const query = usePlatformTransactions({ ...filters, kind, page_size: 25 });
  const change = (key, value) =>
    setFilters((v) => ({ ...v, [key]: value, page: 1 }));
  const open = (row) =>
    setSelection({
      kind,
      id:
        kind === "ledger"
          ? row.exchange_id
          : kind === "payouts"
            ? row.collection_id
            : row.id,
    });
  const common = [
    {
      key: "amount",
      label: "Amount",
      render: (r) => currency(r.amount, r.currency),
    },
    {
      key: "environment",
      label: "Environment",
      render: (r) => (
        <StatusBadge color="informative">{r.environment}</StatusBadge>
      ),
    },
  ];
  const columns =
    kind === "ledger"
      ? [
          { key: "provider_id", label: "Provider ID" },
          { key: "kind", label: "Kind" },
          ...common,
          {
            key: "posted_at",
            label: "Posted",
            render: (r) => when(r.posted_at),
          },
          {
            key: "linked",
            label: "Dwella record",
            render: (r) =>
              r.collection_id || r.payout_collection_id ? (
                <Button
                  appearance="subtle"
                  onClick={() =>
                    setSelection({
                      kind: "collections",
                      id: r.collection_id || r.payout_collection_id,
                    })
                  }
                >
                  Linked transaction
                </Button>
              ) : (
                "Unlinked"
              ),
          },
        ]
      : [
          {
            key: "reference",
            label: "Reference",
            render: (r) => (
              <>
                <strong>{r.reference}</strong>
                <small>{r.invoice_reference || r.collection_reference}</small>
              </>
            ),
          },
          { key: "workspace", label: "Workspace" },
          ...common,
          {
            key: "fee",
            label: kind === "collections" ? "Collection fee" : "Payout fee",
            render: (r) => currency(r.fee, r.currency),
          },
          {
            key: "status",
            label: kind === "collections" ? "Collection" : "Payout",
            render: (r) => (
              <State value={r.status} collection={kind === "collections"} />
            ),
          },
          ...(kind === "collections"
            ? [
                {
                  key: "payout",
                  label: "Payout",
                  render: (r) => <State value={r.payout?.status} />,
                },
              ]
            : []),
          {
            key: "created_at",
            label: "Created",
            render: (r) => when(r.created_at),
          },
        ];
  columns.push({
    key: "details",
    label: "Details",
    render: (r) => (
      <Button size="small" appearance="subtle" onClick={() => open(r)}>
        {kind === "ledger" ? "Response" : "Details"}
      </Button>
    ),
  });
  return (
    <div className="admin-screen transaction-screen">
      <AdminHeader
        title="Transactions"
        description="Tenant collections, landlord payouts and saved gateway responses across all workspaces."
      />
      <TabList
        aria-label="Transaction type"
        className="settings-tabs"
        selectedValue={kind}
        onTabSelect={(_, d) => {
          setParams({ view: d.value });
          setFilters((v) => ({ ...v, status: "", payout_status: "", page: 1 }));
        }}
      >
        {[
          ["collections", "Collections"],
          ["payouts", "Payouts"],
          ["ledger", "Gateway ledger"],
        ].map(([value, label]) => (
          <Tab key={value} value={value}>
            {label}
          </Tab>
        ))}
      </TabList>
      {kind === "ledger" && <Balance />}
      <div className="transaction-filters">
        <Field label="Search">
          <Input
            contentBefore={<Search20Regular />}
            value={search}
            maxLength={150}
            placeholder={
              kind === "ledger"
                ? "Provider transaction ID"
                : "Reference, invoice or workspace"
            }
            onChange={(_, d) => setSearch(d.value)}
          />
        </Field>
        <Field label={kind === "ledger" ? "Kind" : "Status"}>
          <Select
            value={filters.status}
            onChange={(_, d) => change("status", d.value)}
          >
            <option value="">All</option>
            {(kind === "ledger"
              ? ["credit", "debit"]
              : kind === "collections"
                ? ["pending", "successful", "failed", "review", "expired"]
                : [
                    "queued",
                    "submitting",
                    "pending",
                    "successful",
                    "failed",
                    "review",
                  ]
            ).map((value) => (
              <option key={value} value={value}>
                {kind === "collections" && value === "successful"
                  ? "Paid"
                  : labels[value] || value}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Environment">
          <Select
            value={filters.environment}
            onChange={(_, d) => change("environment", d.value)}
          >
            <option value="">All</option>
            <option value="live">Live</option>
            <option value="sandbox">Sandbox</option>
          </Select>
        </Field>
        <Field label="From date">
          <Input
            type="date"
            value={filters.from_date}
            onChange={(_, d) => change("from_date", d.value)}
          />
        </Field>
        <Field label="Until date">
          <Input
            type="date"
            min={filters.from_date}
            value={filters.until_date}
            onChange={(_, d) => change("until_date", d.value)}
          />
        </Field>
      </div>
      <AdminState query={query}>
        {query.data?.results?.length ? (
          <AdminTable
            rows={query.data.results}
            columns={columns}
            pagination={query.data.pagination}
            setPage={(page) => setFilters((v) => ({ ...v, page }))}
          />
        ) : (
          <SettingsSection
            title="No transactions match these filters"
            note="Try a different reference or widen the date range."
          >
            <Button
              onClick={() => {
                setSearch("");
                setFilters({
                  page: 1,
                  search: "",
                  status: "",
                  payout_status: "",
                  environment: "",
                  from_date: "",
                  until_date: "",
                });
              }}
            >
              Clear filters
            </Button>
          </SettingsSection>
        )}
      </AdminState>
      {selection && (
        <TransactionDrawer
          key={`${selection.kind}-${selection.id}`}
          selection={selection}
          onClose={() => setSelection(null)}
        />
      )}
    </div>
  );
}
