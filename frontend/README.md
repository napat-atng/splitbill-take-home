# Frontend

Next.js + TypeScript + Tailwind CSS. English interface with integer-satang allocation and Thai money formatting.

See the [root README](../README.md) for setup, environment variables, lint/typecheck/build and browser tests.

- `npm.cmd test`: unit tests of money parsing, allocation and formatting (Node.js 24+).
- From backend/: `uv run python -m scripts.test_frontend` runs desktop/mobile browser tests against a disposable PostgreSQL database and API.
- `npm.cmd run dev`: local UI at http://localhost:3000 after configuring .env.local.
- API must be running separately for normal development; tests start their own servers.