import React, { useEffect, useRef, useState } from "react";
import { Button, Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle } from "@fluentui/react-components";
import { Dismiss20Regular } from "@fluentui/react-icons";
import { useLocation, useNavigate } from "react-router-dom";
import { useGuidedTour } from "../../Services/accountSetup";
import "./tour.scss";

export default function GuidedTour({ user, enabled }) {
  const query = useGuidedTour(user, enabled);
  const tour = query.data;
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("welcome");
  const [anchor, setAnchor] = useState(null);
  const offered = useRef(false);
  const launcher = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const step = tour?.steps?.find((s) => s.id === tour.current_step);
  const index = tour?.steps?.findIndex((s) => s.id === tour.current_step) ?? 0;
  useEffect(() => {
    if (enabled && tour?.available && tour.status === "not_started" && !offered.current) {
      offered.current = true; setMode("welcome"); setOpen(true);
    }
  }, [enabled, tour]);
  useEffect(() => {
    if (!open || mode !== "step" || !step) { setAnchor(null); return; }
    let highlighted;
    const update = () => {
      const el = document.querySelector(`[data-tour="${step.target}"]`);
      const rect = el?.getBoundingClientRect();
      const visible = rect && rect.width > 0 && rect.height > 0;
      if (highlighted && highlighted !== el) highlighted.removeAttribute("data-tour-active");
      if (visible) { el.setAttribute("data-tour-active", "true"); highlighted = el; }
      setAnchor(visible ? { left: rect.right + 14, top: rect.top } : null);
    };
    if (!document.querySelector(`[data-tour="${step.target}"]`) && location.pathname !== step.path) navigate(step.path);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(document.body);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => { observer.disconnect(); window.removeEventListener("resize", update); window.removeEventListener("scroll", update, true); highlighted?.removeAttribute("data-tour-active"); };
  }, [open, mode, step, location.pathname, navigate]);
  const act = async (action) => {
    try {
      const data = await query.mutation.mutateAsync({ action, ...(["next", "back", "finish"].includes(action) ? { step: tour.current_step } : {}) });
      if (["pause", "skip"].includes(action)) { setOpen(false); launcher.current?.focus(); }
      else { setMode(data.status === "completed" ? "complete" : "step"); setOpen(true); }
    } catch { /* Keep the current step and show its retryable error. */ }
  };
  if (!enabled || !user || user.is_staff || user.is_superuser) return null;
  if (query.isError) return <Button appearance="subtle" onClick={() => query.refetch()}>Retry tour</Button>;
  if (!tour?.available) return null;
  const active = mode === "step";
  const busy = query.mutation.isPending;
  const style = active && anchor && window.innerWidth >= 900 ? { left: Math.min(anchor.left, window.innerWidth - 360), top: Math.max(16, Math.min(anchor.top, window.innerHeight - 300)) } : undefined;
  return <>
    <Button ref={launcher} className="dwella-tour-launcher" aria-label={tour.updates_available ? "New guidance" : "Product tour"} appearance="subtle" onClick={() => { query.mutation.reset(); setMode("welcome"); setOpen(true); }}><span className="dwella-tour-launcher-full">{tour.updates_available ? "New guidance" : "Product tour"}</span><span className="dwella-tour-launcher-short">{tour.updates_available ? "New" : "Tour"}</span></Button>
    <Dialog open={open} modalType={active ? "non-modal" : "modal"} onOpenChange={(_, data) => { if (!data.open && !busy) { if (mode === "complete") setOpen(false); else act(active ? "pause" : "skip"); } }}>
      <DialogSurface className={`dwella-tour ${active ? "is-step" : ""} ${active && anchor ? "is-anchored" : ""}`} style={style}>
        <DialogBody>
          <DialogTitle action={<Button appearance="subtle" aria-label={active ? "Pause tour" : "Close tour"} icon={<Dismiss20Regular />} disabled={busy} onClick={() => mode === "complete" ? setOpen(false) : act(active ? "pause" : "skip")} />}>{active ? step?.title : mode === "complete" ? "You’re ready to explore" : tour.updates_available ? "There’s something new to explore" : tour.status === "not_started" ? "A quick look around Dwella" : "Your product tour"}</DialogTitle>
          <DialogContent>
            {active ? <><p className="dwella-tour-count">Step {index + 1} of {tour.steps.length}</p><p>{step?.body}</p><progress max={tour.steps.length} value={index + 1} aria-label="Tour progress" /></> : <p>{mode === "complete" ? "Return to this tour whenever you need a refresher. Your setup checklist is still available in Get started." : tour.updates_available ? "See guidance for the features added since your last tour. Your completed steps are saved." : "See where to find your tools. You can pause, skip or replay this tour whenever you like."}</p>}
            {query.mutation.isError ? <p role="alert">Could not save your tour progress. Please try again.</p> : null}
          </DialogContent>
          <DialogActions>
            {active ? <><Button appearance="subtle" disabled={busy} onClick={() => act("pause")}>Pause</Button><Button disabled={busy || index === 0} onClick={() => act("back")}>Back</Button><Button appearance="primary" disabled={busy} onClick={() => act("next")}>{busy ? "Saving…" : index === tour.steps.length - 1 ? "Finish" : "Next"}</Button></> : mode === "complete" ? <Button appearance="primary" onClick={() => setOpen(false)}>Done</Button> : <>
              <Button appearance="subtle" disabled={busy} onClick={() => act("skip")}>Not now</Button>
              {!["not_started", "completed"].includes(tour.status) ? <Button disabled={busy} onClick={() => act("replay")}>Replay</Button> : null}
              <Button appearance="primary" disabled={busy} onClick={() => act(tour.updates_available ? "new_steps" : tour.status === "not_started" ? "start" : tour.status === "completed" ? "replay" : "resume")}>{busy ? "Loading…" : tour.updates_available ? "Show what’s new" : tour.status === "not_started" ? "Start tour" : tour.status === "completed" ? "Replay tour" : "Resume tour"}</Button>
            </>}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  </>;
}
