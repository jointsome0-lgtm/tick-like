# Lesson bridge parent runtime — adversarial security review

**Scope:** the Pending queue entry dated 2026-07-20 and the exact requested
range `b93cac4..7630977` (`e57d6bd`, `7630977`) on branch
`fix/36-d2-bridge-runtime`. The complete diff, all 17 touched paths, the full
TypeScript source and committed JavaScript emit, the preview metadata/file
service and route call paths, the Learn template/runtime, the ABI and bundle
contracts, the fixtures/verifier additions, and earlier reviews of the same
Learn/CSP/bundle surface were read. All `file:line` references below name the
tree at `7630977`.

The branch advanced independently to later commits while this review was in
progress. Those later commits are outside the caller-pinned diff and are not
part of this verdict.

**Context:** v0 has no authentication. Per `AGENTS.md`, the deployment decision
assumes a service bound directly to loopback. Lesson pages are untrusted content
inside an opaque-origin iframe. ABI v1 grants no write capability, but D2 freezes
the handshake/membrane that D4/D5 are intended to extend with state-changing
operations.

**Method:** diffed the exact range, treated committed tests and fixtures as
claims rather than evidence, and traced document navigation, asynchronous
metadata binding, `WindowProxy` identity, `MessagePort` transfer, revision
calculation, profile/sandbox transitions, symlink handling, and polling cost.
Static analysis was supplemented with an invented two-page browser probe on an
archived `7630977` tree and an invented mtime-preserving page-replacement probe.

**Summary verdict:** no Critical, High, or Medium finding under the current
ping-only, direct-loopback posture. Three Low findings remain. The most
important is a confirmed document-confusion race: a self-navigated successor
document can receive the expected page's welcome and port before its own
`load` event. Separately, the version token does not bind `page_rev` to the
bytes the iframe received, and every metadata poll hashes the entire page with
no page-size bound.

## Findings (severity-ranked)

### L1 — A successor document can receive the prior page's bridge grant before `load` (Low, confirmed)

The parent uses an iframe's stable `contentWindow` / `WindowProxy` as the source
identity. A valid `ready` is buffered as data only; it is not bound to a
completed document generation (`app/static/src/learn-bridge.ts:86-100`,
`300-318`). `bind()` awaits metadata and then immediately flushes that buffered
announcement (`app/static/src/learn-bridge.ts:150-168`). The generation changes
only when `load` fires (`app/static/src/learn-bridge.ts:171-197`). During a
self-navigation, however, the successor document can execute inline script
while one of its resources is still delaying `load`; throughout that interval
the generation is unchanged and `event.source === frame.contentWindow` remains
true because the `WindowProxy` survives navigation.

`handleReady()` does not retain or re-check the source of the buffered event.
It creates a channel and posts the welcome plus transferred port to whatever
document is current in `frame.contentWindow` at that later moment
(`app/static/src/learn-bridge.ts:263-297`). Consequently a `ready` sent by page
A can be answered into self-navigated page B with page A's identity. This
contradicts the ABI's claims that the parent posts only to the document it
navigated, that source checks identify the current document, and that a
self-navigation is never bound or granted (`docs/lesson-bridge-abi.md:26-38`,
`121-135`).

The exact-tree headless-Chrome probe used two invented declared pages. Page A
announced `ready` and navigated to page B; page B installed a message listener
but did not announce, and an invented same-origin image delayed B's `load`.
The metadata response was delayed into that interval. Before B's `load`, B
received a welcome carrying A's `page_id`, accepted the transferred port, and
received `pong`:

```text
displayed: related/second.html
granted page_id: <the index.html page id>
port reply: pong
```

ABI v1's empty capability set limits immediate impact to crossing the stated
document boundary and disclosing the parent-owned lesson/page/revision identity.
That keeps this Low for the reviewed direct-loopback build. It is nevertheless
a hard blocker for adding attempt or other write operations to this unchanged
handshake: the destination possessing the port is not necessarily the document
whose revision and page id were granted.

Do not grant from an in-flight or pre-`load` announcement. Establish a parent-
observed completed navigation before arming or flushing `ready`; if the module
missed the initial load, force one parent-owned reload after installing the
listener rather than treating a message as proof of document identity. Add a
browser case where A announces, B executes before its delayed `load`, and B
must receive neither welcome nor port.

### L2 — The reload token can stay constant while `page_rev` and served bytes change (Low, confirmed)

