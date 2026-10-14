# DIAG B128 — `matcher.DefaultMatcher.match`: where does the 10-instruction slice-test statement get dropped?

SCOPE: DIAGNOSTIC ONLY. No production edits, no battery. Scratch: `D:/Temp/r10diag/`.

## Questions (to be answered with evidence)

1. Which function/method call actually drops the statement? Probe from outside by importing
   `core`; print the basic-block instruction grouping for the block containing the 10 instructions
   and show what the block-statement builder produces / which branch discards the
   slice + `in` expression (look for an expression-reconstruction helper returning `None`/empty
   whose caller then emits nothing).
2. Is the discard SILENT (no diagnostic, no fallback)? If so, name it as a `rules.md` §1.5 C3 violation.
3. Minimal source-level repro (≤ 4 tiny variants):
   `if a.b.c[None:2] in T:`, `if x[0:1] in T:` in a loop, `if x[None:2] == v:`,
   control `if a.b in T:`. Report which reproduce.
4. Exact fix site: file, function, line numbers, and the mis-firing condition stated ONLY with
   whitelisted facts (opcode / block-tail / successor / region membership). No counts, depths,
   names, offsets.

## Answers

### Q0 — located facts about the block (probe `D:/Temp/r10diag/probe1.py`, `probe2.py`)

Unit = `<module>.DefaultMatcher.match` (`co_qualname 'match'`, `co_firstlineno 176`, `co_code` 4968 B).
`build_cfg(code)` → 78 blocks. `cfg.get_block_by_offset(2164)` returns **exactly one basic block**
whose instruction list is precisely the 10 dropped instructions — no other instruction shares the block:

```
blk#47  2164 LOAD_FAST order | 2166 LOAD_ATTR asset | 2176 LOAD_ATTR symbol
        2186 LOAD_CONST None | 2188 LOAD_CONST 3 | 2190 BUILD_SLICE 2
        2192 BINARY_SUBSCR | 2202 LOAD_CONST ('688','689') | 2204 CONTAINS_OP 0(in)
        2206 POP_JUMP_FORWARD_IF_FALSE -> 2464
  successors: [2208-2210 (fall-through), 2464-2466 (taken)]
  predecessors: 1834-1882, 1884-1894, 1896-1906, 1908-1910, 2038-2078, 2080-2158
  is_conditional() True, loop_header False, loop_depth 0
```

Region tree (`CFGRegionAnalyzer.analyze()`, 45 top-level regions):
**no region has `condition_block == blk(2164-2206)`**. The block is a plain *member* of
`IfRegion(IF_ELIF_CHAIN)` whose `condition_block = blk(2080-2158)`; the next inner region is
`IfRegion(IF_THEN)` with `condition_block = blk(2208-2210)`, i.e. the analyzer treats
`2164-2206` as fall-through inside the elif chain and hands the *next* block over as the head of an
`if is_first_five_trading_days`-style region.

### Q1 — drop site: FOUND (probes `D:/Temp/r10diag/probe3.py`, `probe4.py`)

`_generate_block_statements(blk 2164)` **is** called and returns `[]`; the inner
`_generate_block_statements_body` also returns `[]`. The block is nevertheless registered as
"already generated" — so no later per-block degradation path can recover it
(`tb in gen.generated_blocks == True`, `2164 in gen.generated_offsets == True`).

