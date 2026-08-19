import React, { Fragment } from "react";
import { Alert, Badge, Card, CardBody, Col, Container, Row, Table } from "reactstrap";
import { Home, Layers, Users } from "react-feather";

import { Breadcrumbs, H5, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
import { useCurrentUserQuery, usePropertiesQuery, useUnitsQuery } from "../../Services/queries";

const money = new Intl.NumberFormat("en-ZM", {
  style: "currency",
  currency: "ZMW",
});

const MetricCard = ({ icon: Icon, label, value, detail }) => (
  <Card className="height-equal">
    <CardBody className="d-flex align-items-center gap-3">
      <div className="bg-primary rounded-circle d-flex align-items-center justify-content-center" style={{ width: 42, height: 42 }}>
        <Icon color="#fff" size={20} />
      </div>
      <div>
        <P attrPara={{ className: "mb-1 text-muted" }}>{label}</P>
        <H5>{value}</H5>
        {detail ? <small className="text-muted">{detail}</small> : null}
      </div>
    </CardBody>
  </Card>
);

const Dashboard = () => {
  const currentUserQuery = useCurrentUserQuery();
  const propertiesQuery = usePropertiesQuery();
  const unitsQuery = useUnitsQuery();

  const properties = propertiesQuery.data?.results || [];
  const units = unitsQuery.data?.results || [];
  const occupiedUnits = units.filter((unit) => unit.occupancy_status === "occupied").length;
  const monthlyRent = units.reduce((sum, unit) => sum + Number(unit.rent_amount || 0), 0);
  const activeOrganization = currentUserQuery.data?.memberships?.[0]?.organization;

  const isLoading = currentUserQuery.isLoading || propertiesQuery.isLoading || unitsQuery.isLoading;
  const error = currentUserQuery.error || propertiesQuery.error || unitsQuery.error;

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Dashboard" parent="Dwella Suite" title="Dashboard" />
      <Container fluid={true}>
        {error ? (
          <Alert color="danger">Unable to load dashboard data: {error.message}</Alert>
        ) : null}

        <Row>
          <Col xl="4" md="6">
            <MetricCard
              icon={Home}
              label="Managed properties"
              value={isLoading ? "..." : properties.length}
              detail={activeOrganization?.display_name || activeOrganization?.name || "No organization selected"}
            />
          </Col>
          <Col xl="4" md="6">
            <MetricCard
              icon={Layers}
              label="Units"
              value={isLoading ? "..." : units.length}
              detail={`${occupiedUnits} occupied`}
            />
          </Col>
          <Col xl="4" md="6">
            <MetricCard
              icon={Users}
              label="Monthly rent roll"
              value={isLoading ? "..." : money.format(monthlyRent)}
              detail="Based on listed units"
            />
          </Col>
        </Row>

        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title="Properties" span1="Live data from the Django properties endpoint." />
              <CardBody>
                <div className="table-responsive">
                  <Table className="table-borderless align-middle">
                    <thead>
                      <tr>
                        <th>Property</th>
                        <th>Type</th>
                        <th>Town</th>
                        <th>Status</th>
                        <th>Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      {properties.map((property) => (
                        <tr key={property.id}>
                          <td className="fw-semibold">{property.name}</td>
                          <td>{property.property_type?.replace("_", " ")}</td>
                          <td>{property.town || "Not set"}</td>
                          <td>
                            <Badge color={property.management_status === "managed" ? "success" : "secondary"}>
                              {property.management_status}
                            </Badge>
                          </td>
                          <td>{property.address}</td>
                        </tr>
                      ))}
                      {!isLoading && properties.length === 0 ? (
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
        </Row>
      </Container>
    </Fragment>
  );
};

export default Dashboard;
