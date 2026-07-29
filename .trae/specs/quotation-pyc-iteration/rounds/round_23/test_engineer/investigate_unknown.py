"""R23-N4: 调查 unknown 类失败原因"""
import sys
import dis
import types
import inspect

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def get_instr_list(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval))
    return out


UNKNOWN = ['build_current_period_df', 'datetimeindex_astype', 'getLogger', 'getLogger.Void',
           'get_date_index', 'get_fundamentals_daily_info', 'get_market_list',
           'get_valuation_info', 'get_valuation_new_info']


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in UNKNOWN:
        if name not in pyc_codes or name not in src_codes:
            print(f"\n=== {name}: MISSING ===")
            continue
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        print(f"\n=== {name} ===")
        print(f"pyc: len={len(pi)}, argcount={pc.co_argcount}, kwargcount={pc.co_kwonlyargcount}, "
              f"varargs={pc.co_flags & inspect.CO_VARARGS != 0}, varkw={pc.co_flags & inspect.CO_VARKEYWORDS != 0}")
        print(f"  args={pc.co_varnames[:pc.co_argcount+pc.co_kwonlyargcount]}")
        print(f"src: len={len(si)}, argcount={sc.co_argcount}, kwargcount={sc.co_kwonlyargcount}, "
              f"varargs={sc.co_flags & inspect.CO_VARARGS != 0}, varkw={sc.co_flags & inspect.CO_VARKEYWORDS != 0}")
        print(f"  args={sc.co_varnames[:sc.co_argcount+sc.co_kwonlyargcount]}")
        if pi == si:
            print("  INSTR MATCH - signature diff!")
        else:
            print(f"  INSTR DIFF (pyc={len(pi)} vs src={len(si)})")
            # 找首个差异
            for i, (a, b) in enumerate(zip(pi, si)):
                if a[1] != b[1] or (not (isinstance(a[2], types.CodeType) and isinstance(b[2], types.CodeType)) and a[2] != b[2]):
                    print(f"  first diff @{a[0]}: pyc={a[1]}({a[2]!r}) src={b[1]}({b[2]!r})")
                    break


if __name__ == '__main__':
    main()
