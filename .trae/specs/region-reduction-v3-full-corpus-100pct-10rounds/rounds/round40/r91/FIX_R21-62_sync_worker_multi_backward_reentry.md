# R21-62 — `trade_live_broker._sync_worker`: multi backward re-entry / latch-duplicated while condition

Engineer r91a. Mirror: `D:/Temp/r91`. Repo untouched.

## 0. Base / provenance

Landed bytes re-anchored into `D:/Temp/r91` and verified by sha256[:16]:

| file | bytes | sha16 | expected |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 3852304 | `b4363f5858e58074` | MATCH |
| `core/cfg/region_analyzer.py` | 2109362 | `842e2748bcdfeb66` | MATCH |

Baseline re-measure on the landed bytes, before any edit:

- `python -X utf8 pycdc.py …/trade_live_broker.pyc -o out/broker_BASE.py` → 179288 B,
  **byte-identical** (`cmp`) to `D:/Temp/r91m/out/broker_LANDED.py`.
- judge: `status=failure units=127/128 success_rate=99.22%` — failing unit
  `***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow`.
- rig `win_r91.py`: orig 412 / prod 410 instrs, **windows=9**
  (#1 del22 @362, #2 del18 @544, #3-#6 small, **#7 ins196 @prod726**, #8 rep, **#9 del165 @1890**).

Baseline reproduced exactly as briefed. Nothing below is inherited belief.

## 1. Census (real bytes, read-only rig `census_r91.py`; nothing mutated inside the analyzer)

CFG of `_sync_worker`: **54 blocks**, analyzer: **26 top-level regions / 70 incl. children**.

### 1.1 Backward-jump terminators (whole unit)

| block | n | terminator | target |
|---|---|---|---|
| @704 | 21 | POP_JUMP_BACKWARD_IF_TRUE | @704 |
| @876 | 18 | POP_JUMP_BACKWARD_IF_TRUE | @704 |
| @1056 | 15 | POP_JUMP_BACKWARD_IF_FALSE | @704 |
| @2844 | 7 | POP_JUMP_BACKWARD_IF_TRUE | @2072 |
| @2886 | 8 | JUMP_BACKWARD | @232 |

**Distinct backward targets = 3. `@704` is reached BACKWARD by 3 distinct blocks
(@704 self, @876, @1056).** @704 additionally reached FORWARD by @232/@364/@700.
Full pred set of @704 = [(232,FWD POP_JUMP_FORWARD_IF_TRUE), (364,FWD …IF_TRUE),
(700,FWD JUMP_FORWARD), (704,BWD), (876,BWD), (1056,BWD)] — matches the briefed graph.

### 1.2 What the analyzer declares

```
L1 LoopRegion entry=@232  header=@232  condition_block=None  is_while_true=True
   back_edge_block=@2886  back_edge_blocks={2886}  has_break=True break=[1872]
   body=[230,232,364,522,544,700,702,704,876,1034,1056,1210,1212,1214,1370,1388,
         1502,1524,1638,1770,1872,1876,1890,2026,2064,2066,2072,2090,2114,2136,
         2168,2192,2198,2200,2206,2208,2214,2374,2378,2382,2492,2540,2580,2628,
         2668,2844,2882,2884,2886]                       (50 blocks)   ← CORRECT: `while True:`

L2 LoopRegion entry=@232  header=@704  condition_block=@232  is_while_true=False  (child of L1)
   back_edge_block=@704   back_edge_blocks={704}          ← ONE, the CFG has THREE (@704,@876,@1056)
   condition_chain_blocks=[232,364,522,544, 1214,1890,2026]  ← first four correct, last three LEAKED
   body=[704,876,1034,1056,1212]  has_break=True break=[2064,2066,2168]

L3 LoopRegion entry=@1890  header=@2072  condition_block=@1890  back_edge_block=@2844
   cond_chain=[2026]  body=[2072 … 2884]
```

**Answer to the census question:** yes — the analyzer declares exactly ONE `back_edge_block`
(@704) where the CFG carries three conditional backward edges into @704; @876 and @1056 are
demoted to ordinary body statements, and the latch chain @704tail/@876/@1034/@1056 is rendered
as body text. `back_edges_for_header` at `region_analyzer.py:4958` is then collapsed by the
`max(…)` single-winner selection at `:5023` — structurally it *can* see all three sources, but
only one survives the declaration.

### 1.3 What the original actually is (proved, not guessed)

`dis` of the original @232..@1212 reads as ONE boolean chain evaluated twice:

```
@232 A = int(now().strftime('%H%M')) <  pre_before_trading   IF_TRUE  → 704
@364 B = int(now().strftime('%H%M')) >= int(post_after_trading) IF_TRUE → 704
@522 C = holiday_sync_account == '0'                          IF_FALSE → 702 → 1214
@544 D = self…is_trading_date(now().date())                   IF_TRUE  → 1214   (= `not D`)
@704 time.sleep(60) ; A' → IF_TRUE(back) → 704
@876 B'            → IF_TRUE(back) → 704
@1034 C'           → IF_FALSE → 1212
@1056 D'           → IF_FALSE(back) → 704 ; fall → 1210 → 1214
```

Control compile on this machine (Python 3.11.7) of the plain source

```python
while A < B or C >= D or (E == '0' and not f()):
    time.sleep(60)
```

emits *exactly* this signature: entry chain with `POP_JUMP_FORWARD_IF_TRUE` arms into the body
block, body block = `time.sleep(60)` + first arm of a **duplicated copy of the same test**, and
the duplicated arms `POP_JUMP_BACKWARD_IF_TRUE→body-start` (twice) plus
`POP_JUMP_FORWARD_IF_FALSE` + `POP_JUMP_BACKWARD_IF_FALSE→body-start`.

⇒ **The unit is ONE `while <or-chain>: time.sleep(60)` loop.** CPython duplicates a
short-circuit while-test into the latch; the three backward edges are the *same* expression's
continue arms, not three `continue` statements. Our L1/L2 split turns the latch copy into body
statements of a fake nested `while A:` loop — visible in the product as

```
while True:
    while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading:   # only arm A
        time.sleep(60)
        return int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)  # B' as a statement
        continue
        if holiday_sync_account == '0': continue                                 # C'/D' as statements
        self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())
        continue
```

**Falsified on the way** (consistent with the briefed census): the "chained comparison in the
loop condition is unrenderable" story is dead — we emit *more* chains than CPython (3 vs 2), and
the real defect is the latch duplication, not a chain we cannot build.

## 2. Mechanism

### 2.1 Target is proven reachable (measured, not assumed)

`out/broker_GOLD.py` = the broker product with only `_sync_worker` replaced by the
reconstruction `repro/true_source.py`:

| product | instrs | windows vs orig | del | ins | judge |
|---|---|---|---|---|---|
| `broker_BASE.py` (landed bytes) | 410 | 9 | 206 | 208 | 127/128 failure |
| `broker_PATCHED_L2.py` (only the `while` test line fixed) | 482 | 6 | 168 | 237 | 127/128 failure |
| **`broker_GOLD.py` (full reconstruction)** | **408** | **4** | **5** | **1** | **`status=success units=128/128`** |

⇒ **the unit flips at 128/128 when the emitted source is**

```python
while True:
    while <A or B or (C and not D)>:      # one loop, chain test, body = time.sleep(60)
        time.sleep(60)
    if <E>: …                              # 4 nested ifs, `if not reconnect(…): return`
    while <pre <= int(…strftime) < int(post)>:   # chain-duplicated latch, NOT if+continue
        … body in source order …
        time.sleep(steps)
    time.sleep(steps)
```

The 4 residual windows in GOLD are only `EXTENDED_ARG` distance artifacts, the two
connector `JUMP_FORWARD`s (@700/@702) and one `NOP` — the pylingual judge accepts them
(GOLD reads 128/128). So no unrenderable construct is involved; the emission text is known.

`broker_PATCHED_L2.py` is the scoping measurement: fixing the `while` test alone moves the
unit from 9→6 windows but does **not** flip it — the remaining three defects are downstream,
so the fix must cover both halves below.

### 2.2 Root causes, each with its number

**R-1 (identification, analyzer) — the mixed or-prefix / and-group chain never mounts.**
`_detect_while_condition_boolop_chain(@232, L2)` measures **`[(232,'or')]`, length 1**, so the
Step-5 caller gate `len(chain) >= 2` (`region_analyzer.py:26951`) rejects and no `BoolOpRegion`
is mounted as the loop test ⇒ the generator emits only arm A.
Trace of `_detect_while_boolop_forward_chain`: it does collect
`[(232,'or'),(364,'or'),(522,'and')]` but the R07 `all_same_target` criterion demands one
common jump target, and a mixed `X or Y or (Z and W)` chain structurally has **two** target
classes — the or-run arms jump to the body entry @704, the and-group's false arms jump to the
loop exit (@702/@1214) — so it returns `None`; the fallback backward walk then yields length 1.
This is the mirror image of the already-supported [R7-B45] `and 头前缀 + or 尾 run`; that
detector cannot fire here because it requires the or-run members to be unclaimed, whereas
@364/@522/@544 are claimed by the enclosing region.

**R-2 (emission, generator) — latch re-entry arms are not suppressed.**
L2's latch copy (@704 tail, @876, @1034, @1056, connectors @1210/@1212) is emitted as body
statements. The existing [Round 08] absorption block is gated on

```python
if (_be is not None and _cb is not None and _be is not region.header_block):
```

and for this region `back_edge_block is header_block` (both @704, measured in §1.2), so the
whole absorption is skipped — precisely the "one declared back edge vs three measured backward
edges" case.

**R-3 (emission, generator) — pure-recheck whitelist rejects call-bearing operands.**
L3 (`while pre <= int(…strftime('%H%M')) < int(post)`, chained compare) is recognised
(`is_chained_compare_cond`), but its latch copy survives as an explicit
`if not <chain>: continue` statement, because the suppression test
`_has_only_compare` whitelists only `LOAD_*/COPY/SWAP/COMPARE_OP/IS_OP/CONTAINS_OP/POP_TOP`
and the operand is `int(…)` → contains `CALL`; and the statement-prefix extractor keys on
`last_store_idx >= 0`, while the body statement fused into the latch block @2668 is an
*expression* statement (`time.sleep(steps)` ends in `POP_TOP`, no STORE). Both fail on measured
bytes: `while chain: body; if not chain: continue` compiles to 50 instrs with 2 backward jumps,
the plain `while chain: body` to 38 with 1.

### 2.3 Implemented (measured on the real bytes)

Candidate = landed generator (`b4363f5858e58074`, untouched) + landed analyzer
(`842e2748bcdfeb66`) with one new file-level patch → **`241905c2078f0270`**
(`DELIVER/region_analyzer_R21-62a.py`, BOM+CRLF preserved, `py_compile` passes,
`b'\r\r\n'` count 0, no bare LF).

Two hunks, both shape-only (no names, no offsets, no counters-as-thresholds, no per-file state):

1. **`_detect_while_condition_or_prefix_and_group_chain`** — the mirror of [R7-B45]: an
   `or` run whose tail is an `and` group. Single forward fall-through walk from
   `condition_block`; every member's conditional target must normalise (through
   unconditional-`JUMP_FORWARD`/noise-only connector blocks) into exactly two target classes —
   the body-entry `T` (∈ body_blocks ∪ header ∪ entry ∪ condition_block ∪ back_edge_block) and
   one unique `F` outside that set; members must be store-free (walrus `COPY(1)+STORE` exempt)
   and exception-frame-free; the last member's fall-through must normalise to `T`.
   Gate 2 is the latch-duplication signature proper: the body-entry block's opcode tail must
   duplicate the chain head's whole evaluation sequence (`_r2162_split_duplicated_tail`,
   opcode-name equality with its own statement terminator in the prefix), **and** at least two
   distinct body blocks must carry conditional backward edges normalising to the same `T`
   (measured: 3 — @704/@876/@1056). Ops follow the existing walker's sense rule verbatim.
