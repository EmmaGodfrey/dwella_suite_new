import React, { Fragment, useState } from "react";
import { Col, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P } from "../AbstractElements";
import { EmailAddress, ForgotPassword, Password, RememberPassword } from "../Constant";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import { useLoginMutation } from "../Services/mutations";
import SocialAuth from "./Tabs/LoginTab/SocialAuth";

const Login = ({ selected }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@dwella.local");
  const [password, setPassword] = useState("admin12345");
  const [togglePassword, setTogglePassword] = useState(false);
  const loginMutation = useLoginMutation({
    onSuccess: () => navigate("/dashboard", { replace: true }),
    onError: (error) => toast.error(error.message || "Login failed"),
  });

  const loginAuth = async (e) => {
    e.preventDefault();
    loginMutation.mutate({ email, password });
  };

  return (
    <Fragment>
      <div className="p-0 container-fluid">
        <Row>
          <Col className="col-12">
            <div className="login-card">
              <div className="login-main login-tab">
                <Form className="theme-form">
                  <H4>Dwella Suite</H4>
                  <P>{"Sign in to manage properties, tenants, billing, and maintenance."}</P>
                  <FormGroup>
                    <Label className="col-form-label">{EmailAddress}</Label>
                    <Input className="form-control" type="email" required="" onChange={(e) => setEmail(e.target.value)} value={email} />
                  </FormGroup>
                  <FormGroup className="position-relative">
                    <Label className="col-form-label">{Password}</Label>
                    <Input className="form-control" type={togglePassword ? "text" : "password"} onChange={(e) => setPassword(e.target.value)} value={password} required="" />
                    <div className="show-hide" onClick={() => setTogglePassword(!togglePassword)}>
                      <span className={togglePassword ? "" : "show"}></span>
                    </div>
                  </FormGroup>
                  <div className="form-group mb-0">
                    <div className="checkbox ms-3">
                      <Input id="checkbox1" type="checkbox" />
                      <Label className="text-muted" for="checkbox1">
                        {RememberPassword}
                      </Label>
                    </div>
                    <a className="link" href="#javascript">
                      {ForgotPassword}
                    </a>
                    <Btn attrBtn={{ color: "primary", className: "btn-block", disabled: loginMutation.isPending, onClick: (e) => loginAuth(e) }}>
                      {loginMutation.isPending ? "Signing in..." : "Login"}
                    </Btn>
                  </div>
                </Form>
              </div>
            </div>
          </Col>
        </Row>
      </div>
    </Fragment>
  );
};

export default Login;
