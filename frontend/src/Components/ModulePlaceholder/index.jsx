import React from "react";
import { ArrowRight, Clock } from "react-feather";

const ModulePlaceholder = ({ title, description }) => (
  <div className="dwella-screen">
    <section className="dwella-card dwella-module-placeholder">
      <span><Clock size={22} /></span>
      <div>
        <p className="dwella-kicker">Module workspace</p>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <button className="dwella-secondary-action" type="button">
        Coming next
        <ArrowRight size={15} />
      </button>
    </section>
  </div>
);

export default ModulePlaceholder;
