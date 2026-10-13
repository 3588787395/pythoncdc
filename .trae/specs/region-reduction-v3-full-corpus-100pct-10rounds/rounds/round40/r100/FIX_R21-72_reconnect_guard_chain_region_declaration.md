# FIX_R21-72 - reconnect guard-chain region declaration (analyzer-side, `_sync_worker`)

Engineer: r100a. Round 40. File owned/edited: `core/cfg/region_analyzer.py` ONLY.
Ticket: `rounds/round40/TICKET_R21-59_sync_worker_per_exit_edge_duplication.md`, addendum 19.
Label for the new rule: `[R21-72 …]`.

## 0. Base verification (before any measurement)

Mirror `D:/Temp/r100`, copied from repo `core parsers bytecode utils scripts pycdc.py`.
Pair installed (sha256[:16], byte size, BOM, 0 bare LF, 0 `\r\r\n`):

```
1471c92eca157e46 2121884  core/cfg/region_analyzer.py      (from r93/region_analyzer_R21-64a_FINAL.py)  <- edited here
0f4c3898298e6f2e 3860104  core/cfg/region_ast_generator.py (from r95/..._R21-66_0f4c3898298e6f2e.py)     untouched
```

Repo rig `orchestrator/fastgate_r91m.py` + `gold_diff_r91m.py` + `win_r91.py` copied to
`D:/Temp/r100/orch/` (win_r91 also at mirror root because the rig calls `M/win_r91.py`) and their
`M` constant repointed `D:/Temp/r91m -> D:/Temp/r100` so nothing is written outside my mirror.
Round-14 battery copied to the same relative depth (`M/.trae/specs/…/rounds/round14/repro/`) because
`run_repro.py` derives `ROOT` from its own `__file__` (7 dirname steps -> `D:/Temp/r100`).

## 1. Reproduced orchestrator numbers (base = pair, BEFORE my edit)

target `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`:

```
[single] status=failure units=127/128 success_rate=99.22%
  ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
orig instrs=412 prod instrs=408 delta=-4   windows=5
product = 178790 bytes
unit=_sync_worker ours=42 lines GOLD=45 lines  hunks_vs_GOLD=2
   @@ -18,0 +19,8 @@
   @@ -37,5 +44,0 @@
```

All four orchestrator numbers match the brief exactly (`units=127/128`, sole failing unit
`_sync_worker`, windows 5, 178,790 B, `gold_diff` = 2 hunks). Base is provably the same bytes the
orchestrator measured.

The two hunks (captured `logs/base_unit_ours.txt` vs `logs/base_unit_gold.txt`): hunk 1 deletes from
GOLD the 8-line nested reconnect chain that belongs BETWEEN loop 1 and loop 2; hunk 2 deletes our
flat 5-line rendering of the same chain that sits AFTER loop 2 and ends in `break` instead of
`return`. That is addendum 18 fact 1 = addendum 19's declaration gap, nothing else.

## 2. Diagnosis (from the ticket's read-only dump, reproduced in section 4)

Eleven blocks `@1214..@1876` are unowned body blocks of `LoopRegion@232`; `@1890` opens the child
`LoopRegion@1890`. The generator emits the child region before the unowned blocks that precede it,
so the chain prints after loop 2 and its terminal `RETURN_VALUE` (`@1874`, the unit's only one) is
rendered as a loop exit (`break`). Fix = declare the chain as an `IfRegion` at identification time.

## 3. Census (BEFORE editing) - see section 6 for the filled table

Predicate candidate (block data only, no offsets/names/constants):
* P1 entry block ends in a conditional forward jump whose false target T is a block;
* P2 the block at the true leg is the next block in the same owner's block order and ends in a
  conditional forward jump to the SAME target T (consecutive guard blocks sharing one target);
* P3 T is the entry of a declared sibling region (or the unique merge/next-sibling entry);
* P4 the true-leg chain is finite, all its guards jump to T, and its terminal leg reaches blocks that
  never reach T; among them the last block of the run terminates in `RETURN_VALUE` class;
* P5 all chain + tail blocks are currently unowned body blocks of one enclosing region (so the
  declaration shrinks exactly one owner list: unique membership preserved).

## 4-6. Appended as measured (doc-first policy; 150-turn cap).
