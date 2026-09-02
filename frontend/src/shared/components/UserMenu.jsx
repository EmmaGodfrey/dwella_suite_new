import React from "react";
import { Avatar, Button, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger } from "@fluentui/react-components";
import { ChevronDown24Regular, Person24Regular, Shield24Regular, SignOut24Regular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

import { getApiBaseUrl } from "../../Services/apiClient";

const initialsFor = (user) => {
  const source = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "DS";
  return source.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
};

const resolveMediaUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${getApiBaseUrl().replace(/\/api\/v1$/, "")}${value.startsWith("/") ? value : `/${value}`}`;
};

export const UserMenu = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const avatarUrl = resolveMediaUrl(user?.profile?.avatar_url || user?.profile?.avatar || user?.avatar_url || user?.avatar);
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "Dwella Admin";
  const verificationStatus = user?.identity_verification?.status || "not_submitted";

  return (
    <Menu positioning="below-end">
      <MenuTrigger disableButtonEnhancement>
        <Button className="dwella-user-trigger" appearance="subtle">
          <Avatar name={fullName} image={avatarUrl ? { src: avatarUrl } : undefined} initials={initialsFor(user)} size={32} />
          <span>
            <strong>{fullName}</strong>
            <small>{verificationStatus === "approved" ? "Verified admin" : "Profile verification"}</small>
          </span>
          <ChevronDown24Regular />
        </Button>
      </MenuTrigger>
      <MenuPopover className="dwella-user-dropdown">
        <MenuList>
          <MenuItem icon={<Person24Regular />} onClick={() => navigate("/profile")}>Profile</MenuItem>
          <MenuItem icon={<Shield24Regular />} onClick={() => navigate("/security")}>Security</MenuItem>
          <MenuItem icon={<SignOut24Regular />} onClick={onLogout}>Log out</MenuItem>
        </MenuList>
      </MenuPopover>
    </Menu>
  );
};
