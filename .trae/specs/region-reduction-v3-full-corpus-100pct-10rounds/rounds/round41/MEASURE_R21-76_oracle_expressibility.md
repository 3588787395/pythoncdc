# [R21-76] oracle expressibility measured by the orchestrator (14:48) - no hand-composed variant reaches 13/13 yet

Per file: `python -X utf8 scripts/pyc_verify.py single
site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc --source <file>`
(`--source` mandatory; without it the judge grades the stale in-place product).

| r103a's composed oracle variant | judge line |
|---|---|
| `GOLD_realtime_event_source_PROOF.py` (22,377 B) | `status=failure units=12/13` |
| `GOLD_varA_holiday.py` (22,111 B) | `status=failure units=12/13` |
| `GOLD_varB.py` (21,853 B) | `status=failure units=12/13` |
| `GOLD_varC.py` (21,254 B) | `status=failure units=12/13` |

All four are hand-composed source texts judged against the same pyc the pipeline also reads 12/13 on, so this is
the expressibility probe, not a pipeline run.

Why it matters: the broker axis only moved once an oracle text judged `128/128`, because that turns the work into a
scored distance and every later candidate became measurable as "how far from a proven-reachable text". Here **no
composed text reaches 13/13**, so nothing is installable on the strength of a shrinking delta, and two readings stay
open and must be separated before another dispatch:

1. a source shape still untried (this campaign was surprised twice by CPython shape laws - the duplicated
   `while <BoolOp>` test, and `handlers._target`'s per-exit-edge duplication); or
2. the dropped block `@7972..@8586` is **not expressible from any single source text**, because all its arms share
   the loop back-edge/merge `@9194` and no per-statement label survives.

Cheap discriminator for the next hand, no pipeline needed: compile each variant and diff the **block/edge census**
(predecessors and landings per block, jump targets included) against the original code object's census for that
region - not the text. Reading 2 is confirmed when no shape reproduces the original's jumper/label structure.

## Census discriminator already run (14:51) - varC is ONE structural fact away, so reading 1 is live

Comparing `dis` edge censuses (jump targets kept, unlike the text tools):

| source | instrs | back-edges | fwd-edges | blocks with >=2 preds | top in-edge counts |
|---|---|---|---|---|---|
| **ORIGINAL pyc** `clock_worker` | **1442** | **4** | **119** | **15** | 6 -> @9194, 5 -> @4984, **4 -> @9144**, 3 -> @7164, 3 -> @6280, 2 -> @8588 |
| `GOLD_realtime_event_source_PROOF` | 1443 | 4 | 121 | 11 | 10 -> @9066, 5, 5, 3, 3, 2 |
| `GOLD_varA_holiday` | 1459 | 4 | 122 | 11 | 10 -> @9166, … |
| `GOLD_varB` | 1440 | 5 | 121 | 12 | 10 -> @9166, … |
| **`GOLD_varC`** | **1442** | **5** | **120** | **14** | 7 -> @9198, 5, 5, 3, 3, 2 -> @9148 |

`GOLD_varC` already matches the original's **instruction count exactly (1442)** and is off by one back-edge
(5 vs 4), one forward-edge (120 vs 119) and one multi-predecessor block (14 vs 15), while its loop re-entry has 7
incoming jumps where the original has 6 and the original's loop tail `@9144` has 4 predecessors, which no variant
reproduces. So the target is **not** hopeless: the remaining gap is a single, nameable structural fact —
*thread one of the arms' exits so the re-entry label loses one jumper and the loop-tail label `@9144` gains the
predecessors the original has, without adding a backward edge*. That is a shape question with a countable answer,
not a text question, and it is the criterion the next candidate must be scored on before spending a judge run.
