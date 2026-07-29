"""R10 测试工程师：递归比较 quotation.pyc 与反编译结果的字节码一致性。

精确匹配 = co_code + co_consts(递归) + 签名(argcount/nlocals/varnames/names/cellvars/freevars/flags/stacksize)
指令匹配   = co_code 一致（递归）
"""
import sys
import types
import importlib.util
import marshal
import struct

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r10_decompiled.py'


def load_pyc_code_objects(pyc_path):
    """从 .pyc 加载顶层 code object，递归收集所有 code object (name -> code)。"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        # Python 3.7+: 16-byte header (magic + flags + mtime/size + size)
        # Python 3.8-3.10: 16-byte header
        # Python 3.11+: 16-byte header
        f.read(12)  # skip rest of header
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    # 顶层 module 用 '<module>' 表示；子函数用 '<module>.func' / '<module>.func.nested'
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            child_prefix = name
            _collect(c, result, child_prefix)


def load_src_code_objects(src_path):
    """编译反编译后的源码，递归收集所有 code object。"""
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        code = compile(src, src_path, 'exec')
    except SyntaxError as e:
        print(f"[load_src] SyntaxError: {e}")
        return None
    result = {}
    _collect(code, result, prefix='')
    return result


def code_normalize(code):
    """递归规范化 code object：返回可比较的元组。

    排除 co_filename / co_firstlineno / 内存地址等环境相关属性。
    co_consts 中的嵌套 code object 递归规范化。
    """
    norm_consts = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            norm_consts.append(code_normalize(c))
        else:
            norm_consts.append(c)
    return (
        code.co_code,  # raw bytecode bytes
        tuple(norm_consts),
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        tuple(code.co_cellvars),
        tuple(code.co_freevars),
        tuple(code.co_varnames),
        tuple(code.co_names),
        code.co_stacksize,
        code.co_flags,
    )


def code_normalize_instr_only(code):
    """仅比较 co_code（递归），忽略签名差异。"""
    norm_consts = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            norm_consts.append(code_normalize_instr_only(c))
        else:
            norm_consts.append(c)
    return (
        code.co_code,
        tuple(norm_consts),
    )


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        print("[main] 反编译源码无法编译，跳过统计")
        return

    # 仅比较两者都存在的函数（按名字）
    common = set(pyc_codes.keys()) & set(src_codes.keys())
    only_pyc = set(pyc_codes.keys()) - set(src_codes.keys())
    only_src = set(src_codes.keys()) - set(pyc_codes.keys())

    exact_match = []
    instr_match = []
    mismatch = []

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        if code_normalize(pc) == code_normalize(sc):
            exact_match.append(name)
            instr_match.append(name)
        elif code_normalize_instr_only(pc) == code_normalize_instr_only(sc):
            instr_match.append(name)
            mismatch.append((name, 'instr_ok_sig_diff'))
        else:
            mismatch.append((name, 'instr_diff'))

    total = len(common)
    print(f"\n=== R10 字节码一致性统计 ===")
    print(f"pyc code objects: {len(pyc_codes)}")
    print(f"src code objects: {len(src_codes)}")
    print(f"common:           {total}")
    print(f"only in pyc:      {len(only_pyc)} {sorted(only_pyc)[:10]}")
    print(f"only in src:      {len(only_src)} {sorted(only_src)[:10]}")
    print(f"完全匹配 (指令+签名): {len(exact_match)} / {total} = {100.0*len(exact_match)/max(total,1):.1f}%")
    print(f"指令匹配 (仅指令):    {len(instr_match)} / {total} = {100.0*len(instr_match)/max(total,1):.1f}%")
    print(f"\n--- 失败函数 ({len(mismatch)}) ---")
    for name, kind in mismatch:
        print(f"  [{kind}] {name}")


if __name__ == '__main__':
    main()
