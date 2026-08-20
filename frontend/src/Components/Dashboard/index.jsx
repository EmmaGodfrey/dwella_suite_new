import React, { Fragment } from "react";
import { Alert, Badge, Card, CardBody, Col, Container, Progress, Row, Table } from "reactstrap";
import { Activity, Briefcase, DollarSign, Home, Layers, MapPin, TrendingUp, Users } from "react-feather";

import { Breadcrumbs, H5, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
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
  properties: {
    total: 0,
    active: 0,
    managed: 0,
    prospect: 0,
    archived: 0,
    by_status: [],
    by_type: [],
  },
  units: {
    total: 0,
    occupied: 0,
    vacant: 0,
    maintenance: 0,
    reserved: 0,
    occupancy_rate: 0,
    by_status: [],
  },
  finance: {
    monthly_rent_roll: 0,
    occupied_rent_roll: 0,
    vacancy_loss: 0,
    average_unit_rent: 0,
  },
  portfolio: {
    towns_count: 0,
    average_units_per_property: 0,
  },
  recent_properties: [],
  top_units: [],
};

const MetricCard = ({ icon: Icon, label, value, detail, tone = "primary" }) => (
  <Card className="dwella-metric-card height-equal">
    <CardBody>
      <div className={`dwella-metric-icon bg-${tone}`}>
        <Icon color="#fff" size={18} />
      </div>
      <div className="dwella-metric-content">
        <P attrPara={{ className: "mb-1 text-muted" }}>{label}</P>
        <H5>{value}</H5>
        {detail ? <small className="text-muted">{detail}</small> : null}
      </div>
    </CardBody>
  </Card>
);

const StatusRow = ({ label, count, percentage }) => (
  <div className="dwella-status-row">
    <div>
      <span>{label}</span>
      <strong>{formatNumber(count)}</strong>
    </div>
    <Progress value={percentage || 0} />
  </div>
);

