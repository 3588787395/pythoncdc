# CENSUS_R21-38A_r66a — who renders IfRegion@7270 of `clock_worker`, and why its six leading instructions die

Mirror `D:/Temp/r66` (repo read-only). Base = banked `c4a934d595200c84` (landed+M1+P1+P2) installed as
`core/cfg/region_ast_generator.py`; analyzer untouched at `c069d359cbfe76b0`.

## 0. Control (certifies every reading below)
Mirror at landed bytes (`20fa73b4e8231f0f`, sha256 prefix verified before patching) regenerated
`realtime_event_source.pyc`: product **byte-identical (CR-stripped) to the committed `realtime_event_sourceOK.py`**
(20205 == 20205, IDENTICAL). On the base candidate: `panel14 r66base 12 1` → **units=12/13**, `allwin` →
**delta=-6 hunks=5**, hunk #4 = the six missing instructions `@7270..@7308`.

## 1. Method census (probe log + builder ablation; probes proven inert)
Offset-keyed log probes (no line markers) on 19 methods + cutter counter + `generated_blocks` membership dump:
**product byte-identical to the un-probed base candidate (22322 == 22322)**. Event order for the arm:
`_generate_region(7164) → _generate_if(7164) → _if_generate_normal(7164) → _process_if_blocks(7164,'then',[…7186,7248,7270,…]) → _generate_region(7186) → _generate_if(7186) → _if_generate_full_elif_chain(7186) → _if_generate_elif_chain(7186)`.
**Zero events for entry 7270 and for 7216** — IfRegion@7270 is never dispatched as a region; the only cutter
calls in `clock_worker` are blocks @5598/@5614 from `_loop_generate_while` (R23-B) — never @7270.

Ablation table (stub one method → regenerate; `fused` = product line `elif … and login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:`; `debug` = `system_log.debug('获取重登信号量')`):

| stub | product | fused | debug | verdict |
|---|---|---|---|---|
| `_generate_if`→None | −17188 | 0 | 0 | on path (all ifs) |
| `_if_generate_normal`→None | −16798 | 0 | 0 | renders @7164 arm seq |
| `_if_generate_full_elif_chain`→None | −11322 | 0 | 1 | parent of the emitter |
| **`_if_generate_elif_chain`→[]** | −8140 | **0** | **1** | **the emitter** |
| `_if_generate_branch_stmts`→[] | −485 | 1 | 0 | NOT on path (= r38d inert hookB) |
| `_process_if_blocks`→[] | −15242 | 0 | 0 | walker |
| `_generate_block_statements`→[] | −22211 | 0 | 0 | generic block stmts |
| `_build_statements_from_instructions`→[] | −50 | 1 | 0 | never sees @7270 prefix |
| `_generate_region`→None | −18074 | 0 | 0 | dispatcher |
| `_loop_generate_body`→[] | −8585 | 0 | 0 | container |
| `_loop_process_header_instructions`→None | SAME | 1 | 0 | off path |
| `_discover_predicate_and_chain_forward`→None | **SAME** | 1 | 0 | not the fold here |
| `_chain_block_condition_instrs`→[] | **SAME** | 1 | 0 | ditto |
| `_extract_condition_for_elif_block`→None | **SAME** | 1 | 0 | ditto |
| `_if_extract_cond_instructions`→([],None) | −3210 | 1 | 0 | not the fold |
| `_split_block_condition_prefix`→[] | −50 | 1 | 0 | loop-path consumer only |
| **POSITIVE CONTROL `_if_generate_elif_chain` stubbed ONLY for entry 7186** | −4125 | **0** | **1** | proves this chain's elif_chain call owns the loss |

Fold-site dissection (guard removed one site at a time from my candidate): without the **first-elif-arm
`inline_boolop_chains` consumption site** (base-candidate lines 20163–20180, `if _inline_chain_info:` after the
R21-13 veto block) the fusion stays; without the last-elif site (20626–20640) nothing changes. **Site 1 is the
renderer of this arm.**

