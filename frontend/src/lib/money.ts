/** All arithmetic is integer satang. Never convert money to a floating-point Number. */
const HUNDRED = BigInt(100);
export const ZERO = BigInt(0);
const MAX = BigInt("999999999999");

export function parseMoney(value: string): bigint | null {
  if (!/^[0-9]+(?:\.[0-9]{1,2})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  if (whole.replace(/^0+/, "").length > 10) return null;
  const satang = BigInt(whole) * HUNDRED + BigInt(fraction.padEnd(2, "0"));
  return satang <= MAX ? satang : null;
}

export function apiMoney(satang: bigint): string {
  const absolute = satang < ZERO ? -satang : satang;
  return `${satang < ZERO ? "-" : ""}${absolute / HUNDRED}.${String(absolute % HUNDRED).padStart(2, "0")}`;
}

export function fromApiMoney(value: string): bigint {
  if (!/^-?[0-9]+\.[0-9]{2}$/.test(value))
    throw new Error("Invalid amount from API");
  return BigInt(value.replace(".", ""));
}

export function formatMoney(value: bigint | string): string {
  const [whole, fraction] = apiMoney(
    typeof value === "string" ? fromApiMoney(value) : value,
  ).split(".");
  return `${whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}.${fraction}`;
}

export function equalShares(
  total: bigint,
  members: string[],
): Record<string, bigint> {
  if (
    members.length === 0 ||
    new Set(members).size !== members.length ||
    total < ZERO
  )
    return {};
  const count = BigInt(members.length);
  const base = total / count;
  const remainder = total % count;
  return Object.fromEntries(
    members.map((member, index) => [
      member,
      base + (BigInt(index) < remainder ? BigInt(1) : ZERO),
    ]),
  );
}

export function exactPreview(
  total: bigint,
  members: string[],
  values: Record<string, string>,
) {
  const shares: Record<string, bigint> = {};
  for (const member of members) {
    const share = parseMoney(values[member] ?? "0.00");
    if (share === null) return { shares, remaining: total, valid: false };
    shares[member] = share;
  }
  const remaining =
    total - Object.values(shares).reduce((sum, value) => sum + value, ZERO);
  return { shares, remaining, valid: members.length > 0 && remaining === ZERO };
}
