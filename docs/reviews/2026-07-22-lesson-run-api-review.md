# Lesson run API — adversarial security review

**Scope:** exactly one Pending entry was present at review start: the 2026-07-22
entry for commits after `f2487ee` on `fix/36-f3-run-api`, covering
`app/main.py`, `app/runner.py`, `app/security.py`,
`app/services/artifacts.py`, `app/services/runs.py`,
`app/templates/learn.html`, `docs/lesson-artifacts-api.md`, `verify.py`, and
`docs/reviews/QUEUE.md`, plus their direct callers. The scoped implementation
commits are `f7f6289`, `1f83866`, `78560cd`, and `c660ba4`; ordinary merge
commit `b40a099` landed their reviewed tree on `main`.

**Starting HEAD:** `b40a099547217bc7c5b1f55523be9be952904839` on
`main`. `git status --short --branch` showed only `## main...origin/main`, with
no tracked or untracked worktree change. The starting worktree was clean.

**Fix target:** reviewed branch head
`c660ba4a2ea93b25791f98be74687cc63209077e` is reachable from `main` through
ordinary merge commit `b40a099547217bc7c5b1f55523be9be952904839`.
The merge and reviewed-head trees are byte-identical (`81977f2`). The entry is
therefore merged, so repo tradition and the drain brief put every fix directly
on `main`.

**Report file:** `docs/reviews/2026-07-22-lesson-run-api-review.md`, derived
from the entry's lesson-run-API subject.

**Prior reports to reconcile:** every existing
`docs/reviews/*-review.md` closing verdict was scanned. The binding conditions
for this surface are:

- `2026-07-22-runner-core-review.md`: runner-core M1/M2/L1, the E1 sandbox
  contract, strict runner limits, fail-closed registry/profile selection, and
  lesson-agent/learner isolation were resolved. Route, client, and application
  lifecycle integration remained explicitly open and is the principal gate
  this drain must resolve.
- `2026-07-22-lesson-artifact-editor-backend-review.md`: artifact A1, bounded
  descriptor reads, manifest-derived paths, strict UTF-8, and the B2 write
  perimeter were resolved. The same-user final publication window remains an
  intentional last-write-wins calibration.
- `2026-07-22-terminal-surfaces-review.md` and
  `2026-07-22-pedagogy-template-e-review.md`: the two lesson terminal surfaces
  and generated pedagogy protections were resolved while runner activation
  remained later scope. Terminal-opt-in T1 remains accepted only for the
  deliberately plain owner shell.
- `2026-07-21-check-activation-review.md`: D5 L1 remains mitigated, D5 L2/L3
  are resolved, and the earlier attempt-backend A1/A2 availability findings
  remain accepted Low follow-ups. This run API must not widen the iframe,
  attempt, projection, or page-identity authority paths.
- Bundle-schema parsing/identity/profile protections, the no-unsandboxed-
  fallback rule, terminal F1-F4, terminal-tab L1, workspace refusal, and the
  direct/no-forwarded-header deployment mitigation retain their prior
  dispositions unless this integration changes a direct caller.

The closing verdict below must state whether each condition is resolved,
mitigated, still open/accepted, or unchanged for the closing tree.

**Validation baseline:** approved host runs at the clean starting HEAD passed:
`python verify.py` — **716 passed, 0 failed**; `python verify_restore.py` —
**28 passed, 0 failed**. The verifier used only its automatically created
throwaway instance and the repository's invented runner fixtures.

## Context and method

The deployment decision assumes an unauthenticated, single-user, single-worker
app bound directly to `127.0.0.1:8765`. No service was restarted or signalled,
and no live database, lesson bundle, export, browser profile, screenshot, or
authenticated state was read or written.

The full landed diff and all listed files were read, including the manifest and
artifact readers, runner registry, sandbox spawn path, request-body admission,
security middleware, event writer, application lifespan, SSE response
lifecycle, and verifier coverage. Fresh deterministic probes used fabricated
jobs and invented paths only. Queue prose, earlier reports, verifier assertions,
and the PR bot's clean verdict were treated as claims to verify, not as review
evidence.

## Findings (severity-ranked)

### L1 — A disconnect before SSE body iteration can leak its reader reservation (Low, confirmed)

`stream_lesson_run()` reserves a reader before constructing and returning the
`StreamingResponse`, but releases it only in the async generator's `finally`.
Starlette 0.37 drives response sending and disconnect listening as sibling
tasks. If disconnect cancellation wins while `http.response.start` is still
pending, body iteration never begins, so the generator's `finally` never runs.

An invented ASGI probe blocked only the response-start `send`, delivered an
immediate `http.disconnect`, and let the response finish normally. The job's
`reader_count` remained one. Repeating the sequence consumes both per-job
reader slots, makes the stream permanently `busy`, and also protects a terminal
job from eviction. This is Low in the supported direct-loopback single-user
posture, but it is a deterministic unauthenticated availability primitive on
any wider listener.

