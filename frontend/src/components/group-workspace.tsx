"use client";

import { useEffect, useState } from "react";
import {
  api,
  errorMessage,
  type Balances,
  type Expense,
  type Group,
} from "@/lib/api";
import { formatMoney, fromApiMoney, ZERO } from "@/lib/money";
import { ExpenseForm } from "./expense-form";

type Data = {
  revision: number;
  group?: Group;
  expenses?: Expense[];
  balances?: Balances;
  error?: string;
};
const dateFormat = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeZone: "Asia/Bangkok",
});

export function GroupWorkspace({
  user,
  groupId,
  onLock,
}: {
  user: string;
  groupId: number;
  onLock: (locked: boolean) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState<Data | null>(null);
  const [notice, setNotice] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [formLocked, setFormLocked] = useState(false);
  const loading = data?.revision !== revision;

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api.group(user, groupId, controller.signal),
      api.expenses(user, groupId, controller.signal),
      api.balances(user, groupId, controller.signal),
    ])
      .then(([group, expenses, balances]) => {
        if (!controller.signal.aborted)
          setData({ revision, group, expenses, balances });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setData((previous) => ({
            ...previous,
            revision,
            error: errorMessage(error),
          }));
      });
    return () => controller.abort();
  }, [user, groupId, revision]);

  function lockForm(locked: boolean) {
    setFormLocked(locked);
    onLock(locked);
  }
  function saved(expense: Expense) {
    setNotice(
      expense.is_deleted
        ? "This expense was already saved and has since been deleted."
        : "Expense saved. Your group’s balances are updated below.",
    );
    setRevision((value) => value + 1);
  }

  async function remove(id: number) {
    if (deleting) return;
    setDeleting(true);
    setDeleteError("");
    onLock(true);
    try {
      await api.remove(user, groupId, id);
      setConfirmDelete(null);
      setNotice("Expense deleted. It no longer counts towards your balances.");
      setRevision((value) => value + 1);
    } catch (error) {
      setDeleteError(errorMessage(error));
    } finally {
      setDeleting(false);
      onLock(false);
    }
  }

  return (
    <>
      {notice ? (
        <div className="success-message" role="status">
          <span>{notice}</span>
          <button
            type="button"
            aria-label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            Dismiss
          </button>
        </div>
      ) : null}
      {data?.error && !loading ? (
        <div className="error-message workspace-error" role="alert">
          <span>{data.error}</span>
          <button
            type="button"
            className="text-button"
            onClick={() => setRevision((value) => value + 1)}
          >
            Try again
          </button>
        </div>
      ) : null}
      <div className="workspace-grid">
        {data?.group ? (
          <ExpenseForm
            user={user}
            group={data.group}
            disabled={deleting}
            onLock={lockForm}
            onSaved={saved}
          />
        ) : (
          <section className="panel loading-panel" aria-busy={loading}>
            <h2>Add an expense</h2>
            <p>
              {loading
                ? "Loading your group…"
                : "Your group could not be loaded. Try again above."}
            </p>
          </section>
        )}
        <section
          className="panel balance-panel"
          aria-labelledby="balance-title"
          aria-busy={loading}
        >
          <div className="section-heading">
            <div>
              <h2 id="balance-title">Group balances</h2>
              <p>Where everyone stands.</p>
            </div>
            <span className="currency-label">THB</span>
          </div>
          {loading ? (
            <p className="loading-copy" role="status">
              Updating balances…
            </p>
          ) : data?.error ? (
            <p className="empty-copy">
              Balances unavailable. Reload the group to try again.
            </p>
          ) : (
            <ul className="balance-list">
              {Object.entries(data?.balances?.balances ?? {}).map(
                ([member, amount]) => {
                  const value = fromApiMoney(amount);
                  return (
                    <li key={member} className="balance-row">
                      <span className="avatar" aria-hidden="true">
                        {member[0].toUpperCase()}
                      </span>
                      <span className="balance-person">
                        {member}
                        <small>{member === user ? "You" : "Member"}</small>
                      </span>
                      <span
                        className={`balance-amount ${value > ZERO ? "receivable" : value < ZERO ? "payable" : "settled"}`}
                      >
                        <strong>
                          {value > ZERO ? "+" : ""}
                          {formatMoney(amount)}
                        </strong>
                        <small>
                          {value > ZERO
                            ? "To receive"
                            : value < ZERO
                              ? "To pay"
                              : "Settled up"}
                        </small>
                      </span>
                    </li>
                  );
                },
              )}
            </ul>
          )}
          <div className="balance-explanation">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 11v6M12 7v1" />
            </svg>
            <p>
              Green means money to receive.
              <br />
              Red means money to pay.
            </p>
          </div>
        </section>
      </div>
      <section
        className="panel history-panel"
        aria-labelledby="history-title"
        aria-busy={loading}
      >
        <div className="section-heading">
          <div>
            <h2 id="history-title">Expenses</h2>
            <p>The things you’ve shared, all in one place.</p>
          </div>
          {!loading && !data?.error ? (
            <span className="expense-count">
              {data?.expenses?.length ?? 0}{" "}
              {(data?.expenses?.length ?? 0) === 1 ? "expense" : "expenses"}
            </span>
          ) : null}
        </div>
        {deleteError ? (
          <div className="error-message" role="alert">
            {deleteError} You can retry the deletion safely.
          </div>
        ) : null}
        {loading ? (
          <p className="loading-copy" role="status">
            Loading expenses…
          </p>
        ) : data?.error ? (
          <p className="empty-copy">
            Expenses unavailable. Reload the group to try again.
          </p>
        ) : data?.expenses?.length ? (
          <ul className="expense-list">
            {data.expenses.map((expense) => (
              <li key={expense.id} className="expense-row">
                <div className="expense-description">
                  <h3>{expense.description}</h3>
                  <p>
                    Paid by <strong>{expense.paid_by}</strong>
                    <span aria-hidden="true"> · </span>
                    <time dateTime={expense.created_at}>
                      {dateFormat.format(new Date(expense.created_at))}
                    </time>
                  </p>
                  <details>
                    <summary>
                      {expense.split.type === "equal"
                        ? "Equal split"
                        : "Exact split"}{" "}
                      · {Object.keys(expense.split.shares).length}{" "}
                      {Object.keys(expense.split.shares).length === 1
                        ? "person"
                        : "people"}
                    </summary>
                    <ul className="expense-shares">
                      {Object.entries(expense.split.shares).map(
                        ([member, amount]) => (
                          <li key={member}>
                            <span>{member}</span>
                            <span>{formatMoney(amount)} THB</span>
                          </li>
                        ),
                      )}
                    </ul>
                  </details>
                </div>
                <div className="expense-actions">
                  <strong className="expense-total">
                    {formatMoney(expense.amount)} <small>THB</small>
                  </strong>
                  {expense.paid_by === user ? (
                    <button
                      type="button"
                      className="text-button delete-button"
                      disabled={deleting || formLocked}
                      onClick={() => {
                        setDeleteError("");
                        setConfirmDelete(expense.id);
                      }}
                      aria-label={`Delete ${expense.description}`}
                    >
                      Delete
                    </button>
                  ) : null}
                </div>
                {confirmDelete === expense.id ? (
                  <div className="delete-confirmation">
                    <span>
                      Delete this expense? Balances will be recalculated.
                    </span>
                    <div>
                      <button
                        type="button"
                        className="danger-button"
                        disabled={deleting || formLocked}
                        onClick={() => remove(expense.id)}
                      >
                        {deleting ? "Deleting…" : "Confirm delete"}
                      </button>
                      <button
                        type="button"
                        className="text-button"
                        disabled={deleting}
                        onClick={() => {
                          setConfirmDelete(null);
                          setDeleteError("");
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-history">
            <svg
              width="40"
              height="40"
              viewBox="0 0 40 40"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <rect x="10" y="5" width="20" height="30" rx="3" />
              <path d="M15 13h10M15 19h10M15 25h6" />
            </svg>
            <h3>No expenses yet</h3>
            <p>Add your first expense using the form above.</p>
          </div>
        )}
      </section>
    </>
  );
}
