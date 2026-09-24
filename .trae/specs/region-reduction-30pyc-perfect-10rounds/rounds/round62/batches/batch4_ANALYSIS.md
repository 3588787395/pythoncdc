# Round 62 batch4 ANALYSIS

## log
- [init] created; FACTS read. 12 inconsistent funcs across 6 files.
- [facts] landed baseline reproduces FACTS exactly (6/6 files, 2 mismatch funcs each; report truncates mismatches list at 2 but deficit is genuinely 2 per file).
- [note] site-packages/*OK.py are byte-identical to landed decompiler output (no golden source exists); ground truth = pyc bytecode only. probe.py adds --which=dec (recompile landed output).
- [case fileio_utils.acquire] orig: `if time.time()-start>=timeout: [warning block, then fall-through into nested try/os.unlink, then JUMP_FORWARD 502 raise] / else(POP_JUMP_IF_FALSE 532): time.sleep; POP_EXCEPT; loop-back`. landed hoists the fall-through try/unlink block OUT of the if-true and emits `if/else` then try/unlink then raise -> true branch terminated at first block whose exit is an unconditional forward jump; else-branch (532) placed as fall-through continuation.
- [case history_data_source.get_kline_by_count idx19] orig: outer `if len<1 or count==0:` whose THEN region (fall-through target 128, also the or-chain's true-exit target) is a TERNARY `return EMPTY if fields is None else EMPTY[fields]` (2 exits, both -> RETURN_VALUE). landed emits `if len<1 or count==0 or fields is None: return EMPTY` i.e. ternary TEST absorbed as extra `or` operand of the enclosing boolean chain, and ternary else-value block (146) re-parented to the outer else. => candidate family F1 "boolean-chain swallows nested conditional-expression head".
