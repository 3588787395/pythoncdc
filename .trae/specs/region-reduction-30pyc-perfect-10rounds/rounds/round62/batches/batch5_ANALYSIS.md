# Round 62 batch 5 — read-only diagnosis (targets: logger / flyAccount / order_api / realtime_event_source / matcher)

Baseline: landed bytes sha256 prefix fa0808ca3766b5150dcf ([R62 Fix1] ~wt34605, [R62 Fix2] ~wt35353, Fix3 reverted).
FACTS from D:/Temp/opencode/r62gate/diag5/FACTS.md; targets.txt = 5 pyc.

## Log (append-only)
- [init] workspace created, FACTS/targets read. Plan:
  1. logger.pyc: `logging_process` 99->95 (-4), `write_logging_thread` 113->113 (jump_diffs=1, true_diffs=40, first_diff idx71 LOAD_FAST 'msgs' vs JUMP_FORWARD 612).
  2. flyAccount.pyc: `_do_request` 436->429 (true_diffs=379, first_diff idx54 RETURN_VALUE vs POP_TOP), `init_connection` 42->41 (first_diff idx16 POP_JUMP_FORWARD_IF_FALSE -> POP_JUMP_FORWARD_IF_TRUE, i.e. inverted condition).
  3. order_api.pyc: re-verify Round50 blockers (`_try_build_ternary_kwarg_call` kwarg-slot bail + forward-only chain walk) on current bytes.
  4. realtime_event_source.pyc: else-hood undecidability (R34-E/F) — aim for undecidability + stop proof.
  5. matcher.pyc: re-test R37-B NO-GO on current bytes with measured falsification.
