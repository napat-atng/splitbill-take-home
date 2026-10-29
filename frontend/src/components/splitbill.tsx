"use client";

import { useEffect, useState } from "react";
import { api, errorMessage, type GroupSummary } from "@/lib/api";
import { GroupWorkspace } from "./group-workspace";

const USERS = ["alice", "bob", "carol", "dan"];

export function SplitBill() {
  const [scope, setScope] = useState({ user: "alice", version: 0 });
  const [groupId, setGroupId] = useState<number | null>(null);
  const [locked, setLocked] = useState(false);
  const [result, setResult] = useState<{
    key: string;
    groups: GroupSummary[];
    error?: string;
  } | null>(null);
  const key = `${scope.user}:${scope.version}`;
  const groups = result?.key === key ? result.groups : [];
  const loading = result?.key !== key;
  const error = result?.key === key ? result.error : undefined;
  const selected = groups.find((group) => group.id === groupId) ?? groups[0];

  useEffect(() => {
    const controller = new AbortController();
    api
      .groups(scope.user, controller.signal)
      .then((groups) => {
        if (!controller.signal.aborted) setResult({ key, groups });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResult({ key, groups: [], error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [scope.user, key]);

  return (
    <main className="app-shell" id="main-content">
      <header className="app-header">
        <div className="wordmark">
          <svg
            width="33"
            height="33"
            viewBox="0 0 32 32"
            fill="none"
            aria-hidden="true"
          >
            <rect width="32" height="32" rx="9" fill="currentColor" />
            <path
              d="M10 10h12M10 16h12M10 22h7M16 7v18"
              stroke="white"
              strokeWidth="1.7"
              strokeLinecap="round"
            />
          </svg>
          <span>SplitBill</span>
        </div>
        <span className="header-note">Good company. Fair shares.</span>
      </header>
      <div className="page-heading">
        <div>
          <h1>Shared expenses, sorted.</h1>
          <p>Less maths. More time together.</p>
        </div>
        <span className="currency-tag">
          Thai baht <strong>THB</strong>
        </span>
      </div>
      <section className="group-toolbar" aria-label="Choose user and group">
        <label htmlFor="user">
          Viewing as
          <select
            id="user"
            value={scope.user}
            disabled={locked}
            onChange={(e) => {
              setScope((previous) => ({
                user: e.target.value,
                version: previous.version + 1,
              }));
              setGroupId(null);
            }}
          >
            {USERS.map((user) => (
              <option key={user} value={user}>
                {user}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor="group">
          Your group
          <select
            id="group"
            value={selected?.id ?? ""}
            disabled={locked || loading || groups.length === 0}
            onChange={(e) => setGroupId(Number(e.target.value))}
          >
            {groups.length ? (
              groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))
            ) : (
              <option value="">
                {loading ? "Loading groups…" : "No groups available"}
              </option>
            )}
          </select>
        </label>
        <p className="group-hint">
          Shared costs.
          <br />
          <strong>Every satang accounted for.</strong>
        </p>
      </section>
      {locked ? (
        <p className="lock-hint" role="status">
          Finish or retry the current expense before switching user or group.
        </p>
      ) : null}
      {error ? (
        <div className="error-message" role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="text-button"
            onClick={() =>
              setScope((previous) => ({
                ...previous,
                version: previous.version + 1,
              }))
            }
          >
            Try again
          </button>
        </div>
      ) : loading ? (
        <section className="panel loading-panel" role="status">
          <h2>Loading your groups…</h2>
          <p>Getting everything ready.</p>
        </section>
      ) : selected ? (
        <GroupWorkspace
          key={`${key}:${selected.id}`}
          user={scope.user}
          groupId={selected.id}
          onLock={setLocked}
        />
      ) : (
        <section className="panel empty-history">
          <h2>No groups yet</h2>
          <p>You aren’t a member of any groups.</p>
        </section>
      )}
      <footer className="app-footer">
        <span>Split fairly. Settle easily.</span>
        <span>All amounts in THB.</span>
      </footer>
    </main>
  );
}
