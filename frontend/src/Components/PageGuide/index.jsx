import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button, Tooltip } from "@fluentui/react-components";
import { Dismiss16Regular, Lightbulb20Regular } from "@fluentui/react-icons";
import { useLocation, useNavigate } from "react-router-dom";
import { usePageGuides } from "../../Services/accountSetup";
import { getUserAccess } from "../../shared/access";
import { GUIDES, moduleForPath } from "./guides";
import "./pageGuide.scss";

const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1; };

// The first visible element matching the step's target, or null.
// Handy's launcher belongs to an external widget (class ha-fab) and exists only when Handy is on.
function findHandy() {
  const el = document.querySelector(".ha-fab");
  return el && visible(el) ? el : null;
}

export function findTarget(target) {
  if (!target) return null;
  if (target.handy) return findHandy();
  const wanted = target.text?.toLowerCase();
  const found = [...document.querySelectorAll(target.sel)].find((el) => visible(el) && (!wanted || `${el.textContent} ${el.getAttribute("aria-label") || ""}`.toLowerCase().includes(wanted))) || null;
  return found || (target.fallback ? findTarget(target.fallback) : null);
}

// The bulb lives just to the right of the page's own title, wherever the page draws it.
// Pages re-render their title as data arrives, so the slot is re-attached whenever it is lost.
function useTitleHost(pathname) {
  const [host, setHost] = useState(null);
  useLayoutEffect(() => {
    let span = null;
    let frame = 0;
    const sync = () => {
      frame = 0;
      const title = document.querySelector("main h1") || document.querySelector("main h3");
      if (span && span.isConnected && span.parentElement === title) return;
      span?.remove();
      span = null;
      if (title) {
        span = document.createElement("span");
        span.className = "dwella-page-guide-host";
        title.appendChild(span);
      }
      setHost(span);
    };
    setHost(null);
    sync();
    const observer = new MutationObserver(() => { if (!frame) frame = requestAnimationFrame(sync); });
    observer.observe(document.querySelector("main") || document.body, { childList: true, subtree: true });
    return () => { observer.disconnect(); cancelAnimationFrame(frame); span?.remove(); };
  }, [pathname]);
  return host;
}

