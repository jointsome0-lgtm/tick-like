# Runner core — adversarial security review

**Scope:** exactly one Pending entry was present at review start: the 2026-07-22
entry for commits after `e3cb882` on `fix/36-f1-runner-core`, covering
`app/runner.py`, `app/sandbox.py`, `app/services/runner_registry.py`,
`app/services/bundle_schema.py`, `app/services/lessons.py`, `fixtures/runner/`,
`scripts/probe_runner.py`, `scripts/probe_sandbox_profiles.py`, `verify.py`,
`docs/learn-bundle-spec.md`, and `docs/reviews/QUEUE.md`, plus their direct
callers. The exact scoped branch range is `e3cb882..f6715f5`: `33abe08`,
`7ac224b`, `71716d0`, `c093283`, and `f6715f5`. Phase F slice F3 adds the
fixed single-file runner registry, immutable fd-backed snapshot sandbox
profile, bounded asynchronous job owner, cached health probes, admission and
retention state, and invented isolation/execution fixtures; no HTTP route or
live spawn integration is added.

**Starting HEAD:** `76e521d3b76b8db00bc3641bda0c5fe63fc41970` on
`main`. `git status --short --branch` showed only `## main...origin/main`, with
no tracked or untracked worktree change. The starting worktree was clean.

**Fix target:** the reviewed branch head
`f6715f59b1ac3ece5048ee09663c103c83a8a5d8` is reachable from
`origin/main` through ordinary merge commit
`76e521d3b76b8db00bc3641bda0c5fe63fc41970`. After `git fetch origin --prune`,
local `main` fast-forwarded to that exact merge commit and matched
`origin/main`; `git merge-base --is-ancestor f6715f5 main` succeeds. The entry
is therefore merged, so repo tradition and the owner brief put every drain fix
and the final report/queue commit directly on `main`.

**Report file:** `docs/reviews/2026-07-22-runner-core-review.md`, derived from
the entry's “runner core” subject.

**Prior reports to reconcile:** every existing
`docs/reviews/*-review.md` closing verdict was scanned. The binding reports for
the sandbox, runner, bundle, and lesson surfaces are:

- `2026-07-21-sandbox-launcher-review.md`: E1 S1 is resolved; the explicit
  app-owned bundle authority, strict descendant rule, no-unsandboxed-fallback
  behavior, and three-profile namespace/mount contract must remain intact. Its
  strict runner limits were explicitly deferred to F3.
- `2026-07-21-lesson-agent-sandbox-review.md` and
  `2026-07-21-lesson-learner-sandbox-review.md`: the two live lesson roles'
  server-owned selection and sandbox isolation are resolved, while runner
  integration remained later scope. The agent's host-network/credential
  posture is intentionally accepted only for the trusted agent role; the
  learner remains no-network and separated from the private instance.
- `2026-07-22-terminal-surfaces-review.md` and
  `2026-07-22-pedagogy-template-e-review.md`: the two-surface client and
  generated pedagogy protections are resolved, while runner support remained
  still open/out of scope. The editor/run feature remains fenced unless an
  admitted runner surface exists.
- `2026-07-17-bundle-schema-runtime-review.md`: bounded/total manifest parsing,
  no-symlink containment, v2 resource allowlisting, identity/profile
  fail-closed behavior, and sanitized findings are resolved and must not
  regress in the new runner-selector read.
- `2026-07-21-check-activation-review.md`, superseding the earlier bridge and
  attempt deployment gates: D5 L1 remains mitigated, D5 L2/L3 are resolved,
  and D4 A1/A2 remain accepted Low availability follow-ups. The runner must not
  expose or weaken those lesson HTTP/data paths.
- Terminal-opt-in T1 remains resolved for the sandboxed `lesson-agent` and
  `lesson-learner` roles and still open/accepted for the deliberately plain
  owner shell. Terminal F1-F4, terminal-tab L1, workspace refusal,
  relative-path display, atomic brief publication, and the direct/no-forwarded-
  header deployment mitigation retain their prior dispositions unless this
  entry changes a direct caller.

The closing verdict below must state whether each named condition is resolved,
mitigated, still open/accepted, or unchanged for the code under review.

**Validation baseline:** at the clean starting HEAD, approved host runs of the
exact required commands passed: `python verify.py` — **669 passed, 0 failed**;
`python verify_restore.py` — **28 passed, 0 failed**. Initial restricted-
sandbox runs emitted no assertion result and were interrupted at the
repository's known TestClient/bubblewrap execution-environment stall; only the
complete host counts are used as baselines for every fix cycle.

