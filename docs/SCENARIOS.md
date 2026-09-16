# Required scenarios

## 1. Greenfield
Input: "Build a URL shortener with core APIs, analytics and reliability."
- Normalize: create, resolve, analytics, health, expiry.
- Decompose: API -> persistence -> redirect -> analytics -> tests/security -> docs -> release.
- Orchestrate: architecture first; implementation then parallel tests/security; synchronize; human release gate.
- Validate: API tests, alias collision, expiry, dependency gates.

## 2. Brownfield
Input: "Analytics endpoint is slow and click counts are inconsistent."
- Inspect impacted modules: redirect transaction + analytics query + click persistence.
- Plan: reproduce -> add regression tests -> make click update atomic -> add index -> benchmark -> approval.
- Re-plan trigger: if benchmark shows DB contention, introduce queue/event aggregation instead of increasing API-side work.

## 3. Ambiguous
Input: "Make short links permanent and highly scalable."
- Ambiguities: permanent means no expiry or immutable destination? Scale target? retention? abuse controls? consistency?
- Agent must stop at requirements gate and request/record assumptions before implementation.
- Safe default: no irreversible schema migration until human approval; define explicit SLO and retention policy.
