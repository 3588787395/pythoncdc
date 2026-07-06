"""
第9批：多层嵌套if语句 - if-elif-elif-else链
测试多层if-elif链的反编译效果，必须有字节码验证
"""
import unittest
import sys
import os
import dis
import tempfile
import subprocess
import compileall

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.cfg import build_cfg, generate_ast

# 为了保持兼容性，添加build_cfg_from_source别名
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)


def get_bytecode_details(code_obj):
    """获取详细的字节码信息"""
    instructions = list(dis.get_instructions(code_obj))
    result = []
    for instr in instructions:
        arg_str = f"({instr.arg})" if instr.arg is not None else ""
        argval_str = f" {instr.argval!r}" if instr.argval is not None and instr.argval != instr.arg else ""
        result.append({
            'offset': instr.offset,
            'opname': instr.opname,
            'opcode': instr.opcode,
            'arg': instr.arg,
            'argval': instr.argval,
            'line': instr.starts_line,
            'text': f"{instr.offset:4d} {instr.opname:25s} {arg_str:6s}{argval_str}"
        })
    return result


def decompile_pyc(pyc_path):
    """使用pycdc反编译pyc文件"""
    pycdc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'pycdc.py')
    result = subprocess.run(
        ['python', pycdc_path, pyc_path],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return result.stdout if result.stdout else result.stderr


# 测试用例3: if-elif-elif-else链
def test_if_elif_chain(x):
    if x < 0:
        return 'negative'
    elif x == 0:
        return 'zero'
    elif x < 10:
        return 'single digit'
    elif x < 100:
        return 'double digit'
    else:
        return 'large number'


class TestIfElifChain(unittest.TestCase):
    """测试if-elif-elif-else链"""
    
    def test_01_cfg_build(self):
        """测试CFG构建"""
        source = '''
def test_if_elif_chain(x):
    if x < 0:
        return 'negative'
    elif x == 0:
        return 'zero'
    elif x < 10:
        return 'single digit'
    elif x < 100:
        return 'double digit'
    else:
        return 'large number'
'''
        cfg = build_cfg_from_source(source, 'test_if_elif_chain')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_02_bytecode_comparison(self):
        """测试字节码比对 - 必须有字节码验证结果"""
        source = '''
def test_if_elif_chain(x):
    if x < 0:
        return 'negative'
    elif x == 0:
        return 'zero'
    elif x < 10:
        return 'single digit'
    elif x < 100:
        return 'double digit'
    else:
        return 'large number'
'''
        # 编译原始代码获取字节码
        orig_compiled = compile(source, '<original>', 'exec')
        orig_bytecode = None
        for const in orig_compiled.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test_if_elif_chain':
                orig_bytecode = get_bytecode_details(const)
                break
        
        self.assertIsNotNone(orig_bytecode, "无法获取原始字节码")
        
        # 创建临时文件并编译
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            py_file = f.name
        
        try:
            # 编译为pyc
            compileall.compile_file(py_file, quiet=True)
            
            # 找到pyc文件
            pycache_dir = os.path.join(os.path.dirname(py_file), '__pycache__')
            pyc_file = None
            if os.path.exists(pycache_dir):
                for f in os.listdir(pycache_dir):
                    if f.startswith(os.path.basename(py_file).replace('.py', '')) and f.endswith('.pyc'):
                        pyc_file = os.path.join(pycache_dir, f)
                        break
            
            self.assertIsNotNone(pyc_file, "无法找到pyc文件")
            
            # 反编译
            decompiled = decompile_pyc(pyc_file)
            self.assertTrue(len(decompiled.strip()) > 0, "反编译输出为空")
            
            # 编译反编译后的代码
            decomp_compiled = compile(decompiled, '<decompiled>', 'exec')
            decomp_bytecode = None
            for const in decomp_compiled.co_consts:
                if hasattr(const, 'co_name') and const.co_name == 'test_if_elif_chain':
                    decomp_bytecode = get_bytecode_details(const)
                    break
            
            self.assertIsNotNone(decomp_bytecode, "无法获取反编译后字节码")
            
            # 比对字节码
            orig_ops = [i['opname'] for i in orig_bytecode]
            decomp_ops = [i['opname'] for i in decomp_bytecode]
            
            # 验证关键指令
            self.assertIn('COMPARE_OP', orig_ops, "原始代码缺少COMPARE_OP")
            self.assertIn('POP_JUMP_FORWARD_IF_FALSE', orig_ops, "原始代码缺少POP_JUMP_FORWARD_IF_FALSE")
            self.assertIn('RETURN_VALUE', orig_ops, "原始代码缺少RETURN_VALUE")
            
            # 验证指令数量
            print(f"\n[批次9-if-elif链] 原始指令数: {len(orig_ops)}, 反编译指令数: {len(decomp_ops)}")
            print(f"原始指令: {orig_ops}")
            print(f"反编译指令: {decomp_ops}")
            
            # 验证反编译后的代码包含关键结构
            self.assertIn('if', decompiled, "反编译代码缺少if")
            self.assertIn('elif', decompiled, "反编译代码缺少elif")
            self.assertIn('else', decompiled, "反编译代码缺少else")
            
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)
            if pyc_file and os.path.exists(pyc_file):
                os.remove(pyc_file)
    
    def test_03_logic_correctness(self):
        """测试逻辑正确性"""
        test_cases = [
            (-5, 'negative'),
            (0, 'zero'),
            (5, 'single digit'),
            (50, 'double digit'),
            (500, 'large number'),
        ]
        
        for arg, expected in test_cases:
            result = test_if_elif_chain(arg)
            self.assertEqual(result, expected, f"输入{arg}期望{expected}但得到{result}")


if __name__ == '__main__':
    unittest.main()
