# R38 diag A — sub-shape B: deleted loop back edge at end of an if-arm (6 rows)

Status: IN PROGRESS (skeleton)

## 0. Task / fact base (given, not re-derived)
- Anchor: `IQCommon/util/common_func.pyc :: fill_kline_data` 60/59, j4 t16.
- Deleted instruction: `@188 JUMP_BACKWARD -> 138` (the `FOR_ITER` loop head), which is the
  true-arm's exit at the end of an if-arm; the very next block `@190..` is the arm's
  conditional successor (the "else" side) and got emitted as a *sequential* statement.

## 1. Firing site — TBD
## 2. Discriminator — TBD
## 3. Candidate predicate + hunk — TBD
## 4. Battery — TBD
## 5. Measured before/after — TBD
