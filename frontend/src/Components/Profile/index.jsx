import React, { Fragment, useEffect, useMemo, useState } from "react";
import { Alert, Badge, Card, CardBody, Col, Container, FormGroup, Input, Label, Row } from "reactstrap";
import { Camera, CheckCircle, Shield, Upload } from "react-feather";
import { toast } from "react-toastify";

import { Breadcrumbs, Btn, H4, H5, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
import { useCurrentUserQuery } from "../../Services/queries";
import {
  useAvatarUploadMutation,
  useIdentityVerificationMutation,
  useProfileUpdateMutation,
} from "../../Services/mutations";

const statusColor = {
  approved: "success",
  pending: "warning",
  rejected: "danger",
  not_submitted: "secondary",
};

const displayStatus = (value) => (value || "not_submitted").replace("_", " ");

const validatePhone = (value) => {
  const cleaned = value.trim();
  if (!cleaned) return "";
  return /^\+?[0-9 ]{7,20}$/.test(cleaned) ? "" : "Enter a valid phone number.";
};

const Profile = () => {
  const { data: user, isLoading, isError, error } = useCurrentUserQuery();
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    phoneNumber: "",
    jobTitle: "",
  });
  const [verification, setVerification] = useState({
    legalName: "",
    documentType: "nrc",
    documentNumber: "",
    documentImage: null,
  });

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
    return source
      .split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
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
    if (!form.firstName.trim() || !form.lastName.trim()) {
      toast.error("First and last name are required.");
      return;
    }
    if (phoneError) {
      toast.error(phoneError);
      return;
    }
    profileMutation.mutate({
      first_name: form.firstName.trim(),
      last_name: form.lastName.trim(),
      phone_number: form.phoneNumber.trim(),
      job_title: form.jobTitle.trim(),
    });
  };

  const submitVerification = (event) => {
    event.preventDefault();
    if (verification.legalName.trim().split(" ").length < 2) {
      toast.error("Enter your full legal name.");
      return;
    }
    if (verification.documentNumber.trim().length < 4) {
      toast.error("Document number is too short.");
      return;
    }
    if (!verification.documentImage) {
      toast.error("Attach a document image.");
      return;
    }
    verificationMutation.mutate(verification);
  };

  const currentStatus = user?.identity_verification?.status || "not_submitted";
  const canSubmitVerification = !["approved", "pending"].includes(currentStatus);

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Profile" parent="Dwella Suite" title="Profile" />
      <Container fluid={true}>
        {isError ? <Alert color="danger">Unable to load profile: {error.message}</Alert> : null}
        <Row>
          <Col xl="4">
            <Card>
              <CardBody className="text-center">
                <div className="mx-auto mb-3 rounded-circle overflow-hidden bg-primary d-flex align-items-center justify-content-center" style={{ width: 112, height: 112 }}>
                  {user?.profile?.avatar_url ? (
                    <img src={user.profile.avatar_url} alt="Profile" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  ) : (
                    <span className="text-white fs-2 fw-semibold">{initials}</span>
                  )}
                </div>
                <H4>{isLoading ? "Loading..." : `${user?.first_name || ""} ${user?.last_name || ""}`.trim() || user?.email}</H4>
                <P attrPara={{ className: "text-muted mb-3" }}>{user?.email}</P>
                <Label className="btn btn-outline-primary mb-0">
                  <Camera size={16} className="me-2" />
                  Change Photo
                  <Input
                    type="file"
                    accept="image/*"
                    className="d-none"
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      if (file) avatarMutation.mutate(file);
                    }}
                  />
                </Label>
                <div className="mt-4 d-flex justify-content-center gap-2">
                  <Badge color={user?.has_two_factor ? "success" : "secondary"}>
                    2FA {user?.has_two_factor ? "enabled" : "off"}
                  </Badge>
                  <Badge color={statusColor[currentStatus]}>{displayStatus(currentStatus)}</Badge>
                </div>
              </CardBody>
            </Card>
          </Col>
          <Col xl="8">
            <Card>
              <HeaderCard title="Account Details" span1="Keep your admin identity accurate for audit trails and ownership records." />
              <CardBody>
                <Row>
                  <Col md="6">
                    <FormGroup>
                      <Label>First Name</Label>
                      <Input value={form.firstName} onChange={(event) => setForm({ ...form, firstName: event.target.value })} />
                    </FormGroup>
                  </Col>
                  <Col md="6">
                    <FormGroup>
                      <Label>Last Name</Label>
                      <Input value={form.lastName} onChange={(event) => setForm({ ...form, lastName: event.target.value })} />
                    </FormGroup>
                  </Col>
                  <Col md="6">
                    <FormGroup>
                      <Label>Phone Number</Label>
                      <Input value={form.phoneNumber} onChange={(event) => setForm({ ...form, phoneNumber: event.target.value })} />
                    </FormGroup>
                  </Col>
                  <Col md="6">
                    <FormGroup>
                      <Label>Role / Job Title</Label>
                      <Input value={form.jobTitle} onChange={(event) => setForm({ ...form, jobTitle: event.target.value })} />
                    </FormGroup>
                  </Col>
                </Row>
                <Btn attrBtn={{ color: "primary", disabled: profileMutation.isPending, onClick: submitProfile }}>
                  {profileMutation.isPending ? "Saving..." : "Save Profile"}
                </Btn>
              </CardBody>
            </Card>

            <Card>
              <HeaderCard title="Identity Verification" span1="Submit identity details so sensitive operations can require a verified person." />
              <CardBody>
                <div className="d-flex align-items-start gap-3 mb-4">
                  <div className="bg-light rounded-circle d-flex align-items-center justify-content-center" style={{ width: 42, height: 42 }}>
                    {currentStatus === "approved" ? <CheckCircle size={20} className="text-success" /> : <Shield size={20} className="text-primary" />}
                  </div>
                  <div>
                    <H5 attrH5={{ className: "text-capitalize" }}>{displayStatus(currentStatus)}</H5>
                    <P attrPara={{ className: "text-muted mb-0" }}>
                      {currentStatus === "pending"
                        ? "Your submitted details are awaiting review."
                        : currentStatus === "approved"
                          ? "Your identity has been verified."
                          : "Submit your legal name and identity document for review."}
                    </P>
                    {user?.identity_verification?.rejection_reason ? (
                      <Alert color="danger" className="mt-3 mb-0">
                        {user.identity_verification.rejection_reason}
                      </Alert>
                    ) : null}
                  </div>
                </div>

                {canSubmitVerification ? (
                  <Row>
                    <Col md="6">
                      <FormGroup>
                        <Label>Legal Name</Label>
                        <Input value={verification.legalName} onChange={(event) => setVerification({ ...verification, legalName: event.target.value })} />
                      </FormGroup>
                    </Col>
                    <Col md="6">
                      <FormGroup>
                        <Label>Document Type</Label>
                        <Input type="select" value={verification.documentType} onChange={(event) => setVerification({ ...verification, documentType: event.target.value })}>
                          <option value="nrc">NRC</option>
                          <option value="passport">Passport</option>
                          <option value="drivers_license">Driver's License</option>
                        </Input>
                      </FormGroup>
                    </Col>
                    <Col md="6">
                      <FormGroup>
                        <Label>Document Number</Label>
                        <Input value={verification.documentNumber} onChange={(event) => setVerification({ ...verification, documentNumber: event.target.value })} />
                      </FormGroup>
                    </Col>
                    <Col md="6">
                      <FormGroup>
                        <Label>Document Image</Label>
                        <Input type="file" accept="image/*" onChange={(event) => setVerification({ ...verification, documentImage: event.target.files?.[0] || null })} />
                      </FormGroup>
                    </Col>
                    <Col sm="12">
                      <Btn attrBtn={{ color: "primary", disabled: verificationMutation.isPending, onClick: submitVerification }}>
                        <Upload size={16} className="me-2" />
                        {verificationMutation.isPending ? "Submitting..." : "Submit Verification"}
                      </Btn>
                    </Col>
                  </Row>
                ) : null}
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Profile;
