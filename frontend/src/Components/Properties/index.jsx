import React, { Fragment } from "react";
import { Alert, Badge, Card, CardBody, Col, Container, Row, Table } from "reactstrap";

import { Breadcrumbs } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
import { usePropertiesQuery } from "../../Services/queries";

const Properties = () => {
  const propertiesQuery = usePropertiesQuery();
  const properties = propertiesQuery.data?.results || [];

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Properties" parent="Portfolio" title="Properties" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title="Property Portfolio" span1="Manage buildings, homes, and commercial properties." />
              <CardBody>
                {propertiesQuery.isError ? (
                  <Alert color="danger">Unable to load properties: {propertiesQuery.error.message}</Alert>
                ) : null}
                <div className="table-responsive">
                  <Table hover>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Town</th>
                        <th>Province</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {properties.map((property) => (
                        <tr key={property.id}>
                          <td className="fw-semibold">{property.name}</td>
                          <td>{property.property_type?.replace("_", " ")}</td>
                          <td>{property.town || "Not set"}</td>
                          <td>{property.province || "Not set"}</td>
                          <td>
                            <Badge color={property.is_active ? "success" : "secondary"}>
                              {property.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                      {!propertiesQuery.isLoading && properties.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="text-center text-muted py-4">
                            No properties found.
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

export default Properties;
