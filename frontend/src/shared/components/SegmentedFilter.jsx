import React from "react";

// A row of mutually exclusive filter buttons (All / Active / Past …), styled
// like the Figma segmented control. Plain buttons with aria-pressed rather than
// Fluent's TabList: these filter a list in place, they do not switch panels.
export const SegmentedFilter = ({ options, value, onChange, label }) => (
  <div className="dwella-segmented" role="group" aria-label={label}>
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        aria-pressed={option.value === value}
        className={option.value === value ? "is-selected" : undefined}
        onClick={() => onChange(option.value)}
      >
        {option.label}
      </button>
    ))}
  </div>
);
