import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@fluentui/react-components";
import { Add20Regular } from "@fluentui/react-icons";

import { usePortalOverview, usePortalRequests } from "../../Services/portal";
import { PageActions, SegmentedFilter, StatusBadge } from "../../shared/components";
import { formatDate } from "../../shared/format";
import { categoryLabel, formatVisit, statusBadgeProps } from "../../shared/maintenance";
import PortalState from "./PortalState";
import ReportRepairDrawer from "./ReportRepairDrawer";

const views = [
  { value: "open", label: "Open" },
  { value: "all", label: "All repairs" },
];

export default function PortalMaintenance() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [view, setView] = useState("open");
  const [reporting, setReporting] = useState(false);
  const overview = usePortalOverview();
  const query = usePortalRequests({ page_size: 50, ...(view === "open" ? { open: "true" } : {}) }, { placeholderData: (previous) => previous });
  const homes = (overview.data?.current_leases || []).map((lease) => ({
    id: lease.id,
    label: `${lease.property_name} · ${lease.unit_name}`,
  }));
  const canReport = homes.length > 0;

  // Home's "Report a repair" links here with ?report=1.
  useEffect(() => {
    if (params.get("report") === "1" && canReport) {
      setReporting(true);
      setParams({}, { replace: true });
    }
  }, [params, setParams, canReport]);

  return (
    <PortalState query={query} label="your repairs">
      {(data) => {
        const requests = data.results || [];
        return (
          <div className="dwella-portal">
            <div className="dwella-page-toolbar">
              <SegmentedFilter label="Filter repairs" options={views} value={view} onChange={setView} />
              {canReport ? (
                <PageActions>
                  <Button appearance="primary" icon={<Add20Regular />} onClick={() => setReporting(true)}>Report a repair</Button>
                </PageActions>
              ) : null}
            </div>
            {!overview.isLoading && !canReport ? (
              <p className="dwella-callout is-info">Repairs can be reported while you have a current lease.</p>
            ) : null}
            {requests.length ? (
              <div className="dwella-table-card">
                <table className="dwella-table dwella-portal-table">
                  <thead>
                    <tr>
                      <th scope="col">Repair</th>
                      <th scope="col">Home</th>
                      <th scope="col">Reported</th>
                      <th scope="col">Visit</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.map((request) => (
                      <tr
                        key={request.id}
                        tabIndex={0}
                        onClick={() => navigate(`/maintenance/${request.id}`)}
                        onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && (event.preventDefault(), navigate(`/maintenance/${request.id}`))}
                      >
                        <td>
                          <span className="dwella-who">
                            <span>
                              <strong>{request.title}</strong>
                              <small>{request.reference} · {categoryLabel(request.category)}</small>
                            </span>
                          </span>
                        </td>
                        <td>{request.unit_name ? `${request.property_name} · ${request.unit_name}` : request.property_name}</td>
                        <td>{formatDate(request.created_at)}</td>
                        <td>{request.scheduled_for ? formatVisit(request.scheduled_for) : "—"}</td>
                        <td><StatusBadge {...statusBadgeProps(request.status)} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="dwella-muted-copy">{view === "open" ? "No open repairs." : "No repairs reported yet."}</p>
            )}
            {reporting ? (
              <ReportRepairDrawer
                homes={homes}
                onClose={() => setReporting(false)}
                onSaved={(created) => {
                  setReporting(false);
                  navigate(`/maintenance/${created.id}`);
                }}
              />
            ) : null}
          </div>
        );
      }}
    </PortalState>
  );
}
