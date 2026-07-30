"""Verify which source structure produces 'typet branch JUMP_FORWARD past for-loop'."""
import dis

# Structure A: if/elif/else with for-loop at top level (decompiler's WRONG output)
SRC_A = '''
def f(typet, suffix):
    trade_days = [1, 2, 3]
    total_dts = []
    market_time = []
    if not typet == 5:
        if typet == 1:
            for today in trade_days:
                total_dts.append(today)
        elif typet == 4:
            for today in trade_days:
                for item in market_time:
                    total_dts.append(today + item)
    elif suffix == 'A':
        market_time = [1]
    elif suffix in ('B', 'C'):
        market_time = [2]
    else:
        market_time = [3]
    for today in trade_days:
        for item in market_time:
            total_dts.append(today + item)
    if total_dts:
        total_dts.sort()
    return total_dts
'''

# Structure B: if/else with nested if + for-loop INSIDE else (hypothesized ORIGINAL)
SRC_B = '''
def f(typet, suffix):
    trade_days = [1, 2, 3]
    total_dts = []
    market_time = []
    if not typet == 5:
        if typet == 1:
            for today in trade_days:
                total_dts.append(today)
        elif typet == 4:
            for today in trade_days:
                for item in market_time:
                    total_dts.append(today + item)
    else:
        if suffix == 'A':
            market_time = [1]
        elif suffix in ('B', 'C'):
            market_time = [2]
        else:
            market_time = [3]
        for today in trade_days:
            for item in market_time:
                total_dts.append(today + item)
    if total_dts:
        total_dts.sort()
    return total_dts
'''


def show_jumps(co, label):
    print(f"\n=== {label} ===")
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        if ins.opname in ('JUMP_FORWARD', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE'):
            print(f"  {ins.offset:>4} {ins.opname:<32} {ins.argrepr}")
        elif ins.opname == 'FOR_ITER':
            print(f"  {ins.offset:>4} FOR_ITER {'':<24} {ins.argrepr}")
        elif ins.opname in ('LOAD_FAST',) and ins.argrepr in ('total_dts', 'trade_days'):
            print(f"  {ins.offset:>4} LOAD_FAST {'':<23} {ins.argrepr}  (line {ins.starts_line})")


co_a = compile(SRC_A, '<a>', 'exec').co_consts[0]
co_b = compile(SRC_B, '<b>', 'exec').co_consts[0]
show_jumps(co_a, 'STRUCTURE A: if/elif/else + top-level for-loop (decompiler output)')
show_jumps(co_b, 'STRUCTURE B: if/else + nested if + for-loop in else (hypothesized orig)')
