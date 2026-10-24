import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button, Input } from "@fluentui/react-components";
import {
  Call20Regular,
  Chat20Regular,
  Edit20Regular,
  Mail20Regular,
  PersonAdd20Regular,
  People24Regular,
  Search20Regular,
} from "@fluentui/react-icons";

import { useCurrentUserQuery, useTenantQuery, useTenantsQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, SegmentedFilter, PageActions, StatusBadge } from "../../shared/components";
import { daysUntil, formatDate, formatMoney, initials } from "../../shared/format";
import { leaseBadgeProps, tenantBadgeProps, tenantStatuses } from "../../shared/tenancy";
import TenantDrawer from "./TenantDrawer";
import "../../shared/records.scss";
import "./tenants.scss";

const PAGE_SIZE = 20;
// Avatar tints rotate by name so the same tenant keeps the same colour.
const TINTS = ["navy", "green", "amber", "violet"];
const tintFor = (name) => TINTS[[...name].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % TINTS.length];

function Avatar({ name, size = "md" }) {
  return (
    <span className={`dwella-avatar is-${tintFor(name)} is-${size}`} aria-hidden="true">
      {initials(name)}
    </span>
  );
}

function TableSkeleton() {
  return [0, 1, 2, 3, 4, 5].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      <td><span className="dwella-skeleton" style={{ height: 34, width: 34, borderRadius: 17 }} /><span className="dwella-skeleton" style={{ height: 12, width: 140 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 12, width: 150 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 12, width: 80 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 12, width: 64 }} /></td>
      <td><span className="dwella-skeleton" style={{ height: 18, width: 60 }} /></td>
    </tr>
  ));
}

function TenantProfile({ tenant, canManage, onEdit }) {
  const lease = tenant.current_lease;
  const endsIn = lease ? daysUntil(lease.end_date) : null;
  const phone = tenant.phone_number;

  return (
    <aside className="dwella-tenant-profile" aria-label={`${tenant.full_name} profile`}>
      <header>
        <Avatar name={tenant.full_name} size="lg" />
        <div>
          <h2>{tenant.full_name}</h2>
          <StatusBadge {...tenantBadgeProps(tenant.status)} />
        </div>
        {canManage ? <Button appearance="subtle" icon={<Edit20Regular />} aria-label="Edit tenant" onClick={onEdit} /> : null}
      </header>

      {/* Real links: the device's own phone, SMS and mail apps. In-app
          messaging arrives with the reminders work. */}
      <div className="dwella-contact-actions">
        <Button as="a" href={`tel:${phone}`} icon={<Call20Regular />}>Call</Button>
        <Button as="a" href={`sms:${phone}`} icon={<Chat20Regular />}>SMS</Button>
        <Button as="a" href={tenant.email ? `mailto:${tenant.email}` : undefined} disabled={!tenant.email} icon={<Mail20Regular />}>Email</Button>
      </div>

      <dl className="dwella-detail-list">
        <div><dt>Phone</dt><dd>{phone}</dd></div>
        <div><dt>Email</dt><dd>{tenant.email || "—"}</dd></div>
        <div><dt>NRC / passport</dt><dd>{tenant.national_id || "—"}</dd></div>
        <div><dt>On file since</dt><dd>{formatDate(tenant.created_at)}</dd></div>
      </dl>

      <section>
        <h3>Current lease</h3>
        {lease ? (
          <>
            <dl className="dwella-detail-list">
              <div><dt>Unit</dt><dd>{lease.unit_name} · {lease.property_name}</dd></div>
              <div><dt>Term</dt><dd>{formatDate(lease.start_date)} – {formatDate(lease.end_date)}</dd></div>
              <div><dt>Monthly rent</dt><dd>{formatMoney(lease.monthly_rent)}</dd></div>
              <div><dt>Deposit</dt><dd>{formatMoney(lease.deposit_amount)}</dd></div>
              <div><dt>Status</dt><dd><StatusBadge {...leaseBadgeProps(lease.status)} /></dd></div>
            </dl>
            {lease.status === "active" && endsIn !== null && endsIn <= 60 ? (
              <p className="dwella-callout is-warning">{endsIn < 0 ? "Lease end date has passed." : `Lease ends in ${endsIn} days.`}</p>
            ) : null}
            <Button as={Link} to={`/leases/${lease.id}`} appearance="secondary">Open lease {lease.reference}</Button>
          </>
        ) : (
          <p className="dwella-muted-copy">No lease yet. {canManage ? "Create one from Leases." : ""}</p>
        )}
      </section>

      {tenant.notes ? (
        <section>
          <h3>Notes</h3>
          <p className="dwella-muted-copy">{tenant.notes}</p>
        </section>
      ) : null}
    </aside>
  );
}

