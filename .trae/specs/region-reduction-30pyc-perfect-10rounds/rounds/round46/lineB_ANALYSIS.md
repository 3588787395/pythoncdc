# Round 46 line B — DIAGNOSE ONLY: the "chain merge block is the ENTRY of the following sibling region" hole

No file under `F:/Downloads/pythoncdc-main/core/` was read-modified; the worktree is untouched
(`git status` clean for `core/`). All artifacts live here or in new `mirr_r46b_*` arms under
`D:/Temp/r43gate`. Strict ruler = repo-root `_r10_strict_check.py` (`seq_len` / `seq_diff` /
`target_diff`). Official ruler used only for the `matched_functions` regression gate.

---

## 0. Headline

| item | landed `cc71dd2d` | arm `mirr_r46b_1` |
| --- | --- | --- |
| witness `r46b_01_tail_region_at_merge` (strict) | `seq_len orig=56 decomp=33` **DEFECT** | **CLEAN** (56 = 56) |
| `fly/data/quote_handler.pyc :: <module>.get_index_stocks_local` (strict) | `seq_len orig=151 decomp=60` (−91) | `seq_len orig=151 decomp=150` (−1) |
| `quote_handler.pyc` official | 51/57 | **52/57**, function leaves the mism list |
| residual (a) `trade_live_broker :: get_open_orders` | **already strict-CLEAN** | strict-CLEAN, file BYTE-IDENTICAL |
| G1: 27 partially-failing files (official) | Σ 875/961 | `SAME=26 IMPROVED=1 REGRESSION=0 MOVED=0`, Σ 876/961 |
| G4′: strict over those 27 | defect total 134 | 134, `affected=1 fixed=0 broken=0 changed=1` |
| G4: **all 544 corpus+battery paths** (official, sha surface) | Σ 6119/6240 | `SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`, Σ 6120/6240 |

---

## 1. Target (a) is FALSIFIED as a live defect — restated as a hazard

Round 44 handoff item 3 says verbatim: 「兄弟块若起始于前一守卫区域的 merge 块，`region_ast_generator`
只发射第一个三元表达式（`get_open_orders` **在 c3 下**丢 41 条尾块）」. The qualifier 「在 c3 下」 is
load-bearing: the 41-instruction loss is a *regression that the rejected ownership-side arm c3 opened*
in `get_open_orders`, not a hole in the landed generator.

Measurement (strict ruler, landed bytes):

```
F:/.../IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  total_codeobjs=123 defective=25
  <module>.TradeLiveBroker.get_open_orders               -> (None, 'ok')
  <module>.TradeLiveBroker.get_open_orders.<listcomp>    -> (None, 'ok')
```
`get_open_orders` is **not** in the 25-name defect list. Whole file official 105/119 and
`trade_live_brokerOK.py` is **BYTE-IDENTICAL** between `build_landed` and `build_r46b_1`
(sha256 of the two products equal). So (a) contributes no root cause; it is used below as a
true negative control (it is the shape a *wrong* predicate would break).

Ledger hygiene: the DROP-family path written as `IQCommon/util/finance.pyc` does not exist.
The two real finance pycs are `site-packages/IQCommon/data/finance.pyc` (22/24) and
`site-packages/IQEngine/plugins/plugin_fly_data/local_variables/finance.pyc` (108/108);
both are BYTE-IDENTICAL between the two arms.

DROP-family sweep (landed vs `r46b_1`, official + byte identity):

| file | landed | r46b_1 | product |
| --- | --- | --- | --- |
| `IQCommon/graph.pyc` | 29/31 | 29/31 | byte-identical |
| `IQCommon/util/trade_info_utils.pyc` | 38/40 | 38/40 | byte-identical |
| `fly/logger.pyc` | 28/30 | 28/30 | byte-identical |
| `IQCommon/util/replace_utils.pyc` | 8/9 | 8/9 | byte-identical |
| `IQCommon/data/finance.pyc` | 22/24 | 22/24 | byte-identical |
| `.../local_variables/finance.pyc` | 108/108 | 108/108 | byte-identical |
| `IQCommon/strategy/wizard_quant_api.pyc` (R45 target) | 51/53 | 51/53 | byte-identical |
| `fly/data/quotation.pyc` (canary) | 143/143 | 143/143 | byte-identical |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 105/119 | 105/119 | byte-identical |