## Context and method

The deployment decision assumes an unauthenticated, single-user, single-worker
app bound directly to `127.0.0.1:8765`. No service was restarted or signalled,
and no live database, lesson bundle, export, browser profile, screenshot, or
authenticated state was read or written.

The complete scoped diff, fixed runner registry, manifest read, sandbox argv
and spawn path, job owner, health probes, fixtures, contract text, and direct
callers were reviewed adversarially. The real probes used only invented files
under throwaway `/tmp` directories. Queue prose, prior review claims, and test
assertions were treated as claims to verify, not as authority. The landed merge
tree and reviewed branch-head tree are byte-identical (`3d1bcbf`).

## Findings (severity-ranked)

### M1 — A symlinked Go module-cache path can disclose an unintended host directory (Medium, confirmed)

At the starting head, `_probe_go_module_cache()` accepted the configured
`GOMODCACHE` after only `Path.is_dir()`, and the runner sandbox then passed the
same pathname to bubblewrap's ordinary `--ro-bind`. Both operations follow
symlinks. Unlike the bundle/private authorities, this read-only host authority
had no lexical or descriptor-bound identity check. The agent profile also
provides a writable home, so a normal local Go layout may legitimately contain
administrator- or user-managed links above the final `pkg/mod` component.

A throwaway host proof replaced the configured cache path with a symlink to an
invented private directory. A runner-shaped bubblewrap command then read the
invented secret through the nominal module-cache mount. No live instance or
real private path was involved. Read-only mounting prevents modification but
does not prevent disclosure, and the eventual runner would return program
output to the lesson client. The issue is Medium despite the absent HTTP route:
it is a reusable isolation primitive whose purpose is to make untrusted code
safe before that route exists.

Open the cache without following any path component, keep that descriptor
through the spawn boundary, mount it with bubblewrap's `--ro-bind-fd`, and make
the health probe exercise the same descriptor-backed operation.

### M2 — Rejected and legacy manifests can still advertise Run authority (Medium, confirmed)

At the starting head, `_read_blocks()` set `run_enabled` from registry
membership and suffix compatibility before `_read_v2()` resolved the runtime
profile and overall outcome. Nothing revoked the flag after a missing identity
rejected the manifest or an unknown/missing profile forced
`legacy-display`. Direct reads of invented manifests produced
`rejected legacy-display True` for a missing identity and
`degraded legacy-display True` for an unknown profile.

That contradicts `docs/learn-bundle-spec.md` section 5: legacy and unknown
profiles grant no editor/run authority, and fail-closed means no Run
affordance. There is no current HTTP or client consumer, so this did not expose
a live execution path at the starting head. It is still Medium because the
manifest read model is the intended authority boundary for the later adapter;
a caller that reasonably trusts `run_enabled` would activate rejected content.

After profile/outcome aggregation, force every block to save-only unless the
manifest is accepted under `interactive-local-v1`, and pin both the rejected
and legacy cases in the verifier.

### L1 — Snapshot admission retains and duplicates unbounded bytes (Low, confirmed)

`RunnerRequest.snapshot` had no byte ceiling at admission. The job owner keeps
the request in every active and retained terminal job (up to eight retained
jobs), while `_snapshot_memfd()` copied the entire value into a second
memory-backed file before applying the existing child `RLIMIT_FSIZE`. The
runner's 32 MiB output/file limit therefore constrained the child only after an
unbounded application-side allocation and copy had already succeeded.

There is no live request route in F3, so only a future direct caller could
supply those bytes; that keeps the finding Low for the current deployment.
The primitive nevertheless promises bounded admission and retention. Enforce
the existing `RUNNER_FILE_BYTES` ceiling both before reserving a job and at the
memfd boundary, with regression coverage for each layer.

No Critical, High, or Info finding.

## Confirmed protections and rebutted candidates at starting HEAD

- The registry contains only fixed app-owned argv templates with one file
  placeholder and fixed suffixes. Manifest values cannot supply a command,
  argument, environment variable, shell fragment, or host path.
- Runner snapshots are immutable bytes injected as a sealed mode-0444 memfd.
  Bundle content is mounted read-only; scratch, home, and runtime filesystems
  are bounded tmpfs mounts; the private instance, checkout, and explicit
  private masks are hidden before the bundle is rebound. The runner has no
  network namespace, receives an allowlisted environment, and executes inside
  a transient user scope with CPU, memory, process, file, and wall limits.
