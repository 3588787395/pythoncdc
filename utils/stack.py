"""
工具模块
包含FastStack等辅助类
"""

from typing import List, Optional, Dict, Set, Any
from collections import defaultdict


class FastStack:
    """快速栈类，模拟Python虚拟机栈"""
    
    def __init__(self, size: int = 20):
        self._stack: List[Optional['ASTNode']] = [None] * size
        self._ptr = -1
        # 增强：添加变量追踪和作用域信息
        self._variables: Dict[str, Dict[str, Any]] = {}
        self._variable_operations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._variable_scopes: Dict[str, List[Set[int]]] = defaultdict(list)
        self._scope_stack: List[Set[str]] = [set()]  # 栈化管理作用域
        self._variable_types: Dict[str, str] = {}  # 变量类型追踪
        self._variable_lifecycles: Dict[str, Dict[str, int]] = {}  # 变量生命周期追踪
        self._current_scope_id = 0  # 当前作用域ID
        self._scopes: Dict[int, Set[str]] = {0: set()}  # ID -> 变量集合的映射
        # 增强：添加栈历史管理（来自pycdc的stackhist_t）
        self._history: List['FastStack'] = []  # 栈历史记录
        self._debug_mode = False  # 调试模式
        
    def push_history(self) -> None:
        """保存当前栈状态到历史"""
        import copy
        history_stack = copy.deepcopy(self)
        self._history.append(history_stack)
        
    def pop_history(self) -> 'FastStack':
        """从历史中恢复栈状态"""
        if self._history:
            return self._history.pop()
        return FastStack()  # 返回空栈
        
    def clear_history(self) -> None:
        """清空栈历史"""
        self._history.clear()
        
    def has_history(self) -> bool:
        """检查是否有历史记录"""
        return len(self._history) > 0
    
    def push(self, node: 'ASTNode') -> None:
        """压入栈"""
        if self._ptr + 1 >= len(self._stack):
            self._stack.append(None)
        
        self._ptr += 1
        self._stack[self._ptr] = node
        
        # 增强：记录变量信息
        if node and hasattr(node, 'name'):
            self._track_variable(node.name, 'load')
        
        # 增强：变量生命周期追踪
        if node and hasattr(node, 'name'):
            self._track_variable_lifecycle(node.name)
    
    def pop(self) -> Optional['ASTNode']:
        """弹出栈顶"""
        if self._ptr < 0:
            return None
        
        node = self._stack[self._ptr]
        self._stack[self._ptr] = None
        self._ptr -= 1
        return node
    
    def top(self, i: int = 1) -> Optional['ASTNode']:
        """获取栈顶元素（i=1表示栈顶，i=2表示第二个）"""
        if i <= 0:
            return None
        
        idx = self._ptr + 1 - i
        if idx < 0 or idx > self._ptr:
            return None
        
        return self._stack[idx]
    
    def peek(self, depth: int = 0) -> Optional['ASTNode']:
        """获取栈中指定深度的元素（不弹出）"""
        idx = self._ptr - depth
        if idx < 0 or idx > self._ptr:
            return None
        
        return self._stack[idx]
    
    def empty(self) -> bool:
        """检查栈是否为空"""
        return self._ptr < 0
    
    def size(self) -> int:
        """获取栈大小"""
        return self._ptr + 1
    
    def copy(self) -> 'FastStack':
        """创建栈的浅拷贝
        
        参考C++ pycdc的stack_hist实现
        """
        import copy
        new_stack = FastStack(len(self._stack))
        new_stack._stack = self._stack[:self._ptr + 1] + [None] * (len(self._stack) - self._ptr - 1)
        new_stack._ptr = self._ptr
        # 复制变量追踪信息
        new_stack._variables = copy.deepcopy(self._variables)
        new_stack._variable_operations = copy.deepcopy(self._variable_operations)
        new_stack._variable_scopes = copy.deepcopy(self._variable_scopes)
        new_stack._scope_stack = copy.deepcopy(self._scope_stack)
        new_stack._variable_types = copy.deepcopy(self._variable_types)
        new_stack._variable_lifecycles = copy.deepcopy(self._variable_lifecycles)
        new_stack._current_scope_id = self._current_scope_id
        new_stack._scopes = copy.deepcopy(self._scopes)
        return new_stack
    
    def clear(self) -> None:
        """清空栈"""
        self._stack = [None] * len(self._stack)
        self._ptr = -1
    
    # 增强：变量追踪方法
    def track_variable(self, name: str, operation: str, offset: int = -1, node_type: str = None) -> None:
        """跟踪变量的加载和存储"""
        if offset == -1:
            offset = self._ptr
        
        # 初始化变量记录（如果不存在）
        if name not in self._variables:
            self._variables[name] = {'load': 0, 'store': 0}
            self._variable_operations[name] = []
            self._variable_scopes[name] = []
            self._variable_lifecycles[name] = {'created': -1, 'last_used': -1, 'destroyed': -1}
        
        # 记录操作类型
        self._variables[name][operation] = self._variables[name].get(operation, 0) + 1
        
        # 记录操作偏移和节点类型
        self._variable_operations[name].append({
            'operation': operation,
            'offset': offset,
            'node_type': node_type
        })
        
        # 记录作用域信息
        if self._scope_stack:
            # 获取当前作用域
            current_scope = self._scope_stack[-1] if self._scope_stack else set()
            # 记录作用域信息
            self._variable_scopes[name].append(set(current_scope))
            
            # 记录节点类型
            if node_type:
                self._variable_types[name] = node_type
        
        # 更新生命周期信息
        if name not in self._variable_lifecycles:
            self._variable_lifecycles[name] = {'created': -1, 'last_used': -1, 'destroyed': -1}
        
        if operation == 'store':
            self._variable_lifecycles[name]['created'] = offset
        elif operation == 'load':
            self._variable_lifecycles[name]['last_used'] = offset
    
    def _track_variable(self, name: str, operation: str, node_type: str = None) -> None:
        """内部方法：跟踪变量的操作"""
        self.track_variable(name, operation, node_type=node_type)
    
    def _track_variable_lifecycle(self, name: str) -> None:
        """内部方法：跟踪变量的生命周期"""
        # 查找当前作用域中是否有此变量
        found = False
        for scope_set in self._scopes.values():
            if name in scope_set:
                found = True
                break
        
        # 如果变量不存在于当前作用域，创建新作用域或记录新变量
        if not found:
            # 如果是根作用域
            if self._current_scope_id == 0:
                self._scopes[0].add(name)
                # 记录变量创建
                if name not in self._variable_lifecycles:
                    self._variable_lifecycles[name] = {
                        'created': self._ptr,
                        'last_used': self._ptr,
                        'destroyed': -1
                    }
    
    def push_scope(self, new_scope: Set[str] = None) -> None:
        """压入新的作用域"""
        if new_scope is None:
            new_scope = set()
        
        # 增加作用域ID
        self._current_scope_id += 1
        # 创建新作用域
        self._scopes[self._current_scope_id] = set(new_scope)
        # 添加到作用域栈
        self._scope_stack.append(set(new_scope))
        
        # 记录作用域变更
        if self._debug_mode:
            print(f"进入新作用域: {self._current_scope_id}, 变量: {new_scope}")
    
    def pop_scope(self) -> Dict[str, Any]:
        """弹出当前作用域，返回作用域中的变量和其生命周期信息"""
        if len(self._scope_stack) > 1:
            # 弹出作用域
            popped_scope = self._scope_stack.pop()
            scope_id = self._current_scope_id
            
            # 获取作用域中的变量
            scope_vars = list(self._scopes.get(scope_id, set()))
            
            # 销毁作用域变量
            for var in scope_vars:
                # 记录变量销毁
                if var in self._variable_lifecycles:
                    self._variable_lifecycles[var]['destroyed'] = self._ptr
            
            # 减少作用域ID
            self._current_scope_id -= 1
            
            # 记录作用域变更
            if self._debug_mode:
                print(f"离开作用域: {scope_id}, 变量: {scope_vars}")
            
            # 返回作用域变量及其生命周期信息
            return {
                'scope_id': scope_id,
                'variables': scope_vars,
                'lifecycles': {var: self._variable_lifecycles.get(var, {}) for var in scope_vars}
            }
        else:
            # 根作用域不弹出
            return {'scope_id': 0, 'variables': [], 'lifecycles': {}}
    
    def get_variables(self) -> Dict[str, Dict[str, Any]]:
        """获取变量追踪信息"""
        return self._variables
    
    def get_variable_operations(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取变量的操作记录"""
        return self._variable_operations
    
    def get_variable_scopes(self) -> Dict[str, List[Set[int]]]:
        """获取变量的作用域信息"""
        return self._variable_scopes
    
    def get_variable_types(self) -> Dict[str, str]:
        """获取变量类型信息"""
        return self._variable_types
    
    def add_variable_scope(self, name: str, scope: str) -> None:
        """添加变量的作用域信息"""
        # 更新作用域信息
        if name in self._variables:
            self._variables[name]['scope'] = scope
        else:
            self._variables[name] = {'load': 0, 'store': 0, 'scope': scope}
        
        # 将作用域信息添加到变量生命周期中
        if name in self._variable_lifecycles:
            self._variable_lifecycles[name]['scope'] = scope
        
        # 记录到作用域栈
        if self._scope_stack and len(self._scope_stack) > 0:
            # 获取当前作用域
            current_scope = self._scope_stack[-1]
            # 添加变量到当前作用域
            current_scope.add(name)
    
    def get_variable_lifecycles(self) -> Dict[str, Dict[str, int]]:
        """获取变量生命周期信息"""
        return self._variable_lifecycles
    
    def get_current_scope(self) -> Set[str]:
        """获取当前作用域中的变量"""
        if self._scope_stack:
            return set(self._scope_stack[-1])
        else:
            return set()
    
    def peek_depth(self, depth: int) -> Optional['ASTNode']:
        """获取栈中指定深度的元素（不弹出）"""
        if depth > self._ptr:
            return None
        return self._stack[self._ptr - depth]
    
    def is_variable_alive(self, name: str) -> bool:
        """检查变量是否仍然存活"""
        if name not in self._variable_lifecycles:
            return False
        
        lifecycle = self._variable_lifecycles[name]
        # 如果变量已经销毁，则不存活
        if lifecycle['destroyed'] != -1 and lifecycle['destroyed'] <= self._ptr:
            return False
        
        return True
    
    def get_variable_definitions(self) -> List[Dict[str, Any]]:
        """获取所有变量定义信息"""
        definitions = []
        for var_name, operations in self._variable_operations.items():
            for op in operations:
                if op['operation'] == 'store':
                    definitions.append({
                        'name': var_name,
                        'offset': op['offset'],
                        'type': self._variable_types.get(var_name, 'unknown'),
                        'scope': self._variable_scopes.get(var_name, [])
                    })
        return definitions
    
    def get_variable_references(self) -> List[Dict[str, Any]]:
        """获取所有变量引用信息"""
        references = []
        for var_name, operations in self._variable_operations.items():
            for op in operations:
                if op['operation'] == 'load':
                    references.append({
                        'name': var_name,
                        'offset': op['offset'],
                        'type': self._variable_types.get(var_name, 'unknown'),
                        'scope': self._variable_scopes.get(var_name, [])
                    })
        return references
