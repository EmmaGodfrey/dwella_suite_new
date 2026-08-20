import React, { useState } from "react";
import { ChevronDown, LogOut, Shield, User } from "react-feather";
import { Link, useNavigate } from "react-router-dom";
import { Badge, Dropdown, DropdownItem, DropdownMenu, DropdownToggle } from "reactstrap";

import { LI } from "../../../AbstractElements";
import { logout } from "../../../Services/auth";
import { getApiBaseUrl } from "../../../Services/apiClient";
import { queryClient } from "../../../Services/queryClient";
import { useCurrentUserQuery } from "../../../Services/queries";

const initialsFor = (user) => {
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "DS";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
};

const resolveMediaUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${getApiBaseUrl().replace(/\/api\/v1$/, "")}${value.startsWith("/") ? value : `/${value}`}`;
};

const getCachedUser = () => {
  try {
    return JSON.parse(localStorage.getItem("dwella_user") || "null");
  } catch {
    return null;
  }
};

const AccountMenu = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const cachedUser = getCachedUser();
  const { data: user = cachedUser } = useCurrentUserQuery({ staleTime: 60_000 });
  const avatarUrl = resolveMediaUrl(user?.profile?.avatar_url || user?.profile?.avatar || user?.avatar_url || user?.avatar);
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "Dwella Admin";
  const verificationStatus = user?.identity_verification?.status || "not_submitted";

  const handleLogout = () => {
    logout();
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  return (
    <LI attrLI={{ className: "dwella-account-menu" }}>
      <Dropdown isOpen={open} toggle={() => setOpen((value) => !value)} direction="down">
        <DropdownToggle tag="button" className="dwella-account-trigger" type="button">
          <span className="dwella-account-avatar">
            {avatarUrl ? <img src={avatarUrl} alt={fullName} /> : initialsFor(user)}
          </span>
          <span className="dwella-account-copy">
            <span>{fullName}</span>
            <Badge color={verificationStatus === "approved" ? "success" : "warning"} pill>
              {verificationStatus === "approved" ? "Verified" : "Verify profile"}
            </Badge>
          </span>
          <ChevronDown size={16} />
        </DropdownToggle>
        <DropdownMenu end className="dwella-account-dropdown">
          <DropdownItem tag={Link} to="/profile">
            <User size={16} />
            Profile
          </DropdownItem>
          <DropdownItem tag={Link} to="/security">
            <Shield size={16} />
            Security
          </DropdownItem>
          <DropdownItem divider />
          <DropdownItem onClick={handleLogout} className="text-danger">
            <LogOut size={16} />
            Log out
          </DropdownItem>
        </DropdownMenu>
      </Dropdown>
    </LI>
  );
};

export default AccountMenu;
