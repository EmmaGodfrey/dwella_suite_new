import React, { useEffect, useMemo, useRef, useState } from "react";
import "./profile.scss";
import { Avatar, Badge, Button, Dropdown, Field, Input, Option } from "@fluentui/react-components";
import { ArrowUpload24Regular, Camera24Regular, CheckmarkCircle24Regular, Shield24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { resolveMediaUrl } from "../../Services/apiClient";
import { useCurrentUserQuery } from "../../Services/queries";
import { useAvatarUploadMutation, useIdentityVerificationMutation, useProfileUpdateMutation } from "../../Services/mutations";
import { PageSection, defaultStatusColor } from "../../shared/components";
import { useFormErrors } from "../../shared/useFormErrors";

const displayStatus = (value) => {
  const status = (value || "not_submitted").replace(/_/g, " ");
  return status.charAt(0).toUpperCase() + status.slice(1);
};
const documentTypes = [
  { value: "nrc", label: "NRC" },
  { value: "passport", label: "Passport" },
  { value: "drivers_license", label: "Driver's License" },
];
const documentLabel = (value) => documentTypes.find((item) => item.value === value)?.label || "";
const validatePhone = (value) => {
  const cleaned = value.trim();
  if (!cleaned) return "";
  return /^\+?[0-9 ]{7,20}$/.test(cleaned) ? "" : "Enter a valid phone number.";
};

const Profile = () => {
  const avatarInputRef = useRef(null);
  const documentInputRef = useRef(null);
  const { data: user, isLoading, isError, error } = useCurrentUserQuery();
  const [form, setForm] = useState({ firstName: "", lastName: "", phoneNumber: "", jobTitle: "" });
  const [verification, setVerification] = useState({ legalName: "", documentType: "nrc", documentNumber: "", documentImage: null });
  const profileErrors = useFormErrors();
  const verificationErrors = useFormErrors();

  const updateForm = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }));
    profileErrors.clearError(name);
  };

  const updateVerification = (name, value) => {
    setVerification((current) => ({ ...current, [name]: value }));
    verificationErrors.clearError(name);
  };

  useEffect(() => {
    if (!user) return;
    setForm({
      firstName: user.first_name || "",
      lastName: user.last_name || "",
      phoneNumber: user.profile?.phone_number || "",
      jobTitle: user.profile?.job_title || "",
    });
  }, [user]);

  const initials = useMemo(() => {
    const source = `${user?.first_name || ""} ${user?.last_name || ""}`.trim() || user?.email || "DS";
    return source.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  }, [user]);

  const profileMutation = useProfileUpdateMutation({
    onSuccess: () => toast.success("Profile updated."),
    onError: (mutationError) => toast.error(mutationError.message || "Could not update profile"),
  });
  const avatarMutation = useAvatarUploadMutation({
    onSuccess: () => toast.success("Profile picture updated."),
    onError: (mutationError) => toast.error(mutationError.message || "Could not upload profile picture"),
  });
  const verificationMutation = useIdentityVerificationMutation({
    onSuccess: () => {
      toast.success("Verification submitted for review.");
      setVerification({ legalName: "", documentType: "nrc", documentNumber: "", documentImage: null });
    },
    onError: (mutationError) => toast.error(mutationError.message || "Could not submit verification"),
  });

  const submitProfile = (event) => {
    event.preventDefault();

    const valid = profileErrors.validate({
      firstName: () => (form.firstName.trim() ? "" : "First name is required."),
      lastName: () => (form.lastName.trim() ? "" : "Last name is required."),
      phoneNumber: () => validatePhone(form.phoneNumber),
    }, event.currentTarget);

    if (!valid) return;

    profileMutation.mutate({
      first_name: form.firstName.trim(),
      last_name: form.lastName.trim(),
      phone_number: form.phoneNumber.trim(),
      job_title: form.jobTitle.trim(),
    });
  };

  const submitVerification = (event) => {
    event.preventDefault();

    const valid = verificationErrors.validate({
      legalName: () => (verification.legalName.trim().split(/\s+/).filter(Boolean).length >= 2 ? "" : "Enter your full legal name."),
      documentNumber: () => (verification.documentNumber.trim().length >= 4 ? "" : "Document number is too short."),
      documentImage: () => (verification.documentImage ? "" : "Attach a document image."),
    }, event.currentTarget);

    if (!valid) return;

    verificationMutation.mutate(verification);
  };

  const currentStatus = user?.identity_verification?.status || "not_submitted";
  const canSubmitVerification = !["approved", "pending"].includes(currentStatus);
  const fullName = isLoading ? "Loading..." : `${user?.first_name || ""} ${user?.last_name || ""}`.trim() || user?.email;
  const avatarUrl = resolveMediaUrl(user?.profile?.avatar_url);

  return (
    <div className="dwella-screen dwella-profile-screen">
      {isError ? <div className="dwella-alert danger" role="alert">Unable to load profile: {error.message}</div> : null}
      <section className="dwella-profile-grid">
        <aside className="dwella-profile-summary">
          <Avatar name={fullName} image={avatarUrl ? { src: avatarUrl } : undefined} initials={initials} size={96} />
          <strong className="dwella-profile-name">{fullName}</strong>
          <span className="dwella-profile-email">{user?.email}</span>
          <input ref={avatarInputRef} hidden type="file" accept="image/*" onChange={(event) => {
            const file = event.target.files?.[0];
            // Clear the input so re-picking the same file still fires a change.
            event.target.value = "";
            if (file) avatarMutation.mutate(file);
          }} />
          <Button appearance="secondary" icon={<Camera24Regular />} disabled={avatarMutation.isPending} onClick={() => avatarInputRef.current?.click()}>
            {avatarMutation.isPending ? "Uploading..." : "Change photo"}
          </Button>
          <div className="dwella-chip-row centered">
            <Badge appearance="tint" color={user?.has_two_factor ? "success" : "subtle"}>2FA {user?.has_two_factor ? "enabled" : "off"}</Badge>
            <Badge appearance="tint" color={defaultStatusColor(currentStatus)}>{displayStatus(currentStatus)}</Badge>
          </div>
        </aside>

        <div className="dwella-profile-stack">
          <PageSection className="dwella-profile-section" title="Account details" note="Keep your admin identity accurate for audit trails and ownership records.">
            <form noValidate onSubmit={submitProfile}>
              <div className="dwella-form-grid">
                <Field label="First name" required {...profileErrors.fieldProps("firstName")}><Input value={form.firstName} onChange={(_, data) => updateForm("firstName", data.value)} /></Field>
                <Field label="Last name" required {...profileErrors.fieldProps("lastName")}><Input value={form.lastName} onChange={(_, data) => updateForm("lastName", data.value)} /></Field>
                <Field label="Phone number" {...profileErrors.fieldProps("phoneNumber")}><Input value={form.phoneNumber} onChange={(_, data) => updateForm("phoneNumber", data.value)} /></Field>
                <Field label="Role / job title" {...profileErrors.fieldProps("jobTitle")}><Input value={form.jobTitle} onChange={(_, data) => updateForm("jobTitle", data.value)} /></Field>
              </div>
              <footer><Button appearance="primary" type="submit" disabled={profileMutation.isPending}>{profileMutation.isPending ? "Saving..." : "Save Profile"}</Button></footer>
            </form>
          </PageSection>

          <PageSection className="dwella-profile-section" title="Identity verification" note="Submit identity details so sensitive operations can require a verified person.">
            <form noValidate onSubmit={submitVerification}>
              <div className={`dwella-verification-state${currentStatus === "approved" ? " is-approved" : ""}`}>
                <span>{currentStatus === "approved" ? <CheckmarkCircle24Regular /> : <Shield24Regular />}</span>
                <div>
                  <strong className="dwella-verification-status">{displayStatus(currentStatus)}</strong>
                  <p className="dwella-verification-note">{currentStatus === "pending" ? "Your submitted details are awaiting review." : currentStatus === "approved" ? "Your identity has been verified." : "Submit your legal name and identity document for review."}</p>
                  {user?.identity_verification?.rejection_reason ? <div className="dwella-alert danger" role="alert">{user.identity_verification.rejection_reason}</div> : null}
                </div>
              </div>
              {canSubmitVerification ? (
                <>
                  <div className="dwella-form-grid">
                    <Field label="Legal name" required {...verificationErrors.fieldProps("legalName")}><Input value={verification.legalName} onChange={(_, data) => updateVerification("legalName", data.value)} /></Field>
                    <Field label="Document type"><Dropdown selectedOptions={[verification.documentType]} value={documentLabel(verification.documentType)} onOptionSelect={(_, data) => updateVerification("documentType", data.optionValue)}>{documentTypes.map((item) => <Option key={item.value} value={item.value}>{item.label}</Option>)}</Dropdown></Field>
                    <Field label="Document number" required {...verificationErrors.fieldProps("documentNumber")}><Input value={verification.documentNumber} onChange={(_, data) => updateVerification("documentNumber", data.value)} /></Field>
                    <Field label="Document image" required {...verificationErrors.fieldProps("documentImage")}>
                      <input ref={documentInputRef} hidden type="file" accept="image/*" onChange={(event) => {
                        const file = event.target.files?.[0] || null;
                        event.target.value = "";
                        updateVerification("documentImage", file);
                      }} />
                      <Button appearance="secondary" icon={<ArrowUpload24Regular />} onClick={() => documentInputRef.current?.click()}>{verification.documentImage?.name || "Choose document"}</Button>
                    </Field>
                  </div>
                  <footer><Button appearance="primary" type="submit" icon={<ArrowUpload24Regular />} disabled={verificationMutation.isPending}>{verificationMutation.isPending ? "Submitting..." : "Submit Verification"}</Button></footer>
                </>
              ) : null}
            </form>
          </PageSection>
        </div>
      </section>
    </div>
  );
};

export default Profile;
