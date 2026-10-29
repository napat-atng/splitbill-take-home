export type GroupSummary = { id: number; name: string };
export type Group = GroupSummary & { members: string[] };
export type Expense = {
  id: number;
  group_id: number;
  description: string;
  paid_by: string;
  amount: string;
  split: { type: "equal" | "exact"; shares: Record<string, string> };
  created_at: string;
  is_deleted: boolean;
};
export type Balances = { group_id: number; balances: Record<string, string> };
export type ExpenseInput = {
  description: string;
  amount: string;
  paid_by: string;
  split:
    | { type: "equal"; members: string[] }
    | { type: "exact"; shares: Record<string, string> };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
  }
  get uncertain() {
    return this.status === undefined || this.status >= 500;
  }
}

const BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

async function request<T>(
  path: string,
  user: string,
  init: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  init.signal?.addEventListener("abort", abort, { once: true });
  if (init.signal?.aborted) controller.abort();
  const timeout = setTimeout(abort, 15000);
  try {
    const response = await fetch(`${BASE}${path}`, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
      headers: { "X-User": user, ...init.headers },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const error = body?.error;
      const message =
        error?.code === "validation_error"
          ? error.details?.[0]?.message ||
            "Check the information and try again."
          : error?.message;
      throw new ApiError(
        message || `The request could not be completed (${response.status}).`,
        response.status,
      );
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Could not reach the API. Check your connection and try again.",
    );
  } finally {
    clearTimeout(timeout);
    init.signal?.removeEventListener("abort", abort);
  }
}

export const api = {
  groups: (user: string, signal?: AbortSignal) =>
    request<GroupSummary[]>("/groups", user, { signal }),
  group: (user: string, id: number, signal?: AbortSignal) =>
    request<Group>(`/groups/${id}`, user, { signal }),
  expenses: (user: string, id: number, signal?: AbortSignal) =>
    request<Expense[]>(`/groups/${id}/expenses`, user, { signal }),
  balances: (user: string, id: number, signal?: AbortSignal) =>
    request<Balances>(`/groups/${id}/balances`, user, { signal }),
  create: (user: string, id: number, payload: ExpenseInput, key: string) =>
    request<Expense>(`/groups/${id}/expenses`, user, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": key },
      body: JSON.stringify(payload),
    }),
  remove: (user: string, id: number, expense: number) =>
    request<void>(`/groups/${id}/expenses/${expense}`, user, {
      method: "DELETE",
    }),
};

export function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}
