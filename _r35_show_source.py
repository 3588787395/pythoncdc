"""Show decompiled source for specific functions in trade_live_broker.pyc"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testqouter.round1.base import decompile_pyc

pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
source = decompile_pyc(pyc_path)

lines = source.split('\n')

# Find functions by searching for 'def ' at any indentation
targets = ['get_open_orders', 'get_orders', 'submit_order', 'cancel_order', 'order_tick', '_process_order', 'get_portfolio', '_sync_worker']

for target in targets:
    for i, line in enumerate(lines):
        if f'def {target}(' in line:
            # Find the indentation level
            indent = len(line) - len(line.lstrip())
            # Print this function and its body
            func_lines = [line]
            for j in range(i+1, min(i+50, len(lines))):
                next_line = lines[j]
                # Stop when we find a line at same or lower indentation (not empty)
                if next_line.strip() and not next_line[0].isspace():
                    break
                if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= indent and not next_line.strip().startswith('#'):
                    break
                func_lines.append(next_line)
            
            print(f"\n{'='*60}")
            print(f"=== {target} (line {i+1}) ===")
            for fl in func_lines[:35]:
                print(fl)
            if len(func_lines) > 35:
                print(f"... ({len(func_lines)} total lines)")
            break
