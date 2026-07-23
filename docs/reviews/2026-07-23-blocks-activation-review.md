# Phase F blocks activation review

**Date:** 2026-07-23

## Self-parameterization

- **Scope:** the sole Pending entry in `docs/reviews/QUEUE.md`: commits after
  `1c04bd2` on `fix/35-f5-blocks-activation`, limited to the generated lesson
  brief's editor/run-block activation in `app/services/lessons.py`, its direct
  verifier anchors in `verify.py`, and the queue bookkeeping.
- **Starting HEAD:** `a29f95435d725acdc5d449eb4de3b18ea6a6470c` on a clean
  `fix/35-f5-blocks-activation` worktree.
- **Fix target:** the same PR branch. `git merge-base --is-ancestor HEAD main`
  returned false at the starting tree, while `1c04bd2` is its base; this is the
  required pre-merge template drain.
- **Report file:** `docs/reviews/2026-07-23-blocks-activation-review.md`.
- **Prior reports reconciled:** the generated pedagogy/template-E report, the
  lesson editor/run frontend report, the artifact-editor backend report, the
  runner-core and run-API reports, and the bridge runtime/conventions reports.
  Their closing conditions bind this activation: the brief writer and teaching
  boundary must not regress; the activated guidance must preserve independent
  capability degradation, authenticated port conventions, parent/server
  authority checks, artifact write ownership, text-only output, and the
  sandboxed runner contract; D5 L1 and D4 A1/A2 retain their stated
  dispositions.
- **Validation baseline:** `python verify.py` — **756 passed, 0 failed**;
  `python verify_restore.py` — **28 passed, 0 failed**.

## Context and method

The exact `1c04bd2..a29f954` history and the replaced template section were
read in full. The template writer and generated-workspace call path, the frozen
bundle block/profile/write-authority rules, the artifact/run endpoint contract,
the editor/run bridge ABI and parent capability negotiation, the lesson-agent
sandbox mounts, the F5 design memo, and the verifier anchors were reviewed as
direct context. Earlier PR-bot findings were treated as closed claims to
verify, not re-counted as this drain's findings.

The threat model is the documented direct-loopback, single-worker,
unauthenticated single-user deployment. Generated lesson pages remain untrusted
opaque-origin content and learner artifact bytes remain private runtime data.
No live service, private instance, runtime bundle, authenticated browser state,
or real learner data was read or changed.

## Starting-head verdict

No Critical, High, or Medium finding was found. Two Low instruction-contract
findings are confirmed. Both fail closed in the reviewed parent membrane and
backend, so they do not grant file or execution authority; they can instead
make generated editor/run pages unnecessarily inert or encourage guessed,
invalid protocol envelopes. The queue remains Pending until the guidance is
self-contained, independently capability-gated, and re-verified.

## Findings (severity-ranked)

### A1 — Partial capability grants can disable the working editor (Low, confirmed)

The starting text requests `attempts`, `editor`, and `run` together, then says
to keep the textarea and controls disabled unless the requested capabilities
are granted. The parent deliberately negotiates those capabilities
independently: an editor endpoint plus a declared block can grant `editor`
while `run` is absent because the backend is old, the runner is unhealthy, or
the selected runner is absent/incompatible. The bundle and ABI contracts
explicitly retain the save-only editor in those states.

Reading the starting sentence as an all-requested-capabilities gate therefore
turns a valid editor grant into an inert textarea whenever Run degrades. This
regresses the reviewed graceful-degradation matrix and can block learner saves,
but it cannot bypass the parent or backend authority checks; severity is Low.
The brief must gate textarea/Load/Save on `editor` and Run/Cancel on `run`
separately, with an editor-only page requesting no unused Run authority.

### A2 — The activated operations are not implementable from the mounted brief (Low, confirmed)

The starting section names `artifact.get`, `artifact.save`,
`artifact.save_run`, and `run.cancel`, but supplies none of their request
envelopes or the minimum revision/run state rules. Its relative references to
`docs/lesson-bridge-abi.md` and `docs/lesson-artifacts-api.md` are useful source
citations but not locally readable contracts in the lesson shell: the same
brief says the app repository is a different project that may not exist in the
session, and the lesson-agent sandbox exposes the writable bundle under a
blanked home rather than the Ephemeris checkout.