None of the remaining DROP-family residuals is this shape: `_get_influence_task 207/195`,
`_process_task_queue 378/378 j=1` (equal-length swap family), `logging_process 99/95`,
`write_logging_thread 113/113 j=1`, `get_trade_list 339/323`, `trade_operation 304/302`,
`decrypt_database_url 295/324` — all unchanged by the candidate.

---

## 2. Root cause (target (b) `get_index_stocks_local`, and the general hole)

Emission-side. Round 45 closed the case *chain merge block = a descendant IfRegion's **else arm***.
The un-closed case is *chain merge block = the **entry block** of the following sibling region*:
the merge block is a complete region's condition, so writing "the merge block's bare statements"
(R45-A's action) prints only the block's leading assignment and **deletes the `if` that the block's
terminator carries, plus both arms and the whole nested body**. Ownership is satisfied (someone is
named), the emission obligation is not — 原则 2 的「归属者必发射」is still broken, one level deeper.

Real target, `fly/data/quote_handler.pyc :: <module>.get_index_stocks_local`
(dump: `D:/Temp/r46diagB/probe_qh_gisl.txt`, `probe2_gisl.txt`; landed core, read-only monkeypatch):

```
IfRegion IF_ELIF_CHAIN entry=B0 exit=B344 cond=B0 then=[B10] else=[B88,B170,B214,B298,B302,B340] merge=B344
   elif_cond=[B88,B214,B302] elif_bodies=[[B170];[B298];[B340]] final_else=[]
   blocks=[B0,B10,B88,B170,B214,B298,B302,B340]            <-- merge B344 NOT in the chain's ownership set
IfRegion IF_THEN_ELSE entry=B344 exit=- cond=B344 then=[B424] else=[B428,B546,B578,B808,B624,B804] merge=-
   parent=IfRegion@B214                                    <-- B344 is this region's ENTRY, and it is a
   blocks=[B344,B424,B428,B546,B578,B624,B804,B808]            DESCENDANT of the chain (via sub-chain B214)
ownership:  B344 term=POP_JUMP_FORWARD_IF_FALSE 428 succ=[B424,B428] preds=[B302,B10] owner=IfRegion(RegionType.IF_THEN_ELSE)
emission calls (landed):
   CALL _generate_region  IF_ELIF_CHAIN entry=B0    blocks=[B0,B10,B88,B170,B214,B298,B302,B340]
   CALL _elif_chain       IF_ELIF_CHAIN entry=B0
   CALL _generate_region  IF_ELIF_CHAIN entry=B214  blocks=[B214,B298,B302,B340]
   CALL _elif_chain       IF_ELIF_CHAIN entry=B214
   ...IF_THEN_ELSE entry=B344 is NEVER passed to _generate_region/_generate_if  ==> 91 instructions lost
```
`final_else=[]` on the outer chain while its inner sub-chains carry
`final_else=[B344,B424,B428,...]`: the merge-completion cascade hands the tail to the sub-chains,
which the flattening then consumes as `elif` material, and the outermost chain — the only one the
parent sequence dispatches (it is the sole `parent=None` region) — ends at its merge block.

Sub-chain `B344`'s owner is `IfRegion@B214` (`parent=IfRegion@B214`), i.e. a **descendant** of the
outer chain, so the sibling region is not a top-level region either: nobody is left to write it.

Synthetic witness `D:/Temp/r46diagB/r46b_witness.py :: r46b_01_tail_region_at_merge`
(dumps `probe_syn.txt`, `probe2_syn.txt`) — **structurally identical field by field**:

```
IfRegion IF_ELIF_CHAIN entry=B0 exit=B64 cond=B0 then=[B10] else=[B16,B28,B32,B44,B48,B60] merge=B64
   elif_cond=[B16,B32,B48] elif_bodies=[[B28];[B44];[B60]] final_else=[]      <-- same 3-elif shape
   blocks=[B0,B10,B16,B28,B32,B44,B48,B60]                                    <-- merge B64 absent, 8 blocks
IfRegion IF_THEN_ELSE entry=B64 exit=- cond=B64 then=[B144] else=[B148,B180,B222] merge=-
   parent=IfRegion@B32  blocks=[B64,B144,B148,B180,B222]                      <-- same "merge block is the
                                                                                  sibling region's ENTRY"
ownership:  B64 term=POP_JUMP_FORWARD_IF_FALSE 148 succ=[B144,B148] preds=[B10,B48] owner=IfRegion(RegionType.IF_THEN_ELSE)
emission calls (landed):
   CALL _elif_chain  IF_ELIF_CHAIN entry=B0  blocks=[B0,B10,B16,B28,B32,B44,B48,B60]
   CALL _elif_chain  IF_ELIF_CHAIN entry=B32 blocks=[B32,B44,B48,B60]
   ...IF_THEN_ELSE entry=B64 never dispatched
strict landed:  seq_len orig=56 decomp=33   ==> DEFECTIVE
```
Same predicates, same roles, same absent `final_else` on the outer chain, same never-emitted sibling
region — offsets renamed only (`B344→B64`, `B214→B32`, `B424→B144`, `B428→B148`).

---

## 3. ONE same-level predicate candidate (R46-B)

* **file**: `core/cfg/region_ast_generator.py`
* **anchor** (LF-normalised source, occurs exactly **1** time; asserted by
  `D:/Temp/r46diagB/mkspec46b.py`, enforced again by `D:/Temp/r43gate/build2.py`):

```
            if not self._is_implicit_return_block(_mb45_meaningful):
                _tail45 = self._generate_block_statements(_mb45)
                if _tail45:
```

* **repl** (+19 lines; the guard's five conjuncts are the only new logic — the `else` leg is the
  landed R45-A line, verbatim):

```
            if not self._is_implicit_return_block(_mb45_meaningful):
                # 原则 2（每块唯一归属）+ 原则 4（父引用子入口）（R46-B）：
                # merge 块的**归属区域**若以该块为入口，则该块是「链后的兄弟区域」的起点，
                # 发射责任是整个区域而非它的裸语句（裸语句丢掉终止符携带的条件与两臂）。
                # 同层判据（只读结构事实）：owner 存在、owner 非本链亦非本链之父、
                # owner.entry 即该块、该块在 owner 的归属集内、该区域尚未发射、
                # 该区域的块全部未被任何路径发射。R45-A 的见证里 merge 块是后代
                # 区域的 else 臂（owner.entry 不是它）⇒ 本判据为假、逐字节沿用 R45-A。
                _own46 = self.region_analyzer.block_to_region.get(_mb45)
                if (_own46 is not None and _own46 is not region
                        and _own46 is not region.parent
                        and _own46.entry is _mb45 and _mb45 in _own46.blocks
                        and id(_own46) not in self._generated_regions
                        and not (set(_own46.blocks) & self.generated_blocks)):
                    _rg46 = self._generate_region(_own46)
                    if isinstance(_rg46, dict):
                        _tail45 = [_rg46]
                    else:
                        _tail45 = list(_rg46) if _rg46 else []
                else:
                    _tail45 = self._generate_block_statements(_mb45)
                if _tail45:
```

Full spec: `D:/Temp/r46diagB/spec46b.json`. Mirror arm: `D:/Temp/r43gate/mirr_r46b_1`
(built with `build2.py r46b_1 spec46b.json`; BOM preserved, CRLF-only, +19 inserted lines asserted).

### Why this reads only structural facts

Every input to the guard is a *region-graph* object, never a payload value:
`self.region_analyzer.block_to_region` is the 原则 2 ownership map (block → owning region, pure
identity); `_own46 is not region`, `_own46 is not region.parent`, `_own46.entry is _mb45`,
`_mb45 in _own46.blocks` are block-identity / block-ownership / region-role tests
(entry role, and membership in the region's owned block set);
`id(_own46) not in self._generated_regions` and
`not (set(_own46.blocks) & self.generated_blocks)` are "has this region/block already been
discharged" bookkeeping over block identity. There is no `opname`, no `co_names`, no `argval`,
no constant, no absolute offset, no instruction count, no file name, no per-function history, and
no numeric threshold anywhere in the new lines. The dispatch target `_generate_region` is chosen
*by the owner's own region type* (polymorphic), so the predicate never asserts "this is an
IF_THEN_ELSE" — it only asserts "the merge block is somebody's entry and that somebody has not
been emitted yet".

### Relation to R45-A's five conjuncts — NOT disjoint, deliberately a *refinement*, and provably safe

R46-B sits **inside** R45-A's hit-branch (after conjuncts ①–⑤ and after ③
`_is_implicit_return_block`), so the two can only be evaluated on the same block. That is the
intended interaction, and it is a strict refinement, not a conflict:

* R45-A's conjunct ① (`find_descendant_region_for_block(merge, (IfRegion,))`) is kept verbatim and
  gates R46-B, so R46-B can never fire on a block R45-A does not already fire on. The candidate's
  firing set is a **subset** of the landed firing set — it can only change what is emitted where
  landed already emits something.
* The discriminator against R45-A's own witness is conjunct **`_own46.entry is _mb45`**. In
  `region_mean_desicion` (and in `r45e_witnesses.py`) the merge block is claimed as a descendant
  IfRegion's **else arm**: `ownership: B250 ... owner=IfRegion(RegionType.IF)` while that owner's
  `entry=B114` (`IfRegion IF entry=B114 then=[B246] else=[B250] merge=B246`), i.e.
  `owner.entry is not merge` ⇒ R46-B's guard is **false** ⇒ control takes the `else` leg, which is
  the landed statement character-for-character ⇒ byte-identical output. Measured, not argued:
  `r45e_witnesses.pyc` (4 code objects) and `r45e2_controls.pyc` (8 code objects) are
  **BYTE-IDENTICAL** between `build_landed` and `build_r46b_1`.
* The other three new conjuncts are pure idempotence guards (never emit a region twice; never emit
  a region whose part has already been written by another path), and `_own46 is not region` /
  `_own46 is not region.parent` make upward recursion impossible, which is why no cycle can form
  between the chain and its merge block's owner.
* The block-vs-region choice is exclusive: the R45-A block path is retained as the `else` leg, so
  the landing of R46-B cannot silently delete R45-A's behaviour — it can only specialise it.

---

## 4. Gates (measured)

### G0 — synthetic witnesses, landed defective → arm clean
`D:/Temp/r46diagB/r46b_witness.pyc` (5 code objects; `py_compile` with the project's 3.11.7):

```
build_landed  : RESULT landed: defective=1/5
   <module>.r46b_01_tail_region_at_merge   seq_len orig=56 decomp=33
build_r46b_1  : RESULT r46b_1: defective=0/5           ==> witness strict-CLEAN
```
Diff of the two products is 8 added lines, all inside the witness function (tail region restored):
`if len(stock) != 2: return default_dataList / else: code=… out=[] if code=='QQQ': out.append(code) return out`.
No other function's text moves.

### G0-neg — true negative controls, must be BYTE-IDENTICAL across arms
1. `r45e_witnesses.pyc` — R45-A's own 4-object witness battery (merge block = descendant's else
   arm): `IDENTICAL`.
2. `r45e2_controls.pyc` — R45-A's 8-object control battery (chain-in-loop / plain if+tail /
   implicit merge / if-elif-else+tail / nested chain in arm / chain then for / all-return no tail):
   `IDENTICAL`.
