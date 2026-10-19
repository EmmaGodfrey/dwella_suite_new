import { useCallback, useState } from "react";
import { toast } from "react-toastify";

/**
 * Form validation convention for the app.
 *
 * Rule failures are shown inline on the offending field (Fluent's Field renders
 * the message and sets aria-invalid/aria-describedby for us) and summarised by a
 * single toast. Never toast rule failures one at a time -- the toast says how
 * many fields need attention, the fields themselves say what is wrong.
 *
 *   const { validate, clearError, fieldProps } = useFormErrors();
 *
 *   const submit = (event) => {
 *     event.preventDefault();
 *     const ok = validate({
 *       email: () => (looksValid ? "" : "Enter a valid email address."),
 *     }, event.currentTarget);
 *     if (!ok) return;
 *     mutation.mutate(...);
 *   };
 *
 *   <Field label="Email" {...fieldProps("email")}>
 *     <Input onChange={(_, d) => { setEmail(d.value); clearError("email"); }} />
 *   </Field>
 *
 * A rule returns an empty string when the value is acceptable, or the message to
 * display when it is not.
 */
export const useFormErrors = () => {
  const [errors, setErrors] = useState({});

  const clearError = useCallback((name) => {
    setErrors((current) => {
      if (!current[name]) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
  }, []);

  const clearAll = useCallback(() => setErrors({}), []);

  const validate = useCallback((rules, formElement) => {
    const found = {};

    for (const [name, rule] of Object.entries(rules)) {
      const message = rule();
      if (message) found[name] = message;
    }

    setErrors(found);

    const count = Object.keys(found).length;
    if (count === 0) return true;

    toast.error(count === 1 ? "Fix the highlighted field." : `Fix the ${count} highlighted fields.`);

    if (formElement) {
      // Deferred so the invalid state has been committed and the control exists.
      requestAnimationFrame(() => formElement.querySelector("[aria-invalid='true']")?.focus());
    }

    return false;
  }, []);

  // Puts the API's field errors (`error.data`, from apiClient) on the matching
  // fields. Nested serializers come back nested, so `{lease: {unit: [...]}}` is
  // flattened to the `lease.unit` field name. Returns false when none matched,
  // so the caller can fall back to a toast.
  const showServerErrors = useCallback((data, knownFields) => {
    if (!data || typeof data !== "object") return false;
    const found = {};
    const walk = (value, prefix) => {
      if (Array.isArray(value)) {
        if (typeof value[0] === "string" && knownFields.includes(prefix)) found[prefix] = value[0];
        return;
      }
      if (value && typeof value === "object") {
        Object.entries(value).forEach(([key, inner]) => walk(inner, prefix ? `${prefix}.${key}` : key));
      }
    };
    walk(data, "");
    if (!Object.keys(found).length) return false;
    setErrors(found);
    toast.error(Object.keys(found).length === 1 ? "Fix the highlighted field." : `Fix the ${Object.keys(found).length} highlighted fields.`);
    return true;
  }, []);

  const fieldProps = useCallback(
    (name) => ({
      validationState: errors[name] ? "error" : "none",
      validationMessage: errors[name],
      className: errors[name] ? "dwella-field-invalid" : undefined,
    }),
    [errors]
  );

  return { errors, validate, clearError, clearAll, fieldProps, showServerErrors };
};
