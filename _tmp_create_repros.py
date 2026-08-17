"""Create minimal reproduction cases for the _close_holding and make_trade bytecode mismatches.

Pattern 1 (_close_holding): if/while/else - while loop as last statement in if branch
  The decompiled bytecode generates LOAD_CONST None + RETURN_VALUE instead of JUMP_FORWARD
  after the while loop exits.

Pattern 2 (make_trade): if/else with return in then branch
  The decompiled bytecode generates LOAD_CONST None + RETURN_VALUE instead of JUMP_FORWARD
  after the last assignment in the then branch.
"""
import dis
import sys
import os
import py_compile
import tempfile

# Pattern 1: while loop as last statement in if branch
pattern1 = '''
def close_holding_repro(self, trade):
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

# Pattern 2: multiple statements + return in if branch
pattern2 = '''
def make_trade_repro(self, trade):
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

# Pattern 3: Simple if/else with while in then branch
pattern3 = '''
def simple_while_else(x, data):
    if x > 0:
        while x > 0 and data:
            item = data.pop()
            x -= item
    else:
        if data:
            old = data.pop()
            return old
    return x
'''

# Pattern 4: Simple if/else with return in then branch  
pattern4 = '''
def simple_if_return(x):
    if x > 0:
        if x == 1:
            self_val = x
            return -1 * x
        else:
            old = x
            return old - x
    return 0
'''

patterns = [
    ("repro_01_while_in_if_branch.py", pattern1, "close_holding"),
    ("repro_02_return_in_if_branch.py", pattern2, "make_trade"),
    ("repro_03_simple_while_else.py", pattern3, "simple_while_else"),
    ("repro_04_simple_if_return.py", pattern4, "simple_if_return"),
]

output_dir = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_67/test_engineer/minimal_repros"

for filename, source, func_name in patterns:
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(source)
    
    # Compile and get bytecode
    code = compile(source, filepath, 'exec')
    
    # Find the function
    for const in code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == func_name:
            print(f"\n{'='*60}")
            print(f"Pattern: {filename} ({func_name})")
            print(f"Instructions: {len(list(dis.get_instructions(const)))}")
            
            # Show first 20 instructions
            instrs = list(dis.get_instructions(const))
            for i, instr in enumerate(instrs[:30]):
                print(f"  {i:3d}  {instr.offset:4d}  {instr.opname:<30} {instr.argrepr}")
            break

print("\n\nRepro files created in:", output_dir)
