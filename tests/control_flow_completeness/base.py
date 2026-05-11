import unittest


class ControlFlowCompletenessTest(unittest.TestCase):
    """控制流完备性测试基类"""

    SOURCE_CODE = ""

    def compile_source(self):
        """编译源代码为code object"""
        return compile(self.SOURCE_CODE, '<test>', 'exec')

    def decompile(self, code_obj):
        """使用CFGBuilder + RegionASTGenerator + CFGCodeGenerator反编译

        [P2-2026] 使用函数级code object进行反编译
        模块级CFG只包含MAKE_FUNCTION指令，不包含函数体控制流。
        必须提取嵌套函数的code object才能正确反编译。
        """
        from core.cfg import CFGBuilder, RegionASTGenerator
        from core.cfg.code_generator import CFGCodeGenerator

        func_code = self._extract_func_code(code_obj)

        if func_code:
            cfg = CFGBuilder().build(func_code)
            gen = RegionASTGenerator(cfg)
            ast = gen.generate()
            code_gen = CFGCodeGenerator()
            return code_gen.generate(ast)
        else:
            cfg = CFGBuilder().build(code_obj)
            gen = RegionASTGenerator(cfg)
            ast = gen.generate()
            code_gen = CFGCodeGenerator()
            return code_gen.generate(ast)

    def verify_syntax_valid(self):
        """验证反编译结果语法正确"""
        import ast as ast_module
        result = self.decompile(self.compile_source())
        try:
            ast_module.parse(result)
            return True
        except SyntaxError:
            return False

    def verify_bytecode_equivalence(self):
        """验证重编译后的字节码与原始一致"""
        original = self.compile_source()
        decompiled_code = self.decompile(original)

        func_code = self._extract_func_code(original)
        recompiled = compile(decompiled_code, '<recompiled>', 'exec')
        recomp_func = self._extract_func_code(recompiled)

        if not func_code or not recomp_func:
            return False

        return func_code.co_code == recomp_func.co_code

    def _extract_func_code(self, code_obj):
        """从模块级code object提取第一个函数"""
        for const in code_obj.co_consts:
            if hasattr(const, 'co_name') and const.co_name != '<module>':
                return const
        return None