The metadata helper hashes a no-follow regular-file descriptor and takes its
stat after the read (`app/services/lessons.py:196-221`). That is a useful
single-metadata-read property. The value the client actually uses to decide
whether the loaded document matches that metadata is only
`st_mtime_ns:effective_profile`, while `page_rev` is the separate SHA-256
(`app/services/lessons.py:365-410`). The page response is also served through a
later `FileResponse` path open, not from the descriptor that metadata hashed
(`app/main.py:1215-1235`).

An agent or other same-user writer can replace the page bytes and restore the
old mtime. A focused invented probe did exactly that and obtained:

```text
version_equal: true
page_rev_equal: false
```

If the iframe received the old bytes and that replacement happens before the
binding metadata read, `bind()` sees the expected version and grants the new
hash to the old document. The inverse race is also possible around the
separate response open. The verifier covers only an ordinary write whose mtime
moves (`verify.py:987-999`), so it does not establish the contract's stronger
claim that `page_rev` hashes the bytes the parent loaded
(`docs/learn-bundle-spec.md:401-406`).

This is Low today because v1 cannot persist anything and exploiting it requires
runtime-file influence already inside the single-user boundary. It becomes an
attempt-attribution/data-integrity flaw as soon as D4 trusts the granted
`page_rev`. Bind navigation and metadata to one content-addressed file snapshot
(including the bytes actually served), not an independently re-opened path and
mutable mtime. Add an mtime-preserving replacement and a response/meta race to
the browser regression set.

### L3 — Every visible-page poll re-hashes an unbounded lesson file (Low, confirmed)

Every `preview-meta` request calls `lesson_file_info()`, which enables bridge
identity and streams the full page through SHA-256
(`app/services/lessons.py:196-221`, `365-419`). The client calls that endpoint
every 1.2 seconds while the document is visible, even when its version is
unchanged (`app/static/src/learn-bridge.ts:324-340`). Manifest size and item
counts are bounded, but lesson page bytes have no corresponding size bound.

Thus one large declared page authored in the private bundle turns an idle open
Learn tab into repeated full-file I/O and CPU work. This is a new amplification
path relative to the pre-D2 stat-only poll. It is Low under the current posture
because planting the file requires local/agent-side bundle influence, but a
large or sparse file can keep a worker busy and contend with the rest of the
unauthenticated app.

Bound the work: define a supported page-size limit or cache/reuse a digest from
a robust file identity, and avoid re-reading unchanged bytes on every poll.
The cache key must not repeat L2's mtime-only trust problem.

## Confirmed protections and regression checks

- **Eligibility fails closed.** Per-page identity is emitted only for a valid
  v2 interactive manifest, a declared page, a readable no-follow regular file,
  and a DB-owned lesson UID. Rejected, legacy, unknown-profile, symlinked, and
  missing-page paths carry no `bridge_page`.
- **Profile enforcement remains aligned.** The iframe attribute and response
  CSP use the same server-owned profile map. Interactive pages retain only
  `allow-scripts`; unknown chooser inputs default to that narrower set. The D1
  effective-profile component still changes the version on profile flips.
- **The basic membrane is narrow.** ABI v1 grants `capabilities: []`; only
  `ping` is implemented. Malformed/oversized messages, request-id bounds,
  protocol-error closure, ABI rejection limits, and one-grant state are present.
  The `event.source` check blocks sibling/foreign frames when no navigation is
  occurring; L1 is the narrower same-`WindowProxy` document transition.
- **Earlier bundle protections did not regress.** Manifest reads remain bounded
  and total; rejected manifests do not render; v2 file serving remains a
  declared-pages/`assets/` allowlist; reserved, artifact, and symlinked paths
  remain blocked; public finding details stay path-sanitized.
- **Network posture is unchanged.** No listener, trusted-Host/origin policy,
  unsafe-method guard, terminal, or authentication behavior changed. Wider
  exposure remains unsupported independently of these findings.

## Verification

- `git diff --check b93cac4..7630977` — passed.
- Exact-tree TypeScript compilation — passed; a fresh `tsc` emit from the
  archived `7630977` source was byte-identical to committed
  `app/static/learn-bridge.js`.
- Exact-tree headless-Chrome navigation-race probe — confirmed L1: the second
  document received the first page's identity and a functioning port before
  its delayed `load`.
- Invented mtime-preserving replacement probe — confirmed L2: identical
  `version`, different `page_rev`.
- Static call-path check — confirmed L3: a full SHA-256 read occurs on every
  eligible metadata request and the visible-page interval is 1.2 seconds.
- `PYTHONDONTWRITEBYTECODE=1 timeout 90s ... verify.py` on the archived exact
  tree passed the two terminal-wiring subprocess checks, then timed out at the
  previously documented TestClient startup boundary (exit 124), with no failing
  assertion observed. This review therefore does not independently claim the
  commit message's 531-check result.

