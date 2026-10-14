# R21-24-M3 — clock_worker's third mechanism: `(A and B) or C` arm assembly + a dropped `system_log.debug`

Held back from the round-32 dispatch on purpose: `clock_worker` needs M1+M2+M3 closed before the unit can
flip, and r51a (M2, analyzer) / r52a (M1, generator) are running now. Dispatch this one once their
candidates exist, and then **measure the merged trio, not this hunk alone**.

Source: `rounds/round31/DIAG_R21-24_clock_worker_r49a.md` (r49a's diagnosis, mirror fidelity-proven and
probe `cmp`-inertness-proven). Victim: `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`,
co-name `clock_worker`, sealed `len orig=1424 prod=1311 delta=-113 hunks=7 landings=18`, file 12/13.

## 0. Anchor drift warning — re-verified, do not trust the diagnosis's line numbers

r49a cited the gate-30 bytes (`7d336164eff5bf65`). Gate 31 added 313 lines, so its coordinates are stale.
Measured on the current sealed bytes (`37d9fecb893704ac`):

| what | now |
|---|---|
| `_if_generate_normal` def | `:21346` |
| the `_r23_or_*` arm branch (M1's bulk claim of `else_blocks`) | `:21801–21835` |
| `_process_if_blocks` def | `:25649` |
| `_loop_handle_child_region_entry` def (post-loop dispatch of an unrendered child) | `:14082` |
| `_inline_and_chain_exits_agree` def / its consumption (the gate-29 R21-13 veto) | `:19061` / `:19835` |

r49a's "inline-and claim at `:19619`" maps to the `:19835` veto neighbourhood (+246 = the 105-line and
141-line insertions that precede it). Re-derive the exact site from your own census, not from either
number, and print the two candidate sites you rejected with the reason.

## 1. What M3 is (per the diagnosis, all measured)

Four instances of `(A and B) or C` inside the one loop. Two defects compose it:
1. **arm assembly wires the next *sequential* statement as `else`** — the diagnosis proved the firing case
   is `blocks=[6496] branch=else`, i.e. a block that should follow the `if` is emitted as its `else` arm;
2. **the inline-`and` elif fold drops a statement** — with `_inline_and_chain_exits_agree` returning True
   (1 call measured), the claim removes block `@7270`'s leading `system_log.debug(...)`, which is the
   `−6 debug` component, plus 5 "Group-A" landing diffs and `+1/+1` inserts.

File to change: `core/cfg/region_ast_generator.py` (condition/arm structure, not jump targets). Remember
the structural wall: the generator emits an AST that is then `compile()`d, so no criterion here can write a
jump operand — a landing residual is fixed by changing the CONSTRUCT (see gate 31's
`_r4701_and_lift_or_tail` on `api_base`, which took a pure-landing unit to `0/0/0` that way).

## 2. Acceptance

- Necessary-and-sufficient demonstration: with M1+M2+M3 merged, `clock_worker` must read
  `delta=0 hunks=0 landings=0 judge_diff=False` and the file 13/13. Without M3 the specific M3 hunk
  (`+1/+1` inserts, `−6` debug, 5 Group-A landings) must return.
- Zero regressions on the **20-file** pre-gate panel:
  `python -X utf8 D:/Temp/t30/panel14.py <mirror_root> <tag> 0 20` — quotation 153/153, quote 91/92,
  klinedata 64/64, handlers 29/30, wizard 58/58, trade_info_utils 40/41, api_base 28/28, real_quote 45/45,
  strategy 27/27, order_api 37/37, broker 121/128, matcher 17/17, realtime_event_source 12/13→13/13,
  risk 43/43, plus the canaries `arg_checker`×3 (49/39/43) and `profiler_func`×3 (17/15/18). The canaries
  are in the bar because a −6-unit merge once passed a 14-file panel and only the gate saw it.
- Population count for your criterion, and the list of files it fires in, before you call it a family.

## 3. Constraints

Base = generator `37d9fecb893704ac`, analyzer `35e227ac3e7b25af` (UTF-8 BOM + mixed CRLF/LF → read
`utf-8-sig`, patch byte-level, never re-encode wholesale). Repo READ-ONLY, no git write commands.
`python -X utf8`, never `PYTHONIOENCODING`; no command over 300 s; scratch under `D:/Temp/r55/`; deliver a
WHOLE `CANDIDATE_region_ast_generator.py` with `sha256sum | cut -c1-16` plus `FIX_R21-24-M3.md` (sections
0–7; section 5 must show the M1+M2+M3 merged measurement, using `D:/Temp/t30/mkmix.py` to merge whole
candidates by base coordinates and `D:/Temp/t31_hunkpick.py` to apply a subset of hunks onto a moved base).
Judge with `scripts/pyc_verify.py single <abs .pyc> --source <fresh product>`. If your half cannot be closed
without an analyzer change, do NOT edit `region_analyzer.py` — write the finding as the next ticket.