2. **Relaxation of the [B11] body-reachability walk** in the Step-5 loop pass: it stopped at
   `region.back_edge_block`, which for this shape *is* `region.header_block`, so the latch arms
   never contributed their variables and the chain was trimmed. Cycle protection is already
   carried by `_rvis2`; the walk now continues when `back_edge_block is header_block`.

Measured effect (`_sync_worker`, rig `win_r91.py`, judge `pyc_verify single --source`):

| stage | prod instrs | windows | del | ins | verdict |
|---|---|---|---|---|---|
| landed base | 410 | 9 | 206 | 208 | 127/128 |
| candidate `241905c2…` | 400 | **5** | — | — | **127/128 (no flip)** |
| GOLD (true source spliced) | 408 | 4 | 5 | 1 | **128/128 success** |

The candidate changes the product text from

```
while int(…strftime('%H%M')) < pre_before_trading:            # one arm only
    time.sleep(60); return int(…) >= int(…); continue; …
```
to
```
while int(…) < pre_before_trading or int(…) >= int(post_after_trading):   # two arms mounted
```

**Measured residual blocker (why it does not flip).** Debug probes (`logs/dbg9.txt`,
`logs/dbg11.txt`, prints removed before delivery) show the identification half now works
end-to-end:
`chain=[(232,'or'),(364,'or'),(522,'and'),(544,'or')]` → `owner_ok=True` →
`BoolOpRegion blocks=[364,522,544,232] op_chain=[(232,'or'),(364,'or'),(522,'and'),(544,'or')]
is_condition_context=True` → `add_child` into `loop@232`.
But at generation `_loop_generate_while` reads
`bfw=[232,364]` — **the mounted 4-member `op_chain` is consumed as 2 members**, and the
`and` group survives as sibling `IfRegion522/IfRegion544` children of the same loop, so the
test is still short and the latch arms (@522 group + @704 tail) still print as body statements
(`if holiday_sync_account == '0': continue` etc.). The truncation is downstream of the mount
(generator-side `boolop_for_while` consumption / re-assembly of the two `IfRegion` children),
not in the detector. Second residual: the L3 chained-compare latch copy is still emitted as
`if not <chain>: continue` (R-3: the `_has_only_compare` whitelist rejects the `CALL`-bearing
`int(…)` operand and the fused statement prefix is a `POP_TOP` expression statement, so the
`last_store_idx >= 0` extractor never fires).

