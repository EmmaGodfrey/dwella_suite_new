import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Dropdown, Input, Option } from "@fluentui/react-components";
import {
  Add20Regular,
  Board20Regular,
  Location16Regular,
  PeopleTeam20Regular,
  Search20Regular,
  TextBulletListLtr20Regular,
  Wrench24Regular,
} from "@fluentui/react-icons";

import {
  useCurrentUserQuery,
  useMaintenanceRequestsQuery,
  useMaintenanceSummaryQuery,
  usePropertiesQuery,
  useVendorsQuery,
} from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, PageActions, StatusBadge } from "../../shared/components";
import { formatMoney, initials } from "../../shared/format";
import {
  ageLabel,
  boardColumns,
  dayLabel,
  formatVisit,
  locationLabel,
  priorities,
  priorityBadgeProps,
  sourceLabel,
  statusBadgeProps,
} from "../../shared/maintenance";
import RequestDrawer from "./RequestDrawer";
import VendorsDrawer from "./VendorsDrawer";
import "../../shared/records.scss";
import "./maintenance.scss";

const VIEW_KEY = "dwella.maintenance.view";
const readView = () => {
  try {
    return localStorage.getItem(VIEW_KEY) === "list" ? "list" : "board";
  } catch {
    return "board";
  }
};

function FilterDropdown({ label, allLabel, value, options, onChange }) {
  const selected = options.find((option) => option.value === value);
  return (
    <Dropdown
      aria-label={label}
      className="dwella-maintenance-filter"
      value={selected?.label || allLabel}
      selectedOptions={[value || ""]}
      onOptionSelect={(_, data) => onChange(data.optionValue)}
    >
      <Option value="">{allLabel}</Option>
      {options.map((option) => <Option key={option.value} value={option.value}>{option.label}</Option>)}
    </Dropdown>
  );
}

function Summary() {
  const { data } = useMaintenanceSummaryQuery();
  if (!data) return null;
  return (
    <p className="dwella-maintenance-summary">
      <span><strong>{data.open}</strong> open</span>
      {data.urgent ? <span className="is-urgent"><strong>{data.urgent}</strong> urgent</span> : null}
      {data.average_days_to_close !== null ? (
        <span className="is-good"><strong>{data.average_days_to_close} days</strong> avg. time to close</span>
      ) : null}
    </p>
  );
}

const costLabel = (request) => {
  if (request.actual_cost) return formatMoney(request.actual_cost, { whole: true });
  if (request.estimated_cost) return `${formatMoney(request.estimated_cost, { whole: true })} quoted`;
  return null;
};

function RequestCard({ request, onOpen }) {
  const corner = request.status === "new" ? ageLabel(request.created_at) : costLabel(request);
  let when = "";
  if (request.status === "scheduled") when = formatVisit(request.scheduled_for);
  if (request.status === "in_progress") when = dayLabel("Started", request.started_at);
  if (request.status === "completed") when = dayLabel("Closed", request.completed_at);
  return (
    <li>
      <button type="button" className="dwella-job-card" onClick={() => onOpen(request.id)}>
        <span className="dwella-job-card-top">
          {request.status === "completed" ? <StatusBadge color="success">Closed</StatusBadge> : <StatusBadge {...priorityBadgeProps(request.priority)} />}
          {corner ? <small>{corner}</small> : null}
        </span>
        <strong className="dwella-job-card-title">{request.title}</strong>
        <span className="dwella-job-card-place"><Location16Regular />{locationLabel(request)}</span>
        <span className="dwella-job-card-foot">
          {request.vendor_name ? (
            <span className="dwella-job-vendor">
              <span className="dwella-avatar is-navy" aria-hidden="true">{initials(request.vendor_name)}</span>
              {request.vendor_name}
            </span>
          ) : (
            <span className="dwella-job-unassigned">Unassigned</span>
          )}
          <small>{request.vendor_name ? when : request.tenant_name ? `Reported by ${request.tenant_name}` : sourceLabel(request.source)}</small>
        </span>
      </button>
    </li>
  );
}

function Board({ requests, loading, onOpen }) {
  return (
    <div className="dwella-board">
      {boardColumns.map((column) => {
        const items = requests.filter((request) => request.status === column.value);
        return (
          <section key={column.value} className="dwella-board-column" aria-labelledby={`col-${column.value}`}>
            <header style={{ "--tone": column.tone }}>
              <h2 id={`col-${column.value}`}>{column.label}</h2>
              <span>{loading ? "" : items.length}</span>
            </header>
            {loading ? (
              <span className="dwella-skeleton" style={{ height: 120 }} />
            ) : items.length ? (
              <ul>{items.map((request) => <RequestCard key={request.id} request={request} onOpen={onOpen} />)}</ul>
            ) : (
              <p className="dwella-board-empty">Nothing here</p>
            )}
          </section>
        );
      })}
    </div>
  );
}

