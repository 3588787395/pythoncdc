# NOTE R21-14 attempt (orchestrator, round 29) — my own patch is FALSIFIED, with the reason and the working probe rig

## What I changed and why it did not flip the unit
Criterion I implemented at `region_ast_generator.py:9772-9774`: the `elif` that accepts a
`LOAD_CONST` exit value required `argval is not None`, so a block that IS an explicit
`return None` (`LOAD_CONST None; RETURN_VALUE`, or 3.11 `RETURN_CONST None`) fell through to the
`body=[{'type':'Break'}]` branch at `:9786`. I added a module-level predicate
`_is_explicit_return_none_block(block)` and an `elif` that renders such a block as
`Return(Constant(None))`, gated on the block's own role being `RETURN`/`RETURN_NONE`.

Measured result on the victim `plugin_system_risk_calculation/__init__.pyc::<module>.PluginRiskCalculation._save_testds_to_csv`:
```
before: len orig=80 prod=73 delta=-7 hunks=3 landings=3   (no `time.sleep(0.01)` in the emitted text)
after : len orig=80 prod=73 delta=-7 hunks=3 landings=3   (text now HAS `time.sleep(0.01)` at product line 256,
                                                          but the arm is still `if THREAD_STATUS: break`)
[single] 42/43 -> 42/43   (no flip)
```
i.e. the predicate fired somewhere in the file (it did change the emitted shape — the second loop's
`while not self._stop_save_csv_thread:` became `while True:` and its `else: return None` disappeared)
yet the arm that loses `time.sleep` still renders as `break`, so CPython still deletes the following
statement. **The operative site for that arm is not the `return None` branch of `:9786`.** Reverted
byte-exactly: `git checkout -- core/cfg/region_ast_generator.py`, `git status --porcelain -- core/`
empty, file back to the gate-29 landed bytes `fd0e4c4d73cf5efc`.

## The probe rig that DOES work here (use it in round 30 before touching a site)
My earlier 6-site line probe read zero fires and I nearly recorded that as a negative about the sites.
The working method is a **line-event trace over the whole candidate set**, with a positive control:
`D:/Temp/t30/tracbreak.py` — `sys.settrace` restricted to `region_ast_generator.py` by basename,
recording hits whose `lineno` is in a supplied set, run through `runpy.run_path('pycdc.py')`
**in-process** (must swallow `SystemExit`, which is why my first two runs produced no log at all),
then `cmp` the product against the sealed one to prove the tracer inert.
Reading for the risk file (probe proven inert, positive control = 2 758 746 line events seen):
```
line 9786  hits=1     line 13376  hits=1     line 25838  hits=4     TOTAL=6 distinct=3
```
and the full `{'type': 'Break'}` site list for sealed-vs-current bytes is 71 lines:
`6099 6161 8506 9786 11961 11970 12106 12194 12222 12291 12728 12740 12752 12766 12821 12825 13340
13346 13348 13371 13376 13395 18408 25834 25838 26663 26682 26698 26987 26989 27016 27392 27427 27570
27602 27604 27636 27638 27683 28880 30644 30676 30754 31065 31127 31132 32610 32769 32771 32902 32948
35228 35338 35492 35501 36822 36836 37154 51945 52740 53270 53302 53319 53345 53713 53720 53726 54766 54778`
(next line numbers after gate 29's +83/-7 shift; re-derive with `grep -n "'type': 'Break'"`).

Round-30 first move for R21-14: trace the same three sites for klinedata (ticket R21-15) and then ask
of the risk victim **which statement the `break` at product line 255 is created by** — the answer must
come from the trace plus the region data of the arm's own block, not from a guessed predicate. Note the
victim's *outer* shape is also wrong (two sequential `while not flag:` loops became
`while True: while not flag: ... else: return None ... while ... break`), and r37a's ablation had
already pinned the wrapper merge decision at `:6917 _can_merge` — force-unwrap alone left
`delta=-7 -> hunks=2 landings=2` with `time.sleep` still missing, so the wrapper and the terminator
must be fixed as a pair or the pairing must be proven non-redundant first.
