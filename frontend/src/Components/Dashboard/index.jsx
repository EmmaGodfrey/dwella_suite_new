import React from "react";
import {
  Caption1,
  ProgressBar,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  Title2,
} from "@fluentui/react-components";
import {
  Building24Regular,
  BuildingRetailMoney24Regular,
  Home24Regular,
  Location24Regular,
  People24Regular,
  Pulse24Regular,
  Stack24Regular,
  ArrowTrending24Regular,
} from "@fluentui/react-icons";

import { useDashboardSummaryQuery } from "../../Services/queries";
import { MetricCard, PageSection, StatusBadge, labelize } from "../../shared/components";

const money = new Intl.NumberFormat("en-ZM", { style: "currency", currency: "ZMW", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("en-ZM");
const formatMoney = (value) => money.format(Number(value || 0));
const formatNumber = (value) => number.format(Number(value || 0));
const emptySummary = {
  organization: null,
  properties: { total: 0, managed: 0, by_status: [], by_type: [] },
  units: { total: 0, occupied: 0, vacant: 0, occupancy_rate: 0, by_status: [] },
  finance: { monthly_rent_roll: 0, occupied_rent_roll: 0, vacancy_loss: 0, average_unit_rent: 0 },
  portfolio: { towns_count: 0, average_units_per_property: 0 },
  recent_properties: [],
  top_units: [],
};

const Dashboard = () => {
  const { data = emptySummary, error, isLoading, isFetching } = useDashboardSummaryQuery();
  const organizationName = data.organization?.display_name || data.organization?.name || "No organization selected";

  return (
    <div className="dwella-screen dwella-dashboard">
      {error ? <div className="dwella-alert danger">Unable to load dashboard data: {error.message}</div> : null}
      <section className="dwella-metric-grid">
        <MetricCard icon={<Home24Regular />} label="Managed properties" value={isLoading ? "..." : formatNumber(data.properties.total)} detail={`${formatNumber(data.properties.managed)} managed in ${organizationName}`} />
        <MetricCard icon={<Stack24Regular />} label="Units" value={isLoading ? "..." : formatNumber(data.units.total)} detail={`${formatNumber(data.units.occupied)} occupied, ${formatNumber(data.units.vacant)} vacant`} />
        <MetricCard icon={<BuildingRetailMoney24Regular />} label="Monthly rent roll" value={isLoading ? "..." : formatMoney(data.finance.monthly_rent_roll)} detail={`${formatMoney(data.finance.occupied_rent_roll)} occupied rent`} />
        <MetricCard icon={<ArrowTrending24Regular />} label="Occupancy rate" value={isLoading ? "..." : `${data.units.occupancy_rate}%`} detail={`${formatMoney(data.finance.vacancy_loss)} vacancy exposure`} />
      </section>

      <section className="dwella-dashboard-grid">
        <PageSection title="Portfolio Health" note="Fast aggregate view from a single dashboard endpoint.">
          <div className="dwella-health-layout">
            <div className="dwella-health-meter">
              <div><Text>Occupancy</Text><Title2>{data.units.occupancy_rate}%</Title2></div>
              <ProgressBar value={(data.units.occupancy_rate || 0) / 100} />
            </div>
            <div className="dwella-mini-grid">
              <div><People24Regular /><Text>Avg rent</Text><strong>{formatMoney(data.finance.average_unit_rent)}</strong></div>
              <div><Building24Regular /><Text>Avg units/property</Text><strong>{data.portfolio.average_units_per_property}</strong></div>
              <div><Location24Regular /><Text>Active towns</Text><strong>{formatNumber(data.portfolio.towns_count)}</strong></div>
            </div>
          </div>
          <div className="dwella-status-stack">
            {data.units.by_status.map((status) => (
              <div className="dwella-status-row" key={status.key}>
                <div><Text>{status.label}</Text><strong>{formatNumber(status.count)}</strong></div>
                <ProgressBar value={(status.percentage || 0) / 100} />
              </div>
            ))}
          </div>
        </PageSection>

        <PageSection title="Property Mix" note="Type and management spread.">
          <div className="dwella-property-mix">
            {data.properties.by_type.map((type) => <div key={type.key}><Text>{type.label}</Text><strong>{formatNumber(type.count)}</strong></div>)}
          </div>
          <div className="dwella-chip-row">
            {data.properties.by_status.map((status) => <StatusBadge key={status.key} value={status.key}>{status.label}: {formatNumber(status.count)}</StatusBadge>)}
          </div>
        </PageSection>
      </section>

      <section className="dwella-dashboard-grid bottom">
        <PageSection title="Recent Properties" note={isFetching ? "Refreshing portfolio snapshot..." : "Newest portfolio records."}>
          <div className="dwella-table-wrap">
            <Table className="dwella-table" aria-label="Recent properties">
              <TableHeader>
                <TableRow><TableHeaderCell>Property</TableHeaderCell><TableHeaderCell>Type</TableHeaderCell><TableHeaderCell>Town</TableHeaderCell><TableHeaderCell>Units</TableHeaderCell><TableHeaderCell>Status</TableHeaderCell></TableRow>
              </TableHeader>
              <TableBody>
                {data.recent_properties.map((property) => (
                  <TableRow key={property.id}>
                    <TableCell><strong>{property.name}</strong><Caption1>{property.address}</Caption1></TableCell>
                    <TableCell>{labelize(property.property_type)}</TableCell>
                    <TableCell>{property.town || "Not set"}</TableCell>
                    <TableCell>{formatNumber(property.units_count)}</TableCell>
                    <TableCell><StatusBadge value={property.management_status} /></TableCell>
                  </TableRow>
                ))}
                {!isLoading && data.recent_properties.length === 0 ? <TableRow><TableCell>No properties yet.</TableCell></TableRow> : null}
              </TableBody>
            </Table>
          </div>
        </PageSection>

        <PageSection title="Highest Rent Units" note="Quick view of key revenue contributors.">
          <div className="dwella-unit-list">
            {data.top_units.map((unit) => (
              <div key={unit.id}>
                <span><Pulse24Regular /></span>
                <div><strong>{unit.name}</strong><Caption1>{unit.property_name}</Caption1></div>
                <aside><strong>{formatMoney(unit.rent_amount)}</strong><StatusBadge value={unit.occupancy_status} /></aside>
              </div>
            ))}
            {!isLoading && data.top_units.length === 0 ? <div className="dwella-empty-inline">No units yet.</div> : null}
          </div>
        </PageSection>
      </section>
    </div>
  );
};

export default Dashboard;
