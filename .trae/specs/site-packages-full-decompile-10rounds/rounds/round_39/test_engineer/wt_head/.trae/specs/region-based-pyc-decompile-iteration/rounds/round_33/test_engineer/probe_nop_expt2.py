"""Round 33: 实验——property 函数体后不同数量空行对 NOP 的影响。"""
import dis, types

def class_nops(src):
    code = compile(src, '<t>', 'exec')
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == 'C':
            out = []
            for instr in dis.get_instructions(c):
                if instr.opname == 'NOP':
                    out.append((instr.offset, instr.starts_line))
            return out
    return None

# 实验 A: @property 函数 + N 空行 + 普通函数
for n in range(1, 13):
    blank = '\n' * n
    src = 'class C:\n    @property\n    def f1(self):\n        return 1\n' + blank + '    def f2(self):\n        return 2\n'
    print('A blank=%2d: NOPs=%s' % (n, class_nops(src)))

print()
# 实验 B: 普通函数 + N 空行 + 普通函数
for n in range(1, 13):
    blank = '\n' * n
    src = 'class C:\n    def f1(self):\n        return 1\n' + blank + '    def f2(self):\n        return 2\n'
    print('B blank=%2d: NOPs=%s' % (n, class_nops(src)))
