# FIX_T20-3 — merge-landing family (strategy / api_base / trade_live_broker trio / get_tick_direction)

## VERDICT: **FALSIFIED**

No landing-bearing site exists in `region_ast_generator.py`. All four residuals are
**emitted-structure** defects (wrong test polarity + a short-circuit operand demoted into a
nested statement), and the fold that would fix them needs a cross-region block claim, i.e.
`region_analyzer.py` — the file this ticket forbids me to touch. **Zero units moved; zero
criteria landed.** The delivered `region_ast_generator.py` is byte-identical to the landed base
(sha256 `dff6e81a5f2ff9f6…`, md5 `57fb1d0f7beac49bec2fd0b08ef8e408`); `ast_generator_v2.py` was
**not** touched (md5 `d8e127a79ced4431354133e29e15b258`), so nothing is installable from this
deliverable.

Mirror: `D:/Temp/r20m` (`pycdc.py core parsers utils bytecode scripts` + six batteries copied
`cp --parents -r` at identical relative depth; drivers `D:/Temp/r20m/m.py`, `insp.py`, `inp.py`,
`patcher.py`, `diag1..5.py`). Products written only under `D:/Temp/r20m/out`. Live repo read-only;
no git writes; no 402-file gate.

## Stage 1 — unpatched mirror reproduces the sealed baseline (PASS)

| target | mirror reading | sealed |
|---|---|---|
| strategy | `status=failure units=26/27` | 26/27 |
| api_base | `status=failure units=27/28` | 27/28 |
| trade_live_broker | `units=118/128` | 118/128 |
| real_quote | `units=43/45` | 43/45 |
| quotation | `units=153/153` | 153/153 |
| matcher | `units=17/17` | 17/17 |
| order_api | `units=37/37` | 37/37 |

Batteries: `repro RED=9/9` (9R/9 ✓), `arm GREEN=0 RED=3` (0G/3R ✓), `ccneg GREEN=3 RED=1`
(3G/1R ✓), `retbreak GREEN=2 RED=2 DRIFT_VS_BASELINE=0` (2G/2R ✓), `orderapi GREEN=5 RED=0`
(5G/0R ✓), `tail GREEN=13 RED=0` (13G/0R ✓; needs `make_tail.py --run`).

## Stage 2 — per-unit landings at base (measured, `unit_diff.py`)

```
strategy  <module>.Strategy.tick_worker_thread  len orig=288 prod=288 delta=0 hunks=0 landings=4
   @522/@534 POP_JUMP_FORWARD_IF_TRUE  orig ->idx87 (@568)   prod ->idx153 (@820)
   @992/@1004 POP_JUMP_FORWARD_IF_TRUE orig ->idx197(@1038)  prod ->idx263 (@1286)
api_base  <module>.get_history_df               len orig=1881 prod=1881 delta=0 hunks=0 landings=2
   @994  POP_JUMP_FORWARD_IF_TRUE  orig ->idx219 (@1098)  prod ->idx254 (@1254)
   @1006 POP_JUMP_FORWARD_IF_TRUE  orig ->idx210 (@1040)  prod ->idx254 (@1254)
trade_live_broker  _process_tick_order   hunks=0 landings=1  @178 JUMP_BACKWARD  orig->idx22 prod->idx19
                   rzrq_credit_order     hunks=0 landings=1  @2368 JUMP_FORWARD  orig->idx490 prod->idx485
                   get_ipo_stocks        hunks=0 landings=1  @1108 POP_JUMP_IF_TRUE orig->idx225 prod->idx215
real_quote  <module>.RealQuoteData.get_tick_direction  delta=+1 hunks=1 landings=1  (@1022 JUMP_FORWARD)
```
All seven residuals reproduce the ticket's numbers. `get_tick_direction` is still `delta=+1/hunks=1`
at base: I did **not** include the phantom-else criterion of
`rounds/round20/NOTE_T20_ORDERING_WALL.md`, so nothing combines to flip it either.

## Hit-proof for the sites I inspected (proven-inert file log)

Five read-only census loggers were inserted byte-level (CRLF, `\r\n`-joined) into the mirror file
and re-compiled (`py_compile` OK). Inertness proven by `cmp` of the products against the
untouched-tree products:

