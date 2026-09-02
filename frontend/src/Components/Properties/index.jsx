import React, { useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Caption1,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Dropdown,
  Field,
  Input,
  Option,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  Textarea,
  Title2,
  Title3,
} from "@fluentui/react-components";
import { Add24Regular, Building24Regular, Dismiss24Regular, Grid24Regular, Location24Regular, Search24Regular, Table24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCreatePropertyMutation } from "../../Services/mutations";
import { usePropertiesQuery } from "../../Services/queries";

const initialForm = { name: "", property_type: "apartment", management_status: "managed", address: "", town: "", province: "", description: "" };
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
const orderOptions = [
  { value: "name", label: "Name A-Z" },
  { value: "-created_at", label: "Newest" },
  { value: "management_status", label: "Status" },
];

const labelize = (value) => String(value || "Not set").replace(/_/g, " ");
const optionLabel = (items, value) => items.find((item) => item.value === value)?.label || "";
const statusIntent = (value) => value === "managed" ? "success" : value === "prospect" ? "warning" : "subtle";

const Stat = ({ icon: Icon, label, value }) => (
  <Card className="dwella-card dwella-property-stat" appearance="outline">
    <Icon />
    <Text size={200}>{label}</Text>
    <Title2>{value}</Title2>
  </Card>
);