Bind cleanup to the response lifecycle as well as generator completion, and
make each attachment a distinct idempotently releasable lease so the two cleanup
paths cannot decrement another reader's reservation.

### L2 — Attached readers can bypass the terminal-job and retained-memory bounds (Low, confirmed)

`_prune_locked()` excludes every terminal job with `reader_count > 0` and
reduces the remaining retention slots by that count. There is no cap on the
number of distinct reader-protected jobs. A deterministic service probe with
`max_terminal_jobs=1` inserted four otherwise ordinary protected terminal jobs;
pruning retained all four. The same state is reachable through sequential run
and slow-reader lifecycles because active capacity is released before the SSE
reader detaches.

Each protected job retains its snapshot, event list, output text, and replay
identity. The count can therefore exceed both the frozen maximum of eight
terminal jobs and the `(8 retained + 2 active) × 1 MiB` output-memory argument.
L1 makes protection leakable, but L2 exists independently for legitimately slow
connected readers. It remains Low under the loopback single-user posture and
would become a direct memory-exhaustion primitive on a wider listener.

Cap the number of distinct jobs carrying reader leases at the terminal
retention bound. A second reader for an already protected job may still attach;
the first reader for a ninth distinct job must receive the existing `busy`
refusal. This preserves promised streams without allowing them to invalidate
the global retention bound.

### L3 — The process-lifetime health cache is not single-flight under concurrent starts (Low, confirmed)

The run integration moved health probes to `asyncio.to_thread()`, correctly
keeping them off the ASGI loop and service lock. The cached function still uses
`functools.cache`, whose dictionary is coherent across threads but whose miss
calculation is not single-flight. Starts for different lessons can all pass
preflight before any job reservation exists and enter the cold cached function
concurrently.

An eight-thread invented probe synchronized the first cache miss and observed
eight complete probe entries, all returning healthy. Each entry can run the
bubblewrap, transient-scope, executable, and module-cache subprocess checks.
The worker-pool ceiling limits instantaneous threads but not the redundant
queued work, contradicting the one-probe-per-process contract and amplifying a
cold-start request burst. This is Low for the supported loopback deployment.

Serialize the cache lookup and miss calculation with one process-local lock
while retaining the existing process-lifetime result and test reset hook.
Callers still wait on worker threads, so status, stream, and cancel remain
responsive on the event loop.

No Critical, High, Medium, or Info finding was found.

## Confirmed protections at the starting tree

- Start routes remain behind the central trusted-Host and unsafe-method origin
  middleware. The SSE route rejects browser cross-origin requests before a
  reader reservation; origin-less non-browser clients remain an explicit
  direct-loopback allowance.
- Lesson, block, file, and runner authority are re-derived from the database and
  one pure record-time manifest read. Rejected, identity-mismatched,
  non-interactive, undeclared, unknown-runner, and suffix-incompatible states
  fail closed. No client path or command reaches the runner.
- One no-follow, single-link, size-capped descriptor supplies both the revision
  hash and exact execution bytes. The prior mid-read identity fix remains in
  force, and no verify-to-execute path reopen was introduced.
- The fixed runner registry, immutable fd snapshot, no-network sandbox,
  descriptor-bound Go cache, private masks, aggregate systemd scope, rlimits,
  output ceiling, first-cause-wins state machine, reap-plus-EOF finish rule,
  and exactly-once capacity release remain intact. There is still no
  unsandboxed fallback.
- Replay/conflict, per-lesson/global capacity, health refusal, and rate refunds
  converge under the runner service. Status and stream GETs do not modify the
  bundle or ledger. Terminal telemetry is best-effort, body-free, and attempted
  exactly once.
- The landed merge tree is byte-identical to the final reviewed PR head. No
  terminal PTY/WebSocket code, static bridge runtime, iframe CSP, attempt row,
  or projection path changed in this entry.

## Initial verification and deploy verdict

- `git diff --check f2487ee..b40a099` — passed.
- Starting-head `python verify.py` — **716 passed, 0 failed**.
- Starting-head `python verify_restore.py` — **28 passed, 0 failed**.
- The deterministic retained-job, concurrent-health, and ASGI-disconnect probes
  confirmed L1-L3 without using live state.

**NOT YET SAFE TO MAKE LIVE with runner integration.** The existing application
remains unchanged until the owner restarts it, but L1-L3 leave stream and cold-
health resource ownership weaker than the frozen bounded-runner contract. The
queue entry must stay Pending until all three findings are fixed and the exact
closing tree is re-verified. Wider, proxy-adjacent, or multi-user deployment is
**NO** independently.

## CLOSING ADDENDUM — fix commit `f7e9aef` (cycle 1 of 10)

### L1 — resolved

Every `attach_reader()` now returns a distinct `ReaderLease`. Release is
idempotent under the service lock, so generator cleanup and response cleanup
cannot decrement another connection's slot. `_ReaderStreamingResponse` wraps
the complete ASGI response call in `finally`; it releases the lease even when
disconnect cancellation or a send failure happens before body iteration. The
generator retains its own cleanup for ordinary completion. The exact blocked-
response-start disconnect reproduction now leaves `reader_count == 0`.

