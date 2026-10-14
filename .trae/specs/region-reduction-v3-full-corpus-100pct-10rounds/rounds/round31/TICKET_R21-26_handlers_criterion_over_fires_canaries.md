# R21-26 — the handlers `_target` criterion over-fires: it breaks `arg_checker` and `profiler_func`

Parent: `TICKET_R21-23_handlers_flip_suppressed_by_R21-14.md` (solved) → `rounds/round30/CANDIDATE_r44a_...`
(the criterion) → `rounds/round31/CANDIDATE_r45a_region_ast_generator.py` (criterion + two narrowing
hunks). None of it is landed: gate 31 landed only r47a + r48a after this was found.

## 0. What is already proven — do not re-derive

`handlers._target` reaches **30/30** on the current sealed bytes with r45a's 3-hunk candidate, and `risk`
stays 43/43. That part works. What also happens, measured by the gate (not by any panel):

    [units] 6603/6617 -> 6601/6617   [files] 396 -> 392   新增失败单元=6
    NEW-FAIL ArgumentChecker.is_valid_date.check_is_valid_date   (IQCommon, IQData/utils, IQEngine/utils)
    NEW-FAIL ProfilerTool.show_func                              (same three packages)

Hunk-level attribution on the sealed base `37d9fecb893704ac` (h1 = +32 helper block, h2 = +67 the
**criterion itself** transplanted from r44a, h3 = +2/−1 the R21-14 third-hunk narrowing):

| build | arg_checker (49/49) | profiler_func (17/17) | handlers (29/30) |
|---|---|---|---|
| h1 | 49/49 | 17/17 | 29/30 |
| h3 | 49/49 | 17/17 | 29/30 |
| **h2** | **48/49** | **16/17** | 29/30 |
| h2+h3 | 48/49 | 16/17 | 29/30 |
| h1+h2 | 48/49 | 16/17 | 29/30 |
| h1+h2+h3 | 48/49 | 16/17 | **30/30** |

So h2 alone does the damage and both narrowing hunks are required for the flip. Reusable tooling:
`D:/Temp/t31_hunkpick.py <old_base> <new_base> <candidate> <out> <hunk_ids...>` applies a subset of a
candidate's hunks onto a moved base by content anchors (it asserts a unique anchor hit and that any
replaced line still matches).

## 1. Your job

Narrow h2's precondition so it stops firing in `check_is_valid_date` and `show_func`, keeping h1+h3 and
`handlers 30/30`. Note h2 is a **top-level `if/elif` merge-chain assembly**: it fires when a top-level
IfRegion has `merge_block == next top-level IfRegion's condition/entry`, empty `orelse`/`elif_*`, and its
then-tail `return None` is a single-predecessor `pure-none` non-join landing.

First measure, then decide. For each of the four units (victim + the two canary shapes, which exist in
three packages each) dump, at the moment h2 fires: the two top-level IfRegions'
`entry / cond_block / merge_block / then_blocks / else_blocks / elif_*`, the tail block's predecessor
count and role, and the enclosing construct (is it inside a `for`/`while` body? inside a `try`?). The
conjunct that distinguishes `_target` from the canaries must be a CFG fact available at that point —
**no file names, no qualnames, no offset constants**. If you cannot find one, that is a legitimate
FALSIFIED result; say which candidate conjuncts you tested and what each did to the four units.

Two prior falsifications in this neighborhood, so do not repeat them: the `handlers` "fold" premise (the
two adjacent `return None` pairs are CPython per-exit-edge duplication, not an emission fold), and any
criterion that tries to *land a jump* in the generator (AST has no jump operands).

## 2. Acceptance bar

- `handlers.pyc` **30/30**, victim shape `delta=0 hunks=0 landings=0 judge_diff=False`.
- `IQCommon/arg_checker.pyc` **49/49**, `IQCommon/profiler_func.pyc` **17/17** — and the same for the two
  duplicated-package copies (`IQData/utils`, `IQEngine/utils`); a fix that satisfies only the `IQCommon`
  copy is not done.
- Nothing else decreases: quotation 153/153, klinedata 64/64, strategy 27/27, risk 43/43,
  wizard 58/58, real_quote 45/45, order_api 37/37, matcher 17/17, broker 121/128, quote 91/92,
  realtime_event_source 12/13, trade_info_utils 40/41 (its two units `query_trade_strategy_info`,
  `query_strategy_id` are now green — do not un-flip them), api_base 28/28.
- Run the **20-file** pre-gate panel: `python -X utf8 D:/Temp/t30/panel14.py <mirror_root> <tag> 0 20`
  (it was widened on 2026-10-11 to include the six canary files; `0 14` no longer covers them).
  Then report the corpus-wide byte census — regen all 402 and `cmp` against the sealed products
  (`CHANGED=n` with the list), because a panel of 20 is still not the corpus.

## 3. Constraints

Base = the current sealed generator `37d9fecb893704ac` (gate 31), analyzer `35e227ac3e7b25af`; the file
carries a UTF-8 BOM and mixed CRLF/LF — read with `utf-8-sig`, patch at byte level, never re-encode
wholesale. Repo READ-ONLY, no git write commands. `python -X utf8`, never `PYTHONIOENCODING`; nothing over
300 s; scratch under `D:/Temp/r50/`; only `core/cfg/region_ast_generator.py` may change; judge with
`scripts/pyc_verify.py single <abs .pyc> --source <product>`; deliver a whole file plus `FIX_R21-26.md`
(sections 0–7, and section 6 must list every candidate conjunct with its effect on all four units).
