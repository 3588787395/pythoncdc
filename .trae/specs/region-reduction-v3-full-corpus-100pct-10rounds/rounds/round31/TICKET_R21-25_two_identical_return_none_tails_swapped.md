# R21-25 — `kill_trade_process`: two byte-identical `return None` tails, exits land on the wrong one

Status: **banked, not dispatched** (five engineer slots are busy in round 31). Unassigned unit;
`trade_info_utils 38/41` holds it as its third failure, and it is a *different* mechanism from
R21-21's shared-tail family, which r48a is working.

## 0. Measured shape (from the gate-30 sealed products, 00:26)

`site-packages/IQCommon/util/trade_info_utils.pyc :: kill_trade_process`
`len orig=659 prod=659 delta=0 / hunks=0 landings=2 / judge_diff=True`

The two sides are **the same instruction stream at the same offsets**. The only difference is the operand
of two jumps, and both operands are two adjacent `LOAD_CONST None; RETURN_VALUE` pairs:

| instruction | orig target | product target |
|---|---|---|
| `@3270 LOAD_FAST` / `@3274 POP_JUMP_FORWARD_IF_NONE` (the `is None` test) | `@3864` | **`@3868`** |
| `@3592 LOAD_FAST` / `@3594 LOAD_CONST` / `@3596 COMPARE_OP` / `@3602 POP_JUMP_FORWARD_IF_FALSE` | `@3868` | **`@3864`** |

and the tails themselves are identical in both builds:

    @3856 RERAISE | @3858 COPY | @3860 POP_EXCEPT | @3862 RERAISE
    @3864 LOAD_CONST None | @3866 RETURN_VALUE
    @3868 LOAD_CONST None | @3870 RETURN_VALUE
    @3872 LOAD_GLOBAL NULL + app_log ...        (code continues)

Context that is also byte-identical on both sides: each test is preceded by its own
`POP_EXCEPT / JUMP_FORWARD / RERAISE / COPY / POP_EXCEPT / RERAISE` handler block, i.e. both exits sit
immediately after a `try/except` in the original.

## 1. What this actually asks

Semantically the two tails are the same value (`return None`), so the unit is *not* a content loss. The
judge still says Different, because the CFG pairs predecessors with a specific tail block. So the question
is a **tail-duplication allocation order** question: CPython emits one copy per exit edge, and which copy
each edge gets is determined by the order the compiler processes the exits.

Therefore the fix is not "add a `return None`" and not "change a polarity" (both opcodes already match:
`IF_NONE` for the first, `IF_FALSE` for the second). The fix must change the emitted **source construct
order/nesting** for these two exits so that the `is None` exit is compiled first and gets the first copy.

Prove it with `compile()` before touching the generator: hand-write the two candidate shapes of the
region containing offsets `@3270..@3868` (a `try/except` followed by `if x is None: return`, and the same
exit written so its tail copy is emitted second) and print, for each, the two jump targets. Only a shape
whose table equals `orig` (`@3274→@3864`, `@3602→@3868`) is a candidate rule. This is the same
per-exit-edge duplication family that falsified the handlers `_target` "fold" premise, so expect the
answer to be about which exit is compiled first, not about how many tails exist.

## 2. Census duties (do these before choosing a rule)

1. Is the signature (two identical `LOAD_CONST None/RETURN_VALUE` pairs, exits from an `is None` test and a
   `COMPARE_OP` test, both preceded by their own `POP_EXCEPT/RERAISE` block) present anywhere else in the
   corpus? The `TARGET_ONLY` family is at least 8 units (`get_ipo_stocks`, `api_base.get_history_df`,
   `strategy` — now landed — etc.), but this is a narrow sub-shape; count the units that actually show it
   before claiming a family.
2. Which generator construction emits the two exits here, and in what order? Print the statement list of
   the enclosing region for `kill_trade_process` only.
3. Does any already-landed criterion touch this ordering (`_r2119_or_tail_extension`, the R21-13 veto, the
   R21-14 while/else halves)? If yes, say which, because those three all changed bytes near this file's
   emission and a fourth rule in the same neighborhood must be measured against them, not beside them.

## 3. Acceptance bar

- `kill_trade_process` reads `delta=0 hunks=0 landings=0 judge_diff=False` and the judge reports
  `<module>.kill_trade_process` Equal; `trade_info_utils.pyc` goes 38/41 → 39/41 (NOT a file flip — the
  file's other two units are R21-21's mechanism, and a fix here must leave their shapes unchanged).
- `fly/data/quotation.pyc` 153/153; the 14-file panel counts unchanged:
  `klinedata 64/64`, `strategy 27/27`, `risk_calculation 43/43`, `wizard_quant_api 58/58`,
  `real_quote 45/45`, `order_api 37/37`, `matcher 17/17`, `handlers 29/30`, `api_base 27/28`,
  `quote 91/92`, `realtime_event_source 12/13`, `trade_live_broker 121/128`.
- Because this is a landing-target-only change, judge it with `landings=`, and re-check that you did not
  *rename* the failure: the two R21-21 units must keep `3/1` and `2/0` hunks/landings unless you also fix
  them.
- Fire census over the panel with `cmp` against the sealed products, per file.

## 4. Constraints

Repo read-only; only `core/cfg/region_ast_generator.py` may change (if the answer is an allocation-order
fact the analyzer must declare, write that up as the next ticket instead of editing `region_analyzer.py`);
`python -X utf8`, never `PYTHONIOENCODING`; byte-level CRLF-preserving patches; no command over 300 s;
scratch by absolute path under `D:/Temp/r50/`; deliver `FIX_R21-25.md` (sections 0–7 as usual) plus a whole
`CANDIDATE_region_ast_generator.py` with its `sha256sum | cut -c1-16`, and only if the bar above is met.
