"""R23-N8 测试工程师：分类失败函数的差异类型"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


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
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def categorize():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    with open('/tmp/r23_failures.txt', 'r', encoding='utf-8') as f:
        failures = [line.strip() for line in f if line.strip()]

    print(f"=== 失败函数差异分类 (共 {len(failures)} 个) ===\n")
    categories = {}
    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            print(f"{name}: 缺失")
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        if len(pi) != len(si):
            cat = f"len_diff (pyc={len(pi)}, src={len(si)}, delta={len(si)-len(pi)})"
        else:
            diffs = []
            for idx, (a, b) in enumerate(zip(pi, si)):
                if a[1] != b[1]:
                    diffs.append(f"op@{a[0]}:{a[1]}->{b[1]}")
                elif a[2] != b[2]:
                    av_a = a[2]
                    av_b = b[2]
                    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
                        diffs.append(f"codearg@{a[0]}")
                    else:
                        sa = repr(av_a)[:50]
                        sb = repr(av_b)[:50]
                        diffs.append(f"argval@{a[0]}:{sa}->{sb}")
            if not diffs:
                cat = "sig_diff_only"
            else:
                cat = f"content_diff ({len(diffs)} diffs): " + "; ".join(diffs[:3])
        categories.setdefault(cat, []).append(name)
        print(f"  {name}: {cat}")
    print(f"\n=== 分类汇总 ===")
    for cat, names in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  [{len(names)}] {cat}")
        for n in names[:5]:
            print(f"      - {n}")


if __name__ == '__main__':
    categorize()
