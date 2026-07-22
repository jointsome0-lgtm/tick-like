# Lesson artifact and run endpoints (phase F)

Status: the editor half is frozen with phase F1. The run sections are reserved
for the phase-F4 slice. This is the HTTP contract used by the parent Learn
runtime; the lesson document itself has no network access. Manifest authority
is [learn-bundle-spec.md §4.4](learn-bundle-spec.md), and the child-facing
membrane is [lesson-bridge-abi.md](lesson-bridge-abi.md).

The documented deployment is direct loopback, single user, single worker, and
has no auth. Unsafe methods remain behind the central B2 origin guard. A bridge
port is routing, never authority: every request re-reads the manifest and
derives the file path from its declared `block_id`; no client request contains
a path.

## Artifact routes

```
GET  /learn/lessons/{lesson_id}/blocks/{block_id}/file
POST /learn/lessons/{lesson_id}/blocks/{block_id}/file
GET  /learn/lessons/by-slug/{slug}/blocks/{block_id}/file
POST /learn/lessons/by-slug/{slug}/blocks/{block_id}/file
```

The by-slug forms are aliases with identical behavior. Every route uses the
pure bundle reader: it never creates a bundle, manifest skeleton, standard
directory, artifact root, or legacy copy. Existing preview reads keep their
historical behavior and are a separate surface.

### GET response

An existing strict-UTF-8 file (HTTP 200):

```json
{"ok": true, "exists": true, "content": "print('hi')\n",
 "file_rev": "sha256:…64 lowercase hex…", "size": 12}
```

A missing file is also 200:

```json
{"ok": true, "exists": false, "content": "", "size": 0}
```

`file_rev` hashes the exact raw bytes read from one no-follow descriptor. Raw
content is capped at 64 KiB. The same descriptor must identify a regular file
with one link; invalid UTF-8 is refused rather than replacement-decoded.

### Save request and response

POST is `application/json`, admitted from the request stream with a 512 KiB
cap:

```json
{"content": "print('hi')\n", "base_rev": "absent"}
```

For an existing file, `base_rev` is the `file_rev` returned by GET. A first
write uses the literal `"absent"`. There is no ETag or If-Match variant.

Success (HTTP 200):

```json
{"ok": true, "result": "saved", "file_rev": "sha256:…",
 "size": 12, "event_recorded": true}
```

`result` is `saved` or `unchanged`. Content-equal retries are `unchanged`
without a filesystem write, ledger event, or rate charge. Other saves compare
and publish under a per-bundle lock. Conflict exclusion is strict among
artifact-API writers. Direct terminal writers are detected when their change
is visible during compare or the final descriptor-identity check, but a
same-user direct write in the final publication window remains last-write-wins;
strict mediation of every bundle write is outside v1.

Publication walks or creates parents relative to a no-follow descriptor for
the lesson root, writes and fsyncs a mode-0600 temporary file in the pinned
destination directory, re-checks the current descriptor identity, replaces
fd-relatively, and fsyncs the directory. A block file deeper than four levels
below its declared artifact root is not writable through this API.

Each real save attempts one best-effort `lesson_artifact_saved` event after
the file is durable. Its payload is `lesson_uid`, `lesson_id`, `slug`,
`block_id`, manifest-relative `file`, `file_rev`, `size`, and boolean
`created`; it never contains file content. A crash or DB failure after file
publication can lose telemetry, and an identical retry remains `unchanged`,
so `event_recorded` makes that limitation observable. This path never writes
`attempts.jsonl`.

The in-process single-worker abuse damper permits 30 save attempts per lesson
per 60 seconds. Validation/conflict outcomes are charged because they consume
the manifest/filesystem path; `unchanged` and `rate-limited` are uncharged.

## Refusal matrix

Every refusal is:

```json
{"ok": false, "error": "<code>", "detail": "…"}
```

`file-conflict` additionally carries the current `file_rev` (JSON `null` when
the file is absent). A 429 carries `Retry-After`.

| status | error | condition |
|--------|-------|-----------|
| 400 | `invalid-block-id` | route id does not match `blk_[a-z0-9]{4,32}` |
| 400 | `invalid-base-rev` | neither `absent` nor `sha256:` plus 64 lowercase hex |
| 400 | `invalid-content` | `content` is not a UTF-8-encodable JSON string |
| 400 | `invalid-json`, `invalid-request` | malformed/non-object JSON or bad Content-Length |
| 404 | `unknown-lesson` | no lesson with that id or slug |
| 409 | `manifest-rejected` | the pure record-time manifest read is rejected or missing |
| 409 | `identity-mismatch` | manifest `lesson_uid` differs from DB authority |
| 409 | `blocks-unavailable` | manifest/profile grants no interactive editor affordance |
| 409 | `unsafe-file` | a descriptor is not a single-link regular file, or a parent/root is unsafe |
| 409 | `file-conflict` | `base_rev` differs or the descriptor identity changes before publish |
| 413 | `payload-too-large` | request stream exceeds 512 KiB |
| 413 | `file-too-large` | stored or submitted raw file exceeds 64 KiB |
| 415 | `unsupported-media-type` | save is not `application/json` |
| 422 | `unknown-block` | block did not survive the record-time manifest read |
| 422 | `invalid-encoding` | stored bytes are not strict UTF-8 |
| 422 | `undiscoverable-path` | save target is outside/deeper than the artifact discovery contract |
| 429 | `rate-limited` | more than 30 save attempts in the lesson's 60-second window |

The phase-F4 slice extends this document with `unknown-runner`,
`incompatible-runner`, `runner-unavailable`, `busy`,
`idempotency-conflict`, `job-missing`, and the run/status/SSE/cancel routes.
