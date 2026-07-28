"""R30-6: Find the 2 extra instructions in change_his_to_forward src."""
import sys
import dis
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r30_decompiled.py'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    codes = {}
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(code_obj)
    return codes


def load_src_code_objects(src_path):
    with open(src_path) as f:
        src = f.read()
    codes = {}
    mod = compile(src, src_path, 'exec')
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(mod)
    return codes


def normalize_argval(argval):
    if isinstance(argval, types.CodeType):
        return (argval.co_name, argval.co_code)
    return argval


def get_instr_list_normalized(co):
    result = []
    for ins in dis.get_instructions(co):
        argval = normalize_argval(ins.argval)
        result.append((ins.opname, argval))
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    name = 'change_his_to_forward'
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instr_list_normalized(pc)
    si = get_instr_list_normalized(sc)
    print(f"=== {name}: pyc={len(pi)} src={len(si)} diff={len(si)-len(pi)} ===")
    # Use LCS-like alignment: find first insertion point
    # Walk both lists, when they diverge, check if it's an insertion in src
    i = j = 0
    while i < len(pi) and j < len(si):
        if pi[i] == si[j]:
            i += 1
            j += 1
        else:
            # Check if src has extra instructions (si[j] is extra)
            # Look ahead to see if pi[i] matches si[j+1] or si[j+2]
            matched = False
            for skip in range(1, 4):
                if j + skip < len(si) and pi[i] == si[j + skip]:
                    print(f"\n  INSERTION at pyc_idx={i} src_idx={j}: src has {skip} extra instr(s):")
                    for k in range(skip):
                        print(f"    src[{j+k}]: {si[j+k][0]:25s} {repr(si[j+k][1])[:60]}")
                    print(f"    pyc[{i}]: {pi[i][0]:25s} {repr(pi[i][1])[:60]} (matches src[{j+skip}])")
                    j += skip
                    matched = True
                    break
            if not matched:
                # Check if pyc has extra (deletion in src)
                for skip in range(1, 4):
                    if i + skip < len(pi) and pi[i + skip] == si[j]:
                        print(f"\n  DELETION at pyc_idx={i} src_idx={j}: pyc has {skip} extra instr(s):")
                        for k in range(skip):
                            print(f"    pyc[{i+k}]: {pi[i+k][0]:25s} {repr(pi[i+k][1])[:60]}")
                        print(f"    src[{j}]: {si[j][0]:25s} {repr(si[j][1])[:60]} (matches pyc[{i+skip}])")
                        i += skip
                        matched = True
                        break
            if not matched:
                print(f"\n  MISMATCH at pyc_idx={i} src_idx={j}:")
                print(f"    pyc[{i}]: {pi[i][0]:25s} {repr(pi[i][1])[:60]}")
                print(f"    src[{j}]: {si[j][0]:25s} {repr(si[j][1])[:60]}")
                i += 1
                j += 1
    # Tails
    while i < len(pi):
        print(f"\n  TAIL pyc[{i}]: {pi[i][0]:25s} {repr(pi[i][1])[:60]}")
        i += 1
    while j < len(si):
        print(f"\n  TAIL src[{j}]: {si[j][0]:25s} {repr(si[j][1])[:60]}")
        j += 1


if __name__ == '__main__':
    main()
