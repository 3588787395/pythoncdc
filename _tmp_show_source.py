"""Show the decompiled source for _close_holding and make_trade functions."""
ok_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_positionOK.py"
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()

lines = source.split('\n')

for target in ['def _close_holding', 'def make_trade']:
    in_func = False
    func_lines = []
    for i, line in enumerate(lines):
        if target in line:
            in_func = True
        if in_func:
            func_lines.append((i+1, line))
            # Stop at next function def at same indent level
            if len(func_lines) > 1 and line.strip().startswith('def ') and target not in line:
                func_lines.pop()  # Remove the last line (next function)
                break
            # Also stop at class definition
            if len(func_lines) > 1 and line.strip().startswith('class '):
                func_lines.pop()
                break
    
    print(f"\n{'='*80}")
    print(f"Function: {target}")
    print(f"Lines: {len(func_lines)}")
    for lineno, line in func_lines[:80]:
        print(f"  {lineno:4d}  {line}")
    if len(func_lines) > 80:
        print(f"  ... ({len(func_lines) - 80} more lines)")
