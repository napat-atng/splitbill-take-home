# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Group members sharing costs on trips or lunches. Evaluators review correctness, usability and code quality for the take-home test.

## Product Purpose

Record a group expense, split it equally or exactly, and show each member's net balance accurate to the satang.

## Operating Context

A single-page web application on desktop and mobile. Users switch between seeded identities via X-User, choose their group, enter expenses and inspect balances. No full authentication is required.

## Capabilities and Constraints

Next.js, TypeScript and Tailwind frontend connected to the existing FastAPI API. English interface confirmed by the user. Thai money formatting (1,000.00), integer-satang preview, zero floating-point error, errors in plain language. Only payer may soft-delete expenses; expenses cannot be edited. Exact split submission disabled until shares sum to the total. No deployment requested.

## Brand Commitments

Product name: SplitBill. No existing logo or visual identity.

## Evidence on Hand

PLAN.md, CHECKLIST.md and README.md document the brief and implemented API. Users alice, bob, carol and dan; groups Chiang Mai trip and Office lunch. All expense data displayed must come from the API.

## Product Principles

- Correctness before visual polish.
- Show the allocation before saving.
- Clearly distinguish money owed to versus by each member.
- Preserve input and safe retry behavior when requests fail.