### L2 — resolved

The first reader for a previously unprotected job is admitted only while fewer
than `max_terminal_jobs` distinct jobs already hold reader leases. A second
reader for the same job remains allowed up to the frozen per-job limit. At the
production values, no more than eight jobs can therefore become eviction-
protected; when an active protected job finishes, pruning evicts eligible old
terminal jobs until the total terminal count is at most eight. Active unprotected
jobs remain separately bounded at two, restoring the frozen retained-output
argument. Regression coverage uses a one-job retention limit, proves a second
distinct job is refused, and proves double release of one lease leaves the
other lease intact.

### L3 — resolved

The actual cached health calculation remains a no-argument process-lifetime
`functools.cache`, but every lookup and cache miss now runs behind one
process-local `threading.Lock`. Concurrent callers cannot enter the uncached
probe more than once. The existing cache reset hook also takes that lock, so
tests cannot clear a calculation in flight. Four synchronized cold callers in
the verifier now observe one probe entry and one shared healthy result while
the route continues to await it on worker threads outside the event loop and
service lock.

Fresh review of `f7e9aef` found no new Critical, High, Medium, Low, Info, or
other finding. The response wrapper changes cleanup only; admission, event
ordering, SSE cursor behavior, and two-reader semantics are unchanged. The
distinct-job reader cap uses the existing `busy` refusal and does not evict a
promised stream. The health lock encloses only the process-lifetime cache
lookup/probe and never the runner service or ASGI loop.

Cycle 1 host validation:

- `python verify.py` — **719 passed, 0 failed**, including the new concurrent-
  health, distinct-job lease, idempotent-release, and pre-body-disconnect
  regressions plus the full real runner sandbox matrix.
- `python verify_restore.py` — **28 passed, 0 failed**.
- `git diff --check` — passed.
- `python scripts/check_public_hygiene.py` — passed.
- `git status --short --ignored` — inspected; only the intended report/queue
  closeout remained uncommitted, alongside established ignored local tool and
  dependency paths.

## Prior-condition reconciliation at closing tree

- **Runner-core M1/M2/L1, E1 isolation, strict runner limits, and the no-
  fallback rule — REMAIN RESOLVED.** The route and application-lifecycle
  integration that report left open are now **RESOLVED for the server-side run
  API**. Static bridge/client integration remains later F4/F5 scope and is not
  claimed by this verdict.
- **Artifact A1, manifest-derived addressing, bounded descriptor reads, strict
  UTF-8, and B2 write protection — REMAIN RESOLVED.** Run consumes the exact
  verified bytes without a second path read. The same-user final artifact-
  publication window remains **OPEN/ACCEPTED by design** and is not widened.
- **Two-surface terminal and generated-pedagogy protections — REMAIN
  RESOLVED.** The server-side runner activation condition is resolved here;
  the existing static lesson client remains fenced and unchanged until its own
  reviewed slice. Terminal-opt-in T1 remains **OPEN/ACCEPTED only for the
  deliberately plain owner shell**.
- **Bundle-schema parsing, identity/profile fail-closed behavior, v2
  allowlisting, and sanitized findings — REMAIN RESOLVED.** Rejected, legacy,
  unknown-runner, and incompatible blocks still receive no execution authority.
- **D5 L1 — REMAINS MITIGATED; D5 L2/L3 — REMAIN RESOLVED; attempt-backend
  A1/A2 — REMAIN OPEN/ACCEPTED Low follow-ups.** The run API adds no iframe
  authority, attempt/projection write, or page-serving path and does not alter
  those dispositions.
- **Terminal F1-F4, terminal-tab L1, workspace refusal, relative-path display,
  and atomic brief publication — REMAIN RESOLVED.** The direct/no-forwarded-
  header condition remains **MITIGATED by the documented direct-loopback
  deployment**. No terminal PTY, WebSocket, static client, or listener binding
  changed.

## Closing verification and verdict

The required baseline was **716 passed, 0 failed** and **28 passed, 0 failed**.
Fix commit `f7e9aef` grows and preserves it at **719 passed, 0 failed** and
**28 passed, 0 failed**. Public hygiene passes; no live service or private
runtime data was touched.

**SAFE TO MAKE LIVE for the documented direct-loopback `127.0.0.1:8765`,
single-worker, unauthenticated single-user deployment.** The review found
**3 Low, 0 Critical, 0 High, 0 Medium, and 0 Info** findings; all are resolved
in **1 of 10** cycles, and no open review finding remains for this queue entry.
The server-side lesson run API and application lifecycle are approved; static
bridge/client activation remains later scope. Wider, proxy-adjacent, or
multi-user deployment is **NO**. The queue entry may move to Done. A live
restart remains owner-only and was not performed.
