import React, { useEffect, useState } from "react";
import "./properties.scss";
import { useSearchParams } from "react-router-dom";
import { useIsMutating } from "@tanstack/react-query";
import {
  Button,
  Dropdown,
  Input,
  Option,
  ProgressBar,
  Tooltip,
} from "@fluentui/react-components";
import {
  Add20Regular,
  ArrowLeft20Regular,
  ArrowRight20Regular,
  Building24Regular,
  Dismiss20Regular,
  Edit20Regular,
  Filter20Regular,
  Home20Regular,
  Location20Regular,
  Money20Regular,
  People20Regular,
  Search20Regular,
} from "@fluentui/react-icons";
import {
  useCurrentUserQuery,
  usePropertiesQuery,
  usePropertyQuery,
  useUnitsQuery,
} from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { EmptyState, StatusBadge, labelize } from "../../shared/components";
import { PropertyPhoto } from "../../shared/components/PropertyPhoto";
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
  ordering: "name",
  page: 1,
  page_size: 12,
};
const asNumber = (value) => Number(value || 0);
const percent = (part, whole) => (whole ? Math.round((part / whole) * 100) : 0);
const unitCount = (value) => `${value} ${Number(value) === 1 ? "unit" : "units"}`;

// Placeholder rows mirror the real row's photo-plus-two-lines shape, so the
// rail keeps its height and the list does not jump when results arrive.
function RailSkeleton() {
  return (
    <>
      {[0, 1, 2, 3, 4, 5].map((row) => (
        <div className="dwella-portfolio-skeleton" key={row} aria-hidden="true">
          <span className="dwella-skeleton" />
          <div>
            <span className="dwella-skeleton" style={{ height: 12, width: "72%" }} />
            <span className="dwella-skeleton" style={{ height: 10, width: "48%" }} />
            <span className="dwella-skeleton" style={{ height: 10, width: "60%" }} />
          </div>
        </div>
      ))}
    </>
  );
}

function UnitDirectorySkeleton() {
  return (
    <div className="dwella-unit-directory" aria-hidden="true">
      {[0, 1, 2, 3, 4].map((row) => (
        <div className="dwella-unit-directory-row is-loading" key={row}>
          <span className="dwella-skeleton dwella-unit-symbol-skeleton" />
          <div>
            <span className="dwella-skeleton" style={{ height: 12, width: "44%" }} />
            <span className="dwella-skeleton" style={{ height: 10, width: "28%" }} />
          </div>
          <span className="dwella-skeleton" style={{ height: 12, width: 64 }} />
          <span />
        </div>
      ))}
    </div>
  );
}

