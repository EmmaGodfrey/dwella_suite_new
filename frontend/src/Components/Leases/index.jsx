import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Input } from "@fluentui/react-components";
import { DocumentAdd20Regular, DocumentText24Regular, Search20Regular } from "@fluentui/react-icons";

import { useCurrentUserQuery, useLeasesQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, SegmentedFilter, PageActions, StatusBadge } from "../../shared/components";
import { daysUntil, formatDate, formatMoney } from "../../shared/format";
import { leaseBadgeProps, leaseStatuses } from "../../shared/tenancy";
import LeaseDrawer from "./LeaseDrawer";
import "../../shared/records.scss";
import "./leases.scss";

const PAGE_SIZE = 20;

function TableSkeleton() {
  return [0, 1, 2, 3, 4].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      {[70, 140, 160, 150, 70, 80].map((width, index) => (
        <td key={index}><span className="dwella-skeleton" style={{ height: 12, width }} /></td>
      ))}
    </tr>
  ));
}

export default function Leases() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const canManage = getUserAccess(user).can_manage_properties;
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ status: "", search: "", page: 1, page_size: PAGE_SIZE });
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (params.get("new") === "1" && canManage) {
      setDrawerOpen(true);
      setParams({}, { replace: true });
    }
  }, [canManage, params, setParams]);

  useEffect(() => {
    const timeout = setTimeout(() => setFilters((current) => (current.search === search ? current : { ...current, search, page: 1 })), 300);
    return () => clearTimeout(timeout);
  }, [search]);

  const listQuery = useLeasesQuery(filters, { placeholderData: (previous) => previous, staleTime: 30_000 });
  const leases = listQuery.data?.results || [];
  const pagination = listQuery.data?.pagination;
  const filtered = Boolean(filters.search || filters.status);
  const clearFilters = () => {
    setSearch("");
    setFilters((current) => ({ ...current, search: "", status: "", page: 1 }));
  };
  const open = (id) => navigate(`/leases/${id}`);

  return (
    <div className="dwella-leases-page">
      <div className="dwella-page-toolbar">
        <SegmentedFilter
          label="Filter leases by status"
          options={leaseStatuses}
          value={filters.status || "all"}
          onChange={(value) => {
            
            setFilters((current) => ({ ...current, status: value === "all" ? "" : value, page: 1 }));
          }}
        />
        <Input
          className="dwella-toolbar-search"
          aria-label="Search leases"
          contentBefore={<Search20Regular />}
          placeholder="Search reference, tenant, unit"
          value={search}
          onChange={(_, data) => setSearch(data.value)}
        />
        {canManage ? (
          <PageActions>
            <Button appearance="primary" icon={<DocumentAdd20Regular />} onClick={() => setDrawerOpen(true)}>
              New lease
            </Button>
          </PageActions>
        ) : null}
      </div>

      {listQuery.isError ? (
        <div className="dwella-alert danger">
          Unable to load leases. <Button size="small" onClick={() => listQuery.refetch()}>Retry</Button>
        </div>
      ) : null}

      {listQuery.isError && !leases.length ? null : !listQuery.isLoading && !leases.length ? (
        <EmptyState
          icon={<DocumentText24Regular />}
          title={filtered ? "No matching leases" : "No leases yet"}
          description={filtered ? "Try another search or status." : canManage ? "Create a lease to link a tenant to a unit and start collecting rent." : "Leases will appear once a property manager creates them."}
          actionLabel={filtered ? "Clear filters" : canManage ? "New lease" : undefined}
          onAction={filtered ? clearFilters : canManage ? () => setDrawerOpen(true) : undefined}
        />
      ) : (
        <div className="dwella-table-card" aria-busy={listQuery.isFetching}>
          <table className="dwella-table">
            <thead>
              <tr>
                <th scope="col">Lease</th>
                <th scope="col">Tenant</th>
                <th scope="col">Unit</th>
                <th scope="col">Term</th>
                <th scope="col" className="is-numeric">Rent</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.isLoading ? <TableSkeleton /> : null}
              {leases.map((lease) => {
                const endsIn = daysUntil(lease.end_date);
                const endingSoon = lease.status === "active" && endsIn !== null && endsIn >= 0 && endsIn <= 60;
                return (
                  <tr
                    key={lease.id}
                    tabIndex={0}
                    onClick={() => open(lease.id)}
                    onKeyDown={(event) => event.key === "Enter" && open(lease.id)}
                  >
                    <td><strong>{lease.reference}</strong></td>
                    <td>{lease.tenant_name}</td>
                    <td>{lease.unit_name} · {lease.property_name}</td>
                    <td>
                      {formatDate(lease.start_date)} – {formatDate(lease.end_date)}
                      {endingSoon ? <small className="dwella-cell-note is-warning">Ends in {endsIn} days</small> : null}
                    </td>
                    <td className="is-numeric">{formatMoney(lease.monthly_rent, { whole: true })}</td>
                    <td><StatusBadge {...leaseBadgeProps(lease.status)} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {pagination ? (
            <footer className="dwella-table-footer">
              <span>Showing {leases.length} of {pagination.count} {pagination.count === 1 ? "lease" : "leases"}</span>
              {pagination.total_pages > 1 ? (
                <span className="dwella-table-pager">
                  <Button size="small" disabled={!pagination.previous} onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>Previous</Button>
                  <Button size="small" disabled={!pagination.next} onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next</Button>
                </span>
              ) : null}
            </footer>
          ) : null}
        </div>
      )}

      {drawerOpen ? <LeaseDrawer open onClose={() => setDrawerOpen(false)} onSaved={(lease) => open(lease.id)} /> : null}
    </div>
  );
}
