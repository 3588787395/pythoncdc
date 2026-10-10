# FIX_R21-14 — r33a — parenting/declaration fix (adopt-at-identification)

Status: COMPLETE — **FALSIFIED (0/14 product fires; delivered analyzer is byte-identical to
sealed)**. See `## declaration` at the end.
Mirror: D:/Temp/r33a/wt   Repo (RO): D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main @ e28cade6

## Plan
1. mirror setup + sha256 (analyzer 35e227ac3e7b25af…, generator c16daa4f87dc68e6…)
2. overlay banked generator half a34cdcf4a4ae7147 (unmodified)
3. anatomy print (read-only, out-of-band after analyze())
4. baseline readings broker/quote/quotation
5. fire census (14 files) BEFORE trusting
6. patch + readings + negatives + declaration

## mirror proof

`mkdir -p /d/Temp/r33a/{wt,pristine,DELIVER,tools,out,sig}` then from the repo
`cp -r pycdc.py core parsers utils bytecode scripts /d/Temp/r33a/wt/`. sha256 re-read
**inside the mirror**:

| file | sha16 | brief expected |
|---|---|---|
| `core/cfg/region_analyzer.py` (sealed, = `pristine/`) | `35e227ac3e7b25af` | `35e227ac3e7b25af` ✓ |
| `core/cfg/region_ast_generator.py` sealed | `c16daa4f87dc68e6` | `c16daa4f87dc68e6` ✓ (saved to `pristine/`) |
| `core/cfg/region_ast_generator.py` **after overlay** | `a34cdcf4a4ae7147` | banked `CANDIDATE_r32a_generator_pair_half.py` ✓ |

Overlay = `cp <repo>/.trae/specs/.../round27/CANDIDATE_r32a_generator_pair_half.py
<mirror>/core/cfg/region_ast_generator.py`. Verified: sha256 of the overlaid file equals the
banked file's sha256 (`a34cdbf4a4ae71477986ed7c753ea980…`), `py_compile` clean,
**+73 added / −1 removed** vs sealed, 59 765 lines. **The generator half in my mirror is that
banked candidate, UNMODIFIED** (I never wrote it) ⇒ the install route is two files
(banked generator + my analyzer). Mirrors `r32a/r31a/r30a/r25b` not touched. Repo READ-ONLY.

## baseline (unpatched analyzer + banked generator half)

Products written by `D:/Temp/r33a/tools/regen.py` (in-process `pycdc.decompile_pyc`,
`newline=''`, mirror `pycdc.__file__` asserted inside the mirror). Judge =
`scripts/pyc_verify.py single <pyc> --source <my fresh product>` (always `--source`).

| file | score | brief expected |
|---|---|---|
| `trade_live_broker.pyc` | **120/128** ✓ | 120/128 |
| `fly/data/quote.pyc` | **90/92** ✓ | 90/92 |
| `fly/data/quotation.pyc` | **153/153** ✓ | 153/153 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | **44/45** ✓ | 44/45 |

Broker product `out/broker.BASE.py` = 3067 lines / **175536 B** — byte-length identical to the
previous engineer's `broker.COMB2.py` (175536 B) ⇒ banked half reproduces.

Sealed shapes (`unit_diff … --all`):
`_process_cancel_order len orig=333 prod=334 delta=+1` · `_process_order len orig=507 prod=448 delta=-59` ✓ (both as briefed).

## parenting anatomy (BEFORE; `tools/anatomy.py`, out-of-band, separate process)

`_process_cancel_order` LIST order = LoopRegion@46, TryExceptRegion@98, TryExceptRegion@420,
BoolOpRegion@1608, IfRegion@1100/998/946/926/690/608/514/420/332/312, Region@0 (15 roots).