## Final verdict

**Current ABI-v1 direct-loopback deployment: YES, with L1-L3 as Low follow-ups,
because the shipped port has no write capability. D4/D5 or any other
capability-bearing bridge extension: NO until L1 and L2 are resolved and
browser-tested against the exact loaded document. Wider deployment: NO — v0
remains unauthenticated.**

Per the caller's explicit file-scope constraint, this report does not move the
queue entry; it remains Pending and therefore continues to block a live
restart under `AGENTS.md`.

## ADDENDUM — fix commits `8cfcb9d`, `b74fd0e`, `4315bab`, `1565bd4`

**Scope:** re-review of the exact requested range `7630977..1565bd4`, with the
four named fix commits evaluated against L1–L3 and the resulting source checked
for regressions. References below name the tree at `1565bd4`.

### L1 — partially resolved; Low residual is acceptable only for current ABI v1

The exact buffered-announcement race demonstrated in the original report is
resolved. `4315bab` centralizes arming and refuses it during a parent-observed
pending navigation, and `1565bd4` removes `pendingReady` entirely: an
announcement received before arming is dropped and can be answered only when a
child retry arrives after arming (`app/static/src/learn-bridge.ts:157-185`,
`313-333`). `b74fd0e` also adds an inline load observer before the separately
fetched module, closing the ordinary missed-initial-load case
(`app/templates/learn.html:142-150`; `app/static/src/learn-bridge.ts:74-83`).

The finding is not fully resolved because the parent still has no
document-generation identity stronger than the iframe's navigation-stable
`WindowProxy`. The ABI now correctly records the pre-own-load and in-flight
delivery residuals (`docs/lesson-bridge-abi.md:134-160`), but one additional
startup interleaving introduced by the new observer remains: it counts every
load, while the runtime reduces every positive count to the same
`navPending = false` state (`app/static/src/learn-bridge.ts:82`). If the expected
page finishes loading and self-navigates again before the module initializes,
`data-loaded` is `2`; the already-settled successor is nevertheless treated as
the expected settled document and can be armed and granted.

A fresh invented headless-Chrome probe delayed `learn-bridge.js` until after
that two-load sequence. The observer reported `2`, the iframe was on the
successor document, and that successor received the expected page id plus a
working `pong`. This contradicts the ABI's unqualified statement that
post-load self-navigation is detected and re-asserted. Independently, a live
`ready`, `welcome`, or port message can still cross a navigation because its
source/destination remains the same `WindowProxy`; removing the buffer narrows
that window but cannot remove it.

These residuals are acceptable for the current direct-loopback ABI-v1 build:
the granted capability set is empty and the only operation is `ping`. They are
not acceptable as authority for D4/D5 writes. Before capabilities land, the
startup observer must fail closed or re-assert when it has observed more than
the one expected load, the navigation cases need browser regressions, and every
state-changing operation must re-validate lesson/page/revision and current
manifest authority server-side rather than trusting possession of the port.

### L2 — partially resolved; Low residual is acceptable only for current ABI v1

`1565bd4` resolves the mtime-preserving replacement demonstrated in the
original probe. Eligible bridge-page versions now include a digest prefix, the
initial Learn render takes the same identity-producing path as the metadata
poll, and digest plus closing stat come from one no-follow descriptor
(`app/services/lessons.py:211-243`, `393-406`, `419-434`, `562-566`). Thus a
replacement that restores `st_mtime_ns` still changes both `page_rev` and the
reload token.

The stronger L2 contract remains open: the token and `page_rev` still are not
bound to the bytes the iframe actually received. The normal page route first
resolves metadata through `bundle_resource_info()` and later gives the path to
`FileResponse`, which opens it independently (`app/main.py:1215-1235`); the
placeholder path similarly hashes in `lesson_file_info()` and then performs a
separate `Path.read_text()` (`app/services/lessons.py:1142-1148`). A replacement
between the hash and response open can therefore serve bytes different from
the granted full digest even though the new content-bound token makes the next
poll self-heal. This is acceptable for ping-only loopback operation, but not
proof that D4 records the revision the learner actually saw. D4/D5 still need a
single served-content snapshot (or an equivalently strong design) plus
record-time server validation and race tests.

### L3 — partially resolved; remaining availability risk is acceptable for direct loopback

`1565bd4` removes the steady-state amplification: an unchanged page reuses a
digest cached by device, inode, mtime, size, and ctime, and only a stable
before/after identity is cached (`app/services/lessons.py:196-243`). An idle
visible tab therefore no longer hashes the whole unchanged page every 1.2
seconds.

