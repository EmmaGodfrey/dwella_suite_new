import React, { useEffect, useState } from "react";
import "../../shared/records.scss";
import "./properties.scss";
import { useSearchParams } from "react-router-dom";
import { useIsMutating } from "@tanstack/react-query";
import {
  Button,
  Dropdown,
  Input,
  Menu,
  MenuItemRadio,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Option,
  Tooltip,
} from "@fluentui/react-components";
import {
  Add20Regular,
  ArrowUpload20Regular,
  Building20Regular,
  Building24Regular,
  Camera20Regular,
  ChevronDown16Regular,
  Edit20Regular,
  Location20Regular,
  Search20Regular,
} from "@fluentui/react-icons";
import {
  useCurrentUserQuery,
  useDashboardSummaryQuery,
  usePropertiesQuery,
  usePropertyQuery,
  useUnitsQuery,
} from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge, labelize, PageActions } from "../../shared/components";
import ImportDrawer from "../Imports/ImportDrawer";
import { PropertyPhoto } from "../../shared/components/PropertyPhoto";
import { formatMoney } from "../../shared/format";
import PropertyForm from "./PropertyForm";
import UnitForm from "./UnitForm";
import {
  formatRent,
  managementStatuses,
  optionLabel,
  orderOptions,
  propertyTypes,
} from "./options";

const defaultFilters = {
  search: "",
  property_type: "",
  management_status: "",
  town: "",
  ordering: "-created_at",
  page: 1,
  page_size: 12,
};
const UNIT_PAGE_SIZE = 6;
const asNumber = (value) => Number(value || 0);
const percent = (part, whole) => (whole ? Math.round((part / whole) * 100) : 0);
const unitCount = (value) => `${value} ${Number(value) === 1 ? "unit" : "units"}`;
const sortLabels = { name: "name", "-created_at": "newest", management_status: "status" };

// Placeholder rows mirror the real row's thumb-plus-three-lines shape, so the
// list keeps its height and does not jump when results arrive.
function ListSkeleton() {
  return [0, 1, 2, 3, 4].map((row) => (
    <div className="dwella-portfolio-row is-loading" key={row} aria-hidden="true">
      <span className="dwella-skeleton dwella-portfolio-thumb" />
      <span className="dwella-portfolio-row-copy">
        <span className="dwella-skeleton" style={{ height: 12, width: "62%" }} />
        <span className="dwella-skeleton" style={{ height: 10, width: "48%" }} />
        <span className="dwella-skeleton" style={{ height: 10, width: "40%" }} />
      </span>
    </div>
  ));
}

function UnitTableSkeleton() {
  return [0, 1, 2, 3].map((row) => (
    <tr key={row} className="is-loading" aria-hidden="true">
      {[70, 90, 50, 80, 76].map((width, index) => (
        <td key={index} className={index === 3 ? "is-numeric" : undefined}>
          <span className="dwella-skeleton" style={{ height: 12, width, display: "inline-block" }} />
        </td>
      ))}
      <td />
    </tr>
  ));
}

