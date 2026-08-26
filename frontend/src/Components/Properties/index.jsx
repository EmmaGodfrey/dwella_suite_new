import React, { useEffect, useMemo, useState } from "react";
import { Grid, Home, List, MapPin, Plus, Search, Sliders, X } from "react-feather";
import { toast } from "react-toastify";

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

const Stat = ({ icon: Icon, label, value }) => (
  <article className="dwella-card dwella-property-stat">
    <Icon size={18} />
    <span>{label}</span>
    <strong>{value}</strong>
  </article>
);

const Field = ({ label, children }) => (
  <label className="dwella-field">
    <span>{label}</span>
    {children}
  </label>
);

const Properties = () => {
  const [filters, setFilters] = useState({ search: "", property_type: "", management_status: "", ordering: "name" });
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
    return { total: pagination?.count ?? properties.length, managed, prospects, towns: towns.size };
  }, [pagination?.count, properties]);

  const updateFilter = (key, value) => setFilters((current) => ({ ...current, [key]: value }));
  const updateForm = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const resetFilters = () => setFilters({ search: "", property_type: "", management_status: "", ordering: "name" });

  useEffect(() => {
    if (!modalOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setModalOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [modalOpen]);

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
        <Stat icon={Home} label="Total properties" value={propertiesQuery.isLoading ? "..." : metrics.total} />
        <Stat icon={Sliders} label="Managed" value={propertiesQuery.isLoading ? "..." : metrics.managed} />
        <Stat icon={Plus} label="Prospects" value={propertiesQuery.isLoading ? "..." : metrics.prospects} />
        <Stat icon={MapPin} label="Towns" value={propertiesQuery.isLoading ? "..." : metrics.towns} />
      </section>

      <section className="dwella-card dwella-panel">
        <header className="dwella-panel-heading">
          <div>
            <h2>Property Portfolio</h2>
            <p>Search, filter, and manage buildings, homes, and commercial sites.</p>
          </div>
          <button className="dwella-primary-action compact" type="button" onClick={() => setModalOpen(true)}>
            <Plus size={16} />
            Add Property
          </button>
        </header>

        {propertiesQuery.isError ? <div className="dwella-alert danger">Unable to load properties: {propertiesQuery.error.message}</div> : null}

        <div className="dwella-property-toolbar">
          <label className="dwella-search-field">
            <Search size={15} />
            <input value={filters.search} onChange={(event) => updateFilter("search", event.target.value)} placeholder="Search name, address, town..." />
          </label>
          <select value={filters.property_type} onChange={(event) => updateFilter("property_type", event.target.value)}>
            {propertyTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
          <select value={filters.management_status} onChange={(event) => updateFilter("management_status", event.target.value)}>
            {managementStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
          </select>
          <select value={filters.ordering} onChange={(event) => updateFilter("ordering", event.target.value)}>
            <option value="name">Name A-Z</option>
            <option value="-created_at">Newest</option>
            <option value="management_status">Status</option>
          </select>
          <button className="dwella-icon-button" onClick={resetFilters} type="button" aria-label="Clear filters"><X size={16} /></button>
          <div className="dwella-segment">
            <button className={viewMode === "cards" ? "active" : ""} onClick={() => setViewMode("cards")} type="button" aria-label="Card view"><Grid size={16} /></button>
            <button className={viewMode === "table" ? "active" : ""} onClick={() => setViewMode("table")} type="button" aria-label="Table view"><List size={16} /></button>
          </div>
        </div>

        {viewMode === "cards" ? (
          <div className="dwella-property-grid">
            {properties.map((property) => (
              <article className="dwella-property-card" key={property.id}>
                <div><span>{labelize(property.property_type)}</span><em className={property.management_status}>{labelize(property.management_status)}</em></div>
                <h3>{property.name}</h3>
                <p>{property.address}</p>
                <small>{[property.town, property.province].filter(Boolean).join(", ") || "Location not set"}</small>
              </article>
            ))}
          </div>
        ) : (
          <div className="dwella-table-wrap">
            <table className="dwella-table">
              <thead><tr><th>Name</th><th>Type</th><th>Town</th><th>Province</th><th>Status</th><th>Active</th></tr></thead>
              <tbody>
                {properties.map((property) => (
                  <tr key={property.id}>
                    <td><strong>{property.name}</strong><small>{property.address}</small></td>
                    <td>{labelize(property.property_type)}</td>
                    <td>{property.town || "Not set"}</td>
                    <td>{property.province || "Not set"}</td>
                    <td><span className={`dwella-chip ${property.management_status}`}>{labelize(property.management_status)}</span></td>
                    <td><span className={`dwella-chip ${property.is_active ? "managed" : "archived"}`}>{property.is_active ? "Active" : "Inactive"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!propertiesQuery.isLoading && properties.length === 0 ? (
          <div className="dwella-empty-state">
            <Home size={24} />
            <h3>No properties found</h3>
            <p>Add your first managed property or clear filters to see more records.</p>
            <button className="dwella-primary-action compact" onClick={() => setModalOpen(true)} type="button"><Plus size={16} />Add Property</button>
          </div>
        ) : null}
      </section>

      {modalOpen ? (
        <div className="dwella-modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setModalOpen(false)}>
          <form className="dwella-modal" onSubmit={submitProperty}>
            <header>
              <div><h2>Add Property</h2><p>Create a new portfolio record.</p></div>
              <button type="button" onClick={() => setModalOpen(false)} aria-label="Close modal"><X size={18} /></button>
            </header>
            <div className="dwella-form-grid">
              <Field label="Property name"><input value={form.name} onChange={(event) => updateForm("name", event.target.value)} /></Field>
              <Field label="Type"><select value={form.property_type} onChange={(event) => updateForm("property_type", event.target.value)}>{propertyTypes.filter((type) => type.value).map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></Field>
              <Field label="Status"><select value={form.management_status} onChange={(event) => updateForm("management_status", event.target.value)}>{managementStatuses.filter((status) => status.value).map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></Field>
              <Field label="Address"><input value={form.address} onChange={(event) => updateForm("address", event.target.value)} /></Field>
              <Field label="Town"><input value={form.town} onChange={(event) => updateForm("town", event.target.value)} /></Field>
              <Field label="Province"><input value={form.province} onChange={(event) => updateForm("province", event.target.value)} /></Field>
              <Field label="Description"><textarea rows="3" value={form.description} onChange={(event) => updateForm("description", event.target.value)} /></Field>
            </div>
            <footer>
              <button className="dwella-secondary-action" type="button" onClick={() => setModalOpen(false)}>Cancel</button>
              <button className="dwella-primary-action compact" type="submit" disabled={createPropertyMutation.isPending}>{createPropertyMutation.isPending ? "Saving..." : "Save Property"}</button>
            </footer>
          </form>
        </div>
      ) : null}
    </div>
  );
};

export default Properties;
