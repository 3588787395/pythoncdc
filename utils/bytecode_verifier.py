"""
字节码验证工具
用于比较原始代码和反编译后代码的字节码一致性
"""

import dis
import marshal
import types
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BytecodeVerifier:
    """字节码验证器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.differences = []
    
    def get_bytecode_info(self, code_obj):
        """获取字节码信息"""
        instructions = list(dis.get_instructions(code_obj))
        info = {
            'co_name': code_obj.co_name,
            'co_filename': code_obj.co_filename,
            'co_firstlineno': code_obj.co_firstlineno,
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
    
    def compare_bytecode(self, original_code, decompiled_code):
        """比较两个字节码对象"""
        self.differences = []
        
        orig_info = self.get_bytecode_info(original_code)
        decomp_info = self.get_bytecode_info(decompiled_code)
        
        # 比较指令数量
        if orig_info['instruction_count'] != decomp_info['instruction_count']:
            self.differences.append({
                'type': 'instruction_count',
                'original': orig_info['instruction_count'],
                'decompiled': decomp_info['instruction_count']
            })
        
        # 比较每条指令
        min_len = min(len(orig_info['instructions']), len(decomp_info['instructions']))
        for i in range(min_len):
            orig_instr = orig_info['instructions'][i]
            decomp_instr = decomp_info['instructions'][i]
            
            instr_diff = {}
            
            if orig_instr['opname'] != decomp_instr['opname']:
                instr_diff['opname'] = {
                    'original': orig_instr['opname'],
                    'decompiled': decomp_instr['opname']
                }
            
            if orig_instr['arg'] != decomp_instr['arg']:
                instr_diff['arg'] = {
                    'original': orig_instr['arg'],
                    'decompiled': decomp_instr['arg']
                }
            
            if orig_instr['argval'] != decomp_instr['argval']:
                instr_diff['argval'] = {
                    'original': orig_instr['argval'],
                    'decompiled': decomp_instr['argval']
                }
            
            if instr_diff:
                instr_diff['offset'] = orig_instr['offset']
                self.differences.append({
                    'type': 'instruction',
                    'index': i,
                    'details': instr_diff
                })
        
        return len(self.differences) == 0
    
    def print_comparison(self, original_code, decompiled_code):
        """打印比较结果"""
        print("=" * 80)
        print("字节码比对结果")
        print("=" * 80)
        
        orig_info = self.get_bytecode_info(original_code)
        decomp_info = self.get_bytecode_info(decompiled_code)
        
        print(f"\n原始代码:")
        print(f"  函数名: {orig_info['co_name']}")
        print(f"  指令数: {orig_info['instruction_count']}")
        
        print(f"\n反编译代码:")
        print(f"  函数名: {decomp_info['co_name']}")
        print(f"  指令数: {decomp_info['instruction_count']}")
        
        print(f"\n差异统计:")
        print(f"  差异数: {len(self.differences)}")
        
        if self.differences:
            print(f"\n详细差异:")
            for diff in self.differences:
                if diff['type'] == 'instruction_count':
                    print(f"  指令数量不匹配: 原始={diff['original']}, 反编译={diff['decompiled']}")
                elif diff['type'] == 'instruction':
                    print(f"  指令 #{diff['index']} (offset={diff['details'].get('offset', 'N/A')}):")
                    for key, values in diff['details'].items():
                        if key != 'offset':
                            print(f"    {key}: 原始={values['original']}, 反编译={values['decompiled']}")
        else:
            print(f"\n✅ 字节码完全一致！")
        
        print("=" * 80)
    
    def verify_source(self, source_code, func_name):
        """验证源代码的反编译效果"""
        # 编译原始代码
        original_code = compile(source_code, '<original>', 'exec')
        
        # 找到目标函数
        original_func = None
        for const in original_code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == func_name:
                original_func = const
                break
        
        if not original_func:
            print(f"错误: 找不到函数 {func_name}")
            return False
        
        # 反编译（这里应该调用实际的反编译器）
        # 暂时直接编译源代码作为"反编译后"的代码
        # 实际使用时应该调用 pycdc 进行反编译
        decompiled_source = source_code  # 占位符
        decompiled_code = compile(decompiled_source, '<decompiled>', 'exec')
        
        decompiled_func = None
        for const in decompiled_code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == func_name:
                decompiled_func = const
                break
        
        if not decompiled_func:
            print(f"错误: 反编译后找不到函数 {func_name}")
            return False
        
        # 比较字节码
        is_match = self.compare_bytecode(original_func, decompiled_func)
        self.print_comparison(original_func, decompiled_func)
        
        return is_match


def verify_function_from_pyc(pyc_path, func_name, decompiled_source):
    """
    从.pyc文件验证函数的反编译效果
    
    Args:
        pyc_path: .pyc文件路径
        func_name: 要验证的函数名
        decompiled_source: 反编译后的源代码
    
    Returns:
        bool: 字节码是否一致
    """
    # 加载.pyc文件
    with open(pyc_path, 'rb') as f:
        f.read(16)  # 跳过头部
        code = marshal.load(f)
    
    # 找到目标函数
    original_func = None
    for const in code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == func_name:
            original_func = const
            break
    
    if not original_func:
        print(f"错误: 在.pyc文件中找不到函数 {func_name}")
        return False
    
    # 编译反编译后的代码
    decompiled_code = compile(decompiled_source, '<decompiled>', 'exec')
    
    decompiled_func = None
    for const in decompiled_code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == func_name:
            decompiled_func = const
            break
    
    if not decompiled_func:
        print(f"错误: 反编译后找不到函数 {func_name}")
        return False
    
    # 比较字节码
    verifier = BytecodeVerifier(verbose=True)
    is_match = verifier.compare_bytecode(original_func, decompiled_func)
    verifier.print_comparison(original_func, decompiled_func)
    
    return is_match


if __name__ == '__main__':
    # 测试示例
    source = '''
def test_simple_if(x):
    if x > 0:
        return 'positive'
    return 'non-positive'
'''
    
    verifier = BytecodeVerifier(verbose=True)
    result = verifier.verify_source(source, 'test_simple_if')
    print(f"\n验证结果: {'通过' if result else '失败'}")
