import React from "react";
import { Nav, NavItem, NavLink } from "reactstrap";
import { Image } from "../AbstractElements";
import simpleLogin from "/assets/images/simple-login.svg";

const NavAuth = ({ callbackNav, selected }) => {
  return (
    <Nav className="border-tab flex-column" tabs>
      <NavItem>
        <NavLink className={selected === "simpleLogin" ? "active" : ""} onClick={() => callbackNav("simpleLogin")}>
          <Image attrImage={{ src: `${simpleLogin}`, alt: "" }} />
          <span>Simple Login</span>
        </NavLink>
      </NavItem>
    </Nav>
  );
};

export default NavAuth;