const Properties = () => {
  const [filters, setFilters] = useState({ search: "", property_type: "", management_status: "", ordering: "name" });
  const [viewMode, setViewMode] = useState("cards");
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(initialForm);

  const propertiesQuery = usePropertiesQuery(filters, { placeholderData: (previousData) => previousData, staleTime: 45_000 });
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
    return { total: pagination?.count ?? properties.length, managed, prospects, towns: towns.size };
  }, [pagination?.count, properties]);

  const updateFilter = (key, value) => setFilters((current) => ({ ...current, [key]: value }));
  const updateForm = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const resetFilters = () => setFilters({ search: "", property_type: "", management_status: "", ordering: "name" });
  const dropdownHandler = (key) => (_, data) => updateFilter(key, data.optionValue ?? "");

  const submitProperty = (event) => {
    event.preventDefault();
    if (!form.name.trim()) return toast.error("Property name is required.");
    if (!form.address.trim()) return toast.error("Address is required.");
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
    <div className="dwella-screen dwella-properties-screen">
      <section className="dwella-metric-grid">
        <Stat icon={Building24Regular} label="Total properties" value={propertiesQuery.isLoading ? "..." : metrics.total} />
        <Stat icon={Grid24Regular} label="Managed" value={propertiesQuery.isLoading ? "..." : metrics.managed} />
        <Stat icon={Add24Regular} label="Prospects" value={propertiesQuery.isLoading ? "..." : metrics.prospects} />
        <Stat icon={Location24Regular} label="Towns" value={propertiesQuery.isLoading ? "..." : metrics.towns} />
      </section>

      <Card className="dwella-card dwella-panel" appearance="outline">
        <header className="dwella-panel-heading">
          <div><Title3 as="h2">Property Portfolio</Title3><Text size={200}>Search, filter, and manage buildings, homes, and commercial sites.</Text></div>
          <Button appearance="primary" icon={<Add24Regular />} onClick={() => setModalOpen(true)}>Add Property</Button>
        </header>

        {propertiesQuery.isError ? <div className="dwella-alert danger">Unable to load properties: {propertiesQuery.error.message}</div> : null}

        <div className="dwella-property-toolbar">
          <Input contentBefore={<Search24Regular />} value={filters.search} onChange={(_, data) => updateFilter("search", data.value)} placeholder="Search name, address, town..." />
          <Dropdown selectedOptions={[filters.property_type]} value={optionLabel(propertyTypes, filters.property_type)} onOptionSelect={dropdownHandler("property_type")}>{propertyTypes.map((type) => <Option key={type.value || "all"} value={type.value}>{type.label}</Option>)}</Dropdown>
          <Dropdown selectedOptions={[filters.management_status]} value={optionLabel(managementStatuses, filters.management_status)} onOptionSelect={dropdownHandler("management_status")}>{managementStatuses.map((status) => <Option key={status.value || "all"} value={status.value}>{status.label}</Option>)}</Dropdown>
          <Dropdown selectedOptions={[filters.ordering]} value={optionLabel(orderOptions, filters.ordering)} onOptionSelect={dropdownHandler("ordering")}>{orderOptions.map((option) => <Option key={option.value} value={option.value}>{option.label}</Option>)}</Dropdown>
          <Button appearance="subtle" icon={<Dismiss24Regular />} onClick={resetFilters} aria-label="Clear filters" />
          <div className="dwella-segment">
            <Button appearance={viewMode === "cards" ? "primary" : "subtle"} icon={<Grid24Regular />} onClick={() => setViewMode("cards")} aria-label="Card view" />
            <Button appearance={viewMode === "table" ? "primary" : "subtle"} icon={<Table24Regular />} onClick={() => setViewMode("table")} aria-label="Table view" />
          </div>
        </div>

        {viewMode === "cards" ? (
          <div className="dwella-property-grid">
            {properties.map((property) => (
              <Card className="dwella-property-card" key={property.id} appearance="filled-alternative">
                <div><Caption1>{labelize(property.property_type)}</Caption1><Badge appearance="tint" color={statusIntent(property.management_status)}>{labelize(property.management_status)}</Badge></div>
                <Title3 as="h3">{property.name}</Title3>
                <Text>{property.address}</Text>
                <Caption1>{[property.town, property.province].filter(Boolean).join(", ") || "Location not set"}</Caption1>
              </Card>
            ))}
          </div>
        ) : (
          <div className="dwella-table-wrap">
            <Table className="dwella-table" aria-label="Properties">
              <TableHeader><TableRow><TableHeaderCell>Name</TableHeaderCell><TableHeaderCell>Type</TableHeaderCell><TableHeaderCell>Town</TableHeaderCell><TableHeaderCell>Province</TableHeaderCell><TableHeaderCell>Status</TableHeaderCell><TableHeaderCell>Active</TableHeaderCell></TableRow></TableHeader>
              <TableBody>
                {properties.map((property) => (
                  <TableRow key={property.id}>
                    <TableCell><strong>{property.name}</strong><Caption1>{property.address}</Caption1></TableCell>
                    <TableCell>{labelize(property.property_type)}</TableCell>
                    <TableCell>{property.town || "Not set"}</TableCell>
                    <TableCell>{property.province || "Not set"}</TableCell>
                    <TableCell><Badge appearance="tint" color={statusIntent(property.management_status)}>{labelize(property.management_status)}</Badge></TableCell>
                    <TableCell><Badge appearance="tint" color={property.is_active ? "success" : "subtle"}>{property.is_active ? "Active" : "Inactive"}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {!propertiesQuery.isLoading && properties.length === 0 ? (
          <div className="dwella-empty-state"><Building24Regular /><Title3>No properties found</Title3><Text>Add your first managed property or clear filters to see more records.</Text><Button appearance="primary" icon={<Add24Regular />} onClick={() => setModalOpen(true)}>Add Property</Button></div>
        ) : null}
      </Card>

      <Dialog open={modalOpen} onOpenChange={(_, data) => setModalOpen(data.open)}>
        <DialogSurface className="dwella-fluent-dialog">
          <form onSubmit={submitProperty}>
            <DialogBody>
              <DialogTitle>Add Property</DialogTitle>
              <DialogContent>
                <div className="dwella-form-grid">
                  <Field label="Property name"><Input value={form.name} onChange={(_, data) => updateForm("name", data.value)} /></Field>
                  <Field label="Type"><Dropdown selectedOptions={[form.property_type]} value={optionLabel(propertyTypes, form.property_type)} onOptionSelect={(_, data) => updateForm("property_type", data.optionValue)}>{propertyTypes.filter((type) => type.value).map((type) => <Option key={type.value} value={type.value}>{type.label}</Option>)}</Dropdown></Field>
                  <Field label="Status"><Dropdown selectedOptions={[form.management_status]} value={optionLabel(managementStatuses, form.management_status)} onOptionSelect={(_, data) => updateForm("management_status", data.optionValue)}>{managementStatuses.filter((status) => status.value).map((status) => <Option key={status.value} value={status.value}>{status.label}</Option>)}</Dropdown></Field>
                  <Field label="Address"><Input value={form.address} onChange={(_, data) => updateForm("address", data.value)} /></Field>
                  <Field label="Town"><Input value={form.town} onChange={(_, data) => updateForm("town", data.value)} /></Field>
                  <Field label="Province"><Input value={form.province} onChange={(_, data) => updateForm("province", data.value)} /></Field>
                  <Field label="Description"><Textarea rows={3} value={form.description} onChange={(_, data) => updateForm("description", data.value)} /></Field>
                </div>
              </DialogContent>
              <DialogActions>
                <Button appearance="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
                <Button appearance="primary" type="submit" disabled={createPropertyMutation.isPending}>{createPropertyMutation.isPending ? "Saving..." : "Save Property"}</Button>
              </DialogActions>
            </DialogBody>
          </form>
        </DialogSurface>
      </Dialog>
    </div>
  );
};

export default Properties;
