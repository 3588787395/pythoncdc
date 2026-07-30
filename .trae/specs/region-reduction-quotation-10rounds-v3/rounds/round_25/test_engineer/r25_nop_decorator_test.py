"""R25: verify @decorator + multi-line sig + blank lines also produces NOPs that vanish after decompile."""
import sys, dis, os, subprocess, marshal
sys.path.insert(0, '/workspace')

SRC = """def check_arg(f):
    return f


@check_arg
def get_price(get_type, prod_code, candle_period, candle_mode=None,
              search_direction=None, date=None, min_time=None,
              data_count=None, start_date=None, end_date=None):
    return prod_code


@check_arg
def get_history(get_type, prod_code, candle_period, candle_mode=None,
                date=None):
    return prod_code
"""

WORK = '/tmp/r25_nop_test2'
os.makedirs(WORK, exist_ok=True)
src_path = os.path.join(WORK, 'dec_test.py')
with open(src_path, 'w') as f:
    f.write(SRC)
pyc_path = os.path.join(WORK, 'dec_test.pyc')
import py_compile
py_compile.compile(src_path, pyc_path, doraise=True)

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def count_nops(co):
    return sum(1 for ins in dis.get_instructions(co) if ins.opname != 'CACHE' and ins.opname == 'NOP')

print(f"=== ORIGINAL (@check_arg + multi-line sig + blanks): NOP count = {count_nops(code)} ===")
for ins in dis.get_instructions(code):
    if ins.opname == 'CACHE':
        continue
    if ins.opname in ('NOP', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST'):
        sl = ins.starts_line if ins.starts_line else ''
        print(f"  {ins.offset:>4} L{str(sl):>4}  {ins.opname:<14} {str(ins.argrepr)[:60]}")

# decompile
out_path = os.path.join(WORK, 'dec_test_decompiled.py')
r = subprocess.run([sys.executable, '/workspace/pycdc.py', pyc_path],
                   capture_output=True, text=True, timeout=60, cwd='/workspace')
with open(out_path, 'w') as f:
    f.write(r.stdout)
with open(out_path) as f:
    decomp_src = f.read()
new_code = compile(decomp_src, '<d>', 'exec')
print(f"\n=== RECOMPILED from decompiled: NOP count = {count_nops(new_code)} ===")
print(f"--- Decompiled source ---")
print(decomp_src)