```
cmp pristine/strategy_prod.py out/strategy_prod.py   -> INERT-S
cmp pristine/api_base_prod.py out/api_base_prod.py   -> INERT-A
```
(The first attempt was NOT inert and `cmp` caught it: a placeholder substitution rewrote
`D:/Temp/...` into `D:/Bemp/...`, the `open()` raised, the generator's broad `except` swallowed it
and the product lost 2444 bytes of `tick_worker_thread`. Reverted, re-proved. Rig trap (e) earned
its keep.)

Measured readings (log lines `NORM`, taken inside `_if_generate_normal` immediately after
`then_stmts = self._if_generate_then_branch(region)`):

```
NORM entry=512 condblk=524 ibc_op=None ibc_blocks=[] merge=568
     cond = UnaryOp('not', BoolOp('or', [dt_strf > '15:15:00', dt_strf < '08:30:00']))
     then_blocks=[536,552,564,562,612,…]  then_stmts[0]=If(test=Compare '11:30:00' < dt_strf < '12:30:00')
NORM entry=992 condblk=992 ibc_op=None ibc_blocks=[] merge=1098
     cond = UnaryOp('not', Name('include'))
     then_blocks=[996,1008,1040,1024,1036,1034]  then_stmts[0]=If(test=UnaryOp('not', Compare _query_date > …))
```

Region census for the same two units (`REG`, all regions owning the chain blocks):

```
strategy : BoolOpRegion entry=512 merge=568 blocks=[512,524] op_chain=[(512,'or'),(524,'or')]
           IfRegion     entry=512 merge=568 cond=524 else=[] then=[536,552,564,562,612,…]  (568 ∉ blocks)
           IfRegion     entry=536 merge=568 cond=536 then=[562] else=[564,612,…]
           IfRegion     entry=350 merge=1286 cond=350 then=[392] else=[512,524,568,536,…]
api_base : IfRegion entry=992  merge=1098 cond=992  else=[] then=[996,1008,1040,1024,1036,1034]
           IfRegion entry=996  merge=1040 cond=996  else=[] then=[1008,1024,1036,1034,…]
           IfRegion entry=1008 merge=1040 cond=1008 then=[1040] else=[1098]
           Region     entry=992 merge=None blocks=[992]
```

Also measured: `_if_generate_elif_chain` is entered **exactly once** for the whole strategy module
(`L19D entry=210`, `ecs=[822]`). The residual elif at 512 (and its twin at 982) is **not** produced
by that function at all — it comes from `_if_generate_normal` for region@512 reached through
region@350's `else` blocks, then upgraded to `elif` by the orelse-elif machinery. So the ticket's
named candidate branch `:19454 elif_jump_target = elif_last.argval` is off-path for this residual.

## Why the ticket's criterion cannot be executed (premise falsified, measured)

1. **`:39406` does not use a declared merge as a jump landing.** The line is
   `merge_offset = region.merge_block.start_offset` (`:39406`) inside
   `def _try_build_and_inner_or_pattern(self, region: 'BoolOpRegion')` (`:39338`). Its three
   uses are all discriminators that *reject* a pattern:
   `:39411 if (li is None or li.argval != merge_offset …): return None`,
   `:39419` (same shape for the `or` members), `:39448 if (li.argval != merge_offset or 'FALSE' not
   in li.opname)`. There is **no assignment of `merge_offset` into any emitted target anywhere in
   the 33 `merge_block.start_offset` reads.** The generator emits an AST; `ast.BoolOp`/`ast.If`
   carry no jump operands, so a jump landing is 100 % emergent from the emitted nesting. A
   "emit the tail jump from the region's declared merge" criterion has no actuation channel in this
   file — #37 landed only because in `bar`/`strategy_universe`/`load_daily` the declared merge
   coincided with an existing statement boundary, so appending `{'type':'Continue'}` was enough.
2. **strategy@512**: the original source is the flat `elif A or B or C:` (`C` = the chained compare
   at 536) whose body is `@568`. The product is `elif not (A or B): if C: …`. `A`'s and `B`'s
   `POP_JUMP_IF_TRUE` therefore *must* land at the enclosing chain's next alternative (820) — with
   the emitted nesting, `->568` is not representable. The only emission giving `->568` is the flat
   three-operand `or`, which requires taking block 536 out of `IfRegion entry=536`'s ownership.
