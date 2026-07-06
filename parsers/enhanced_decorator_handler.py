#!/usr/bin/env python3
"""
增强的装饰器处理器

处理与装饰器相关的字节码指令，支持Python 3.11特性
"""

from typing import Optional, Any
from bytecode.bytecode_ops import Opcode
from core.ast_nodes import ASTName, ASTCall, ASTFunctionDef, ASTClassDef


class EnhancedDecoratorHandler:
    """增强的装饰器处理器"""
    
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.decorator_stack = []
        
    def can_handle(self, opcode: int, operand: Any) -> bool:
        """检查是否能够处理这个指令"""
        # 只在有装饰器待处理时处理这些指令
        has_pending_decorator = len(self.decorator_stack) > 0
        
        # 识别与装饰器相关的指令
        if opcode == Opcode.SETUP_ANNOTATIONS:
            return True
        elif opcode == Opcode.LOAD_NAME_A:
            # 只在有装饰器待处理时处理这些指令
            return has_pending_decorator
        elif opcode == Opcode.CALL_A:
            # [关键修复] CALL_A指令不应该由装饰器处理器处理
            # 因为CALL_A可能用于BUILD_CLASS，需要由主处理器处理
            return False
        
        return False
    
    def handle(self, opcode: int, operand: Any, ast_builder) -> Optional[Any]:
        """处理与装饰器相关的指令"""
        print(f"[DECORATOR_HANDLER] handle被调用，opcode={opcode}, operand={operand}")
        if opcode == Opcode.LOAD_NAME_A:
            return self._handle_load_name(operand, ast_builder)
        elif opcode == Opcode.CALL_A:
            return self._handle_call_function(operand, ast_builder)
        elif opcode == Opcode.SETUP_ANNOTATIONS:
            return self._handle_setup_annotations(operand, ast_builder)
        
        print(f"[DECORATOR_HANDLER] 没有匹配的处理器，返回None")
        return None
    
    def _handle_load_name(self, operand: Any, ast_builder) -> Optional[Any]:
        """处理LOAD_NAME_A指令"""
        # 从名称空间中加载一个名称（Python 3.11+）
        # 正确的方式：从 module.code.get().names 获取名称列表
        name = f"__unknown_name_{operand}__"
        
        if ast_builder.module and ast_builder.module.code:
            names = ast_builder.module.code.get().names
            if names and names.get():
                names_obj = names.get()
                # 处理 PycSequence
                if hasattr(names_obj, 'size') and hasattr(names_obj, 'get'):
                    if 0 <= operand < names_obj.size():
                        try:
                            name_ref = names_obj.get(operand)
                            if name_ref:
                                name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                                if hasattr(name_obj, 'value'):
                                    name = name_obj.value
                                else:
                                    name = str(name_obj)
                        except (IndexError, TypeError, AttributeError):
                            pass
        
        # 创建一个名称节点
        name_node = ASTName(name)
        
        # 检查是否是装饰器名称
        if name.startswith('@'):
            # 这是装饰器名称，压入装饰器栈
            self.decorator_stack.append(name_node)
        
        # 将名称节点压入栈
        ast_builder.stack.push(name_node)
        
        return None
    
    def _handle_call_function(self, operand: Any, ast_builder) -> Optional[Any]:
        """处理CALL_FUNCTION_EX指令"""
        # 从栈中弹出参数并调用函数
        if ast_builder.stack.empty():
            return None
        
        # 根据operand确定如何处理参数
        # operand可能包含有关参数数量的信息
        
        # 这里是简化处理，实际应该根据operand的值精确处理
        # 获取调用信息
        if operand & 0x1:  # 如果设置了标志位
            # 有关键字参数
            if ast_builder.stack.empty():
                return None
            kwargs = ast_builder.stack.pop()
        else:
            kwargs = None
        
        if operand & 0x2:  # 如果设置了标志位
            # 有位置参数
            arg_count = operand >> 2  # 获取参数数量
            args = []
            
            # 弹出参数
            for _ in range(arg_count):
                if ast_builder.stack.empty():
                    break
                args.append(ast_builder.stack.pop())
            
            # 反转参数顺序（栈是后进先出）
            args.reverse()
        else:
            args = None
        
        # 获取函数对象
        if ast_builder.stack.empty():
            return None
        
        func = ast_builder.stack.pop()
        
        # 创建调用节点
        call_node = ASTCall(func, args or [], kwargs or [])
        
        # 将调用结果压入栈
        ast_builder.stack.push(call_node)
        
        # 检查是否是装饰器调用
        if isinstance(func, ASTName) and hasattr(func, 'id'):
            decorator_name = func.id
            if decorator_name.startswith('@'):
                # 这是装饰器调用
                decorator_node = call_node
                
                # 获取被装饰的目标（函数或类）
                if not ast_builder.stack.empty():
                    target = ast_builder.stack.pop()
                    
                    # 应用装饰器
                    if isinstance(target, ASTFunctionDef):
                        # 装饰函数
                        target.decorator_list.append(decorator_node)
                        ast_builder.stack.push(target)
                    elif isinstance(target, ASTClassDef):
                        # 装饰类
                        target.decorator_list.append(decorator_node)
                        ast_builder.stack.push(target)
                    else:
                        # 不支持的装饰目标类型
                        ast_builder.stack.push(call_node)
                else:
                    # 没有被装饰的目标，先将装饰器保存
                    ast_builder.stack.push(call_node)
        
        return None
    
    def _handle_setup_annotations(self, operand: Any, ast_builder) -> Optional[Any]:
        """处理SETUP_ANNOTATIONS指令"""
        # Python 3.10+引入的指令，用于处理类型注解
        # 设置 annotations 变量，存储所有类型注解
        if ast_builder.stack.empty():
            return None
        
        # 弹出注解字典
        annotations_dict = ast_builder.stack.pop()
        
        # 创建赋值节点，将注解存储到__annotations__变量
        annotations_node = ASTName('__annotations__', ASTName.Store)
        assign_node = ASTAssign([annotations_node], annotations_dict)
        
        # 发射节点
        ast_builder._emit(assign_node)
        
        return None