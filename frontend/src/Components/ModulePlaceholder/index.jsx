import React, { Fragment } from "react";
import { Card, CardBody, Col, Container, Row } from "reactstrap";

import { Breadcrumbs, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";

const ModulePlaceholder = ({ title, description }) => (
  <Fragment>
    <Breadcrumbs mainTitle={title} parent="Dwella Suite" title={title} />
    <Container fluid={true}>
      <Row>
        <Col sm="12">
          <Card>
            <HeaderCard title={title} span1={description} />
            <CardBody>
              <P>
                This module is part of the Dwella Suite roadmap. Its backend app exists and will follow the same
                API client, TanStack Query, and template-component pattern as the dashboard and properties flow.
              </P>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  </Fragment>
);

export default ModulePlaceholder;
