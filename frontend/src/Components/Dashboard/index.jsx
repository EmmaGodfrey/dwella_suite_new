import React from "react";
import { Activity, Briefcase, DollarSign, Home, Layers, MapPin, TrendingUp, Users } from "react-feather";

import { useDashboardSummaryQuery } from "../../Services/queries";

const money = new Intl.NumberFormat("en-ZM", {
  style: "currency",
  currency: "ZMW",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("en-ZM");
const formatMoney = (value) => money.format(Number(value || 0));
const formatNumber = (value) => number.format(Number(value || 0));
const labelize = (value) => String(value || "Not set").replace(/_/g, " ");

const emptySummary = {
  organization: null,
  properties: { total: 0, managed: 0, by_status: [], by_type: [] },
  units: { total: 0, occupied: 0, vacant: 0, occupancy_rate: 0, by_status: [] },
  finance: { monthly_rent_roll: 0, occupied_rent_roll: 0, vacancy_loss: 0, average_unit_rent: 0 },
  portfolio: { towns_count: 0, average_units_per_property: 0 },
  recent_properties: [],
  top_units: [],
};

const MetricCard = ({ icon: Icon, label, value, detail, tone = "" }) => (
  <article className={`dwella-card dwella-metric ${tone}`}>
    <span className="dwella-metric-icon">
      <Icon size={18} />
    </span>
    <p>{label}</p>
    <strong>{value}</strong>
    <small>{detail}</small>
  </article>
);

const Panel = ({ title, note, children }) => (
  <section className="dwella-card dwella-panel">
    <header>
      <div>
        <h2>{title}</h2>
        {note ? <p>{note}</p> : null}
      </div>
    </header>
    {children}
  </section>
);

const Dashboard = () => {
  const { data = emptySummary, error, isLoading, isFetching } = useDashboardSummaryQuery();
  const organizationName = data.organization?.display_name || data.organization?.name || "No organization selected";

  return (
    <div className="dwella-screen dwella-dashboard">
      {error ? <div className="dwella-alert danger">Unable to load dashboard data: {error.message}</div> : null}

      <section className="dwella-metric-grid">
        <MetricCard icon={Home} label="Managed properties" value={isLoading ? "..." : formatNumber(data.properties.total)} detail={`${formatNumber(data.properties.managed)} managed in ${organizationName}`} />
        <MetricCard icon={Layers} label="Units" value={isLoading ? "..." : formatNumber(data.units.total)} detail={`${formatNumber(data.units.occupied)} occupied, ${formatNumber(data.units.vacant)} vacant`} tone="green" />
        <MetricCard icon={DollarSign} label="Monthly rent roll" value={isLoading ? "..." : formatMoney(data.finance.monthly_rent_roll)} detail={`${formatMoney(data.finance.occupied_rent_roll)} occupied rent`} tone="gold" />
        <MetricCard icon={TrendingUp} label="Occupancy rate" value={isLoading ? "..." : `${data.units.occupancy_rate}%`} detail={`${formatMoney(data.finance.vacancy_loss)} vacancy exposure`} tone="blue" />
      </section>

      <section className="dwella-dashboard-grid">
        <Panel title="Portfolio Health" note="Fast aggregate view from a single dashboard endpoint.">
          <div className="dwella-health-layout">
            <div className="dwella-health-meter">
              <div>
                <span>Occupancy</span>
                <strong>{data.units.occupancy_rate}%</strong>
              </div>
              <progress value={data.units.occupancy_rate || 0} max="100" />
            </div>
            <div className="dwella-mini-grid">
              <div><Users size={15} /><span>Avg rent</span><strong>{formatMoney(data.finance.average_unit_rent)}</strong></div>
              <div><Briefcase size={15} /><span>Avg units/property</span><strong>{data.portfolio.average_units_per_property}</strong></div>
              <div><MapPin size={15} /><span>Active towns</span><strong>{formatNumber(data.portfolio.towns_count)}</strong></div>
            </div>
          </div>
          <div className="dwella-status-stack">
            {data.units.by_status.map((status) => (
              <div className="dwella-status-row" key={status.key}>
                <div><span>{status.label}</span><strong>{formatNumber(status.count)}</strong></div>
                <progress value={status.percentage || 0} max="100" />
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Property Mix" note="Type and management spread.">
          <div className="dwella-property-mix">
            {data.properties.by_type.map((type) => (
              <div key={type.key}><span>{type.label}</span><strong>{formatNumber(type.count)}</strong></div>
            ))}
          </div>
          <div className="dwella-chip-row">
            {data.properties.by_status.map((status) => (
              <span className={`dwella-chip ${status.key}`} key={status.key}>{status.label}: {formatNumber(status.count)}</span>
            ))}
          </div>
        </Panel>
      </section>

      <section className="dwella-dashboard-grid bottom">
        <Panel title="Recent Properties" note={isFetching ? "Refreshing portfolio snapshot..." : "Newest portfolio records."}>
          <div className="dwella-table-wrap">
            <table className="dwella-table">
              <thead>
                <tr><th>Property</th><th>Type</th><th>Town</th><th>Units</th><th>Status</th></tr>
              </thead>
              <tbody>
                {data.recent_properties.map((property) => (
                  <tr key={property.id}>
                    <td><strong>{property.name}</strong><small>{property.address}</small></td>
                    <td>{labelize(property.property_type)}</td>
                    <td>{property.town || "Not set"}</td>
                    <td>{formatNumber(property.units_count)}</td>
                    <td><span className={`dwella-chip ${property.management_status}`}>{labelize(property.management_status)}</span></td>
                  </tr>
                ))}
                {!isLoading && data.recent_properties.length === 0 ? <tr><td colSpan="5">No properties yet.</td></tr> : null}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Highest Rent Units" note="Quick view of key revenue contributors.">
          <div className="dwella-unit-list">
            {data.top_units.map((unit) => (
              <div key={unit.id}>
                <span><Activity size={15} /></span>
                <div><strong>{unit.name}</strong><small>{unit.property_name}</small></div>
                <aside><strong>{formatMoney(unit.rent_amount)}</strong><em>{labelize(unit.occupancy_status)}</em></aside>
              </div>
            ))}
            {!isLoading && data.top_units.length === 0 ? <div className="dwella-empty-inline">No units yet.</div> : null}
          </div>
        </Panel>
      </section>
    </div>
  );
};

export default Dashboard;
