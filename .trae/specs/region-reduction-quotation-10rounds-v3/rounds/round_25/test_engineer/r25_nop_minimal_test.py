"""R25: minimal test - verify <module> NOPs are line-layout artifacts (multi-line sig + blanks).

Pattern from quotation.pyc: between STORE_NAME prev_func and LOAD_CONST next_func defaults,
CPython emits NOPs carrying line numbers of the next function's multi-line signature /
blank lines. Test whether decompile->recompile preserves them.
"""
import sys, dis, os, subprocess, tempfile
sys.path.insert(0, '/workspace')

# Mimic the orig pattern: long multi-line signature + blank lines between funcs.
# get_kline in orig has def at L419, NOPs at L422-428 (multi-line sig + blanks).
SRC = """def api_get_financial(url, params=None, request_times=0):
    token_value = get_token()
    return token_value


def get_kline(get_type, prod_code, candle_period, candle_mode=None,
              search_direction=None, date=None, min_time=None,
              data_count=None, start_date=None, end_date=None):
    prod_code = prod_code.replace('.XSHE', '.SZ')
    return prod_code


def get_holiday_online():
    return None
"""

WORK = '/tmp/r25_nop_test'
os.makedirs(WORK, exist_ok=True)
src_path = os.path.join(WORK, 'mod_test.py')
with open(src_path, 'w') as f:
    f.write(SRC)

# compile to pyc
pyc_path = os.path.join(WORK, 'mod_test.pyc')
import py_compile
py_compile.compile(src_path, pyc_path, doraise=True)


def count_nops(co):
    n = 0
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        if ins.opname == 'NOP':
            n += 1
    return n


def show_nops(co, label):
    print(f"\n=== {label}: NOP count = {count_nops(co)} ===")
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        if ins.opname == 'NOP':
            print(f"  NOP @ {ins.offset} starts_line={ins.starts_line}")


# Load orig compiled module code object
import importlib.util
spec = importlib.util.spec_from_file_location('mod_test', pyc_path)
mod = importlib.util.module_from_spec(spec)
# don't exec; just read the code object from the pyc
import marshal
with open(pyc_path, 'rb') as f:
    magic = f.read(16)
    code = marshal.load(f)
show_nops(code, 'ORIGINAL (multi-line sig + blanks)')

# Decompile with pycdc
out_path = os.path.join(WORK, 'mod_test_decompiled.py')
r = subprocess.run([sys.executable, '/workspace/pycdc.py', pyc_path],
                   capture_output=True, text=True, timeout=60, cwd='/workspace')
with open(out_path, 'w') as f:
    f.write(r.stdout)
print(f"\n--- Decompiled source ---")
print(r.stdout)
print(f"--- End decompiled (stderr: {r.stderr[:200]}) ---")

# Recompile the decompiled source
with open(out_path) as f:
    decomp_src = f.read()
new_code = compile(decomp_src, '<d>', 'exec')
show_nops(new_code, 'RECOMPILED from decompiled (single-line sig, no blanks)')
