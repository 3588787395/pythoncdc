# Round 47 — DIAGNOSE: `site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc`

Scratch: `D:/Temp/r47diagA`. Arm: `D:/Temp/r43gate/mirr_r47aA` (only arm created by this round).
Repo untouched (`core/` shas re-verified below).

## 0. Headline

The two deficits are **two independent, unrelated defects that only share a file**.
`trade_logs_control` (189/190, one EXTRA instruction) is an *emission* hole and is
**flipped by one same-level predicate** (candidate **R47-A**, `_loop_handle_no_exit_successors`):
the loop-header conditional jump's "else" arm is in fact the then-arm's **fall-through
successor**, so folding it into `else:` requires inventing a `JUMP_FORWARD` that the
bytecode does not contain. Official: **8/10 → 9/10**, `lost=0`, `broken=0`, and the
**sha-change face over all 544 corpus paths is exactly 1 product**.
`setup` (320/253, 65 missing) is **not** a region-reduction hole: no block is unemitted —
three *statement prefixes* of `TernaryRegion` cond/merge blocks are swallowed by the
expression-stack carry. R47-A leaves `setup` byte-identical. The file therefore stays
9/10 (one function short), and the file cannot flip this round.

Measured against CURRENT landed bytes (`region_ast_generator.py` `b8bfc794dc6c852e7d9c`,
len 3 000 351, CRLF 48 620, bare LF 0, BOM present; `region_analyzer.py`
`55a9f61b9b0703063d44`; HEAD `7a17aeca`), by my own re-run — not from old notes.

## 1. Relation between the two functions

None, except that both live in `DefaultLogger` and both report `jump_diffs=1`.

* Official (re-measured, `scripts/pyc_batch_verify.py single`) — identical to the mirror
  harness `--arm=landed` row:

```
  matched_functions: 8
    - setup: orig=320 decomp=253 jump_diffs=1 true_diffs=293
      first_diff: {'index': 25, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': 'os', 'decomp_arg': 'LOG_SWITCH'}
    - trade_logs_control: orig=189 decomp=190 jump_diffs=1 true_diffs=144
      first_diff: {'index': 42, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'JUMP_FORWARD', 'orig_arg': 'os', 'decomp_arg': 420}
```