- Admission serializes replay, health, rate, per-lesson capacity, global
  capacity, and reservation. Failure and cancellation converge on one terminal
  transition, rate reservations are refunded on pre-start failure, retained
  jobs are bounded, and shutdown stops admission before killing active scopes.
- A detached-descendant escape was tested with an invented runner program that
  created a separate-session child with detached standard streams and then
  exited normally. The parent job reached `FINISHED` and released capacity;
  `systemctl --user show` reported the transient scope inactive and the child
  did not survive. The namespace/scope lifecycle therefore rebutted this
  candidate; no change was warranted.
- The F3 service has no app route, lifespan owner, WebSocket, template, or
  static-client caller. Only the verification/probe scripts instantiate it;
  `lessons.py` supplies the fixed registry to manifest reads. Thus none of the
  findings was reachable from the running v0 service at the starting head.
- Agent and learner sandbox argv remained byte-identical under the F3 changes.
  Their server-owned role selection, network split, private masking, and
  terminal fd lifecycle were not widened.

## Initial verification and deploy verdict

- `git diff --check e3cb882..f6715f5` — passed.
- Starting-head `python verify.py` — **669 passed, 0 failed**.
- Starting-head `python verify_restore.py` — **28 passed, 0 failed**.
- The real three-profile sandbox probe and full runner matrix passed, apart
  from the separately demonstrated module-cache authority substitution.

**Not yet for runner integration.** The current live application remains safe
for its documented loopback posture because F3 is not wired into it, but M1
weakens the runner's host-read boundary, M2 exposes an authority flag on
fail-closed manifests, and L1 leaves snapshot ownership unbounded. The entry
must stay Pending until those findings are closed and the exact fixed tree is
re-verified. Wider, proxy-adjacent, multi-user, or live-runner deployment is NO
independently.

## CLOSING ADDENDUM — fix commit `68045f6` (cycle 1 of 10)

### M2 — resolved

After parsing the runtime profile and identity, `_read_v2()` now clears
`run_enabled` on every block when the manifest is rejected or its effective
profile is not `interactive-local-v1`
(`app/services/bundle_schema.py:517-522`). The editor metadata remains visible,
but rejected, missing-profile, unknown-profile, and identity-mismatch reads no
longer claim execution authority. `verify.py:4533-4573` pins a compatible
interactive block as enabled and legacy/rejected blocks as disabled.

### L1 — resolved

`RunnerService.admit()` rejects a snapshot above the existing 32 MiB runner
file ceiling before health, rate, capacity, job, or idempotency state is
reserved (`app/runner.py:326-348`). `_snapshot_memfd()` independently applies
the same bound before creating or writing a descriptor
(`app/sandbox.py:516-523`). Tests cover the low-level boundary and admission's
no-side-effect refusal. The job owner now has a finite snapshot-memory bound
consistent with its finite active and retained job counts.

### M1 — mitigated but still open after fresh review

Cycle 1 replaced the raw-path cache mount with a descriptor opened using
`O_NOFOLLOW`, passed that fd across `systemd-run`, and mounted it with native
`--ro-bind-fd`. The cached health check now proves the actual fd-backed bwrap
operation rather than merely testing `is_dir()`. The original final-component
substitution is closed and the opened directory cannot change beneath the
spawn.

Fresh review found that `O_NOFOLLOW` protected only the final `mod` component:
the kernel could still traverse a symlink in an earlier component such as
`go/pkg`. Because that parent can be within a writable user tree, M1 was not
closed. The queue correctly remained Pending and a second cycle was required.

Cycle 1 host validation:

- `python scripts/probe_sandbox_profiles.py --skip-agent-api` — all three
  profiles passed.
- `python scripts/probe_runner.py` — fixed Python/JavaScript/Go matrix and all
  runner isolation/limit assertions passed.
- `python verify.py` — **672 passed, 0 failed**.
- `python verify_restore.py` — **28 passed, 0 failed**.
- `python scripts/check_public_hygiene.py` — passed; the status/ignored-file
  inspection found no public-data boundary violation.

## SECOND CLOSING ADDENDUM — fix commit `3347293` (cycle 2 of 10)

### M1 — resolved

