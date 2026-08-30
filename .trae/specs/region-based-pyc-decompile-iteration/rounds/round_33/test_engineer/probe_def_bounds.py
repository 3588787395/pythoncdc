"""Round 33: 遍历 PtradeAccount 类体所有 def 边界，分析 NOP 出现模式。

对每个 def 边界（前一个 def 的 STORE_NAME 之后到下一个 def 的 LOAD_CONST 之前）：
- 前函数名 / 前函数 co_lastlineno / 前函数 def 行
- 后函数名 / 后 def 行 / 后函数是否 property / 后函数是否带默认参数
- 该边界是否出现 NOP 及行号
与 OK 类体按 co_name 对齐，找出差异。
"""
import sys, marshal, types, py_compile, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_cls(code, name):
    return [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == name][0]


def last_line(code_obj):
    """3.11 无 co_lastlineno，用 co_lines 求最大行号。"""
    lines = [l for _, _, l in code_obj.co_lines() if l is not None]
    return max(lines) if lines else None


def analyze_cls(cls, tag):
    """返回 def 边界列表: [(前名, 前末行, 前def行, 后名, 后def行, NOP行号或None, 后带默认值?)]"""
    ins = list(dis.get_instructions(cls))
    # 找出所有函数定义边界
    bounds = []
    i = 0
    n = len(ins)
    last_def_name = None
    last_def_line = None
    last_code_obj = None   # 前一个 def 的 code 对象
    last_store_off = None
    pending = None  # 等待收集当前 def 信息
    while i < n:
        insn = ins[i]
        if insn.opname == 'LOAD_CONST' and isinstance(insn.argval, types.CodeType):
            code_obj = insn.argval
            def_line = insn.starts_line
            # 前一个 def 的 STORE_NAME 应该刚结束；检查 pending
            # 收集: 是否有默认参数 LOAD_CONST 在它前面
            has_defaults = False
            j = i - 1
            while j >= 0 and ins[j].offset >= insn.offset - 6:
                if ins[j].opname == 'LOAD_CONST' and isinstance(ins[j].argval, tuple):
                    has_defaults = True
                j -= 1
            # property: 前面有 LOAD_NAME 'property'
            has_property = False
            j = i - 1
            while j >= 0 and ins[j].offset >= insn.offset - 6:
                if ins[j].opname == 'LOAD_NAME' and ins[j].argval == 'property':
                    has_property = True
                j -= 1
            bounds.append({
                'name': code_obj.co_name,
                'def_line': def_line,
                'lastlineno': last_line(code_obj),
                'has_defaults': has_defaults,
                'has_property': has_property,
                'offset': insn.offset,
            })
        i += 1
    # 找 NOP 位置
    nops = {}
    for insn in ins:
        if insn.opname == 'NOP':
            nops[insn.offset] = insn.starts_line
    # 组装边界: 前一个 def 的 STORE 到后一个 def 的 LOAD 之间
    print('== %s: %d 个 def, %d 个 NOP ==' % (tag, len(bounds), len(nops)))
    rows = []
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        # 该边界是否有 NOP: NOP 偏移在 a.offset 与 b.offset 之间
        gap_nops = [(off, ln) for off, ln in nops.items() if a['offset'] < off < b['offset']]
        rows.append((a, b, gap_nops))
        f = lambda v: ('%d' % v) if isinstance(v, int) else '-'
        print('  %-30s def@%-5s 体末%-5s | %-30s def@%-5s %s%s | NOP=%s' % (
            a['name'], f(a['def_line']), f(a['lastlineno']),
            b['name'], f(b['def_line']),
            'prop ' if b['has_property'] else '',
            'defs ' if b['has_defaults'] else '',
            gap_nops))
    return rows


def main():
    pyc = load_code(PYC)
    cfile = py_compile.compile(OK, doraise=True, quiet=2)
    ok = load_code(cfile)
    a = find_cls(pyc, 'PtradeAccount')
    b = find_cls(ok, 'PtradeAccount')
    print('pyc len:', len(a.co_code), ' ok len:', len(b.co_code))
    print()
    analyze_cls(a, 'PYC')
    print()
    analyze_cls(b, 'OK')


if __name__ == '__main__':
    main()