```
LoopRegion@46        nb=43 parent=None         children=[IfRegion@312, IfRegion@332]   ← no try child
TryExceptRegion@98   nb=5  parent=IfRegion@312 children=[]        held_by_parent=0/5    ← DEFECT
TryExceptRegion@420  nb=29 parent=IfRegion@332 children=[8 IfRegion] held_by_parent=23/29 (entry 420 IS held)
IfRegion@332         nb=26 parent=LoopRegion@46  held_by_parent=26/26
IfRegion@312         nb=30 parent=LoopRegion@46  held_by_parent=30/30
blocks @96/@98/@200/@252/@306  → owner=TryExceptRegion@98 ; TryExceptRegion@98.blocks=[96,98,200,252,306]
IfRegion@312.blocks =[44,312,332,350,418,420,442,514,…,1822,1930]   ← contains NONE of 96/98/200/252/306
LoopRegion@46.blocks=[44,46,96,98,200,252,306,312,…,2000]           ← contains ALL FIVE
```

**Which call site claims @98** (tracer `tools/trace_adopt.py`, monkeypatched `Region.add_child`
in a diagnostic process whose final tree I verified is identical to the uninstrumented
`anatomy.py` dump ⇒ the reading is not a probe artifact):

```
ADOPT child=TryExceptRegion@98 claimant=IfRegion@312 -> parent=IfRegion@312 (was None)
      site=region_analyzer.py:32280
```

⇒ host is **`core/cfg/region_analyzer.py:32280  best_parent.add_child(child)`** inside
`_build_region_hierarchy` (def at **32074**), NOT the `9925-9935` try-nesting site the brief
quoted (that site is `region_b.add_child(region_a)`, try↔try pairing only, and did not fire for
@98). `Region.add_child` itself = **221-233** (first-adopter-wins as described).
Mechanism: candidates are collected by **offset-range** containment (`ps<=cs and pe>=ce`,
:32095) and IfRegion branch-entry (:32097-32100); IfRegion@312's range (44..1930) *spans* the
try's blocks although its block SET holds none of them, and the tie-breakers
(:32168 `_use_if_tiebreaker`, then :32226 `max(candidates, key=(priority, -range))`) prefer the
*smallest range* at equal priority ⇒ the non-containing IfRegion wins over LoopRegion@46, which
really holds the blocks.

## 判据实现 (as measured — R33A-1)

Host (re-derived from the sealed bytes, the brief's `9925-9935` is the try↔try pairing site and
did NOT fire for @98): **`core/cfg/region_analyzer.py:32280` `best_parent.add_child(child)`**
inside `_build_region_hierarchy` (def :32074); `Region.add_child` = **:221-233**
(first-adopter-wins confirmed).

Inserted at :32280 (before the adoption call, 27 lines, CRLF, `ast.parse`-gated writer):

```python
# [R33A-1] correct-at-identification adoption guard: a container region may only
# adopt a child whose ENTRY block it actually holds.
if (isinstance(child, TryExceptRegion)
        and child.entry is not None
        and child.entry not in best_parent.blocks):
    _r33a_holders = [_c for _c in candidates
                     if _c is not child and _c is not best_parent
                     and child.entry in _c.blocks]
    if _r33a_holders:
        best_parent = min(_r33a_holders,
                          key=lambda _c: ranges[id(_c)][1] - ranges[id(_c)][0])
```

Predicate = "the adopting region owns the child's entry block" (entry ownership is what
"nested regions act as single abstract nodes" is keyed on: the parent dispatches the child AT
its entry). Reads only `child.entry` + each candidate's own `.blocks` + the `ranges` map
already built at :32078. Fires while the parent is still being chosen ⇒ not a retrospective
repair pass; no emission-order change; no sibling internals.

Why `entry` and not `all blocks`: measured, `TryExceptRegion@420` is legitimately nested in
`IfRegion@332` (the elif arm) yet 6 of its 29 blocks (the finally-copy tail 1828/1846/1918/
1922/1924 + the loop-condition block 418) are not in that arm's set — a "holds ALL blocks"
test would wrongly hoist it out of the arm. Population of "parent not holding ALL child
blocks" = **1652 over the 14 files** vs **6** for the entry test: the containment test must be
the entry one.

## fire census (structural, measured BEFORE trusting the patch)

`tools/treesig.py` = out-of-band analyze-only signature of the whole region tree of **every**
code object of the 14 census files + the population counter "TryExceptRegion adopted by a parent
that does not hold its entry". BASELINE (pristine analyzer, saved to `sig/BASE/*.sig`):

