"""Round 33: 最小复现实验——逐步逼近类体 NOP 触发条件。

策略：从 pyc 的真实布局出发，构造等价源码（同样的 def/体末/间隙），
逐条验证 3.11.7 编译器行为。每个实验打印类体 linetable 关键段。
"""
import dis, types

def dump_cls_lines(src, tag):
    code = compile(src, '<t>', 'exec')
    cls = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == 'C']
    if not cls:
        print('%-40s 无类体' % tag)
        return
    cls = cls[0]
    lines = {}
    for off, end, line in cls.co_lines():
        lines[off] = line
    # 提取每个 def 的边界段
    instrs = list(dis.get_instructions(cls))
    print('%-40s co_code=%d 行号序列:' % (tag, len(cls.co_code)))
    for ins in instrs:
        line = lines.get(ins.offset, '?')
        if ins.opname in ('NOP', 'STORE_NAME', 'LOAD_CONST', 'LOAD_NAME', 'MAKE_FUNCTION', 'PRECALL', 'CALL'):
            nm = ''
            if ins.opname == 'LOAD_CONST' and isinstance(ins.argval, types.CodeType):
                nm = ' <code %s>' % ins.argval.co_name
            elif ins.argval is not None:
                nm = ' %r' % ins.argval
            print('    %-5d L%-4s %-14s%s' % (ins.offset, line, ins.opname, nm))
    nops = [o for o, l in lines.items() if o + 2 <= len(cls.co_code) and cls.co_code[o] == 0x09]
    print('    NOP offsets: %s' % nops)
    print()

# 实验 1: 最小 property 类（get_operator 原型）
src = 'class C:\n    @property\n    def a(self):\n        return 1\n    def b(self):\n        return 2\n'
dump_cls_lines(src, 'E1 property 1行体 紧邻')

# 实验 2: 有间隙（末行4 -> def b 在 L12，差 8，模拟 252->260）
src = 'class C:\n    @property\n    def a(self):\n        return 1\n' + '\n' * 7 + '    def b(self):\n        return 2\n'
dump_cls_lines(src, 'E2 property 1行体 间隙8')

# 实验 3: 无 property，普通函数，间隙 8
src = 'class C:\n    def a(self):\n        return 1\n' + '\n' * 6 + '    def b(self):\n        return 2\n'
dump_cls_lines(src, 'E3 普通 1行体 间隙8')

# 实验 4: 普通函数 4 行体（get_clsc 原型：def L1238 体末1242 -> next 1253 差 11）
src = 'class C:\n    def a(self):\n        x = 1\n        y = 2\n        return x + y\n' + '\n' * 7 + '    def b(self, v=0):\n        return v\n'
dump_cls_lines(src, 'E4 普通4行体->默认参数 间隙8')