function Metric({ label, value, detail, tone }) {
  return (
    <div className="dwella-asset-metric">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

const layoutLabel = (unit) => {
  const bedrooms = asNumber(unit.bedrooms);
  const bathrooms = asNumber(unit.bathrooms);
  if (!bedrooms && !bathrooms) return "—";
  return [
    bedrooms ? `${bedrooms} bed` : "Studio",
    bathrooms ? `${+bathrooms.toFixed(1)} bath` : null,
  ]
    .filter(Boolean)
    .join(" · ");
};

function PropertyDetail({ property, onEdit, canManage }) {
  const [unitPage, setUnitPage] = useState(1);
  const [unitStatus, setUnitStatus] = useState("");
  const [editingUnit, setEditingUnit] = useState(null);
  const unitsQuery = useUnitsQuery(
    {
      property: property.id,
      occupancy_status: unitStatus,
      ordering: "name",
      page: unitPage,
      page_size: UNIT_PAGE_SIZE,
    },
    { placeholderData: (previous) => previous, staleTime: 30_000 },
  );
  const units = unitsQuery.data?.results || [];
  const pagination = unitsQuery.data?.pagination;
  const totalUnits = asNumber(property.units_count);
  const occupiedUnits = asNumber(property.occupied_units);
  const potential = asNumber(property.monthly_rent);
  const occupiedRent = asNumber(property.occupied_rent);
  const vacancy = Math.max(0, potential - occupiedRent);
  const notLet = Math.max(0, totalUnits - occupiedUnits);
  const tabs = [
    { value: "", label: "All", count: totalUnits },
    { value: "occupied", label: "Occupied", count: occupiedUnits },
    { value: "vacant", label: "Vacant", count: asNumber(property.vacant_units) },
    { value: "maintenance", label: "Maintenance", count: asNumber(property.maintenance_units) },
    ...(asNumber(property.reserved_units)
      ? [{ value: "reserved", label: "Reserved", count: asNumber(property.reserved_units) }]
      : []),
  ];
  const location = [property.address, property.town].filter(Boolean).join(", ") || "Location not set";

  return (
    <>
      <div className="dwella-property-cover">
        {property.cover_image ? <PropertyPhoto src={property.cover_image} name={property.name} /> : null}
        {canManage ? (
          <Button size="small" icon={<Camera20Regular />} onClick={onEdit}>
            {property.cover_image ? "Change cover" : "Add a cover photo"}
          </Button>
        ) : null}
      </div>

      <div className="dwella-property-body">
        <header className="dwella-asset-header">
          <div className="dwella-asset-identity">
            <div>
              <h2>{property.name}</h2>
              <StatusBadge value={property.management_status} />
            </div>
            <ul>
              <li>
                <Location20Regular />
                {location}
              </li>
              <li>
                <Building20Regular />
                {labelize(property.property_type)}
              </li>
            </ul>
          </div>
          {canManage ? (
            <Button icon={<Edit20Regular />} onClick={onEdit}>
              Edit
            </Button>
          ) : (
            <span className="dwella-read-only-label">Admin oversight</span>
          )}
        </header>

        <div className="dwella-asset-metrics">
          <Metric
            label="Monthly rent potential"
            value={formatRent(potential)}
            detail={totalUnits ? `${unitCount(totalUnits)} at full occupancy` : "No units yet"}
          />
          <Metric
            label="Occupancy"
            value={`${percent(occupiedUnits, totalUnits)}%`}
            detail={`${occupiedUnits} of ${unitCount(totalUnits)} let`}
          />
          <Metric
            label="Occupied rent"
            value={formatRent(occupiedRent)}
            detail="Earned each month"
            tone={occupiedRent ? "is-positive" : undefined}
          />
          <Metric
            label="Vacancy exposure"
            value={formatRent(vacancy)}
            detail={`${unitCount(notLet)} not let`}
            tone={vacancy ? "is-warning" : undefined}
          />
        </div>

        <section className="dwella-units-section" aria-label="Units">
          <div className="dwella-units-head">
            <h3>Units</h3>
            <div className="dwella-unit-tabs" role="group" aria-label="Filter units">
              {tabs.map((tab) => (
                <button
                  key={tab.value || "all"}
                  type="button"
                  aria-pressed={unitStatus === tab.value}
                  className={unitStatus === tab.value ? "is-selected" : undefined}
                  onClick={() => {
                    setUnitStatus(tab.value);
                    setUnitPage(1);
                  }}
                >
                  {tab.label}
                  <span>{tab.count}</span>
                </button>
              ))}
            </div>
            {canManage ? (
              <Button icon={<Add20Regular />} onClick={() => setEditingUnit({})}>
                Add unit
              </Button>
            ) : null}
          </div>

          {editingUnit && (
            <UnitForm
              key={editingUnit.id || "new"}
              propertyId={property.id}
              unit={editingUnit.id ? editingUnit : null}
              onClose={() => setEditingUnit(null)}
              onSaved={() => setEditingUnit(null)}
            />
          )}

          {unitsQuery.isError ? (
            <div className="dwella-alert danger">
              Could not load units.{" "}
              <Button size="small" onClick={() => unitsQuery.refetch()}>
                Retry
              </Button>
            </div>
          ) : !unitsQuery.isLoading && !units.length ? (
            <div className="dwella-asset-empty">
              {unitStatus ? `No ${labelize(unitStatus).toLowerCase()} units.` : "No units recorded for this property yet."}
            </div>
          ) : (
            <div className="dwella-unit-table" aria-busy={unitsQuery.isFetching}>
              <table className="dwella-table">
                <thead>
                  <tr>
                    <th scope="col">Unit</th>
                    <th scope="col">Layout</th>
                    <th scope="col">Floor area</th>
                    <th scope="col" className="is-numeric">Monthly rent</th>
                    <th scope="col">Status</th>
                    <th scope="col"><span className="dwella-visually-hidden">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {unitsQuery.isLoading ? <UnitTableSkeleton /> : null}
                  {units.map((unit) => (
                    <tr
                      key={unit.id}
                      tabIndex={canManage ? 0 : undefined}
                      onClick={canManage ? () => setEditingUnit(unit) : undefined}
                      onKeyDown={canManage ? (event) => event.key === "Enter" && setEditingUnit(unit) : undefined}
                    >
                      <td><strong>{unit.name}</strong></td>
                      <td>{layoutLabel(unit)}</td>
                      <td>{unit.floor_area ? `${+Number(unit.floor_area).toFixed(1)} m²` : "—"}</td>
                      <td className="is-numeric"><strong>{formatMoney(unit.rent_amount)}</strong></td>
                      <td><StatusBadge value={unit.occupancy_status} /></td>
                      <td className="dwella-unit-action">
                        {canManage ? (
                          <Tooltip content={`Edit ${unit.name}`} relationship="label">
                            <Button
                              appearance="subtle"
                              size="small"
                              icon={<Edit20Regular />}
                              onClick={(event) => {
                                event.stopPropagation();
                                setEditingUnit(unit);
                              }}
                            />
                          </Tooltip>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {pagination && units.length ? (
            <footer className="dwella-units-footer">
              <span>
                Showing {units.length} of {unitCount(pagination.count)}
              </span>
              {pagination.total_pages > 1 ? (
                <span className="dwella-table-pager">
                  <Button disabled={!pagination.previous} onClick={() => setUnitPage((p) => p - 1)}>
                    Previous
                  </Button>
                  <Button disabled={!pagination.next} onClick={() => setUnitPage((p) => p + 1)}>
                    Next
                  </Button>
                </span>
              ) : null}
            </footer>
          ) : null}
        </section>

        {property.description && (
          <section className="dwella-asset-notes">
            <h3>About this property</h3>
            <p>{property.description}</p>
          </section>
        )}
      </div>
    </>
  );
}

function FilterDropdown({ label, options, value, onChange }) {
  return (
    <Dropdown
      aria-label={label}
      className="dwella-filter-dropdown"
      selectedOptions={[value]}
      value={optionLabel(options, value)}
      onOptionSelect={(_, data) => onChange(data.optionValue)}
    >
      {options.map((option) => (
        <Option key={option.value || "all"} value={option.value}>
          {option.label}
        </Option>
      ))}
    </Dropdown>
  );
}

export default function Properties() {
  const [params, setParams] = useSearchParams();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const access = getUserAccess(user);
  const canManage = access.can_manage_properties;
  const initialSearch = params.get("search") || "";
  const [search, setSearch] = useState(initialSearch);
  const [filters, setFilters] = useState({
    ...defaultFilters,
    search: initialSearch,
  });
  const [selectedId, setSelectedId] = useState(null);
  const [mode, setMode] = useState("view");
  const [importing, setImporting] = useState(false);
  const saving = useIsMutating({ mutationKey: ["saveProperty"] }) > 0;
  const { data: summary } = useDashboardSummaryQuery({ enabled: Boolean(user), staleTime: 60_000 });
  const townOptions = [
    { value: "", label: "All towns" },
    ...(summary?.portfolio?.towns || []).map((town) => ({ value: town, label: town })),
  ];
  const typeOptions = propertyTypes;
  const statusOptions = [{ value: "", label: "Any status" }, ...managementStatuses.filter((item) => item.value)];

  useEffect(() => {
    if (!user) return;
    if (params.get("new") === "1") {
      setMode(canManage ? "add" : "view");
      setParams({}, { replace: true });
    }
  }, [canManage, params, setParams, user]);
  useEffect(() => {
    const timeout = setTimeout(
      () =>
        setFilters((current) =>
          current.search === search ? current : { ...current, search, page: 1 },
        ),
      300,
    );
    return () => clearTimeout(timeout);
  }, [search]);

  const listQuery = usePropertiesQuery(filters, {
    placeholderData: (previous) => previous,
    staleTime: 45_000,
  });
  const properties = listQuery.data?.results || [];
  const pagination = listQuery.data?.pagination;
  const activeId = selectedId || properties[0]?.id;
  const selectedQuery = usePropertyQuery(activeId, {
    placeholderData: () => properties.find((item) => item.id === activeId),
    staleTime: 30_000,
  });
  const property = selectedQuery.data;
  const updateFilter = (key, value) => {
    setSelectedId(null);
    setFilters((current) => ({ ...current, [key]: value, page: 1 }));
  };
  const clearFilters = () => {
    setSearch("");
    setSelectedId(null);
    setFilters(defaultFilters);
  };
  const onSaved = (data) => {
    if (data?.id) {
      setSelectedId(data.id);
      setSearch(data.name);
      setFilters({ ...defaultFilters, search: data.name });
    }
    setMode("view");
  };
  const closeForm = () => setMode("view");
  const matches =
    filters.search || filters.property_type || filters.management_status || filters.town;

  return (
    <div className="dwella-portfolio-page">
      <div className="dwella-page-toolbar dwella-portfolio-toolbar">
        <Input
          className="dwella-portfolio-search"
          aria-label="Search properties"
          contentBefore={<Search20Regular />}
          placeholder="Search by name, address or town"
          value={search}
          onChange={(_, d) => {
            setSearch(d.value);
            setSelectedId(null);
          }}
        />
        <FilterDropdown label="Property type" options={typeOptions} value={filters.property_type} onChange={(value) => updateFilter("property_type", value)} />
        <FilterDropdown label="Management status" options={statusOptions} value={filters.management_status} onChange={(value) => updateFilter("management_status", value)} />
        {townOptions.length > 2 ? (
          <FilterDropdown label="Town" options={townOptions} value={filters.town} onChange={(value) => updateFilter("town", value)} />
        ) : null}
        {matches ? (
          <Button appearance="transparent" onClick={clearFilters}>
            Clear
          </Button>
        ) : null}
        {summary ? (
          <dl className="dwella-portfolio-totals" aria-label="Portfolio totals">
            <div><dt>{summary.properties.total}</dt><dd>{summary.properties.total === 1 ? "property" : "properties"}</dd></div>
            <div><dt>{summary.units.total}</dt><dd>{summary.units.total === 1 ? "unit" : "units"}</dd></div>
            <div><dt>{Math.round(summary.units.occupancy_rate)}%</dt><dd>occupied</dd></div>
          </dl>
        ) : null}
        {canManage ? (
          <PageActions>
            <Button icon={<ArrowUpload20Regular />} onClick={() => setImporting(true)}>Import units</Button>
            <Button appearance="primary" icon={<Add20Regular />} onClick={() => setMode("add")}>
              Add property
            </Button>
          </PageActions>
        ) : null}
      </div>

      <div className="dwella-portfolio-workspace">
        <aside className="dwella-portfolio-list-card" aria-label="Property list">
          <div className="dwella-portfolio-list-head">
            <Menu
              checkedValues={{ ordering: [filters.ordering] }}
              onCheckedValueChange={(_, data) => updateFilter("ordering", data.checkedItems[0])}
            >
              <MenuTrigger disableButtonEnhancement>
                <Button appearance="transparent" size="small" icon={<ChevronDown16Regular />} iconPosition="after">
                  Sorted by {sortLabels[filters.ordering]}
                </Button>
              </MenuTrigger>
              <MenuPopover>
                <MenuList>
                  {orderOptions.map((option) => (
                    <MenuItemRadio key={option.value} name="ordering" value={option.value}>
                      {option.label}
                    </MenuItemRadio>
                  ))}
                </MenuList>
              </MenuPopover>
            </Menu>
            <span>{pagination ? `${pagination.count} ${matches ? "found" : "total"}` : ""}</span>
          </div>

          {listQuery.isError && (
            <div className="dwella-alert danger">
              Unable to load properties.{" "}
              <Button size="small" onClick={() => listQuery.refetch()}>
                Retry
              </Button>
            </div>
          )}
          <div className="dwella-portfolio-list" aria-busy={listQuery.isFetching}>
            {listQuery.isLoading && <ListSkeleton />}
            {properties.map((item) => {
              const units = asNumber(item.units_count);
              const active = item.id === activeId && mode !== "add";
              return (
                <button
                  type="button"
                  className={`dwella-portfolio-row${active ? " is-active" : ""}`}
                  aria-current={active ? "true" : undefined}
                  key={item.id}
                  disabled={saving}
                  onClick={() => {
                    setSelectedId(item.id);
                    setMode("view");
                  }}
                >
                  <span className="dwella-portfolio-thumb">
                    {item.cover_image ? <PropertyPhoto src={item.cover_image} name={item.name} /> : <Building20Regular />}
                  </span>
                  <span className="dwella-portfolio-row-copy">
                    <strong>{item.name}</strong>
                    <small>{[item.address, item.town].filter(Boolean).join(" · ") || "Location not set"}</small>
                    <span className="dwella-portfolio-row-meta">
                      <StatusBadge value={item.management_status} />
                      <span>{units ? `${unitCount(units)} · ${percent(asNumber(item.occupied_units), units)}% let` : "No units"}</span>
                    </span>
                  </span>
                </button>
              );
            })}
            {!listQuery.isLoading && !listQuery.isError && !properties.length && (
              <div className="dwella-portfolio-no-results">
                {matches ? "No matching properties." : "No properties yet."}
                {matches || canManage ? (
                  <Button size="small" onClick={matches ? clearFilters : () => setMode("add")}>
                    {matches ? "Clear filters" : "Add property"}
                  </Button>
                ) : null}
              </div>
            )}
          </div>
          {pagination?.total_pages > 1 && (
            <footer className="dwella-units-footer dwella-portfolio-pagination">
              <span>
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <span className="dwella-table-pager">
                <Button
                  size="small"
                  disabled={!pagination.previous}
                  onClick={() => {
                    setSelectedId(null);
                    setFilters((f) => ({ ...f, page: f.page - 1 }));
                  }}
                >
                  Previous
                </Button>
                <Button
                  size="small"
                  disabled={!pagination.next}
                  onClick={() => {
                    setSelectedId(null);
                    setFilters((f) => ({ ...f, page: f.page + 1 }));
                  }}
                >
                  Next
                </Button>
              </span>
            </footer>
          )}
        </aside>

        <section className="dwella-property-detail" aria-label="Property details">
          {canManage && (mode === "add" || mode === "edit") ? (
            <PropertyForm
              key={mode === "edit" ? activeId : "add"}
              property={mode === "edit" ? property : null}
              onClose={closeForm}
              onSaved={onSaved}
            />
          ) : listQuery.isError ? (
            <div className="dwella-asset-empty">Select a property when your portfolio is available.</div>
          ) : property ? (
            <PropertyDetail
              key={property.id}
              property={property}
              onEdit={() => setMode("edit")}
              canManage={canManage}
            />
          ) : listQuery.isLoading ? (
            <div className="dwella-property-body" aria-hidden="true">
              <span className="dwella-skeleton" style={{ height: 26, width: 240 }} />
              <span className="dwella-skeleton" style={{ height: 92, width: "100%" }} />
              <span className="dwella-skeleton" style={{ height: 220, width: "100%" }} />
            </div>
          ) : (
            <EmptyState
              icon={<Building24Regular />}
              title={matches ? "No matching properties" : canManage ? "Start your portfolio" : "No property manager properties"}
              description={
                matches
                  ? "Try another search or clear the filters."
                  : canManage ? "Add your first property to begin." : "Properties will appear after a property manager adds them."
              }
              actionLabel={matches ? "Clear filters" : canManage ? "Add property" : undefined}
              onAction={matches ? clearFilters : canManage ? () => setMode("add") : undefined}
            />
          )}
        </section>
      </div>
      {importing ? <ImportDrawer kind="units" onClose={() => setImporting(false)} /> : null}
    </div>
  );
}
