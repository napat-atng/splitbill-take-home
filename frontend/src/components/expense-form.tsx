"use client";

import { useRef, useState, type FormEvent } from "react";
import {
  api,
  ApiError,
  errorMessage,
  type Expense,
  type ExpenseInput,
  type Group,
} from "@/lib/api";
import {
  apiMoney,
  equalShares,
  exactPreview,
  formatMoney,
  parseMoney,
  ZERO,
} from "@/lib/money";

type Props = {
  user: string;
  group: Group;
  disabled: boolean;
  onLock: (value: boolean) => void;
  onSaved: (expense: Expense) => void;
};

export function ExpenseForm({ user, group, disabled, onLock, onSaved }: Props) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [payer, setPayer] = useState(user);
  const [type, setType] = useState<"equal" | "exact">("equal");
  const [selected, setSelected] = useState(group.members);
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef<{ key: string; payload: ExpenseInput } | null>(null);
  const submitting = useRef(false);
  const total = parseMoney(amount);
  const exact = exactPreview(total ?? ZERO, selected, values);
  const shares =
    type === "equal" ? equalShares(total ?? ZERO, selected) : exact.shares;
  const validAmount = total !== null && total > ZERO;
  const valid =
    description.trim().length > 0 &&
    validAmount &&
    selected.length > 0 &&
    (type === "equal" || exact.valid);
  const frozen = saving || uncertain || disabled;
  const invalidAmount = amount.length > 0 && !validAmount;

  function toggle(member: string) {
    setSelected((previous) =>
      previous.includes(member)
        ? previous.filter((name) => name !== member)
        : [...previous, member],
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current || (!valid && !pending.current)) return;
    if (!pending.current) {
      pending.current = {
        key: crypto.randomUUID(),
        payload: {
          description: description.trim(),
          amount: apiMoney(total!),
          paid_by: payer,
          split:
            type === "equal"
              ? { type, members: selected }
              : {
                  type,
                  shares: Object.fromEntries(
                    selected.map((member) => [
                      member,
                      apiMoney(shares[member]),
                    ]),
                  ),
                },
        },
      };
    }
    submitting.current = true;
    setSaving(true);
    setError("");
    onLock(true);
    let keepLocked = false;
    try {
      const expense = await api.create(
        user,
        group.id,
        pending.current.payload,
        pending.current.key,
      );
      pending.current = null;
      setUncertain(false);
      setDescription("");
      setAmount("");
      setValues({});
      onSaved(expense);
    } catch (error) {
      keepLocked = !(error instanceof ApiError) || error.uncertain;
      setUncertain(keepLocked);
      if (!keepLocked) pending.current = null;
      setError(errorMessage(error));
    } finally {
      submitting.current = false;
      setSaving(false);
      onLock(keepLocked);
    }
  }

  return (
    <section className="panel expense-form" aria-labelledby="expense-title">
      <div className="section-heading">
        <div>
          <h2 id="expense-title">Add an expense</h2>
          <p>Start with what you paid. We’ll work out the rest.</p>
        </div>
      </div>
      <form onSubmit={submit}>
        <fieldset disabled={frozen} className="form-fields">
          <label htmlFor="description">
            Description
            <input
              id="description"
              value={description}
              maxLength={500}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What was it for?"
              required
            />
          </label>
          <div className="field-pair">
            <label htmlFor="amount">
              Amount <span className="label-note">THB</span>
              <input
                id="amount"
                inputMode="decimal"
                type="text"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                aria-invalid={invalidAmount}
                aria-describedby={invalidAmount ? "amount-error" : undefined}
                required
              />
            </label>
            <label htmlFor="payer">
              Paid by
              <select
                id="payer"
                value={payer}
                onChange={(e) => setPayer(e.target.value)}
              >
                {group.members.map((member) => (
                  <option key={member} value={member}>
                    {member}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {invalidAmount ? (
            <p className="field-error" id="amount-error">
              Enter a positive amount with up to 2 decimal places (maximum
              9,999,999,999.99).
            </p>
          ) : null}
          <fieldset className="split-fieldset">
            <legend>How should we split it?</legend>
            <div className="split-options">
              {(["equal", "exact"] as const).map((mode) => (
                <label
                  key={mode}
                  className={
                    type === mode ? "split-option selected" : "split-option"
                  }
                >
                  <input
                    type="radio"
                    name="split-type"
                    value={mode}
                    checked={type === mode}
                    onChange={() => setType(mode)}
                  />
                  <span>
                    {mode === "equal" ? "Split equally" : "Exact amounts"}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="allocation-heading">
            <span>Split between</span>
            <span>
              {type === "equal"
                ? "Share preview · THB"
                : "Amount per person · THB"}
            </span>
          </div>
          <div className="allocations">
            {group.members.map((member) => {
              const included = selected.includes(member);
              const invalid =
                included &&
                type === "exact" &&
                parseMoney(values[member] ?? "0.00") === null;
              return (
                <div
                  key={member}
                  className={`allocation-row ${included ? "included" : ""}`}
                >
                  <label className="member-choice">
                    <input
                      type="checkbox"
                      checked={included}
                      onChange={() => toggle(member)}
                    />
                    <span className="avatar" aria-hidden="true">
                      {member[0].toUpperCase()}
                    </span>
                    <span>
                      {member}
                      <small>{member === user ? "You" : "Member"}</small>
                    </span>
                  </label>
                  {type === "exact" ? (
                    <input
                      aria-label={`Share for ${member}`}
                      className="share-input"
                      inputMode="decimal"
                      disabled={!included}
                      value={values[member] ?? "0.00"}
                      onChange={(e) =>
                        setValues((old) => ({
                          ...old,
                          [member]: e.target.value,
                        }))
                      }
                      aria-invalid={invalid}
                    />
                  ) : (
                    <span className="share-value">
                      {included && validAmount
                        ? formatMoney(shares[member])
                        : "—"}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
          <div className="split-summary" role="status" aria-live="polite">
            {type === "equal" ? (
              <span>
                {selected.length
                  ? "Any remaining satang go to selected members in selection order."
                  : "Select at least one member."}
              </span>
            ) : (
              <>
                <span>
                  {exact.remaining < ZERO
                    ? "Overallocated"
                    : "Unallocated amount"}
                </span>
                <strong>
                  {formatMoney(
                    exact.remaining < ZERO ? -exact.remaining : exact.remaining,
                  )}{" "}
                  THB
                </strong>
                {!exact.valid && validAmount ? (
                  <small>
                    {Object.keys(exact.shares).length < selected.length
                      ? "Enter valid amounts with up to 2 decimal places."
                      : "The shares must add up to the total before saving."}
                  </small>
                ) : null}
              </>
            )}
          </div>
        </fieldset>
        {error ? (
          <div className="error-message" role="alert">
            <strong>{error}</strong>
            {uncertain ? (
              <p>
                We couldn’t confirm whether it was saved. Retry this same
                expense safely. Your entries are locked until the result is
                confirmed.
              </p>
            ) : null}
          </div>
        ) : null}
        <button
          className="primary-button save-button"
          disabled={saving || disabled || (!valid && !uncertain)}
          type="submit"
        >
          {saving
            ? "Saving expense…"
            : uncertain
              ? "Retry expense"
              : "Save expense"}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path d="M4 12h15m-6-6 6 6-6 6" />
          </svg>
        </button>
      </form>
    </section>
  );
}
