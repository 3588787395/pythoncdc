"""Round 33: 验证常量语句（裸字符串/数字）在类体中产生 NOP。"""
import dis, types

def dump(src, tag):
    code = compile(src, '<t>', 'exec')
    cls = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == 'C'][0]
    print('==', tag, 'co_code=', len(cls.co_code))
    for ins in dis.get_instructions(cls):
        if ins.opname in ('NOP', 'STORE_NAME', 'LOAD_CONST', 'LOAD_NAME', 'MAKE_FUNCTION', 'PRECALL', 'CALL'):
            nm = ''
            if ins.opname == 'LOAD_CONST' and isinstance(ins.argval, types.CodeType):
                nm = ' <code %s>' % ins.argval.co_name
            elif ins.argval is not None:
                nm = ' %r' % ins.argval
            print('   %-4d L%-5s %-12s%s' % (ins.offset, str(ins.starts_line), ins.opname, nm))
    nops = []
    for ins in dis.get_instructions(cls):
        if ins.opname == 'NOP':
            nops.append((ins.offset, ins.starts_line))
    print('   NOPs:', nops)
    print()

# 实验 5: property 函数 + 函数间裸字符串 + 普通函数
src = ('class C:\n'
       '    @property\n'
       '    def a(self):\n'
       '        return 1\n'
       '    "hello string"\n'
       '    def b(self):\n'
       '        return 2\n')
dump(src, 'E5 裸字符串在函数间')

# 实验 6: 普通函数 + 数字常量 + 普通函数
src = ('class C:\n'
       '    def a(self):\n'
       '        return 1\n'
       '    12345\n'
       '    def b(self):\n'
       '        return 2\n')
dump(src, 'E6 数字常量在函数间')

# 实验 7: 普通函数 + 带空行 + 裸字符串 + 普通函数（模拟末行+2）
src = ('class C:\n'
       '    def a(self):\n'
       '        return 1\n'
       '\n'
       '    "mid string"\n'
       '    def b(self):\n'
       '        return 2\n')
dump(src, 'E7 空行+裸字符串')
