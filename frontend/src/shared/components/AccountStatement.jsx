import React from "react";
import { Button } from "@fluentui/react-components";
import { formatDate } from "../format";
import { statementMoney } from "../statement.mjs";

export function StatementBalances({ data }) {
  const money = (value, full = false) => statementMoney(value, data.currency, full);
  return (
    <section className="portal-statement__balance" aria-label="Period balances">
      <div className="portal-statement__balance-heading">
        <div><span>Closing balance</span><strong>{money(data.totals.closing_balance, true)}</strong></div>
        <span className="portal-statement__as-of">{formatDate(data.date_to)}</span>
      </div>
      {data.totals.closing_balance.startsWith("-") && <p className="portal-statement__credit">Credit balance</p>}
      <dl className="portal-statement__facts">
        {[ ["Opening", "Opening balance", "opening_balance"], ["Charges", "Charges in this period", "charges"],
          ["Payments", "Payments in this period", "payments"] ].map(([short, label, key]) => (
          <div key={key}><dt><span className="portal-statement__desktop">{label}</span><span className="portal-statement__mobile">{short}</span></dt>
            <dd>{money(data.totals[key])}</dd></div>
        ))}
      </dl>
    </section>
  );
}

export function StatementActivity({ data, onPage }) {
  const money = (value, full = false) => statementMoney(value, data.currency, full);
  const home = (row) => [row.property, row.unit].filter(Boolean).join(" · ");
  const label = (row) => `${row.type === "charge" ? "Charge" : "Payment"} · ${row.reference}`;
  return (
    <section className="portal-statement__activity" aria-labelledby="statement-activity-heading">
      <div className="portal-statement__activity-heading"><h2 id="statement-activity-heading">Account activity</h2>
        <span>{data.total_rows} {data.total_rows === 1 ? "entry" : "entries"}</span></div>
      {!data.rows.length ? <div className="portal-statement__empty"><h3>No activity in this period</h3>
        <p>Your opening and closing balances are included in the CSV.</p></div> : <>
        <div className="portal-statement__desktop">
          <table className="dwella-table portal-statement__table">
            <caption className="portal-statement__sr-only">Charges, payments and running balance in {data.currency}</caption>
            <thead><tr><th scope="col">Date</th><th scope="col">Activity / reference</th><th scope="col">Home</th>
              <th scope="col" className="is-numeric">Charges ({data.currency})</th><th scope="col" className="is-numeric">Payments ({data.currency})</th>
              <th scope="col" className="is-numeric">Balance ({data.currency})</th></tr></thead>
            <tbody>{data.rows.map((row) => <tr key={`${row.type}-${row.id}`}>
              <td>{formatDate(row.date)}</td><td>{label(row)}</td><td>{home(row)}</td>
              <td className="is-numeric">{row.type === "charge" ? money(row.debit) : "—"}</td>
              <td className="is-numeric">{row.type === "payment" ? money(row.credit) : "—"}</td>
              <td className="is-numeric">{money(row.balance)}</td>
            </tr>)}</tbody>
          </table>
        </div>
        <ul className="portal-statement__mobile portal-statement__entries">
          {data.rows.map((row) => <li key={`${row.type}-${row.id}`}>
            <div className="portal-statement__entry-heading"><strong>{label(row)}</strong><strong>{money(row.type === "charge" ? row.debit : row.credit)}</strong></div>
            <div className="portal-statement__entry-context"><time dateTime={row.date}>{formatDate(row.date)}</time><span>{home(row)}</span></div>
            <p className="portal-statement__running">Balance {money(row.balance, true)}</p>
          </li>)}
        </ul>
      </>}
      <footer className="portal-statement__pagination">
        <span>Page {data.page} of {data.total_pages}</span>
        <div><Button disabled={data.page <= 1} onClick={() => onPage(data.page - 1)}>Previous</Button>
          <Button disabled={data.page >= data.total_pages} onClick={() => onPage(data.page + 1)}>Next</Button></div>
      </footer>
    </section>
  );
}

