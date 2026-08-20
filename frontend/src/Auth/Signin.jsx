import React, { Fragment, useMemo, useState } from "react";
import { Col, Form, FormGroup, Input, Label, Row } from "reactstrap";
import { Btn, H4, P } from "../AbstractElements";
import { EmailAddress, ForgotPassword, Password, RememberPassword } from "../Constant";
import { toast } from "react-toastify";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  useLoginMutation,
  usePasswordResetConfirmMutation,
  usePasswordResetRequestMutation,
  useTwoFactorLoginMutation,
} from "../Services/mutations";
import SocialAuth from "./Tabs/LoginTab/SocialAuth";

const disposableDomains = new Set(["10minutemail.com", "guerrillamail.com", "mailinator.com", "tempmail.com", "temp-mail.org", "throwawaymail.com", "yopmail.com"]);

const validateEmail = (value) => {
  const email = value.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address.";
  if (disposableDomains.has(email.split("@").pop())) return "Use a permanent email address.";
  return "";
};

const validatePassword = (value) => {
  if (value.length < 10) return "Password must be at least 10 characters.";
  if (/^\d+$/.test(value)) return "Password cannot be entirely numeric.";
  return "";
};

const Login = ({ selected }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("admin@dwella.local");
  const [password, setPassword] = useState("admin12345");
  const [resetPassword, setResetPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [challengeToken, setChallengeToken] = useState("");
  const [mode, setMode] = useState(searchParams.get("reset_uid") && searchParams.get("reset_token") ? "reset-confirm" : "login");
  const [togglePassword, setTogglePassword] = useState(false);
  const resetUid = searchParams.get("reset_uid");
  const resetToken = searchParams.get("reset_token");
  const isResetConfirm = mode === "reset-confirm";
  const heading = useMemo(() => {
    if (mode === "forgot") return "Reset Password";
    if (isResetConfirm) return "Set New Password";
    if (mode === "2fa") return "Two-Factor Verification";
    return "Dwella Suite";
  }, [isResetConfirm, mode]);
  const loginMutation = useLoginMutation({
    onSuccess: (data) => {
      if (data.two_factor_required) {
        setChallengeToken(data.challenge_token);
        setMode("2fa");
        return;
      }
      navigate("/dashboard", { replace: true });
    },
    onError: (error) => toast.error(error.message || "Login failed"),
  });
  const twoFactorMutation = useTwoFactorLoginMutation({
    onSuccess: () => navigate("/dashboard", { replace: true }),
    onError: (error) => toast.error(error.message || "Invalid authentication code"),
  });
  const resetRequestMutation = usePasswordResetRequestMutation({
    onSuccess: () => toast.success("If that email exists, a reset link has been sent."),
    onError: (error) => toast.error(error.message || "Password reset failed"),
  });
  const resetConfirmMutation = usePasswordResetConfirmMutation({
    onSuccess: () => {
      toast.success("Password reset complete. Sign in with your new password.");
      setMode("login");
      navigate("/login", { replace: true });
    },
    onError: (error) => toast.error(error.message || "Password reset failed"),
  });

  const loginAuth = async (e) => {
    e.preventDefault();
    const emailError = validateEmail(email);
    if (emailError) {
      toast.error(emailError);
      return;
    }
    if (!password) {
      toast.error("Enter your password.");
      return;
    }
    loginMutation.mutate({ email: email.trim().toLowerCase(), password });
  };

  const submitResetRequest = (e) => {
    e.preventDefault();
    const emailError = validateEmail(email);
    if (emailError) {
      toast.error(emailError);
      return;
    }
    resetRequestMutation.mutate({ email: email.trim().toLowerCase() });
  };

  const submitResetConfirm = (e) => {
    e.preventDefault();
    const passwordError = validatePassword(resetPassword);
    if (passwordError) {
      toast.error(passwordError);
      return;
    }
    resetConfirmMutation.mutate({ uid: resetUid, token: resetToken, password: resetPassword });
  };

  const submitTwoFactor = (e) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(twoFactorCode)) {
      toast.error("Enter the 6-digit code from your authenticator app.");
      return;
    }
    twoFactorMutation.mutate({ challengeToken, code: twoFactorCode });
  };

  return (
    <Fragment>
      <div className="p-0 container-fluid">
        <Row>
          <Col className="col-12">
            <div className="login-card">
              <div className="login-main login-tab">
                <Form className="theme-form">
                  <H4>{heading}</H4>
                  <P>{mode === "2fa" ? "Enter the code from your authenticator app." : "Secure access for Dwella property operations."}</P>
                  {mode === "2fa" ? (
                    <>
                      <FormGroup>
                        <Label className="col-form-label">Authentication Code</Label>
                        <Input className="form-control" inputMode="numeric" maxLength="6" onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ""))} value={twoFactorCode} />
                      </FormGroup>
                      <Btn attrBtn={{ color: "primary", className: "btn-block", disabled: twoFactorMutation.isPending, onClick: submitTwoFactor }}>
                        {twoFactorMutation.isPending ? "Verifying..." : "Verify and Login"}
                      </Btn>
                      <button type="button" className="btn btn-link w-100 mt-2" onClick={() => setMode("login")}>
                        Back to login
                      </button>
                    </>
                  ) : mode === "forgot" ? (
                    <>
                      <FormGroup>
                        <Label className="col-form-label">{EmailAddress}</Label>
                        <Input className="form-control" type="email" onChange={(e) => setEmail(e.target.value)} value={email} />
                      </FormGroup>
                      <Btn attrBtn={{ color: "primary", className: "btn-block", disabled: resetRequestMutation.isPending, onClick: submitResetRequest }}>
                        {resetRequestMutation.isPending ? "Sending..." : "Send Reset Link"}
                      </Btn>
                      <button type="button" className="btn btn-link w-100 mt-2" onClick={() => setMode("login")}>
                        Back to login
                      </button>
                    </>
                  ) : isResetConfirm ? (
                    <>
                      <FormGroup>
                        <Label className="col-form-label">New Password</Label>
                        <Input className="form-control" type={togglePassword ? "text" : "password"} onChange={(e) => setResetPassword(e.target.value)} value={resetPassword} />
                        <div className="show-hide" onClick={() => setTogglePassword(!togglePassword)}>
                          <span className={togglePassword ? "" : "show"}></span>
                        </div>
                      </FormGroup>
                      <Btn attrBtn={{ color: "primary", className: "btn-block", disabled: resetConfirmMutation.isPending, onClick: submitResetConfirm }}>
                        {resetConfirmMutation.isPending ? "Saving..." : "Set Password"}
                      </Btn>
                    </>
                  ) : (
                    <>
                      <FormGroup>
                        <Label className="col-form-label">{EmailAddress}</Label>
                        <Input className="form-control" type="email" onChange={(e) => setEmail(e.target.value)} value={email} />
                      </FormGroup>
                      <FormGroup className="position-relative">
                        <Label className="col-form-label">{Password}</Label>
                        <Input className="form-control" type={togglePassword ? "text" : "password"} onChange={(e) => setPassword(e.target.value)} value={password} />
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
                        <button type="button" className="btn btn-link p-0 link" onClick={() => setMode("forgot")}>
                          {ForgotPassword}
                        </button>
                        <Btn attrBtn={{ color: "primary", className: "btn-block", disabled: loginMutation.isPending, onClick: loginAuth }}>
                          {loginMutation.isPending ? "Signing in..." : "Login"}
                        </Btn>
                      </div>
                    </>
                  )}
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
