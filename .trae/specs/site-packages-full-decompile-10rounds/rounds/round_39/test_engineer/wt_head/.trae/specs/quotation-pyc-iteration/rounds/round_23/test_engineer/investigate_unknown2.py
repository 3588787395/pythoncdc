"""R23-N4: 深入查看 unknown 失败的具体差异"""
import sys
import dis
import types

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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in ['build_current_period_df', 'getLogger', 'get_market_list']:
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = list(dis.get_instructions(pc))
        si = list(dis.get_instructions(sc))
        pi = [i for i in pi if i.opname not in ('EXTENDED_ARG', 'CACHE')]
        si = [i for i in si if i.opname not in ('EXTENDED_ARG', 'CACHE')]

        print(f"\n=== {name} ===")
        for i, (a, b) in enumerate(zip(pi, si)):
            if a.opname != b.opname:
                print(f"  [{i}] OPDIFF @{a.offset}: pyc={a.opname}({a.argval!r}) vs src={b.opname}({b.argval!r})@{b.offset}")
                continue
            av_a, av_b = a.argval, b.argval
            if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
                if av_a.co_name != av_b.co_name:
                    print(f"  [{i}] CODENAME @{a.offset}: pyc={av_a.co_name!r} vs src={av_b.co_name!r}")
                # deep diff
                elif av_a.co_code != av_b.co_code:
                    print(f"  [{i}] CODE_BYTE_DIFF @{a.offset}: pyc_co_name={av_a.co_name!r} (len {len(av_a.co_code)}) vs src (len {len(av_b.co_code)})")
                continue
            if av_a != av_b:
                print(f"  [{i}] ARGVALDIFF @{a.offset} op={a.opname}: pyc={av_a!r} vs src={av_b!r}")


if __name__ == '__main__':
    main()