* `setup` is a **deletion** (65 instructions net never emitted); `trade_logs_control` is an
  **insertion** (exactly one `JUMP_FORWARD`, everything after it merely shifts by 2 bytes —
  all 144 `true_diffs` and the single `jump_diffs` are that one instruction's shadow).
* A difflib edit script over the strict ruler's token sequences proves the second point:
  `trade_logs_control` has **exactly one** non-shift edit —
  `INSERT orig[43:43] decomp[43:44] DECOMP first=('JUMP', 420)` — every other row is
  `EQUAL` or a jump-target `REPLACE` of the same opname (`_r10` counts, 193 vs 194).

## 2. Root cause with structural evidence

### 2a. `trade_logs_control` — SHIPPABLE shape (R47-A)

Original bytecode (`blocks.py`, index ranges in the strict ruler's filtered sequence):

```
B12  idx[36]    term=POP_JUMP_FORWARD_IF_FALSE 294   succ=[B232(fall), B294(jump)]
B232 idx[37:43] term=STORE_FAST norm_log_size        succ=[B294]      <-- PURE FALL-THROUGH
B294 idx[43:49] term=POP_JUMP_FORWARD_IF_FALSE 418   succ=[B356, B418]
```

i.e. source is `if exists(norm): sz=…` **then, sequentially,** `if exists(sys): sz=…`
(CPython emits `PJF → B294` and B232 simply falls into B294; there is **no**
`JUMP_FORWARD` over the second test, which a real `elif` would require).

Ownership (`probe45e`, read-only monkeypatch of `RegionAnalyzer.analyze`):
`B12`, `B232`, `B294` are all owned by the single `LoopRegion WHILE_LOOP entry=B12`;
`B294` is additionally the entry of a *sibling* child `IfRegion IF_THEN entry=B294 exit=B418
merge=B418`. So the correct rendering is two flat sibling regions inside the loop body
(principle 4: the loop references `B294` by its entry).

Instead the header path swallows `B294` as the *else arm* of `B12`. Emission trace
(`trace47.py`, wraps all 236 methods and reports the first completed result — or
mutated argument list — holding the shape):

```
HIT  _loop_handle_no_exit_successors   arg0=BasicBlock entry=      ret=NoneType argscan=A
HIT  _loop_process_header_break_condition  arg0=BasicBlock entry=B12 ret=NoneType argscan=A
HIT  _loop_process_header_instructions     arg0=BasicBlock entry=B12 ret=NoneType argscan=A
HIT  _loop_handle_header                   arg0=BasicBlock entry=B12 ret=NoneType argscan=A
HIT  _loop_dispatch_block                  arg0=BasicBlock entry=B12 ret=bool   argscan=A
HIT  _loop_postprocess                     arg0=LoopRegion   entry=B12 ret=NoneType argscan=A
```

`_loop_handle_no_exit_successors` (`core/cfg/region_ast_generator.py:9955`) picks the arms by
polarity only — `_is_if_false ⇒ _then_succ=_fall_through, _else_succ=_jump_block` — and ends
unconditionally with

```
_hdr_stmts.append({'type': 'If', 'test': _expr, 'body': _then_stmts, 'orelse': _else_stmts})
```

after having generated `_else_stmts` **as a region** (`_generate_region(IfRegion@B294)`) and
marked `B294` emitted. `If(body, orelse=[If(...)])` is what unparse renders as `if/elif`, and
`py_compile` must then emit the missing `JUMP_FORWARD` — the one extra instruction.
`_r10` strict: `seq_len orig=193 decomp=194`.

Violated principle: **1** — `B232`'s single terminator is `STORE_FAST`, i.e. a fall-through;
the emitter pretends it is an unconditional jump, which is exactly "a block with one
terminator it does not have". Nothing is unemitted, so principles 2/4 are only reached
*after* the fix (the loop body then owes `B294` again).

### 2b. `setup` — NOT a region-reduction hole (no admissible predicate found)

All 65 vanished instructions live in **three statement prefixes**:

| block | byte-offset range | instructions | prefix never emitted |
|---|---|---|---|
| `B176` | idx 25..76 | 52 | 48 (3 full `os.path.join` assignments + `LOAD RotatingFileHandler / self.info_backtest_path / 10485760`) |
| `B688` | idx 82..94 | 13 | 9 (`'UTF-8' True KW_NAMES CALL 5 STORE_FAST info_backtest_handler`, 2nd handler's prologue) |
| `B800` | idx 100..126 | 27 | 4 + 5 (`'UTF-8' True KW_NAMES CALL 5`; `info_backtest_sys_handler = LogEngine.add_async(...)`) |

`48 + 9 + 9 = 66` deleted, `1` inserted (`BUILD_TUPLE`) ⇒ net **65**, matching the ruler.
Every one of these blocks *is* emitted — only its **terminator-carrying tail** survives, so
**no region fails 原则 2** and the R45-A/R46-B family does not reach it. The blocks involved
are precisely the cond/merge blocks of the two `TernaryRegion`s:

```
TernaryRegion TERNARY entry=B176 cond=B176 merge=B688 blocks=[B176,B646,B686]
TernaryRegion TERNARY entry=B688 cond=B688 merge=B800 blocks=[B688,B758,B798,B800]
IfRegion IF_ELIF_CHAIN entry=B112 exit=B646 merge=B646   <-- merge is an INTERIOR block of
   blocks=[B112,B176,B686,B688,B758,B798,B800,B994,...]      the first ternary, not its entry
      (B646 not in chain.blocks; block_to_region[B646]=TernaryRegion(B176))
```

The source is `h = RotatingFileHandler(path, 10485760, int(BACKTEST_LOG_CONTROL) if … else 102400, 'UTF-8', True)`
— a call whose **argument list is split across the ternary's region boundary**: the queue of
pending operands lives in the cond block's *prefix*, the `CALL` lives in the merge block.
The ternary is emitted as a value node, the pending operand queue is discarded, the two
orphaned ternary values are then collected by the next `STORE_FAST` into a tuple.

Reproduced synthetically on **landed bytes** (`w47_ternary.py`, plain `.py`, no corpus data),
including the exact `h2 = (cond, cond)` artifact and the same "second store target wins"
detail:

```
<module>.t47_10_ternary_in_call_args orig=69 decomp=37 seq_len orig=69 decomp=37
<module>.t47_11_ternary_plain        orig=17 decomp=17 OK ok
<module>.t47_12_ternary_after_statements orig=24 decomp=24 OK ok
```

`t47_11` (one ternary in a call) and `t47_12` (statements then one ternary call) stay clean —
the defect needs **two consecutive calls each carrying a conditional expression**, exactly the
`setup` shape. The discriminating fact is "this block's instruction stream ends *mid-*expression*
(stack depth > 0 at the block boundary)", which is not a block-identity / ownership / region-role /
successor / **terminator**-opcode-class fact. It is `ExpressionReconstructor` /
operand-stack territory ⇒ **no same-level predicate for `setup` was found; reported as such.**

## 3. ONE same-level predicate — R47-A

File `core/cfg/region_ast_generator.py`, method `_loop_handle_no_exit_successors`
(`:9955`), inserted immediately before the unique line
`                if _else_is_continue:` (guard at 16-space depth, i.e. inside
`if _cond_instrs: / if _expr:`), so it runs **before** the else arm is generated:

```python
                _r47_ter = self.region_analyzer.get_entry_region_for_block(_then_succ)
                _r47_loop = self._current_loop
                _r47_last = _then_succ.get_last_instruction()
                if (not _then_is_continue and _else_succ is not None
                        and _else_succ is not block
                        and _else_succ in (list(_then_succ.successors) or [])
                        and _r47_last is not None
                        and _r47_last.opname not in FORWARD_JUMP_OPS
                        and _r47_last.opname not in BACKWARD_JUMP_OPS
                        and (_r47_ter is None or _r47_ter.entry is not _then_succ)
                        and _r47_loop is not None
                        and _else_succ in (getattr(_r47_loop, 'blocks', None) or set())
                        and _else_succ not in self.generated_blocks):
                    self.generated_blocks.add(_then_succ)
                    self.generated_offsets.add(_then_succ.start_offset)
                    _hdr_stmts.append({'type': 'If', 'test': _expr, 'body': _then_stmts})
                    return
```

Which conjunct reads which structural fact:

| conjunct | structural fact read | kind |
|---|---|---|
| `not _then_is_continue` | arm role already computed by the pre-existing `BlockRole`-based continue predicates | block role |
| `_else_succ is not None`, `_else_succ is not block` | block identity (`is`), the jump target is not the header itself | block identity |
| `_else_succ in _then_succ.successors` | **pred/successor relation** | successor |
| `_r47_last.opname not in FORWARD_JUMP_OPS \| BACKWARD_JUMP_OPS` | **terminator opcode CLASS** (the two module-level frozensets already imported at `:138`, no new opcode list) — a non-jump terminator means its only successor is the **fall-through** successor | terminator class |
| `_r47_ter is None or _r47_ter.entry is not _then_succ` | ownership: the then arm is a plain block, not a nested region entry, hence `_then_succ` **is** the arm's tail block | ownership / region entry |
| `_else_succ in _r47_loop.blocks` | the "else" candidate is still a body block of the enclosing loop region ⇒ an owning region exists that will emit it | ownership (`region.blocks`) |
| `_else_succ not in self.generated_blocks` | it has not been emitted yet ⇒ emission duty is genuinely still open | block identity / emitted set |

Consequence: emit `If(test, body)` with **no `orelse`**, mark only `_then_succ`, and
**return without touching `_else_succ`** so the loop body's sequential reduction picks it up
by its entry (principles 2 and 4). Nothing is renamed, no offsets/counts/constants/names are
read, no history list is consulted.

Negative-shield reasoning (why real `else`/`elif` cannot match): a genuine else arm's then
block must *jump over* the else arm, so either its terminator is an unconditional forward jump
(conjunct 4 false) or its successor set does not contain `_else_succ` (conjunct 3 false).

Where it fires on the corpus (exact numbers): file
`site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc`, function
`<module>.DefaultLogger.trade_logs_control` — official row `[189, 190, 1, 144]`
**disappears**; `matched_functions 8 → 9` of 10; strict
`seq_len orig=193 decomp=194` → `None 'ok'` (arm product signature
`fae0d0a84cead854` **equals** the original code object's signature).

## 4. Gates measured

Byte preflight (this round):

```
b8bfc794dc6c852e7d9c len 3000351 CRLF 48620 bareLF 0 BOM True   # landed generator
2a3d522b0ec9e8fe66e4 len 3003323 CRLF 48654 bareLF 0 BOM True   # mirr_r47aA generator
```

**G0 synthetic witness** — `python -X utf8 D:/Temp/r47diagA/g047.py r47aA`
(9 code objects: 2 witnesses of the shape + 7 controls):

```
<module>.w47_01_two_ifs_in_while              eeb4b190d43dac7a 0e24a1abc15a8b94 *** DIFFERS ***
<module>.w47_02_true_else_in_while            46735e45888f87aa 46735e45888f87aa IDENTICAL
<module>.w47_03_true_elif_in_while            9c22d7bbe5336d2e 9c22d7bbe5336d2e IDENTICAL
<module>.w47_04_two_ifs_at_func_level         7691ff53bfd8a542 7691ff53bfd8a542 IDENTICAL
<module>.w47_05_two_ifs_in_for                e5efce8a2fa3089c e5efce8a2fa3089c IDENTICAL
<module>.w47_06_two_ifs_in_cond_while         1d66c95f04fee882 1d66c95f04fee882 IDENTICAL
<module>.w47_07_then_arm_multi_block_in_while 5645146766540f7e 5645146766540f7e IDENTICAL
<module>.w47_08_three_sequential_ifs_in_while facb2e7e6a6d0e2a 5700ebbea89a7093 *** DIFFERS ***
n=9 identical=7 differs=2
defective[landed]=3/9  [['<module>.w47_01_two_ifs_in_while', 'seq_len orig=35 decomp=36'], ['<module>.w47_07_then_arm_multi_block_in_while', 'seq_len orig=44 decomp=45'], ['<module>.w47_08_three_sequential_ifs_in_while', 'seq_len orig=45 decomp=46']]
defective[r47aA]=1/9   [['<module>.w47_07_then_arm_multi_block_in_while', 'seq_len orig=44 decomp=45']]
```

witness product, landed (wrong `elif`) vs arm (correct siblings):

```
-        elif os.path.exists(s):          # landed:  folds the sibling if into an elif
+        if os.path.exists(s):            # r47aA:   two flat sibling ifs
```

Residual disclosed: `w47_07` (then arm is itself a nested if/else, so conjunct 5 is false)
stays defective on both sides — it is a **different sub-shape** and is not claimed.

**G1 target + 27-file partially-failing pool** —
`python -X utf8 r43g.py run --arm=r47aA --list=…/rounds/round46/g1pool46.txt --out=D:/Temp/r47diagA/o_g1.jsonl`
then
`python -X utf8 tally43.py …/rounds/round46/g1_r46bB.jsonl D:/Temp/r47diagA/o_g1.jsonl`:

```
UP   __init__.pyc                           8/10 -> 9/10
SUM files=27 same=26 gained=1 lost=0
```

**G2′ test_repros battery (143)** — a-side `bat45.jsonl` (landed-equivalent per Round 46):

```
SUM files=143 same=143 gained=0 lost=0
```

**G3 anchors (109)** — a-side `anch45.jsonl`:

```
SUM files=109 same=109 gained=0 lost=0
```

**G4 full A/B, 544 paths (shipping authority)** —
`r43g.py run --arm=r47aA --list=r45full.txt --nshard=3` (544 rows) vs
`…/rounds/round46/g4bB_all.jsonl`:

```
UP   __init__.pyc                           8/10 -> 9/10
SUM files=544 same=543 gained=1 lost=0
```

sha-change face across all 544 products (`changed47a.txt`):

```
a rows 544 b rows 544 missing-in-a 0
sha-changed products = 1
   site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc 8 -> 9
```

**G4′ strict ruler over the changed face** — `python -X utf8 g4prime43.py D:/Temp/r47diagA/changed47a.txt r47aA`:

```
== IQEngine/plugins/plugin_system_log/__init__.pyc  strict-defective a=2 b=1
   FIXED   <module>.DefaultLogger.trade_logs_control   [seq_len orig=193 decomp=194]
G4-prime affected=1 fixed=1 broken=0 changed=0
```

Per-code-object signature table (orig / landed / arm) — proves `setup` is not perturbed:

```
<module>.DefaultLogger.setup                  90fccfb5e6343d61 e872776252a65530 e872776252a65530 both differ  arm==landed
<module>.DefaultLogger.trade_logs_control     fae0d0a84cead854 497642640b335851 fae0d0a84cead854 ARM FIXED    arm!=landed
   (the other 8 code objects: all three signatures equal)
```

## 5. Falsified leads (with numbers)

1. **FALSIFIED — "`setup`'s 65 missing instructions are a 归属者不发射 hole of the
   R45-A/R46-B family".** `setup`'s chain `merge_block=B646` is indeed not in the chain's
   blocks and is owned by `TernaryRegion(entry=B176)`, but **all 4 of `B646`'s instructions are
   present in the product**, and *no* block of `setup` is wholly unemitted. R46-B's conjunct ③
   (`owner.entry is the merge block`) is false here (`owner.entry = B176 ≠ B646`), and the
   R45-A bare-statement path already emits `B646` correctly. `setup`'s loss is 3 statement
   prefixes (48 + 9 + 9), not a region.
2. **FALSIFIED — "one predicate can cover this cluster".** R47-A leaves `setup`'s code object
   byte-identical to landed (`e872776252a65530` on both arms) and its official row unchanged
   at `[320, 253, 1, 293]`. The file stays 9/10: it does **not** flip.
3. **FALSIFIED — "`trade_logs_control 189/190` and the ledger's equal-length row
   `write_logging_thread 113/113 j1` (`fly/logger.pyc`, the R46-C1 line) are the same cluster".**
   R47-A leaves `fly/logger.pyc` at `28/30` with row `['write_logging_thread', 113, 113, 1, 40]`
   **byte-identical in sha** to the a-side. Different mechanism (loop-body MOVE, not an inserted
   jump); R47-A neither fixes nor disturbs it.
4. **FALSIFIED — "`flyAccount :: init_connection 42/41` (Round 46 line D) is nearby".** Its row
   `['init_connection', 42, 41, 0, 25]` is unchanged on the arm (pool file `flyAccount.pyc`
   `21/23` on both sides). Line D remains a two-layer (analysis + emission) problem, untouched here.
5. **FALSIFIED (self) — "the extra jump comes from `_loop_postprocess` / an epilogue duplicate".**
   The trace's creator of the `If(..., orelse=[If(...)])` node is
   `_loop_handle_no_exit_successors`; `_loop_postprocess` only *propagates* it (its arg scan
   hits, its body does not create it), and the single edit row is `INSERT …('JUMP', 420)`.
6. **OPEN lead handed over — `setup`.** A 3-code-object synthetic battery (`w47_ternary.py`)
   reproduces it on landed bytes at `strict seq_len orig=69 decomp=37` with the same
   `(cond, cond)` tuple artifact, with two clean negative controls (`17/17`, `24/24`).
   Fixing it needs an operand-stack-carry predicate in `ExpressionReconstructor`/block
   statement emission ("the block's instruction stream ends with a non-empty pending operand
   queue"), i.e. **outside the same-level doctrine**; also worth a look:
   `region_analyzer` letting `IF_ELIF_CHAIN@B112` take `merge_block=B646` that is an
   *interior* block of a descendant `TernaryRegion` (B646 ∉ chain.blocks, chain.exit=B646).

## 6. SHIP / DO NOT SHIP

**SHIP R47-A.** Deciding number: **official `matched_functions` 8 → 9 on this file, and over the
full 544-path A/B `gained=1 lost=0`, `SUM files=544 same=543 gained=1 lost=0`, with a sha-change
face of exactly 1 product and G4′ `broken=0`.**

Supporting: G0 witness defective 3/9 → 1/9 with 7/9 controls byte-identical; G2′ 143/143 same;
G3 109/109 same. The blast radius (one product out of 544) makes over-firing implausible — this is
the narrowest change face seen in the program so far, in the same class as Round 46's shipped
`same=543 gained=1 lost=0`.

Caveats to record: (a) `plugin_system_log/__init__.pyc` reaches only 9/10, so the *file* does not
flip this round; (b) witness `w47_07` (nested if/else as the then arm) is a sibling sub-shape still
defective on both sides; (c) landing must preserve the UTF-8 BOM and CRLF (arm verified:
CRLF 48 654, bare LF 0, BOM True, +34 lines / +2 972 bytes).

## 7. Artifacts

Mine (scratch, `D:/Temp/r47diagA/`): `dumpfn.py`, `blocks.py`, `editscript.py`, `probe47.py`
(copy of `probe45e.py`), `trace47.py`, `trace_setup.py`, `g047.py`, `mkspec47.py`,
`spec_r47a.json`, `w47_witness.py` (= `r47a_witness.py`), `w47_ternary.py`,
`g0_landed.json` / `g0_r47aA.json`, `g0prod_*.py`, `b_setup.txt`, `b_tlc.txt`, `d_setup.txt`,
`d_tlc.txt`, `e_setup.txt`, `e_tlc.txt`, `p_setup.txt`, `p_tlc.txt`, `t_tlc.txt`, `t_tlc2.txt`,
`ts_setup.txt`, `tgt.txt`, `changed47a.txt`, `o_landed.jsonl`, `o_r47aA.jsonl`, `o_g1.jsonl`,
`o_g2.jsonl`, `o_g3.jsonl`, `o_g4_s{0,1,2}.jsonl`, `o_g4_all.jsonl`, `runG.sh/.log`, `runG4.sh/.log`.

Shared dir `D:/Temp/r43gate/`: **`mirr_r47aA`** only (plus the harness's own
`build_r47aA` products). No other agent's directory was read; the Round-46 a-side baselines used
are the **committed repo copies** under
`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round46/`
(`g1pool46.txt`, `g1_r46bB.jsonl`, `g4bB_all.jsonl`, `g0_r46.py`).
