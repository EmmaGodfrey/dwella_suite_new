import React from "react";
import "./dashboard.scss";
import { Link, useNavigate } from "react-router-dom";
import { Button, ProgressBar } from "@fluentui/react-components";
import {
  Add20Regular,
  ArrowRight20Regular,
  DocumentText24Regular,
  Home24Regular,
  Payment24Regular,
  Wrench24Regular,
} from "@fluentui/react-icons";

import { useCurrentUserQuery, useDashboardSummaryQuery } from "../../Services/queries";
import { getUserAccess } from "../../shared/access";
import { StatusBadge } from "../../shared/components";
import { PropertyPhoto } from "../../shared/components/PropertyPhoto";

const money = new Intl.NumberFormat("en-ZM", {
  style: "currency",
  currency: "ZMW",
  maximumFractionDigits: 0,
});
const number = new Intl.NumberFormat("en-ZM");
const formatMoney = (value) => money.format(Number(value || 0));
const formatNumber = (value) => number.format(Number(value || 0));
const unitCount = (value) => `${formatNumber(value)} ${Number(value) === 1 ? "unit" : "units"}`;
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
  portfolio: { towns_count: 0, average_units_per_property: 0 },
  recent_properties: [],
  top_units: [],
};

function TenantDashboard({ navigate }) {
  return (
    <div className="dwella-screen dwella-dashboard-v2 dwella-tenant-dashboard">
      <header className="dwella-dashboard-intro">
        <div>
          <span className="dwella-dashboard-kicker">Tenant workspace</span>
          <h2>Your home at a glance</h2>
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

// A figure reserves its own height while loading, so the pulse band does not
// change size when the request lands.
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

// Placeholder rows match the real card's grid, so the roster does not reflow
// when the properties arrive.
function RosterSkeleton() {
  return (
    <>
      {[0, 1, 2, 3].map((row) => (
        <div className="dwella-property-roster-item is-loading" key={row} aria-hidden="true">
          <span className="dwella-skeleton dwella-roster-photo-skeleton" />
          <div className="dwella-property-roster-copy">
            <span className="dwella-skeleton" style={{ width: "58%", height: 12 }} />
            <span className="dwella-skeleton" style={{ width: "42%", height: 10 }} />
            <span className="dwella-skeleton" style={{ width: "34%", height: 10 }} />
          </div>
        </div>
      ))}
    </>
  );
}

const Dashboard = () => {
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const access = getUserAccess(user);
  const isPlatformAdmin = access.persona === "platform_admin";
  const isTenant = access.persona === "tenant";
  const {
    data = emptySummary,
    error,
    isLoading,
    isFetching,
  } = useDashboardSummaryQuery({ enabled: Boolean(user) && !isTenant });

  if (isTenant) return <TenantDashboard navigate={navigate} />;
  const organizationName =
    data.organization?.display_name ||
    data.organization?.name ||
    "No organization selected";
  const occupancy = Number(data.units.occupancy_rate || 0);

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
          <h2>{isPlatformAdmin ? "Landlord portfolios" : organizationName}</h2>
        </div>
        {access.can_manage_properties ? (
          <Button
            appearance="primary"
            icon={<Add20Regular />}
            onClick={() => navigate("/properties?new=1")}
          >
            Add property
          </Button>
        ) : null}
      </header>

      {/* One focal figure the rest of the screen is measured against, then a
          quiet strip of supporting counts. Collected rent replaces the rent roll
          here once billing exists; until then the bar splits what the
          portfolio earns from what vacancy costs it. */}
      <section className="dwella-portfolio-pulse" aria-label="Portfolio pulse">
        <div className="dwella-pulse-lead">
          <span>{isPlatformAdmin ? "Managed rent roll per month" : "Monthly rent roll"}</span>
          <div className="dwella-pulse-figure">
            <strong>
              <Figure loading={isLoading} width="7ch">
                {formatMoney(data.finance.monthly_rent_roll)}
              </Figure>
            </strong>
            <small>across {unitCount(data.units.total)}</small>
          </div>
          <div
            className="dwella-pulse-bar"
            role="img"
            aria-label={`${formatMoney(data.finance.occupied_rent_roll)} from occupied units, ${formatMoney(data.finance.vacancy_loss)} lost to vacancy`}
          >
            <span className="is-occupied" style={{ flexGrow: Number(data.finance.occupied_rent_roll || 0) }} />
            <span className="is-vacant" style={{ flexGrow: Number(data.finance.vacancy_loss || 0) }} />
          </div>
          <ul className="dwella-pulse-legend">
            <li className="is-occupied">{formatMoney(data.finance.occupied_rent_roll)} from occupied units</li>
            <li className="is-vacant">
              {formatMoney(data.finance.vacancy_loss)} lost to vacancy · {unitCount(data.units.vacant)} vacant
            </li>
          </ul>
        </div>

        <dl className="dwella-pulse-stats">
          <PulseStat label="Occupancy" loading={isLoading} value={`${occupancy}%`} note={`${formatNumber(data.units.occupied)} of ${unitCount(data.units.total)}`} />
          {isPlatformAdmin ? (
            <>
              <PulseStat label="Organizations" loading={isLoading} value={formatNumber(data.platform?.organizations)} />
              <PulseStat label="Landlords" loading={isLoading} value={formatNumber(data.platform?.landlords)} />
              <PulseStat label="Properties" loading={isLoading} value={formatNumber(data.properties.total)} />
            </>
          ) : (
            <>
              <PulseStat label="Properties" loading={isLoading} value={formatNumber(data.properties.total)} />
              <PulseStat label="Average rent" loading={isLoading} value={formatMoney(data.finance.average_unit_rent)} note="per unit" />
              <PulseStat label="Active towns" loading={isLoading} value={formatNumber(data.portfolio.towns_count)} />
            </>
          )}
        </dl>
      </section>

      <div className="dwella-dashboard-columns">
        <div className="dwella-dashboard-column">
          <section className="dwella-property-roster">
            <SectionHeading
              title="Properties"
              note={isFetching && !isLoading ? "Updating portfolio..." : isPlatformAdmin ? "Recently added across landlord portfolios" : "Recently added assets"}
              action={
                <Button
                  appearance="subtle"
                  icon={<ArrowRight20Regular />}
                  iconPosition="after"
                  onClick={() => navigate("/properties")}
                >
                  View portfolio
                </Button>
              }
            />
            <div className="dwella-property-roster-grid">
              {isLoading ? <RosterSkeleton /> : null}
              {data.recent_properties.map((property) => (
                <Link
                  className="dwella-property-roster-item"
                  key={property.id}
                  to={`/properties?search=${encodeURIComponent(property.name)}`}
                >
                  <PropertyPhoto
                    src={property.cover_image}
                    name={property.name}
                  />
                  <div className="dwella-property-roster-copy">
                    <div>
                      <strong>{property.name}</strong>
                      <StatusBadge value={property.management_status} />
                    </div>
                    <p>{isPlatformAdmin ? property.organization_name : property.address || property.town || "Location not set"}</p>
                    <span>
                      {unitCount(property.units_count)}
                      {property.town ? ` / ${property.town}` : ""}
                    </span>
                  </div>
                  <ArrowRight20Regular className="dwella-property-roster-arrow" />
                </Link>
              ))}
              {!isLoading && data.recent_properties.length === 0 ? (
                <div className="dwella-dashboard-empty">
                  <strong>No properties yet</strong>
                  <p>{isPlatformAdmin ? "No landlord has added a property yet." : "Add a property to begin tracking units and rent."}</p>
                  {access.can_manage_properties ? (
                    <Button size="small" onClick={() => navigate("/properties?new=1")}>
                      Add property
                    </Button>
                  ) : null}
                </div>
              ) : null}
            </div>
          </section>

          <section className="dwella-rent-ladder">
            <SectionHeading
              title="Rent ladder"
              note="Highest monthly unit values"
            />
            <div className="dwella-rent-ladder-list">
              {data.top_units.map((unit, index) => (
                <div key={unit.id}>
                  <span className="dwella-rent-rank">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <strong>{unit.name}</strong>
                    <small>{unit.property_name}</small>
                  </div>
                  <StatusBadge value={unit.occupancy_status} />
                  <strong>{formatMoney(unit.rent_amount)}</strong>
                </div>
              ))}
              {!isLoading && data.top_units.length === 0 ? (
                <div className="dwella-dashboard-empty compact">
                  No units recorded yet.
                </div>
              ) : null}
            </div>
          </section>
        </div>

        <div className="dwella-dashboard-column">
          <section className="dwella-availability-board">
            <SectionHeading
              title="Unit availability"
              note={`${formatNumber(data.units.occupied)} of ${formatNumber(data.units.total)} units occupied`}
            />
            <ProgressBar value={occupancy / 100} thickness="large" />
            <div className="dwella-availability-list">
              {(data.units.by_status || []).map((status) => (
                <div key={status.key}>
                  <span className={`dwella-status-dot is-${status.key}`} />
                  <span>{status.label}</span>
                  <strong>{formatNumber(status.count)}</strong>
                  <small>{status.percentage}%</small>
                </div>
              ))}
              {!isLoading && !(data.units.by_status || []).length ? (
                <p className="dwella-board-empty">No units recorded yet.</p>
              ) : null}
            </div>
            <div className="dwella-average-rent">
              <span>Average unit rent</span>
              <strong>{formatMoney(data.finance.average_unit_rent)}</strong>
            </div>
          </section>

          <section className="dwella-portfolio-composition">
            <SectionHeading
              title="Portfolio composition"
              note={`Across ${formatNumber(data.portfolio.towns_count)} ${data.portfolio.towns_count === 1 ? "town" : "towns"}`}
            />
            <div className="dwella-composition-list">
              {data.properties.by_type.map((type) => (
                <div key={type.key}>
                  <div>
                    <span>{type.label}</span>
                    <strong>{formatNumber(type.count)}</strong>
                  </div>
                  <ProgressBar
                    value={
                      data.properties.total
                        ? type.count / data.properties.total
                        : 0
                    }
                  />
                </div>
              ))}
              {!isLoading && !data.properties.by_type.length ? (
                <p className="dwella-board-empty">No properties recorded yet.</p>
              ) : null}
            </div>
            <div className="dwella-management-summary">
              {(data.properties.by_status || []).map((status) => (
                <div key={status.key}>
                  <strong>{formatNumber(status.count)}</strong>
                  <span>{status.label}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
