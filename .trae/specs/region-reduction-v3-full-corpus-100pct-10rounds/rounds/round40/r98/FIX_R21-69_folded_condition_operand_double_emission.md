FIX_R21-69_folded_condition_operand_double_emission.md

Engineer r98a, round 40, mirror D:/Temp/r98. Read-only reference repo:
D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main. Deliverable patch only; no repo install.

== Base installed in the mirror and verified (sha256 first 16 hex) ==
  generator core/cfg/region_ast_generator.py = b4363f5858e58074  (landed bytes, copied from repo)
  analyzer  core/cfg/region_analyzer.py      = 1471c92eca157e46  (pinned snapshot
        rounds/round40/r93/region_analyzer_R21-64a_pinned_1471c92eca157e46.py)
  The rig prints "[installed] gen=b4363f5858e58074 ana=1471c92eca157e46".

== Rigs (all in the mirror, so paths resolve to the mirror) ==
  .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round40/orchestrator/
      fastgate_r98.py  = orchestrator fastgate_r91m.py with the mirror constant pointed at
                         D:/Temp/r98 (repro + round-14 battery + optional --full panel)
  win_r91.py           at the mirror root (opcode-name alignment only, so shifted jump
                         operands cannot inflate windows)
  broker_r98.py        at the mirror root (broker regenerate + judge + windows)
  The round-14 battery is copied to the mirror at the same relative depth because the runner
  derives ROOT from its own file path with seven dirname steps; it prints ROOT=D:\Temp\r98.

== Baselines measured in this mirror (before any edit) ==
  [repro mechanism A] rounds/round40/r90/repro/repro_rotated_while.pyc
      ***<module>.sync_worker: Failure: Different bytecode
      [single] status=failure units=1/2 success_rate=50.00%
  [battery no-regression] RED=8 / 9  (base level, neighbouring if/elif chained-compare family)
  [broker] site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
      ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
      [single] status=failure units=127/128 success_rate=99.22%
      [_sync_worker] windows=6 (the r93 base), win header orig instrs=412 prod instrs=431 delta=19

== Defect ==
The repro emits the folded chained-comparison first-operand block a second time as a bare
expression statement (LOAD_FAST then POP_TOP) inside the second while body:
orig instrs=170 prod instrs=172 delta=2, one window at +1106/+1108.
A block consumed by the condition fold must never also be handed to the loop-body statement
sequence (unique block membership). Fix the claim/consumption bookkeeping, not the text.

== Constraints ==
Bottom-up region reduction; unique block membership; nested regions as single abstract nodes;
correct-at-identification (no retrospective repair over the emitted tree); one-way dataflow;
no cross-region/cross-level heuristics; criteria in opcode class / stack shape / region data /
predecessor-successor relations only. Forbidden: function names, file names, absolute offsets,
counters, thresholds, magic numbers. Byte discipline: UTF-8 BOM, all-CRLF, patch by splitting
on CRLF, unique anchors, assert zero stray CR-CR-LF triples after every write, py_compile each
time. Rule label: [R21-69 ...].


== SITE PROVEN BY MEASUREMENT (step 2) ==
Emitter of the stray body statement in the repro:
  RegionASTGenerator._loop_extract_self_loop_stmts, the residual-buffer flush at landed line
  12035-12038 (`if _self_loop_instrs:` / `_stmt = self._build_statement(_self_loop_instrs)`),
  reached from _loop_generate_body for the second while (hdr=1064, cond=886, body=[1064,1240,1278]).
