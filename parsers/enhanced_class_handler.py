#!/usr/bin/env python3
"""
增强的类处理器

处理与类相关的字节码指令，支持Python 3.11特性
"""

from typing import Optional, Any
from bytecode.bytecode_ops import Opcode
from core.ast_nodes import ASTClassDef, ASTName, ASTAssign, ASTObject


class EnhancedClassHandler:
    """增强的类处理器"""
    
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.class_name_stack = []
        self.class_def_stack = []
        self.in_class_body = False
        
    def can_handle(self, opcode: int, operand: Any) -> bool:
        """检查是否能够处理这个指令"""
        # 只在类定义上下文中处理这些指令
        from .context_manager import ContextType
        is_class_context = self.context_manager.current_context_type() == ContextType.CLASS
        
        # 🔧 关键修复：LOAD_BUILD_CLASS只在类定义上下文中处理
        # 在Python 3.11+中，LOAD_BUILD_CLASS不再用于类定义
        if opcode == Opcode.LOAD_BUILD_CLASS:
            return is_class_context  # 只在类上下文中处理
        elif opcode in (Opcode.LOAD_NAME_A, Opcode.STORE_NAME_A):
            # 只在类定义上下文中处理这些指令
            return is_class_context
        elif opcode == Opcode.CALL_A:
            # [关键修复] CALL_A指令在类定义上下文中处理
            # 但在模块级别，应该由主处理器处理（用于BUILD_CLASS）
            return is_class_context
        
        return False
    
    def handle(self, opcode: int, operand: Any, ast_builder) -> Optional[Any]:
        """处理与类相关的指令"""
        if opcode == Opcode.LOAD_BUILD_CLASS:
            return self._handle_load_build_class(operand, ast_builder)
        elif opcode == Opcode.LOAD_NAME_A:
            return self._handle_load_name(operand, ast_builder)
        elif opcode == Opcode.STORE_NAME_A:
            return self._handle_store_name(operand, ast_builder)
        elif opcode == Opcode.CALL_A:
            return self._handle_call_function(operand, ast_builder)
        
        return None
    
    def _handle_load_build_class(self, operand: Any, ast_builder) -> Optional[Any]:
        """处理LOAD_BUILD_CLASS指令"""
        # Python 3.11引入的指令，用于处理类创建
        # 在类定义开始时弹出栈上的函数对象
        if not ast_builder.stack.empty():
            class_func = ast_builder.stack.pop()
            
            # 检查是否在类上下文中
            context = self.context_manager.get_current_context()
            if context and context.context_type.value == 'class':
                # 这可能是一个嵌套类定义
                # 弹出类定义上下文
                old_context = self.context_manager.pop_context()
                
                # 类定义处理已完成
                return None
            else:
                # 这可能是一个新的类定义开始
                # 将函数对象压回栈中（保留以供后续处理）
                ast_builder.stack.push(class_func)
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
        
        # 将名称节点压入栈
        ast_builder.stack.push(name_node)
        
        return None
    
    def _handle_store_name(self, operand: Any, ast_builder) -> Optional[Any]:
        """处理STORE_NAME_A指令"""
        # 在名称空间中存储一个名称（Python 3.11+）
        if ast_builder.stack.empty():
            return None
        
        # 弹出值
        value = ast_builder.stack.pop()
        
        # 获取名称
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
        
        # 创建赋值节点
        target = ASTName(name)
        assign_node = ASTAssign([target], value)
        
        # 发射节点
        ast_builder._emit(assign_node)
        
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
        from core.ast_nodes import ASTCall
        call_node = ASTCall(func, args or [], kwargs or [])
        
        # 将调用结果压入栈
        ast_builder.stack.push(call_node)
        
        return None