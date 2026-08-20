import React, { Fragment, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  ButtonGroup,
  Card,
  CardBody,
  Col,
  Container,
  Form,
  FormGroup,
  Input,
  Label,
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Row,
  Table,
} from "reactstrap";
import { Grid, Home, List, MapPin, Plus, Search, Sliders, X } from "react-feather";
import { toast } from "react-toastify";

import { Breadcrumbs, H5, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
import { useCreatePropertyMutation } from "../../Services/mutations";
import { usePropertiesQuery } from "../../Services/queries";

const initialForm = {
  name: "",
  property_type: "apartment",
  management_status: "managed",
  address: "",
  town: "",
  province: "",
  description: "",
};

const propertyTypes = [
  { value: "", label: "All types" },
  { value: "apartment", label: "Apartment" },
  { value: "house", label: "House" },
  { value: "commercial", label: "Commercial" },
  { value: "mixed_use", label: "Mixed Use" },
  { value: "land", label: "Land" },
];

const managementStatuses = [
  { value: "", label: "All statuses" },
  { value: "managed", label: "Managed" },
  { value: "prospect", label: "Prospect" },
  { value: "archived", label: "Archived" },
];

const labelize = (value) => String(value || "Not set").replace(/_/g, " ");

const statusColor = (status) => {
  if (status === "managed") return "success";
  if (status === "prospect") return "warning";
  return "secondary";
};

const Properties = () => {
  const [filters, setFilters] = useState({
    search: "",
    property_type: "",
    management_status: "",
    ordering: "name",
  });
  const [viewMode, setViewMode] = useState("cards");
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(initialForm);

  const propertiesQuery = usePropertiesQuery(filters, {
    placeholderData: (previousData) => previousData,
    staleTime: 45_000,
  });
  const properties = propertiesQuery.data?.results || [];
  const pagination = propertiesQuery.data?.pagination;

  const createPropertyMutation = useCreatePropertyMutation({
    onSuccess: () => {
      toast.success("Property added.");
      setModalOpen(false);
      setForm(initialForm);
    },
    onError: (error) => toast.error(error.message || "Could not add property"),
  });

  const metrics = useMemo(() => {
    const managed = properties.filter((property) => property.management_status === "managed").length;
    const prospects = properties.filter((property) => property.management_status === "prospect").length;
    const towns = new Set(properties.map((property) => property.town).filter(Boolean));

    return {
      total: pagination?.count ?? properties.length,
      managed,
      prospects,
      towns: towns.size,
    };
  }, [pagination?.count, properties]);

  const updateFilter = (key, value) => {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const resetFilters = () => {
    setFilters({
      search: "",
      property_type: "",
      management_status: "",
      ordering: "name",
    });
  };

  const updateForm = (key, value) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const submitProperty = (event) => {
    event.preventDefault();
    if (!form.name.trim()) {
      toast.error("Property name is required.");
      return;
    }
    if (!form.address.trim()) {
      toast.error("Address is required.");
      return;
    }

    createPropertyMutation.mutate({
      ...form,
      name: form.name.trim(),
      address: form.address.trim(),
      town: form.town.trim(),
      province: form.province.trim(),
      description: form.description.trim(),
    });
  };

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Properties" parent="Portfolio" title="Properties" />
      <Container fluid={true} className="dwella-properties">
        <Row>
          <Col xl="3" sm="6">
            <Card className="dwella-property-stat">
              <CardBody>
                <Home size={18} />
                <span>Total properties</span>
                <H5>{propertiesQuery.isLoading ? "..." : metrics.total}</H5>
              </CardBody>
            </Card>
          </Col>
          <Col xl="3" sm="6">
            <Card className="dwella-property-stat">
              <CardBody>
                <Sliders size={18} />
                <span>Managed</span>
                <H5>{propertiesQuery.isLoading ? "..." : metrics.managed}</H5>
              </CardBody>
            </Card>
          </Col>
          <Col xl="3" sm="6">
            <Card className="dwella-property-stat">
              <CardBody>
                <Plus size={18} />
                <span>Prospects</span>
                <H5>{propertiesQuery.isLoading ? "..." : metrics.prospects}</H5>
              </CardBody>
            </Card>
          </Col>
          <Col xl="3" sm="6">
            <Card className="dwella-property-stat">
              <CardBody>
                <MapPin size={18} />
                <span>Towns</span>
                <H5>{propertiesQuery.isLoading ? "..." : metrics.towns}</H5>
              </CardBody>
            </Card>
          </Col>
        </Row>

        <Row>
          <Col sm="12">
            <Card className="dwella-properties-panel">
              <HeaderCard title="Property Portfolio" span1="Search, filter, and manage buildings, homes, and commercial sites." />
              <CardBody>
                {propertiesQuery.isError ? (
                  <Alert color="danger">Unable to load properties: {propertiesQuery.error.message}</Alert>
                ) : null}

                <div className="dwella-property-toolbar">
                  <div className="dwella-property-search">
                    <Search size={15} />
                    <Input
                      value={filters.search}
                      onChange={(event) => updateFilter("search", event.target.value)}
                      placeholder="Search name, address, town..."
                    />
                  </div>
                  <Input
                    type="select"
                    value={filters.property_type}
                    onChange={(event) => updateFilter("property_type", event.target.value)}
                  >
                    {propertyTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </Input>
                  <Input
                    type="select"
                    value={filters.management_status}
                    onChange={(event) => updateFilter("management_status", event.target.value)}
                  >
                    {managementStatuses.map((status) => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </Input>
                  <Input type="select" value={filters.ordering} onChange={(event) => updateFilter("ordering", event.target.value)}>
                    <option value="name">Name A-Z</option>
                    <option value="-created_at">Newest</option>
                    <option value="management_status">Status</option>
                  </Input>
                  <Button color="light" className="dwella-icon-button" onClick={resetFilters} type="button">
                    <X size={16} />
                  </Button>
                  <ButtonGroup>
                    <Button
                      color={viewMode === "cards" ? "primary" : "light"}
                      className="dwella-icon-button"
                      onClick={() => setViewMode("cards")}
                      type="button"
                    >
                      <Grid size={16} />
                    </Button>
                    <Button
                      color={viewMode === "table" ? "primary" : "light"}
                      className="dwella-icon-button"
                      onClick={() => setViewMode("table")}
                      type="button"
                    >
                      <List size={16} />
                    </Button>
                  </ButtonGroup>
                  <Button color="primary" className="dwella-property-add" onClick={() => setModalOpen(true)} type="button">
                    <Plus size={16} />
                    Add Property
                  </Button>
                </div>

                {viewMode === "cards" ? (
                  <div className="dwella-property-grid">
                    {properties.map((property) => (
                      <article className="dwella-property-card" key={property.id}>
                        <div>
                          <span>{labelize(property.property_type)}</span>
                          <Badge color={statusColor(property.management_status)} pill>
                            {labelize(property.management_status)}
                          </Badge>
                        </div>
                        <H5>{property.name}</H5>
                        <P attrPara={{ className: "mb-2" }}>{property.address}</P>
                        <small>
                          {[property.town, property.province].filter(Boolean).join(", ") || "Location not set"}
                        </small>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="table-responsive">
                    <Table hover className="align-middle">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Type</th>
                          <th>Town</th>
                          <th>Province</th>
                          <th>Status</th>
                          <th>Active</th>
                        </tr>
                      </thead>
                      <tbody>
                        {properties.map((property) => (
                          <tr key={property.id}>
                            <td>
                              <span className="fw-semibold">{property.name}</span>
                              <small className="d-block text-muted">{property.address}</small>
                            </td>
                            <td>{labelize(property.property_type)}</td>
                            <td>{property.town || "Not set"}</td>
                            <td>{property.province || "Not set"}</td>
                            <td>
                              <Badge color={statusColor(property.management_status)}>{labelize(property.management_status)}</Badge>
                            </td>
                            <td>
                              <Badge color={property.is_active ? "success" : "secondary"}>
                                {property.is_active ? "Active" : "Inactive"}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                )}

                {!propertiesQuery.isLoading && properties.length === 0 ? (
                  <div className="dwella-empty-state">
                    <Home size={24} />
                    <H5>No properties found</H5>
                    <P>Add your first managed property or clear filters to see more records.</P>
                    <Button color="primary" onClick={() => setModalOpen(true)} type="button">
                      <Plus size={16} />
                      Add Property
                    </Button>
                  </div>
                ) : null}
              </CardBody>
            </Card>
          </Col>
        </Row>

        <Modal isOpen={modalOpen} toggle={() => setModalOpen((value) => !value)} centered className="dwella-themed-modal">
          <Form onSubmit={submitProperty}>
            <ModalHeader toggle={() => setModalOpen(false)}>Add Property</ModalHeader>
            <ModalBody>
              <Row>
                <Col md="12">
                  <FormGroup>
                    <Label>Property name</Label>
                    <Input value={form.name} onChange={(event) => updateForm("name", event.target.value)} />
                  </FormGroup>
                </Col>
                <Col md="6">
                  <FormGroup>
                    <Label>Type</Label>
                    <Input type="select" value={form.property_type} onChange={(event) => updateForm("property_type", event.target.value)}>
                      {propertyTypes.filter((type) => type.value).map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </Input>
                  </FormGroup>
                </Col>
                <Col md="6">
                  <FormGroup>
                    <Label>Status</Label>
                    <Input
                      type="select"
                      value={form.management_status}
                      onChange={(event) => updateForm("management_status", event.target.value)}
                    >
                      {managementStatuses.filter((status) => status.value).map((status) => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </Input>
                  </FormGroup>
                </Col>
                <Col md="12">
                  <FormGroup>
                    <Label>Address</Label>
                    <Input value={form.address} onChange={(event) => updateForm("address", event.target.value)} />
                  </FormGroup>
                </Col>
                <Col md="6">
                  <FormGroup>
                    <Label>Town</Label>
                    <Input value={form.town} onChange={(event) => updateForm("town", event.target.value)} />
                  </FormGroup>
                </Col>
                <Col md="6">
                  <FormGroup>
                    <Label>Province</Label>
                    <Input value={form.province} onChange={(event) => updateForm("province", event.target.value)} />
                  </FormGroup>
                </Col>
                <Col md="12">
                  <FormGroup>
                    <Label>Description</Label>
                    <Input
                      type="textarea"
                      rows="3"
                      value={form.description}
                      onChange={(event) => updateForm("description", event.target.value)}
                    />
                  </FormGroup>
                </Col>
              </Row>
            </ModalBody>
            <ModalFooter>
              <Button color="light" type="button" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button color="primary" type="submit" disabled={createPropertyMutation.isPending}>
                {createPropertyMutation.isPending ? "Saving..." : "Save Property"}
              </Button>
            </ModalFooter>
          </Form>
        </Modal>
      </Container>
    </Fragment>
  );
};

export default Properties;
