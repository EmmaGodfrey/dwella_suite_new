import React, { Fragment, useState } from "react";
import { Alert, Card, CardBody, Col, Container, FormGroup, Input, Label, Row } from "reactstrap";
import { toast } from "react-toastify";

import { Breadcrumbs, Btn, H4, P } from "../../AbstractElements";
import HeaderCard from "../Common/Component/HeaderCard";
import { useCurrentUserQuery } from "../../Services/queries";
import {
  useTwoFactorDisableMutation,
  useTwoFactorSetupMutation,
  useTwoFactorSetupVerifyMutation,
} from "../../Services/mutations";

const Security = () => {
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const { data: user } = useCurrentUserQuery();
  const setupMutation = useTwoFactorSetupMutation({
    onSuccess: setSetup,
    onError: (error) => toast.error(error.message || "Could not start 2FA setup"),
  });
  const verifyMutation = useTwoFactorSetupVerifyMutation({
    onSuccess: () => {
      setSetup(null);
      setCode("");
      toast.success("Two-factor authentication enabled.");
    },
    onError: (error) => toast.error(error.message || "Invalid authentication code"),
  });
  const disableMutation = useTwoFactorDisableMutation({
    onSuccess: () => toast.success("Two-factor authentication disabled."),
    onError: (error) => toast.error(error.message || "Could not disable 2FA"),
  });

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Security" parent="Dwella Suite" title="Security" />
      <Container fluid={true}>
        <Row>
          <Col xl="7">
            <Card>
              <HeaderCard title="Account Protection" span1="Manage sign-in protections for your admin account." />
              <CardBody>
                <div className="d-flex justify-content-between align-items-start gap-3">
                  <div>
                    <H4>Two-Factor Authentication</H4>
                    <P>{user?.has_two_factor ? "2FA is enabled for this account." : "Add an authenticator code before account access is granted."}</P>
                  </div>
                  {user?.has_two_factor ? (
                    <Btn attrBtn={{ color: "outline-danger", disabled: disableMutation.isPending, onClick: () => disableMutation.mutate() }}>
                      Disable
                    </Btn>
                  ) : (
                    <Btn attrBtn={{ color: "primary", disabled: setupMutation.isPending, onClick: () => setupMutation.mutate() }}>
                      {setupMutation.isPending ? "Starting..." : "Set Up 2FA"}
                    </Btn>
                  )}
                </div>
                {setup && (
                  <div className="mt-4">
                    <Alert color="light" className="border">
                      <strong>Secret:</strong> <code>{setup.secret}</code>
                      <br />
                      <strong>Authenticator URI:</strong> <code className="text-break">{setup.provisioning_uri}</code>
                    </Alert>
                    <FormGroup>
                      <Label>6-digit code</Label>
                      <Input inputMode="numeric" maxLength="6" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
                    </FormGroup>
                    <Btn attrBtn={{ color: "primary", disabled: verifyMutation.isPending, onClick: () => verifyMutation.mutate({ code }) }}>
                      {verifyMutation.isPending ? "Verifying..." : "Verify 2FA"}
                    </Btn>
                  </div>
                )}
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Security;
