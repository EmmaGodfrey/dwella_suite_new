import React, { useState } from "react";
import { Button, Dropdown, Field, Input, Option, Radio, RadioGroup, Switch, Textarea } from "@fluentui/react-components";
import { Camera20Regular, Dismiss24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useRepairPhoto, useReportRepair } from "../../Services/portal";
import { FormDrawer } from "../../shared/components/FormFlow";
import { firstErrorStep } from "../../shared/formFlow";
import { categories } from "../../shared/maintenance";
import { useFormErrors } from "../../shared/useFormErrors";
import { MAX_PHOTOS, PHOTO_MAX_BYTES, PHOTO_TYPES, checkPhotos } from "../Maintenance/RequestDrawer";
import "../Maintenance/maintenance.scss";

const groups = [["lease", "title", "category", "priority", "description"], ["permission_to_enter", "access_notes"]];

// Two steps: what is wrong, then how to get in and any photos. Photos upload
// after the request exists; a failed photo never loses the report.
export default function ReportRepairDrawer({ homes, onClose, onSaved }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    lease: homes.length === 1 ? homes[0].id : "",
    title: "",
    category: "general",
    priority: "normal",
    description: "",
    permission_to_enter: false,
    access_notes: "",
  });
  const [photos, setPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const { errors, validate, clearError, fieldProps, showServerErrors } = useFormErrors();
  const photo = useRepairPhoto();
  const report = useReportRepair({
    onSuccess: async (data) => {
      setUploading(true);
      let failed = 0;
      for (const file of photos) {
        try {
          await photo.mutateAsync({ id: data.id, file });
        } catch {
          failed += 1;
        }
      }
      setUploading(false);
      toast.success(`Repair ${data.reference} reported.`);
      if (failed) toast.error(`${failed} ${failed === 1 ? "photo" : "photos"} could not be uploaded. Add them from the repair page.`);
      onSaved(data);
    },
    onError: (error) => {
      setStep(firstErrorStep(error.data, groups, step));
      if (!showServerErrors(error.data, groups.flat())) toast.error(error.message || "Could not report the repair.");
    },
  });
  const busy = report.isPending || uploading;
  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key);
  };
  const choosePhotos = (event) => {
    const { accepted, problem } = checkPhotos(Array.from(event.target.files || []), MAX_PHOTOS - photos.length);
    event.target.value = "";
    if (problem) toast.error(problem);
    setPhotos((current) => [...current, ...accepted]);
  };

  const submit = (event) => {
    event.preventDefault();
    if (busy) return;
    if (step === 0) {
      const ok = validate({
        lease: () => (form.lease ? "" : "Choose which home this is for."),
        title: () => (form.title.trim() ? "" : "Say briefly what needs fixing."),
      }, event.currentTarget);
      if (ok) setStep(1);
      return;
    }
    report.mutate({
      lease: form.lease,
      title: form.title.trim(),
      category: form.category,
      priority: form.priority,
      description: form.description.trim(),
      permission_to_enter: form.permission_to_enter,
      access_notes: form.access_notes.trim(),
    });
  };

  return (
    <FormDrawer
      title="Report a repair"
      description="Your property manager is notified and replies here."
      steps={["What needs fixing", "Access and photos"]}
      step={step}
      stepDescription={step === 0 ? "Fields marked * are required." : "Photos help the repairer bring the right parts."}
      onSubmit={submit}
      onBack={() => setStep(0)}
      onClose={onClose}
      busy={busy}
      errors={errors}
      submitLabel="Send report"
      pendingLabel={uploading ? "Uploading photos…" : "Sending…"}
    >
      {step === 0 ? (
        <div className="dwella-form-grid">
          {homes.length > 1 ? (
            <Field label="Home" required {...fieldProps("lease")} className={`dwella-field-wide ${fieldProps("lease").className || ""}`}>
              <Dropdown
                placeholder="Choose a home"
                selectedOptions={form.lease ? [form.lease] : []}
                value={homes.find((home) => home.id === form.lease)?.label || ""}
                onOptionSelect={(_, d) => update("lease", d.optionValue)}
              >
                {homes.map((home) => <Option key={home.id} value={home.id}>{home.label}</Option>)}
              </Dropdown>
            </Field>
          ) : null}
          <Field label="What needs fixing?" required {...fieldProps("title")} className={`dwella-field-wide ${fieldProps("title").className || ""}`}>
            <Input maxLength={160} placeholder="e.g. Kitchen tap leaking" value={form.title} onChange={(_, d) => update("title", d.value)} />
          </Field>
          <Field label="Type">
            <Dropdown
              selectedOptions={[form.category]}
              value={categories.find((item) => item.value === form.category)?.label}
              onOptionSelect={(_, d) => update("category", d.optionValue)}
            >
              {categories.map((item) => <Option key={item.value} value={item.value}>{item.label}</Option>)}
            </Dropdown>
          </Field>
          <Field label="How urgent?">
            <RadioGroup layout="horizontal" value={form.priority} onChange={(_, d) => update("priority", d.value)}>
              <Radio value="normal" label="Can wait a few days" />
              <Radio value="urgent" label="Urgent" />
            </RadioGroup>
          </Field>
          <Field label="Details" hint="Where it is and what you have noticed." className="dwella-field-wide">
            <Textarea rows={4} maxLength={4000} value={form.description} onChange={(_, d) => update("description", d.value)} />
          </Field>
        </div>
      ) : (
        <>
          <section className="dwella-form-section">
            <Switch
              checked={form.permission_to_enter}
              onChange={(_, d) => update("permission_to_enter", d.checked)}
              label="The repairer may enter if I'm not home"
            />
            <Field label="Best times to visit" {...fieldProps("access_notes")}>
              <Input maxLength={200} placeholder="e.g. Weekdays after 17:00" value={form.access_notes} onChange={(_, d) => update("access_notes", d.value)} />
            </Field>
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
            <p className="dwella-muted-copy">
              Optional · JPEG, PNG or WebP · Up to {PHOTO_MAX_BYTES / (1024 * 1024)}MB each · Up to {MAX_PHOTOS} photos
            </p>
          </section>
        </>
      )}
    </FormDrawer>
  );
}
