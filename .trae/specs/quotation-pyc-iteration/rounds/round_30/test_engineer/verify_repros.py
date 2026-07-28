"""R30 验证最小复现：检查反编译+重编译后字节码是否一致"""
import sys
import dis
import types
import importlib.util

sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_30/test_engineer/minimal_repros')

from pycdc import decompile_pyc

# Import the repro module
spec = importlib.util.spec_from_file_location(
    "repro_01",
    "/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_30/test_engineer/minimal_repros/repro_01_elif_merge_block_skips_next_if.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Get all functions from the module
func_names = [name for name in dir(mod) if name.startswith('repro_') and callable(getattr(mod, name))]

def get_instr_list(co):
    result = []
    for ins in dis.get_instructions(co):
        argval = ins.argval
        if isinstance(argval, types.CodeType):
            argval = (argval.co_name, argval.co_code)
        result.append((ins.opname, argval))
    return result

passed = 0
failed = 0
for fname in func_names:
    func = getattr(mod, fname)
    original_code = func.__code__

    # Compile the function's source to get bytecode
    import inspect
    src = inspect.getsource(func)
    # Dedent
    lines = src.split('\n')
    min_indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    src = '\n'.join(l[min_indent:] for l in lines)

    # Recompile
    ns = {}
    exec(compile(src, '<test>', 'exec'), ns)
    recompiled_code = ns[fname].__code__

    # Now decompile the original and recompile
    # We need to create a .pyc from the original code
    import marshal
    import struct
    import time

    # Create a code object for a module containing the function
    # Actually, let's just use decompile_pyc with the function's code

    # Create a temporary pyc file
    import tempfile
    import os

    # Build a module code object
    mod_code = compile(src, '<repro>', 'exec')

    # Write pyc
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False, mode='wb') as f:
        # Python 3.11 pyc header: magic (4) + flags (4) + timestamp (4) + size (4) = 16 bytes
        magic = b'\xa7\r\r\n'  # Python 3.11 magic
        flags = 0
        timestamp = int(time.time())
        size = len(src.encode())
        f.write(magic + struct.pack('<III', flags, timestamp, size))
        f.write(marshal.dumps(mod_code))
        pyc_path = f.name

    try:
        decompiled_src = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
        # Extract the function from decompiled source
        decompiled_ns = {}
        exec(compile(decompiled_src, '<decompiled>', 'exec'), decompiled_ns)

        if fname not in decompiled_ns:
            print(f"FAIL {fname}: function not found in decompiled source")
            failed += 1
            continue

        decompiled_code = decompiled_ns[fname].__code__

        orig_instrs = get_instr_list(original_code)
        decomp_instrs = get_instr_list(decompiled_code)

        if orig_instrs == decomp_instrs:
            print(f"PASS {fname}: {len(orig_instrs)} instructions match")
            passed += 1
        else:
            print(f"FAIL {fname}: orig={len(orig_instrs)} decomp={len(decomp_instrs)}")
            # Show first diff
            min_len = min(len(orig_instrs), len(decomp_instrs))
            for i in range(min_len):
                if orig_instrs[i] != decomp_instrs[i]:
                    print(f"  First diff at idx {i}:")
                    print(f"    orig:  {orig_instrs[i][0]:30s} {repr(orig_instrs[i][1])[:60]}")
                    print(f"    decomp: {decomp_instrs[i][0]:30s} {repr(decomp_instrs[i][1])[:60]}")
                    break
            else:
                if len(orig_instrs) > min_len:
                    print(f"  Extra in orig: {orig_instrs[min_len:]}")
                elif len(decomp_instrs) > min_len:
                    print(f"  Extra in decomp: {decomp_instrs[min_len:]}")
            failed += 1
    except Exception as e:
        print(f"ERROR {fname}: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    finally:
        os.unlink(pyc_path)

print(f"\n=== Results: {passed} passed, {failed} failed ===")