function PropertyMetric({ icon, label, value, detail, tone }) {
  return (
    <div className={"dwella-asset-metric dwella-asset-metric-" + tone}>
      <span className="dwella-asset-metric-icon">{icon}</span>
      <span className="dwella-asset-metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function PropertyWorkspace({ property, onEdit, canManage }) {
  const [unitPage, setUnitPage] = useState(1);
  const [editingUnit, setEditingUnit] = useState(null);
  useEffect(() => setUnitPage(1), [property.id]);
  const unitsQuery = useUnitsQuery(
    { property: property.id, page: unitPage, page_size: 5 },
    { staleTime: 30_000 },
  );
  const units = unitsQuery.data?.results || [];
  const pagination = unitsQuery.data?.pagination;
  const totalUnits = asNumber(property.units_count);
  const occupiedUnits = asNumber(property.occupied_units);
  const potential = asNumber(property.monthly_rent);
  const occupiedRent = asNumber(property.occupied_rent);
  const vacancy = Math.max(0, potential - occupiedRent);
  const occupancy = percent(occupiedUnits, totalUnits);

  return (
    <>
      <header className="dwella-asset-header">
        <PropertyPhoto src={property.cover_image} name={property.name} />
        <div className="dwella-asset-identity">
          <div>
            <h2>{property.name}</h2>
            <StatusBadge value={property.management_status} />
          </div>
          <p>
            <Location20Regular />
            {[property.address, property.town, property.province]
              .filter(Boolean)
              .join(", ") || "Location not set"}
          </p>
        </div>
        {canManage ? (
          <Button appearance="primary" icon={<Edit20Regular />} onClick={onEdit}>
            Manage property
          </Button>
        ) : (
          <span className="dwella-read-only-label">Admin oversight</span>
        )}
      </header>

      <div className="dwella-asset-content">
        <div className="dwella-asset-metrics">
          <PropertyMetric
            icon={<Money20Regular />}
            label="Monthly rent potential"
            value={formatRent(potential)}
            detail={unitCount(totalUnits)}
            tone="green"
          />
          <PropertyMetric
            icon={<People20Regular />}
            label="Occupancy rate"
            value={occupancy + "%"}
            detail={`${occupiedUnits} of ${unitCount(totalUnits)} occupied`}
            tone="blue"
          />
          <PropertyMetric
            icon={<Home20Regular />}
            label="Occupied rent"
            value={formatRent(occupiedRent)}
            detail="Monthly value of occupied units"
            tone="gold"
          />
          <PropertyMetric
            icon={<Building24Regular />}
            label="Vacancy exposure"
            value={formatRent(vacancy)}
            detail={
              `${unitCount(Math.max(0, totalUnits - occupiedUnits))} not occupied`
            }
            tone="violet"
          />
        </div>

        <div className="dwella-asset-main-grid">
          <section className="dwella-asset-panel dwella-rent-panel">
            <div className="dwella-asset-panel-heading">
              <div>
                <h3>Rent potential</h3>
                <p>Current unit rent compared with occupied rent</p>
              </div>
            </div>
            {totalUnits ? (
              <>
                <div className="dwella-rent-figure">
                  <span>Monthly potential</span>
                  <strong>{formatRent(potential)}</strong>
                </div>
                <div className="dwella-rent-bars">
                  <div>
                    <div>
                      <span>Occupied rent</span>
                      <strong>{formatRent(occupiedRent)}</strong>
                    </div>
                    <ProgressBar
                      value={potential ? occupiedRent / potential : 0}
                    />
                  </div>
                  <div>
                    <div>
                      <span>Vacancy exposure</span>
                      <strong>{formatRent(vacancy)}</strong>
                    </div>
                    <ProgressBar
                      className="dwella-progress-vacant"
                      value={potential ? vacancy / potential : 0}
                    />
                  </div>
                </div>
                <div className="dwella-rent-footnote">
                  {occupancy}% of units currently occupied
                </div>
              </>
            ) : (
              <div className="dwella-asset-empty">
                Add units to this property to see its rent potential.
              </div>
            )}
          </section>

          <section className="dwella-asset-panel dwella-unit-panel">
            <div className="dwella-asset-panel-heading">
              <div>
                <h3>Unit directory</h3>
                <p>{unitCount(totalUnits)}</p>
              </div>
              {canManage ? (
                <Button
                  size="small"
                  icon={<Add20Regular />}
                  onClick={() => setEditingUnit({})}
                >
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
            {unitsQuery.isError && (
              <div className="dwella-alert danger">
                Could not load units.{" "}
                <Button size="small" onClick={() => unitsQuery.refetch()}>
                  Retry
                </Button>
              </div>
            )}
            {unitsQuery.isLoading && <UnitDirectorySkeleton />}
            {!unitsQuery.isLoading && !unitsQuery.isError && !units.length && (
              <div className="dwella-asset-empty">
                No units recorded for this property.
              </div>
            )}
            <div className="dwella-unit-directory">
              {units.map((unit) => {
                const Row = canManage ? "button" : "div";
                return (
                <Row
                  type={canManage ? "button" : undefined}
                  className={`dwella-unit-directory-row${canManage ? "" : " is-read-only"}`}
                  key={unit.id}
                  onClick={canManage ? () => setEditingUnit(unit) : undefined}
                  aria-label={canManage ? `Edit ${unit.name}` : undefined}
                >
                  <span className="dwella-unit-symbol">
                    <Home20Regular />
                  </span>
                  <div>
                    <strong>{unit.name}</strong>
                    <small>{labelize(unit.occupancy_status)}</small>
                  </div>
                  <div className="dwella-unit-rent">
                    <strong>{formatRent(unit.rent_amount)}</strong>
                    <small>/month</small>
                  </div>
                  {canManage ? <Edit20Regular className="dwella-unit-edit-icon" /> : <span />}
                </Row>
                );
              })}
            </div>
            {pagination?.total_pages > 1 && (
              <div className="dwella-unit-pagination">
                <span>
                  {pagination.page} / {pagination.total_pages}
                </span>
                <Tooltip content="Previous units" relationship="label">
                  <Button
                    aria-label="Previous units"
                    size="small"
                    icon={<ArrowLeft20Regular />}
                    disabled={!pagination.previous}
                    onClick={() => setUnitPage((p) => p - 1)}
                  />
                </Tooltip>
                <Tooltip content="Next units" relationship="label">
                  <Button
                    aria-label="Next units"
                    size="small"
                    icon={<ArrowRight20Regular />}
                    disabled={!pagination.next}
                    onClick={() => setUnitPage((p) => p + 1)}
                  />
                </Tooltip>
              </div>
            )}
          </section>
        </div>
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
  const [showFilters, setShowFilters] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [mode, setMode] = useState("view");
  const saving = useIsMutating({ mutationKey: ["saveProperty"] }) > 0;

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
    filters.search || filters.property_type || filters.management_status;

  return (
    <div className="dwella-portfolio-page">
      <aside className="dwella-portfolio-rail" aria-label="Property portfolio">
        <div className="dwella-portfolio-rail-head">
          <div>
            <h2>Portfolio</h2>
            <small>
              {pagination?.count ?? 0} {matches ? "matches" : "assets"}
            </small>
          </div>
          {canManage ? (
            <Tooltip content="Add property" relationship="label">
              <Button
                appearance="primary"
                icon={<Add20Regular />}
                aria-label="Add property"
                onClick={() => setMode("add")}
              />
            </Tooltip>
          ) : null}
        </div>
        <Input
          aria-label="Search portfolio"
          contentBefore={<Search20Regular />}
          placeholder="Search portfolio..."
          value={search}
          onChange={(_, d) => {
            setSearch(d.value);
            setSelectedId(null);
          }}
        />
        <div className="dwella-portfolio-filter-head">
          <span>Properties</span>
          <Tooltip content="Filters" relationship="label">
            <Button
              aria-label="Filters"
              icon={<Filter20Regular />}
              appearance="subtle"
              aria-expanded={showFilters}
              onClick={() => setShowFilters((value) => !value)}
            />
          </Tooltip>
        </div>
        {showFilters && (
          <div className="dwella-portfolio-filters">
            <Dropdown
              aria-label="Property type"
              selectedOptions={[filters.property_type]}
              value={optionLabel(propertyTypes, filters.property_type)}
              onOptionSelect={(_, d) =>
                updateFilter("property_type", d.optionValue)
              }
            >
              {propertyTypes.map((t) => (
                <Option key={t.value} value={t.value}>
                  {t.label}
                </Option>
              ))}
            </Dropdown>
            <Dropdown
              aria-label="Management status"
              selectedOptions={[filters.management_status]}
              value={optionLabel(managementStatuses, filters.management_status)}
              onOptionSelect={(_, d) =>
                updateFilter("management_status", d.optionValue)
              }
            >
              {managementStatuses.map((t) => (
                <Option key={t.value} value={t.value}>
                  {t.label}
                </Option>
              ))}
            </Dropdown>
            <Dropdown
              aria-label="Sort properties"
              selectedOptions={[filters.ordering]}
              value={optionLabel(orderOptions, filters.ordering)}
              onOptionSelect={(_, d) => updateFilter("ordering", d.optionValue)}
            >
              {orderOptions.map((t) => (
                <Option key={t.value} value={t.value}>
                  {t.label}
                </Option>
              ))}
            </Dropdown>
            {matches && (
              <Button
                appearance="transparent"
                icon={<Dismiss20Regular />}
                onClick={clearFilters}
              >
                Clear filters
              </Button>
            )}
          </div>
        )}
        {listQuery.isError && (
          <div className="dwella-alert danger">
            Unable to load properties.{" "}
            <Button size="small" onClick={() => listQuery.refetch()}>
              Retry
            </Button>
          </div>
        )}
        <div className="dwella-portfolio-list" aria-busy={listQuery.isFetching}>
          {listQuery.isLoading && <RailSkeleton />}
          {properties.map((item) => (
            <button
              type="button"
              className={
                "dwella-portfolio-item" +
                (item.id === activeId && mode === "view" ? " is-active" : "")
              }
              key={item.id}
              disabled={saving}
              onClick={() => {
                setSelectedId(item.id);
                setMode("view");
              }}
            >
              <PropertyPhoto src={item.cover_image} name={item.name} />
              <span className="dwella-portfolio-item-copy">
                <strong>{item.name}</strong>
                <small>{item.town || item.address || "Location not set"}</small>
                <span className="dwella-portfolio-item-meta">
                  <span>{unitCount(item.units_count ?? 0)}</span>
                  <b>{formatRent(item.monthly_rent)}</b>
                </span>
              </span>
            </button>
          ))}
          {!listQuery.isLoading && !listQuery.isError && !properties.length && (
            <div className="dwella-portfolio-no-results">
              {matches ? "No matching properties." : "No properties yet."}
              {matches || canManage ? (
                <Button
                  size="small"
                  onClick={matches ? clearFilters : () => setMode("add")}
                >
                  {matches ? "Clear filters" : "Add property"}
                </Button>
              ) : null}
            </div>
          )}
        </div>
        {pagination?.total_pages > 1 && (
          <div className="dwella-portfolio-pagination">
            <span>
              Page {pagination.page} / {pagination.total_pages}
            </span>
            <Button
              aria-label="Previous properties"
              size="small"
              icon={<ArrowLeft20Regular />}
              disabled={!pagination.previous}
              onClick={() => {
                setSelectedId(null);
                setFilters((f) => ({ ...f, page: f.page - 1 }));
              }}
            />
            <Button
              aria-label="Next properties"
              size="small"
              icon={<ArrowRight20Regular />}
              disabled={!pagination.next}
              onClick={() => {
                setSelectedId(null);
                setFilters((f) => ({ ...f, page: f.page + 1 }));
              }}
            />
          </div>
        )}
      </aside>
      <section
        className="dwella-portfolio-workspace"
        aria-label="Property workspace"
      >
        {canManage && (mode === "add" || mode === "edit") ? (
          <PropertyForm
            key={mode === "edit" ? activeId : "add"}
            property={mode === "edit" ? property : null}
            onClose={closeForm}
            onSaved={onSaved}
          />
        ) : listQuery.isError ? (
          <div className="dwella-asset-empty">
            Select a property when your portfolio is available.
          </div>
        ) : property ? (
          <PropertyWorkspace
            key={property.id}
            property={property}
            onEdit={() => setMode("edit")}
            canManage={canManage}
          />
        ) : (
          <EmptyState
            icon={<Building24Regular />}
            title={matches ? "No matching properties" : canManage ? "Start your portfolio" : "No landlord properties"}
            description={
              matches
                ? "Try another search or clear the filters."
                : canManage ? "Add your first property to begin." : "Properties will appear after a landlord adds them."
            }
            actionLabel={matches ? "Clear filters" : canManage ? "Add property" : undefined}
            onAction={matches ? clearFilters : canManage ? () => setMode("add") : undefined}
          />
        )}
      </section>
    </div>
  );
}
