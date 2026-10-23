import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  OverlayDrawer,
  Spinner,
  Textarea,
  Tooltip,
} from "@fluentui/react-components";
import {
  Add24Regular,
  BotSparkle24Regular,
  Checkmark20Regular,
  Dismiss20Regular,
  Dismiss24Regular,
  History24Regular,
  Send24Filled,
} from "@fluentui/react-icons";

import {
  approveHandyAgentAction,
  chatWithHandyAgent,
  getHandyAgentIdentity,
  getHandyAgentSession,
  HANDY_AGENT_SUGGESTIONS,
  isHandyAgentEnabled,
  listHandyAgentSessions,
  resetHandyAgentCredentials,
} from "../../Services/handyAgent";
import { getAuthToken } from "../../Services/apiClient";
import { queryClient } from "../../Services/queryClient";
import "./handyAssistant.scss";

const emptyConversation = { sessionId: null, messages: [] };

function AssistantMark() {
  return <span className="dwella-assistant-mark" aria-hidden="true">
    <img src={`${import.meta.env.BASE_URL}assets/images/logo/dwella-mark.png`} alt="" />
    <span><BotSparkle24Regular /></span>
  </span>;
}

function appendSegment(segments, event) {
  const last = segments.at(-1);
  if ((event.type === "text" || event.type === "thinking") && last?.kind === event.type) {
    return [...segments.slice(0, -1), { ...last, text: `${last.text}${event.delta || ""}` }];
  }
  if (event.type === "text" || event.type === "thinking") {
    return [...segments, { kind: event.type, text: event.delta || "" }];
  }
  if (event.type === "tool") return [...segments, { kind: "tool", id: event.id, label: event.label }];
  if (event.type === "tool_done") {
    return segments.map((segment) => segment.kind === "tool" && segment.id === event.id
      ? { ...segment, done: true, ok: event.ok }
      : segment);
  }
  if (event.type === "block") return [...segments, { kind: "block", block: event.block }];
  if (event.type === "pending") {
    return [
      ...segments,
      ...(event.cards || []).map((card) => ({
        kind: card.kind === "ask" ? "ask" : "card",
        card,
        state: "pending",
      })),
    ];
  }
  return segments;
}

