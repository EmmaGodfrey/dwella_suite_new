import React from "react";
import { Avatar, Menu, MenuItem, MenuList, MenuPopover, MenuTrigger } from "@fluentui/react-components";
import { MoreHorizontal20Regular, Person24Regular, Shield24Regular, SignOut24Regular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

import { resolveMediaUrl } from "../../Services/apiClient";
import { accessLabel } from "../access";

const initialsFor = (user) => {
  const source = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "DS";
  return source.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
};

// The account block that closes the sidebar. The whole row opens the menu, so
// the identity stays readable while collapsed and still has one obvious target.
export const UserMenu = ({ user, onLogout, compact = false }) => {
  const navigate = useNavigate();
  const avatarUrl = resolveMediaUrl(user?.profile?.avatar_url || user?.profile?.avatar || user?.avatar_url || user?.avatar);
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.email || "Dwella Admin";

  return (
    <Menu positioning={compact ? "after-bottom" : "above-start"}>
      <MenuTrigger disableButtonEnhancement>
        <button className="dwella-account" type="button" aria-label={`Account menu for ${fullName}`}>
          <Avatar name={fullName} image={avatarUrl ? { src: avatarUrl } : undefined} initials={initialsFor(user)} size={32} color="brand" />
          {!compact ? (
            <>
              <span className="dwella-account-copy">
                <strong>{fullName}</strong>
                <small>{user?.email || accessLabel(user)}</small>
              </span>
              <MoreHorizontal20Regular className="dwella-account-more" />
            </>
          ) : null}
        </button>
      </MenuTrigger>
      <MenuPopover className="dwella-user-dropdown">
        <div className="dwella-user-card">
          <strong>{fullName}</strong>
          {user?.email ? <small>{user.email}</small> : null}
          <small>{accessLabel(user)}</small>
        </div>
        <MenuList>
          <MenuItem icon={<Person24Regular />} onClick={() => navigate("/profile")}>Profile</MenuItem>
          <MenuItem icon={<Shield24Regular />} onClick={() => navigate("/security")}>Security</MenuItem>
          <MenuItem icon={<SignOut24Regular />} onClick={onLogout}>Log out</MenuItem>
        </MenuList>
      </MenuPopover>
    </Menu>
  );
};
