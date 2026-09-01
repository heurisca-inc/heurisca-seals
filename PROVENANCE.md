# Provenance notes

This file records anything about the record that a reader should know but could
not infer from the roots alone. It is append-only in spirit: entries are added,
never edited away.

## 2026-09-01 — first root, produced during bring-up

The root published for 2026-09-01 was produced while the sealing machinery was
being brought up. Its 13 leaves were predictions in the development database,
not substantive forecasts about real pending decisions, and they were written
before the definition of "sealed content" was consolidated into a single
function. They are therefore **not revealable** under the current definition.

It is left in place rather than removed for two reasons. Removing it would mean
rewriting this branch's history, which the record's whole value depends on not
happening. And a gap in the chain would be less honest than an explained entry.

The chain is intact: 2026-09-02's `prev_root` points at it.

**The record of substantive predictions begins after this entry.** Any reveal
packet offered as evidence will reference a root dated 2026-09-02 or later.

## Content definition

From 2026-09-02 onward, the content hashed into each leaf fingerprint is exactly:

```json
{"question_id": "...", "distribution": {...}, "reasoning": "..." }
```

serialised with sorted keys and no incidental whitespace, then hashed together
with that prediction's 32-byte random salt. `verify.py` implements this and
nothing else.

## 2026-09-01 — development database reset

The development database was dropped and rebuilt on 2026-09-01, by operator
decision. It had accumulated bring-up artifacts, test fixtures, and the first
real predictions in one place, and its seal dates had begun colliding with real
ones.

**This repository was not touched.** No commit was rewritten, no root was
removed, and the 2026-09-01 root above still stands exactly as published. That
was a condition of the reset: the seal record's history is the proof layer, and
it is never rewritten — not to tidy up, and not to correct a mistake.

What the reset means in practice: the salts for the 2026-09-01 root are gone, so
those leaves were already non-revealable and now permanently are. Nothing else
changes. No prediction that was ever offered as evidence is affected, because
none had been.

Alongside the reset, the environments were permanently separated: development
and CI now run on throwaway databases, and the real ledger lives where test code
cannot reach it — a production connection is refused outright whenever a test
process is running. The separation is the actual fix; the reset was only the
cleanup.