An agent following only its generated workspace instructions must therefore
guess fields such as `v`, `block_id`, `content`, `base_rev`, `after`, and
`run_id`, or avoid the feature. Guessed envelopes fail closed in the parent,
so this is bounded functional loss rather than an authority escalation; a
page that guesses response state can nevertheless ship dead controls. Severity
is Low. The active section must repeat the minimum frozen request shapes and
state transitions while keeping the full documents authoritative.

## Confirmed protections at the starting head

- The replacement remains one `_AGENTS_TEMPLATE` hunk. Every other generated
  brief section and the mode-0600 atomic writer path are unchanged; no lesson,
  title, URL, attempt, or artifact content is interpolated into the constant.
- The first PR-bot round's fixes correctly keep learner-owned artifacts
  read-only to the agent, place starter code in page state, require an
  unrejected v2 manifest with `interactive-local-v1`, and use one ready message
  that requests editor/run for a runner-backed page.
- Stable block/page identity, manifest-derived file paths, the two fixed runner
  ids and suffixes, single-file dependency-free execution, and the ban on
  manifest commands remain accurate. No schema, registry, route, sandbox, CSP,
  static, terminal, or listener code changes.
- The general bridge section still authenticates the exact parent/origin and
  envelope, consumes one handshake result, treats identity as parent-owned,
  mints lesson-wide request ids, and degrades to a useful read-only page.
- Private artifact reads still require parent-owned per-document consent.
  Editor/run writes and starts retain fresh parent and server validation;
  execution uses the reviewed immutable sandbox snapshot, and output is data,
  never authority.

## Starting-head verification

- `git diff --check` — passed.
- `python -m py_compile app/services/lessons.py verify.py` — passed.
- `python verify.py` — **756 passed, 0 failed**.
- `python verify_restore.py` — **28 passed, 0 failed**.
- `python scripts/check_public_hygiene.py` — passed; ignored-status inspection
  showed only established local tool, environment, cache, screenshot-reference,
  and review-work paths.

## CLOSING ADDENDUM — fix commit `d2f97f4` (cycle 1 of 10)

The exact-head review of `a29f954..d2f97f4` confirmed A1 and A2, then found
one additional Low instruction-contract issue in the new minimum response
guidance. The commit changes only the active editor/run-block guidance and its
verifier anchors; no runtime, endpoint, schema, ABI document, static, sandbox,
CSP, terminal, or listener path changed.

### A1 — resolved

The brief now makes capability gates explicit and independent. An `editor`
grant alone makes the textarea writable and enables Load/Save; `run` alone
enables Run/Cancel, and its absence cannot revoke an already granted editor.
An editor-only page asks for `editor`, adds `attempts` only when it also records
declared questions, and omits `run`. The save-only editor therefore survives
old-backend, runner-health, unknown-runner, and incompatible-runner degradation
as the bundle and ABI contracts require.

### A2 — resolved

The active section now repeats the four exact minimum v1 request envelopes,
labels every ellipsis as a placeholder rather than a literal id/value, and
states the required `base_rev` progression, request/run ownership matching,
monotonic output sequence handling, retry cursor, and text-only rendering.
The canonical ABI and endpoint docs remain named as authorities, while an agent
whose sandbox contains only the bundle no longer has to invent the protocol.
Parent/backend validation remains unchanged and fail closed.

### A3 — Asynchronous run errors leave generated controls active (Low, confirmed)

The cycle-1 guidance lists `run.output` and `run.exit` as the asynchronous
owned-run messages to accept, but omits the ABI's `run.error`. The parent emits
that terminal error when an SSE relay is malformed, oversized, or closes
prematurely. A generated page following the list literally can leave its Run
UI stuck active and fail to show the bounded relay failure. The error remains
scoped to a parent-owned `run_id` and grants no new authority, so severity is
Low. Handle `run.error` under the same owned-run check and clear active state
on either exit or error.

## SECOND CLOSING ADDENDUM — fix commit `c148e6b` (cycle 2 of 10)

Fresh review of the exact `d2f97f4..c148e6b` diff found no new Critical,
High, Medium, Low, Info, or other finding. The change remains confined to the
active generated guidance and its verifier anchors.

### A3 — resolved

The brief now accepts `run.error` only under the same page-owned `run_id` check
as output and exit, and explicitly treats either `run.exit` or `run.error` as
terminal for the active UI state. Sequence progression remains limited to the
output/exit messages that carry a cursor. A malformed, oversized, or prematurely
closed relay therefore becomes visible text and releases the local Run controls
without inventing output, a terminal cause, or cross-run ownership.

