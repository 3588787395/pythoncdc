"""
字节码匹配器 - 智能选择最优反编译策略

通过分析字节码特征，决定使用CFG方法还是传统方法。
"""

import types
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum, auto


class ComplexityLevel(Enum):
    """复杂度等级"""
    SIMPLE = auto()      # 简单 - 使用CFG
    MODERATE = auto()    # 中等 - 根据历史成功率选择
    COMPLEX = auto()     # 复杂 - 使用传统方法


class BytecodeMatcher:
    """
    字节码匹配器
    
    分析代码对象的字节码特征，评估复杂度，
    推荐最适合的反编译方法。
    """
    
    # 复杂指令集合（传统方法处理更好）
    COMPLEX_OPCODES = {
        # 异常处理
        'SETUP_FINALLY', 'SETUP_EXCEPT', 'POP_EXCEPT', 'END_FINALLY',
        'PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'RERAISE',
        # 生成器/协程
        'YIELD_VALUE', 'YIELD_FROM', 'SEND', 'ASYNC_GEN_WRAP',
        # 复杂控制流
        'WITH_EXCEPT_START', 'BEFORE_ASYNC_WITH', 'SETUP_ASYNC_WITH',
        # 元编程
        'MAKE_FUNCTION', 'MAKE_CELL', 'LOAD_CLOSURE',
    }
    
    # 需要特殊处理的边界情况
    EDGE_CASE_PATTERNS = [
        # 推导式模式
        ('LOAD_CONST', 'LOAD_FAST', 'FOR_ITER'),
        # 多重嵌套if
        ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_FALSE'),
        # 复杂异常处理
        ('SETUP_FINALLY', 'SETUP_EXCEPT'),
    ]
    
    def __init__(self):
        self.history: Dict[str, Dict] = {}  # 历史成功率记录
    
    def analyze(self, code_obj: types.CodeType) -> ComplexityLevel:
        """
        分析代码对象的复杂度
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            复杂度等级
        """
        score = 0
        
        # 1. 检查字节码长度
        bytecode_len = len(code_obj.co_code)
        if bytecode_len > 1000:
            score += 3
        elif bytecode_len > 500:
            score += 2
        elif bytecode_len > 200:
            score += 1
        
        # 2. 分析指令类型
        instructions = self._disassemble_simple(code_obj)
        
        # 检查复杂指令
        complex_count = sum(1 for instr in instructions 
                          if instr['opname'] in self.COMPLEX_OPCODES)
        if complex_count > 5:
            score += 3
        elif complex_count > 2:
            score += 2
        elif complex_count > 0:
            score += 1
        
        # 3. 检查嵌套深度
        max_depth = self._calculate_nesting_depth(instructions)
        if max_depth > 5:
            score += 3
        elif max_depth > 3:
            score += 2
        elif max_depth > 2:
            score += 1
        
        # 4. 检查边界情况模式
        edge_case_count = self._count_edge_case_patterns(instructions)
        score += edge_case_count
        
        # 5. 检查历史成功率
        func_name = code_obj.co_name
        if func_name in self.history:
            cfg_success_rate = self.history[func_name].get('cfg_success_rate', 0.5)
            if cfg_success_rate < 0.3:
                score += 2  # CFG历史成功率低，倾向传统方法
            elif cfg_success_rate > 0.8:
                score -= 1  # CFG历史成功率高，倾向CFG方法
        
        # 根据总分判断复杂度
        if score >= 6:
            return ComplexityLevel.COMPLEX
        elif score >= 3:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
    def recommend_method(self, code_obj: types.CodeType) -> str:
        """
        推荐反编译方法
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            'cfg' 或 'traditional'
        """
        level = self.analyze(code_obj)
        
        if level == ComplexityLevel.SIMPLE:
            return 'cfg'
        elif level == ComplexityLevel.COMPLEX:
            return 'traditional'
        else:  # MODERATE
            # 检查历史记录
            func_name = code_obj.co_name
            if func_name in self.history:
                cfg_rate = self.history[func_name].get('cfg_success_rate', 0.5)
                trad_rate = self.history[func_name].get('traditional_success_rate', 0.5)
                return 'cfg' if cfg_rate >= trad_rate else 'traditional'
            else:
                return 'cfg'  # 默认尝试CFG
    
    def update_history(self, func_name: str, method: str, success: bool):
        """
        更新历史成功率
        
        Args:
            func_name: 函数名
            method: 使用的方法 ('cfg' 或 'traditional')
            success: 是否成功
        """
        if func_name not in self.history:
            self.history[func_name] = {
                'cfg_success_rate': 0.5,
                'traditional_success_rate': 0.5,
                'cfg_attempts': 0,
                'traditional_attempts': 0,
            }
        
        key = f'{method}_success_rate'
        attempts_key = f'{method}_attempts'
        
        # 使用指数移动平均更新成功率
        current_rate = self.history[func_name][key]
        alpha = 0.3  # 学习率
        new_rate = current_rate + alpha * (1.0 if success else 0.0 - current_rate)
        
        self.history[func_name][key] = new_rate
        self.history[func_name][attempts_key] += 1
    
    def _disassemble_simple(self, code_obj: types.CodeType) -> List[Dict]:
        """简单反汇编，获取指令列表"""
        instructions = []
        bytecode = code_obj.co_code
        
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]
            
            # 获取操作名
            opname = self._get_opcode_name(opcode)
            
            # 获取操作数（如果有）
            operand = None
            if opcode >= 90:  # 有参数的指令
                if i + 1 < len(bytecode):
                    operand = bytecode[i + 1]
                    i += 2
                else:
                    i += 1
            else:
                i += 1
            
            instructions.append({
                'offset': i,
                'opcode': opcode,
                'opname': opname,
                'operand': operand,
            })
        
        return instructions
    
    def _get_opcode_name(self, opcode: int) -> str:
        """获取操作码名称"""
        try:
            import dis
            return dis.opname.get(opcode, f'UNKNOWN({opcode})')
        except:
            return f'OPCODE_{opcode}'
    
    def _calculate_nesting_depth(self, instructions: List[Dict]) -> int:
        """计算最大嵌套深度"""
        depth = 0
        max_depth = 0
        
        for instr in instructions:
            opname = instr['opname']
            
            # 增加深度的指令
            if any(x in opname for x in ['SETUP_', 'FOR_ITER', 'JUMP']):
                depth += 1
                max_depth = max(max_depth, depth)
            # 减少深度的指令
            elif any(x in opname for x in ['POP_', 'END_']):
                depth = max(0, depth - 1)
        
        return max_depth
    
    def _count_edge_case_patterns(self, instructions: List[Dict]) -> int:
        """统计边界情况模式出现次数"""
        count = 0
        opnames = [instr['opname'] for instr in instructions]
        
        for pattern in self.EDGE_CASE_PATTERNS:
            pattern_len = len(pattern)
            for i in range(len(opnames) - pattern_len + 1):
                if tuple(opnames[i:i + pattern_len]) == pattern:
                    count += 1
        
        return count


# 便捷函数
def analyze_bytecode(code_obj: types.CodeType) -> ComplexityLevel:
    """分析字节码复杂度"""
    matcher = BytecodeMatcher()
    return matcher.analyze(code_obj)


def recommend_method(code_obj: types.CodeType) -> str:
    """推荐反编译方法"""
    matcher = BytecodeMatcher()
    return matcher.recommend_method(code_obj)