export default function Tenants() {
  const [params, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  // `?search=` lets other pages (e.g. a lease) deep-link to one tenant.
  const [search, setSearch] = useState(() => params.get("search") || "");
  const [filters, setFilters] = useState(() => ({
    status: "",
    search: params.get("search") || "",
    page: 1,
    page_size: PAGE_SIZE,
    ordering: "full_name",
  }));
  const [selectedId, setSelectedId] = useState(null);
  const [drawer, setDrawer] = useState(null); // null | "add" | "edit"

  useEffect(() => {
    if (params.get("new") === "1" && canManage) {
      setDrawer("add");
      setParams({}, { replace: true });
    }
  }, [canManage, params, setParams]);

  useEffect(() => {
    const timeout = setTimeout(() => setFilters((current) => (current.search === search ? current : { ...current, search, page: 1 })), 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const listQuery = useTenantsQuery(filters, { placeholderData: (previous) => previous, staleTime: 30_000 });
  const tenants = listQuery.data?.results || [];
  const pagination = listQuery.data?.pagination;
  const activeId = selectedId && tenants.some((item) => item.id === selectedId) ? selectedId : tenants[0]?.id;
  const tenantQuery = useTenantQuery(activeId, {
    placeholderData: () => tenants.find((item) => item.id === activeId),
    staleTime: 30_000,
  });
  const tenant = tenantQuery.data;
  const filtered = Boolean(filters.search || filters.status);
  const clearFilters = () => {
    setSearch("");
    setFilters((current) => ({ ...current, search: "", status: "", page: 1 }));
  };

  const onSaved = (data) => {
    setSelectedId(data.id);
    setDrawer(null);
  };

  return (
    <div className="dwella-tenants-page">
      <div className="dwella-page-toolbar">
        <SegmentedFilter
          label="Filter tenants by status"
          options={tenantStatuses}
          value={filters.status || "all"}
          onChange={(value) => {
            setSelectedId(null);
            setFilters((current) => ({ ...current, status: value === "all" ? "" : value, page: 1 }));
          }}
        />
        <Input
          className="dwella-toolbar-search"
          aria-label="Search tenants"
          contentBefore={<Search20Regular />}
          placeholder="Search name, phone, email"
          value={search}
          onChange={(_, data) => {
            setSearch(data.value);
            setSelectedId(null);
          }}
        />
        {canManage ? (
          <PageActions>
            <Button appearance="primary" icon={<PersonAdd20Regular />} onClick={() => setDrawer("add")}>
              Add tenant
            </Button>
          </PageActions>
        ) : null}
      </div>

      {listQuery.isError ? (
        <div className="dwella-alert danger">
          Unable to load tenants. <Button size="small" onClick={() => listQuery.refetch()}>Retry</Button>
        </div>
      ) : null}

      {listQuery.isError && !tenants.length ? null : !listQuery.isLoading && !tenants.length ? (
        <EmptyState
          icon={<People24Regular />}
          title={filtered ? "No matching tenants" : "No tenants yet"}
          description={
            filtered ? "Try another search or status." : canManage ? "Add a tenant, and their unit and lease if you have them." : "Tenants will appear once a property manager adds them."
          }
          actionLabel={filtered ? "Clear filters" : canManage ? "Add tenant" : undefined}
          onAction={filtered ? clearFilters : canManage ? () => setDrawer("add") : undefined}
        />
      ) : (
        <div className="dwella-tenants-workspace">
          <div className="dwella-table-card" aria-busy={listQuery.isFetching}>
            <table className="dwella-table">
              <thead>
                <tr>
                  <th scope="col">Tenant</th>
                  <th scope="col">Unit</th>
                  <th scope="col">Lease ends</th>
                  <th scope="col" className="is-numeric">Rent</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {listQuery.isLoading ? <TableSkeleton /> : null}
                {tenants.map((row) => {
                  const lease = row.current_lease;
                  const selected = row.id === activeId;
                  return (
                    <tr
                      key={row.id}
                      className={selected ? "is-selected" : undefined}
                      aria-selected={selected}
                      tabIndex={0}
                      onClick={() => setSelectedId(row.id)}
                      onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && (event.preventDefault(), setSelectedId(row.id))}
                    >
                      <td>
                        <span className="dwella-who">
                          <Avatar name={row.full_name} />
                          <span>
                            <strong>{row.full_name}</strong>
                            <small>{row.phone_number}</small>
                          </span>
                        </span>
                      </td>
                      <td>{lease ? `${lease.unit_name} · ${lease.property_name}` : <span className="dwella-muted-copy">—</span>}</td>
                      <td>{lease ? formatDate(lease.end_date) : "—"}</td>
                      <td className="is-numeric">{lease ? formatMoney(lease.monthly_rent, { whole: true }) : "—"}</td>
                      <td><StatusBadge {...tenantBadgeProps(row.status)} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {pagination ? (
              <footer className="dwella-table-footer">
                <span>
                  Showing {tenants.length} of {pagination.count} {pagination.count === 1 ? "tenant" : "tenants"}
                </span>
                {pagination.total_pages > 1 ? (
                  <span className="dwella-table-pager">
                    <Button size="small" disabled={!pagination.previous} onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>Previous</Button>
                    <Button size="small" disabled={!pagination.next} onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next</Button>
                  </span>
                ) : null}
              </footer>
            ) : null}
          </div>

          {tenant ? <TenantProfile key={tenant.id} tenant={tenant} canManage={canManage} onEdit={() => setDrawer("edit")} /> : null}
        </div>
      )}

      {drawer ? (
        <TenantDrawer
          key={drawer === "edit" ? tenant?.id : "add"}
          open
          tenant={drawer === "edit" ? tenant : null}
          onClose={() => setDrawer(null)}
          onSaved={onSaved}
        />
      ) : null}
    </div>
  );
}
