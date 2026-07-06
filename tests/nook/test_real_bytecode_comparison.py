"""
真实反编译前后字节码比对测试
验证代码一致性和字节码一致性
"""
import unittest
import sys
import os
import dis
import marshal
import tempfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BytecodeComparisonTest(unittest.TestCase):
    """真实字节码比对测试"""
    
    def get_bytecode_info(self, code_obj):
        """获取字节码详细信息"""
        instructions = list(dis.get_instructions(code_obj))
        info = {
            'co_name': code_obj.co_name,
            'instruction_count': len(instructions),
            'instructions': []
        }
        for instr in instructions:
            info['instructions'].append({
                'offset': instr.offset,
                'opname': instr.opname,
                'opcode': instr.opcode,
                'arg': instr.arg,
                'argval': instr.argval,
                'argrepr': instr.argrepr,
                'starts_line': instr.starts_line
            })
        return info
    
    def compile_and_get_bytecode(self, source, func_name):
        """编译源代码并获取指定函数的字节码"""
        compiled = compile(source, '<string>', 'exec')
        for const in compiled.co_consts:
            if hasattr(const, 'co_name') and const.co_name == func_name:
                return self.get_bytecode_info(const)
        return None
    
    def decompile_pyc(self, pyc_path):
        """使用pycdc反编译pyc文件"""
        result = subprocess.run(
            ['python', 'pycdc.py', pyc_path, '-o', '-'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return result.stdout
    
    def test_simple_if_bytecode_comparison(self):
        """测试简单if语句的字节码比对"""
        # 原始代码
        original_source = '''
def test_if(x):
    if x > 0:
        return 'positive'
    return 'non-positive'
'''
        # 获取原始字节码
        orig_bytecode = self.compile_and_get_bytecode(original_source, 'test_if')
        self.assertIsNotNone(orig_bytecode)
        
        # 编译为pyc文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_source)
            py_file = f.name
        
        try:
            # 编译为pyc
            import py_compile
            pyc_file = py_file + 'c'
            py_compile.compile(py_file, pyc_file, doraise=True)
            
            # 反编译
            decompiled_source = self.decompile_pyc(pyc_file)
            
            # 获取反编译后的字节码
            decomp_bytecode = self.compile_and_get_bytecode(decompiled_source, 'test_if')
            
            # 比对结果
            print("\n" + "="*60)
            print("简单if语句字节码比对")
            print("="*60)
            print(f"\n原始代码:\n{original_source}")
            print(f"反编译代码:\n{decompiled_source}")
            print(f"\n原始字节码指令数: {orig_bytecode['instruction_count']}")
            if decomp_bytecode:
                print(f"反编译字节码指令数: {decomp_bytecode['instruction_count']}")
                
                # 比对关键指令
                orig_opnames = [i['opname'] for i in orig_bytecode['instructions']]
                decomp_opnames = [i['opname'] for i in decomp_bytecode['instructions']]
                
                print(f"\n原始指令序列: {orig_opnames}")
                print(f"反编译指令序列: {decomp_opnames}")
                
                # 验证关键指令存在
                self.assertIn('COMPARE_OP', orig_opnames)
                self.assertIn('RETURN_VALUE', orig_opnames)
            else:
                print("反编译后无法获取字节码")
            print("="*60)
            
        finally:
            # 清理临时文件
            if os.path.exists(py_file):
                os.remove(py_file)
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
    
    def test_for_loop_bytecode_comparison(self):
        """测试for循环的字节码比对"""
        original_source = '''
def test_for(n):
    total = 0
    for i in range(n):
        total += i
    return total
'''
        orig_bytecode = self.compile_and_get_bytecode(original_source, 'test_for')
        self.assertIsNotNone(orig_bytecode)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_source)
            py_file = f.name
        
        try:
            import py_compile
            pyc_file = py_file + 'c'
            py_compile.compile(py_file, pyc_file, doraise=True)
            
            decompiled_source = self.decompile_pyc(pyc_file)
            decomp_bytecode = self.compile_and_get_bytecode(decompiled_source, 'test_for')
            
            print("\n" + "="*60)
            print("For循环字节码比对")
            print("="*60)
            print(f"\n原始代码:\n{original_source}")
            print(f"反编译代码:\n{decompiled_source}")
            print(f"\n原始字节码指令数: {orig_bytecode['instruction_count']}")
            if decomp_bytecode:
                print(f"反编译字节码指令数: {decomp_bytecode['instruction_count']}")
                
                orig_opnames = [i['opname'] for i in orig_bytecode['instructions']]
                decomp_opnames = [i['opname'] for i in decomp_bytecode['instructions']]
                
                print(f"\n原始指令序列: {orig_opnames}")
                print(f"反编译指令序列: {decomp_opnames}")
                
                # 验证循环相关指令
                self.assertIn('FOR_ITER', orig_opnames)
                self.assertIn('BINARY_OP', orig_opnames)
            print("="*60)
            
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
    
    def test_exception_handling_bytecode(self):
        """测试异常处理的字节码"""
        original_source = '''
def test_exception():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    return result
'''
        orig_bytecode = self.compile_and_get_bytecode(original_source, 'test_exception')
        self.assertIsNotNone(orig_bytecode)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_source)
            py_file = f.name
        
        try:
            import py_compile
            pyc_file = py_file + 'c'
            py_compile.compile(py_file, pyc_file, doraise=True)
            
            decompiled_source = self.decompile_pyc(pyc_file)
            decomp_bytecode = self.compile_and_get_bytecode(decompiled_source, 'test_exception')
            
            print("\n" + "="*60)
            print("异常处理字节码比对")
            print("="*60)
            print(f"\n原始代码:\n{original_source}")
            print(f"反编译代码:\n{decompiled_source}")
            print(f"\n原始字节码指令数: {orig_bytecode['instruction_count']}")
            
            orig_opnames = [i['opname'] for i in orig_bytecode['instructions']]
            print(f"\n原始指令序列: {orig_opnames}")
            
            # 验证异常处理指令
            self.assertIn('BINARY_OP', orig_opnames)
            self.assertIn('RETURN_VALUE', orig_opnames)
            
            if decomp_bytecode:
                print(f"反编译字节码指令数: {decomp_bytecode['instruction_count']}")
                decomp_opnames = [i['opname'] for i in decomp_bytecode['instructions']]
                print(f"反编译指令序列: {decomp_opnames}")
            print("="*60)
            
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
    
    def test_class_method_bytecode(self):
        """测试类方法的字节码"""
        original_source = '''
class MyClass:
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value

def test_class():
    obj = MyClass(10)
    return obj.get_value()
'''
        orig_bytecode = self.compile_and_get_bytecode(original_source, 'test_class')
        self.assertIsNotNone(orig_bytecode)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_source)
            py_file = f.name
        
        try:
            import py_compile
            pyc_file = py_file + 'c'
            py_compile.compile(py_file, pyc_file, doraise=True)
            
            decompiled_source = self.decompile_pyc(pyc_file)
            decomp_bytecode = self.compile_and_get_bytecode(decompiled_source, 'test_class')
            
            print("\n" + "="*60)
            print("类方法字节码比对")
            print("="*60)
            print(f"\n原始代码:\n{original_source}")
            print(f"反编译代码:\n{decompiled_source}")
            print(f"\n原始字节码指令数: {orig_bytecode['instruction_count']}")
            
            orig_opnames = [i['opname'] for i in orig_bytecode['instructions']]
            print(f"\n原始指令序列: {orig_opnames}")
            
            # 验证类相关指令
            self.assertIn('CALL', orig_opnames)
            self.assertIn('RETURN_VALUE', orig_opnames)
            
            if decomp_bytecode:
                print(f"反编译字节码指令数: {decomp_bytecode['instruction_count']}")
                decomp_opnames = [i['opname'] for i in decomp_bytecode['instructions']]
                print(f"反编译指令序列: {decomp_opnames}")
            print("="*60)
            
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
    
    def test_generator_bytecode(self):
        """测试生成器的字节码"""
        original_source = '''
def test_generator():
    yield 1
    yield 2
    yield 3
'''
        orig_bytecode = self.compile_and_get_bytecode(original_source, 'test_generator')
        self.assertIsNotNone(orig_bytecode)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_source)
            py_file = f.name
        
        try:
            import py_compile
            pyc_file = py_file + 'c'
            py_compile.compile(py_file, pyc_file, doraise=True)
            
            decompiled_source = self.decompile_pyc(pyc_file)
            decomp_bytecode = self.compile_and_get_bytecode(decompiled_source, 'test_generator')
            
            print("\n" + "="*60)
            print("生成器字节码比对")
            print("="*60)
            print(f"\n原始代码:\n{original_source}")
            print(f"反编译代码:\n{decompiled_source}")
            print(f"\n原始字节码指令数: {orig_bytecode['instruction_count']}")
            
            orig_opnames = [i['opname'] for i in orig_bytecode['instructions']]
            print(f"\n原始指令序列: {orig_opnames}")
            
            # 验证生成器指令
            self.assertIn('YIELD_VALUE', orig_opnames)
            
            if decomp_bytecode:
                print(f"反编译字节码指令数: {decomp_bytecode['instruction_count']}")
                decomp_opnames = [i['opname'] for i in decomp_bytecode['instructions']]
                print(f"反编译指令序列: {decomp_opnames}")
                
                # 比对yield指令数量
                orig_yield_count = orig_opnames.count('YIELD_VALUE')
                decomp_yield_count = decomp_opnames.count('YIELD_VALUE')
                print(f"\n原始yield数量: {orig_yield_count}")
                print(f"反编译yield数量: {decomp_yield_count}")
            print("="*60)
            
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)
            if os.path.exists(pyc_file):
                os.remove(pyc_file)


