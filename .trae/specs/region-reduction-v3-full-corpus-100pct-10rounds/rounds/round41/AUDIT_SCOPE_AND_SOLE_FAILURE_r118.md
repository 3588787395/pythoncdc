# AUDIT - fresh scope and sole-failure recount (2026-10-14 01:48 UTC)

Re-read directly from disk and from the sealed gate-40 shard reports; no number here is
inherited from an earlier row. Purpose: the completion audit requires that any "green"
status be shown to cover the whole objective, and the objective is
"every .pyc decompiles successfully AND is judged Equal".

## Decompilation half - satisfied corpus-wide

Walk of `site-packages/**/*.pyc` excluding `__pycache__`:

```
pyc-named files                 406
with the current interpreter magic (real inputs)   405
of those, a non-empty *OK.py product exists       405
zero-byte products                                 0
```

So every real input has a produced, non-empty product. Working-tree products are byte-clean
against HEAD: `git status --porcelain -- site-packages/` filtered to `*OK.py` lists 0 lines, and
this session ran no regen and wrote no product (products come only from the pipeline).
Measured 2026-10-14 01:49 UTC. The 406-vs-405 gap and the 402-file roster boundary are documented
in `AUDIT_CORPUS_SCOPE_402.md`: the roster is 402, the extra names are the mis-suffixed
`IQCommon/util/email_utils.py.pyc` (whose bytes are a Decompyle++ comment header, i.e. a product
not an input) and compiled scratch artifacts.

## Judge half - exactly one unit fails

Summed over all 8 sealed shards in `rounds/round40/after/*.json` (402 file rows):

```
units = 6616/6617  (99.9849 %)
files_success = 401   files_failure = 1
failing unit list (verbatim):
  ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
```

That single unit is the entire distance to 100 %. It is the unit ticket
`TICKET_R21-91_else_body_hoist.md` attacks, and its acceptance instrument is controlled on a
known-GREEN input (`block_diff_r118.py` on the 13/13 GOLD oracle reads
`SIG-ONLY-ORIG=0 SIG-ONLY-PROD=0`, `blocks 176/176`, `instrs 1442/1442`).

## Gate readiness for label 41 (checked, not assumed)

- `gate_chain.py 41 40 --dry` prints all four stages `regen -> verify -> report -> checks`
  with both labels resolved.
- `gate_round.py` creates `rounds/round41/after` itself (`os.makedirs(exist_ok=True)`), and the
  `before` side reads the committed `rounds/round40/after` (8 shard files present).
- `regen` deletes each product before producing it, so a re-run cannot reuse stale bytes.
- Install rig signature verified: `install_pair.py --ana <file> --gen <file> --gold-hunks N
  --units "x/y" [--gate]` - `--gold-hunks` is REQUIRED and nonzero makes it refuse; there is no
  `--sweep` flag. The zero-hunk-vs-GOLD condition is sufficient-not-necessary, so the ticket
  carries the direct-write fallback that repeats the same byte checks (BOM, zero bare LF, zero
  `\r\r\n`, `py_compile`, in-place re-hash, `git status --porcelain -- core/` exactly 2 lines).

## Compliance state at this row

Landed bytes unmoved (analyzer `fef59e95359f36fd`, generator `c3049a87daf59acc`,
`git status --porcelain -- core/` = 0 lines); gate label 41 unconsumed; `[R21-90]` banked with
all collateral bars passed; engineer r117a running ticket R21-91. Objective NOT achieved:
one unit short, so the goal stays open.
