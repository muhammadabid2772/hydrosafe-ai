# Integration Checklist

## Before anyone codes

- Freeze sensor field names and units.
- Freeze the unified payload and authentication responses.
- Confirm one owner for every folder.
- Confirm the lead alone merges `main`.

## Member 6 handoff

- Run the frontend in mock mode.
- Test landing, login, signup and protected dashboard navigation.
- Switch among NORMAL, WATCH, WARNING and CRITICAL demo states.
- Confirm the risk gauge, alert message, evidence factors and next action change together.
- Set `VITE_USE_MOCK_API=false` only when lead endpoints are available.
- Never place passwords, tokens or backend secrets in a `VITE_` variable.

## Lead integration

- Return a complete unified payload from `/api/analysis/latest`.
- Add CORS for the exact frontend origin during development.
- Replace demo authentication with server-side password hashing and real sessions or tokens.
- Verify unauthorized dashboard access returns the user to login.
- Run the deterministic progression NORMAL → WATCH → WARNING → CRITICAL.

## Definition of done

- Production build succeeds.
- Mobile layout has no horizontal overflow.
- Forms provide keyboard focus and readable errors.
- Risk state never depends on a frontend calculation.
- Empty, loading and API failure states are visible and recoverable.
- Critical alert includes a human-verification safety note.

