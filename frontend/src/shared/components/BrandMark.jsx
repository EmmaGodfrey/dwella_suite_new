import React from "react";
import { Link } from "react-router-dom";

export const BrandMark = ({ compact = false, onClick }) => (
  <Link className="dwella-brand-link" to="/dashboard" onClick={onClick} aria-label="Dwella Suite dashboard">
    <span className="dwella-brand-mark">
      <img src="/assets/images/logo/dwella-icon.png" alt="" />
    </span>
    {!compact ? (
      <span className="dwella-brand-copy">
        <strong>Dwella Suite</strong>
      </span>
    ) : null}
  </Link>
);