const Dashboard = () => {
  const { data = emptySummary, error, isLoading, isFetching } = useDashboardSummaryQuery();
  const organizationName = data.organization?.display_name || data.organization?.name || "No organization selected";

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Dashboard" parent="Dwella Suite" title="Dashboard" />
      <Container fluid={true} className="dwella-dashboard">
        {error ? <Alert color="danger">Unable to load dashboard data: {error.message}</Alert> : null}

        <Row className="align-items-stretch">
          <Col xxl="3" xl="6" md="6">
            <MetricCard
              icon={Home}
              label="Managed properties"
              value={isLoading ? "..." : formatNumber(data.properties.total)}
              detail={`${formatNumber(data.properties.managed)} managed · ${organizationName}`}
            />
          </Col>
          <Col xxl="3" xl="6" md="6">
            <MetricCard
              icon={Layers}
              label="Units"
              value={isLoading ? "..." : formatNumber(data.units.total)}
              detail={`${formatNumber(data.units.occupied)} occupied · ${formatNumber(data.units.vacant)} vacant`}
              tone="success"
            />
          </Col>
          <Col xxl="3" xl="6" md="6">
            <MetricCard
              icon={DollarSign}
              label="Monthly rent roll"
              value={isLoading ? "..." : formatMoney(data.finance.monthly_rent_roll)}
              detail={`${formatMoney(data.finance.occupied_rent_roll)} currently occupied`}
              tone="warning"
            />
          </Col>
          <Col xxl="3" xl="6" md="6">
            <MetricCard
              icon={TrendingUp}
              label="Occupancy rate"
              value={isLoading ? "..." : `${data.units.occupancy_rate}%`}
              detail={`${formatMoney(data.finance.vacancy_loss)} vacancy exposure`}
              tone="info"
            />
          </Col>
        </Row>

        <Row>
          <Col xl="8">
            <Card className="dwella-dashboard-panel">
              <HeaderCard title="Portfolio Health" span1="Fast aggregate view from a single dashboard endpoint." />
              <CardBody>
                <Row>
                  <Col md="6">
                    <div className="dwella-health-meter">
                      <div>
                        <span>Occupancy</span>
                        <strong>{data.units.occupancy_rate}%</strong>
                      </div>
                      <Progress value={data.units.occupancy_rate || 0} />
                    </div>
                    <div className="dwella-mini-grid">
                      <div>
                        <Users size={15} />
                        <span>Avg rent</span>
                        <strong>{formatMoney(data.finance.average_unit_rent)}</strong>
                      </div>
                      <div>
                        <Briefcase size={15} />
                        <span>Avg units/property</span>
                        <strong>{data.portfolio.average_units_per_property}</strong>
                      </div>
                      <div>
                        <MapPin size={15} />
                        <span>Active towns</span>
                        <strong>{formatNumber(data.portfolio.towns_count)}</strong>
                      </div>
                    </div>
                  </Col>
                  <Col md="6">
                    <div className="dwella-status-stack">
                      {data.units.by_status.map((status) => (
                        <StatusRow
                          key={status.key}
                          label={status.label}
                          count={status.count}
                          percentage={status.percentage}
                        />
                      ))}
                    </div>
                  </Col>
                </Row>
              </CardBody>
            </Card>
          </Col>

          <Col xl="4">
            <Card className="dwella-dashboard-panel">
              <HeaderCard title="Property Mix" span1="Type and management spread." />
              <CardBody>
                <div className="dwella-property-mix">
                  {data.properties.by_type.map((type) => (
                    <div key={type.key}>
                      <span>{type.label}</span>
                      <strong>{formatNumber(type.count)}</strong>
                    </div>
                  ))}
                </div>
                <div className="dwella-status-chips">
                  {data.properties.by_status.map((status) => (
                    <Badge key={status.key} color={status.key === "managed" ? "success" : "secondary"} pill>
                      {status.label}: {formatNumber(status.count)}
                    </Badge>
                  ))}
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>

        <Row>
          <Col xl="7">
            <Card className="dwella-dashboard-panel">
              <HeaderCard title="Recent Properties" span1={isFetching ? "Refreshing portfolio snapshot..." : "Newest portfolio records."} />
              <CardBody>
                <div className="table-responsive">
                  <Table className="table-borderless align-middle">
                    <thead>
                      <tr>
                        <th>Property</th>
                        <th>Type</th>
                        <th>Town</th>
                        <th>Units</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_properties.map((property) => (
                        <tr key={property.id}>
                          <td>
                            <span className="fw-semibold">{property.name}</span>
                            <small className="d-block text-muted">{property.address}</small>
                          </td>
                          <td>{labelize(property.property_type)}</td>
                          <td>{property.town || "Not set"}</td>
                          <td>{formatNumber(property.units_count)}</td>
                          <td>
                            <Badge color={property.management_status === "managed" ? "success" : "secondary"}>
                              {labelize(property.management_status)}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                      {!isLoading && data.recent_properties.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="text-center text-muted py-4">
                            No properties yet. Create one from the Properties section.
                          </td>
                        </tr>
                      ) : null}
                    </tbody>
                  </Table>
                </div>
              </CardBody>
            </Card>
          </Col>

          <Col xl="5">
            <Card className="dwella-dashboard-panel">
              <HeaderCard title="Highest Rent Units" span1="Quick view of key revenue contributors." />
              <CardBody>
                <div className="dwella-unit-list">
                  {data.top_units.map((unit) => (
                    <div key={unit.id}>
                      <div>
                        <Activity size={15} />
                        <span>
                          <strong>{unit.name}</strong>
                          <small>{unit.property_name}</small>
                        </span>
                      </div>
                      <div>
                        <strong>{formatMoney(unit.rent_amount)}</strong>
                        <Badge color={unit.occupancy_status === "occupied" ? "success" : "secondary"} pill>
                          {labelize(unit.occupancy_status)}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {!isLoading && data.top_units.length === 0 ? <div className="text-center text-muted py-4">No units yet.</div> : null}
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Dashboard;
