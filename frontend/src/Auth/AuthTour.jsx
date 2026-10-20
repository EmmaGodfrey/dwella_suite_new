import React, { useState } from "react";
import { ChevronLeft20Regular, ChevronRight20Regular } from "@fluentui/react-icons";

import "./authTour.scss";

// The sign-in brand panel doubles as a short product tour. Slides change only
// when the visitor clicks: nothing moves on its own while they type.
// Each preview is illustrative sample data, kept in the same words the app uses.
const slides = [
  {
    eyebrow: "Dwella Suite",
    title: "The operations desk for your property portfolio.",
    body: "Properties, units, occupancy and rent roll in one place, with an audit trail behind every change.",
    preview: {
      heading: "This month",
      rows: [
        ["Units occupied", "11 of 12", "good"],
        ["Rent billed", "K46,800", ""],
        ["Collected so far", "K38,100", "good"],
      ],
    },
  },
  {
    eyebrow: "Rent and billing",
    title: "Bill every lease in one click.",
    body: "Rent invoices come straight from active leases. Record cash, bank and mobile-money payments, and late fees add themselves after the grace period.",
    preview: {
      heading: "Invoices",
      rows: [
        ["INV-0041 · Unit 2A", "Paid", "good"],
        ["INV-0042 · Unit 3B", "Part paid", "warn"],
        ["INV-0043 · Shop 2", "Overdue · 4 days", "bad"],
      ],
    },
  },
  {
    eyebrow: "Tenants and leases",
    title: "Know who lives where, and until when.",
    body: "Each tenant has their lease, balance and history together. See leases coming up for renewal before they lapse.",
    preview: {
      heading: "Leases ending soon",
      rows: [
        ["Natasha Banda · 1A", "30 Nov", "warn"],
        ["Moses Daka · 3B", "15 Jan", ""],
        ["Copper Traders · Shop 2", "28 Feb", ""],
      ],
    },
  },
  {
    eyebrow: "Maintenance",
    title: "Repairs from report to done.",
    body: "Log a job, assign a vendor, book the visit and keep the tenant updated. Charge the repair to the tenant when it was theirs to fix.",
    preview: {
      heading: "Board",
      rows: [
        ["Burst pipe · 3B", "Urgent", "bad"],
        ["Geyser element · 2B", "Scheduled", ""],
        ["Door lock · 1B", "Done", "good"],
      ],
    },
  },
];

export default function AuthTour() {
  const [index, setIndex] = useState(0);
  const slide = slides[index];
  const go = (next) => setIndex((next + slides.length) % slides.length);

  return (
    <section className="dwella-auth-tour" aria-roledescription="carousel" aria-label="What Dwella does">
      <div
        key={index}
        className="dwella-auth-slide"
        role="group"
        aria-roledescription="slide"
        aria-label={`${index + 1} of ${slides.length}`}
        aria-live="polite"
      >
        <span className="dwella-auth-rule" aria-hidden="true" />
        <p className="dwella-auth-eyebrow">{slide.eyebrow}</p>
        <h2>{slide.title}</h2>
        <p>{slide.body}</p>

        <div className="dwella-auth-preview" aria-label="Example">
          <strong>{slide.preview.heading}</strong>
          <ul>
            {slide.preview.rows.map(([label, value, tone]) => (
              <li key={label}>
                <span>{label}</span>
                <span className={tone ? `is-${tone}` : undefined}>{value}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="dwella-auth-tour-controls">
        <button type="button" className="dwella-auth-tour-arrow" aria-label="Previous" onClick={() => go(index - 1)}>
          <ChevronLeft20Regular />
        </button>
        <div className="dwella-auth-tour-dots">
          {slides.map((item, dot) => (
            <button
              key={item.eyebrow}
              type="button"
              aria-label={`Show ${item.eyebrow}`}
              aria-current={dot === index ? "true" : undefined}
              className={dot === index ? "is-active" : undefined}
              onClick={() => setIndex(dot)}
            />
          ))}
        </div>
        <button type="button" className="dwella-auth-tour-arrow" aria-label="Next" onClick={() => go(index + 1)}>
          <ChevronRight20Regular />
        </button>
        <span className="dwella-auth-tour-count" aria-hidden="true">{index + 1} / {slides.length}</span>
      </div>
    </section>
  );
}
