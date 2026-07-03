# Guide: reviewing a draft capture

A model wrote something into `captures/`. Before it becomes part of the
knowledge base, you review it. This is the single manual step the whole
capture system depends on — `hcd` is safe *because* this review stands
between a model and the substrate. Skipping it defeats the design.

## Why drafts exist

`hcd` drafts a capture from session notes using the local model. Models
paraphrase, compress, and occasionally invent — a hallucinated capture is
worse than no capture, because future decisions cite the substrate as fact.
So model output lands as `YYYY-MM-DD-topic.md.draft`, not `.md`. Drafts are
inert: the render site excludes them, nothing consumes them, and the
pre-commit hook blocks a `.md` capture that still looks like an unreviewed
draft. The `.draft` suffix is the safety boundary.

## Lifecycle

```
session → hcd → <date>-<topic>.md.draft → [YOU REVIEW] → rename to .md → commit
                                              │
                                              └── or delete it (rejecting is fine)
```

## The review checklist

Read the draft against the session it summarises. Check, in order:

1. **Invented headers.** The top line fields — Date, Session tier(s),
   **Audit** — must reflect what actually happened. Models fill these with
   plausible guesses; a drafter once wrote `Audit: PASS` for a session that
   was never audited. If it wasn't audited, the value is `n-a`.
2. **Findings match reality.** Every bullet should map to something that
   actually occurred. Delete anything the model embellished or assumed.
3. **Dead ends preserved.** The most valuable and most often-dropped
   content. If the session hit a wrong turn, the draft must record it —
   re-add it if the model tidied it away.
4. **No real secrets, and `[REDACTED]` handled.** `hcd` redacts credentials
   it recognises, but confirm. Anything sensitive that slipped through comes
   out now, before commit (the hook is a backstop, not the first line).
5. **Rollback is real.** "Not applicable" is valid only for pure-knowledge
   captures. If an action was taken, the rollback must be a real procedure,
   not "remember what it looked like."
6. **Links resolve.** ADR numbers, other captures, external refs — check
   they exist and point where claimed.
7. **`Not recorded — fill in.` is filled in or the section removed.** These
   are the model telling you it had nothing; either supply it or cut it.

## Promote

When the draft is true and complete:

```bash
cd captures
$EDITOR 2026-07-03-topic.md.draft      # make your edits
git mv 2026-07-03-topic.md.draft 2026-07-03-topic.md   # rename: draft → capture
git add 2026-07-03-topic.md
git commit -m "capture: <topic>"       # hook scans for secrets AND draft markers
```

The rename is the act of vouching for it. After this, the substrate treats
it as fact.

## Reject

If the draft is wrong beyond quick fixing, or the session didn't warrant a
capture after all:

```bash
rm captures/2026-07-03-topic.md.draft
```

No ceremony. A rejected draft costs nothing — that's the point of the
contract. Better to redraft or hand-write than to promote something you'd
have to un-cite later.

## What the hook enforces

The pre-commit hook (G5 + this) blocks a staged `*.md` file in `captures/`
that still contains the `DRAFT by hcd` marker or a `Not recorded — fill in.`
placeholder. It cannot judge truthfulness — that is yours — but it stops the
mechanical mistakes: committing a draft you forgot to review, or one with
unfilled gaps. Override for a deliberate exception with `--no-verify`, but
if you're doing that to a capture, ask yourself why.
