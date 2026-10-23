import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  Dropdown,
  Field,
  Input,
  Option,
  Textarea,
} from "@fluentui/react-components";
import { Dismiss20Regular, ImageAdd20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";
import { useSavePropertyMutation } from "../../Services/mutations";
import { PropertyPhoto } from "../../shared/components/PropertyPhoto";
import { useFormErrors } from "../../shared/useFormErrors";
import { propertyTypes, managementStatuses, optionLabel } from "./options";

const initialForm = {
  name: "",
  property_type: "apartment",
  management_status: "managed",
  address: "",
  town: "",
  province: "",
  description: "",
};

export default function PropertyForm({ property, onClose, onSaved }) {
  const [form, setForm] = useState(() =>
    Object.fromEntries(
      Object.keys(initialForm).map((key) => [
        key,
        property?.[key] ?? initialForm[key],
      ]),
    ),
  );
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState("");
  const [removePhoto, setRemovePhoto] = useState(false);
  const [photoError, setPhotoError] = useState("");
  const picker = useRef(null);
  const { validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  useEffect(() => {
    if (!photo) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  const mutation = useSavePropertyMutation({
    onSuccess: (data) => {
      toast.success(property ? "Property updated." : "Property added.");
      onSaved?.(data);
    },
    onError: (error) => {
      if (!showServerErrors(error.data, Object.keys(initialForm)))
        toast.error(error.message || "Could not save property.");
    },
  });
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const choosePhoto = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (
      !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
      file.size > 5 * 1024 * 1024
    ) {
      setPhotoError("Choose a JPEG, PNG, or WebP photo, 5MB or smaller.");
      return;
    }
    setPhotoError("");
    setPhoto(file);
    setRemovePhoto(false);
  };
  const submit = (event) => {
    event.preventDefault();
    if (mutation.isPending) return;
    if (
      !validate(
        {
          name: () => (form.name.trim() ? "" : "Property name is required."),
          address: () => (form.address.trim() ? "" : "Address is required."),
        },
        event.currentTarget,
      ) ||
      photoError
    )
      return;
    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) =>
      payload.append(key, value.trim()),
    );
    if (photo) payload.append("cover_image", photo);
    else if (removePhoto) payload.append("cover_image", "");
    mutation.mutate({ id: property?.id, payload });
  };

  return (
    <form noValidate onSubmit={submit} className="dwella-property-form">
      <header className="dwella-property-form-header">
        <div>
          <h2>{property ? "Edit property" : "Add property"}</h2>
          <p>
            {property
              ? "Update the property details and cover photo."
              : "Add a new asset to your portfolio."}
          </p>
        </div>
        <Button
          appearance="subtle"
          icon={<Dismiss20Regular />}
          aria-label="Close property form"
          disabled={mutation.isPending}
          onClick={onClose}
        />
      </header>
      <div className="dwella-property-form-content">
        <fieldset disabled={mutation.isPending}>
          <section className="dwella-form-section dwella-cover-field">
            <PropertyPhoto
              src={preview || (!removePhoto ? property?.cover_image : "")}
              name={form.name || "Cover preview"}
            />
            <div>
              <h3>
                Cover photo <small>Optional</small>
              </h3>
              <p>JPEG, PNG or WebP. Up to 5MB.</p>
              <input
                ref={picker}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                onChange={choosePhoto}
              />
              <div className="dwella-cover-actions">
                <Button
                  icon={<ImageAdd20Regular />}
                  onClick={() => picker.current?.click()}
                >
                  {photo || property?.cover_image ? "Change photo" : "Add photo"}
                </Button>
                {(photo || (!removePhoto && property?.cover_image)) && (
                  <Button
                    appearance="subtle"
                    onClick={() => {
                      setPhoto(null);
                      setRemovePhoto(true);
                      setPhotoError("");
                    }}
                  >
                    Remove
                  </Button>
                )}
              </div>
              {photoError && (
                <p role="alert" className="dwella-field-error">
                  {photoError}{" "}
                  <button
                    type="button"
                    className="dwella-text-link"
                    onClick={() => setPhotoError("")}
                  >
                    Dismiss
                  </button>
                </p>
              )}
            </div>
          </section>
          <section className="dwella-form-section">
            <h3>Property details</h3>
            <div className="dwella-form-grid">
              <Field
                label="Property name"
                required
                {...fieldProps("name")}
                className={`dwella-field-wide ${fieldProps("name").className || ""}`}
              >
                <Input
                  maxLength={180}
                  placeholder="e.g. Kabulonga Heights"
                  value={form.name}
                  onChange={(_, d) => update("name", d.value)}
                />
              </Field>
              <Field label="Property type">
                <Dropdown
                  selectedOptions={[form.property_type]}
                  value={optionLabel(propertyTypes, form.property_type)}
                  onOptionSelect={(_, d) =>
                    update("property_type", d.optionValue)
                  }
                >
                  {propertyTypes
                    .filter((t) => t.value)
                    .map((t) => (
                      <Option key={t.value} value={t.value}>
                        {t.label}
                      </Option>
                    ))}
                </Dropdown>
              </Field>
              <Field label="Management status">
                <Dropdown
                  selectedOptions={[form.management_status]}
                  value={optionLabel(
                    managementStatuses,
                    form.management_status,
                  )}
                  onOptionSelect={(_, d) =>
                    update("management_status", d.optionValue)
                  }
                >
                  {managementStatuses
                    .filter((t) => t.value)
                    .map((t) => (
                      <Option key={t.value} value={t.value}>
                        {t.label}
                      </Option>
                    ))}
                </Dropdown>
              </Field>
            </div>
          </section>
          <section className="dwella-form-section">
            <h3>Location</h3>
            <div className="dwella-form-grid">
              <Field
                label="Street address"
                required
                {...fieldProps("address")}
                className={`dwella-field-wide ${fieldProps("address").className || ""}`}
              >
                <Input
                  placeholder="Street and plot number"
                  value={form.address}
                  onChange={(_, d) => update("address", d.value)}
                />
              </Field>
              <Field label="Town">
                <Input
                  maxLength={120}
                  value={form.town}
                  onChange={(_, d) => update("town", d.value)}
                />
              </Field>
              <Field label="Province">
                <Input
                  maxLength={120}
                  value={form.province}
                  onChange={(_, d) => update("province", d.value)}
                />
              </Field>
            </div>
          </section>
          <section className="dwella-form-section">
            <Field label="Notes (optional)">
              <Textarea
                rows={2}
                value={form.description}
                onChange={(_, d) => update("description", d.value)}
              />
            </Field>
          </section>
        </fieldset>
      </div>
      <footer className="dwella-property-form-actions">
        <Button onClick={onClose} disabled={mutation.isPending}>
          Cancel
        </Button>
        <Button
          appearance="primary"
          type="submit"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Saving..." : "Save property"}
        </Button>
      </footer>
    </form>
  );
}
