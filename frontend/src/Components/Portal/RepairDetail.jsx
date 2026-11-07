import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button, Textarea } from "@fluentui/react-components";
import { Camera20Regular } from "@fluentui/react-icons";
import { toast } from "react-toastify";

import { resolveMediaUrl } from "../../Services/apiClient";
import { usePortalRequest, useRepairMessage, useRepairPhoto } from "../../Services/portal";
import { StatusBadge } from "../../shared/components";
import { formatDate, initials } from "../../shared/format";
import { categoryLabel, formatVisit, statusBadgeProps } from "../../shared/maintenance";
import { MAX_PHOTOS, PHOTO_TYPES, checkPhotos } from "../Maintenance/RequestDrawer";
import PortalState from "./PortalState";
import "../Maintenance/maintenance.scss";

const stamp = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const OPEN = ["new", "scheduled", "in_progress"];

function Photos({ request, open }) {
  const mutation = useRepairPhoto();
  const [uploading, setUploading] = useState(false);
  const room = MAX_PHOTOS - request.photos.length;
  const add = async (event) => {
    const { accepted, problem } = checkPhotos(Array.from(event.target.files || []), room);
    event.target.value = "";
    if (problem) toast.error(problem);
    if (!accepted.length) return;
    setUploading(true);
    for (const file of accepted) {
      try {
        await mutation.mutateAsync({ id: request.id, file });
      } catch (error) {
        toast.error(error.data?.image?.[0] || error.message || "Could not upload the photo.");
      }
    }
    setUploading(false);
  };
  if (!request.photos.length && !open) return null;
  return (
    <div className="dwella-request-photos">
      {request.photos.map((photo, index) => (
        <a key={photo.id} href={resolveMediaUrl(photo.image)} target="_blank" rel="noreferrer">
          <img src={resolveMediaUrl(photo.image)} alt={`Photo ${index + 1} of ${request.title}`} loading="lazy" />
        </a>
      ))}
      {open && room > 0 ? (
        <label className={`dwella-photo-tile ${uploading ? "is-busy" : ""}`}>
          <Camera20Regular />
          {uploading ? "Uploading…" : "Add photo"}
          <input type="file" accept={PHOTO_TYPES.join(",")} multiple disabled={uploading} onChange={add} />
        </label>
      ) : null}
    </div>
  );
}

function Updates({ request, open }) {
  const [body, setBody] = useState("");
  const mutation = useRepairMessage({
    onSuccess: () => setBody(""),
    onError: (error) => toast.error(error.data?.body?.[0] || error.message || "Could not send."),
  });
  const send = (event) => {
    event.preventDefault();
    const text = body.trim();
    if (!text || mutation.isPending) return;
    mutation.mutate({ id: request.id, body: text });
  };
  return (
    <section className="dwella-surface">
      <h3>Updates</h3>
      <ul className="dwella-thread dwella-portal-thread">
        {request.updates.map((update) =>
          update.kind === "status" ? (
            <li key={update.id} className="is-status">
              <span>{update.body}</span>
              <small>{stamp.format(new Date(update.created_at))}</small>
            </li>
          ) : (
            <li key={update.id} className={update.from_you ? "is-yours" : undefined}>
              <span className="dwella-avatar is-navy" aria-hidden="true">{initials(update.from_you ? "You" : update.author_name || "")}</span>
              <div>
                <p className="dwella-thread-meta">
                  <strong>{update.from_you ? "You" : update.author_name || "Your property manager"}</strong>
                  <small>{stamp.format(new Date(update.created_at))}</small>
                </p>
                <p className="dwella-thread-body">{update.body}</p>
              </div>
            </li>
          ),
        )}
      </ul>
      {open ? (
        <form className="dwella-reply" onSubmit={send}>
          <Textarea
            aria-label="Write an update for your property manager"
            placeholder="Write an update for your property manager…"
            rows={2}
            maxLength={2000}
            value={body}
            onChange={(_, d) => setBody(d.value)}
          />
          <div className="dwella-reply-actions">
            <span />
            <Button appearance="primary" type="submit" disabled={!body.trim() || mutation.isPending}>
              {mutation.isPending ? "Sending…" : "Send update"}
            </Button>
          </div>
        </form>
      ) : (
        <p className="dwella-muted-copy">This repair is closed. <Link to="/maintenance?report=1">Report a new repair</Link> if the problem comes back.</p>
      )}
    </section>
  );
}

export default function PortalRepairDetail() {
  const { id } = useParams();
  const query = usePortalRequest(id);
  return (
    <PortalState query={query} label="this repair">
      {(request) => {
        const open = OPEN.includes(request.status);
        return (
          <div className="dwella-portal">
            <header className="dwella-detail-header">
              <div>
                <div className="dwella-detail-title">
                  <h1>{request.title}</h1>
                  <StatusBadge {...statusBadgeProps(request.status)} />
                </div>
                <p>{request.reference} · {categoryLabel(request.category)} · reported {formatDate(request.created_at)}</p>
              </div>
            </header>
            <div className="dwella-portal-grid">
              <section className="dwella-surface">
                <h3>Details</h3>
                <dl className="dwella-detail-list">
                  <div><dt>Home</dt><dd>{request.unit_name ? `${request.property_name} · ${request.unit_name}` : request.property_name}</dd></div>
                  <div><dt>Visit</dt><dd>{request.scheduled_for ? formatVisit(request.scheduled_for) : "Not scheduled yet"}</dd></div>
                  <div><dt>Repairer</dt><dd>{request.vendor_name || "Not assigned yet"}</dd></div>
                  <div><dt>Entry</dt><dd>{request.permission_to_enter ? "Allowed if you're not home" : "Only when you're home"}</dd></div>
                  {request.access_notes ? <div><dt>Best times</dt><dd>{request.access_notes}</dd></div> : null}
                  {request.charge_invoice_id ? <div><dt>Charge</dt><dd><Link to={`/billing?invoice=${request.charge_invoice_id}`}>View invoice</Link></dd></div> : null}
                </dl>
                {request.description ? <p className="dwella-muted-copy">{request.description}</p> : null}
                <Photos request={request} open={open} />
              </section>
              <Updates request={request} open={open} />
            </div>
            <p className="dwella-muted-copy">Internal notes and repair costs stay with your property manager.</p>
          </div>
        );
      }}
    </PortalState>
  );
}