## 2. Why the test is `B and C` and where the six instructions go
Analyzer fact (read-only census): `chain@7186` (IF_ELIF_CHAIN) has `elif_conditions=[block@7248]`,
`elif_bodies=[[7372,7488]]`, `elif_final_else=[7492,…]`, and
**`inline_boolop_chains[id(block@7248)] = {'blocks': [7248, 7270], 'op': None}`**. `_if_generate_elif_chain`
rebuilds each chain member by filtering noise+conditional jumps (POP_TOP is dropped by the noise filter) and
feeding `expr_reconstructor.reconstruct` per member, yielding the fused test
`now_date != self.first_run_date and login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False`
(**yes — C is exactly that test**) under the product structure
`if now_date > pre_before_trading_date:` → `if A: pass` / `elif B and C: error;put;return None` / `else: <@7492 stmts>`.
The six debug instructions are **neither consumed into the test (reconstruct silently drops the non-expression
prefix) nor emitted as statements**: the fold ends with
`for _cb in _chain_blocks[1:]: self.generated_blocks.add(_cb)` — block@7270 is marked generated whole.
Census of @7270: role `LOOP_BODY`; `get_region_for_block` = enclosing `TryExceptRegion` (first-write-wins collapse);
declared as entry/condition_block of `IfRegion@7270` (IF_THEN_ELSE, then=[7372,7488], else=[7492], merge=@7582) and
member of @7216/@7164 then_blocks and of the ibc chain [7248,7270]; **in `generated_blocks`: True**;
`prefix_emitted_upto[@7270]`: **None** (never registered); cutter never asked about it.

## 3. Where a fourth consumer must go, and why :4423 double-emitted
Any *emitting* consumer belongs **inside `_if_generate_elif_chain` site 1, in the arm-body assembly of the
UNFOLDED path** (emit prefix stmts + the member's tail test as a nested If into the elif arm before
`_process_if_blocks(elif_bodies)`), never at a `_generate_if` dispatcher: block@7270 never reaches
`_generate_region`/`_generate_if`/`_if_generate_branch_stmts` (probe §1), which is why hookB was fully inert;
hookA at the :4423 dispatcher fires for *every* dispatched IfRegion whose dual-role block was already emitted
whole by the generic block walkers (`_generate_block_statements`/`_build_statements_from_instructions` paths
don't consult `prefix_emitted_upto`), so prepending there duplicates prefixes → +1658 and one lost green unit.

## 4. Candidate (measured) — refusal-only guard, structurally double-emit-proof
`D:/Temp/r66/DELIVER/CANDIDATE_r66a_region_ast_generator.py` **sha16 `07ff9a163b07140a`** (base + module helper
`_r66a_ibc_chain_has_stmt_prefix` + 2 fold-site guards; built by `D:/Temp/r66/build_cand_r66a_ibc_prefix_guard.py`;
BOM+CRLF verified, anchors unique, py_compile OK). The helper reuses only the existing cutter + existing ledger:
refuses the fold iff a non-head chain member has a cutter prefix with offsets above `prefix_emitted_upto`; it
**emits nothing anywhere**, so double emission is impossible by construction.

Measurements (mirror): `panel14 r66p 12 1` → **units=12/13 held**; allwin → **delta=-6 → 0** (prod 1424 == orig 1424),
hunks 5→6: the six @7270 instructions **appear** (with test C re-unfused: `elif B:` … `debug` … `if C: pass`) but land
at the chain tail instead of inside the elif arm (17-instr delete+insert window). Full 20-file panel: **19 files
byte-identical SAME, 1 CHANGED (realtime), 0 flips, 0 regressions** — the guard fires exactly in this file.
Verdict: success bar met (6 instructions present, delta 0, 12/13 held); the residual is a PLACEMENT problem
(owner: `_if_generate_elif_chain` arm-body assembly), not an emission problem; closing hunk #4 fully needs the
nested-If injected ahead of `elif_bodies` — deeper than a fourth-consumer ticket, flagged for adjudication.

Repo `core/` and `site-packages/` untouched (`git status --porcelain` empty); `D:/Temp/r30chk` not written.
