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

## Addendum, 16:57 — R21-16's root cause found, and it is an ANALYZER declaration defect
`owner file for R21-16 should be core/cfg/region_analyzer.py, NOT the generator.`
Evidence, from an in-process region dump of `fly/data/quote.pyc`'s `run_individual_transform` code
object (`build_cfg` → `RegionASTGenerator(cfg).region_analyzer.analyze()`, 10 regions):
```
== TryExceptRegion entry=686
   try_blocks             []                              <-- the try body is EMPTY by declaration
   handler_entry_blocks   [754]
   except_handlers        [('BaseException','x', 23 blocks)]
      those 23 blocks include offsets 586, 638, 640, 684, 686, 752, 774, 1024, 1032,
      1050, 1112, 1116, 1240, 1282, 1354, 1396, 1468, 1510, 1578, 1620, 2116, 2208
      i.e. blocks that PRECEDE the region entry (586 < 686) and the try-body blocks themselves
   else_blocks [] finally_blocks [] merge_block None exit_block None continue_map None
```
That single declaration explains the whole emitted shape I read in `quoteOK.py:1326-1347`:
`try:` body `pass` (because `try_blocks` is empty), the handler suite holding everything that should
be the try body and the statements AFTER the try, and — since that handler ends in `continue` —
CPython ≥3.10 deleting the 15 instructions (`message = socket.recv()`, `if message:
message = eval(message.decode())`) that the unit is missing (`delta=-52`).
Criterion to implement: a `TryExceptRegion` whose declared handler body contains blocks with
`start_offset < region.entry.start_offset`, or has `try_blocks == []` while its handler body lists
blocks that precede `handler_entry_blocks[0]`, is mis-assembled — the pre-entry/try-body blocks must be
owned by the region's try side (or by the enclosing loop body), never by the handler. This is a
*correct-at-identification* fix in the analyzer, and `region_analyzer.py` is currently unowned by any
other ticket, so it cannot collide with R21-13's landed generator bytes.
Caveats to honour while implementing: (1) an isolated `analyze()` census can name regions the real run
never renders, so confirm with the live run (the generator-side log of `_generate_try` for `entry=686`
showed `body=1 handlers[...:13]`, i.e. the real run does render this region exactly as dumped);
(2) my monkeypatch driver that produced that log was NOT byte-inert (it wrote 90 167 B against the
sealed 94 155 B because `pycdc.main()` was called with a different cwd/flag path), so treat call-count
numbers as indicative and re-derive any counting reading with the `runpy`-based inert rig;
(3) blast radius is every `TryExceptRegion` in the corpus — run the fire census over the 14-file panel
before delivering, and expect `fly/data/quotation.pyc` 153/153 to be the first thing this breaks.

## Second addendum, 17:03 — two variants of the R21-16 analyzer fix, both MEASURED and REVERTED
The swallow lives in `region_analyzer.py::_extract_except_handler._collect_body` (`:11292+`), the same
walk the `[W21 fix]`/`[W27 fix]` comments already fence (POP_EXCEPT + `JUMP_FORWARD`, POP_EXCEPT +
backward jump). The unhandled third case is a block that contains `POP_EXCEPT`, then only `as`-cleanup
instructions, and **ends without any jump** — its successors are the code after the whole `try`
statement, and following them walks back around the loop into the try body.
Variant A (stop the walk at such a block entirely):
```
run_individual_transform  delta -52 -> -3   hunks 3 landings 2      (the try body IS restored)
fly/data/quote.pyc        91/92 -> 90/92                            (run_tick_socket REGRESSES to Different control flow)
```
Variant B (keep following successors but refuse only those whose `start_offset` is below the handler
entry, i.e. the back edge into pre-handler code):
```
product byte-identical to sealed (94 155 B); delta still -52, file still 91/92   -> NO EFFECT AT ALL
```
Why B is inert: the pre-entry blocks (586/638/640/684) are reached through other blocks of the walk,
not from the POP_EXCEPT-cleanup block itself, so a skip keyed only on that one block never triggers.
**Therefore the next attempt must bound the handler body by the exception table, not by successor
direction.** The data is already in scope at the call site (`:8966-8988`): `handler_info['try_end']`,
`handler_infos[j]['handler_start']`, and `self.cfg.exception_table` entries as
`(start, end, target, depth)`. Note the *last* handler in a region has no following `handler_start`, so
its upper bound must come from the try statement's end, not from the next handler — that is the part
Variant A stumbled on, since cutting at the cleanup block also truncated `run_tick_socket`'s legitimate
handler tail. Both variants are reverted; the tree is back at
`region_analyzer.py = 35e227ac3e7b25af` with the quote product `cmp`-identical to sealed.


