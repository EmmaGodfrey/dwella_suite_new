import React from "react";
import { Link } from "react-router-dom";

// The wordmark is set in type rather than an image so it inherits the theme:
// "Dwe" takes the primary colour and "lla" the accent, as in the logo lockup.
export const BrandMark = ({ onClick, showWordmark = true }) => (
  <Link className="dwella-brand-link" to="/dashboard" onClick={onClick} aria-label="Dwella Suite dashboard">
    <img className="dwella-brand-mark" src="/assets/images/logo/dwella-mark.png" alt="" />
    {showWordmark ? (
      <span className="dwella-brand-word" aria-hidden="true">
        Dwe<span>lla</span>
      </span>
    ) : null}
  </Link>
);
