import React, { useState } from "react";
import {
  Button,
  Field,
  Input,
  Select,
  Switch,
  Textarea,
} from "@fluentui/react-components";
import { toast } from "react-toastify";
import {
  useOutreachChoices,
  useOutreachList,
  useOutreachMutation,
  useOutreachPreview,
} from "../../Services/outreach";
import { useFormErrors } from "../../shared/useFormErrors";
import { AdminDrawer, AdminHeader, AdminState } from "../Platform/AdminUI";
import {
  ActionButton,
  ErrorText,
  OutreachTabs,
  options,
  segments,
} from "./OutreachUI";
import "./outreach.scss";

function TemplateEditor({ template, contacts, fields }) {
  const [draft, setDraft] = useState(template);
  const [contact, setContact] = useState("");
  const [rendered, setRendered] = useState(null);
  const mutation = useOutreachMutation();
  const preview = useOutreachPreview();
  const errors = useFormErrors();
  return (
    <section className="admin-card">
      <h2>Edit template</h2>
      <form
        className="outreach-form"
        noValidate
        onSubmit={async (e) => {
          e.preventDefault();
          if (
            !errors.validate(
              {
                name: () => (draft.name.trim() ? "" : "Enter a template name."),
                subject: () => (draft.subject.trim() ? "" : "Enter a subject."),
                body: () =>
                  draft.body.trim() ? "" : "Enter the message body.",
              },
              e.currentTarget,
            )
          )
            return;
          try {
            const saved = await mutation.mutateAsync({
              resource: "templates",
              id: template.id,
              method: "patch",
              body: Object.fromEntries(
                ["name", "subject", "body", "whatsapp_body", "active"].map(
                  (key) => [key, draft[key]],
                ),
              ),
            });
            setDraft(saved);
            toast.success(
              "Template saved. Existing approved copies stay unchanged.",
            );
            setRendered(null);
          } catch (error) {
            errors.showServerErrors(error.data, [
              "name",
              "subject",
              "body",
              "whatsapp_body",
            ]);
          }
        }}
      >
        {[
          ["name", "Template name"],
          ["subject", "Subject"],
        ].map(([key, label]) => (
          <Field key={key} label={label} required {...errors.fieldProps(key)}>
            <Input
              maxLength={key === "name" ? 150 : 250}
              value={draft[key]}
              onChange={(_, d) => {
                setDraft({ ...draft, [key]: d.value });
                errors.clearError(key);
                setRendered(null);
              }}
            />
          </Field>
        ))}
        <Field label="Message body" required {...errors.fieldProps("body")}>
          <Textarea
            id="outreach-template-body"
            rows={12}
            maxLength={10000}
            value={draft.body}
            onChange={(_, d) => {
              setDraft({ ...draft, body: d.value });
              errors.clearError("body");
              setRendered(null);
            }}
          />
        </Field>
        <div className="outreach-merge-fields" aria-label="Insert merge field">
          {fields.map((key) => (
            <Button
              key={key}
              size="small"
              onClick={() => {
                setDraft({ ...draft, body: `${draft.body}{${key}}` });
                setRendered(null);
                document.getElementById("outreach-template-body")?.focus();
              }}
            >{`{${key}}`}</Button>
          ))}
        </div>
        <Field label="WhatsApp version" {...errors.fieldProps("whatsapp_body")}>
          <Textarea
            rows={5}
            maxLength={4000}
            value={draft.whatsapp_body}
            onChange={(_, d) => setDraft({ ...draft, whatsapp_body: d.value })}
          />
        </Field>
        <Switch
          label="Template active"
          checked={draft.active}
          onChange={(_, d) => setDraft({ ...draft, active: d.checked })}
        />
        <Button
          type="submit"
          appearance="primary"
          disabled={mutation.isPending}
        >
          Save template
        </Button>
        <ErrorText error={mutation.error} />
        <Field label="Preview with contact">
          <Select
            value={contact}
            onChange={(_, d) => {
              setContact(d.value);
              setRendered(null);
            }}
          >
            <option value="">Choose contact</option>
            {contacts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <ActionButton
          busy={
            !contact ||
            preview.isPending ||
            JSON.stringify(draft) !== JSON.stringify(template)
          }
          onClick={async () => {
            setRendered(null);
            const data = await preview.mutateAsync({
              resource: "templates",
              id: template.id,
              body: { contact },
            });
            setRendered(data);
          }}
        >
          Preview saved template
        </ActionButton>
        <ErrorText error={preview.error} />
        {rendered && (
          <div className="outreach-preview">
            <h3>{rendered.subject}</h3>
            <pre>{rendered.body}</pre>
          </div>
        )}
      </form>
    </section>
  );
}

export default function Sequences() {
  const sequences = useOutreachChoices("sequences");
  const templates = useOutreachChoices("templates");
  const contacts = useOutreachChoices("contacts");
  const settings = useOutreachList("settings");
  const [selected, setSelected] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [dialog, setDialog] = useState(null);
  const mutation = useOutreachMutation();
  const sequence =
    sequences.data?.results.find((s) => s.id === selected) ||
    sequences.data?.results[0];
  const template = templates.data?.results.find(
    (t) => t.id === (templateId || sequence?.steps[0]?.template),
  );
  return (
    <div className="admin-screen outreach-screen">
      <AdminHeader
        title="Sequences & templates"
        description="Reusable personal messages. Review the rendered email before approving a recipient."
      >
        <Button onClick={() => setDialog("template")}>New template</Button>
        <Button appearance="primary" onClick={() => setDialog("sequence")}>
          New sequence
        </Button>
      </AdminHeader>
      <OutreachTabs />
      <AdminState query={sequences}>
        <div className="outreach-review-grid">
          <section className="admin-card outreach-sequences">
            <h2>Sequences</h2>
            <Field label="Choose sequence">
              <Select
                value={sequence?.id || ""}
                onChange={(_, d) => {
                  setSelected(d.value);
                  setTemplateId("");
                }}
              >
                <option value="">Choose sequence</option>
                {sequences.data?.results.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            {sequence?.steps.map((step, i) => (
              <button
                key={step.order}
                type="button"
                className={template?.id === step.template ? "is-selected" : ""}
                onClick={() => setTemplateId(step.template)}
              >
                <span className="admin-note">
                  Day{" "}
                  {sequence.steps
                    .slice(0, i + 1)
                    .reduce((sum, s) => sum + s.wait_days, 0)}
                </span>
                <strong>{step.template_name}</strong>
                <span className="admin-note">Only while there is no reply</span>
              </button>
            ))}
            {sequence && (
              <>
                <ActionButton
                  busy={mutation.isPending}
                  onClick={() => setDialog("edit_sequence")}
                >
                  Edit sequence steps
                </ActionButton>
                <ActionButton
                  busy={mutation.isPending}
                  onClick={() =>
                    mutation.mutateAsync({
                      resource: "sequences",
                      id: sequence.id,
                      method: "patch",
                      body: { active: !sequence.active },
                    })
                  }
                >
                  {sequence.active ? "Archive sequence" : "Activate sequence"}
                </ActionButton>
              </>
            )}
            <Field label="All templates">
              <Select
                value={template?.id || ""}
                onChange={(_, d) => setTemplateId(d.value)}
              >
                <option value="">Choose template</option>
                {templates.data?.results.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </Field>
          </section>
          <AdminState
            query={templates}
            empty={!template}
            title="Add or choose a template"
          >
            {template && (
              <TemplateEditor
                key={template.id}
                template={template}
                contacts={contacts.data?.results || []}
                fields={settings.data?.merge_fields || []}
              />
            )}
          </AdminState>
        </div>
      </AdminState>
      {dialog === "template" && (
        <AdminDrawer
          title="New template"
          onClose={() => setDialog(null)}
          initial={{ segment: "other" }}
          fields={[
            {
              key: "name",
              label: "Template name",
              required: true,
              maxLength: 150,
            },
            {
              key: "segment",
              label: "Segment",
              type: "select",
              options: options(segments),
            },
            {
              key: "subject",
              label: "Subject",
              required: true,
              maxLength: 250,
            },
            {
              key: "body",
              label: "Message body",
              type: "textarea",
              required: true,
              maxLength: 10000,
            },
            {
              key: "whatsapp_body",
              label: "WhatsApp version",
              type: "textarea",
              maxLength: 4000,
            },
          ]}
          onSubmit={async (values) => {
            const data = await mutation.mutateAsync({
              resource: "templates",
              body: values,
            });
            setTemplateId(data.id);
            setDialog(null);
          }}
        />
      )}
      {dialog === "sequence" && (
        <AdminDrawer
          title="New sequence"
          onClose={() => setDialog(null)}
          fields={[
            {
              key: "name",
              label: "Sequence name",
              required: true,
              maxLength: 150,
            },
            {
              key: "description",
              label: "Description",
              type: "textarea",
              maxLength: 1000,
            },
            {
              key: "template",
              label: "First email template",
              type: "select",
              required: true,
              options: (templates.data?.results || [])
                .filter((t) => t.active)
                .map((t) => ({ value: t.id, label: t.name })),
            },
            {
              key: "wait_days",
              label: "Days before first email",
              type: "number",
              required: true,
              pattern: /^(\d|[1-9]\d|[12]\d\d|3[0-5]\d|36[0-5])$/,
            },
          ]}
          initial={{ wait_days: "0" }}
          onSubmit={async (values) => {
            const data = await mutation.mutateAsync({
              resource: "sequences",
              body: {
                name: values.name,
                description: values.description || "",
                steps: [
                  {
                    order: 0,
                    template: values.template,
                    wait_days: Number(values.wait_days),
                  },
                ],
              },
            });
            setSelected(data.id);
            setDialog(null);
          }}
        />
      )}
      {dialog === "edit_sequence" && (
        <SequenceSteps
          sequence={sequence}
          templates={templates.data?.results || []}
          onClose={() => setDialog(null)}
        />
      )}
    </div>
  );
}

function SequenceSteps({ sequence, templates, onClose }) {
  const [steps, setSteps] = useState(sequence.steps);
  const mutation = useOutreachMutation();
  return (
    <AdminDrawer
      title={`Edit ${sequence.name}`}
      fields={[]}
      onClose={onClose}
      onSubmit={async () => {
        if (
          !steps.length ||
          steps.some(
            (s) =>
              !s.template ||
              !Number.isInteger(Number(s.wait_days)) ||
              Number(s.wait_days) < 0 ||
              Number(s.wait_days) > 365,
          )
        )
          throw Error("Each step needs a template and a delay of 0–365 days.");
        await mutation.mutateAsync({
          resource: "sequences",
          id: sequence.id,
          method: "patch",
          body: {
            steps: steps.map((s, order) => ({
              order,
              template: s.template,
              wait_days: Number(s.wait_days),
            })),
          },
        });
        onClose();
      }}
    >
      <p>
        Approved sequences keep their structure. Create a new sequence if this
        one already has approved recipients.
      </p>
      {steps.map((step, index) => (
        <div key={index} className="outreach-form">
          <Field label={`Step ${index + 1} template`}>
            <Select
              value={step.template}
              onChange={(_, d) =>
                setSteps(
                  steps.map((s, i) =>
                    i === index ? { ...s, template: d.value } : s,
                  ),
                )
              }
            >
              <option value="">Choose template</option>
              {templates
                .filter((t) => t.active)
                .map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
            </Select>
          </Field>
          <Field label="Days after previous step">
            <Input
              type="number"
              min={0}
              max={365}
              value={String(step.wait_days)}
              onChange={(_, d) =>
                setSteps(
                  steps.map((s, i) =>
                    i === index ? { ...s, wait_days: d.value } : s,
                  ),
                )
              }
            />
          </Field>
          <Button onClick={() => setSteps(steps.filter((_, i) => i !== index))}>
            Remove step
          </Button>
        </div>
      ))}
      <Button
        disabled={steps.length >= 20}
        onClick={() => setSteps([...steps, { template: "", wait_days: 1 }])}
      >
        Add step
      </Button>
    </AdminDrawer>
  );
}
