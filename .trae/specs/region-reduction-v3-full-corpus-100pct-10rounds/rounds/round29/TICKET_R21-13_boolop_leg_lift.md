# TICKET R21-13 (round 29) — stop lifting one leg of an `or` chain into the enclosing test

Owner file (the ONLY file you may modify, and only inside your mirror):
`core/cfg/region_ast_generator.py`
Sealed hashes of the read-only twins (re-verify in your mirror at copy time):
`region_ast_generator.py = ac8ec5aa2d5796ea`, `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`.
Repo (read-only): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `20d94605`.
Products only under `D:/Temp/r29/out/`. **No git writes of any kind.**

## 0. The mechanism, already measured for you (do not re-derive, do not re-litigate)
Two residual units fail with the *same* shape: `delta=+2`, one hunk = a trailing
`LOAD_CONST None; RETURN_VALUE` pair, and exactly one jump whose target moved to that pair.
In both cases the generator took an inner short-circuit test `A or B` whose legs share ONE
then-body and **lifted leg A into the enclosing condition (negated) instead of reconstructing
the whole `or` chain as the inner test.** That leaves the lifted leg's exit with no copy of the
shared body to land on, so CPython threads it to the function/suite-tail implicit `return None`
and materializes a second `LOAD_CONST None; RETURN_VALUE` pair.

### victim 1 — `IQCommon/strategy/wizard_quant_api.pyc` :: `<module>.filter_desicion` (file 57/58)
original source shape (derived from the pyc, idx173-194):
```python
    elif filter_type == 'short_status':
        if short_values is None or long_values is None:
            return None
        return down_v_desicion(short_values[-1], long_values[-1])
```
emitted product (wizard_quant_apiOK.py:93-97) — leg A lifted into the elif test:
```python
    elif filter_type == 'short_status' and short_values is not None:
        if long_values is None:
            return None
        else:
            return down_v_desicion(short_values[-1], long_values[-1])
```
byteprint: `@704 POP_JUMP_FORWARD_IF_NONE` targets idx181 (`LOAD_CONST None @710`, the shared
then-body) in the original but idx195 (`LOAD_CONST None @774`, the appended tail) in the product.
Behaviour is the same; **layout is not**, and the judge compares layout.

### victim 2 — `IQData/plugins/plugin_system_realquote/real_quote.pyc` :: `<module>.RealQuoteData.get_real_minute_kline` (file 44/45)
original shape (idx99-104 + the continuation):
```python
            if fq is None or ex_info is None:
                return kline
            names = list(kline.dtype.names[1:])   # continuation stays at the same suite level
```
emitted product (real_quoteOK.py:386-390) — leg A became a whole enclosing `if`:
```python
            if fq is not None:
                if ex_info is None:
                    return kline
                else:
                    names = list(kline.dtype.names[1:])
```
byteprint: `@572 POP_JUMP_FORWARD_IF_NONE` → idx103 (`LOAD_FAST kline; RETURN_VALUE`) in the
original, → idx251 (`LOAD_CONST None @1312`) in the product. **This one is also semantically
wrong** (fq is None now returns None instead of kline), so it is the stronger proof.

## 1. What to change
The rule to implement: when a condition chain's legs share one then-body (the `or` form), the
test must be reconstructed as the FULL `or` chain on the inner `If` and the continuation must
stay sequential — never lift a leg into an enclosing `If.test` (as `and not leg`) and never
synthesise an enclosing `If` around it. Locate the site that produces the lift by *ablation over
the two victims' regions*, not by print markers; candidate names to start from:
`_if_extract_condition_from_instructions`, `_if_generate_elif_chain`, `_if_generate_normal`,
`_generate_chain_condition`, and any `BoolOp`/`or` assembly helper reachable from them.
The analyzer data you may READ (not modify): `inline_boolop_chains`, `IfRegion.elif_chain`,
`merge_block`, `then_blocks`/`else_blocks`.

## 2. Acceptance (hard, measured — report the literal rig lines)
Rig: `python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py <pyc-rel> <qualname> --all`
- `filter_desicion` must become `len orig=195 prod=195 delta=0 hunks=0 landings=0 judge_diff=False`
  ⇒ file `wizard_quant_api` 57/58 → **58/58 (file flip)**.
- `get_real_minute_kline` must become `len orig=279 prod=279 delta=0 hunks=0 landings=0 judge_diff=False`
  ⇒ file `real_quote` 44/45 → **45/45 (file flip)**.
- Judge both products with `scripts/pyc_verify.py single <abs pyc> --source <your product>`; both
  must print `Equal` for those qualnames.
- Landing both is NOT required; landing ONE is enough (one file flip), but say plainly which.

## 3. Anti-regression duties (all mandatory, run them BEFORE you deliver)
1. **Fire census**: instrument the criterion to count fires over the 14-file panel
   (`fly/data/quotation.pyc`, `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`).
   Report `TOTAL_FIRES` and the per-file product `cmp` result vs the sealed product.
   A criterion that fires on >3 files AND changes their products is a broad relax — narrow it or
   deliver it as a negative result. (History: a broad relax on this campaign cost −20 units.)
2. `fly/data/quotation.pyc` must stay **153/153**.
3. The two other sole-unit files must not regress: `handlers` 29/30, `klinedata` 63/64,
   `trade_info_utils` 38/41, `strategy` 26/27, `api_base` 27/28, `order_api` 37/37, `matcher` 17/17.
4. Probes must be `cmp`-proved inert per target or the reading is VOID; an empty probe log is
   SUSPECT, not a negative (log the exception text; never wrap the probe body in a bare except).
5. Reproduce codegen decisions by **compiling candidate sources** on this interpreter
   (Python 3.11.7), not by arguing. I already falsified two cheap transforms that way: dropping
   the `else:` when the then-arm returns, and flipping `not x is not None` → `x is None`, and
   adding/removing a final `else: return None` — all four variants compile byte-identical (43
   instructions in my 2-arm mini), so they are NOT the mechanism. Do not spend your run on them.

## 4. Deliverable
`D:/Temp/r29/DELIVER/FIX_R21-13.md` (sections: mirror proof, baseline reproduction, 取证 of both
victims' sites, criterion, fire census, stage readings, negative evidence, final declaration) plus
`D:/Temp/r29/DELIVER/CANDIDATE_region_ast_generator.py` ONLY if the acceptance test is met on your
mirror with no panel regression. If it is not met, deliver the diagnosis and say FALSIFIED — a
measured negative with the census is accepted and banked; a silent no-op is not.
