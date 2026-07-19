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
