# Lesson editor/run frontend — adversarial security review

## Derived parameters

- **Scope:** the one Pending entry in `docs/reviews/QUEUE.md`: commits after
  `fd9f54a` on `fix/36-f4-editor-run-frontend`, covering the TypeScript lesson
  bridge source and emitted JavaScript, bridge ABI, editor/run conventions
  fixture, verifier coverage, and queue entry.
- **Starting HEAD:** `9d7eaa444f8799416d13072f272b4763044e2d56` on a clean
  `fix/36-f4-editor-run-frontend` worktree.
- **Fix target:** the PR branch. `9d7eaa4` is not reachable from `main`, while
  base `fd9f54a` is its ancestor; this is the required pre-merge static drain.
- **Report file:**
  `docs/reviews/2026-07-23-lesson-editor-run-frontend-review.md`.
- **Prior reports reconciled:** the bridge-runtime and bridge-conventions
  reports, the artifact-editor backend report, the runner-core and run-API
  reports, and the pedagogy/template-E report. Their closing conditions bind
  this client activation: per-operation authority and served-byte binding must
  remain effective; B1/B2 client conventions, artifact A1, runner/run-API
  findings, sandbox/lesson-role isolation, and the generated-pedagogy boundary
  must not regress; D5 L1 and D4 A1/A2 retain their stated dispositions.
- **Validation baseline:** `python verify.py` — **751 passed, 0 failed**;
  `python verify_restore.py` — **28 passed, 0 failed**.

## Context and method

The exact `fd9f54a..9d7eaa4` history was reviewed as two membranes in its
required commit order: editor first, then composite save/run, SSE relay, and
cancel. The complete TypeScript source, emitted JavaScript relationship, ABI,
fixture, and new verifier section were read together with their direct callers:
preview metadata/template endpoint discovery, artifact GET/save, run
start/SSE/cancel, the runner coordinator, and the current generated lesson
brief. Earlier bot findings were treated as already closed threads; their
resulting code was assessed fresh rather than counted again.

The threat model is the documented direct-loopback, single-worker,
unauthenticated single-user deployment. Lesson HTML remains untrusted
opaque-origin content. Invented examples only were used; no live service,
private instance, runtime data, or authenticated browser state was touched.

## Starting-head verdict

No Critical, High, or Medium finding was found in the parent editor/run
membranes. Two Low convention-fixture findings are confirmed. The fixture is
not shipped by the Learn template, but the ABI names it as the executable child
example and later generated pages are expected to copy these conventions. The
queue therefore remains Pending until both are closed and the exact fixed tree
is re-verified.

## Findings (severity-ranked)

### C1 — The executable child example does not authenticate or consume one handshake result (Low, confirmed)

`fixtures/lesson-bridge/editor-run-conventions.html` checks only
`event.source === window.parent` and the lesson-bridge marker. It does not
require the exact served-page origin, selected ABI 1, or exactly one
transferred port. It sets `answered` but never refuses later messages, so a
second parent-shaped `welcome` can replace the port and upgrade capabilities.
It also treats an arbitrary marker-bearing parent message as terminal before
validating the envelope.

This regresses the bridge-conventions report's closed B1 receiving contract.
A copy served outside the app's `frame-ancestors` response policy can be
embedded by a foreign parent, accept a forged editor/run welcome and port, and
send learner-entered source to that port on Save or Run. The repository fixture
is test-only, so current production exposure is indirect, and the normal app
parent is trusted; severity is Low. The example must compare
`event.origin` with the exact non-opaque URL origin, validate welcome/reject by
their own frozen envelopes, require exactly one port for welcome, and consume
only the first valid terminal result. The direct opaque-origin case must fail
closed and remain read-only.

### C2 — Deterministic per-load request ids collide across reloads and tabs (Low, confirmed)

The fixture mints ids as `fixture-<kind>-<counter>`, with the counter reset to
zero on every document load. Two tabs following the same actions therefore use
the same Run id for the same block/content. After reload, a new logical Run can
also reuse the previous document's id. Because the parent intentionally maps
the logical tuple to the server idempotency key, those distinct actions can
replay and attach to the same retained job rather than start independently;
one example page may then display or cancel the other's run.

This regresses the closed B2 lesson-wide uniqueness rule and the run ABI's
distinction between a new logical operation and an exact retry. Under the
single-user posture the impact is wrong-run output/cancellation and bounded
availability; the runner still exposes no private root or network and enforces
its normal capacity limits. Severity is Low. Each loaded document must create
an unpredictable nonce with browser randomness and combine it with its
monotonic counter; only `runRequestId` retained for the same content/cursor
retry may be reused. If randomness is unavailable, the example should stay
read-only rather than use a predictable fallback.

## Confirmed protections at the starting head

- Editor and Run grants are fresh-metadata routing hints only. Every selected
  block is revalidated against page identity/version before relevant HTTP;
  saves/cancels retain the navigation-settle gate, and start authority is
  checked again after the returned job before ownership or output is exposed.
- Private artifact bytes are not fetched until a parent-owned, sticky,
  per-document confirmation explicitly warns about the accepted same-frame
  navigation egress. Denial performs no artifact GET, and a post-prompt fresh
  block check prevents stale authorization.
- Composite save/run preserves conflict-before-start ordering. The
  domain-tagged SHA-256 key binds request id, block, and exact content without
  a secure-context-only API; standard vectors and the committed emit are
  verified. The deviation from a verbatim key is explicit in the ABI.
- One active relay is enforced before mutation. SSE parsing drains complete
  coalesced frames, bounds the one retained partial frame, validates sequence,
  event kind, stream, UTF-8 output size, and terminal causes, and relays output
  only as structured data. Ownership gates relay and cancel; navigation aborts
  the relay and drops client authority without cancelling the bounded server
  job.