3. `nc_02_plain_if_tail`, `nc_03_chain_merge_returnonly`, `nc_04_chain_no_tail` + `<module>` in my
   own witness file — 4 code objects clean on landed and textually untouched in the product diff ⇒
   `IDENTICAL` (the unified diff shows a single hunk, inside `r46b_01_…`).
4. `fly/data/quotation.pyc` (143/143 fully-matched canary): `IDENTICAL`.
5. `trade_live_broker.pyc` (123 code objects, holds the (a) residual and the 25-name DROP list):
   `IDENTICAL`.
6. wizard_quant_api / graph / trade_info_utils / logger / replace_utils / both finance files:
   `IDENTICAL` (see table §1).

### G1 — the 27 partially-failing corpus files (official ruler, `pyc_batch_verify` reading)
`D:/Temp/r46diagB/par27.txt` = every index row with `0 < matched_functions < function_count`
(27 files, i.e. **more than the 20 required**), `r43g.py run --arm=landed` vs `--arm=r46b_1`,
`r43g.py ab` on the two jsonls:

```
TALLY SAME=26 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0   (files=27, unpaired=0)
IMPROVED  fly/data/quote_handler.pyc  51/57 -> 52/57
sum matched_functions over the 27 files: landed 875/961 -> arm 876/961   (+1)
```
**REGRESSION = 0 in official `matched_functions` on the 27-file partially-failing sample.**

