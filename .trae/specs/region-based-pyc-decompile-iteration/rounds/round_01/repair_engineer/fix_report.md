# Round 01 Fix Report

## Target
IQCommon/strategy/strategy.pyc (fn=2, previously 50% match)

## Result
100% bytecode match (2/2 functions OK)

## Bugs Fixed

### Bug 1: import X.Y as Z decompiled as from X.Y import Z
- **Root cause**: The fromlist constant (LOAD_CONST before IMPORT_NAME) was not checked to distinguish bare import with alias from from-import. Both have IMPORT_FROM instructions, but `import X.Y as Z` has fromlist=None while `from X.Y import Z` has fromlist=tuple.
- **Fix**: Added `_fromlist_is_none` check at all 6 import handling locations in region_ast_generator.py. When fromlist=None and IMPORT_FROM is present, emit Import with asname instead of ImportFrom.
- **Extended lookup**: Increased STORE_* search range from 3 to 8 instructions ahead to handle the `IMPORT_FROM + SWAP + POP_TOP` sequence in import-as patterns.
- **State machine fix**: Added `_imp_fromlist_is_none` tracking in _build_statements_from_instructions, with SWAP/POP_TOP skip for import-as sequences.

### Bug 2: Nested try/except with return in except handler
- **Root cause**: In `_extract_except_handler` (region_analyzer.py:8398-8425), `_collect_body` stopped at POP_EXCEPT blocks. In nested try/except with return in handler, CPython splits POP_EXCEPT and return into separate blocks. The return block was orphaned into the outer region instead of the inner handler body.
- **Fix**: Changed `_collect_body` to follow normal (non-exception) successors of POP_EXCEPT blocks, while filtering out exception successors that lead to outer handlers. Added guard: if the normal successor contains PUSH_EXC_INFO/CHECK_EXC_MATCH, it's an outer handler entry and is skipped.

### Bug 3: Multi-context with statement missing return
- **Root cause**: In `_generate_with` (region_ast_generator.py:23097-23141), the successor check only looked at direct successors for SWAP+RETURN_VALUE together. For multi-context with, these are in different blocks in a chain, so the check failed.
- **Fix**: Extended successor check to follow chains of WITH_EXIT_CALL blocks through the cleanup sequence until finding RETURN_VALUE. Also extended `_detect_with_body_return` (region_analyzer.py:6014-6019) to skip ALL `as` targets from with_region.items, not just the first.

## Regression Results
- quotation.pyc: 147/150 (no degradation)
- All 12 repros: 10 PASS, 2 PARTIAL (repro_04 and repro_12 have different patterns not targeted this round)
- pytest subset: 168 passed, 9 xpassed, 2 pre-existing failures (no regression)
- Batch test: 100/138 functions in 20 partial pycs (72.5%)

## Index Update
- pyc_index.json: 291 -> 293 OK, 111 -> 109 partial
- OK rate: 72.4% -> 72.9%

## Anti-pattern Check
0 new _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ prefixes added.