```
quote        CODES=92  TRY_ADOPT_TOTAL=38 NOHOLD=0      quotation CODES=153 TOTAL=47 NOHOLD=0
trade_live_broker CODES=128 TOTAL=56 NOHOLD=6  ← all 6 events of the whole census
wizard       CODES=58  TOTAL=7  NOHOLD=0      real_quote CODES=45 TOTAL=23 NOHOLD=0
klinedata    CODES=64  TOTAL=59 NOHOLD=0      handlers CODES=30 TOTAL=12 NOHOLD=0
event_source CODES=13  TOTAL=8  NOHOLD=0      api_base CODES=28 TOTAL=2  NOHOLD=0
strategy     CODES=27  TOTAL=4  NOHOLD=0      risk __init__ CODES=43 TOTAL=10 NOHOLD=0
trade_info_utils CODES=41 TOTAL=45 NOHOLD=0 · order_api CODES=37 TOTAL=2 NOHOLD=0
matcher CODES=17 TOTAL=0 NOHOLD=0
TOTAL_PRECONDITION_EVENTS = 6, in 1 of 14 files
```

## tightening ladder (populations of the same idea, measured before patching)

```
all child types, entry not held by parent : 171 events, 11/14 files nonzero  → REJECTED untested
                                              (this is the broad-relax shape that cost −20 and −4)
try+with containers                        : superset of the 6, no need (see below)
TRY-ONLY, entry not held  (R33A-1)         :   6 events, 1/14 file  (broker) → PATCHED
```

## readings AFTER R33A-1

Parenting before → after (`_process_cancel_order`; `tools/anatomy.py`, uninstrumented):

```
TryExceptRegion@98.parent   IfRegion@312  →  LoopRegion@46
LoopRegion@46.children      [IfRegion@312, IfRegion@332]
                        →   [IfRegion@312, TryExceptRegion@98, IfRegion@332]
blocks @96/@98/@200/@252/@306 : owner TryExceptRegion@98 in BOTH builds (unchanged, unique);
   ancestor chain IfRegion@312→Loop@46  →  Loop@46  (the lock try/finally is now declared
   INSIDE the loop, exactly as the ticket asked)
TryExceptRegion@420.parent  IfRegion@332  →  IfRegion@332 (unchanged: entry 420 IS held)
```