There is still no page-size bound. Every cold or invalidated cache miss hashes
the complete file, and local churn can invalidate the ctime/inode key on each
poll. A working set that reaches the 64-entry limit also clears the entire
cache rather than evicting one entry. The original always-rehash claim is fixed,
but the unbounded-work availability finding is only reduced, not eliminated.
That residual remains Low and acceptable for the current single-user,
direct-loopback posture; it should be closed with a supported page-size limit
and non-thrashing bounded cache policy before any wider exposure. It is not by
itself a D4/D5 integrity blocker, but capability work must not treat L3 as fully
closed.

### Regression check and verification

- **New Low regression R1:** the pre-module two-load case described under L1
  grants the successor document. It was reproduced in headless Chrome with a
  working v1 port and is not covered by the committed structural observer
  assertion.
- Manifest-only identity drift now tears down/reloads an armed document, and a
  transient load-time metadata failure can be recovered by a same-version poll
  (`app/static/src/learn-bridge.ts:337-360`). These changes did not widen the
  capability membrane, eligibility rules, sandbox/CSP selection, or bundle
  file allowlist.
- `git diff --check 7630977..1565bd4` passed. A fresh TypeScript emit was
  byte-identical to committed `app/static/learn-bridge.js`.
- The full `verify.py` run reached the same previously documented TestClient
  startup boundary and timed out after 150 seconds (exit 124), with no failing
  assertion emitted; this addendum therefore does not independently claim the
  commit message's 534-check result.

**Updated final verdict — (a) current ABI-v1 direct-loopback deployment: YES,
with L1–L3 only partially resolved and R1 remaining Low because the port is
ping-only; (b) D4/D5 capability extensions: NO on this exact handshake until
the L1/R1 document-confusion paths and L2 served-byte binding are resolved and
browser-tested, with per-operation server-side authority/revision validation
mandatory.**

## ADDENDUM — closing fixes `edf0f8b`, `4fdc572`, `927e8b1`, `9dd4111`

**Scope:** re-review of the exact requested range `1565bd4..9dd4111`, followed
by a closing check at merge head `0565f66`. The merge tree is byte-identical to
`9dd4111`. The three runtime changes, the docs-only residual update, the full
resulting parent runtime and ABI, and the earlier findings above were checked.
All `file:line` references in this addendum name the tree at `0565f66`.

**Result:** no new Critical, High, Medium, or Low finding in this range. R1 is
resolved. The previously reported L1 document-generation residuals, L2
served-byte race, and reduced L3 cold-hash availability residual remain Low
under the current ping-only, direct-loopback posture.

### R1 / `4fdc572` — resolved

The fix distinguishes the one legitimate pre-module load from the unsafe
multi-load state instead of reducing every positive count to the same settled
state. When the inline observer has counted more than one load, the runtime
sets `navPending`, consumes one re-assert slot, and assigns a cache-busted copy
of the parent-owned expected URL before any arming path can run
(`app/static/src/learn-bridge.ts:82-103`). `armFromMeta()` refuses to arm while
that navigation is pending, and the load handler clears the pending state only
when the forced expected document completes, then binds against that new
generation (`app/static/src/learn-bridge.ts:178-208`, `210-235`). The settled
successor from the pre-module two-load sequence can therefore no longer enter
the rescue or poll arming paths.

An invented delayed-module browser probe reproduced the earlier sequence. The
observer reached three loads (expected, successor, forced expected); the only
welcome went to the forced expected page with its expected page id. The
successor received neither welcome nor port. **`4fdc572` resolves R1.** It does
not and does not claim to solve the separate browser blind windows that remain
under L1.

### `edf0f8b` — budget exhaustion now fails closed

This fix closes the post-budget re-arm path. Every load first tears down the
port and identity; after the third forced return has been resisted, the next
self-navigation load sets `quarantined` instead of leaving an unarmed,
apparently settled frame for the poll to arm
(`app/static/src/learn-bridge.ts:210-232`). The single arming choke point checks
quarantine before navigation or identity state, while `navigate()` is the only
in-runtime path that clears the latch
(`app/static/src/learn-bridge.ts:145-159`, `178-197`). A focused
browser probe drove four expected-page grants followed by four settled
successors: the first three successors were forced back, the fourth remained
visible and received no grant, including across later polls.

The new behavior is deliberately sticky denial, not recovery: further child
loads and same-version polls leave the frame unbridged. In particular,
quarantine has already cleared `armed`, so the poll's identity-only reload
branch cannot fire; effective recovery is a fresh parent page/runtime or a
metadata version change that calls `navigate()`
(`app/static/src/learn-bridge.ts:112-119`, `371-400`). That availability cost
is fail-closed and is not a new security finding. A parent-owned navigation
also tears down first, marks its load pending, and only then clears quarantine,
so it does not reopen the outgoing-document grant gap
(`app/static/src/learn-bridge.ts:145-159`).

