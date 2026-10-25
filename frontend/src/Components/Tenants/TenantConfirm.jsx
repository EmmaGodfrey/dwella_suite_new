import React from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
} from "@fluentui/react-components";
import { toast } from "react-toastify";

import { useTenantActionMutation } from "../../Services/mutations";

const firstName = (name) => name.split(" ")[0];

// Archive and remove-portal-access are reversible but change what the tenant
// sees, so both ask first. A refusal from the API (a lease opened meanwhile)
// is shown in the dialog rather than a toast.
const copy = {
  archive: (tenant) => ({
    title: `Archive ${tenant.full_name}?`,
    body: [
      `${firstName(tenant.full_name)} will be hidden from your tenant lists and can't be put on a new lease until restored. Their history stays: leases, invoices, payments, documents and repairs.`,
      "Any pending portal invitation is withdrawn and the tenant portal closes.",
    ],
    confirm: "Archive tenant",
    pending: "Archiving…",
    done: `${tenant.full_name} archived.`,
  }),
  "remove-portal-access": (tenant) => ({
    title: `Remove portal access for ${tenant.full_name}?`,
    body: [
      `${firstName(tenant.full_name)} will no longer see their lease, invoices, receipts or repairs in Dwella. Pending invitations are withdrawn.`,
      `${firstName(tenant.full_name)} stays a tenant and every record is kept. You can invite them again at any time.`,
    ],
    confirm: "Remove access",
    pending: "Removing…",
    done: "Portal access removed.",
  }),
};

export default function TenantConfirm({ tenant, action, onClose }) {
  const text = copy[action](tenant);
  const mutation = useTenantActionMutation({
    onSuccess: () => {
      toast.success(text.done);
      onClose();
    },
  });
  const error = mutation.error;
  const reason = error?.data && typeof error.data === "object"
    ? Object.values(error.data).flat().find((item) => typeof item === "string")
    : null;
  return (
    <Dialog open onOpenChange={(_, data) => !data.open && !mutation.isPending && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{error ? (action === "archive" ? `${tenant.full_name} can't be archived yet` : "Portal access was not removed") : text.title}</DialogTitle>
          <DialogContent>
            {error ? (
              <p role="alert">{reason || error.message}</p>
            ) : (
              text.body.map((line, index) => <p key={index} className={index ? "dwella-muted-copy" : undefined}>{line}</p>)
            )}
          </DialogContent>
          <DialogActions>
            <Button disabled={mutation.isPending} onClick={onClose}>{error ? "Close" : "Cancel"}</Button>
            {error ? null : (
              <Button
                appearance="primary"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate({ id: tenant.id, action })}
              >
                {mutation.isPending ? text.pending : text.confirm}
              </Button>
            )}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
