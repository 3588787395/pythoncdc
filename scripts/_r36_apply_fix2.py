with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """                _merge_is_return_only = False
                if region.merge_block:
                    _merge_non_noise = [i for i in region.merge_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if _merge_non_noise and all(i.opname in ('RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                                for i in _merge_non_noise):
                        _last_merge = region.merge_block.get_last_instruction()
                        if _last_merge and _last_merge.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            _merge_is_return_only = True"""

new = """                _merge_is_return_only = False
                _merge_return_followup = None  # [R36] RETURN_VALUE block reached via cleanup
                if region.merge_block:
                    _merge_non_noise = [i for i in region.merge_block.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if _merge_non_noise and all(i.opname in ('RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                                for i in _merge_non_noise):
                        _last_merge = region.merge_block.get_last_instruction()
                        if _last_merge and _last_merge.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            _merge_is_return_only = True
                    # [R36] BoolOp merge_block may be a chained-compare cleanup
                    # block (SWAP 2; POP_TOP) whose successor is RETURN_VALUE.
                    # Pattern: `return A < x < B or C < x < D` — the `or` short
                    # circuit jump target and the second chained compare's
                    # cleanup both lead to a RETURN_VALUE block. Follow the
                    # successor chain to find it.
                    if not _merge_is_return_only:
                        _merge_last = region.merge_block.get_last_instruction()
                        if _merge_last and _merge_last.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'JUMP_BACKWARD',
                                                                       'JUMP_BACKWARD_NO_INTERRUPT'):
                            _merge_succs = list(region.merge_block.successors)
                            for _ms in _merge_succs:
                                _ms_non_noise = [i for i in _ms.instructions
                                                 if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                                if _ms_non_noise and all(i.opname in ('RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST',
                                                                       'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                                                       'LOAD_DEREF')
                                                          for i in _ms_non_noise):
                                    _ms_last = _ms.get_last_instruction()
                                    if _ms_last and _ms_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                        _merge_is_return_only = True
                                        _merge_return_followup = _ms
                                        break"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix2 applied")
else:
    print("FAIL: old_string not found")
    # Debug
    idx = content.find("_merge_is_return_only = False")
    if idx >= 0:
        print(f"Found _merge_is_return_only at index {idx}")
        print(repr(content[idx:idx+500]))