`sys.settrace` line trace of the single call to
`RegionASTGenerator._generate_block_statements_body` (`D:/Temp/r10diag/probe4.py`, 377 events,
full log `D:/Temp/r10diag/probe4.out`) walks every guard (all skip-guards, the
chain/unpack/comprehension/await/boolop attempts — `_has_boolop` False, `_cond_jump_bs` = the
`POP_JUMP_FORWARD_IF_FALSE` at 2206) and exits at **`core/cfg/region_ast_generator.py:54921
`return stmts`** through the `_cjb_skip_inline_if` branch. The tail of the trace verbatim:

```
54778 if _cond_jump_bs is not None:            # 2206 POP_JUMP_FORWARD_IF_FALSE
54779   _cjb_succs = list(block.conditional_successors)   # [2208, 2464]
54780   _cjb_jump_target = _cond_jump_bs.argval            # 2464
54787     _cjb_then_entry = _cjb_cs                        # 2208 (fall-through)
54785     _cjb_else_entry  = _cjb_cs                       # 2464 (taken)
54816   _cjb_cond_instrs = [2164..2204]                    # 9 instrs, jump excluded
54861   _cjb_pure_cond   = _cjb_cond_instrs
54865   _cjb_cond_expr = self.expr_reconstructor.reconstruct(_cjb_pure_cond)
54866   if _cjb_cond_expr is None:  -> NOT taken           # reconstruction SUCCEEDED
54886   if _cjb_then_entry and _cjb_then_entry not in self.generated_blocks:
54887     _er = self.region_analyzer.get_entry_region_for_block(_cjb_then_entry)   # IfRegion(IF_THEN) entry=2208
54888     if _er and _er.entry == _cjb_then_entry and isinstance(_er, _ALL_REGION_TYPES):
54889       _cjb_skip_inline_if = True      # <<< inline `if` suppressed HERE
54890       _cjb_pend_key = _cjb_then_entry
54896   if _cjb_skip_inline_if:
54897     if _cjb_pre_stmts:                # empty -> nothing extended
54899     if _cjb_pend_key is not None and _cjb_pure_cond:
54900       _pend_expr = _cjb_cond_expr     # the full Subscript+Compare dict
54901       if isinstance(_pend_expr, dict) and not Constant(True):  -> True
54906       setattr(_cjb_pend_key, '_leading_operand', (_pend_expr, 'and', 2464))
54918       self._leading_guard_candidate(_cjb_pend_key, _pend_expr, _cjb_jump_target)
54920   self.generated_blocks.add(block)
54921   return stmts                        # stmts == []  -> THE DROP
```

So: **the expression is NOT the failure** — `ExpressionReconstructor.reconstruct` returns the
complete `Compare(Subscript(Attribute(Attribute(order,'asset'),'symbol'), Slice(None,3)), 'in',
('688','689'))` dict. The statement is dropped because the emitter *defers* ownership to a
consumer that never runs.

The deferred handoff has two independent records (both keyed on the fall-through entry block):

| record | setter | ONLY consumer | fires for our case? |
|---|---|---|---|
| `_leading_operand` (R75 fix1) | `:54906` | `_graft_pending_operand` `:38289`, called **only** from `_build_boolop_expression` `:38412` → `BoolOpRegion` only | **NO** — fall-through 2208 owns an `IfRegion`, `_build_boolop_expression` is never called for it. Probe `probe5.py`: `then._leading_operand` is still set on the block **after** `generate()` returns ⇒ written, never read. |
| `_leading_guard` (R76-A1/A2) | `_leading_guard_candidate` `:38472` (sets at `:38516`) | `generate()` top-level region loop, `:1874` | **NO** — candidate returns False at its **[C3] guard ① `:38496`** `if getattr(_R, 'parent', None) is not None: return False`. Probe `probe5.py`: `get_entry_region_for_block(2208)` is `IfRegion` with `entry is then == True` but **`parent = LoopRegion`** (the `for account, order in open_orders:` header at 6-8). ⇒ nested IfRegion ⇒ no record ⇒ `then._leading_guard is None`. |

The return value of `_leading_guard_candidate(...)` at `:54918` is **discarded** — the emitter does
not test it, so a failed registration is indistinguishable from a successful one from the emitter's
point of view, and `:54920-54921` proceeds to claim the block and emit nothing.

### Q2 — the discard is SILENT: YES (`rules.md` §1.5 C3-class violation)

`D:/Temp/r10diag/probe4.out` shows the branch reaches `return stmts` with `stmts == []`: no
`logger`/`warnings`/`print`, no counter, no `_debug` env gate (contrast the neighbouring
`52520/53277/53425` `os.environ.get('R23N6_DEBUG2'|'R23N6_DEBUG5'|'R16_DEBUG')` hooks), and **no
fallback** — the reconstructed `_cjb_cond_expr` is dropped on the floor while still in hand, and the
block is added to `generated_blocks` (`:54920`) so the `except Exception` per-statement degradation
in `generate()` (`:1887` `_generate_degraded_statements`) can never see it either. The code's own
docstring at `:54913` claims the guard record exists "替代此处对条件的静默丢弃" ("to replace the
silent discard of the condition here"), yet the guard path is gated to top-level regions only, so
for every nested host the silent discard it advertises against is still the executed behaviour.
This is a *silent exemption with no diagnostic and no fallback*, i.e. exactly the §1.5 C3 shape.
