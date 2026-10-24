import React, { useCallback, useEffect, useId, useRef } from "react";
import { Button, Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle, DrawerBody, DrawerFooter, DrawerHeader, DrawerHeaderTitle, OverlayDrawer } from "@fluentui/react-components";
import { Checkmark20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import "./formFlow.scss";

export function FormSteps({ steps, step, label = "Form progress" }) {
  return (
    <nav aria-label={label}>
      <ol className="dwella-form-steps">
        {steps.map((title, index) => (
          <li
            key={title}
            aria-current={index === step ? "step" : undefined}
            className={index < step ? "is-complete" : ""}
          >
            <span aria-hidden="true">
              {index < step ? <Checkmark20Regular /> : index + 1}
            </span>
            <span>{title}</span>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/** Keep the existing page visible while a short or stepped form is open. */
export function FormDrawer({ title, description, steps, step = 0, stepTitle,
  stepDescription, onSubmit, onBack, onClose, submitLabel = "Save",
  pendingLabel = "Saving…", busy = false, errors, children, notice, open = true, compact = false }) {
  const id = useId();
  const formRef = useRef(null);
  const headingRef = useRef(null);
  useRestoreFocus();
  useFormFocus(formRef, headingRef, step, errors, busy);
  const last = !steps || step === steps.length - 1;
  return <OverlayDrawer open={open} position="end" size="medium" className={`dwella-drawer dwella-form-drawer${compact ? " is-compact" : ""}`}
    onOpenChange={(_, data) => { if (!data.open && !busy) onClose(); }}>
    <DrawerHeader>
      <DrawerHeaderTitle action={<Button appearance="subtle" icon={<Dismiss20Regular />}
        aria-label="Close" disabled={busy} onClick={onClose} />}>{title}</DrawerHeaderTitle>
      {description && (!steps || step === 0) && <p className="dwella-drawer-note">{description}</p>}
      {steps && <FormSteps steps={steps} step={step} />}
    </DrawerHeader>
    <DrawerBody>
      <form id={id} ref={formRef} noValidate onSubmit={onSubmit} aria-busy={busy} className="dwella-form-drawer-content">
        {steps && <div className="dwella-form-step-heading">
          <span className="dwella-form-count" role="status">Step {step + 1} of {steps.length}</span>
          <h2 ref={headingRef} tabIndex={-1}>{stepTitle || steps[step]}</h2>
          {stepDescription && <p>{stepDescription}</p>}
        </div>}
        <fieldset disabled={busy} className="dwella-form-body">{children}</fieldset>
        {notice}
      </form>
    </DrawerBody>
    <DrawerFooter className="dwella-drawer-footer">
      {step > 0 && onBack ? <Button onClick={onBack} disabled={busy}>Back</Button>
        : <Button onClick={onClose} disabled={busy}>Cancel</Button>}
      <Button form={id} type="submit" appearance="primary" disabled={busy}>
        {busy ? pendingLabel : last ? submitLabel : "Continue"}
      </Button>
    </DrawerFooter>
  </OverlayDrawer>;
}

/** A focused submission, with Fluent's focus trap and vertically scrolling body. */
export function FormModal({ title, description, onSubmit, onClose, children,
  submitLabel = "Save changes", pendingLabel = "Saving…", busy = false,
  errors, notice, wide = false }) {
  const formRef = useRef(null);
  const headingRef = useRef(null);
  useRestoreFocus();
  useFormFocus(formRef, headingRef, 0, errors, busy);
  return <Dialog open onOpenChange={(_, data) => { if (!data.open && !busy) onClose(); }}>
    <DialogSurface className={`dwella-form-modal${wide ? " is-wide" : ""}`}>
      <form ref={formRef} noValidate onSubmit={onSubmit} aria-busy={busy} className="dwella-modal-form">
        <DialogBody>
          <div className="dwella-modal-heading">
            <DialogTitle>{title}</DialogTitle>
            <Button appearance="subtle" icon={<Dismiss20Regular />}
              aria-label="Close" disabled={busy} onClick={onClose} />
          </div>
          <DialogContent className="dwella-modal-content">
            {description && <p className="dwella-modal-description">{description}</p>}
            <fieldset disabled={busy} className="dwella-form-body">{children}</fieldset>
            {notice}
          </DialogContent>
          <DialogActions className="dwella-modal-actions">
            <Button onClick={onClose} disabled={busy}>Cancel</Button>
            <Button type="submit" appearance="primary" disabled={busy}>
              {busy ? pendingLabel : submitLabel}
            </Button>
          </DialogActions>
        </DialogBody>
      </form>
    </DialogSurface>
  </Dialog>;
}

function useRestoreFocus() {
  const openerRef = useRef(typeof document === "undefined" ? null : document.activeElement);
  useEffect(() => () => {
    // Conditional overlays have no Fluent trigger to restore focus to.
    requestAnimationFrame(() => {
      if (openerRef.current?.isConnected && !document.querySelector('[role="dialog"]'))
        openerRef.current.focus({ preventScroll: true });
    });
  }, []);
}

function useFormFocus(formRef, headingRef, step, errors, busy) {
  const previousErrors = useRef({});
  const focusInvalid = useCallback(() => formRef.current?.querySelector(
    "[aria-invalid='true'], .dwella-field-invalid input, .dwella-field-invalid select, .dwella-field-invalid textarea, .dwella-field-invalid button",
  ), [formRef]);
  useEffect(() => {
    const request = requestAnimationFrame(() => (focusInvalid() || headingRef.current)?.focus());
    return () => cancelAnimationFrame(request);
  }, [step, focusInvalid, headingRef]);
  useEffect(() => {
    // Mutation callbacks can set field errors before disabled controls re-enable.
    if (busy) return undefined;
    const added = Object.keys(errors || {}).some((key) => !previousErrors.current[key]);
    previousErrors.current = errors || {};
    if (!added) return undefined;
    const request = requestAnimationFrame(() => focusInvalid()?.focus());
    return () => cancelAnimationFrame(request);
  }, [errors, busy, focusInvalid]);
}

/** A document-scrolling creation surface inside the existing app shell. */
export function FormPage({
  title,
  description,
  steps,
  step = 0,
  stepTitle,
  stepDescription,
  onSubmit,
  onBack,
  onClose,
  submitLabel = "Save",
  pendingLabel = "Saving…",
  busy = false,
  errors,
  children,
  notice,
}) {
  const formRef = useRef(null);
  const headingRef = useRef(null);
  useFormFocus(formRef, headingRef, step, errors, busy);
  const last = !steps || step === steps.length - 1;
  return (
    <section className="dwella-form-page">
      <header className="dwella-page-header">
        <div className="dwella-page-header-copy">
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
        {onClose && (
          <Button
            appearance="subtle"
            icon={<Dismiss20Regular />}
            aria-label={`Close ${title.toLowerCase()}`}
            onClick={onClose}
            disabled={busy}
          />
        )}
      </header>
      <form
        ref={formRef}
        className="dwella-form-sheet"
        noValidate
        onSubmit={onSubmit}
        aria-busy={busy}
      >
        {steps && <FormSteps steps={steps} step={step} />}
        <div className="dwella-form-step-heading">
          {steps && (
            <span className="dwella-form-count" role="status">
              Step {step + 1} of {steps.length}
            </span>
          )}
          <h2 ref={headingRef} tabIndex={-1}>
            {stepTitle || title}
          </h2>
          {stepDescription && <p>{stepDescription}</p>}
        </div>
        <fieldset disabled={busy} className="dwella-form-body">
          {children}
        </fieldset>
        {notice}
        <footer className="dwella-form-actions">
          {step > 0 && onBack ? (
            <Button type="button" onClick={onBack} disabled={busy}>
              Back
            </Button>
          ) : onClose ? (
            <Button type="button" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
          ) : (
            <span />
          )}
          <Button type="submit" appearance="primary" disabled={busy}>
            {busy ? pendingLabel : last ? submitLabel : "Continue"}
          </Button>
        </footer>
      </form>
    </section>
  );
}

export function FormReview({ items, onEdit }) {
  return (
    <dl className="dwella-form-review">
      {items.map(({ label, value, step }) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value === "" || value === null || value === undefined ? "Not provided" : value}</dd>
          {onEdit && step !== undefined && (
            <Button
              type="button"
              appearance="subtle"
              size="small"
              onClick={() => onEdit(step)}
              aria-label={`Edit ${label.toLowerCase()}`}
            >
              Edit
            </Button>
          )}
        </div>
      ))}
    </dl>
  );
}
