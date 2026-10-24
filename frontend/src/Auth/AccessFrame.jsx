import React from "react";
import AuthTour from "./AuthTour";
import "./accountAccess.scss";

export default function AccessFrame({ title, children }) {
  return <main className="dwella-auth-page">
    <section className="dwella-auth-hero">
      <div className="dwella-auth-brand"><img src="/assets/images/logo/dwella-mark-white.png" alt="" /><strong>Dwella Suite</strong></div>
      <AuthTour />
    </section>
    <section className="dwella-auth-panel">
      <div className="dwella-auth-form dwella-access-form">
        <div className="dwella-auth-compact-brand"><img src="/assets/images/logo/dwella-mark.png" alt="" /><strong>Dwella Suite</strong></div>
        <header className="dwella-auth-heading"><h1>{title}</h1></header>
        {children}
      </div>
    </section>
  </main>;
}
