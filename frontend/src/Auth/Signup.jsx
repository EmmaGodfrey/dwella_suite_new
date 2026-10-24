import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Field, Input } from "@fluentui/react-components";
import { useRegistrationQuery } from "../Services/queries";
import { useRegisterMutation } from "../Services/mutations";
import { useFormErrors } from "../shared/useFormErrors";
import AuthTour from "./AuthTour";

const names = ["first_name", "last_name", "email", "password", "confirm"];
export default function Signup() {
  const navigate = useNavigate();
  const registration = useRegistrationQuery();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const { validate, fieldProps, clearError, showServerErrors } =
    useFormErrors();
  const mutation = useRegisterMutation({
    onSuccess: (data) => navigate("/verify-email", { replace: true, state: { deliveryFailed: data.verification_delivery?.sent === false } }),
    onError: (error) => showServerErrors(error.data, names),
  });
  const submit = (event) => {
    event.preventDefault();
    if (
      !validate(
        {
          first_name: () =>
            form.first_name.trim() ? "" : "Enter your first name.",
          last_name: () =>
            form.last_name.trim() ? "" : "Enter your last name.",
          email: () =>
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())
              ? ""
              : "Enter a valid email address.",
          password: () =>
            form.password.length >= 10 && !/^\d+$/.test(form.password)
              ? ""
              : "Use at least 10 characters, not all digits.",
          confirm: () =>
            form.password === form.confirm ? "" : "Passwords must match.",
        },
        event.currentTarget,
      )
    )
      return;
    mutation.mutate({
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim().toLowerCase(),
      password: form.password,
    });
  };
  return (
    <main className="dwella-auth-page">
      <section className="dwella-auth-hero">
        <div className="dwella-auth-brand">
          <img src="/assets/images/logo/dwella-mark-white.png" alt="" />
          <span>Dwella</span>
        </div>
        <AuthTour />
        <img
          className="dwella-auth-watermark"
          src="/assets/images/logo/dwella-mark-white.png"
          alt=""
          aria-hidden="true"
        />
      </section>
      <section className="dwella-auth-panel">
        <form className="dwella-auth-form" onSubmit={submit} noValidate>
          <div className="dwella-auth-compact-brand">
            <img src="/assets/images/logo/dwella-mark.png" alt="" />
            <span>Dwella</span>
          </div>
          <header className="dwella-auth-heading">
            <h1>Create your account</h1>
            <p>Start managing your properties with Dwella.</p>
          </header>
          {registration.isLoading ? (
            <p role="status">Checking beta availability…</p>
          ) : registration.isError ? (
            <div role="alert">
              <p>Could not check registration.</p>
              <Button onClick={() => registration.refetch()}>Retry</Button>
            </div>
          ) : !registration.data.open ? (
            <p>
              The beta opens 18 November 2026.{" "}
              <a href="https://dwella.properties/#beta">Join the beta list</a>{" "}
              for launch updates.
            </p>
          ) : (
            <>
              <div className="dwella-auth-fields dwella-signup-fields">
                {[
                  ["first_name", "First name", "given-name"],
                  ["last_name", "Last name", "family-name"],
                  ["email", "Email address", "email"],
                  ["password", "Password", "new-password"],
                  ["confirm", "Confirm password", "new-password"],
                ].map(([name, label, autoComplete]) => (
                  <Field key={name} label={label} {...fieldProps(name)} className={`${!["first_name", "last_name"].includes(name) ? "dwella-field-wide" : ""} ${fieldProps(name).className || ""}`}>
                    <Input
                      name={name}
                      value={form[name]}
                      autoComplete={autoComplete}
                      type={
                        name === "email"
                          ? "email"
                          : ["password", "confirm"].includes(name)
                            ? "password"
                            : "text"
                      }
                      maxLength={
                        name === "email"
                          ? 150
                          : name === "password" || name === "confirm"
                            ? 128
                            : 150
                      }
                      onChange={(_, data) => {
                        setForm((old) => ({ ...old, [name]: data.value }));
                        clearError(name);
                      }}
                    />
                  </Field>
                ))}
              </div>
              <p className="dwella-muted-copy">
                Use a permanent email and a password of at least 10 characters.
              </p>
              {mutation.isError ? (
                <p role="alert">{mutation.error.message}</p>
              ) : null}
              <Button
                className="dwella-auth-submit"
                type="submit"
                appearance="primary"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? "Creating account…" : "Create account"}
              </Button>
            </>
          )}
          <p className="dwella-auth-signup">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </section>
    </main>
  );
}
