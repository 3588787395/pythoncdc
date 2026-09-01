"""R23-N3: 显示小差异失败函数的字节码差异"""
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


def show(co, label):
    print(f"\n--- {label} ---")
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d}  {ins.opname:30s} {ins.argrepr}")


def diff_pair(pc, sc):
    """显示首个差异位置（处理长度不同）"""
    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))
    pi = [i for i in pi if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    si = [i for i in si if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    i = j = 0
    while i < len(pi) and j < len(si):
        if pi[i].opname != si[j].opname:
            print(f"  DIFF @{pi[i].offset} (src@{si[j].offset}): pyc={pi[i].opname}({pi[i].argrepr!r}) vs src={si[j].opname}({si[j].argrepr!r})")
            # 显示上下文
            print(f"    PYC context:")
            for k in range(max(0,i-2), min(len(pi), i+3)):
                mark = ">>>" if k == i else "   "
                print(f"      {mark} {pi[k].offset:4d}  {pi[k].opname:30s} {pi[k].argrepr}")
            print(f"    SRC context:")
            for k in range(max(0,j-2), min(len(si), j+3)):
                mark = ">>>" if k == j else "   "
                print(f"      {mark} {si[k].offset:4d}  {si[k].opname:30s} {si[k].argrepr}")
            return
        if pi[i].argval != si[j].argval:
            if not (isinstance(pi[i].argval, types.CodeType) and isinstance(si[j].argval, types.CodeType)):
                print(f"  ARGVAL DIFF @{pi[i].offset}: pyc={pi[i].opname}({pi[i].argval!r}) vs src={pi[i].opname}({si[j].argval!r})")
                print(f"    PYC context:")
                for k in range(max(0,i-2), min(len(pi), i+3)):
                    mark = ">>>" if k == i else "   "
                    print(f"      {mark} {pi[k].offset:4d}  {pi[k].opname:30s} {pi[k].argrepr}")
                print(f"    SRC context:")
                for k in range(max(0,j-2), min(len(si), j+3)):
                    mark = ">>>" if k == j else "   "
                    print(f"      {mark} {si[k].offset:4d}  {si[k].opname:30s} {si[k].argrepr}")
                return
        i += 1
        j += 1
    if i < len(pi):
        print(f"  PYC has extra from @{pi[i].offset}: {pi[i].opname}({pi[i].argrepr!r})")
        for k in range(i, min(len(pi), i+5)):
            print(f"    {pi[k].offset:4d}  {pi[k].opname:30s} {pi[k].argrepr}")
    if j < len(si):
        print(f"  SRC has extra from @{si[j].offset}: {si[j].opname}({si[j].argrepr!r})")
        for k in range(j, min(len(si), j+5)):
            print(f"    {si[k].offset:4d}  {si[k].opname:30s} {si[k].argrepr}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    # 分析几个小差异的函数
    targets = ['get_holiday_online', 'get_index_stocks', 'multi_prod_to_dataframe', 'date_convert', 'get_fields']
    for name in targets:
        if name not in pyc_codes or name not in src_codes:
            print(f"\n{'='*60}\n{name}: MISSING")
            continue
        print(f"\n{'='*60}\n{name}")
        diff_pair(pyc_codes[name], src_codes[name])

        # 显示源码
        import re
        with open(SRC, 'r', encoding='utf-8') as f:
            src = f.read()
        m = re.search(rf'def {name}\([^)]*\)[^\n]*:\n(?:.|\n)*?(?=\ndef [a-z]|\nclass |\Z)', src)
        if m:
            print(f"\n  SRC CODE:")
            for line in m.group(0).split('\n')[:30]:
                print(f"    {line}")


if __name__ == '__main__':
    main()
