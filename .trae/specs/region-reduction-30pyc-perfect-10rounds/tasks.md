# Tasks

- [ ] Task 1: Round 1 — Fix trade_info_utils.pyc (75% → 100%)
  - [ ] SubTask 1.1: Test engineer: decompile trade_info_utils.pyc, analyze 10 mismatching functions, create 10+ minimal repro cases
  - [ ] SubTask 1.2: Fix engineer: analyze repro cases, fix try/except boundary + control flow in region_analyzer.py and region_ast_generator.py
  - [ ] SubTask 1.3: Verify trade_info_utils.pyc reaches 100% bytecode match, generate OK.py
  - [ ] SubTask 1.4: Batch regression test on all 30 partial files
  - [ ] SubTask 1.5: Commit and push Round 1

- [ ] Task 2: Round 2 — Fix next lowest-rate pyc (real_quote.pyc 79.6%)
  - [ ] SubTask 2.1: Test engineer: decompile and analyze mismatches, create repro cases
  - [ ] SubTask 2.2: Fix engineer: fix region analysis for identified patterns
  - [ ] SubTask 2.3: Verify target pyc reaches 100%, batch regression
  - [ ] SubTask 2.4: Commit and push Round 2

- [ ] Task 3: Round 3 — Fix plugin_system_log/__init__.pyc (80%)
  - [ ] SubTask 3.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 3.2: Fix engineer: fix identified patterns
  - [ ] SubTask 3.3: Verify, batch regression, commit and push

- [ ] Task 4: Round 4 — Fix fly/data/quote.pyc (80.3%)
  - [ ] SubTask 4.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 4.2: Fix engineer: fix identified patterns
  - [ ] SubTask 4.3: Verify, batch regression, commit and push

- [ ] Task 5: Round 5 — Fix trade_live_broker.pyc (83.2%)
  - [ ] SubTask 5.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 5.2: Fix engineer: fix identified patterns
  - [ ] SubTask 5.3: Verify, batch regression, commit and push

- [ ] Task 6: Round 6 — Fix strategy.pyc (83.3%)
  - [ ] SubTask 6.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 6.2: Fix engineer: fix identified patterns
  - [ ] SubTask 6.3: Verify, batch regression, commit and push

- [ ] Task 7: Round 7 — Fix fileio_utils.pyc (85.7%)
  - [ ] SubTask 7.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 7.2: Fix engineer: fix identified patterns
  - [ ] SubTask 7.3: Verify, batch regression, commit and push

- [ ] Task 8: Round 8 — Fix quote_handler.pyc (86.0%)
  - [ ] SubTask 8.1: Test engineer: analyze and create repro cases
  - [ ] SubTask 8.2: Fix engineer: fix identified patterns
  - [ ] SubTask 8.3: Verify, batch regression, commit and push

- [ ] Task 9: Round 9 — Fix remaining partial pyc files
  - [ ] SubTask 9.1: Test engineer: batch analyze all remaining partial files
  - [ ] SubTask 9.2: Fix engineer: apply fixes for remaining patterns
  - [ ] SubTask 9.3: Verify all remaining, batch regression, commit and push

- [ ] Task 10: Round 10 — Final verification and all 402 pyc 100%
  - [ ] SubTask 10.1: Full batch verification on all 402 pyc files
  - [ ] SubTask 10.2: Fix any remaining issues
  - [ ] SubTask 10.3: Final commit and push

# Task Dependencies
- Task 2 depends on Task 1 (must fix lowest-rate file first)
- Task 3 depends on Task 2
- Each subsequent round depends on previous round completion
- SubTask N.3 (verify) depends on SubTask N.2 (fix)