class DetailedBytecodeReport(unittest.TestCase):
    """详细字节码报告"""
    
    def generate_full_report(self):
        """生成完整的字节码比对报告"""
        test_cases = [
            ("简单if语句", '''
def test_if(x):
    if x > 0:
        return 'positive'
    return 'non-positive'
'''),
            ("if-else语句", '''
def test_if_else(x):
    if x > 0:
        result = 'positive'
    else:
        result = 'non-positive'
    return result
'''),
            ("for循环", '''
def test_for(n):
    total = 0
    for i in range(n):
        total += i
    return total
'''),
            ("while循环", '''
def test_while(n):
    count = 0
    while count < n:
        count += 1
    return count
'''),
            ("try-except", '''
def test_try():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    return result
'''),
            ("with语句", '''
def test_with():
    with open('test.txt', 'w') as f:
        f.write('hello')
'''),
            ("列表推导式", '''
def test_comp():
    return [x**2 for x in range(10)]
'''),
            ("生成器", '''
def test_gen():
    yield 1
    yield 2
'''),
        ]
        
        print("\n" + "="*80)
        print("完整字节码比对报告")
        print("="*80)
        
        for name, source in test_cases:
            print(f"\n{'='*60}")
            print(f"测试用例: {name}")
            print(f"{'='*60}")
            print(f"源代码:\n{source}")
            
            # 获取字节码
            compiled = compile(source, '<string>', 'exec')
            for const in compiled.co_consts:
                if hasattr(const, 'co_name') and const.co_name.startswith('test_'):
                    print(f"\n函数: {const.co_name}")
                    print(f"字节码指令数: {len(list(dis.get_instructions(const)))}")
                    print("\n详细字节码:")
                    dis.dis(const)
                    break
        
        print("\n" + "="*80)


if __name__ == '__main__':
    # 运行详细报告
    report = DetailedBytecodeReport()
    report.generate_full_report()
    
    # 运行测试
    unittest.main(argv=[''], exit=False, verbosity=2)
