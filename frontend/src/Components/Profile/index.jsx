import React, { useEffect, useMemo, useState } from "react";
import { Camera, CheckCircle, Shield, Upload } from "react-feather";
import { toast } from "react-toastify";

import { useCurrentUserQuery } from "../../Services/queries";
import { useAvatarUploadMutation, useIdentityVerificationMutation, useProfileUpdateMutation } from "../../Services/mutations";

const displayStatus = (value) => (value || "not_submitted").replace("_", " ");
const validatePhone = (value) => {
  const cleaned = value.trim();
  if (!cleaned) return "";
  return /^\+?[0-9 ]{7,20}$/.test(cleaned) ? "" : "Enter a valid phone number.";
};

const Field = ({ label, children }) => (
  <label className="dwella-field">
    <span>{label}</span>
    {children}
  </label>
);

const Profile = () => {
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
        <aside className="dwella-card dwella-profile-summary">
          <div className="dwella-profile-photo">
            {user?.profile?.avatar_url ? <img src={user.profile.avatar_url} alt="Profile" /> : <span>{initials}</span>}
          </div>
          <h2>{fullName}</h2>
          <p>{user?.email}</p>
          <label className="dwella-secondary-action file-action">
            <Camera size={16} />
            Change Photo
            <input
              type="file"
              accept="image/*"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) avatarMutation.mutate(file);
              }}
            />
          </label>
          <div className="dwella-chip-row centered">
            <span className={`dwella-chip ${user?.has_two_factor ? "managed" : "archived"}`}>2FA {user?.has_two_factor ? "enabled" : "off"}</span>
            <span className={`dwella-chip ${currentStatus}`}>{displayStatus(currentStatus)}</span>
          </div>
        </aside>

        <div className="dwella-profile-stack">
          <form className="dwella-card dwella-panel" onSubmit={submitProfile}>
            <header className="dwella-panel-heading">
              <div><h2>Account Details</h2><p>Keep your admin identity accurate for audit trails and ownership records.</p></div>
            </header>
            <div className="dwella-form-grid two">
              <Field label="First name"><input value={form.firstName} onChange={(event) => setForm({ ...form, firstName: event.target.value })} /></Field>
              <Field label="Last name"><input value={form.lastName} onChange={(event) => setForm({ ...form, lastName: event.target.value })} /></Field>
              <Field label="Phone number"><input value={form.phoneNumber} onChange={(event) => setForm({ ...form, phoneNumber: event.target.value })} /></Field>
              <Field label="Role / job title"><input value={form.jobTitle} onChange={(event) => setForm({ ...form, jobTitle: event.target.value })} /></Field>
            </div>
            <footer><button className="dwella-primary-action compact" disabled={profileMutation.isPending}>{profileMutation.isPending ? "Saving..." : "Save Profile"}</button></footer>
          </form>

          <form className="dwella-card dwella-panel" onSubmit={submitVerification}>
            <header className="dwella-panel-heading">
              <div><h2>Identity Verification</h2><p>Submit identity details so sensitive operations can require a verified person.</p></div>
            </header>
            <div className="dwella-verification-state">
              <span>{currentStatus === "approved" ? <CheckCircle size={20} /> : <Shield size={20} />}</span>
              <div>
                <h3>{displayStatus(currentStatus)}</h3>
                <p>{currentStatus === "pending" ? "Your submitted details are awaiting review." : currentStatus === "approved" ? "Your identity has been verified." : "Submit your legal name and identity document for review."}</p>
                {user?.identity_verification?.rejection_reason ? <div className="dwella-alert danger">{user.identity_verification.rejection_reason}</div> : null}
              </div>
            </div>
            {canSubmitVerification ? (
              <>
                <div className="dwella-form-grid two">
                  <Field label="Legal name"><input value={verification.legalName} onChange={(event) => setVerification({ ...verification, legalName: event.target.value })} /></Field>
                  <Field label="Document type">
                    <select value={verification.documentType} onChange={(event) => setVerification({ ...verification, documentType: event.target.value })}>
                      <option value="nrc">NRC</option>
                      <option value="passport">Passport</option>
                      <option value="drivers_license">Driver's License</option>
                    </select>
                  </Field>
                  <Field label="Document number"><input value={verification.documentNumber} onChange={(event) => setVerification({ ...verification, documentNumber: event.target.value })} /></Field>
                  <Field label="Document image"><input type="file" accept="image/*" onChange={(event) => setVerification({ ...verification, documentImage: event.target.files?.[0] || null })} /></Field>
                </div>
                <footer><button className="dwella-primary-action compact" disabled={verificationMutation.isPending}><Upload size={16} />{verificationMutation.isPending ? "Submitting..." : "Submit Verification"}</button></footer>
              </>
            ) : null}
          </form>
        </div>
      </section>
    </div>
  );
};

export default Profile;
