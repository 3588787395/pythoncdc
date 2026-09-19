# Tasks

- [ ] Task 1: Round 1 — Fix trade_info_utils.pyc (75% → 100%)
  - [ ] SubTask 1.1: Test engineer: decompile trade_info_utils.pyc, analyze 10 mismatching functions, create 10+ minimal repro cases
  - [ ] SubTask 1.2: Fix engineer: analyze repro cases, fix try/except boundary + control flow in region_analyzer.py and region_ast_generator.py
  - [ ] SubTask 1.3: Verify trade_info_utils.pyc reaches 100% bytecode match, generate OK.py
  - [ ] SubTask 1.4: Batch regression test on all 30 partial files
  - [ ] SubTask 1.5: Commit and push Round 1

- [x] Task 2: Round 2 — Deep analysis of trade_info_utils.pyc remaining 10 mismatching functions
  - [x] SubTask 2.1: Test engineer: classified 10 mismatches into 2 categories
    - Category A (4 functions, jump-only equivalence): query_strategy_id, query_trade_strategy_info, set_trade_status, check_and_update_trade — POP_EXCEPT vs LOAD_CONST first_diff, raw filtered instructions identical, only jump target layout differs
    - Category B (6 functions, genuine structural bugs): create_user_code_iqe (279), get_last_stat (176), get_user_info (66), kill_trade_process (283), get_trade_unit_info (130), trade_operation (133)
  - [x] SubTask 2.2: Analysis complete — Category A is comparator normalization limitation (not decompiler bug); Category B requires deep decompiler reconstruction fixes
  - [x] SubTask 2.3: Fix Category B structural bugs one by one (P0-1 done: orelse None→[] + per-statement degradation → 5 funcs solved; R2-SWAP deferred return-in-loop → get_user_info solved; R2-With ternary-with overlap → trade_operation with solved; P1-1a boolop chain purity → r2_05 solved)
  - [x] SubTask 2.4: Document findings (test_repros/round2/ANALYSIS.md + 11 repros, 7/11 now match)

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
