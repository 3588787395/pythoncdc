# FIX_R21-11 — r30a — run_tick_socket: the empty-data guard arm relocated one line late

## mirror proof

- Mirror `D:/Temp/r30a/wt` built by `cp -r pycdc.py core parsers utils bytecode scripts` from the repo at
  `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, with `analyzer_pristine.py` kept beside it. The
  brief's hashes were verified against the repo rather than trusted:
  `core/cfg/region_analyzer.py = 35e227ac3e7b25af` (2,097,160 bytes, 32,810 lines) — matches;
  `region_ast_generator.py = c16daa4f87dc68e6`, `comprehension_generator.py = 7d8acab92ccc7782` — matched at
  the first build. Files over numbers.
- **Two environment events inside this session, neither caused by me.**
  1. The repo advanced `093d19e3 → 5a14e066 (gate 26) → 7c778596 (gate 27)` while I worked. Gate 27 landed
     r27a's try/else arm-tail ownership and moved `fly/data/quote.pyc` 89/92 → **90/92**, so the brief's
     baseline number is still current, and `region_analyzer.py` bytes did **not** change across it
     (`git log -1 -- core/cfg/region_analyzer.py` = 5a14e066).
  2. A disk-level cleanup deleted `D:\Temp` (now `D:\Temppurge_wCpt`), `D:\python-sdk` (the pyc corpus the
     brief's paths point at), `D:\pylingual` and `D:\qoder-feedback` mid-run, taking my first mirror, its
     `pristine/` copy, every product and the trace output. My only `rm -rf` all session targeted
     `probe/_bak`. Everything under "baseline check" onward is re-measured on a **rebuilt** mirror.
- End state: `cmp wt/core/cfg/region_analyzer.py <repo>/core/cfg/region_analyzer.py` → **BYTE_IDENTICAL**
  (35e227ac3e7b25af). No repo writes, no git mutations, no `*OK.py` in the repo, `gate_round.py` /
  `gate_chain.py` never run, one heavy job at a time, every command bounded under 300 s.

## baseline check

- Specimen: the sealed corpus pyc went with `D:/python-sdk`, so I used a surviving byte-copy
  `D:/temp/r24a/wt/site-packages/fly/data/quote.pyc` (127,591 B, `co_name = <module>`) staged at
  `D:/Temp/r30a/corpus/fly/data/quote.pyc` (plus `quotation.pyc`, 209,494 B, from the same tree). It
  reproduces the ticket exactly, which is what makes it the same specimen for our purposes — sealed-base
  product, `unit_diff … "<module>.Quote.run_tick_socket" --prod … --all`:

  ```
  == delete orig[90..114 @@528..@@682] prod[90..90] del=24 ins=0
  == insert orig[226..226 @@1278..@-] prod[202..227] del=0 ins=25
  ```

  one relocation, 2 hunks, 24 deleted / 25 inserted, boundary `@682` = the arm's own `RETURN_VALUE`.
- Judges on the sealed mirror, always with `--source` on my own product (the stale-in-place NOTE heeded):
  `fly/data/quote.pyc` → `status=failure units=90/92 success_rate=97.83%`;
  `fly/data/quotation.pyc` → `status=success units=153/153 success_rate=100.00%`.
  Both brief baselines reproduced, so the rebuilt mirror is the right host.
- The judge survived the wipe because `compare_pyc` lives in the repo (`bytecode_compare/`) and pylingual is
  a pip package under `AppData\Roaming\Python\Python313`, not under `D:\pylingual`.
- Spot files (broker 120/128, wizard, real_quote, klinedata, handlers, api_base, strategy,
  realtime_event_source, risk `__init__`, trade_info_utils, matcher, order_api): **all SKIPPED.** No
  candidate got installed, so there was nothing to A/B, and the recovery budget went to rebuilding the
  wiped mirror. Stated plainly as the brief requires.

## anatomy (measured)

The relocated arm is the empty-data guard of `run_tick_socket`:
`self.log.quote.warning('tick数据返回为空')` @528–@588, `userLock.acquire()` @590–@628,
`dataDict['updateflag'] = -1` (STORE_SUBSCR) @630/@632/@634, `userLock.release()` @640–@678, and **its own
`LOAD_CONST None; RETURN_VALUE` @680/@682**. The product emits that text 24 lines lower than the original
(orig line 90 → prod line 202) and the original slot is deleted, so `delta=+1` is one net extra line above
it, not a lost statement — consistent with the brief's disassembly.

**The brief's hypothesis is verified on the sealed bytes.** A print-only census of the sealed analyzer's own
`IfRegion(` constructors — site 1 = plain `IF_THEN`/`IF_THEN_ELSE` at sealed line 21323, site 2 =
`IF_ELIF_CHAIN` at sealed line 23012 (a third constructor exists at 23188) — executed *inside the process
that produces the artifact*, printing every declaration touching `{528, 680, 684, 1512, 1770}`, gives for
`<module>.Quote.run_tick_socket`:

```
[R30A-REG] entry=24   merge=1512 then=[68, 70, 136, 684, 808, 844, 1146, 1188, 1190, 1226, 1230, 1234, 1276]
                       else=[528, 680]                    ertype=RegionType.IF_THEN_ELSE
[R30A-REG] entry=1318 merge=1512 then=[1444, 1450] else=[1446]           ertype=RegionType.IF_THEN_ELSE
[R30A-REG] entry=640  merge=2208 then=[684, 686, 752, 1116, 1240, 1282, 1354, 1396, 1468, 1510, 1578, 1620]
                       else=[1050]                                      ertype=RegionType.IF_THEN_ELSE
```

(7 census lines for the whole file; the four not shown belong to another unit — `entry=1412/1052/302/284`,
all `merge=1980` — which is also why offset 1770 appears in *its* branch lists and not in the victim's.)

So, from the region's own blocks and their last instructions, at identification time:

* the guard arm **is declared** — it is this region's `else_blocks=[528, 680]`;
* **684 really is misdeclared as a `then_block` of that same region while its `merge_block=1512`** — the
  brief's sentence, confirmed verbatim on the sealed build;
* 684 is the block the CFG reaches only **after** 1512 (the block list puts `[1512..1520]` immediately before
  `[684..]`), i.e. post-conditional merge code absorbed into the then arm; and it is *simultaneously*
  declared as a then-block of `entry=640` — a block inside the guard arm itself — whose merge is 2208. The
  same block is claimed twice, by two different regions, and the generator renders the statements at the
  later of the two places. That is the relocation.

## 判据实现

**Nothing is installed. `DELIVER/region_analyzer.py` is byte-identical to sealed (first line of the
declaration).** The criterion I built and measured is recorded here and is **falsified for the sealed base
at the census step**, before any actuation question — which is a stronger statement than a guessed patch:

> Drop from a conditional's branch list the block that its own merge falls through to: the branch has
> already been consumed by an inner conditional, so the block after the merge belongs to neither branch.

The version I implemented (the one the previous engineer's report implies) removes **the merge block itself**
when it sits inside a branch, guarded by three own-data tests: branch list contains `merge_block`; the
branch's last instruction jumps to `merge_block`; `merge_block` is declared as a copy of the region entry
(same first instruction offset). Anchor was the IfRegion finalisation site, `TOTAL_FIRES` counted at the
removal.

**Measured: that predicate has no anchor in the sealed file.** `merge_block ∈ then_blocks ∪ else_blocks`
fired on **0 of the 7** census regions in `quote.pyc`, i.e. `TOTAL_FIRES = 0`, and on the victim specifically
`1512` is declared in no branch list of any region. The misdeclared member is **684, the merge's
fall-through successor**, not the merge. So the shape of the repair is one indirection away from what the
ticket inherited, and I did not ship an untested substitute for it.

### 判据（未安装，给下一张票可直接落地）

Anchor: sealed `region_analyzer.py:21323` (plain `IF_THEN`/`IF_THEN_ELSE` constructor) **and** `:23012`
(`IF_ELIF_CHAIN` constructor) — both, because the victim's neighbour `entry=1318` proves nested conditionals
reach site 2, and a single-site patch is a partial patch. Locals at both sites: `block`, `merge`,
`then_blocks`, `else_blocks`; blocks are objects with `.start_offset`, `.get_last_instruction()`
(`.opname` / `.argval` / `.offset`) and `.instructions[i].offset` — the sealed file already does this exact
arithmetic 60 lines above site 1 (`_r26a_c_last.argval == merge.start_offset` at 21262), so the style is the
one landed twice today.

```python
        # r30a: a block that this region's own merge falls through to is
        # post-conditional code, not a branch of this region.  Three tests, all
        # on the region's own blocks and their last instructions, evaluated once
        # at identification time (no graph read, no cross-region lookup):
        #   (1) B is declared in then_blocks or else_blocks of THIS region;
        #   (2) merge is not None and merge's last real instruction ENDS where B
        #       STARTS (merge.instructions[-1].offset + its size == B.start_offset)
        #       ⇒ B is reachable only after the conditional has already merged;
        #   (3) the arm this region merges into is the arm that ends in a
        #       RETURN_VALUE / unconditional jump (the guard arm @682), so no
        #       path re-enters B from inside the branch.
        # Drop B from the branch list that is longer, so the region renders the
        # branch through the block that actually owns it and the arm keeps its
        # own trailing RETURN_VALUE at @682.
```

(2) is precisely the `@1520 → @684` boundary and is decidable from `merge.instructions` alone; (3) is the
arm's own `RETURN_VALUE` @680/@682, which the victim census already prints. Test (1)+(2) alone would be the
minimal fire; the `TOTAL_FIRES` census over the 14 panel files is the first thing to run with it, because a
predicate that only needs `merge`'s last instruction can fire wherever a merge falls through into a declared
block, which is common.

## readings

* Sealed base, victim: 2 hunks / del 24 / ins 25 (block quote above), judge `fly/data/quote.pyc` **90/92**.
* Sealed base, sanity: `fly/data/quotation.pyc` **153/153**.
* **Fire census on the sealed base of the inherited criterion: `TOTAL_FIRES = 0`** (7 candidate regions in
  `quote.pyc`, none with the merge inside a branch). I did not run the 14-file census, because the criterion
  that census would count has no anchor on the sealed bytes — reporting a zero-fire number for one file where
  the predicate is provably unreachable elsewhere-by-construction is not a substitute for a census, so I say
  it is not measured rather than imply coverage.
* Pre-wipe readings, on a mirror whose `region_analyzer.py` carried **another engineer's in-flight**
  `_if_regions_to_try` / `_region_captures_branch` machinery — real measurements, **not valid on the sealed
  base**, labelled as such:
  - that tree did declare, for the re-generated copy of the parent's branch, `merge=1770 then=[684]`, with
    all three signature tests true and `TOTAL_FIRES = 1` on the victim and 0 across the other panel files;
    removing 684 took that tree's `quote.pyc` 20/21 → **21/21** top-level units;
  - the over-broad variant (drop the declared block whenever the branch tail jumps to it, ignoring the
    merge-copy test) took the same tree 20/21 → **18/21**: `update_data` 85% → 74%, `get_dingding_data`
    96% → 85%, 3 hunks / 5 landings, `if __name__ == '__main__'` lost — the correct-at-identification
    penalty, which is why the predicate is sealed to three conditions and why I did not ship the loose form.

## negatives

1. **On the sealed base the merge is not misdeclared — the block after it is.** `1512 ∉ then_blocks ∪
   else_blocks` for every region of the victim, so the natural reading of the inherited report ("remove the
   merge from the branch") is a 0-fire predicate. This is the single most important negative fact of the
   ticket.
2. **The inherited mechanism does not exist in the sealed file.** `_if_regions_to_try` and
   `_region_captures_branch` — which is the path that made the parent's branch declare `then=[684]` with
   `merge=1770` — occur **zero** times in sealed `region_analyzer.py` (35e227ac, 32,810 lines). Every line
   number in the inherited report (`:20456`, `:22152`, `:21263`, `_if_generate_then_branch:17780`,
   `_merge_block_is_then_exclusive:20275`) is written against an unsealed tree and must be re-anchored
   before it can land. The generator sites are the same story: the *product* they surface is real, the *code*
   that surfaces it moved.
3. **One block, two claim sites — and both are regions, not a region and its caller.** 684 is declared as a
   then-block of `entry=24 merge=1512` **and** of `entry=640 merge=2208`. Un-marking one claim does not by
   itself prove the other renders the arm's trailing `RETURN_VALUE` @682; the claim to keep is the one whose
   region contains @640–@682.
4. Not re-attempted (measured-dead from the brief, and consistent with everything I saw): generator
   predicates that move a jump landing (AST has no jump operands); declaring a missing merge for
   `api_base`/`strategy`; `_loop_preheader_blocks` entry/header narrowing; `handlers._target`,
   `kill_trade_process`, `clock_worker`, broker `_process_order`/`_process_cancel_order`.
5. Instrument discipline: the censuses printed only (no mutation) and ran to completion with no traceback;
   the mutating probes were confined to the mirror; the mirror was restored and `cmp`-proved byte-exact;
   products were checked for size before judging (94,223 B and 182,759 B, no stubs).

## declaration

**FIRST LINE: `D:/Temp/r30a/DELIVER/region_analyzer.py` is BYTE-IDENTICAL to the sealed file at `7c778596` —
sha256 `35e227ac3e7b25af`, 2,097,160 bytes, 32,810 lines. No patch is installed.**

* **Verdict: FALSIFIED-but-supporting.** The premise is true on the sealed bytes and the anatomy is now
  measured to the instruction boundary; the inherited criterion cannot actuate there because the merge is
  declared in no branch list (`TOTAL_FIRES = 0`), and no alternative predicate was both measured and
  installable inside budget. I sealed the ticket with the re-anchored criterion instead of shipping an
  untested one.
* Bar: `run_tick_socket` stays red, `fly/data/quote.pyc` stays **90/92**, `fly/data/quotation.pyc` stays
  **153/153**, shape unchanged (`delete orig[90..114 @@528..@@682] del=24` + `insert prod[202..227] ins=25`,
  2 hunks, 5 landings, `delta=+1`). Nothing decreased.
* Most important negative fact: **sealed `region_analyzer.py` has no `_if_regions_to_try` /
  `_region_captures_branch` at all**, so the previous engineer's 684/1770 region and every line number he
  quoted belong to an unsealed tree. Re-anchor at `region_analyzer.py:21323` and `:23012`, and key the drop
  on **the merge's fall-through successor (684)** — not on the merge's own branch membership.
