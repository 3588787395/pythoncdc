"""
上下文管理器

用于跟踪反编译过程中的上下文信息，支持嵌套结构处理
"""

from typing import List, Optional, Dict, Any
from enum import Enum


class ContextType(Enum):
    """上下文类型"""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    CONTROL_FLOW = "control_flow"
    EXCEPTION = "exception"
    DECORATOR = "decorator"


class ContextInfo:
    """上下文信息"""
    def __init__(self, context_type: ContextType, name: str = "", parent=None):
        self.context_type = context_type
        self.name = name
        self.parent = parent
        self.children: List['ContextInfo'] = []
        self.data: Dict[str, Any] = {}
        
        # 特定上下文的信息
        if context_type == ContextType.CLASS:
            self.data.update({
                'methods': [],
                'properties': [],
                'class_variables': [],
                'decorators': []
            })
        elif context_type == ContextType.FUNCTION:
            self.data.update({
                'parameters': [],
                'decorators': [],
                'return_type': None,
                'is_async': False,
                'is_generator': False
            })
        elif context_type == ContextType.METHOD:
            self.data.update({
                'parameters': [],
                'decorators': [],
                'return_type': None,
                'is_async': False,
                'is_generator': False,
                'is_static': False,
                'is_class_method': False,
                'is_property': False
            })


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.context_stack: List[ContextInfo] = []
        self.root_context = ContextInfo(ContextType.MODULE, "module")
        self.current_context = self.root_context
    
    def push_context(self, context_type: ContextType, name: str = "") -> ContextInfo:
        """推入新的上下文"""
        new_context = ContextInfo(context_type, name, self.current_context)
        self.context_stack.append(new_context)
        self.current_context = new_context
        
        # 添加到父上下文的子节点
        if self.current_context.parent:
            self.current_context.parent.children.append(new_context)
        
        return new_context
    
    def pop_context(self) -> Optional[ContextInfo]:
        """弹出当前上下文"""
        if not self.context_stack:
            return None
        
        old_context = self.context_stack.pop()
        self.current_context = old_context.parent if old_context.parent else self.root_context
        
        return old_context
    
    def current_context_type(self) -> Optional[ContextType]:
        """获取当前上下文类型"""
        return self.current_context.context_type if self.current_context else None
    
    def get_current_context(self) -> Optional[ContextInfo]:
        """获取当前上下文"""
        return self.current_context
    
    def is_in_context(self, context_type: ContextType) -> bool:
        """检查是否在指定类型的上下文中"""
        for context in reversed(self.context_stack):
            if context.context_type == context_type:
                return True
        return False
    
    def find_nearest_context(self, context_type: ContextType) -> Optional[ContextInfo]:
        """查找最近的指定类型上下文"""
        for context in reversed(self.context_stack):
            if context.context_type == context_type:
                return context
        return None
    
    def get_context_data(self, key: str, default=None):
        """获取当前上下文的数据"""
        return self.current_context.data.get(key, default)
    
    def set_context_data(self, key: str, value):
        """设置当前上下文的数据"""
        self.current_context.data[key] = value
    
    def update_context_data(self, key: str, value):
        """更新当前上下文的数据"""
        if key in self.current_context.data:
            if isinstance(self.current_context.data[key], list):
                self.current_context.data[key].append(value)
            elif isinstance(self.current_context.data[key], dict):
                self.current_context.data[key].update(value)
            else:
                self.current_context.data[key] = value
        else:
            self.current_context.data[key] = value
    
    def get_all_contexts_of_type(self, context_type: ContextType) -> List[ContextInfo]:
        """获取所有指定类型的上下文"""
        result = []
        
        def collect_contexts(context):
            if context.context_type == context_type:
                result.append(context)
            for child in context.children:
                collect_contexts(child)
        
        collect_contexts(self.root_context)
        return result
    
    def get_context_path(self) -> List[str]:
        """获取当前上下文路径"""
        path = []
        for context in self.context_stack:
            path.append(f"{context.context_type.value}:{context.name}")
        return path
    
    def __str__(self):
        """字符串表示"""
        return f"ContextManager(current={self.current_context.context_type.value}:{self.current_context.name}, depth={len(self.context_stack)})"