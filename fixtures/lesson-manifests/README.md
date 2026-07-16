# Lesson manifest fixtures (Vera Example demo data)

Invented-from-scratch demo manifests for the Learn bundle contract
([`docs/learn-bundle-spec.md`](../../docs/learn-bundle-spec.md), frozen by
issue #39). No file here contains real lesson content, titles, or URLs; every
file carries the "Vera Example" marker that
`scripts/check_public_hygiene.py` requires of public fixtures.

- `cases.json` is the machine-readable expectation table. `expect` is the
  reader outcome (`ok` / `degraded` / `rejected`); `findings` lists finding
  codes that MUST appear (informational extras MAY appear on top).
- `v1-valid.json` → `v1-migrated.json` is the executable form of the
  migration mapping (spec §10): migrating the v1 fixture with its
  `lesson_uid` (`1b7e…1f04`) under the canonical serialization (spec §9.3)
  must reproduce `v1-migrated.json` byte-for-byte, deterministic page ids
  included.
- There is deliberately no `attempts.jsonl` fixture: `*.jsonl` is denied
  repo-wide by the hygiene policy (the real file is runtime data). The
  projection record format is specified with an inline example in spec §6.2.

Consumers: C3 (`verify.py` dual-read/normalization tests), C4 (migration
tool dry-run/idempotency/byte-equality tests).
