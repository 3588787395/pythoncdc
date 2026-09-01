"""Round 33: 系统性实验——类体函数间空行数量 vs NOP 行号锚点。"""
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

# 实验 1: property 函数 + N 空行 + 普通函数
for n in range(0, 7):
    blank = '\n' * n
    src = 'class C:\n    @property\n    def f1(self):\n        return 1\n' + blank + '    def f2(self):\n        return 2\n'
    print('blank=%d: NOPs=%s' % (n, class_nops(src)))

print()
# 实验 2: 普通函数 + N 空行 + 带默认参数函数
for n in range(0, 7):
    blank = '\n' * n
    src = 'class C:\n    def f1(self):\n        return 1\n' + blank + '    def f2(self, x=0):\n        return 2\n'
    print('blank=%d(默认参数): NOPs=%s' % (n, class_nops(src)))

print()
# 实验 3: 普通函数 + N 空行 + 普通函数
for n in range(0, 7):
    blank = '\n' * n
    src = 'class C:\n    def f1(self):\n        return 1\n' + blank + '    def f2(self):\n        return 2\n'
    print('blank=%d(无默认参数): NOPs=%s' % (n, class_nops(src)))
