# r38 diag B — sub-shape A: duplicated trailing `JUMP_BACKWARD` swallowed by elif flattening

STATUS: in progress (skeleton)

## 0. Fact base (given, not re-derived)
- 2 corpus rows owned here:
  1. `IQCommon/strategy/wizard_quant_api.pyc :: wizard_quant_check_limit` 91/90 j2 t10  (anchor)
  2. `IQCommon/api/klinedata.pyc :: get_all_real_daily_kline` 188/187 j3 t26
- Whole deficit = ONE deleted `JUMP_BACKWARD`; original emits the same back-edge twice in a row,
  then `PUSH_EXC_INFO` (enclosing try's handler entry).

## 1. Firing site (TBD — measured)
## 2. Discriminator (TBD)
## 3. Candidate predicate + spec hunk (TBD)
## 4. Battery (TBD)
## 5. Measurements (TBD)
## 6. Equal-length transposition group verdict (TBD)