`open_runner_module_cache_fd()` now starts at an fd for `/` and walks every
absolute path component with dir-relative `open`, `O_DIRECTORY`, and
`O_NOFOLLOW`, closing each parent as it advances
(`app/sandbox.py:559-577`). The final verified directory descriptor—not the
pathname—is inherited and mounted read-only by fd
(`app/sandbox.py:616-656`; `app/runner.py:162-181`). A concurrent pathname
replacement cannot retarget that descriptor, and a link in either the final
component or any ancestor is refused. `verify.py:4661-4701` covers both cases
and the snapshot ceiling.

Fresh review of `68045f6..3347293` found no new Critical, High, Medium, Low,
Info, or other finding. Cycle 2 host validation preserved the grown baseline:

- `python scripts/probe_sandbox_profiles.py --skip-agent-api` — all three
  profiles passed.
- `python verify.py` — **672 passed, 0 failed**, including the full real runner
  probe.
- `python verify_restore.py` — **28 passed, 0 failed**.
- `python scripts/check_public_hygiene.py` — passed; the status/ignored-file
  inspection found no public-data boundary violation.

## Prior-condition reconciliation at closing tree

- **E1 S1 and the sandbox-launcher contract — REMAIN RESOLVED.** Bundle
  authority is still explicit, a strict descendant is required, failure never
  falls back to unsandboxed execution, and the agent/learner profiles remain
  unchanged. The strict F3 runner-limit condition previously deferred by that
  report is now **RESOLVED for the runner-core primitive**: snapshot, scratch,
  home, CPU, memory, process, output, wall, capacity, and retention bounds are
  enforced and probed.
- **Lesson-agent and lesson-learner isolation — REMAIN RESOLVED.** Role
  selection and mounts are unchanged. The trusted agent's host-network and
  credential posture remains **OPEN/ACCEPTED by design**; the learner remains
  no-network and separated from the private instance. Runner integration that
  those reports left for later is **RESOLVED only at the F3 core layer** and
  **STILL OPEN** for route, client, and application-lifecycle wiring.
- **E4 two-surface client and pedagogy protections — REMAIN RESOLVED.** No
  template or static client changed. The inactive editor/run fence remains in
  force because no live runner surface exists; the corrected read model makes
  legacy and rejected bundles fail closed before later integration.
- **Bundle-schema runtime protections — REMAIN RESOLVED.** Bounded/total
  parsing, the whole-bundle no-symlink rule, v2 allowlisting, immutable
  identity, sanitized findings, and profile fail-closed behavior remain
  intact. M2 closes the one new runner-affordance inconsistency.
- **D5 L1 — MITIGATED; D5 L2/L3 — RESOLVED; D4 A1/A2 — STILL
  OPEN/ACCEPTED.** F3 adds no attempt, page, bridge, database, or projection
  caller and does not weaken those controls. These residuals still bar wider
  unauthenticated deployment.
- **Terminal-opt-in T1 — RESOLVED for `lesson-agent` and `lesson-learner`,
  STILL OPEN/ACCEPTED for the deliberately plain owner shell.** Terminal
  F1-F4, terminal-tab L1, fail-closed workspace refusal, relative-path display,
  and atomic brief publication **REMAIN RESOLVED**. The
  direct/no-forwarded-header launch condition remains **MITIGATED by the
  documented direct-loopback deployment**, not removed from the broader threat
  model. No terminal fd, PTY, WebSocket, route, or listener code changed.

## Closing verification and verdict

The required baseline was **669 passed, 0 failed** and **28 passed, 0 failed**.
Both fix commits preserve or grow it: cycle 1 and cycle 2 each passed
`python verify.py` at **672 passed, 0 failed** and `python verify_restore.py`
at **28 passed, 0 failed**. The final documentation-only head is verified
again before push; its exact counts are recorded in the queue entry and remain
the deployment gate. Public hygiene passes, and no live service or data was
touched.

**SAFE TO MAKE LIVE for the documented direct-loopback
`127.0.0.1:8765`, single-worker, unauthenticated single-user application.**
The review found **2 Medium, 1 Low, 0 Critical, 0 High, and 0 Info** findings;
all are resolved in **2 of 10** cycles, and no open review finding remains.
The F3 runner core is safe as a not-yet-wired primitive. Live runner route,
client, and lifecycle integration remain later scope and are not approved by
this verdict; wider, proxy-adjacent, multi-user, or live-runner deployment is
**NO**. The queue entry may move to Done. Any live restart remains owner-only
and was not performed.
