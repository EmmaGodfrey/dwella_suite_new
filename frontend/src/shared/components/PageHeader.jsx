import React, { createContext, useContext } from "react";
import { createPortal } from "react-dom";

// The layout renders the page title; each page owns its actions. Pages hand
// their buttons to <PageActions>, which portals them into the header slot so
// they sit beside the title the way the Figma pages show them.
export const PageActionsSlot = createContext(null);

export const PageHeader = ({ title, description, onSlot }) => (
  <header className="dwella-page-header">
    <div className="dwella-page-header-copy">
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </div>
    <div className="dwella-page-actions" ref={onSlot} />
  </header>
);

export const PageActions = ({ children }) => {
  const slot = useContext(PageActionsSlot);
  return slot ? createPortal(children, slot) : null;
};
