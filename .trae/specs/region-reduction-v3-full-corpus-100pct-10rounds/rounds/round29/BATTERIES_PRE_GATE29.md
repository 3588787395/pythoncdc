# Battery baseline re-sealed on the UNTOUCHED tree, 19:36 local / pre-gate-29

口径 = each dir's own committed runner, cwd = repo root (`ROOT` self-printed by the first runner),
HEAD `c0744254`, `git status --porcelain -- core parsers utils bytecode scripts pycdc.py` empty.
Log: `D:/Temp/t29/batt_pre_901.log`.

| battery | runner | reading this run | recorded base | match |
|---|---|---|---|---|
| repro | `rounds/round14/repro/run_repro.py` | `RED=9 / 9` | 9R/9 | ✓ |
| arm | `rounds/round14/repro_arm/run_arm.py` | `GREEN=0 RED=3 / 3` | 0G/3R | ✓ |
| ccneg | `rounds/round14/repro_ccneg/run_ccneg.py` | `GREEN=3 RED=1 / 4` | 3G/1R | ✓ |
| retbreak | `rounds/round18/repro_retbreak/run_retbreak.py` | `GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4` | 2G/2R DRIFT=0 | ✓ |
| orderapi | `rounds/round19/repro_orderapi/run_orderapi.py` | `GREEN=5 RED=0 / 5` | 5G/0R | ✓ |
| tail | `rounds/round19/repro_tail/make_tail.py --run` | `GREEN=13 RED=0 / 13` | 13G/0R | ✓ |

Relevance to the four tickets in flight this round (R21-13 or-chain leg lift, R21-14 synthetic
`while True` wrapper turning `return None` into `break`, R21-15 loop fall-through emitted as a loop
exit, R21-16 handler suite stealing the blocks after the `Try` node): `retbreak` already carries
`r02_break_arm_control` as a **RED** arm (`while not self.stop: / try: / ... / if self.flag: break`)
and `r03_return_in_else_suite` + `r04_two_return_arms` as **GREEN**, so a correct R21-14/R21-15
patch should be visible as `r02` turning GREEN with `DRIFT_VS_BASELINE` staying 0; `tail`'s
`t10_two_returns_same_value` is GREEN today, so any candidate that breaks it is over-claiming.
Any post-install reading different from the table above is a regression signal for the gate, not an
improvement, unless it is exactly `r02` RED->GREEN and is attributed to the installed criterion.