3. **api_base@992**: the original is `if (not include) and (_query_date > pm_close or am_close <
   _query_date <= pm_open): <1040> else: <1098>`. The product is the three-deep nest
   `if not include: if not X: if Y: … else: …`, so `include`'s and `X`'s short-circuit exits are
   forced to the outer skip (1254). The fix needs `region@992` to own `else = [1098]`, which the
   analyzer gives to `region@1008` (its `merge=1040`, `else=[1098]`) — again a cross-region claim.
   `ibc_op=None ibc_blocks=[]` proves `inline_boolop_chains` has no entry for `cond_block` 992 or
   524, so the existing fold at `:20977 _main_ibc` (and the `_disc_chain` fallback at `:21129`,
   which only ever builds `op='and'`) never sees a chain to fold.
4. **broker trio**: each unit differs by exactly one jump target, all landing *earlier* (3/5/10
   instructions). They are inside `for`/loop bodies and the products differ only in which merge the
   emitted arm ends at; like 2–3 above, no landing constant exists to change. Even fully fixed they
   cannot flip `trade_live_broker` (118/128 → at best 121/128), so they cannot satisfy stage 3.

## Stage-by-stage result

* Stage 1 **PASS** (all seven files + six batteries at the sealed values).
* Stage 2 **NOT MOVED** — `strategy landings=4 → 4`, `api_base landings=2 → 2`.
* Stage 3 (landing bar `strategy 27/27` OR `api_base 28/28`) **FAIL** → stop here per the ladder.
* Stage 4 not run: no byte of `region_ast_generator.py` changes from the landed base, so the
  patched arm is byte-identical to the base arm by construction (md5 above). The 19-file panel is
  therefore unmeasured-but-unmoved; the main agent should install **nothing** from this ticket.

## Negative-arm numbers (= base arm, since no criterion landed)

`strategy 26/27, tick_worker_thread hunks=0 landings=4`;
`api_base 27/28, get_history_df hunks=0 landings=2`;
`trade_live_broker 118/128` with the three pure-landing units unchanged;
`real_quote 43/45`, `get_tick_direction delta=+1 hunks=1 landings=1`;
`quotation 153/153`, `matcher 17/17`, `order_api 37/37`; batteries 9R / 0G3R / 3G1R / 2G2R / 5G0R /
13G0R.

## Exact predicate/block that is still wrong

* `core/cfg/region_ast_generator.py` → `_if_generate_normal` condition build
  (`_if_extract_cond_instructions` `:17218` + `_if_extract_condition_from_instructions` and the
  negate step feeding `:21174 self.generated_blocks.add(cond_block)`): it returns
  `UnaryOp('not', BoolOp('or', [b1, b2]))` for `region.entry=512` and `UnaryOp('not', Name)` for
  `region.entry=992`, i.e. it negates a short-circuit chain whose members' exits are the *then*
  body, then leaves the remaining operand (`536` / `1008`) as a nested statement. The block that
  owns the correct structure is the `_main_ibc` fold at `:20977` / the `_disc_chain` fallback at
  `:21129` — both read `region.inline_boolop_chains[id(cond_block)]`, measured `None` here.
* `core/cfg/region_analyzer.py` (not owned by this ticket): `_identify_conditional_regions` builds
  `BoolOpRegion entry=512 op_chain=[512,524]` while stopping before the chained-compare operand
  `536`, and assigns `else=[1098]` to `IfRegion entry=1008` instead of `IfRegion entry=992`
  (`entry=992 merge=1098 else=[]`). Those two ownership facts are the missing fold; the ordering
  wall recorded in `rounds/round20/NOTE_T20_ORDERING_WALL.md` is what prevents a sibling-region
  claim from the generator.

## Banked, reusable facts (do not re-derive)

* `_if_generate_elif_chain` fires once per strategy module; elifs at 512/982 come from
  `_if_generate_normal` + the orelse-elif upgrade, so any elif-chain-only criterion is blind to them.
* `_cond_block_branch_targets` (`:20098-:20128`) is confirmed a (jump, fallthrough) *condition-block*
  extractor, not an arm-tail landing.
* A five-site read-only census logger in the generator is provably `cmp`-inert on strategy **and**
  api_base; reuse `diag1..diag5.py` patterns (`patcher.py` byte-level CRLF insert) for the next ticket.