### `927e8b1` — concurrent rescue fan-out is fixed; retry semantics stay bounded by state

The late-initialisation rescue remains limited to the one state that needs it:
generation zero, a settled initial document, and no armed identity. The new
`rescueBinding` latch is set before `bind()` and cleared in `finally`, so ready
retries cannot create overlapping rescue fetches while the first is pending
(`app/static/src/learn-bridge.ts:339-367`). The triggering announcement is
still dropped rather than buffered; after a successful bind, a later live
child retry receives the grant, preserving the document-confusion fix at
`app/static/src/learn-bridge.ts:192-197`.

The latch is intentionally not a global request lock or rate limiter. The poll
has its own `inFlight` guard, so one rescue fetch and one poll fetch may coexist;
while a document remains unarmed, a continuously posting child can also start
another serialized rescue after the preceding one settles
(`app/static/src/learn-bridge.ts:358-363`, `371-400`). An invented fast-poster
probe with delayed metadata responses observed six serialized rescue requests
and a maximum rescue concurrency of one. This is a material reduction from
fan-out, uses only the fixed preview-metadata URL, and adds no authority; it is
not a security-severity finding under the current direct-loopback posture. A
future wider/authenticated deployment should share or cool down this work if
it needs a stronger untrusted-content request-rate guarantee.

### Remaining findings and `9dd4111`

- **L1 remains Low, with R1 removed from it.** The documented pre-own-load
  ambiguity, the now-explicit armed-window successor-ready case, and in-flight
  delivery all arise from the navigation-stable `WindowProxy`; the browser
  supplies no document-generation token. The new ABI text accurately states
  that a successor can post a live `ready` before its own load tears down the
  armed identity, and that a stalled load can retain the ping-only port
  (`docs/lesson-bridge-abi.md:137-175`). `9dd4111` changes documentation only;
  it neither fixes nor worsens that residual. Capability-bearing work must not
  treat port possession as authority and remains subject to the closing gate
  below.
- **L2 remains Low and unchanged.** Metadata binds digest and token to one
  descriptor, but the normal file response still resolves metadata and then
  lets `FileResponse` open the path separately; the placeholder path likewise
  hashes and later re-opens by path (`app/services/lessons.py:211-243`,
  `1142-1148`; `app/main.py:1215-1235`). No commit in this range binds the
  granted revision to the exact served bytes.
- **L3 remains Low and unchanged.** Stable files use the inode/ctime-aware
  digest cache, but a cold or invalidated entry still hashes the entire file,
  and reaching 64 entries clears the whole cache
  (`app/services/lessons.py:196-243`). The range adds no new hashing or polling
  path beyond the bounded rescue behavior assessed above.
- ABI v1 still grants `capabilities: []` and implements only ping/pong
  (`app/static/src/learn-bridge.ts:24-25`, `281-300`, `320-336`). None of the
  scoped commits changes the iframe sandbox/CSP owner, metadata eligibility,
  bundle allowlist, listener, authentication, or loopback deployment posture.

### Verification

- `git diff --check 1565bd4..9dd4111` — passed.
- `git diff --exit-code 9dd4111 0565f66` — passed; the merge tree is identical
  to the reviewed branch head.
- Fresh strict TypeScript compilation to a scratch directory — passed; the
  emitted `learn-bridge.js` was byte-identical to the committed served file.
- Invented headless-Chrome delayed-module probe — R1 resolved: only the forced
  expected document received a welcome and port after the two-load startup
  sequence.
- Invented headless-Chrome re-assert probe — terminal quarantine held after
  the fourth settled successor; no successor received a post-load grant.
- Invented headless-Chrome fast-ready probe — six rescue metadata requests
  completed serially with maximum rescue concurrency one.

**Closing verdict — merge head `0565f66`: (a) current ABI-v1 direct-loopback
deployment: YES, with L1–L3 as Low follow-ups; R1 is resolved and the closing
range introduces no new security-severity finding; (b) D4/D5 capability
extensions: NO on this exact handshake until the remaining L1 document-
confusion paths and L2 served-byte binding are resolved and browser-tested,
with per-operation server-side authority/revision validation mandatory; (c)
wider deployment: NO — v0 remains unauthenticated.**

Per the caller's explicit one-file constraint, this addendum does not move the
queue entry. It therefore remains Pending as an administrative restart gate
until that separate file is updated.
