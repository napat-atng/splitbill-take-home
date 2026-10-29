import assert from "node:assert/strict";
import { test } from "node:test";
import {
  apiMoney,
  equalShares,
  exactPreview,
  formatMoney,
  fromApiMoney,
  parseMoney,
} from "../src/lib/money.ts";

test("100.00 splits exactly in request order", () => {
  const shares = equalShares(parseMoney("100.00")!, ["alice", "bob", "carol"]);
  assert.deepEqual(Object.values(shares).map(apiMoney), [
    "33.34",
    "33.33",
    "33.33",
  ]);
  assert.equal(
    Object.values(shares).reduce((a, b) => a + b, BigInt(0)),
    parseMoney("100.00"),
  );
  assert.deepEqual(
    Object.values(equalShares(BigInt(1), ["bob", "alice"])).map(apiMoney),
    ["0.01", "0.00"],
  );
});

test("decimal addition and Thai formatting avoid floating point", () => {
  assert.equal(apiMoney(parseMoney("0.1")! + parseMoney("0.2")!), "0.30");
  assert.equal(formatMoney("1000.00"), "1,000.00");
  assert.equal(formatMoney("-333.33"), "-333.33");
  assert.equal(
    formatMoney("99999999999999999.99"),
    "99,999,999,999,999,999.99",
  );
  assert.equal(fromApiMoney("-0.01"), BigInt(-1));
});

test("invalid monetary input is never rounded", () => {
  for (const value of [
    "",
    "10.005",
    "-1",
    "1e2",
    "NaN",
    "1,000",
    "10000000000.00",
    "0.",
  ]) {
    assert.equal(parseMoney(value), null, value);
  }
  assert.equal(apiMoney(parseMoney("9999999999.99")!), "9999999999.99");
  assert.equal(parseMoney("0.00"), BigInt(0));
});

test("exact shares track unallocated and overallocated money", () => {
  const total = parseMoney("100")!;
  assert.equal(
    exactPreview(total, ["alice", "bob"], { alice: "75", bob: "25" }).valid,
    true,
  );
  assert.equal(
    exactPreview(total, ["alice"], { alice: "99.99" }).remaining,
    BigInt(1),
  );
  assert.equal(
    exactPreview(total, ["alice"], { alice: "100.01" }).remaining,
    BigInt(-1),
  );
  assert.equal(
    exactPreview(total, ["alice"], { alice: "100.005" }).valid,
    false,
  );
  assert.equal(exactPreview(total, [], {}).valid, false);
});