## Prior-condition reconciliation at the closing tree

- **Generated brief writer and teaching/data-boundary protections — REMAIN
  RESOLVED.** The constant writer, atomic publication, symlink/special-file
  replacement, immutable manifest identity, unknown-field preservation,
  untrusted-data boundary, learner-artifact ownership, and no-symlink rules are
  unchanged. The activated guidance reinforces rather than weakens text-only
  treatment of artifact and run data.
- **F4 generated-pedagogy activation condition — RESOLVED.** The prior
  frontend report left the shipped brief intentionally inactive pending this
  separate F5 slice. The reviewed text now activates only the already-landed
  manifest/editor/run contract, with exact capability and envelope guidance;
  no other pedagogy section changes.
- **Bridge-conventions B1/B2/N1 — REMAIN RESOLVED.** Exact parent/origin and
  envelope authentication, one-result consumption, fresh lesson-wide request
  ids, and correct reject handling remain in the unchanged general section.
  The new operation examples use only that authenticated port and explicitly
  reject literal placeholder ids.
- **Bridge-runtime D5 L1 — REMAINS MITIGATED; D5 L2/L3 — REMAIN RESOLVED.**
  The same-`WindowProxy` document-generation residual remains documented.
  Content-bound serving, fresh parent/server operation checks, private-read
  consent, and bounded identity/cache rules are unchanged.
- **Artifact A1 and the artifact write boundary — REMAIN RESOLVED.** The brief
  preserves app-owned save authority and agent read-only ownership. Descriptor
  stability, no-follow traversal, bounded UTF-8 reads/writes, conflict checks,
  and rate/event behavior are unchanged. The same-user final-publication window
  remains **OPEN/ACCEPTED by design** and is not widened.
- **Runner-core, run-API, and F4 frontend findings — REMAIN RESOLVED.** Fixed
  registry templates, immutable snapshots, namespace/private-root isolation,
  resource bounds, health single-flight, admission/retention, SSE replay,
  owned cancellation, private-read consent, and text-only relay are unchanged.
  The earlier runner/client activation conditions are now **RESOLVED for the
  generated brief**.
- **Lesson-role, terminal, and deployment protections — REMAIN RESOLVED at
  their prior dispositions.** Agent/learner/runner sandboxes and private masks
  are unchanged. Terminal-opt-in remains resolved for lesson roles and
  **OPEN/ACCEPTED** only for the deliberately plain owner shell. The
  direct/no-forwarded-header condition remains **MITIGATED** by the documented
  direct-loopback deployment.
- **D4 A1/A2 — REMAIN OPEN/ACCEPTED Low availability follow-ups.** This text
  slice changes neither attempt buffering nor projection reconciliation and
  does not claim to resolve them.

## Closing verification

- Both fix cycles' `git diff --check` and
  `python -m py_compile app/services/lessons.py verify.py` — passed.
- Cycle-1 and cycle-2 `python verify.py` — **756 passed, 0 failed** each,
  including the independent-grant, minimum-envelope, revision, run-ownership,
  relay-error, terminal-state, and text-only guidance anchors.
- Cycle-1 and cycle-2 `python verify_restore.py` — **28 passed, 0 failed** each.
- PR #72's exact application head `c148e6b` had both CI checks green and
  received the review bot's clean `+1` at 2026-07-23 00:26:04 UTC before this
  report and Done bookkeeping were committed.
- `python scripts/check_public_hygiene.py` — passed. Ignored-status inspection
  showed only established local tool, environment, cache, screenshot-reference,
  and review-work paths.

## Closing verdict

**SAFE TO MAKE LIVE for the documented direct-loopback `127.0.0.1:8765`,
single-worker, unauthenticated single-user deployment.** The review found
**3 Low, 0 Critical, 0 High, 0 Medium, and 0 Info** findings; all were resolved
in **2 of 10** cycles, and no open finding remains for this queue entry. The
activated generated guidance is self-contained at its mounted boundary,
preserves independent editor/run degradation, learner artifact ownership,
authenticated bridge operations, fixed runner authority, and text-only data
handling. Wider, proxy-adjacent, or multi-user deployment remains **NO**. The
queue entry may move to Done. A live restart remains owner-only and was not
performed.