function List({ requests, loading, onOpen }) {
  return (
    <div className="dwella-table-card">
      <table className="dwella-table">
        <thead>
          <tr>
            <th scope="col">Request</th>
            <th scope="col">Where</th>
            <th scope="col">Priority</th>
            <th scope="col">Vendor</th>
            <th scope="col">Visit</th>
            <th scope="col" className="is-numeric">Cost</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr className="is-loading"><td colSpan={7}><span className="dwella-skeleton" style={{ height: 12, width: 220 }} /></td></tr>
          ) : null}
          {requests.map((request) => (
            <tr key={request.id} tabIndex={0} onClick={() => onOpen(request.id)} onKeyDown={(event) => event.key === "Enter" && onOpen(request.id)}>
              <td><strong>{request.title}</strong><span className="dwella-cell-note">{request.reference} · {ageLabel(request.created_at)}</span></td>
              <td>{locationLabel(request)}</td>
              <td><StatusBadge {...priorityBadgeProps(request.priority)} /></td>
              <td>{request.vendor_name || <span className="dwella-job-unassigned">Unassigned</span>}</td>
              <td>{formatVisit(request.scheduled_for)}</td>
              <td className="is-numeric">{costLabel(request) || "—"}</td>
              <td><StatusBadge {...statusBadgeProps(request.status)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Maintenance() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const openFilter = searchParams.get("open") === "true" ? "true" : "";
  const setOpenFilter = (value) => setSearchParams((current) => {
    const next = new URLSearchParams(current);
    if (value) next.set("open", value);
    else next.delete("open");
    return next;
  });
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const [view, setView] = useState(readView);
  const [filters, setFilters] = useState({ property: "", priority: "", vendor: "" });
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [drawer, setDrawer] = useState(null); // null | "request" | "vendors"

  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(search), 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const changeView = (next) => {
    setView(next);
    try {
      localStorage.setItem(VIEW_KEY, next);
    } catch {
      // Remembering the view is a convenience only.
    }
  };

  const propertiesQuery = usePropertiesQuery({ page_size: 200, ordering: "name" }, { staleTime: 60_000 });
  const vendorsQuery = useVendorsQuery({ page_size: 200, is_active: "true" }, { staleTime: 60_000 });
  // The board shows open work plus the past week's finished jobs; the list
  // shows every request, newest first.
  const listQuery = useMaintenanceRequestsQuery({
    ...filters,
    ...(openFilter ? { open: openFilter } : {}),
    search: debounced,
    ...(view === "board" ? { board: "true", page_size: 200 } : { page_size: 100 }),
    ordering: "-created_at",
  });
  const requests = listQuery.data?.results || [];
  const filtered = Boolean(filters.property || filters.priority || filters.vendor || debounced || openFilter);
  const open = (id) => navigate(`/maintenance/${id}`);
  const setFilter = (key) => (value) => setFilters((current) => ({ ...current, [key]: value }));

  return (
    <div className="dwella-maintenance-page">
      {canManage ? (
        <PageActions>
          <Button icon={<PeopleTeam20Regular />} onClick={() => setDrawer("vendors")}>Vendors</Button>
          <Button appearance="primary" icon={<Add20Regular />} onClick={() => setDrawer("request")}>New request</Button>
        </PageActions>
      ) : null}

      <div className="dwella-page-toolbar">
        <div className="dwella-segmented" role="group" aria-label="Layout">
          {[
            { value: "board", label: "Board", icon: <Board20Regular /> },
            { value: "list", label: "List", icon: <TextBulletListLtr20Regular /> },
          ].map((option) => (
            <button key={option.value} type="button" aria-pressed={view === option.value} className={view === option.value ? "is-selected" : undefined} onClick={() => changeView(option.value)}>
              {option.icon}{option.label}
            </button>
          ))}
        </div>
        <FilterDropdown
          label="Property"
          allLabel="All properties"
          value={filters.property}
          options={(propertiesQuery.data?.results || []).map((item) => ({ value: item.id, label: item.name }))}
          onChange={setFilter("property")}
        />
        <FilterDropdown
          label="Work status"
          allLabel="All requests"
          value={openFilter}
          options={[{ value: "true", label: "Open requests" }]}
          onChange={setOpenFilter}
        />
        <FilterDropdown label="Priority" allLabel="Any priority" value={filters.priority} options={priorities} onChange={setFilter("priority")} />
        <FilterDropdown
          label="Vendor"
          allLabel="Any vendor"
          value={filters.vendor}
          options={(vendorsQuery.data?.results || []).map((item) => ({ value: item.id, label: item.name }))}
          onChange={setFilter("vendor")}
        />
        <Input
          className="dwella-toolbar-search"
          aria-label="Search requests"
          contentBefore={<Search20Regular />}
          placeholder="Search request, unit, tenant"
          value={search}
          onChange={(_, data) => setSearch(data.value)}
        />
        <Summary />
      </div>

      {listQuery.isError ? (
        <div className="dwella-alert danger">
          Unable to load requests. <Button size="small" onClick={() => listQuery.refetch()}>Retry</Button>
        </div>
      ) : !listQuery.isLoading && !requests.length && (filtered || view === "list") ? (
        <EmptyState
          icon={<Wrench24Regular />}
          title={filtered ? "No matching requests" : "No requests yet"}
          description={filtered ? "Try another search or filter." : "Log a repair to track it from report to done."}
          actionLabel={filtered ? "Clear filters" : canManage ? "New request" : undefined}
          onAction={filtered ? () => { setFilters({ property: "", priority: "", vendor: "" }); setSearch(""); setOpenFilter(""); } : () => setDrawer("request")}
        />
      ) : view === "board" ? (
        <Board requests={requests} loading={listQuery.isLoading} onOpen={open} />
      ) : (
        <List requests={requests} loading={listQuery.isLoading} onOpen={open} />
      )}

      {drawer === "request" ? <RequestDrawer onClose={() => setDrawer(null)} onSaved={(request) => open(request.id)} /> : null}
      {drawer === "vendors" ? <VendorsDrawer onClose={() => setDrawer(null)} /> : null}
    </div>
  );
}
