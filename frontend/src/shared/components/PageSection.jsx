import React from "react";

// Plain heading/paragraph rather than Fluent's Title3/Text: those force
// `display: inline`, which ran the title and note together on one line.
export const PageSection = ({
  title,
  note,
  actions,
  children,
  className = "",
  as: Heading = "h2",
}) => (
  <section className={`dwella-panel ${className}`.trim()}>
    {title || note || actions ? (
      <header className="dwella-panel-heading">
        <div>
          {title ? (
            <Heading className="dwella-panel-title">{title}</Heading>
          ) : null}
          {note ? <p className="dwella-panel-note">{note}</p> : null}
        </div>
        {actions ? <div className="dwella-panel-actions">{actions}</div> : null}
      </header>
    ) : null}
    {children}
  </section>
);