`_process_order`: the same site claimed 3 of its 6 NOHOLD events (brief's `IfRegion@318`);
after the patch broker-wide `TRY_ADOPT_NOHOLD` = **6 → 0** (treesig, 128 code objects).

Structural fires: **1/14** region trees differ (broker only); the other 13 tree signatures are
byte-identical to `sig/BASE/*.sig`.

Product readings (judge `pyc_verify single --source`, always on my own fresh products):

| file | BASE | V1 |
|---|---|---|
| trade_live_broker | 120/128 | **120/128** (product `cmp` byte-identical: both 175 536 B) |
| quote | 90/92 | 90/92 NOFIRE |
| quotation | 153/153 | 153/153 NOFIRE |
| wizard_quant_api | 57/58 | 57/58 NOFIRE |
| real_quote | 44/45 | 44/45 NOFIRE |
| klinedata | 63/64 | 63/64 NOFIRE |
| handlers | 29/30 | 29/30 NOFIRE |
| realtime_event_source | 12/13 | 12/13 NOFIRE |
| api_base | 27/28 | 27/28 NOFIRE |
| strategy | 26/27 | 26/27 NOFIRE |
| risk `__init__` | 42/43 | 42/43 NOFIRE |
| trade_info_utils | 38/41 | 38/41 NOFIRE |
| order_api | 37/37 | 37/37 NOFIRE |
| matcher | 17/17 | 17/17 NOFIRE |

`TOTAL_PRODUCT_FIRES = 0/14`. Unit shapes unchanged: `_process_cancel_order orig=333 prod=334
delta=+1`, `_process_order orig=507 prod=448 delta=−59`.

## negatives

1. **The criterion is redundant under the mandated pairing.** The banked generator half
   (R32A-2) already defers a body block to its parent *only if that parent holds it*, so the
   lock try/finally is already emitted at the right position; once the analyzer declares the
   same fact, the walk takes the identical route and the text is the same. `cmp` proves it:
   `out/broker.BASE.py` == `out/broker.V1.py` (175 536 B).
2. Counter-factual (my V1 analyzer + **sealed** generator, measured to separate the halves):
   broker still **120/128**, `_process_cancel_order` −293 → **−262**, `_process_order`
   −465 → **−432** ⇒ the parenting fix alone does move the group into the loop, but only
   ~31 instructions of the 293-gap, and it does not flip a unit either.
3. The residual on both victims is 5 / 17 jump-**landing** hunks (`del 1 @@924 JUMP_BACKWARD`,
   `rep 1/2 @@1606 JUMP_FORWARD`, …), the family already proved to have **no channel** in the
   AST-emitting generator; a parenting declaration cannot act on it.
4. Instrumentation hygiene: no probe wrote a product. `anatomy.py`/`treesig.py`/`trace_adopt.py`
   are separate analyze-only processes; the tracer's final tree was verified identical to the
   uninstrumented anatomy dump before I trusted its `site=region_analyzer.py:32280` reading.
   `block.successors` / `get_block_by_offset` were never read inside the analyzer.
5. Tool incident (mine, self-reported): my first patch block had one surplus `)`,
   `py_compile` failed on the mirror while an in-memory splice parsed — resolved by making
   `tools/patch.py` `ast.parse` the rebuilt bytes before writing, and by spelling `min(...)`
   with its close on its own line. The sealed file also has a **UTF-8 BOM + pure CRLF**
   (`b'\xef\xbb\xbf'`, 32 810 CRLF, 0 bare LF), which is why naive byte/line queries misreport:
   read it with `utf-8-sig`.
6. Brief's host line numbers were wrong as warned: adoption happens at **:32280**, not
   :9925-9935 (`region_b.add_child(region_a)`, try↔try pairing, never fired for @98).

## declaration

**NOTHING FLIPPED — `D:/Temp/r33a/DELIVER/region_analyzer.py` IS BYTE-IDENTICAL TO THE SEALED
FILE** (`35e227ac3e7b25af`, 32 810 lines, 2 097 160 B, `py_compile` OK). R33A-1 is therefore
**FALSIFIED as a landing** (0/14 product fires, broker stays 120/128, no unit reaches `Equal`),
even though it is structurally correct and maximally narrow (6→0 mis-parented try regions,
1/14 trees, 13/14 trees byte-identical, 0 decreases on the 14 judged files).

* Changed-line count vs pristine: **0** (delivered file = pristine). The V1 patch itself
  (27 added lines at :32280, `+0/−1` none) is NOT delivered; it is reproducible with
  `python -X utf8 D:/Temp/r33a/tools/patch.py apply V1` (mirror currently reverted).
* **Generator half**: `D:/Temp/r33a/wt/core/cfg/region_ast_generator.py` is
  `CANDIDATE_r32a_generator_pair_half.py` **copied unmodified** (sha16 `a34cdcf4a4ae7147`,
  sha256 `a34cdbf4a4ae71477986ed7c753ea980f91167291a5504af9bfede9503cb2a97`, 59 765 lines,
  +73/−1 vs sealed `c16daa4f87dc68e6`, `py_compile` clean) ⇒ install route is two files, and I
  never wrote that file.
* Revert command (mirror already reverted; repo was never written):
  `cp /d/Temp/r33a/pristine/region_analyzer.py /d/Temp/r33a/wt/core/cfg/region_analyzer.py`
  → sha16 must read `35e227ac3e7b25af` (verified: mirror analyzer `35e227ac3e7b25af`).
* Bankable residue: the containment test at the single adoption site is the *correct* rule for
  try-region parenting and is free of regressions; it only pays off if paired with a generator
  route that consumes `LoopRegion.children` for the try group instead of the `body_blocks`
  deferral (i.e. delete R32A-2's guard in favour of this declaration — a generator-file change,
  outside my file ownership).

