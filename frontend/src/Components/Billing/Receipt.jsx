import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import {
  Button,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Field,
  Textarea,
} from "@fluentui/react-components";
import { Print20Regular } from "@fluentui/react-icons";
import { useCurrentUserQuery, useReceiptQuery } from "../../Services/queries";
import { useReversePaymentMutation } from "../../Services/mutations";
import { getUserAccess } from "../../shared/access";
import { useFormErrors } from "../../shared/useFormErrors";
import PaymentReceipt from "../../shared/components/PaymentReceipt";

export default function Receipt() {
  const { id } = useParams();
  const query = useReceiptQuery(id);
  useEffect(() => {
    if (!query.data?.receipt_number) return;
    const previous = document.title;
    document.title = `${query.data.receipt_number} · Payment receipt · Dwella`;
    return () => {
      document.title = previous;
    };
  }, [query.data?.receipt_number]);
  const { data: user } = useCurrentUserQuery();
  const [confirm, setConfirm] = useState(false);
  const [reason, setReason] = useState("");
  const { validate, fieldProps, clearError, showServerErrors } =
    useFormErrors();
  const reversal = useReversePaymentMutation({
    onSuccess: () => setConfirm(false),
    onError: (error) => showServerErrors(error.data, ["reason"]),
  });
  if (query.isLoading) return <p role="status">Loading receipt…</p>;
  if (query.isError)
    return (
      <div role="alert">
        <p>Could not load this receipt.</p>
        <Button onClick={() => query.refetch()}>Retry</Button>{" "}
        <Link to="/billing/receipts">Back to receipts</Link>
      </div>
    );
  const receipt = query.data;
  const reverse = (event) => {
    event.preventDefault();
    if (
      validate(
        {
          reason: () =>
            reason.trim().length >= 5 && reason.trim().length <= 500
              ? ""
              : "Give a reason between 5 and 500 characters.",
        },
        event.currentTarget,
      )
    )
      reversal.mutate({ id, reason: reason.trim() });
  };
  return (
    <div className="dwella-receipt-page">
      <div className="dwella-receipt-toolbar">
        <Link to="/billing/receipts">← Receipts</Link>
        <div>
          {getUserAccess(user).can_manage_properties && !receipt.reversed_at && !receipt.online_payment ? (
            <Button onClick={() => setConfirm(true)}>Reverse payment</Button>
          ) : null}
          <Button
            appearance="primary"
            icon={<Print20Regular />}
            onClick={() => window.print()}
          >
            Print / Save PDF
          </Button>
        </div>
      </div>
      <PaymentReceipt receipt={receipt} />
      <p className="dwella-receipt-context">
        <Link to={`/billing/invoices/${receipt.invoice_id}`}>
          View invoice {receipt.invoice_reference}
        </Link>
      </p>
      {createPortal(
        <div className="dwella-print-root">
          <PaymentReceipt receipt={receipt} />
        </div>,
        document.body,
      )}
      <Dialog
        open={confirm}
        onOpenChange={(_, data) => !reversal.isPending && setConfirm(data.open)}
      >
        <DialogSurface>
          <form onSubmit={reverse}>
            <DialogBody>
              <DialogTitle>Reverse {receipt.receipt_number}?</DialogTitle>
              <DialogContent>
                <p>
                  The invoice balance will reopen. The original receipt and your
                  reason remain on record. This does not refund a bank or
                  mobile-money transaction.
                </p>
                <Field label="Reason for correction" {...fieldProps("reason")}>
                  <Textarea
                    value={reason}
                    maxLength={500}
                    onChange={(_, data) => {
                      setReason(data.value);
                      clearError("reason");
                    }}
                  />
                </Field>
                {reversal.isError ? (
                  <p role="alert">{reversal.error.message}</p>
                ) : null}
              </DialogContent>
              <DialogActions>
                <Button
                  disabled={reversal.isPending}
                  onClick={() => setConfirm(false)}
                >
                  Keep payment
                </Button>
                <Button
                  type="submit"
                  appearance="primary"
                  disabled={reversal.isPending}
                >
                  {reversal.isPending ? "Reversing…" : "Reverse payment"}
                </Button>
              </DialogActions>
            </DialogBody>
          </form>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
