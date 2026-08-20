import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = """                        # [R45 fix] Only skip the as-var cleanup chain (r0, r1,
                        # r2) and RETURN_VALUE, NOT any LOAD_CONST between them
                        # that forms the return value expression. Old code
                        # unconditionally skipped ALL LOAD_CONST after POP_EXCEPT,
                        # erasing return values (e.g. `return 0` -> `return None`).
                        skip_offsets.add(r0.offset)
                        skip_offsets.add(r1.offset)
                        skip_offsets.add(r2.offset)
                        _after_cleanup_r45 = remaining[remaining.index(r2) + 1:]
                        for ri in _after_cleanup_r45:
                            if ri.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                skip_offsets.add(ri.offset)
                                break
                            elif ri.opname in ('RESUME', 'NOP', 'CACHE',
                                               'PUSH_NULL', 'EXTENDED_ARG'):
                                skip_offsets.add(ri.offset)
                            else:
                                break
                        continue"""

new_text = """                        # [R45 fix] Only skip the as-var cleanup chain (r0, r1,
                        # r2) and RETURN_VALUE, NOT any LOAD_CONST between them
                        # that forms the return value expression. Old code
                        # unconditionally skipped ALL LOAD_CONST after POP_EXCEPT,
                        # erasing return values (e.g. `return 0` -> `return None`).
                        # [R06 fix] Skip ALL instructions between as-var cleanup
                        # and RETURN_VALUE (including return value expression),
                        # because the return value was already reconstructed above
                        # (line 18294-18308). Original code broke on non-noise
                        # instructions, leaving return value instructions un-skipped,
                        # causing duplicate Return statements.
                        skip_offsets.add(r0.offset)
                        skip_offsets.add(r1.offset)
                        skip_offsets.add(r2.offset)
                        _after_cleanup_r45 = remaining[remaining.index(r2) + 1:]
                        for ri in _after_cleanup_r45:
                            if ri.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                skip_offsets.add(ri.offset)
                                break
                            elif ri.opname in ('RESUME', 'NOP', 'CACHE',
                                               'PUSH_NULL', 'EXTENDED_ARG'):
                                skip_offsets.add(ri.offset)
                            else:
                                # [R06 fix] Also skip return value expression
                                # instructions (LOAD_CONST, LOAD_FAST, CALL, etc.)
                                # to prevent duplicate Return generation
                                skip_offsets.add(ri.offset)
                        continue"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("Old text NOT found!")
    # Find the exact location
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_after_cleanup_r45' in line and 'for ri in' not in line:
            for j in range(i, min(len(lines), i+15)):
                print(f"  {j+1}: {repr(lines[j])}")
            break
