import React, { Fragment } from "react";
import { Card } from "reactstrap";
import { Btn, LI } from "../../../AbstractElements";
import { LogOut } from "react-feather";
import { Link, useNavigate } from "react-router-dom";
import { logout } from "../../../Services/auth";
import { queryClient } from "../../../Services/queryClient";

const LogoutClass = () => {
  const history = useNavigate();
  const handleLogout = () => {
    logout();
    queryClient.clear();
    history(`/login`, { replace: true });
  };

  return (
    <Fragment>
      <LI attrLI={{ className: "onhover-dropdown p-0", onClick: handleLogout }}>
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