// A lightbulb beside the page title opens a small speech-bubble guide that points
// at the real control it describes. It opens once on a person's first visit and is
// always replayable from the bulb. It never dims the page and never acts for the user.
export default function PageGuide({ user }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const access = getUserAccess(user);
  const persona = access.persona;
  const isManager = access.role === "manager";
  const role = persona === "tenant" ? "tenant" : persona === "landlord" ? "landlord" : null;
  const guides = usePageGuides(user, Boolean(role));
  const module = moduleForPath(pathname);
  const guide = role ? GUIDES[role][module] : null;
  const offered = Boolean(guide) && guides.data?.available && guides.data.modules.includes(module);
  const host = useTitleHost(pathname);
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const [pos, setPos] = useState(null);
  const autoOpened = useRef(new Set());
  const bulb = useRef(null);
  const card = useRef(null);
  const { markSeen } = guides;
  // Handy steps only appear when Handy is actually switched on for this person.
  const steps = React.useMemo(() => (guide ? guide.steps.filter((item) => {
    if (isManager && module === "settings" && ["Workspace", "Payments"].includes(item.title)) return false;
    return (!item.target?.handy || findHandy()) && (!item.optional || findTarget(item.target));
  }) : []), [guide, isManager, module, open]); // eslint-disable-line react-hooks/exhaustive-deps
  const step = steps[index];

  useEffect(() => {
    if (!offered || !host || guides.data.seen.includes(module) || autoOpened.current.has(module)) return;
    autoOpened.current.add(module);
    // Give the page a moment to fill in so optional steps can find their controls.
    const timer = window.setTimeout(() => { setIndex(0); setOpen(true); }, 600);
    return () => { window.clearTimeout(timer); autoOpened.current.delete(module); };
  }, [offered, host, guides.data, module]);
  useEffect(() => { setOpen(false); }, [pathname]);

  const close = useCallback(() => {
    setOpen(false);
    if (guides.data && !guides.data.seen.includes(module)) markSeen.mutate(module);
    bulb.current?.focus();
  }, [guides.data, module, markSeen]);

  // Highlight the target and keep the bubble beside it as the page scrolls or resizes.
  useLayoutEffect(() => {
    if (!open || !step) { setPos(null); return undefined; }
    let marked = null;
    let scrolled = null;
    const place = () => {
      const el = findTarget(step.target) || bulb.current;
      if (!el) return;
      if (el !== marked) {
        marked?.removeAttribute("data-guide-active");
        if (el !== bulb.current) el.setAttribute("data-guide-active", "true");
        marked = el;
      }
      if (scrolled !== el) { scrolled = el; el.scrollIntoView?.({ block: "center", behavior: "auto" }); }
      const r = el.getBoundingClientRect();
      const w = Math.min(280, window.innerWidth - 24);
      const h = card.current?.offsetHeight || 150;
      const below = r.bottom + 16 + h <= window.innerHeight - 8;
      const left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12));
      const center = r.left + Math.min(r.width, 160) / 2;
      setPos({
        left, width: w, placement: below ? "below" : "above",
        top: below ? r.bottom + 14 : Math.max(8, r.top - h - 14),
        arrow: Math.max(16, Math.min(center - left, w - 16)),
      });
    };
    place();
    const frame = requestAnimationFrame(place);
    // Pages fill in after the guide opens: keep looking for the target until it appears.
    let watching = null;
    if (step.target && !findTarget(step.target)) {
      let pending = 0;
      watching = new MutationObserver(() => {
        if (pending) return;
        pending = requestAnimationFrame(() => { pending = 0; if (findTarget(step.target)) { watching.disconnect(); place(); } });
      });
      watching.observe(document.body, { childList: true, subtree: true });
    }
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      cancelAnimationFrame(frame);
      watching?.disconnect();
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
      marked?.removeAttribute("data-guide-active");
    };
  }, [open, step]);

  const placed = Boolean(pos);
  useEffect(() => { if (open && placed) card.current?.focus({ preventScroll: true }); }, [open, index, placed]);

  if (!offered || !host) return null;
  const last = index === steps.length - 1;
  return <>
    {createPortal(
      <Tooltip content="Page tips" relationship="label">
        <Button ref={bulb} className="dwella-page-guide-bulb" appearance="subtle" size="small" icon={<Lightbulb20Regular />} aria-label="Page tips" aria-expanded={open} onClick={() => { if (open) close(); else { setIndex(0); setOpen(true); } }} />
      </Tooltip>, host)}
    {open && pos ? createPortal(
      <div ref={card} className={`dwella-page-guide is-${pos.placement}`} role="dialog" aria-label={`${guide.title} tips`} tabIndex={-1}
        style={{ left: pos.left, top: pos.top, width: pos.width, "--arrow": `${pos.arrow}px` }}
        onKeyDown={(e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } }}>
        <div className="dwella-page-guide-head">
          <strong>{step.title}</strong>
          <Button appearance="subtle" size="small" icon={<Dismiss16Regular />} aria-label="Close tips" onClick={close} />
        </div>
        <p>{step.body}</p>
        {step.to ? <Button appearance="outline" size="small" onClick={() => { close(); navigate(step.to); }}>{step.toLabel}</Button> : null}
        <div className="dwella-page-guide-foot">
          <span className="dwella-page-guide-count">{index + 1} / {steps.length}</span>
          <span>
            {!last ? <Button size="small" appearance="subtle" onClick={close}>Skip</Button> : null}
            {index > 0 ? <Button size="small" appearance="subtle" onClick={() => setIndex(index - 1)}>Back</Button> : null}
            <Button size="small" appearance="primary" onClick={() => (last ? close() : setIndex(index + 1))}>{last ? "Done" : "Next"}</Button>
          </span>
        </div>
      </div>, document.body) : null}
  </>;
}
