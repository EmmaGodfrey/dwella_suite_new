import React, { Fragment } from "react";
import { Card } from "reactstrap";
import { Btn, LI } from "../../../AbstractElements";
import { LogOut } from "react-feather";
import { Link, useNavigate } from "react-router-dom";

const LogoutClass = () => {
  const history = useNavigate();
  const Logout = () => {
    localStorage.removeItem("profileURL");
    localStorage.removeItem("token");

    localStorage.removeItem("auth0_profile");
    localStorage.removeItem("Name");
    localStorage.setItem("authenticated", false);
    history(`/login`);
  };

  return (
    <Fragment>
      <LI attrLI={{ className: "onhover-dropdown p-0", onClick: Logout }}>
        <Btn attrBtn={{ as: Card.Header, className: "btn btn-primary-light", color: "default" }}>
          <Link to={`/login`}>
            <LogOut />
            Log out
          </Link>
        </Btn>
      </LI>
    </Fragment>
  );
};

export default LogoutClass;
