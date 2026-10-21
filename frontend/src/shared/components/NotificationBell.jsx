import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  Popover,
  PopoverTrigger,
  PopoverSurface,
  Tooltip,
} from "@fluentui/react-components";
import { Alert20Regular, Dismiss20Regular } from "@fluentui/react-icons";
import {
  useCurrentUserQuery,
  useNotificationsQuery,
} from "../../Services/queries";
import { useReadNotificationsMutation } from "../../Services/mutations";
import { getUserAccess } from "../access";
import { formatDate } from "../format";
import "./notifications.scss";

export function NotificationBell() {
  const { data: user } = useCurrentUserQuery();
  const enabled = getUserAccess(user).persona === "landlord";
  const query = useNotificationsQuery({ enabled });
  const [open, setOpen] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const mutation = useReadNotificationsMutation();
  if (!enabled) return null;
  const items = query.data?.items || [];
  const count = query.data?.unread_count || 0;
  const shown = unreadOnly ? items.filter((item) => !item.read) : items;
  const mark = (ids) => {
    if (ids.length) mutation.mutate(ids);
  };
  return (
    <Popover
      open={open}
      onOpenChange={(_, data) => setOpen(data.open)}
      positioning={{ position: "below", align: "end" }}
    >
      <PopoverTrigger disableButtonEnhancement>
        <Tooltip content="Notifications" relationship="label">
          <Button
            className="dwella-icon-action dwella-notification-trigger"
            appearance="subtle"
            icon={<Alert20Regular />}
            aria-label={`Notifications${count ? `, ${count} unread` : ""}`}
          >
            {count ? (
              <span className="dwella-notification-count">
                {count > 99 ? "99+" : count}
              </span>
            ) : null}
          </Button>
        </Tooltip>
      </PopoverTrigger>
      <PopoverSurface
        className="dwella-notification-panel"
        aria-label="Notifications"
      >
        <header>
          <h2>Notifications {count ? <small>{count} unread</small> : null}</h2>
          <Button
            size="small"
            appearance="subtle"
            icon={<Dismiss20Regular />}
            aria-label="Close notifications"
            onClick={() => setOpen(false)}
          />
        </header>
        <div className="dwella-notification-controls">
          <Button
            size="small"
            appearance="subtle"
            aria-pressed={unreadOnly}
            onClick={() => setUnreadOnly(!unreadOnly)}
          >
            {unreadOnly ? "Show all" : "Unread only"}
          </Button>
          <Button
            size="small"
            appearance="subtle"
            disabled={!count || mutation.isPending}
            onClick={() =>
              mark(items.filter((item) => !item.read).map((item) => item.id))
            }
          >
            {mutation.isPending ? "Marking…" : "Mark all read"}
          </Button>
        </div>
        {query.isLoading ? (
          <p role="status">Loading notifications…</p>
        ) : query.isError ? (
          <div role="alert">
            <p>Could not load notifications.</p>
            <Button onClick={() => query.refetch()}>Retry</Button>
          </div>
        ) : !shown.length ? (
          <p className="dwella-notification-empty">
            {unreadOnly
              ? "You’re all caught up."
              : "No alerts right now. Overdue rent, lease endings and open repairs will appear here."}
          </p>
        ) : (
          <ul>
            {shown.map((item) => (
              <li key={item.id} className={item.read ? "is-read" : "is-unread"}>
                <span
                  className={`dwella-notification-dot ${item.kind}`}
                  aria-hidden="true"
                />
                <div>
                  <Link
                    to={item.path}
                    onClick={() => {
                      if (!item.read) mark([item.id]);
                      setOpen(false);
                    }}
                  >
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                  </Link>
                  <small>{formatDate(item.date)}</small>
                  {!item.read ? (
                    <Button
                      size="small"
                      appearance="subtle"
                      disabled={mutation.isPending}
                      onClick={() => mark([item.id])}
                    >
                      Mark read
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        {mutation.isError ? (
          <p role="alert">Could not mark notifications as read. Try again.</p>
        ) : null}
        <footer>Current alerts from your portfolio.</footer>
      </PopoverSurface>
    </Popover>
  );
}
