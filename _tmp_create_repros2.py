"""Create minimal repro pyc files and test decompiler."""
import dis
import marshal
import types
import sys
import os
import py_compile
import tempfile

# Create test pyc files
output_dir = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_67/test_engineer/minimal_repros"

# Pattern 1: if/while/else - while loop as last stmt in if branch (like _close_holding)
repro_files = []

# repro_05: if/while/else pattern (like _close_holding)
repro5 = '''
def close_holding(self, trade):
    left_amount = trade
    delta = 0
    if trade > 0:
        if trade == 1:
            left_amount = trade
            while left_amount > 0 and self.data:
                item = self.data.pop()
                if item > left_amount:
                    consumed = left_amount
                else:
                    consumed = item
                left_amount -= consumed
                delta += item
        else:
            if self.old_data:
                old = self.old_data.pop()
                if old > left_amount:
                    return old
                else:
                    left_amount -= old
                    delta += old
                    while left_amount > 0 and self.data:
                        item = self.data.pop()
                        left_amount -= item
                    return delta
    return delta
'''

# repro_06: if/else with return in then branch (like make_trade)
repro6 = '''
def make_trade(self, trade):
    amount = trade
    if trade > 0:
        if trade == 1:
            if self.count == 0:
                self.time = trade
            self.type = 1
            self.price = (self.price * self.count + amount * trade) / (self.count + amount)
            self.cost += trade
            self.list.insert(0, (trade, amount))
            return -1 * self.calc(amount, trade)
        else:
            if self.count - amount != 0:
                self.price = (self.price * self.count - amount * trade) / (self.count - amount)
            else:
                self.time = trade
                self.price = 0.0
            old = self.margin
            self.cost += trade
            delta = self.close(trade)
            self.pnl += delta
            return old - self.margin + delta
    return 0
'''

# repro_07: Simple nested if/else with while in then
repro7 = '''
def test_while_in_if(x, data):
    if x > 0:
        if x == 1:
            while x > 0 and data:
                item = data.pop()
                x -= item
        else:
            if data:
                old = data.pop()
                return old
    return x
'''

# repro_08: Simple if/else with multiple statements + return
repro8 = '''
def test_multi_stmt_return(x):
    if x > 0:
        if x == 1:
            y = x
            z = x * 2
            return -1 * x
        else:
            old = x
            y = x - 1
            return old - y
    return 0
'''

# repro_09: if/elif/else with while in one branch
repro9 = '''
def test_elif_while(x, data):
    if x == 1:
        while x > 0 and data:
            item = data.pop()
            x -= item
    elif x == 2:
        if data:
            return data.pop()
    return x
'''

# repro_10: if/elif/else with return in branches  
repro10 = '''
def test_elif_return(x):
    if x == 1:
        y = x
        return -1 * x
    elif x == 2:
        old = x
        return old - x
    return 0
'''

patterns = [
    ("repro_05_close_holding_pattern.py", repro5, "close_holding"),
    ("repro_06_make_trade_pattern.py", repro6, "make_trade"),
    ("repro_07_while_in_if.py", repro7, "test_while_in_if"),
    ("repro_08_multi_stmt_return.py", repro8, "test_multi_stmt_return"),
    ("repro_09_elif_while.py", repro9, "test_elif_while"),
    ("repro_10_elif_return.py", repro10, "test_elif_return"),
]

for filename, source, func_name in patterns:
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(source)
    
    # Compile to pyc
    pyc_path = filepath.replace('.py', '.pyc')
    py_compile.compile(filepath, pyc_path, doraise=True)
    
    # Load and check bytecode
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        f.read(8)  # timestamp + size (or source hash)
        code = marshal.load(f)
    
    for const in code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == func_name:
            instrs = list(dis.get_instructions(const))
            print(f"\n{'='*60}")
            print(f"Repro: {filename} ({func_name}) - {len(instrs)} instructions")
            # Show key instructions around while/if patterns
            for i, instr in enumerate(instrs):
                if instr.opname in ('JUMP_FORWARD', 'RETURN_VALUE', 'POP_JUMP_BACKWARD_IF_TRUE', 
                                     'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE'):
                    print(f"  [{i:3d}] {instr.offset:4d}  {instr.opname:<30} {instr.argrepr}")
            break

print("\n\nAll repro files created.")
print(f"Directory: {output_dir}")
