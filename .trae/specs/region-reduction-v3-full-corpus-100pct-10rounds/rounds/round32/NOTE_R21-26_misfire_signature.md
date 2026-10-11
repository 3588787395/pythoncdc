# R21-26 evidence — the exact signature of the handlers criterion's mis-fire

Measured 04:07 on r50a's second live build (`78f88001394ed59b`, still mid-flight: `handlers` reaches
`delta=0 hunks=0 landings=0 judge_diff=False` = **30/30**, and **all six canaries regress by exactly one
unit**):

| file | sealed | under this build |
|---|---|---|
| `IQCommon/arg_checker.pyc` | 49/49 | **48/49** |
| `IQData/utils/arg_checker.pyc` | 39/39 | **38/39** |
| `IQEngine/utils/arg_checker.pyc` | 43/43 | **42/43** |
| `IQCommon/profiler_func.pyc` | 17/17 | **16/17** |
| `IQData/utils/profiler_func.pyc` | 15/15 | **14/15** |
| `IQEngine/utils/profiler_func.pyc` | 18/18 | **17/18** |

Each file loses exactly one unit, and the two distinct shapes broken are
`ArgumentChecker.is_valid_date.check_is_valid_date` and `ProfilerTool.show_func`.

## Both damages are byte-for-byte the same defect

```
ProfilerTool.show_func                     len orig=275 prod=274 delta=-1  hunks=1 landings=0
  - @132  LOAD_CONST  None
  - @134  RETURN_VALUE
  + @132  JUMP_FORWARD

ArgumentChecker.is_valid_date.check_is_valid_date   len orig=94 prod=93 delta=-1 hunks=1 landings=0
  - @12   LOAD_CONST  None
  - @14   RETURN_VALUE
  + @12   JUMP_FORWARD
```

So the criterion, when it mis-fires, **deletes the function's implicit `return None` tail and threads a jump
into the following block instead** — the exact inverse of its stated purpose, which is to re-use a shared
tail. That is what "the then-tail `return None` is a real per-edge landing (single-pred `pure-none`
non-join)" was supposed to exclude and evidently does not: in both canary shapes the tail is
**compiler-synthesized** (the source has no `return None` statement at that point), and the criterion's
predicate cannot tell a synthesized tail from a real one, so it re-declares the arms and the tail collapses.

## The narrowing this implies (hand to the next attempt, do not re-derive)

Require the tail to be an *explicit* source statement rather than the function's implicit terminal block.
Facts available at the decision point that separate the cases:
- `handlers._target`'s arms contain a real `return None` written by the source (two exits, per-edge copies);
- the canaries' `LOAD_CONST None/RETURN_VALUE` sits at the function's terminal offset and is reached by
  **fallthrough** from the previous block, not by a conditional jump whose operand names it.
So a candidate conjunct is: the block providing the tail must be the *target* of the region's own condition
jump(s) (an operand-named landing), not merely the next block in offset order. Both canary cases fail that
test and the victim passes it — but measure it, don't adopt it: I have written conjuncts before that read
correctly against one pair and fired wrongly corpus-wide.

Two more things worth knowing before editing: the mis-fire is **systematic across all three package copies**
of each duplicated module, so a fix that helps one copy and not the others is not a fix; and 6 files × 1
unit = the −6 units the gate reported at gate 31 attempt 1, which the 14-file panel could not see at all.
