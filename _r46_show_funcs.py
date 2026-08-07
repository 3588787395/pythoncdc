"""Show decompiled source of specific functions in future_positionOK.py"""
import sys
sys.path.insert(0, '.')

with open('site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_positionOK.py', 'r', encoding='utf-8') as f:
    src = f.read()

lines = src.split('\n')

# Find _close_holding, load_from_kwargs, make_trade
targets = ['_close_holding', 'load_from_kwargs', 'make_trade']
for target in targets:
    for i, line in enumerate(lines):
        if f'def {target}' in line:
            # Print 40 lines from function start
            print(f"\n=== {target} (line {i+1}) ===")
            for j in range(i, min(i+50, len(lines))):
                print(f"{j+1}: {lines[j]}")
                if j > i and lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                    break
            break
