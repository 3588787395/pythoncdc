"""Round 33: 实验——确定 3.11 类体中函数定义间 NOP 行号锚点的产生规则。"""
import dis, types

def compile_class(src):
    code = compile(src, '<t>', 'exec')
    # 找类体 code：co_consts 中名为 C 的 code
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == 'C':
            return c
    return None

def nops_of(co):
    return [instr.offset for instr in dis.get_instructions(co) if instr.opname == 'NOP']

CASES = {
    'A_no_blank': '''class C:
    def f1(self):
        return 1
    def f2(self):
        return 2
    def f3(self):
        return 3
''',
    'B_one_blank_between': '''class C:
    def f1(self):
        return 1

    def f2(self):
        return 2

    def f3(self):
        return 3
''',
    'C_property_then_def': '''class C:
    @property
    def f1(self):
        return 1
    def f2(self):
        return 2
''',
    'D_def_then_property': '''class C:
    def f1(self):
        return 1
    @property
    def f2(self):
        return 2
''',
    'E_property_then_blank_def': '''class C:
    @property
    def f1(self):
        return 1

    def f2(self):
        return 2
''',
    'F_docstring_then_def': '''class C:
    def f1(self):
        """docstring"""
        return 1
    def f2(self):
        return 2
''',
    'G_multi_stmt_then_def': '''class C:
    def f1(self):
        x = 1
        y = 2
        return x + y
    def f2(self):
        return 2
''',
}

for name, src in CASES.items():
    co = compile_class(src)
    print('%-28s NOP offsets: %s' % (name, nops_of(co)))