**Not delivered as installable.** No flip, so I am not asking for a landing; the numbers, the
GOLD proof (`DELIVER/broker_GOLD_PROOF.py` → 128/128), the target text
(`DELIVER/true_source_sync_worker.py`) and the four residual causes above are the deliverable.

## 3. Panel + sweep + verdict

Panel measured with the candidate in `D:/Temp/r91` (regenerate then judge with `--source`):

| file | candidate verdict | required |
|---|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 127/128 `status=failure` (residual `_sync_worker`) | 128/128 — NOT MET |
| `IQCommon/util/replace_utils.pyc` | 9/9 `status=success` | 9/9 ✓ |
| `IQEngine/plugins/plugin_system_risk_calculation/function.pyc` | **15/15 `status=success`** | 15/15 ✓ (no inherited `db1f0e96…` regression — base is the landed bytes) |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | **12/13** `status=failure`, residual is `clock_worker` (not mine) — not regressed | 12/13 ✓ |
| `fly/data/quotation.pyc` | **153/153** `status=success` | 153/153 ✓ |

Step 6 (full 402-file sweep) **NOT completed**: `git archive HEAD | tar -x` aborted on this
box with `Can't unlink already-existing object` against the deep `.trae/specs/...` paths, so
`new_products/` is empty and no CHANGED list exists. The candidate therefore carries **no
corpus-level certification** — the 5-file panel above is all that was measured. Since the
candidate does not flip the unit, do not treat it as installable regardless.

## 4. Framing discipline for the next hand (cheap, measured)

The whole chain is a **CPython 3.11 latch duplication of a short-circuit while test**, proved by
control compile on this machine (3.11.7): `while A<B or C>=D or (E=='0' and not f()): time.sleep(60)`
reproduces the original's signature exactly (entry chain with forward true-arms into the body
block, then body block = first statement + head of a *copy* of the test, with
`POP_JUMP_BACKWARD_IF_TRUE→body-start` twice and `POP_JUMP_BACKWARD_IF_FALSE→body-start` once).
CPython therefore emits the test twice, and any emitted source that shows it twice
(`while X: …; if not X: continue`) is one copy too many — the generator must take the test from
the **entry** chain and suppress the latch copy entirely.
