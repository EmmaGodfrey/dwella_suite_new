import React, { useEffect, useMemo, useRef, useState } from "react";
import { Avatar, Badge, Button, Card, Dropdown, Field, Input, Option, Text, Title2, Title3 } from "@fluentui/react-components";
import { ArrowUpload24Regular, Camera24Regular, CheckmarkCircle24Regular, Shield24Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { useAvatarUploadMutation, useIdentityVerificationMutation, useProfileUpdateMutation } from "../../Services/mutations";

const displayStatus = (value) => (value || "not_submitted").replace("_", " ");
const statusIntent = (value) => value === "approved" ? "success" : value === "pending" ? "warning" : value === "rejected" ? "danger" : "subtle";
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
    onSuccess: () => toast.success("Verification submitted for review."),
    onError: (mutationError) => toast.error(mutationError.message || "Could not submit verification"),
  });

  const submitProfile = (event) => {
    event.preventDefault();
    const phoneError = validatePhone(form.phoneNumber);
    if (!form.firstName.trim() || !form.lastName.trim()) return toast.error("First and last name are required.");
    if (phoneError) return toast.error(phoneError);
    profileMutation.mutate({
      first_name: form.firstName.trim(),
      last_name: form.lastName.trim(),
      phone_number: form.phoneNumber.trim(),
      job_title: form.jobTitle.trim(),
    });
  };

  const submitVerification = (event) => {
    event.preventDefault();
    if (verification.legalName.trim().split(" ").length < 2) return toast.error("Enter your full legal name.");
    if (verification.documentNumber.trim().length < 4) return toast.error("Document number is too short.");
    if (!verification.documentImage) return toast.error("Attach a document image.");
    verificationMutation.mutate(verification);
  };

  const currentStatus = user?.identity_verification?.status || "not_submitted";
  const canSubmitVerification = !["approved", "pending"].includes(currentStatus);
  const fullName = isLoading ? "Loading..." : `${user?.first_name || ""} ${user?.last_name || ""}`.trim() || user?.email;

  return (
    <div className="dwella-screen dwella-profile-screen">
      {isError ? <div className="dwella-alert danger">Unable to load profile: {error.message}</div> : null}
      <section className="dwella-profile-grid">
        <Card className="dwella-card dwella-profile-summary" appearance="outline">
          <Avatar name={fullName} image={user?.profile?.avatar_url ? { src: user.profile.avatar_url } : undefined} initials={initials} size={96} />
          <Title2>{fullName}</Title2>
          <Text>{user?.email}</Text>
          <input ref={avatarInputRef} hidden type="file" accept="image/*" onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) avatarMutation.mutate(file);
          }} />
          <Button appearance="secondary" icon={<Camera24Regular />} onClick={() => avatarInputRef.current?.click()}>
            Change Photo
          </Button>
          <div className="dwella-chip-row centered">
            <Badge appearance="tint" color={user?.has_two_factor ? "success" : "subtle"}>2FA {user?.has_two_factor ? "enabled" : "off"}</Badge>
            <Badge appearance="tint" color={statusIntent(currentStatus)}>{displayStatus(currentStatus)}</Badge>
          </div>
        </Card>

        <div className="dwella-profile-stack">
          <Card className="dwella-card dwella-panel" appearance="outline">
            <form onSubmit={submitProfile}>
              <header className="dwella-panel-heading"><div><Title3>Account Details</Title3><Text>Keep your admin identity accurate for audit trails and ownership records.</Text></div></header>
              <div className="dwella-form-grid two">
                <Field label="First name"><Input value={form.firstName} onChange={(_, data) => setForm({ ...form, firstName: data.value })} /></Field>
                <Field label="Last name"><Input value={form.lastName} onChange={(_, data) => setForm({ ...form, lastName: data.value })} /></Field>
                <Field label="Phone number"><Input value={form.phoneNumber} onChange={(_, data) => setForm({ ...form, phoneNumber: data.value })} /></Field>
                <Field label="Role / job title"><Input value={form.jobTitle} onChange={(_, data) => setForm({ ...form, jobTitle: data.value })} /></Field>
              </div>
              <footer><Button appearance="primary" type="submit" disabled={profileMutation.isPending}>{profileMutation.isPending ? "Saving..." : "Save Profile"}</Button></footer>
            </form>
          </Card>

          <Card className="dwella-card dwella-panel" appearance="outline">
            <form onSubmit={submitVerification}>
              <header className="dwella-panel-heading"><div><Title3>Identity Verification</Title3><Text>Submit identity details so sensitive operations can require a verified person.</Text></div></header>
              <div className="dwella-verification-state">
                <span>{currentStatus === "approved" ? <CheckmarkCircle24Regular /> : <Shield24Regular />}</span>
                <div>
                  <Title3>{displayStatus(currentStatus)}</Title3>
                  <Text>{currentStatus === "pending" ? "Your submitted details are awaiting review." : currentStatus === "approved" ? "Your identity has been verified." : "Submit your legal name and identity document for review."}</Text>
                  {user?.identity_verification?.rejection_reason ? <div className="dwella-alert danger">{user.identity_verification.rejection_reason}</div> : null}
                </div>
              </div>
              {canSubmitVerification ? (
                <>
                  <div className="dwella-form-grid two">
                    <Field label="Legal name"><Input value={verification.legalName} onChange={(_, data) => setVerification({ ...verification, legalName: data.value })} /></Field>
                    <Field label="Document type"><Dropdown selectedOptions={[verification.documentType]} value={documentLabel(verification.documentType)} onOptionSelect={(_, data) => setVerification({ ...verification, documentType: data.optionValue })}>{documentTypes.map((item) => <Option key={item.value} value={item.value}>{item.label}</Option>)}</Dropdown></Field>
                    <Field label="Document number"><Input value={verification.documentNumber} onChange={(_, data) => setVerification({ ...verification, documentNumber: data.value })} /></Field>
                    <Field label="Document image">
                      <input ref={documentInputRef} hidden type="file" accept="image/*" onChange={(event) => setVerification({ ...verification, documentImage: event.target.files?.[0] || null })} />
                      <Button appearance="secondary" icon={<ArrowUpload24Regular />} onClick={() => documentInputRef.current?.click()}>{verification.documentImage?.name || "Choose document"}</Button>
                    </Field>
                  </div>
                  <footer><Button appearance="primary" type="submit" icon={<ArrowUpload24Regular />} disabled={verificationMutation.isPending}>{verificationMutation.isPending ? "Submitting..." : "Submit Verification"}</Button></footer>
                </>
              ) : null}
            </form>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Profile;
