# ADJUDICATION ROUND 41 (2026-10-14, session end-state)

**Landed bytes unchanged all session:** analyzer `1471c92eca157e46`, generator `566ff5c502276e48`;
`git status --porcelain -- core/` empty at every checkpoint, `site-packages/` untouched, every commit
pushed and verified by `git fetch` + `rev-list --count origin/...HEAD == 0`.

**Corpus: 6616/6617 units (99.9849 %), 401/402 files. Gate label 41 NOT consumed** — no candidate
reached judge `13/13`, so nothing was installed (fires-without-flips). Sole failing unit:
`<module>.RealtimeEventSource.clock_worker` in `realtime_event_source.pyc`, `12/13`,
*Different control flow*.

## 1. Arms measured this session

All by the orchestrator in `D:/Temp/r91m` on the pinned platform, analyzer/generator restored and
re-hashed after every arm.

| arm | analyzer | generator | product | instrs | jsites | back | hunks | judge | installable |
|---|---|---|---|---|---|---|---|---|---|
| F5 base | 996a1b1acf143458 | 566ff5c502276e48 | 20190 192ba0f0 | -114 | -9 | +0 | 4 | 12/13 | - |
| [R21-79] tail release | 3ad5ceaa23135334 | landed | 20078 25730af9 | -115 | -9 | +0 | 4 | 12/13 | no (zero flip) |
| [R21-80] folded join | 7e8350f7d52fe9a3 | landed | base bytes | -114 | -9 | +0 | 4 | 12/13 | no (inert) |
| [R21-79]+[R21-80] | 890a1593abfcfb6b | landed | 20078 25730af9 | -115 | -9 | +0 | 4 | 12/13 | no (superseded by one half) |
| **[R21-81] dispatch ledger** | 996a1b1acf143458 | 8da14b53a94e07c3 | 20628 7f3d1796 | **-77** | **-3** | **+0** | 4 | 12/13 | no (quote 89/92, real_quote 42/45) |
| **[R21-79]+[R21-81] pair** | 3ad5ceaa | 8da14b53 | 20484 | **-78** | **-3** | **+0** | **3** | 12/13 | no (ledger incomplete) |

- `[R21-81]` is the first arm in the campaign to move its named fact positively: 37 of the 112 dropped
  instructions recovered, unit body 241 → 248 lines against the oracle 254, `jsites` −9 → −3 with
  `back` still `+0`.
- The pair is the **first sub-4-hunk reading in 41 rounds**: the analyzer tail-release and the generator
  dispatch ledger are additive — unlike every two-analyzer-half merge measured so far (fifth
  supersession).
- Controls re-certified in the same window: `GOLD_realtime_event_source_PROOF.py` reads `hunks=0`,
  `instrs=+0`, `indeg-equal=True`, `13/13`; the F5 base reads `-114 / 4 / False / 12/13`.

## 2. Ruled out this session (do not re-dispatch)

1. **`[R21-80]` stub-folded join as an analyzer-only fix.** Three byte states measured:
   `c8fd738b922cd390` destroyed output (`instrs=-210`, `jsites=-22`); `7e8350f7d52fe9a3` is byte-inert on
   the victim; in combination with `[R21-79]` it contributes nothing. r106a then hit its 150-turn cap
   (163 tool uses, no MEASURE doc).
2. **`elif_final_else` over-absorption as the drop mechanism.** `[R21-79]` proves the release is correct
   and collateral-free (42-block arm → 1, keeping `@7492`; `region.blocks` 48 → 7; 253 instructions
   freed; panel 19 of 20 identical; ROOT-joined 402 sweep `CHANGED={realtime_event_source}`), and it
   still does not flip: the freed run is simultaneously in the next chain level
   `IfRegion@7634.then_blocks`, and after the release its `block_to_region` owner is
   `TryExceptRegion@6`, so both renderers decline. Fifth exclusion on that axis.
3. **Jump-target criteria in the generator** — standing finding unchanged (the AST carries no jump
   operands). `[R21-81]` can act because it is an emission-coverage rule, not a landing rule.

## 3. Live dispatch and the next hand

- **r109a / `[R21-82]`** is running on `D:/Temp/r109`, building on r108a delivered bytes: write
  `_r2181_emitted_entries` at **every** structural emission site — today 4/8/2/8 direct
  `_generate_if` / `_generate_try` / `_generate_loop` / `_generate_match` calls bypass the
  `_generate_region` funnel, which is exactly what regresses `quote 92→89` and `real_quote 45→42` — with
  `[R21-79]` as the labelled analyzer co-requisite. Bar in order: `instrs` toward 0 with `back=+0` kept;
  `quote 92/92` and `real_quote 45/45` restored; 20-file panel unmoved (pair rows by index, three
  same-basename canaries); ROOT-joined 402 sweep `CHANGED={realtime_event_source}`; judge `13/13`.
- Remaining distance after the pair: **78 instructions, 3 hunks, 6 text lines**, `indeg-equal=False` —
  the judge still sees a different CFG, so text parity alone would not be sufficient. Per-hunk
  attribution: `rounds/round41/hunk_attribution_r107.py` (certified: oracle 0 hunks; F5 product labelled
  step1 / step3 / step4 / step6).
- On a `13/13` with a clean sweep: `install_pair.py --ana <3ad5ceaa bytes> --gen <R21-82 candidate>
  --units "13/13" --sweep "ok=402 bad=0 changed=1" --gate`, then `gate_chain.py 41 40` against
  `rounds/round40/after`, `residual_report.py 41 40` (expect `UNREGISTERED=0`), commit the regenerated
  products plus `rounds/round41/after` shards, push and verify the ref.

## 4. Artifacts banked this session

`rounds/round41/CANDIDATE_r2179_3ad5ceaa23135334.py` + `r107/PATCH_R21-79_region_analyzer.py` +
`r107/FIX_R21-79_clock_worker_tail_claim.md`;
`rounds/round41/CANDIDATE_r2179pair_890a1593abfcfb6b.py`;
`rounds/round41/r108/` (candidate, patch, FIX and MEASURE for `[R21-81]`);
`MEASURE_R21-79_fe_overabsorption_census.md`; `MEASURE_R21-81_pair_matrix.md`;
`TICKET_R21-79_*.md` addenda 1–6; `TICKET_R21-78_*.md` addenda 6–7; `hunk_attribution_r107.py`;
`r107/` census logs.

**Objective status: not achieved.** 6616/6617 = 99.9849 %, one unit short of 100 %, with the instruction
gap to the last unit narrowed from −114 to −78 and the first additive analyzer+generator pair measured.

## 5. Engineer liveness at session end (recorded so the next hand does not wait)

`r109a` (`[R21-82]`) has produced **no file writes for 30 minutes** (`D:/Temp/r109` newest mtime = its own
mirror/copy step) and `Get-Process python` shows **no engineer-driven process** — only my probe. Precedent
says a Chat quota cap kills an engineer with no report (r105a died mid-round exactly this way), so treat
`[R21-82]` as **unconfirmed, not delivered**: do not wait on its notification. Re-dispatch from the pinned
bytes rather than from its prose — analyzer `3ad5ceaa23135334`
(`rounds/round41/CANDIDATE_r2179_3ad5ceaa23135334.py`), generator `8da14b53a94e07c3`
(`rounds/round41/r108/CANDIDATE_r2181_8da14b53a94e07c3.py`) plus its
`PATCH_R21-81_region_ast_generator.py`, and the single required change: write `_r2181_emitted_entries`
at every structural emission site instead of only the `_generate_region` funnel. Task `#157` carries the
bar in execution order.