- The parent changes no CSP, iframe sandbox token, listener binding, backend
  route, terminal surface, or attempt semantics. Old backends omit endpoint
  attributes and therefore grant neither new capability. No bridge/no grant,
  direct-open, and old-backend states remain readable and non-mutating.

## Starting-head verification

- `git diff --check fd9f54a..9d7eaa4` — passed.
- `python verify.py` — **751 passed, 0 failed**.
- `python verify_restore.py` — **28 passed, 0 failed**.
- `npm run build` — passed; the emitted `app/static/learn-bridge.js` SHA-256
  remained `46df6a08c38cf1db6eebb9c3a055d379683df1a4b8eec1067b0bc6a88038af1d`.
- `python scripts/check_public_hygiene.py` — passed; ignored-status inspection
  found only established local tool, environment, cache, and review-work paths.

## CLOSING ADDENDUM — fix commit `9e3956b` (cycle 1 of 10)

Fresh review of the exact `9d7eaa4..9e3956b` diff found no new Critical,
High, Medium, Low, Info, or other finding. The fix changes only the child
conventions fixture, the ABI rules it exemplifies, and verifier anchors; it
does not change the parent runtime, emitted static, endpoint, sandbox, CSP,
runner, or live deployment surface.

### C1 — resolved

The example now ignores every message after its first valid terminal result
and requires the sender to be both `window.parent` and the exact origin derived
from the served page URL. A welcome must select ABI 1, carry a string-only
capability array, and transfer exactly one port. A reject is checked against
its own `abi-unsupported`/`supported` envelope and must transfer no port. Noise
does not stop the retry timer, and an opaque URL origin skips the handshake and
stays read-only. The ABI now states the same complete receiving boundary.

This restores the bridge-conventions B1 result: a foreign embedder, malformed
message, later claimed upgrade, or wrong-ABI welcome cannot acquire the
example's learner-entered source through an attacker-selected port.

### C2 — resolved

Each loaded example document now obtains 128 random bits with
`crypto.getRandomValues()` and combines that nonce with the action kind and a
monotonic counter. New actions therefore do not collide across reloads or
tabs. The existing `runRequestId` is still deliberately retained only while
retrying the same content/job cursor. If browser randomness is unavailable,
the example fails closed to read-only rather than selecting a predictable
fallback. The ABI now makes fresh lesson-wide ids and exact-retry reuse a
common port-protocol rule.

This restores the bridge-conventions B2 result and keeps the composite run
idempotency deviation narrow: equal logical retries reattach, while independent
runs do not share output or cancellation authority merely because two
documents followed the same UI sequence.

## Prior-condition reconciliation at the closing tree

- **Bridge-conventions B1/B2 and reject-envelope N1 — REMAIN RESOLVED.** The
  generated lesson brief already carries the exact source/origin/envelope,
  one-result, and fresh lesson-wide id rules; the executable editor/run example
  now follows them too.
- **Bridge-runtime D5 L1 — REMAINS MITIGATED; D5 L2/L3 — REMAIN RESOLVED.**
  The navigation-stable `WindowProxy` residual remains documented rather than
  claimed eliminated. Editor/run mutations add the required settle and fresh
  parent/server authority checks; private reads additionally require explicit
  parent consent. Versioned page serving, bounded identity, and digest-cache
  protections are unchanged.
- **Artifact A1 and the artifact write boundary — REMAIN RESOLVED.** Reads are
  still descriptor-stable and bounded; saves retain no-follow, compare-and-
  publish, rate, and event rules. The same-user final-publication window stays
  **OPEN/ACCEPTED by design** and is not widened by the client.
- **Runner-core and run-API findings — REMAIN RESOLVED.** Snapshot isolation,
  fd authority, health single-flight, reader leases, retained-job bounds,
  event-loop responsiveness, SSE replay, and cancellation semantics are
  unchanged. F4 activates only their reviewed routes through a block-specific
  parent membrane.
- **Generated pedagogy and lesson-role isolation — REMAIN RESOLVED.** The
  shipped lesson brief still says editor/run blocks are inactive until the
  separate F5 text slice; this fixture remains test-only and is not loaded by
  the Learn template. Agent/learner/runner sandbox roles and private masks are
  unchanged.
- **D4 A1/A2 — REMAIN OPEN/ACCEPTED Low availability follow-ups.** F4 changes
  neither attempt request buffering nor projection reconciliation. Terminal
  protections remain resolved; the deliberately plain owner-shell condition
  remains **OPEN/ACCEPTED** only for that role.

## Closing verification

- Fix-cycle `git diff --check` and `npm run build` — passed; the emitted lesson
  bridge static remained unchanged and reproducible.
- Fix-cycle `python verify.py` — **754 passed, 0 failed**, including the new
  authenticated-handshake, one-result, random-id, and ABI-contract checks.
- Fix-cycle `python verify_restore.py` — **28 passed, 0 failed**.
- `python scripts/check_public_hygiene.py` — passed. Ignored-status inspection
  showed only established local tool, dependency, cache, screenshot-reference,
  and review-work paths.

## Closing verdict

**SAFE TO MAKE LIVE for the documented direct-loopback `127.0.0.1:8765`,
single-worker, unauthenticated single-user deployment.** The review found
**2 Low, 0 Critical, 0 High, 0 Medium, and 0 Info** findings; both were resolved
in **1 of 10** cycles, and no open finding remains for this queue entry. The
editor/run parent membrane, private-read consent, graceful degradation,
composite save/start ordering, owned relay/cancel boundary, and text-only child
conventions are approved. Wider, proxy-adjacent, or multi-user deployment
remains **NO**. The queue entry may move to Done. A live restart remains
owner-only and was not performed.
