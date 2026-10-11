# Gate 32 adjudication and landing record

Landed file: `core/cfg/region_ast_generator.py` `pre=37d9fecb893704ac` → **`e7e2b2dd4cf6ed64`**
(4 additive hunks from two engineers' candidates, merged by base-line coordinates, byte-level install,
`py_compile OK`). Exactly two products moved corpus-wide.

## 1. Certified numbers (`gate_chain.py 32 31`, all four stages rc=0)

- regen `ok=402 bad=0` (431 s — slow because six engineer mirrors were still churning CPU)
- verify (330 s), report: **units 6606 → 6608 /6617 (99.8640%), files 397 → 398**,
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=2`
  - FIXED `trade_info_utils.<module>.kill_trade_process` → file **41/41, first fully green file of the round**
  - FIXED `trade_live_broker.<module>.TradeLiveBroker.get_ipo_stocks` → **122/128**
- checks (112 s): quotation **153/153**, small34 `units_success 1559 / success 30` (+2 units, +1 green file —
  the second witness moved exactly as predicted), ruler selfcheck OK,
  pytest `2 failed, 282 passed, 2 xpassed` (the same two registered residents)
- sealed residual: **4 files / 9 units**, `UNREGISTERED 行数=0` (`RESIDUAL_ROUND32.md`)

## 2. The two candidates and what each actually fixed

**r53a — R21-25 `kill_trade_process`** (DELIVER `5eee6feaa1ee1e94`, +86 lines at base 3340 and 20398).
The unit was `delta=0 hunks=0 landings=2`: two byte-identical `LOAD_CONST None/RETURN_VALUE` tails with the
two exits' operands exchanged. Its `compile()` table decided the mechanism on 3.11.7: shape **P** (an
`else: return None` present in the elif chain) reproduces the SWAPPED allocation, shape **Q** (no `else:` arm)
reproduces the original — both with the identical six tail offsets, so only the tail *allocation order*
differs. The construction site is `_if_generate_elif_chain`'s non-nested final-else path: the surviving
`final_else_stmts = [Return None]` exists because `_r23n16_blocks_have_explicit_return([@3868])` is true,
which skips the pop at 20381–20388, and the While-case at 20389–20398 does not apply. Its criterion
`_r2125_identical_none_tail_else(region)` is structurally disjoint from gate 31's `_r2121_shared_tail_sinks`
(that one requires `parent is None` and IF_THEN; here the parent is an IfRegion carrying an elif chain),
which is why both can coexist in one file. Census: corpus bytes `SAME=401 / CHANGED=1`, `TOTAL_FIRES=1`;
and it measured the TARGET_ONLY family down to **exactly two units**, noting that `get_ipo_stocks` swaps a
different pair (`IF_TRUE → LOAD_GLOBAL NULL+str`) and is therefore *not* the same mechanism — matching the
fact that r54a was separately fixing it.

**r54a — broker `get_ipo_stocks`** (2 hunks: +19 at base 22323, +2/−1 at 22334). `landings=1 → 0`,
`judge_diff=False`, broker 121 → 122.

## 3. How the landing was decided, and the one rule I bent deliberately

Neither candidate was installed on a claim. Before merging I measured each alone, then measured the
**merge** on the 20-file panel: 18 rows byte-identical, exactly the two intended products changed, all six
duplicated-module canaries green — so this pair shows no suppression (the gate-30 failure mode) and no
over-fire (the gate-31 failure mode).

r54a had **not** written its DELIVER file when I opened the gate. Rather than land a moving target I
re-hashed its mirror (`34e4464845e95447`, unchanged since the merge was built and since the panel run) and
installed only on that equality; r53a independently observed the same repo bytes afterwards and reported
`kill_trade_process delta=0 hunks=0 landings=0`, `units=41/41`, having never written the repo. If r54a's
delivered file later differs from `34e446…`, it becomes a fresh candidate for gate 33 — the landed content is
the content that was measured, and the gate certified it, which is the standard that decides, not authorship.

## 4. Clock_worker state after this gate (not landed)

- **M1** (r52a) banked: `−113 → −10`, seven never-dispatched entries now render, `TOTAL_FIRES` 1 file,
  19/20 panel SAME. Co-requisite, not landable alone.
- **M2** (r51a) banked after I reproduced its own verdict: delivered build makes the unit **worse**
  (`−122`), leaves hunks/landings at 7/18, and does not touch `quote` or `_sync_worker`. The
  analyzer-role route as implemented pays nothing; if M1+M3 still leaves the relocation hunk, M2 must be
  re-scoped as generator-side arm placement.
- **M3** (r59a) still running, briefed to measure merged-with-M1 rather than alone.

## 5. Next gate

Label **33** against `rounds/round32/after`. **9 units in 4 files**: `trade_live_broker` 6
(`_process_order`, `_process_cancel_order` — r58a; `etf_purchase_redemption` — R21-27; `ipo_stocks_order` —
R21-28; `_sync_worker`, `_trade_status_handle` — see NOTE_R21-31), `realtime_event_source.clock_worker` 1,
`handlers._target` 1 (R21-26, mis-fire signature recorded), `quote.run_individual_transform` 1.
Progress this session: gate 30 6603 → gate 31 6606 → **gate 32 6608 / 6617 (99.8640%)**, 398 green files.
