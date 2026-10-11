# R21-28 — broker `ipo_stocks_order`: a pure loop back-edge is not emitted (1 deleted `JUMP_BACKWARD`, 3 early landings)

Banked from a read-only pass over the sealed gate-31 bytes. Narrowest un-dispatched broker residual:
`len orig=1181 prod=1180 delta=-1 / hunks=1 / landings=3 / judge_diff=True`. The file is 121/128 with seven
registered mechanisms, so this is a **unit flip (→122/128)**, and r54a is already on `get_ipo_stocks` in the
same file — different unit, do not bundle the two criteria without measuring each alone and together.

## 0. The whole diff, measured

```
== delete orig[717..718 @@3574] prod[717..717]  del=1 ins=0
   - @3574  JUMP_BACKWARD
   ~ orig[466] @2494 POP_JUMP_FORWARD_IF_TRUE  -> idx485 | prod[466] @2494 -> idx475   (10 earlier)
   ~ orig[526] @2812 POP_JUMP_FORWARD_IF_TRUE  -> idx676 | prod[526] @2810 -> idx542   (134 earlier)
   ~ orig[708] @3524 POP_JUMP_FORWARD_IF_FALSE -> idx717 | prod[708] @3522 -> idx717   (same idx, shifted operand)
```

The content stream is otherwise identical: one unconditional backward jump missing, and three forward
condition jumps land on earlier blocks. That is the signature of a **loop whose tail is emitted as straight-
line code**: the back-edge disappears and the blocks that should join the loop header join something before
it. Two previously landed criteria address neighbouring shapes of exactly this family — `#37` (emit the tail
jump from the region's declared merge) and gate 30's R21-18 arm-local `continue` — so before inventing a
rule, check whether the region here reaches those code paths with a declaration that is wrong rather than an
emission that is missing.

Structural fact that constrains the fix: the generator emits an AST that is then `compile()`d, so nothing can
"set a jump target". A landing residual is only fixable by changing the emitted CONSTRUCT (gate 31's
`_r4701_and_lift_or_tail` took a `delta=0 hunks=0 landings=2` unit to `0/0/0` exactly that way) or by fixing
an analyzer declaration. If the diagnosis says analyzer, do not edit `region_analyzer.py` — write it up as
the next ticket.

## 1. Related but NOT the same mechanism (do not merge without proof)

`_trade_status_handle` (`-3/3/2`) shares the missing-`JUMP_BACKWARD` symptom but adds two independent
defects, measured here:

```
== delete orig[7..16 @@46..@90]   9 instructions LOST:
   LOAD_GLOBAL NULL + get_trade_status / LOAD_FAST self / LOAD_ATTR trade_id / LOAD_CONST True /
   KW_NAMES / PRECALL / CALL / LOAD_FAST self / STORE_ATTR trade_info
   i.e. the statement `self.trade_info = get_trade_status(self.trade_id, True)` is not emitted at all.
== insert orig[120..120] 5 instructions EXTRA in the product:
   LOAD_FAST self / LOAD_ATTR trade_status / LOAD_FAST trade_status / COMPARE_OP != /
   POP_JUMP_BACKWARD_IF_TRUE
== replace: orig @872 JUMP_BACKWARD  ->  product LOAD_CONST None / RETURN_VALUE
```

So `_trade_status_handle` = a dropped call statement **+** a loop tail rendered as a function return. A
criterion that fixes only the tail still leaves the first hunk, so it will not flip: plan for two sub-tickets
or state honestly that the unit needs both.

## 2. Acceptance and duties

- Shape target: `ipo_stocks_order` → `delta=0 hunks=0 landings=0 judge_diff=False` and judge Equal
  (122/128). Report the other six broker unit shapes before/after: `_process_order −465/4/1`,
  `_process_cancel_order −293/3/0`, `_sync_worker −3/5/6`, `_trade_status_handle −3/3/2`,
  `etf_purchase_redemption −12/5/0` (R21-27), `get_ipo_stocks 0/0/1` (r54a's).
- Census the predicate corpus-wide before calling anything a family; report `TOTAL_FIRES` over the
  **20-file** panel (`python -X utf8 D:/Temp/t30/panel14.py <root> <tag> 0 20`), whose last six entries are
  the duplicated-module canaries `arg_checker`×3 (49/39/43) and `profiler_func`×3 (17/15/18) — a −6-unit
  merge passed a 14-file panel at gate 31 and only the gate saw it.
- Prove the emission site by ablation (stub the candidate construction to return `None` in the process that
  produces the artifact) and `cmp`-prove any probe inert per target; an empty probe log is a broken rig.
- Mirror: copy `pycdc.py core parsers utils bytecode scripts` + `unit_diff.py` at the same relative depth to
  `D:/Temp/r57/wt`; sealed generator `37d9fecb893704ac`, analyzer `35e227ac3e7b25af`; prove fidelity by
  regen + `cmp` against the committed `trade_live_brokerOK.py` before measuring anything.
- Repo READ-ONLY, no git write commands, only `core/cfg/region_ast_generator.py` may change,
  `python -X utf8` and never `PYTHONIOENCODING`, byte-level CRLF-preserving patches, nothing over 300 s,
  judge with `scripts/pyc_verify.py single <abs .pyc> --source <fresh product>`. Deliver a whole
  `CANDIDATE_region_ast_generator.py` + `FIX_R21-28.md` (sections 0–7).
