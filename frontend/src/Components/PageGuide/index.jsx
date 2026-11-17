import React, { useEffect, useRef, useState } from "react";
import { Button, Dialog, DialogActions, DialogBody, DialogContent, DialogSurface, DialogTitle, Tooltip } from "@fluentui/react-components";
import { Dismiss20Regular, Lightbulb20Regular } from "@fluentui/react-icons";
import { useLocation, useNavigate } from "react-router-dom";
import { usePageGuides } from "../../Services/accountSetup";
import { getUserAccess } from "../../shared/access";
import { GUIDES, moduleForPath } from "./guides";
import "./pageGuide.scss";

// A lightbulb that opens the current page's short guide. The guide opens by
// itself once, the first time this person visits the page, and is always
// replayable from the bulb. Guides only explain; they never act.
export default function PageGuide({ user, floating = false }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const persona = getUserAccess(user).persona;
  const role = persona === "tenant" ? "tenant" : persona === "landlord" ? "landlord" : null;
  const guides = usePageGuides(user, Boolean(role));
  const module = moduleForPath(pathname);
  const guide = role ? GUIDES[role][module] : null;
  const offered = guides.data?.available && guides.data.modules.includes(module);
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const autoOpened = useRef(new Set());
  const button = useRef(null);
  const { markSeen } = guides;

  useEffect(() => {
    if (!guide || !offered || guides.data.seen.includes(module) || autoOpened.current.has(module)) return;
    autoOpened.current.add(module);
    setIndex(0);
    setOpen(true);
  }, [guide, offered, guides.data, module]);

  useEffect(() => { setOpen(false); }, [pathname]);

  if (!guide || !offered) return null;
  const step = guide.steps[index];
  const last = index === guide.steps.length - 1;
  const close = () => {
    setOpen(false);
    if (!guides.data.seen.includes(module)) markSeen.mutate(module);
    button.current?.focus();
  };
  return <>
    <Tooltip content="Page tips" relationship="label">
      <Button ref={button} className={`dwella-page-guide-bulb ${floating ? "is-floating" : ""}`} appearance="subtle" size="small" icon={<Lightbulb20Regular />} aria-label="Page tips" onClick={() => { setIndex(0); setOpen(true); }} />
    </Tooltip>
    <Dialog open={open} modalType="modal" onOpenChange={(_, data) => { if (!data.open) close(); }}>
      <DialogSurface className="dwella-page-guide">
        <DialogBody>
          <DialogTitle action={<Button appearance="subtle" aria-label="Close tips" icon={<Dismiss20Regular />} onClick={close} />}>{step.title}</DialogTitle>
          <DialogContent>
            <p className="dwella-page-guide-count">{guide.title} · {index + 1} of {guide.steps.length}</p>
            <p>{step.body}</p>
            {step.to ? <Button appearance="outline" size="small" onClick={() => { close(); navigate(step.to); }}>{step.toLabel}</Button> : null}
          </DialogContent>
          <DialogActions>
            <Button appearance="subtle" onClick={close}>{last ? "Close" : "Skip"}</Button>
            {index > 0 ? <Button onClick={() => setIndex(index - 1)}>Back</Button> : null}
            {!last ? <Button appearance="primary" onClick={() => setIndex(index + 1)}>Next</Button> : <Button appearance="primary" onClick={close}>Got it</Button>}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  </>;
}
