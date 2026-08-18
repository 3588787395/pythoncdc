#!/usr/bin/env python3
"""Test minimal repros: compile -> decompile -> compare bytecodes."""
import sys, os, dis, types, tempfile, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_all_code_objects(code, prefix=''):
    result = {}
    result[prefix or '<module>'] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(get_all_code_objects(const, name))
    return result

def filter_noise(instrs):
    NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'}
    return [i for i in instrs if i.opname not in NOISE]

def normalize_argval(argval):
    if isinstance(argval, types.CodeType):
        return f"<code object {argval.co_name}>"
    if isinstance(argval, str):
        low = argval.lower()
        if (low.endswith('.py') or low.endswith('.pyc')) and ('/' in argval or '\\' in argval):
            return os.path.basename(argval)
    if isinstance(argval, frozenset):
        return frozenset(argval)
    return argval

def compare_code_objects(orig, new):
    """Compare two code objects' bytecodes."""
    orig_instrs = filter_noise(list(dis.get_instructions(orig)))
    new_instrs = filter_noise(list(dis.get_instructions(new)))
    if len(orig_instrs) != len(new_instrs):
        return False, f"len mismatch: {len(orig_instrs)} vs {len(new_instrs)}"
    diffs = []
    for i, (o, n) in enumerate(zip(orig_instrs, new_instrs)):
        if o.opname != n.opname:
            diffs.append(f"  [{i}] {o.opname}({o.argrepr}) vs {n.opname}({n.argrepr})")
        elif normalize_argval(o.argval) != normalize_argval(n.argval):
            if o.opname not in ('JUMP_FORWARD','JUMP_BACKWARD','JUMP_ABSOLUTE',
                                'POP_JUMP_FORWARD_IF_TRUE','POP_JUMP_FORWARD_IF_FALSE',
                                'POP_JUMP_BACKWARD_IF_TRUE','POP_JUMP_BACKWARD_IF_FALSE',
                                'POP_JUMP_IF_TRUE','POP_JUMP_IF_FALSE',
                                'POP_JUMP_FORWARD_IF_NONE','POP_JUMP_FORWARD_IF_NOT_NONE',
                                'POP_JUMP_BACKWARD_IF_NONE','POP_JUMP_BACKWARD_IF_NOT_NONE',
                                'POP_JUMP_IF_NONE','POP_JUMP_IF_NOT_NONE',
                                'JUMP_IF_TRUE_OR_POP','JUMP_IF_FALSE_OR_POP',
                                'FOR_ITER','SEND'):
                diffs.append(f"  [{i}] argval {o.argrepr} vs {n.argrepr} ({o.opname})")
    if diffs:
        return False, '\n'.join(diffs[:10])
    return True, "OK"

def test_repro(py_path):
    """Test a single repro file."""
    print(f"\n=== Testing: {os.path.basename(py_path)} ===")
    with open(py_path, 'r') as f:
        source = f.read()
    
    # Compile original
    try:
        orig_code = compile(source, py_path, 'exec')
    except SyntaxError as e:
        print(f"  SKIP (syntax error): {e}")
        return True  # Not a decompiler issue
    
    orig_funcs = get_all_code_objects(orig_code)
    
    # Decompile
    from pycdc import decompile_pyc
    # Save to temp .pyc and decompile
    import marshal
    fd, tmp_pyc = tempfile.mkstemp(suffix='.pyc')
    with os.fdopen(fd, 'wb') as f:
        f.write(b'\x6f\x0d\x0d\x0a')  # magic
        f.write(b'\x00' * 12)  # flags + timestamp + size
        marshal.dump(orig_code, f)
    
    try:
        decompiled_source = decompile_pyc(tmp_pyc)
    except Exception as e:
        traceback.print_exc()
        print(f"  FAIL (decompile error): {e}")
        return False
    finally:
        os.unlink(tmp_pyc)
    
    # Clean header
    lines = decompiled_source.split('\n')
    clean_lines = [l for l in lines if not l.startswith('# Source') and not l.startswith('# File:')]
    decompiled_source = '\n'.join(clean_lines).strip()
    
    # Compile decompiled
    try:
        new_code = compile(decompiled_source, '<decompiled>', 'exec')
    except SyntaxError as e:
        print(f"  FAIL (syntax error in decompiled): {e}")
        print(f"  Decompiled:\n{decompiled_source[:500]}")
        return False
    
    new_funcs = get_all_code_objects(new_code)
    
    # Compare
    all_ok = True
    for name, orig_func in orig_funcs.items():
        if name not in new_funcs:
            print(f"  FAIL: {name} missing in decompiled")
            all_ok = False
            continue
        ok, msg = compare_code_objects(orig_func, new_funcs[name])
        if ok:
            print(f"  OK: {name}")
        else:
            print(f"  FAIL: {name}")
            print(f"    {msg}")
            all_ok = False
    
    return all_ok

if __name__ == '__main__':
    repro_dir = sys.argv[1] if len(sys.argv) > 1 else '.trae/specs/site-packages-full-decompile-10rounds/rounds/round_01/test_engineer/minimal_repros'
    results = []
    for fname in sorted(os.listdir(repro_dir)):
        if fname.endswith('.py'):
            ok = test_repro(os.path.join(repro_dir, fname))
            results.append((fname, ok))
    print(f"\n=== Summary ===")
    passed = sum(1 for _, ok in results if ok)
    print(f"Passed: {passed}/{len(results)}")