Per-code-object byte identity of the negative controls *inside* my witness file
(`D:/Temp/r46diagB/r46b_nc.py`, sha of the full `dis` instruction signature of each code object
compiled from each arm's product):

```
   <module>                              IDENTICAL
   <module>.nc_02_plain_if_tail          IDENTICAL
   <module>.nc_03_chain_merge_returnonly IDENTICAL
   <module>.nc_04_chain_no_tail          IDENTICAL
   <module>.r46b_01_tail_region_at_merge DIFFERS   (the witness, as intended)
per-code-object identical: 4/5
```

### G4′ — strict ruler over every product in that sample
`python -X utf8 D:/Temp/r46diagB/r46b_g4p.py par27.txt`:

```
== fly/data/quote_handler.pyc  strict-defective a=7 b=7
   CHANGED <module>.get_index_stocks_local  a=[seq_len orig=151 decomp=60] b=[seq_len orig=151 decomp=150]
G4p files=27 defect-set-identical=26  strict-defect-total a=134 b=134
G4-prime affected=1 fixed=0 broken=0 changed=1
```
`broken = 0`, and the only CHANGED row is the target function, which strictly improves
(−91 instructions → −1) and loses all official jump diffs (`[150,60,0,92]` → not in the mism list).

### G4 — full 544-path A/B (the strongest available; only one side re-run)
Baseline = Round 45's `D:/Temp/r43gate/r45a_full.jsonl` + `r45a_full2.jsonl` (544 rows, produced by
arm `mirr_r45a`), whose `core/cfg/region_ast_generator.py` I verified **sha256-equal to landed
`cc71dd2d`** (`e743b6de1d8efc01…` == `e743b6de1d8efc01…`), so those rows *are* landed rows.
Path-set equality with the list checked: `544 == 544`, symmetric difference `0`.
Candidate side: `r43g.py run --arm=r46b_1 --list=r45full.txt` in 3 shards
(`D:/Temp/r46diagB/full_r46b1_{0,1,2}.jsonl`, 544 rows, 0 errors), tallied by `r46b_g4.py`:

