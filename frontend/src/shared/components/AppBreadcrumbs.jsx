import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Breadcrumb, BreadcrumbButton, BreadcrumbDivider, BreadcrumbItem } from "@fluentui/react-components";

import { useCurrentUserQuery, useInvoiceQuery, useLeaseQuery } from "../../Services/queries";
import { getPageMeta } from "../navigation";

// Detail pages name the record once its page has loaded it. The queries are
// disabled, so this only reads what the page already fetched.
function useDetailLabel(pathname) {
  const [section, id, sub] = pathname.split("/").filter(Boolean);
  const leaseId = section === "leases" ? id : null;
  const invoiceId = section === "billing" && id === "invoices" ? sub : null;
  const lease = useLeaseQuery(leaseId, { enabled: false });
  const invoice = useInvoiceQuery(invoiceId, { enabled: false });
  if (leaseId) return lease.data?.reference || "Lease";
  if (invoiceId) return invoice.data?.reference || "Invoice";
  return null;
}

export const AppBreadcrumbs = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery({ staleTime: 60_000 });
  const detail = useDetailLabel(pathname);
  const section = `/${pathname.split("/").filter(Boolean)[0] || "dashboard"}`;

  const crumbs = [{ to: "/dashboard", label: getPageMeta("/dashboard", user)[0] }];
  if (section !== "/dashboard") crumbs.push({ to: section, label: getPageMeta(section, user)[0] });
  if (detail) crumbs.push({ to: pathname, label: detail });

  return (
    <Breadcrumb className="dwella-breadcrumbs" aria-label="Breadcrumb" size="medium">
      {crumbs.map((crumb, index) => {
        const current = index === crumbs.length - 1;
        return (
          <React.Fragment key={crumb.to}>
            <BreadcrumbItem>
              <BreadcrumbButton
                href={crumb.to}
                current={current}
                onClick={(event) => {
                  if (event.metaKey || event.ctrlKey || event.shiftKey) return;
                  event.preventDefault();
                  if (!current) navigate(crumb.to);
                }}
              >
                {crumb.label}
              </BreadcrumbButton>
            </BreadcrumbItem>
            {current ? null : <BreadcrumbDivider />}
          </React.Fragment>
        );
      })}
    </Breadcrumb>
  );
};
