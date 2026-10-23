import React, { useState } from "react";
import {
  Button,
  Dropdown,
  Field,
  Input,
  Option,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { Camera20Regular, Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useMaintenancePhotoMutation, useSaveMaintenanceRequestMutation } from "../../Services/mutations";
import { usePropertiesQuery, useUnitsQuery } from "../../Services/queries";
import { categories, priorities, sources } from "../../shared/maintenance";
import { useFormErrors } from "../../shared/useFormErrors";
import { FormDrawer } from "../../shared/components/FormFlow";
import { firstErrorStep } from "../../shared/formFlow";

export const MAX_PHOTOS = 8;
export const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const PHOTO_MAX_BYTES = 8 * 1024 * 1024;

// Returns the files that can be sent and a message for any that cannot.
export const checkPhotos = (files, room) => {
  const accepted = [];
  let problem = "";
  files.forEach((file) => {
    if (!PHOTO_TYPES.includes(file.type)) problem = "Photos must be JPEG, PNG or WebP.";
    else if (file.size > PHOTO_MAX_BYTES) problem = "Photos must be 8MB or smaller.";
    else if (accepted.length >= room) problem = `A request can have up to ${MAX_PHOTOS} photos.`;
    else accepted.push(file);
  });
  return { accepted, problem };
};

const pick = (list, value) => list.find((item) => item.value === value)?.label || "";

export default function RequestDrawer({ onClose, onSaved }) {
  const [form, setForm] = useState({
    property: "",
    unit: "",
    title: "",
    description: "",
    category: "general",
    priority: "normal",
    source: "landlord",
    access_notes: "",
    permission_to_enter: false,
  });
  const [step, setStep] = useState(0);
  const [photos, setPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const { errors, validate, clearError, fieldProps, showServerErrors } =
    useFormErrors();
  const propertiesQuery = usePropertiesQuery({ page_size: 200, ordering: "name" }, { staleTime: 60_000 });
  const unitsQuery = useUnitsQuery({ property: form.property, page_size: 200, ordering: "name" }, { enabled: Boolean(form.property), staleTime: 30_000 });
  const properties = propertiesQuery.data?.results || [];
  const units = unitsQuery.data?.results || [];
  const photoMutation = useMaintenancePhotoMutation();

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value, ...(key === "property" ? { unit: "" } : {}) }));
    clearError(key);
  };

  const mutation = useSaveMaintenanceRequestMutation({
    onSuccess: async (data) => {
      // Photos go up one by one once the request exists; a failed photo does
      // not undo the request, it is just reported.
      if (photos.length) {
        setUploading(true);
        let failed = 0;
        for (const file of photos) {
          try {
            await photoMutation.mutateAsync({ id: data.id, file });
          } catch {
            failed += 1;
          }
        }
        setUploading(false);
        if (failed) toast.warning(`${failed} ${failed === 1 ? "photo" : "photos"} could not be uploaded.`);
      }
      toast.success(`${data.reference} logged.`);
      onSaved?.(data);
    },
    onError: (error) => {
      setStep(
        firstErrorStep(
          error.data,
          [
            [
              "property",
              "unit",
              "title",
              "description",
              "category",
              "priority",
            ],
            ["source", "access_notes", "permission_to_enter"],
          ],
          step,
        ),
      );
      if (!showServerErrors(error.data, Object.keys(form))) {
        toast.error(error.message || "Could not log the request.");
      }
    },
  });
  const busy = mutation.isPending || uploading;

  const choosePhotos = (event) => {
    const { accepted, problem } = checkPhotos(Array.from(event.target.files || []), MAX_PHOTOS - photos.length);
    if (problem) toast.error(problem);
    setPhotos((current) => [...current, ...accepted]);
    event.target.value = "";
  };

  const submit = (event) => {
    event.preventDefault();
    if (busy) return;
    const ok = validate({
      property: () => (form.property ? "" : "Choose the property."),
      title: () => (form.title.trim() ? "" : "Say what needs fixing."),
    }, event.currentTarget);
    if (!ok) {
      setStep(0);
      return;
    }
    if (step === 0) {
      setStep(1);
      return;
    }
    mutation.mutate({
      payload: {
        ...form,
        unit: form.unit || null,
        title: form.title.trim(),
        description: form.description.trim(),
        access_notes: form.access_notes.trim(),
      },
    });
  };

  const property = properties.find((item) => item.id === form.property);
  const unit = units.find((item) => item.id === form.unit);

  return (
    <FormDrawer
      title="New maintenance request"
      description="Record the issue, then add access details and photos."
      steps={["Issue and location", "Access and photos"]}
      step={step}
      stepTitle={step === 0 ? "Issue and location" : "Access and photos"}
      onSubmit={submit}
      onBack={() => setStep(step - 1)}
      onClose={onClose}
      busy={busy}
      errors={errors}
      submitLabel="Create request"
      pendingLabel={uploading ? "Uploading photos…" : "Creating request…"}
    >
      {step === 0 ? (
        <>
          <section className="dwella-form-section">
            <Field label="What needs fixing?" required {...fieldProps("title")}>
              <Input maxLength={160} placeholder="e.g. Leaking kitchen tap" value={form.title} onChange={(_, d) => update("title", d.value)} />
            </Field>
            <Field label="Details" hint="What happened, since when, anything already tried.">
              <Textarea rows={3} value={form.description} onChange={(_, d) => update("description", d.value)} />
            </Field>
          </section>
          <section className="dwella-form-section">
            <h3>Where</h3>
            <div className="dwella-form-grid">
              <Field label="Property" required {...fieldProps("property")}>
                <Dropdown
                  placeholder={
                    propertiesQuery.isLoading ? "Loading…" : "Choose a property"
                  }
                  value={property?.name || ""}
                  selectedOptions={form.property ? [form.property] : []}
                  onOptionSelect={(_, d) => update("property", d.optionValue)}
                >
                  {properties.map((item) => (
                    <Option key={item.id} value={item.id}>
                      {item.name}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Field
                label="Unit"
                hint="Leave as common area for gates, roofs and grounds."
                {...fieldProps("unit")}
              >
                <Dropdown
                  disabled={!form.property}
                  value={unit?.name || "Common area"}
                  selectedOptions={[form.unit]}
                  onOptionSelect={(_, d) => update("unit", d.optionValue)}
                >
                  <Option value="">Common area</Option>
                  {units.map((item) => (
                    <Option key={item.id} value={item.id}>
                      {item.name}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
            </div>
          </section>
          <section className="dwella-form-section">
            <div className="dwella-form-grid">
              <Field label="Category">
                <Dropdown
                  value={pick(categories, form.category)}
                  selectedOptions={[form.category]}
                  onOptionSelect={(_, d) => update("category", d.optionValue)}
                >
                  {categories.map((item) => (
                    <Option key={item.value} value={item.value}>
                      {item.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Field label="Priority">
                <Dropdown
                  value={pick(priorities, form.priority)}
                  selectedOptions={[form.priority]}
                  onOptionSelect={(_, d) => update("priority", d.optionValue)}
                >
                  {priorities.map((item) => (
                    <Option key={item.value} value={item.value}>
                      {item.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
            </div>
          </section>
        </>
      ) : (
        <>
          <section className="dwella-form-section">
            <div className="dwella-form-grid">
              <Field label="Reported by">
                <Dropdown
                  value={pick(sources, form.source)}
                  selectedOptions={[form.source]}
                  onOptionSelect={(_, d) => update("source", d.optionValue)}
                >
                  {sources.map((item) => (
                    <Option key={item.value} value={item.value}>
                      {item.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>
              <Field label="Access" hint="When someone can get in.">
                <Input maxLength={200} placeholder="e.g. Weekdays after 17:00" value={form.access_notes} onChange={(_, d) => update("access_notes", d.value)} />
              </Field>
            </div>
            <Switch
              checked={form.permission_to_enter}
              onChange={(_, d) => update("permission_to_enter", d.checked)}
              label="Tenant gave permission to enter when they are out"
            />
          </section>
          <section className="dwella-form-section">
            <h3>Photos</h3>
            <div className="dwella-photo-picker">
              {photos.map((file, index) => (
                <span key={`${file.name}-${index}`} className="dwella-photo-chip">
                  {file.name}
                  <Button size="small" appearance="subtle" aria-label={`Remove ${file.name}`} icon={<Dismiss24Regular />} onClick={() => setPhotos((current) => current.filter((_, i) => i !== index))} />
                </span>
              ))}
              {photos.length < MAX_PHOTOS ? (
                <label className="dwella-photo-add">
                  <Camera20Regular />
                  Add photos
                  <input type="file" accept={PHOTO_TYPES.join(",")} multiple onChange={choosePhotos} />
                </label>
              ) : null}
            </div>
          </section>
          <p className="dwella-muted-copy">
            JPEG, PNG or WebP · Up to {PHOTO_MAX_BYTES / (1024 * 1024)}MB each · Up to {MAX_PHOTOS} photos
          </p>
        </>
      )}
    </FormDrawer>
  );
}