Evidence chain (all measured in this mirror):
  1. inert logging probe dbg3_r98.py (15 named plain-function emitters wrapped; product
     comment-stripped byte-identical to the ungarded product => PROBE3_INERT):
       _build_statement [1064..1092] -> time.sleep(1)
       _build_statement [1104..1104] -> Expr(Name 'pre_before_trading')   <-- the stray
       _loop_extract_self_loop_stmts @1064 -> ['Expr', 'Expr']
     A blanket wrapper over all 322 methods is NOT inert (product 977 vs 605 bytes) because
     classmethod descriptors rebind; only the named plain-function set is safe.
  2. boundary replay probe2_r98.py (dump-only): header @1064 has 23 instructions, terminal
     POP_JUMP_FORWARD_IF_FALSE -> FORWARD branch of _loop_extract_self_loop_stmts; the
     backward dis.stack_effect simulation breaks at idx7 (@1106 LOAD_GLOBAL int), so
     _body_end_idx=6 (@1104). The flat stack effect cannot see that the leg's SWAP 2 / COPY 2
     need the value pushed at @1104, so the leg's operand prefix stays inside the body range
     and is flushed as a bare expression statement (LOAD_FAST + POP_TOP = the delta=2).
  3. ablation (ablate_r98.py flush_off, unconditional => deliberate over-fire):
     repro 1/2 -> 2/2, windows 1 -> 0, stray line gone. Broker _sync_worker byte-identical
     (units 127/128, windows 6, delta 19) => the real unit's 6 windows are NOT this site.

== CANDIDATE [R21-69] ==
Generator half only: core/cfg/region_ast_generator.py, sha16 f1af4faa87e842bc
(installed from landed b4363f5858e58074 by patch_r98.py; 61174 -> 61220 lines; py_compile OK;
BOM + all-CRLF + zero CR-CR-LF asserted by byteio_r98.write_lines).
Rule: new claim test _r2169_is_folded_condition_leg_prefix + one hook at the flush, which
returns the body sequence at the previous statement boundary when the residual is the operand
prefix of the duplicated test copy. Conjuncts (region data / opcode class / stack shape only):
  (1) the loop has its own condition_block and it is not this header (the rendered test came
      from another block, so this block's tail can only be a copy of it);
  (2) the header tail from the residual's first instruction to the block end, noise ops
      dropped, has the same opcode-name sequence as the condition block (jump operands are
      not compared - the AST carries none and the copies differ only in them);
  (3) that tail ends in a conditional jump and contains no STORE_* (a binding statement is
      never a pure test copy);
  (4) the residual itself is not a self-contained statement, judged by the landed [R21-56]
      consumption criterion _r2156_tail_is_bounded_statements (no conditional jump inside and
      no statement-close op at the end) => its pushed value has no body-side consumer, it is
      the copy's first operand.
No names/constants/absolute offsets/counters/thresholds; failure of any conjunct returns
False and the product is byte-identical to the landed behaviour.

== MEASUREMENTS UNDER THE CANDIDATE ==
  [repro]      status=success units=2/2 success_rate=100.00%   windows=0   (base 1/2, windows=1)
  [broker]     ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
               units=127/128  windows=6  orig instrs=412 prod instrs=431 delta=19
               => UNCHANGED vs base; the real unit is NOT closed by this half (see below)
  [battery]    RED=8 / 9  ROOT=D:\Temp\r98   (unchanged)
  [panel]      realtime 12/13 (clock_worker the sole red, same as base) - replace_utils 9/9
               - function 15/15 - order_api 37/37 - quote 92/92 - quotation 153/153

== WHY THE REAL UNIT STILL NEEDS MORE (measured, not assumed) ==
The real unit's second while is a single chained comparison (`pre <= int(..) < int(post)`),
which the campaign's own census reports as P-negative (predicate [R21-64] fires only on
or-chain tests), so its latch copy is never folded/claimed at all: probe3_r98.py on
_sync_worker shows loop hdr=2072 cond=1890 backedge=2844, header effective opcode sequence
`LOAD_CONST STORE_FAST LOAD_FAST LOAD_ATTR BEFORE_WITH` (a with-statement prologue, carries
STORE_*), i.e. the duplicated leg is NOT the header tail here. dbg4_r98.py (same wrapped set,
inert) names the emitter of the real unit's copy: _loop_generate_body returns the body list
that already contains the If(not chained-compare) -> Continue statement; neither
_loop_extract_self_loop_stmts nor the residual flush appears. Ablation agrees: killing the
flush leaves the broker byte-identical (delta 19, windows 6).
So the surviving windows in the real unit belong to (a) the P-negative duplicated test
emitted as `if not <chain>: continue` by _loop_generate_body, plus the other textual facts
against GOLD (reconnect return-vs-break, unguarded sync_data_flag = 1). Those are the
sibling-predicate axis (analyzer, r93a's rule), which this ticket must not restructure.