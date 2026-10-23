import React, { useState } from "react";
import { Button, Dropdown, Field, Input, Option, Textarea } from "@fluentui/react-components";
import { toast } from "react-toastify";
import { useSaveUnitMutation } from "../../Services/mutations";
import { useFormErrors } from "../../shared/useFormErrors";

const statuses = [
  { value: "vacant", label: "Vacant" },
  { value: "occupied", label: "Occupied" },
  { value: "reserved", label: "Reserved" },
  { value: "maintenance", label: "Maintenance" },
];

export default function UnitForm({ propertyId, unit, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: unit?.name || "",
    rent_amount: unit?.rent_amount || "",
    occupancy_status: unit?.occupancy_status || "vacant",
    bedrooms: String(unit?.bedrooms ?? 0),
    bathrooms: String(unit?.bathrooms ?? 0),
    floor_area: unit?.floor_area || "",
    notes: unit?.notes || "",
  });
  const { validate, clearError, fieldProps } = useFormErrors();
  const mutation = useSaveUnitMutation({
    onSuccess: () => {
      toast.success(unit ? "Unit updated." : "Unit added.");
      onSaved();
    },
    onError: (error) => toast.error(error.message || "Could not save unit."),
  });
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (!validate({
      name: () => form.name.trim() ? "" : "Unit name is required.",
      rent_amount: () => Number.isFinite(Number(form.rent_amount)) && Number(form.rent_amount) >= 0 && form.rent_amount !== ""
        ? "" : "Enter a valid monthly rent.",
      bedrooms: () => form.bedrooms !== "" && Number.isInteger(Number(form.bedrooms)) && Number(form.bedrooms) >= 0
        ? "" : "Enter a whole number of bedrooms.",
      bathrooms: () => form.bathrooms !== "" && Number.isFinite(Number(form.bathrooms)) && Number(form.bathrooms) >= 0
        ? "" : "Enter a valid number of bathrooms.",
      floor_area: () => !form.floor_area || Number.isFinite(Number(form.floor_area)) && Number(form.floor_area) >= 0
        ? "" : "Enter a valid floor area.",
    }, event.currentTarget)) return;
    mutation.mutate({
      id: unit?.id,
      payload: {
        ...form,
        name: form.name.trim(),
        rent_amount: form.rent_amount,
        floor_area: form.floor_area || null,
        notes: form.notes.trim(),
        ...(unit ? {} : { property: propertyId }),
      },
    });
  };

  return (
    <form className="dwella-unit-form" onSubmit={submit} noValidate>
      <div className="dwella-unit-form-heading">
        <div>
          <h4>{unit ? `Edit ${unit.name}` : "Add a unit"}</h4>
          <p>Keep rent and availability current for this property.</p>
        </div>
      </div>
      <fieldset disabled={mutation.isPending}>
        <div className="dwella-unit-form-grid">
          <Field label="Unit name" required {...fieldProps("name")}>
            <Input value={form.name} maxLength={80} placeholder="e.g. A1" onChange={(_, d) => update("name", d.value)} />
          </Field>
          <Field label="Monthly rent (ZMW)" required {...fieldProps("rent_amount")}>
            <Input type="number" min="0" step="0.01" value={form.rent_amount} onChange={(_, d) => update("rent_amount", d.value)} />
          </Field>
          <Field label="Availability">
            <Dropdown selectedOptions={[form.occupancy_status]} value={statuses.find((s) => s.value === form.occupancy_status)?.label} onOptionSelect={(_, d) => update("occupancy_status", d.optionValue)}>
              {statuses.map((status) => <Option key={status.value} value={status.value}>{status.label}</Option>)}
            </Dropdown>
          </Field>
          <Field label="Floor area (sq m)" {...fieldProps("floor_area")}>
            <Input type="number" min="0" step="0.01" value={form.floor_area} onChange={(_, d) => update("floor_area", d.value)} />
          </Field>
          <Field label="Bedrooms" {...fieldProps("bedrooms")}>
            <Input type="number" min="0" step="1" value={form.bedrooms} onChange={(_, d) => update("bedrooms", d.value)} />
          </Field>
          <Field label="Bathrooms" {...fieldProps("bathrooms")}>
            <Input type="number" min="0" step="0.5" value={form.bathrooms} onChange={(_, d) => update("bathrooms", d.value)} />
          </Field>
          <Field label="Notes" className="dwella-unit-form-wide">
            <Textarea rows={2} value={form.notes} onChange={(_, d) => update("notes", d.value)} />
          </Field>
        </div>
      </fieldset>
      <div className="dwella-unit-form-actions">
        <Button type="button" onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button type="submit" appearance="primary" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving..." : unit ? "Save changes" : "Add unit"}
        </Button>
      </div>
    </form>
  );
}
