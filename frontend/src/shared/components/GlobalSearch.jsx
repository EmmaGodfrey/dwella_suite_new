import React, { useEffect, useId, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Building20Regular, People20Regular, Receipt20Regular, Search20Regular } from "@fluentui/react-icons";

import { useCurrentUserQuery, useInvoicesQuery, usePropertiesQuery, useTenantsQuery } from "../../Services/queries";
import { getUserAccess } from "../access";
import { formatMoney } from "../format";

const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
const PER_GROUP = 4;

// One box for the three records people look up most. It searches with the
// list endpoints' own `search` filter, so results match what each page finds.
export const GlobalSearch = () => {
  const navigate = useNavigate();
  const listId = useId();
  const inputRef = useRef(null);
  const rootRef = useRef(null);
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const access = getUserAccess(user);
  const [value, setValue] = useState("");
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timeout = setTimeout(() => setTerm(value.trim()), 250);
    return () => clearTimeout(timeout);
  }, [value]);

  useEffect(() => {
    const onKey = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    const onPointer = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    return () => document.removeEventListener("pointerdown", onPointer);
  }, [open]);

  const enabled = access.can_view_portfolio && term.length >= 2;
  const filters = { search: term, page_size: PER_GROUP };
  const properties = usePropertiesQuery(filters, { enabled, staleTime: 30_000 });
  const tenants = useTenantsQuery(filters, { enabled, staleTime: 30_000 });
  const invoices = useInvoicesQuery(filters, { enabled, staleTime: 30_000 });
  const loading = enabled && (properties.isFetching || tenants.isFetching || invoices.isFetching);

  const groups = useMemo(
    () =>
      [
        {
          label: "Properties",
          icon: <Building20Regular />,
          items: (properties.data?.results || []).map((item) => ({
            key: `p-${item.id}`,
            title: item.name,
            detail: [item.address, item.town].filter(Boolean).join(" · "),
            to: `/properties?search=${encodeURIComponent(item.name)}`,
          })),
        },
        {
          label: "Tenants",
          icon: <People20Regular />,
          items: (tenants.data?.results || []).map((item) => ({
            key: `t-${item.id}`,
            title: item.full_name,
            detail: item.phone_number || item.email || "",
            to: `/tenants?search=${encodeURIComponent(item.full_name)}`,
          })),
        },
        {
          label: "Invoices",
          icon: <Receipt20Regular />,
          items: (invoices.data?.results || []).map((item) => ({
            key: `i-${item.id}`,
            title: item.reference,
            detail: `${item.tenant_name} · ${formatMoney(item.total)}`,
            to: `/billing/invoices/${item.id}`,
          })),
        },
      ].filter((group) => group.items.length),
    [properties.data, tenants.data, invoices.data],
  );
  const flat = groups.flatMap((group) => group.items);
  const showPanel = open && term.length >= 2;

  useEffect(() => setActive(0), [term]);

  if (!access.can_view_portfolio) return <div className="dwella-global-search-spacer" />;

  const go = (item) => {
    if (!item) return;
    setOpen(false);
    setValue("");
    inputRef.current?.blur();
    navigate(item.to);
  };

  const onKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActive((index) => (flat.length ? (index + 1) % flat.length : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => (flat.length ? (index - 1 + flat.length) % flat.length : 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      go(flat[active]);
    } else if (event.key === "Escape") {
      if (value) setValue("");
      else inputRef.current?.blur();
      setOpen(false);
    }
  };

  let index = -1;
  return (
    <div className="dwella-global-search" ref={rootRef}>
      <Search20Regular className="dwella-global-search-icon" aria-hidden="true" />
      <input
        ref={inputRef}
        type="search"
        role="combobox"
        aria-label="Search properties, tenants and invoices"
        aria-expanded={showPanel}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showPanel && flat[active] ? `${listId}-${flat[active].key}` : undefined}
        placeholder="Search properties, tenants, invoices…"
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      <kbd aria-hidden="true">{isMac ? "⌘ K" : "Ctrl K"}</kbd>

      {showPanel ? (
        <div className="dwella-global-search-panel">
          <ul id={listId} role="listbox" aria-label="Search results">
            {groups.map((group) => (
              <li key={group.label} role="presentation">
                <span className="dwella-global-search-group" role="presentation">{group.label}</span>
                <ul role="group" aria-label={group.label}>
                  {group.items.map((item) => {
                    index += 1;
                    const position = index;
                    return (
                      <li
                        key={item.key}
                        id={`${listId}-${item.key}`}
                        role="option"
                        aria-selected={position === active}
                        className={position === active ? "is-active" : undefined}
                        onPointerEnter={() => setActive(position)}
                        onPointerDown={(event) => event.preventDefault()}
                        onClick={() => go(item)}
                      >
                        <span className="dwella-global-search-result-icon">{group.icon}</span>
                        <span>
                          <strong>{item.title}</strong>
                          {item.detail ? <small>{item.detail}</small> : null}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ul>
          {!flat.length ? (
            <p className="dwella-global-search-empty" role="status">
              {loading ? "Searching…" : `Nothing matches “${term}”.`}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
};
