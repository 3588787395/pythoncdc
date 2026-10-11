# R21-33 (pre-digested, round 35) — broker `_trade_status_handle`: the FIRST statement of a fused loop-header block is dropped

Measured 2026-10-11 ~17:15 on the **gate-34 sealed base** (generator `065e4d77243190dc`,
`trade_live_broker.pyc` 123/128). Victim shape:

```
len orig=127 prod=124 delta=-3  hunks=3  landings=2  judge_diff=True
== delete orig[7..16 @@46..@@90]   del=9 ins=0     ← hunk 1: a whole statement missing
== insert orig[120..120 @@830..@-] prod[111..116]  del=0 ins=5
== replace orig[126..127 @@872..@@872] prod[122..124]  del=1 ins=2
```

## 0. Hunk 1 is a statement loss, not a shift

Original instructions `@46..@90` disassemble to exactly one Python statement:

```
@46 LOAD_GLOBAL get_trade_status / @58 LOAD_FAST self / @60 LOAD_ATTR trade_id /
@70 LOAD_CONST True / @72 KW_NAMES / @74 PRECALL 2 / @78 CALL 2 /
@88 LOAD_FAST self / @90 STORE_ATTR trade_info
```
i.e. `self.trade_info = get_trade_status(self.trade_id, True)`.

The emitted product (`trade_live_brokerOK.py:894-899`) goes straight from
`engine.set_engine(engine)` to `trade_status = self.trade_info[2]`, so the statement is **never rendered**.
That is a real behaviour loss, not an offset shift.

## 1. Why it vanishes — the block it lives in is the loop header

Read-only CFG/analyzer census of the unit (`forensics`-style, no generation):

```
block @46  n=20  term=POP_JUMP_FORWARD_IF_FALSE  role=BlockRole.LOOP_HEADER
           entry_region=LoopRegion  owner=LoopRegion
LoopRegion hdr=46 cond=46 init_blocks=[] pre_condition_blocks=[] else=[720, 830]
           body=[46, 150, 186, 296, 318, 340, 452, 474, 680, 722]
```

`get_block_by_offset(46 / 88 / 100 / 112)` all return **the same block**: CPython fused three statements
into one maximal straight-line block —

1. `self.trade_info = get_trade_status(self.trade_id, True)`   (@46..@90) **← dropped**
2. `trade_status = self.trade_info[2]`                          (@100..@~118) **← emitted**
3. the loop condition test `self.trade_status != trade_status`   (block terminator) **← emitted as `while`**

So the defect is not in region formation (the region is the loop header and that is correct) but in the
header-prefix renderer, which consumes the prefix and keeps only the **last** statement before the
condition. **Named site:** `RegionASTGenerator._loop_process_header_instructions`
(`core/cfg/region_ast_generator.py:12722`; the collected prefix is flushed by
`body_stmts.extend(_hdr_stmts)` at `:12915`). Start by counting how many statements the prefix walk
produces for this block — one emitted from two present is the signature.

Do not confuse this with `pre_condition_blocks`: it is a *block*-level list (analyzer
`region_analyzer.py:518`, only read at `:5368` as a jump-target guard, consumed at generator `:12923`),
and it is empty here because the prefix is intra-block, not a separate block.

## 2. The flip needs a second, independent mechanism (do not promise hunk 1 alone)

Hunks 2 and 3 are the loop-tail family already documented in
`rounds/round32/TICKET_R21-28_broker_loop_tail_not_emitted.md` §1: the original's `@872 JUMP_BACKWARD` is
rendered as `LOAD_CONST None / RETURN_VALUE`, plus a 5-instruction `POP_JUMP_BACKWARD_IF_TRUE` insert at
`@830`. A criterion that only restores hunk 1 leaves `−3 → 0` at best with hunk 2/3 still open, i.e.
**no unit flip**. Split the ticket accordingly: fix A = hunk 1 (this note), fix B = the loop-tail
rendering; the acceptance bar is `delta=0 hunks=0 landings=0 judge_diff=False` (broker 123 → 124/128).

## 3. Method requirements carried over from R21-28 (this round's lesson, measured)

- Measure the candidate on the **20-file panel** before the gate:
  `python -X utf8 D:/Temp/t30/panel14.py <mirror_root> <tag> 0 20`. This round's v1 candidate
  (interior-only conjunct) looked like a clean +1 on the victim file and was caught only by the panel
  (`quote 91→90`, `real_quote 45→44`, net −1) — see `rounds/round34/PANEL_R34.md`.
- A criterion that adds/keeps a statement must be checked against **payload-carrying vs payload-free**
  sites and against the region's own declared `back_edge_block(s)`; R21-28's three own-data conjuncts are
  the template (`rounds/round34/FIX_R21-28_r34.md` §4).
- Census the qualifying population corpus-wide over the 402-file verification face before claiming any
  family; the read-only rig `rounds/round34/census_r34_loop_tail.py` is the pattern (it prints
  hits/terminal/interior/qualifying and can be filtered by filename).
- Mirror: reuse `D:/Temp/r30chk` (holds the landed generator; pristine copy of every base edit goes to a
  content-addressed file in scratch before patching). Repo read-only for measurement; only
  `core/cfg/region_ast_generator.py` may change unless the diagnosis proves analyzer-side, in which case
  write it up rather than editing both files in one round.
- `python -X utf8`, never `PYTHONIOENCODING`; byte-level CRLF-preserving patches; nothing over 300 s;
  judge a fresh product with `scripts/pyc_verify.py single <abs pyc> --source <product>`.
