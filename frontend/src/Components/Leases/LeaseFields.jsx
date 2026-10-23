import React from "react";
import { Button, Dropdown, Field, Input, Option, Radio, RadioGroup } from "@fluentui/react-components";

import { useUnitsQuery } from "../../Services/queries";
import { formatMoney } from "../../shared/format";

const unitLabel = (unit) => (unit ? `${unit.name} · ${unit.property_name}` : "");

// Lease terms shared by "Add tenant" and "New lease". `prefix` namespaces the
// field names so a nested form can report `lease.unit` errors on the right field.
export default function LeaseFields({ lease, onChange, fieldProps, prefix = "", section = "all" }) {
  // Only vacant units can take a new tenant. 200 covers a large single
  // landlord; a picker with search replaces this once portfolios outgrow it.
  const unitsQuery = useUnitsQuery({ available: "true", page_size: 200, ordering: "name" }, { staleTime: 30_000 });
  const units = unitsQuery.data?.results || [];
  const selected = units.find((unit) => unit.id === lease.unit);
  const props = (name) => fieldProps(`${prefix}${name}`);

  const chooseUnit = (unitId) => {
    const unit = units.find((item) => item.id === unitId);
    onChange("unit", unitId);
    onChange("_unitLabel", unitLabel(unit));
    // Rent follows the unit until the landlord types their own figure.
    if (unit && (!lease.monthly_rent || lease.monthly_rent === lease._unitRent)) {
      onChange("monthly_rent", String(Number(unit.rent_amount)));
      onChange("_unitRent", String(Number(unit.rent_amount)));
    }
  };

  return (
    <div className="dwella-form-grid">
      {section !== "terms" && <Field
        label="Unit"
        required
        {...props("unit")}
        hint={!unitsQuery.isLoading && !unitsQuery.isError && !units.length ? "No vacant units. Mark a unit vacant or add one under Properties." : undefined}
        className={`dwella-field-wide ${props("unit").className || ""}`}
      >
        <Dropdown
          placeholder={unitsQuery.isLoading ? "Loading units…" : "Choose a vacant unit"}
          disabled={unitsQuery.isLoading || !units.length}
          selectedOptions={lease.unit ? [lease.unit] : []}
          value={unitLabel(selected)}
          onOptionSelect={(_, data) => chooseUnit(data.optionValue)}
        >
          {units.map((unit) => (
            <Option key={unit.id} value={unit.id} text={unitLabel(unit)}>
              <span className="dwella-option-split">
                <span>{unitLabel(unit)}</span>
                <small>{formatMoney(unit.rent_amount, { whole: true })}</small>
              </span>
            </Option>
          ))}
        </Dropdown>
      </Field>}
      {section !== "terms" && unitsQuery.isError && <p role="alert" className="dwella-field-wide">
        Could not load available units. <Button type="button" onClick={() => unitsQuery.refetch()}>Retry units</Button>
      </p>}
      {section !== "unit" && <>
        <Field label="Move-in date" required {...props("start_date")}>
          <Input type="date" value={lease.start_date} onChange={(_, data) => onChange("start_date", data.value)} />
        </Field>
        <Field label="Lease ends" required {...props("end_date")}>
          <Input type="date" value={lease.end_date} min={lease.start_date || undefined} onChange={(_, data) => onChange("end_date", data.value)} />
        </Field>
        <Field label="Monthly rent (ZMW)" required {...props("monthly_rent")}>
          <Input inputMode="decimal" value={lease.monthly_rent} placeholder="3900.00" onChange={(_, data) => onChange("monthly_rent", data.value)} />
        </Field>
        <Field label="Deposit (ZMW)" {...props("deposit_amount")}>
          <Input inputMode="decimal" value={lease.deposit_amount} placeholder="0.00" onChange={(_, data) => onChange("deposit_amount", data.value)} />
        </Field>
        <Field label="Rent due on day" required {...props("rent_due_day")} hint="1–28, so the day exists in every month.">
          <Input type="number" min={1} max={28} value={lease.rent_due_day} onChange={(_, data) => onChange("rent_due_day", data.value)} />
        </Field>
        {section !== "terms" && <LeaseStatus lease={lease} onChange={onChange} />}
      </>}
    </div>
  );
}

export function LeaseStatus({ lease, onChange }) {
  return (
    <Field label="Lease status" className="dwella-field-wide">
      <RadioGroup
        layout="horizontal"
        value={lease.activate ? "active" : "draft"}
        onChange={(_, data) => onChange("activate", data.value === "active")}
      >
        <Radio value="active" label="Start now — tenant moves in" />
        <Radio value="draft" label="Save as draft — sign later" />
      </RadioGroup>
    </Field>
  );
}