function relativeTime(value) {
  const minutes = Math.round((Date.now() - new Date(value).getTime()) / 60_000);
  if (!Number.isFinite(minutes) || minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 1440) return `${Math.round(minutes / 60)} hr ago`;
  return new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

function AssistantBlock({ block }) {
  if (!block) return null;
  if (block.type === "text") return <div className="dwella-assistant-copy">{block.markdown}</div>;

  const columns = block.columns || (block.rows?.[0] ? Object.keys(block.rows[0]) : []);
  if (columns.length && block.rows?.length) {
    return (
      <div className="dwella-assistant-data">
        {block.title ? <strong>{block.title}</strong> : null}
        <div className="dwella-assistant-table-wrap">
          <table>
            <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
            <tbody>
              {block.rows.map((row, index) => (
                <tr key={index}>{columns.map((column) => <td key={column}>{String(row[column] ?? "-")}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  return <div className="dwella-assistant-copy">{block.title || "Data ready."}</div>;
}

function ActionFields({ fields = [] }) {
  if (!fields.length) return null;
  return (
    <dl className="dwella-assistant-fields">
      {fields.map((field, index) => (
        <div key={`${field.label}-${index}`}>
          <dt>{field.label}</dt>
          <dd>
            {field.previous !== undefined ? <del>{String(field.previous || "-")}</del> : null}
            {field.rows ? `${field.rows.length} item${field.rows.length === 1 ? "" : "s"}` : String(field.value ?? "-")}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function ActionCard({ segment, busy, onDecision }) {
  const { card, state } = segment;
  const settled = state !== "pending";
  return (
    <section className={`dwella-assistant-action is-${state}`}>
      <span className="dwella-assistant-action-label">
        {settled ? (state === "approved" ? "Approved" : "Declined") : "Needs your approval"}
      </span>
      <strong>{card.summary || card.action || "Confirm this change"}</strong>
      <ActionFields fields={card.fields} />
      {!settled ? (
        <div className="dwella-assistant-action-buttons">
          <Button size="small" appearance="primary" icon={<Checkmark20Regular />} disabled={busy} onClick={() => onDecision(card, true)}>
            Approve
          </Button>
          <Button size="small" icon={<Dismiss20Regular />} disabled={busy} onClick={() => onDecision(card, false)}>
            Decline
          </Button>
        </div>
      ) : null}
    </section>
  );
}

function AskCard({ segment, busy, onAnswer }) {
  const { card, state } = segment;
  const [selected, setSelected] = useState([]);
  if (state !== "pending") return <p className="dwella-assistant-decision">Answer submitted.</p>;
  return (
    <section className="dwella-assistant-question">
      <strong>{card.question}</strong>
      <div>
        {(card.options || []).map((option) => (
          <Button key={String(option)} size="small" appearance={selected.includes(option) ? "primary" : "secondary"} aria-pressed={card.allow_multiple ? selected.includes(option) : undefined} disabled={busy} onClick={() => card.allow_multiple ? setSelected((current) => current.includes(option) ? current.filter((item) => item !== option) : [...current, option]) : onAnswer(card, [option])}>
            {String(option)}
          </Button>
        ))}
        {card.allow_multiple ? <Button size="small" appearance="primary" disabled={busy || !selected.length} onClick={() => onAnswer(card, selected)}>Continue</Button> : null}
        <Button size="small" appearance="subtle" disabled={busy} onClick={() => onAnswer(card, [])}>Skip</Button>
      </div>
    </section>
  );
}

function AgentMessage({ message, busy, onDecision, onAnswer }) {
  if (!message.segs?.length && !message.error) return null;
  return (
    <div className="dwella-assistant-message is-agent">
      <span className="dwella-assistant-avatar"><AssistantMark /></span>
      <div className={`dwella-assistant-bubble${message.error ? " is-error" : ""}`}>
        {(message.segs || []).map((segment, index) => {
          if (segment.kind === "text") return <div className="dwella-assistant-copy" key={index}>{segment.text}</div>;
          if (segment.kind === "thinking") return <details key={index}><summary>Thinking</summary><p>{segment.text}</p></details>;
          if (segment.kind === "tool") return (
            <div className="dwella-assistant-tool" key={segment.id || index}>
              {segment.done ? (segment.ok ? <Checkmark20Regular /> : <Dismiss20Regular />) : <Spinner size="tiny" />}
              <span>{segment.label || "Checking your records"}</span>
            </div>
          );
          if (segment.kind === "block") return <AssistantBlock block={segment.block} key={index} />;
          if (segment.kind === "ask") return <AskCard segment={segment} busy={busy} onAnswer={onAnswer} key={segment.card.id} />;
          if (segment.kind === "card") return <ActionCard segment={segment} busy={busy} onDecision={onDecision} key={segment.card.id} />;
          return null;
        })}
        {message.error ? <p role="alert">{message.error}</p> : null}
      </div>
    </div>
  );
}

export default function HandyAssistant() {
  const enabled = isHandyAgentEnabled();
  const [identity, setIdentity] = useState(null);
  const [open, setOpen] = useState(false);
  const [conversation, setConversation] = useState(emptyConversation);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState(null);
  const [historyError, setHistoryError] = useState("");
  const [identityError, setIdentityError] = useState("");
  const bodyRef = useRef(null);
  const generationRef = useRef(0);

  const loadIdentity = useCallback(async () => {
    const generation = ++generationRef.current;
    resetHandyAgentCredentials();
    setIdentity(null);
    setIdentityError("");
    setConversation(emptyConversation);
    setHistory(null);
    setBusy(false);
    setMessage("");
    if (!enabled || !getAuthToken()) {
      setOpen(false);
      return;
    }
    try {
      const next = await getHandyAgentIdentity();
      if (generation === generationRef.current) setIdentity(next);
    } catch (error) {
      if (generation === generationRef.current && error.name !== "AbortError") setIdentityError(error.message);
    }
  }, [enabled]);

  useEffect(() => {
    loadIdentity();
    window.addEventListener("dwella:auth-changed", loadIdentity);
    return () => window.removeEventListener("dwella:auth-changed", loadIdentity);
  }, [loadIdentity]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k" && identity) {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [identity]);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [conversation.messages, busy]);

  const pendingCards = useMemo(() => conversation.messages.flatMap((entry) => entry.role === "agent"
    ? (entry.segs || []).filter((segment) => (segment.kind === "card" || segment.kind === "ask") && segment.state === "pending")
    : []), [conversation.messages]);

  const updateLastAgent = useCallback((updater) => {
    setConversation((current) => {
      const index = current.messages.length - 1;
      const last = current.messages[index];
      if (last?.role !== "agent") return current;
      return { ...current, messages: [...current.messages.slice(0, index), updater(last)] };
    });
  }, []);

  const handleEvent = useCallback((event) => {
    if (event.type === "session") {
      setConversation((current) => ({ ...current, sessionId: event.session_id }));
      return;
    }
    if (event.type === "data_changed") {
      queryClient.invalidateQueries();
      return;
    }
    if (event.type === "error") {
      updateLastAgent((entry) => ({ ...entry, error: event.message || "The assistant could not finish that request." }));
      return;
    }
    updateLastAgent((entry) => ({ ...entry, segs: appendSegment(entry.segs || [], event) }));
  }, [updateLastAgent]);

  const runStream = useCallback(async (request) => {
    const generation = generationRef.current;
    setConversation((current) => ({ ...current, messages: [...current.messages, { role: "agent", segs: [] }] }));
    try {
      await request((event) => { if (generation === generationRef.current) handleEvent(event); });
      return true;
    } catch (error) {
      if (generation === generationRef.current && error.name !== "AbortError") updateLastAgent((entry) => ({ ...entry, error: error.message || "The assistant is unavailable right now." }));
      return false;
    }
  }, [handleEvent, updateLastAgent]);

  const sendMessage = async (value) => {
    const text = value.trim();
    if (!text || busy || pendingCards.length) return;
    setMessage("");
    setHistory(null);
    setBusy(true);
    setConversation((current) => ({ ...current, messages: [...current.messages, { role: "user", text }] }));
    try {
      await runStream((onEvent) => chatWithHandyAgent({
        session_id: conversation.sessionId,
        message: text,
        page_route: window.location.pathname,
      }, onEvent));
    } finally {
      setBusy(false);
    }
  };

  const markCard = (id, state) => {
    setConversation((current) => ({
      ...current,
      messages: current.messages.map((entry) => entry.role !== "agent" ? entry : {
        ...entry,
        segs: entry.segs.map((segment) => segment.card?.id === id ? { ...segment, state } : segment),
      }),
    }));
  };

  const decide = async (card, approved) => {
    markCard(card.id, approved ? "approved" : "rejected");
    setBusy(true);
    try {
      const succeeded = await runStream((onEvent) => approveHandyAgentAction({
        session_id: conversation.sessionId,
        decisions: { [card.id]: approved },
        page_route: window.location.pathname,
      }, onEvent));
      if (!succeeded) markCard(card.id, "pending");
    } finally {
      setBusy(false);
    }
  };

  const answer = async (card, answers) => {
    markCard(card.id, answers.length ? "approved" : "rejected");
    setBusy(true);
    try {
      const succeeded = await runStream((onEvent) => approveHandyAgentAction({
        session_id: conversation.sessionId,
        answers: { [card.id]: answers },
        page_route: window.location.pathname,
      }, onEvent));
      if (!succeeded) markCard(card.id, "pending");
    } finally {
      setBusy(false);
    }
  };

  const showHistory = async () => {
    if (history) {
      setHistory(null);
      return;
    }
    setHistoryError("");
    setHistory([]);
    try {
      setHistory(await listHandyAgentSessions());
    } catch (error) {
      setHistoryError(error.message);
    }
  };

  const openSession = async (id) => {
    setHistoryError("");
    try {
      const session = await getHandyAgentSession(id);
      setConversation({ sessionId: session.session_id, messages: session.messages || [] });
      setHistory(null);
    } catch (error) {
      setHistoryError(error.message);
    }
  };

  if (!enabled || !getAuthToken()) return null;
  const ready = Boolean(identity?.thinker || identity?.actor);

  return (
    <>
      <Tooltip content="Dwella assistant (Ctrl+K)" relationship="label">
        <Button
          className="dwella-assistant-fab"
          appearance="primary"
          shape="circular"
          size="large"
          icon={open ? <Dismiss24Regular /> : <AssistantMark />}
          aria-label={open ? "Close Dwella assistant" : "Open Dwella assistant"}
          onClick={() => setOpen((value) => !value)}
        />
      </Tooltip>
      <OverlayDrawer
        open={open}
        position="end"
        size="small"
        modalType="non-modal"
        className="dwella-assistant-drawer"
        onOpenChange={(_, data) => setOpen(data.open)}
      >
        <DrawerHeader>
          <DrawerHeaderTitle
            action={(
              <div className="dwella-assistant-header-actions">
                <Tooltip content="Past conversations" relationship="label">
                  <Button appearance={history ? "secondary" : "subtle"} icon={<History24Regular />} aria-label="Past conversations" disabled={busy} onClick={showHistory} />
                </Tooltip>
                <Tooltip content="New conversation" relationship="label">
                  <Button appearance="subtle" icon={<Add24Regular />} aria-label="New conversation" disabled={busy} onClick={() => { setConversation(emptyConversation); setHistory(null); }} />
                </Tooltip>
                <Button appearance="subtle" icon={<Dismiss24Regular />} aria-label="Close assistant" onClick={() => setOpen(false)} />
              </div>
            )}
          >
            <span className="dwella-assistant-title"><AssistantMark /> Dwella assistant</span>
          </DrawerHeaderTitle>
          <p className="dwella-assistant-subtitle">
            {!identity && !identityError ? "Connecting to your workspace..." : busy ? "Working on it..." : identity?.actor ? "Reads your data and asks before making changes" : "Reads and explains your Dwella data"}
          </p>
        </DrawerHeader>
        <DrawerBody ref={bodyRef} className="dwella-assistant-body">
          {identityError ? <div role="alert"><p>{identityError}</p><Button onClick={loadIdentity}>Try again</Button></div> : null}
          {!identity && !identityError ? <Spinner size="small" label="Connecting to Dwella assistant" /> : null}
          {history ? (
            <section className="dwella-assistant-history">
              <h2>Past conversations</h2>
              {historyError ? <p role="alert">{historyError}</p> : null}
              {!history.length && !historyError ? <p>No past conversations yet.</p> : null}
              {history.map((session) => (
                <button type="button" key={session.id} className={session.id === conversation.sessionId ? "is-current" : ""} onClick={() => openSession(session.id)}>
                  <strong>{session.title || "Conversation"}</strong>
                  <span>{relativeTime(session.updated_at)}{session.pending ? " - awaiting approval" : ""}</span>
                </button>
              ))}
            </section>
          ) : (
            <>
              {ready && !conversation.messages.length ? (
                <section className="dwella-assistant-empty">
                  <span className="dwella-assistant-empty-icon"><AssistantMark /></span>
                  <h2>What can I help with?</h2>
                  <p>Ask about your portfolio. Any change will be shown to you before it is saved.</p>
                  <span>Try asking</span>
                  <div>
                    {HANDY_AGENT_SUGGESTIONS.map((suggestion) => (
                      <button type="button" key={suggestion} onClick={() => sendMessage(suggestion)}>{suggestion}</button>
                    ))}
                  </div>
                </section>
              ) : null}
              {conversation.messages.map((entry, index) => entry.role === "user" ? (
                <div className="dwella-assistant-message is-user" key={index}><div className="dwella-assistant-bubble">{entry.text}</div></div>
              ) : (
                <AgentMessage message={entry} busy={busy} onDecision={decide} onAnswer={answer} key={index} />
              ))}
              {busy && conversation.messages.at(-1)?.role === "agent" && !conversation.messages.at(-1)?.segs?.length ? (
                <div className="dwella-assistant-message is-agent is-loading"><span className="dwella-assistant-avatar"><BotSparkle24Regular /></span><Spinner size="tiny" label="Working" /></div>
              ) : null}
            </>
          )}
        </DrawerBody>
        {!history ? (
          <form className="dwella-assistant-composer" onSubmit={(event) => { event.preventDefault(); sendMessage(message); }}>
            {pendingCards.length ? <p>Approve or decline the proposed change above to continue.</p> : null}
            <div>
              <Textarea
                resize="none"
                rows={2}
                value={message}
                disabled={!ready || busy || Boolean(pendingCards.length)}
                placeholder={pendingCards.length ? "Review the proposed change above" : "Ask about your portfolio"}
                aria-label="Message Dwella assistant"
                onChange={(_, data) => setMessage(data.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage(message);
                  }
                }}
              />
              <Button appearance="primary" shape="circular" icon={<Send24Filled />} aria-label="Send message" type="submit" disabled={!ready || busy || !message.trim() || Boolean(pendingCards.length)} />
            </div>
          </form>
        ) : null}
      </OverlayDrawer>
    </>
  );
}
