import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = """            # as-var cleanup 命中，检查其后是否紧跟 RETURN_VALUE / RETURN_CONST
            for ri in remaining[r_idx + 3:]:
                if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if ri.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    return True
                break
        return False"""

new_text = """            # as-var cleanup 命中，检查其后是否紧跟 RETURN_VALUE / RETURN_CONST
            # [R06 fix] Allow return value expression (LOAD_CONST, LOAD_FAST, etc.)
            # between as-var cleanup and RETURN_VALUE. Original code breaks on
            # non-RETURN_VALUE instructions, causing return value expressions to
            # be misidentified as non-cleanup instructions, returning False.
            for ri in remaining[r_idx + 3:]:
                if ri.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if ri.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    return True
                # Allow return value expression instructions between cleanup
                # and RETURN_VALUE (e.g. LOAD_CONST False in `return False`)
                continue
        return False"""

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
        if 'as-var cleanup' in line and 'RETURN_VALUE' in line:
            for j in range(max(0, i-1), min(len(lines), i+8)):
                print(f"  {j+1}: {repr(lines[j])}")
            break