```
paired=544 (base=544 arm=544)  SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0
IMPROVED F:/Downloads/pythoncdc-main/site-packages/fly/data/quote_handler.pyc  51/57 -> 52/57
sum matched_functions  landed=6119 arm=6120  delta=+1   (total_functions 6240)
```
The **sha change surface over the entire corpus + batteries + Round-45 witnesses is exactly one
product**, and its unified diff is a single 14-line addition (the restored tail region), no other
hunk:
```
hunks 1
@@ -220,0 +221,14 @@   (if len(stock) != 2 / else: stock_code… / with open… / for line in cin… / return returnData)
```

The baseline was **cross-validated against my own independent `--arm=landed` runs**: all 27
partially-failing rows I produced match the Round-45 baseline rows on `sha` *and*
`matched_functions` (`ok=27/27`), and the baseline `quote_handler.pyc` row reads `51/57`, so the two
sides of the A/B are the same landed bytes measured twice.

---

## 5. Falsified leads (stated as falsified, with their measurement)

1. **「(a) `get_open_orders` loses a ~41-instruction tail on the guard/ternary sibling path in the
   landed core» — FALSIFIED.** Landed strict: `get_open_orders` and
   `get_open_orders.<listcomp>` both `(None,'ok')`; the file's 25-name defect list does not contain
   them; the whole product is byte-identical between the arms. The 41-instruction loss is a
   *c3-arm* effect (Round 44's wording 「在 c3 下」), i.e. a hazard for ownership-side predicates,
   not a landed hole. It served this round as negative control #5.
2. **「the residual is an ownership-side (region_analyzer) defect — give the outer chain a
   `final_else`» — FALSIFIED by measurement for this round's purpose and rejected on record.**
   The asymmetry (outer chain `final_else=[]`, sub-chains `final_else=[B344,…]`) is real, but
   Round 43 established that `region_analyzer`'s merge completion is a *cascading* fallback
   (`:17014/:17062/:17102`) where a single-point conjunct is non-monotone (G1 SAME=4 IMPROVED=0
   **REGRESSION=2 MOVED=13**, `function.pyc 69/71 → 53/71`), and Round 44's c3 attempt gave
   `SAME=283 IMPROVED=3 REGRESSION=8`, `Σ5523→5504`, strict `fixed=10 broke=24`. The emission-side
   candidate here needs none of that: it changes exactly one file, +19 lines, and its firing set is
   a subset of the landed firing set.
3. **「R46-B must be disjoint from R45-A to be safe» — FALSIFIED as a requirement, and the
   alternative proven instead.** R46-B evaluates on exactly R45-A's blocks; safety comes from the
   subset property plus a discriminating conjunct (`owner.entry is merge`) that is measurably false
   on every R45-A witness (byte-identity of 12 R45-A witness/control code objects).
4. **「`get_index_stocks_local`'s remaining −1 instruction belongs to this shape, so the fix is
   incomplete» — FALSIFIED as a claim about this shape.** The residual is a single
   `JUMP_FORWARD 808` at the with-region exit, and the ruler's target tracking already normalises
   `POP_JUMP_FORWARD_IF_FALSE 806 → 804 → 808`. It is the *same* one-instruction family as the
   untouched `get_industry_stocks_local 89/88` and `get_kline_binary 129/128` residuals in the same
   file, i.e. a jump-stub-folding family orthogonal to merge-block emission.
5. **「`IQCommon/util/finance.pyc` is a DROP-family file still in the ledger» — FALSIFIED: no such
   path exists in the corpus.** Real files `IQCommon/data/finance.pyc` (22/24) and
   `IQEngine/plugins/plugin_fly_data/local_variables/finance.pyc` (108/108) were measured instead;
   both are byte-identical across the arms, so neither carries this shape.

---

## 6. Recommendation

**SHIP R46-B** (single file, single edit, +19 lines), with the honest caveat that the corpus target
lands at `150/151`, not CLEAN.

Gate evidence for shipping: G4 `SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0` over all 544 paths;
G1 over the 27-file partially-failing pool `REGRESSION=0`; G4′ `broken=0` with
strict-defect-total unchanged (134 → 134) and the single CHANGED row strictly better
(−91 → −1 instructions, official jump diffs 5 → 0 → row leaves the mism list); G0 witness
`defective=1/5 → 0/5` with the other 4 code objects byte-identical per code object; R45-A's own
12 witness/control code objects byte-identical, so the landed Round 45 fix cannot regress.
Additional argument for safety: the candidate's firing set is a strict **subset** of the landed
R45-A firing set (it only re-decides *what* to write inside a branch that already fires), and the
whole-corpus measurement confirms exactly one product moves.

Not claimed: `get_index_stocks_local` is not certified CLEAN. Its remaining −1 is the
`JUMP_FORWARD` at the `with`-region exit, i.e. the equal-but-one jump-stub family that also owns
`get_industry_stocks_local 89/88` and `get_kline_binary 129/128` in the same file — hand that to the
jump-stub-folding line, not to this one.

## 7. Artifacts (all outside `core/`)

| path | what |
| --- | --- |
| `D:/Temp/r46diagB/r46b_witness.py` / `.pyc` | synthetic witness + 3 negative controls |
| `D:/Temp/r46diagB/probe_qh_gisl.txt`, `probe2_gisl.txt` | real-target region roles + ownership + parent links + emission calls |
| `D:/Temp/r46diagB/probe_syn.txt`, `probe2_syn.txt` | same, synthetic witness |
| `D:/Temp/r46diagB/spec46b.json`, `mkspec46b.py` | the candidate (anchor asserted unique, +19 lines) |
| `D:/Temp/r43gate/mirr_r46b_1` | the measured mirror arm (`build2.py r46b_1 spec46b.json`) |
| `D:/Temp/r46diagB/r46b_strict.py` / `r46b_align.py` / `r46b_ident.py` / `r46b_nc.py` | strict ruler wrappers |
| `D:/Temp/r46diagB/r46b_g4p.py` / `r46b_g4.py` | G4′ and G4 tallies |
| `D:/Temp/r46diagB/{par_landed,par_r46b1}.jsonl`, `full_r46b1_{0,1,2}.jsonl`, `run_landed.jsonl`, `run_r46b_1.jsonl`, `r45e_*.jsonl`, `fin_*.jsonl` | raw gate rows |
| `D:/Temp/r46diagB/r46b_probe2.py` | read-only monkeypatch: `rs` order + `parent` links + which regions reach `_generate_region/_generate_if/_if_generate_full_elif_chain` |

`F:/Downloads/pythoncdc-main/core/` was never written: `git status --porcelain core/` is empty.
`core/cfg/region_analyzer.py` is not touched by the arm either (`build2.py` patched only
`region_ast_generator.py`). The arm-vs-landed source diff is exactly **1 hunk, 20 added / 1 removed
= net +19 lines** at `_if_generate_full_elif_chain` line 12541, and the removed line
`_tail45 = self._generate_block_statements(_mb45)` re-appears verbatim as the guard's `else` leg.
Product directories `build_landed/` and `build_r46b_1/` were moved out of the shared
`D:/Temp/r43gate` into this private dir after the tallies, so the only additions left in
`D:/Temp/r43gate` are `mirr_r46b_1/`; all gate numbers above were re-verified after the move.
