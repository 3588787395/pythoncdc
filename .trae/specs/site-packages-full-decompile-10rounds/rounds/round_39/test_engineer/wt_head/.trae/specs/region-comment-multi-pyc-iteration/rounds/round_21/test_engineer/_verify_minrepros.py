"""R21: Batch decompile and verify minimal repro .pyc files."""
import os, sys, types, marshal, dis, tempfile, shutil

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

REPRO_DIR = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros'
PYC_DIR = os.path.join(REPRO_DIR, '__pycache__')


def load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract_code_objects(code_obj):
    result = [code_obj]
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType):
            result.extend(extract_code_objects(c))
    return result


def normalize_instructions(code_obj):
    """Get normalized instruction list for comparison."""
    instrs = []
    for i in dis.get_instructions(code_obj):
        if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
            continue
        instrs.append((i.opname, i.argval))
    return instrs


def decompile_pyc(pyc_path):
    """Decompile a pyc file and return source code."""
    from pycdc import decompile
    code = load_pyc_code(pyc_path)
    try:
        src = decompile(pyc_path)
        return src
    except Exception as e:
        return None


def compare_bytecode(orig_code, dec_src, func_name=None):
    """Compile dec_src and compare bytecode with orig_code."""
    try:
        compiled = compile(dec_src, '<decompiled>', 'exec')
        dec_codes = extract_code_objects(compiled)
        orig_codes = extract_code_objects(orig_code)
        
        # Find matching code objects by name
        mismatches = []
        total = 0
        matched = 0
        
        for oc in orig_codes:
            if func_name and oc.co_name != func_name:
                continue
            # Find matching dec code
            dc_candidates = [dc for dc in dec_codes if dc.co_name == oc.co_name]
            if not dc_candidates:
                mismatches.append((oc.co_name, 'no_match_in_dec'))
                total += 1
                continue
            
            for dc in dc_candidates:
                total += 1
                orig_instrs = normalize_instructions(oc)
                dec_instrs = normalize_instructions(dc)
                if orig_instrs == dec_instrs:
                    matched += 1
                else:
                    mismatches.append((oc.co_name, f'orig={len(orig_instrs)} dec={len(dec_instrs)}'))
        
        return matched, total, mismatches
    except Exception as e:
        return 0, 1, [(func_name or 'root', str(e))]


def main():
    pycs = sorted(f for f in os.listdir(PYC_DIR) if f.endswith('.pyc'))
    print(f'Found {len(pycs)} .pyc files')
    
    ok_list = []
    fail_list = []
    
    for pyc_name in pycs:
        pyc_path = os.path.join(PYC_DIR, pyc_name)
        orig_code = load_pyc_code(pyc_path)
        
        # Decompile
        from pycdc import decompile_pyc
        try:
            dec_src = decompile_pyc(pyc_path)
        except Exception as e:
            fail_list.append((pyc_name, 0, 1, [f'decompile_error: {e}']))
            print(f'  [!] {pyc_name}: DECOMPILE ERROR: {e}')
            continue
        
        # Compare bytecode
        matched, total, mismatches = compare_bytecode(orig_code, dec_src)
        rate = matched / total if total > 0 else 0
        
        if rate == 1.0:
            ok_list.append(pyc_name)
            print(f'  [V] {pyc_name}: {matched}/{total} (100%)')
        else:
            fail_list.append((pyc_name, matched, total, mismatches))
            print(f'  [X] {pyc_name}: {matched}/{total} ({rate:.1%})')
            for fn, detail in mismatches:
                print(f'      {fn}: {detail}')
            # Show decompiled source for failing cases
            if len(dec_src) < 500:
                print(f'      dec_src:')
                for line in dec_src.split('\n')[:20]:
                    print(f'        {line}')
    
    print(f'\n=== Summary ===')
    print(f'  OK: {len(ok_list)}, FAIL: {len(fail_list)}')
    if fail_list:
        print(f'  Failing:')
        for name, m, t, mm in fail_list:
            print(f'    {name}: {m}/{t}')


if __name__ == '__main__':
    main()
