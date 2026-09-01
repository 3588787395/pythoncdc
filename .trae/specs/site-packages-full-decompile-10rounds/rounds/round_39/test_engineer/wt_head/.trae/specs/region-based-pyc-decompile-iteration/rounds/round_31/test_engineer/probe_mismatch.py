"""Probe round_31: 深入比对 future_position.pyc 中 make_trade 的 orig vs recomp 字节码。

用法: D:/Python/python.exe probe_mismatch.py
"""
import difflib
import marshal
import py_compile
import sys
import types

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

PYC = ROOT + r'\site-packages\IQEngine\plugins\plugin_system_accounts\position_model\future_position.pyc'
OK_PY = PYC[:-4] + 'OK.py'
TARGET = 'make_trade'


def load_code(path, skip=16):
    with open(path, 'rb') as f:
        f.read(skip)
        return marshal.load(f)


def extract(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract(const))
    return result


def instr_lines(code):
    lines = []
    for ins in code.co_instructions() if hasattr(code, 'co_instructions') else __import__('dis').get_instructions(code):
        lines.append('%4d %-26s %s %s' % (ins.offset, ins.opname, ins.arg if ins.arg is not None else '', repr(ins.argrepr)))
    return lines


def main():
    orig_map = extract(load_code(PYC))
    cfile = py_compile.compile(OK_PY, doraise=True, quiet=2)
    decomp_map = extract(load_code(cfile))

    o, d = orig_map[TARGET], decomp_map[TARGET]
    print('== const diff ==')
    oc = [repr(c) for c in o.co_consts]
    dc = [repr(c) for c in d.co_consts]
    for line in difflib.unified_diff(oc, dc, 'orig_consts', 'recomp_consts', lineterm='', n=1):
        print(line)
    print()
    print('== names diff ==')
    for line in difflib.unified_diff(list(o.co_names), list(d.co_names), 'orig_names', 'recomp_names', lineterm='', n=1):
        print(line)
    print()
    ol, dl = instr_lines(o), instr_lines(d)
    print('== instr diff (orig=%d, recomp=%d) ==' % (len(ol), len(dl)))
    for line in difflib.unified_diff(ol, dl, 'orig', 'recomp', lineterm='', n=3):
        print(line)


if __name__ == '__main__':
    main()
