"""
AST节点模块
包含所有AST节点类 - 性能优化版本
"""

from typing import List, Optional, Union, Any, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import threading

# 导入PycRef以支持PYC引用节点
from .pyc_stream import PycRef

# 导入性能优化模块
try:
    from .object_pool import create_ast_node, release_ast_node, get_ast_node_pool
    from .cache_system import get_performance_cache, performance_cache_decorator
    _PERFORMANCE_ENABLED = True
except ImportError:
    _PERFORMANCE_ENABLED = False


_MAX_COMPARE_DEPTH = 100


# 优化的节点创建函数
def create_optimized_ast_node(node_class: type, *args, **kwargs) -> 'ASTNode':
    """创建优化的AST节点（使用对象池）"""
    if _PERFORMANCE_ENABLED and hasattr(node_class, '__init__'):
        try:
            # 尝试使用对象池
            return create_ast_node(node_class, *args, **kwargs)
        except Exception:
            # 如果对象池失败，回退到普通创建
            return node_class(*args, **kwargs)
    else:
        # 如果性能优化未启用，使用普通创建
        return node_class(*args, **kwargs)


# 性能监控装饰器
def monitor_ast_creation(func):
    """监控AST节点创建的装饰器"""
    if not _PERFORMANCE_ENABLED:
        return func
    
    @performance_cache_decorator(max_size=500)
    def wrapper(*args, **kwargs):
        # 这里可以添加性能监控逻辑
        start_time = __import__('time').time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 可以在这里记录创建时间等统计信息
            pass
    return wrapper


# 常用节点类型缓存
_COMMON_NODES_CACHE = {}


_compare_depth = threading.local()


def _get_depth():
    return getattr(_compare_depth, 'depth', 0)


def _inc_depth():
    _compare_depth.depth = _get_depth() + 1
    return _get_depth()


def _dec_depth():
    current = _get_depth()
    if current > 0:
        _compare_depth.depth = current - 1
    return current


def _reset_depth():
    _compare_depth.depth = 0


def _check_depth():
    return _get_depth() < _MAX_COMPARE_DEPTH


class NodeType(Enum):
    """节点类型枚举"""
    NODE_INVALID = 0
    NODE_OBJECT = 1
    NODE_BINARY = 2
    NODE_UNARY = 3
    NODE_COMPARE = 4
    NODE_SUBSCRIPT = 5
    NODE_CALL = 6
    NODE_KEYWORD = 7
    NODE_FUNCTION = 8
    NODE_CLASS = 9
    NODE_ASSIGN = 10
    NODE_BLOCK = 11
    NODE_LOOP = 12
    NODE_JUMP = 13
    NODE_RETURN = 14
    NODE_YIELD = 15
    NODE_DELETE = 16
    NODE_PRINT = 17
    NODE_IMPORT = 18
    NODE_ASSERT = 19
    NODE_GLOBAL = 20
    NODE_NONLOCAL = 21
    NODE_STORE = 22
    NODE_LOAD = 23
    NODE_PARAM = 24
    NODE_FORMAT = 25
    NODE_ANN_ASSIGN = 26
    NODE_ANNOTATED_VAR = 27
    NODE_RAISE = 28
    NODE_TRY = 29
    NODE_EXCEPT = 30
    NODE_IF = 31
    NODE_DECORATOR_APP = 32
    NODE_WHILE = 33
    NODE_FOR = 34
    NODE_WITH = 35
    NODE_PASS = 36
    NODE_BREAK = 37
    NODE_CONTINUE = 38
    NODE_LIST = 39
    NODE_TUPLE = 40
    NODE_DICT = 41
    NODE_SET = 42
    NODE_SLICE = 43
    NODE_ATTRIBUTE = 44
    NODE_NAME = 45
    NODE_CONSTANT = 46
    NODE_EXPR = 47
    NODE_NODELIST = 48
    NODE_CHAINSTORE = 49
    NODE_COMPREHENSION = 50
    NODE_LAMBDA = 51
    NODE_LISTCOMP = 52
    NODE_SETCOMP = 53
    NODE_DICTCOMP = 54
    NODE_GENEXPR = 55
    NODE_CONDITIONALEXP = 56
    # Pattern matching nodes
    NODE_MATCH_CLASS = 57
    NODE_MATCH_MAPPING = 58
    NODE_MATCH_SEQUENCE = 59
    NODE_MATCH_KEYS = 60
    NODE_TERNARY = 61
    NODE_CONST_MAP = 62
    NODE_AWAITABLE = 63
    NODE_KW_NAMES_MAP = 64
    NODE_AUGASSIGN = 65
    NODE_LOAD_BUILD_CLASS = 66
    NODE_CHAIN_STORE = 67
    NODE_FORMATTED_VALUE = 68
    NODE_JOINED_STR = 69
    NODE_CONVERT = 70
    NODE_MATCH = 71
    NODE_LOCALS = 72


class ASTNode(ABC):
    """AST节点基类 - 性能优化版本"""
    
    # 使用__slots__优化内存使用和访问速度
    __slots__ = ('_type', '_processed', '_parent', '_line_number', '_node_id')
    
    def __init__(self, node_type: NodeType = NodeType.NODE_INVALID):
        self._type = node_type
        self._processed = False
        self._parent = None
        self._line_number = None
        self._node_id = str(uuid.uuid4())
    
    @property
    def type(self) -> NodeType:
        return self._type
    
    @property
    def node_id(self) -> str:
        return self._node_id
    
    @property
    def processed(self) -> bool:
        return self._processed
    
    @property
    def parent(self) -> Optional['ASTNode']:
        return self._parent
    
    @parent.setter
    def parent(self, value: Optional['ASTNode']):
        self._parent = value
    
    @property
    def line_number(self) -> Optional[int]:
        return self._line_number
    
    @line_number.setter
    def line_number(self, value: Optional[int]):
        self._line_number = value
    
    def set_processed(self) -> None:
        """标记为已处理"""
        self._processed = True
    
    def add_child(self, child: 'ASTNode') -> None:
        """添加子节点"""
        if hasattr(child, 'parent'):
            child.parent = self
    
    def to_code(self, indent_level=0):
        """生成Python代码的抽象方法"""
        # 基类返回空字符串，子类应覆盖此方法
        return ""


class ASTNodeList(ASTNode):
    """节点列表 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_nodes',)
    
    def __init__(self, nodes: List['ASTNode'] = None, node_type: NodeType = NodeType.NODE_NODELIST):
        super().__init__(node_type)
        self._nodes = nodes if nodes is not None else []
    
    def __iter__(self):
        """支持迭代"""
        return iter(self._nodes)
    
    def __len__(self):
        """支持len()函数"""
        return len(self._nodes)
    
    def __bool__(self):
        """支持bool()函数 - 始终返回True，表示对象存在"""
        return True
    
    @property
    def nodes(self) -> List['ASTNode']:
        return self._nodes
    
    def append(self, node: 'ASTNode') -> None:
        """添加节点"""
        self._nodes.append(node)
    
    def remove_first(self) -> None:
        """移除第一个节点"""
        if self._nodes:
            self._nodes.pop(0)
    
    def remove_last(self) -> None:
        """移除最后一个节点"""
        if self._nodes:
            self._nodes.pop()
    
    def init(self) -> None:
        """初始化节点列表"""
        pass
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        if not self._nodes:
            return ""
        
        lines = []
        for node in self._nodes:
            if hasattr(node, 'to_code'):
                node_code = node.to_code(indent_level)
            else:
                node_code = str(node)
            lines.append(node_code)
        
        return "\n".join(lines)


class ASTBlock(ASTNodeList):
    """代码块节点 - 性能优化版本
    
    参考C++ pycdc实现，支持块栈管理
    """
    
    # 添加__slots__优化
    __slots__ = ('_blk_type', '_end', '_inited')
    
    class BlockType(Enum):
        BLK_MAIN = 0
        BLK_IF = 1
        BLK_ELSE = 2
        BLK_ELIF = 3
        BLK_WHILE = 4
        BLK_FOR = 5
        BLK_TRY = 6
        BLK_EXCEPT = 7
        BLK_FINALLY = 8
        BLK_WITH = 9
        BLK_CONTAINER = 10  # 容器块，用于包裹其他块
    
    def __init__(self, nodes: List['ASTNode'] = None, blk_type: 'ASTBlock.BlockType' = None, end: int = 0, inited: bool = False):
        super().__init__(nodes, NodeType.NODE_BLOCK)
        self._blk_type = blk_type if blk_type is not None else ASTBlock.BlockType.BLK_MAIN
        self._end = end  # 块结束位置
        self._inited = inited  # 是否已初始化
    
    @property
    def end(self) -> int:
        """块结束位置"""
        return self._end
    
    @end.setter
    def end(self, value: int) -> None:
        self._end = value
    
    @property
    def inited(self) -> bool:
        """是否已初始化"""
        return self._inited
    
    @inited.setter
    def inited(self, value: bool) -> None:
        self._inited = value
    
    def emit(self, node: 'ASTNode') -> None:
        """发射节点到代码块"""
        try:
            # 🔧 关键修复：检查是否是函数处理期间
            from parsers.enhanced_ast_builder import EnhancedASTBuilder
            
            # 方法1：检查静态标记
            if hasattr(EnhancedASTBuilder, '_current_function_nodes') and EnhancedASTBuilder._current_function_nodes is not None:
                EnhancedASTBuilder._current_function_nodes.append(node)
            else:
                # 方法2：检查block ID匹配
                from parsers.enhanced_ast_builder import EnhancedASTBuilder
                if hasattr(EnhancedASTBuilder, '_function_block_ids') and EnhancedASTBuilder._function_block_ids and id(self) in EnhancedASTBuilder._function_block_ids:
                    if EnhancedASTBuilder._current_function_nodes:
                        EnhancedASTBuilder._current_function_nodes.append(node)
                else:
                    # 普通发射到当前block
                    self.append(node)
                
        except Exception as e:
            print(f"ASTBlock.emit - 发射失败: {e}")
            import traceback
            traceback.print_exc()
    
    def init(self):
        """初始化块"""
        pass
    
    @property
    def blk_type(self) -> 'ASTBlock.BlockType':
        return self._blk_type
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        if not self._nodes:
            return "    " * indent_level + "pass"
        
        lines = []
        prev_was_method = False
        for node in self._nodes:
            # 🔧 修复：在类的方法之间添加空行
            if prev_was_method and hasattr(node, 'to_code'):
                node_code = node.to_code(indent_level)
                # 检查是否是方法定义（以 "def " 开头）
                if node_code.strip().startswith('def '):
                    lines.append("")  # 添加空行
            
            # 🔧 修复：特殊处理装饰器应用节点，给它们零缩进
            if hasattr(node, '_node_type') and node._node_type == NodeType.NODE_DECORATOR_APP:
                # 装饰器应用节点使用零缩进
                original_node_code = node.to_code(0)
                node_code = original_node_code  # 不添加缩进
            elif hasattr(node, 'to_code'):
                node_code = node.to_code(indent_level)
            else:
                # 为字符串节点添加缩进
                node_str = str(node)
                if node_str.strip():
                    node_code = "    " * indent_level + node_str
                else:
                    node_code = ""
            lines.append(node_code)
            
            # 标记是否是方法
            prev_was_method = node_code.strip().startswith('def ')
        
        # 过滤空行并连接，但保留方法之间的空行（空字符串）
        result_lines = []
        for i, line in enumerate(lines):
            if line.strip() or line == "":  # 保留非空行和显式的空行
                result_lines.append(line)
        
        # 移除开头和结尾的空行
        while result_lines and result_lines[0] == "":
            result_lines.pop(0)
        while result_lines and result_lines[-1] == "":
            result_lines.pop()
        
        result = "\n".join(result_lines)
        return result


class ASTChainStore(ASTNodeList):
    """链式存储节点"""
    
    def __init__(self, nodes: List['ASTNode'], src: 'ASTNode'):
        super().__init__(nodes, NodeType.NODE_CHAINSTORE)
        self._src = src
    
    @property
    def src(self) -> 'ASTNode':
        return self._src


class ASTStore(ASTNode):
    """存储节点"""
    
    def __init__(self, dest: 'ASTNode' = None, src: 'ASTNode' = None, value: 'ASTNode' = None):
        super().__init__(NodeType.NODE_STORE)
        self._dest = dest
        self._src = src
        self._value = value if value is not None else src
    
    @property
    def dest(self) -> 'ASTNode':
        return self._dest
    
    @dest.setter
    def dest(self, value: 'ASTNode'):
        self._dest = value
    
    @property
    def src(self) -> 'ASTNode':
        return self._src
    
    @src.setter
    def src(self, value: 'ASTNode'):
        self._src = value
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成赋值代码"""
        indent = "    " * indent_level
        # 获取目标代码
        if hasattr(self, '_dest') and self._dest is not None:
            target_code = self._dest.to_code() if hasattr(self._dest, 'to_code') else str(self._dest)
        elif hasattr(self, '_target') and self._target is not None:
            target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        else:
            target_code = "unknown"
        
        # 获取值代码
        value = getattr(self, '_value', None) or getattr(self, '_src', None)
        if value is not None:
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
        else:
            value_code = "None"
        
        return f"{indent}{target_code} = {value_code}"
    
    @value.setter
    def value(self, value: 'ASTNode'):
        self._value = value
    
    def __eq__(self, other):
        """比较两个存储节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTStore):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._dest == other._dest and 
                    self._src == other._src and 
                    self._value == other._value)
        finally:
            _dec_depth()


class ASTObject(ASTNode):
    """对象节点"""
    
    def __init__(self, obj):
        super().__init__(NodeType.NODE_OBJECT)
        self._obj = obj
        # 添加value属性别名，保持向后兼容
        self._value = obj
    
    @property
    def object(self):
        return self._obj
    
    @property
    def value(self):
        """value属性别名，保持向后兼容"""
        # 处理 PycString 对象，返回实际的字符串值
        from core.pyc_objects import PycString, PycNumeric, PycObject
        if isinstance(self._obj, PycString):
            return self._obj.value
        elif isinstance(self._obj, PycNumeric):
            return self._obj.value
        elif isinstance(self._obj, PycObject):
            # 处理布尔值类型
            if hasattr(self._obj, '_type'):
                if self._obj._type == PycObject.TYPE_TRUE:
                    return True
                elif self._obj._type == PycObject.TYPE_FALSE:
                    return False
                elif self._obj._type == PycObject.TYPE_NONE:
                    return None
        return self._obj
    
    def __repr__(self):
        """返回对象的字符串表示"""
        from core.pyc_objects import PycString, PycNumeric, PycObject
        
        if self._obj is None:
            return "None"
        elif isinstance(self._obj, str):
            return repr(self._obj)
        elif isinstance(self._obj, bytes):
            return repr(self._obj.decode('latin-1', errors='replace'))
        elif isinstance(self._obj, (int, float, bool)):
            return str(self._obj)
        elif isinstance(self._obj, tuple):
            items = []
            for item in self._obj:
                items.append(repr(item) if isinstance(item, str) else str(item))
            return "(" + ", ".join(items) + ")"
        elif isinstance(self._obj, list):
            items = []
            for item in self._obj:
                items.append(repr(item) if isinstance(item, str) else str(item))
            return "[" + ", ".join(items) + "]"
        elif isinstance(self._obj, PycString):
            # 🔧 修复：正确处理PycString对象，返回实际的字符串值
            return repr(self._obj.value)
        elif isinstance(self._obj, PycNumeric):
            # 🔧 修复：正确处理PycNumeric对象，返回实际的数值
            return str(self._obj.value)
        elif isinstance(self._obj, PycObject):
            # 🔧 修复：处理布尔值和None类型
            if hasattr(self._obj, '_type'):
                if self._obj._type == PycObject.TYPE_TRUE:
                    return "True"
                elif self._obj._type == PycObject.TYPE_FALSE:
                    return "False"
                elif self._obj._type == PycObject.TYPE_NONE:
                    return "None"
            # 对于其他PycObject对象，尝试获取value属性
            if hasattr(self._obj, 'value') and self._obj.value is not None:
                return str(self._obj.value)
            else:
                return "None"
        else:
            return str(self._obj)
    
    def __eq__(self, other):
        """比较两个对象节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTObject):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return self._obj == other._obj
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成对象节点的哈希值"""
        return hash((super().__hash__(), self._obj))
    
    def to_code(self, indent_level=0):
        """生成对象代码"""
        if self._obj is None:
            return "None"
        elif isinstance(self._obj, str):
            return repr(self._obj)
        elif isinstance(self._obj, (int, float, bool)):
            return str(self._obj)
        else:
            return str(self._obj)
    
    def to_code(self, indent_level=0):
        """生成对象代码"""
        if self._obj is None:
            return "None"
        elif isinstance(self._obj, str):
            return repr(self._obj)
        elif isinstance(self._obj, (int, float, bool)):
            return str(self._obj)
        elif isinstance(self._obj, bytes):
            return repr(self._obj.decode('latin-1', errors='replace'))
        else:
            # 处理 PycString 对象
            from core.pyc_objects import PycString, PycNumeric, PycObject
            if isinstance(self._obj, PycString):
                return repr(self._obj.value)
            elif isinstance(self._obj, PycNumeric):
                return str(self._obj.value)
            elif isinstance(self._obj, PycObject):
                # 🔧 修复：对于PycObject对象，尝试获取value属性
                if hasattr(self._obj, 'value') and self._obj.value is not None:
                    return str(self._obj.value)
                else:
                    return "None"
            return str(self._obj)


class ASTUnary(ASTNode):
    """一元操作节点"""
    
    class UnOp(Enum):
        UN_POSITIVE = 0
        UN_NEGATIVE = 1
        UN_INVERT = 2
        UN_NOT = 3
    
    def __init__(self, operand: 'ASTNode', op: int):
        super().__init__(NodeType.NODE_UNARY)
        self._operand = operand
        self._op = op
    
    @property
    def operand(self) -> 'ASTNode':
        return self._operand
    
    @property
    def op(self) -> int:
        return self._op
    
    def __eq__(self, other):
        """比较两个一元操作节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTUnary):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return self._operand == other._operand and self._op == other._op
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成一元操作节点的哈希值"""
        return hash((super().__hash__(), self._operand, self._op))
    
    def to_code(self, indent_level=0):
        """生成一元操作代码"""
        operand_code = self._operand.to_code() if hasattr(self._operand, 'to_code') else str(self._operand)
        
        # 操作符映射
        op_map = {
            self.UnOp.UN_POSITIVE.value: "+",
            self.UnOp.UN_NEGATIVE.value: "-",
            self.UnOp.UN_INVERT.value: "~",
            self.UnOp.UN_NOT.value: "not ",
        }
        
        op_str = op_map.get(self._op, f"#{self._op}")
        return f"{op_str}{operand_code}"


class ASTBinary(ASTNode):
    """二元操作节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_left', '_right', '_op')
    
    class BinOp(Enum):
        BIN_ATTR = 0
        BIN_POWER = 1
        BIN_MULTIPLY = 2
        BIN_DIVIDE = 3
        BIN_FLOOR_DIVIDE = 4
        BIN_MODULO = 5
        BIN_ADD = 6
        BIN_SUBTRACT = 7
        BIN_LSHIFT = 8
        BIN_RSHIFT = 9
        BIN_AND = 10
        BIN_XOR = 11
        BIN_OR = 12
        BIN_LOG_AND = 13
        BIN_LOG_OR = 14
        BIN_MAT_MULTIPLY = 15
        BIN_IP_ADD = 16
        BIN_IP_SUBTRACT = 17
        BIN_IP_MULTIPLY = 18
        BIN_IP_DIVIDE = 19
        BIN_IP_MODULO = 20
        BIN_IP_POWER = 21
        BIN_IP_LSHIFT = 22
        BIN_IP_RSHIFT = 23
        BIN_IP_AND = 24
        BIN_IP_XOR = 25
        BIN_IP_OR = 26
        BIN_IP_MAT_MULTIPLY = 27
        BIN_IP_FLOORDIV = 28
        BIN_INVALID = 29
    
    def __init__(self, left: 'ASTNode', right: 'ASTNode', op: int,
                 node_type: NodeType = NodeType.NODE_BINARY):
        super().__init__(node_type)
        self._left = left
        self._right = right
        # 如果op是枚举类型，转换为值
        if isinstance(op, self.BinOp):
            self._op = op.value
        else:
            self._op = op
    
    @property
    def left(self) -> 'ASTNode':
        return self._left
    
    @left.setter
    def left(self, value: 'ASTNode'):
        self._left = value
    
    @property
    def right(self) -> 'ASTNode':
        return self._right
    
    @right.setter
    def right(self, value: 'ASTNode'):
        self._right = value
    
    @property
    def op(self) -> int:
        return self._op
    
    def __eq__(self, other):
        """比较两个二元操作节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTBinary):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._left == other._left and 
                    self._right == other._right and 
                    self._op == other._op)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成二元操作节点的哈希值"""
        return hash((super().__hash__(), self._left, self._right, self._op))
    
    def to_code(self, indent_level=0):
        """生成二元操作代码"""
        left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        
        # 操作符映射
        op_map = {
            self.BinOp.BIN_ADD.value: "+",
            self.BinOp.BIN_SUBTRACT.value: "-",
            self.BinOp.BIN_MULTIPLY.value: "*",
            self.BinOp.BIN_DIVIDE.value: "/",
            self.BinOp.BIN_FLOOR_DIVIDE.value: "//",
            self.BinOp.BIN_MODULO.value: "%",
            self.BinOp.BIN_POWER.value: "**",
            self.BinOp.BIN_AND.value: "&",
            self.BinOp.BIN_OR.value: "|",
            self.BinOp.BIN_XOR.value: "^",
            self.BinOp.BIN_LSHIFT.value: "<<",
            self.BinOp.BIN_RSHIFT.value: ">>",
            self.BinOp.BIN_MAT_MULTIPLY.value: "@",
            self.BinOp.BIN_ATTR.value: ".",
            self.BinOp.BIN_LOG_AND.value: "and",
            self.BinOp.BIN_LOG_OR.value: "or",
        }
        
        op_str = op_map.get(self._op, f"#{self._op}")
        
        # 处理特殊操作符
        if self._op == self.BinOp.BIN_ATTR.value:
            return f"{left_code}.{right_code}"
        else:
            return f"{left_code} {op_str} {right_code}"


class ASTCompare(ASTBinary):
    """比较操作节点"""
    
    class CompareOp(Enum):
        CMP_LESS = 0
        CMP_LESS_EQUAL = 1
        CMP_EQUAL = 2
        CMP_NOT_EQUAL = 3
        CMP_GREATER = 4
        CMP_GREATER_EQUAL = 5
        CMP_IN = 6
        CMP_NOT_IN = 7
        CMP_IS = 8
        CMP_IS_NOT = 9
        CMP_EXCEPTION = 10
        CMP_BAD = 11
    
    def __init__(self, left: 'ASTNode', comparators: Union['ASTNode', List['ASTNode']] = None, ops: Union[int, List[int]] = None):
        # 处理不同的输入格式
        if isinstance(comparators, list):
            right = comparators[0] if comparators and len(comparators) > 0 else None
            self._comparators = comparators
        else:
            right = comparators
            self._comparators = [comparators] if comparators else []
        
        if isinstance(ops, list):
            op = ops[0] if ops and len(ops) > 0 else 0
            self._ops = ops
        else:
            op = ops if ops is not None else 0
            self._ops = [ops] if ops is not None else []
        
        super().__init__(left, right, op, NodeType.NODE_COMPARE)
    
    @property
    def comparators(self) -> List['ASTNode']:
        return self._comparators
    
    @property
    def ops(self) -> List[int]:
        return self._ops
    
    def op_str(self) -> str:
        """获取比较操作符字符串"""
        op_strings = [
            "<", "<=", "==", "!=", ">", ">=",
            "in", "not in", "is", "is not", "<exception>", "<bad>"
        ]
        return op_strings[self._op]
    
    def to_code(self, indent_level=0):
        """生成比较表达式代码"""
        # 获取左侧表达式
        left_str = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        
        # 处理单个比较（最常见的情况）
        if len(self._comparators) == 1 and len(self._ops) == 1:
            comparator = self._comparators[0]
            op_str = self.op_str()
            comp_str = comparator.to_code() if hasattr(comparator, 'to_code') else str(comparator)
            return f"{left_str} {op_str} {comp_str}"
        
        # 处理链式比较：a < b < c
        if len(self._comparators) >= 1 and len(self._ops) >= 1:
            parts = [left_str]
            for i, (comparator, op) in enumerate(zip(self._comparators, self._ops)):
                # 获取操作符字符串
                op_strings = [
                    "<", "<=", "==", "!=", ">", ">=",
                    "in", "not in", "is", "is not", "<exception>", "<bad>"
                ]
                op_str = op_strings[op] if op < len(op_strings) else "<unknown>"
                
                comp_str = comparator.to_code() if hasattr(comparator, 'to_code') else str(comparator)
                parts.append(f"{op_str} {comp_str}")
            
            return " ".join(parts)
        
        # 退化为简单比较
        return f"{left_str} {self.op_str()}"


class ASTSlice(ASTBinary):
    """切片操作节点"""
    
    def __init__(self, lower: 'ASTNode', upper: 'ASTNode', step: 'ASTNode'):
        super().__init__(lower, upper, 0, NodeType.NODE_SLICE)
        self._step = step
    
    @property
    def step(self) -> 'ASTNode':
        return self._step
    
    def to_code(self, indent_level=0):
        """生成切片表达式代码"""
        lower_str = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        upper_str = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        step_str = self._step.to_code() if hasattr(self._step, 'to_code') else str(self._step) if self._step else None
        
        if step_str and step_str != "None":
            return f"{lower_str}[{lower_str}:{upper_str}:{step_str}]"
        else:
            return f"{lower_str}[{lower_str}:{upper_str}]"


class ASTSliceExpr(ASTNode):
    """切片表达式节点 - 用于表示切片操作如 [1:3]"""
    
    def __init__(self, lower: Optional['ASTNode'], upper: Optional['ASTNode'], step: Optional['ASTNode'] = None):
        super().__init__(NodeType.NODE_OBJECT)
        self._lower = lower
        self._upper = upper
        self._step = step
    
    @property
    def lower(self) -> Optional['ASTNode']:
        return self._lower
    
    @property
    def upper(self) -> Optional['ASTNode']:
        return self._upper
    
    @property
    def step(self) -> Optional['ASTNode']:
        return self._step
    
    def to_code(self, indent_level=0) -> str:
        """生成切片表达式代码"""
        lower_str = ""
        if self._lower is not None:
            if hasattr(self._lower, 'value') and self._lower.value is not None:
                lower_str = str(self._lower.value)
        
        upper_str = ""
        if self._upper is not None:
            if hasattr(self._upper, 'value') and self._upper.value is not None:
                upper_str = str(self._upper.value)
        
        step_str = None
        if self._step is not None:
            if hasattr(self._step, 'value') and self._step.value is not None:
                step_str = str(self._step.value)
        
        if step_str:
            return f"{lower_str}:{upper_str}:{step_str}"
        else:
            return f"{lower_str}:{upper_str}"


class ASTSubscript(ASTNode):
    """下标操作节点"""
    
    def __init__(self, container: 'ASTNode', slice_node: 'ASTNode'):
        super().__init__(NodeType.NODE_SUBSCRIPT)
        self._container = container
        self._slice = slice_node
    
    @property
    def container(self) -> 'ASTNode':
        return self._container
    
    @property
    def slice(self) -> 'ASTNode':
        return self._slice
    
    def to_code(self, indent_level=0):
        """生成下标操作代码"""
        container_str = self._container.to_code() if hasattr(self._container, 'to_code') else str(self._container)
        slice_str = self._slice.to_code() if hasattr(self._slice, 'to_code') else str(self._slice)
        return f"{container_str}[{slice_str}]"


class ASTCall(ASTNode):
    """函数调用节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_func', '_pparams', '_kwparams', '_var', '_kw')
    
    def __init__(self, func: 'ASTNode', pparams: List['ASTNode'] = None, 
                 kwparams: List['ASTKeyword'] = None, var: 'ASTNode' = None, kw: 'ASTNode' = None):
        super().__init__(NodeType.NODE_CALL)
        self._func = func
        self._pparams = pparams if pparams is not None else []
        self._kwparams = kwparams if kwparams is not None else []
        self._var = var
        self._kw = kw
    
    @property
    def func(self) -> 'ASTNode':
        return self._func
    
    @property
    def pparams(self) -> List['ASTNode']:
        return self._pparams
    
    @pparams.setter
    def pparams(self, value: List['ASTNode']):
        self._pparams = value if value is not None else []
    
    @property
    def kwparams(self) -> List['ASTKeyword']:
        return self._kwparams
    
    @property
    def var(self) -> 'ASTNode':
        return self._var
    
    @property
    def kw(self) -> 'ASTNode':
        return self._kw
    
    def to_code(self, indent_level=0):
        """生成函数调用代码"""
        # [DEBUG] 关键修复：处理推导式函数调用
        # 如果func是推导式函数（函数名以 < 开头和 > 结尾），转换为推导式表达式
        if isinstance(self._func, ASTFunctionDef):
            func_name = self._func.name if hasattr(self._func, 'name') else ''
            # 检查是否是推导式函数名（包括<anonymous>，因为推导式函数可能被命名为<anonymous>）
            is_comp_func = func_name.startswith('<') and func_name.endswith('>')
            
            if is_comp_func:
                # 推导式函数，转换为推导式表达式
                # 获取迭代对象（第一个参数）
                iterable = None
                if self._pparams:
                    iterable = self._pparams[0]
                
                # 获取迭代对象字符串
                iterable_str = iterable.to_code() if hasattr(iterable, 'to_code') else str(iterable)
                
                # 从函数体中提取表达式和变量
                body = self._func.body if hasattr(self._func, 'body') else None
                expr_str = 'i'  # 默认表达式
                var_name = 'i'  # 默认变量名
                
                if body and hasattr(body, 'nodes') and body.nodes:
                    # 尝试从函数体中提取表达式
                    expr_node = body.nodes[0] if body.nodes else None
                    if expr_node and hasattr(expr_node, 'to_code'):
                        expr_code = expr_node.to_code()
                        # 如果是return语句，提取返回值
                        if expr_code.startswith('return '):
                            expr_str = expr_code[7:]  # 去掉'return '
                        else:
                            expr_str = expr_code
                
                # 获取迭代变量名（从函数参数）
                if hasattr(self._func, 'args') and self._func.args:
                    var_name = str(self._func.args[0]) if self._func.args else 'i'
                
                # 根据函数名确定推导式类型
                # 注意：<anonymous>也可能是列表推导式，需要根据代码特征判断
                if func_name == '<listcomp>' or func_name == '<anonymous>':
                    # 列表推导式: [expr for var in iterable]
                    return f"[{expr_str} for {var_name} in {iterable_str}]"
                elif func_name == '<setcomp>':
                    # 集合推导式
                    return f"{{{expr_str} for {var_name} in {iterable_str}}}"
                elif func_name == '<dictcomp>':
                    # 字典推导式
                    return f"{{{expr_str}: {expr_str} for {var_name} in {iterable_str}}}"
                elif func_name == '<genexpr>':
                    # 生成器表达式
                    return f"({expr_str} for {var_name} in {iterable_str})"
        
        # 获取函数名
        func_str = self._func.to_code() if hasattr(self._func, 'to_code') else str(self._func)
        
        # 处理参数
        args = []
        
        # 位置参数
        for arg in self._pparams:
            arg_str = arg.to_code() if hasattr(arg, 'to_code') else str(arg)
            args.append(arg_str)
        
        # 关键字参数
        for kwarg in self._kwparams:
            if hasattr(kwarg, 'to_code'):
                kw_str = kwarg.to_code()
            else:
                kw_str = str(kwarg)
            args.append(kw_str)
        
        # *args参数
        if self._var:
            var_str = self._var.to_code() if hasattr(self._var, 'to_code') else str(self._var)
            args.append(f"*{var_str}")
        
        # **kwargs参数
        if self._kw:
            kw_str = self._kw.to_code() if hasattr(self._kw, 'to_code') else str(self._kw)
            args.append(f"**{kw_str}")
        
        return f"{func_str}({', '.join(args)})"


class ASTKeyword(ASTNode):
    """关键字参数节点"""
    
    def __init__(self, name: str, value: 'ASTNode'):
        super().__init__(NodeType.NODE_KEYWORD)
        self._name = name
        self._value = value
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成关键字参数代码"""
        value_str = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        return f"{self._name}={value_str}"


class ASTList(ASTNode):
    """列表节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_items',)
    
    def __init__(self, items: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_LIST)
        self._items = items if items is not None else []
    
    @property
    def items(self) -> List['ASTNode']:
        return self._items
    
    @property
    def elts(self) -> List['ASTNode']:
        """兼容性属性，兼容code_generator的期望"""
        return self._items
    
    def to_code(self, indent_level=0):
        """生成列表代码"""
        if not self._items:
            return "[]"
        
        item_strs = []
        for item in self._items:
            item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
            item_strs.append(item_str)
        
        return f"[{', '.join(item_strs)}]"


class ASTTuple(ASTNode):
    """元组节点"""
    
    def __init__(self, items: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_TUPLE)
        self._items = items if items is not None else []
    
    @property
    def items(self) -> List['ASTNode']:
        return self._items
    
    @property
    def elts(self) -> List['ASTNode']:
        """兼容性属性，兼容code_generator的期望"""
        return self._items
    
    def to_code(self, indent_level=0):
        """生成元组代码"""
        if not self._items:
            return "()"
        
        if len(self._items) == 1:
            # 单元素元组需要逗号
            item = self._items[0]
            item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
            return f"({item_str},)"
        
        item_strs = []
        for item in self._items:
            item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
            item_strs.append(item_str)
        
        return f"({', '.join(item_strs)})"


class ASTDict(ASTNode):
    """字典节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_keys', '_values')
    
    def __init__(self, keys: List['ASTNode'] = None, values: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_DICT)
        self._keys = keys if keys is not None else []
        self._values = values if values is not None else []
    
    @property
    def keys(self) -> List['ASTNode']:
        return self._keys
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    @property
    def elts(self) -> List['ASTNode']:
        """兼容性属性，兼容code_generator的期望"""
        return self._keys
    
    def to_code(self, indent_level=0):
        """生成字典代码"""
        if not self._keys or not self._values:
            return "{}"
        
        items = []
        for key, value in zip(self._keys, self._values):
            key_code = key.to_code() if hasattr(key, 'to_code') else str(key)
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
            items.append(f"{key_code}: {value_code}")
        
        return "{" + ", ".join(items) + "}"


class ASTSet(ASTNode):
    """集合节点"""
    
    def __init__(self, items: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_SET)
        self._items = items if items is not None else []
    
    @property
    def items(self) -> List['ASTNode']:
        return self._items
    
    def to_code(self, indent_level=0):
        """生成集合代码"""
        if not self._items:
            return "set()"
        
        item_strs = []
        for item in self._items:
            item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
            item_strs.append(item_str)
        
        return "{" + ", ".join(item_strs) + "}"


class ASTConstant(ASTNode):
    """常量节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_value',)
    
    def __init__(self, value: Any):
        super().__init__(NodeType.NODE_OBJECT)
        self._value = value
    
    @property
    def value(self) -> Any:
        return self._value
    
    @property
    def constant(self) -> Any:
        return self._value
    
    def to_code(self, indent_level=0):
        """生成常量代码"""
        if isinstance(self._value, str):
            return repr(self._value)
        elif isinstance(self._value, (int, float, complex)):
            return str(self._value)
        elif self._value is None:
            return "None"
        elif self._value is True:
            return "True"
        elif self._value is False:
            return "False"
        else:
            return repr(self._value)
    
    def __str__(self) -> str:
        """字符串表示 - 特别处理代码对象"""
        # 检查是否是代码对象
        if hasattr(self._value, 'co_name'):
            # 这是一个代码对象，尝试提取函数名
            if hasattr(self._value, 'co_name') and self._value.co_name:
                return f"<code '{self._value.co_name}'>"
            else:
                return "<code object>"
        elif hasattr(self._value, '_name'):
            # PycCode对象
            return f"<code '{self._value._name}'>"
        elif 'PycObject' in str(type(self._value)):
            # 其他PycObject类型
            return str(self._value)
        else:
            # 正常值使用repr
            return repr(self._value)
    
    def __eq__(self, other):
        """比较两个常量节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTConstant):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        return self._value == other._value
    
    def __hash__(self):
        """生成常量节点的哈希值"""
        return hash((super().__hash__(), self._value))


class ASTDecoratorApplication(ASTNode):
    """装饰器应用节点"""
    
    def __init__(self, decorator_name: str, function: 'ASTNode' = None, args: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_DECORATOR_APP)
        self._decorator_name = decorator_name
        self._function = function
        self._args = args if args is not None else []
    
    @property
    def decorator_name(self) -> str:
        return self._decorator_name
    
    @property
    def function(self) -> 'ASTNode':
        return self._function
    
    @function.setter
    def function(self, value: 'ASTNode'):
        self._function = value
    
    @property
    def args(self) -> List['ASTNode']:
        return self._args
    
    def __eq__(self, other):
        if not isinstance(other, ASTDecoratorApplication):
            return False
        return (self._decorator_name == other._decorator_name and
                self._function == other._function and
                self._args == other._args)
    
    def __hash__(self):
        return hash((self._decorator_name, self._function, tuple(self._args)))
    
    def __repr__(self):
        return f"ASTDecoratorApplication({self._decorator_name}, {self._function})"
    
    def to_smt(self):
        """转换为SMT格式"""
        func_smt = self._function.to_smt() if self._function else "None"
        args_smt = ", ".join(arg.to_smt() for arg in self._args)
        return f"(decorator-app {self._decorator_name} {func_smt} [{args_smt}])"
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成装饰器语法
        decorator_syntax = f"@{self._decorator_name}"
        
        if self._function and hasattr(self._function, 'to_code'):
            # 获取函数的代码并添加装饰器
            func_code = self._function.to_code(indent_level)
            
            # 在函数定义前添加装饰器
            if func_code.startswith(indent + "def "):
                # 找到函数定义的开始
                lines = func_code.split('\n')
                if lines:
                    lines[0] = decorator_syntax + "\n" + lines[0]
                    return '\n'.join(lines)
            elif func_code.startswith("def "):
                # 顶级函数定义
                lines = func_code.split('\n')
                if lines:
                    lines[0] = decorator_syntax + "\n" + lines[0]
                    return '\n'.join(lines)
            
            # 默认情况：直接拼接
            return decorator_syntax + "\n" + func_code
        else:
            return decorator_syntax


class ASTName(ASTNode):
    """名称节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_name', 'module_name')
    
    def __init__(self, name, module_name=None):
        super().__init__(NodeType.NODE_NAME)
        self._name = name
        self.module_name = module_name  # 用于from ... import ...语句
    
    @property
    def name(self):
        return self._name
    
    def __str__(self) -> str:
        if hasattr(self._name, '_value'):
            return str(self._name._value)
        return str(self._name)
    
    def to_code(self, indent_level=0):
        """生成名称代码"""
        if hasattr(self._name, '_value'):
            return str(self._name._value)
        return str(self._name)
    
    def __eq__(self, other):
        """比较两个名称节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTName):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        return self._name == other._name
    
    def __hash__(self):
        """生成名称节点的哈希值"""
        return hash((super().__hash__(), self._name))


class ASTModule(ASTNode):
    """模块节点"""
    
    def __init__(self, body: 'ASTNode' = None, type_ignores: List[Any] = None):
        super().__init__(NodeType.NODE_INVALID)
        self._body = body if body is not None else ASTNodeList()
        self._type_ignores = type_ignores if type_ignores is not None else []
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @property
    def type_ignores(self) -> List[Any]:
        return self._type_ignores
    
    def to_code(self, indent_level=0):
        """生成模块代码"""
        if hasattr(self._body, 'to_code'):
            body_code = self._body.to_code(indent_level)
        else:
            body_code = str(self._body)
        return body_code


class ASTFunctionDef(ASTNode):
    """函数定义节点"""
    
    def __init__(self, name: str, args: List['ASTNode'] = None, 
                 body: 'ASTNode' = None, returns: 'ASTNode' = None, 
                 decorators: List['ASTNode'] = None, code_obj: 'PycCode' = None):
        super().__init__(NodeType.NODE_FUNCTION)
        self._name = name
        self._args = args if args is not None else []
        self._body = body if body is not None else ASTNodeList()
        self._returns = returns
        self._decorators = decorators if decorators is not None else []
        self._code_obj = code_obj  # 存储函数代码对象，用于生成函数体
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def args(self) -> List['ASTNode']:
        return self._args
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @property
    def returns(self) -> 'ASTNode':
        return self._returns
    
    @property
    def decorators(self) -> List['ASTNode']:
        return self._decorators
    
    @property
    def code_obj(self) -> 'PycCode':
        """获取函数代码对象"""
        return self._code_obj
    
    def __eq__(self, other):
        """比较两个函数定义节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTFunctionDef):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._name == other._name and 
                    self._args == other._args and
                    self._body == other._body and
                    self._returns == other._returns and
                    self._decorators == other._decorators)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成函数定义节点的哈希值"""
        return hash((super().__hash__(), self._name, tuple(self._args), 
                    self._body, self._returns, tuple(self._decorators)))
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成装饰器
        decorator_lines = []
        for decorator in self._decorators:
            if isinstance(decorator, str):
                decorator_lines.append(f"@{decorator}")
            elif hasattr(decorator, 'decorator_name'):
                decorator_lines.append(f"@{decorator.decorator_name}")
            elif hasattr(decorator, 'to_code'):
                decorator_lines.append(decorator.to_code(indent_level))
            else:
                decorator_lines.append(f"@{decorator}")
        
        decorator_str = "\n".join(decorator_lines)
        if decorator_str:
            decorator_str += "\n"
        
        # 生成函数签名
        args_str = ", ".join(str(arg) for arg in self._args)
        
        # 生成函数体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        elif isinstance(self._body, str):
            # 简单的字符串直接使用
            body_str = self._body
        else:
            # 如果没有函数体，生成pass语句
            body_str = "    " * (indent_level + 1) + "pass"
        
        return f"{decorator_str}{indent}def {self._name}({args_str}):\n{body_str}"


class ASTClassDef(ASTNode):
    """类定义节点"""
    
    def __init__(self, name: str, bases: List['ASTNode'] = None, 
                 body: List['ASTNode'] = None, keywords: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_CLASS)
        self._name = name
        self._bases = bases if bases is not None else []
        self._body = body if body is not None else []
        self._keywords = keywords if keywords is not None else []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def bases(self) -> List['ASTNode']:
        return self._bases
    
    @property
    def body(self) -> List['ASTNode']:
        return self._body
    
    @property
    def keywords(self) -> List['ASTNode']:
        return self._keywords
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成基类
        bases_str = ""
        if self._bases:
            base_codes = []
            for base in self._bases:
                if hasattr(base, 'to_code'):
                    base_codes.append(base.to_code())
                else:
                    base_codes.append(str(base))
            bases_str = "(" + ", ".join(base_codes) + ")"
        
        # 生成类体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        elif isinstance(self._body, list) and self._body:
            # 如果body是列表，生成基本的类体结构
            body_lines = []
            prev_was_method = False
            for item in self._body:
                # 在方法之间添加空行
                if prev_was_method and hasattr(item, 'to_code'):
                    item_code = item.to_code(indent_level + 1)
                    # 检查是否是方法定义（以 "def " 开头）
                    if item_code.strip().startswith('def '):
                        body_lines.append("")  # 添加空行
                
                if hasattr(item, 'to_code'):
                    item_code = item.to_code(indent_level + 1)
                    body_lines.append(item_code)
                    # 标记是否是方法
                    prev_was_method = item_code.strip().startswith('def ')
                else:
                    body_lines.append("    " * (indent_level + 1) + str(item))
                    prev_was_method = False
            body_str = "\n".join(body_lines)
        else:
            # 如果没有类体，生成pass语句
            body_str = "    " * (indent_level + 1) + "pass"
        
        return f"{indent}class {self._name}{bases_str}:\n{body_str}"


class ASTAssign(ASTNode):
    """赋值节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_targets', '_value')
    
    def __init__(self, targets: List['ASTNode'], value: 'ASTNode'):
        super().__init__(NodeType.NODE_ASSIGN)
        self._targets = targets
        self._value = value
    
    @property
    def targets(self) -> List['ASTNode']:
        return self._targets
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成赋值语句代码"""
        indent = "    " * indent_level
        # 生成目标表达式代码
        target_codes = []
        for target in self._targets:
            if hasattr(target, 'to_code'):
                target_codes.append(target.to_code())
            else:
                target_codes.append(str(target))
        
        # 生成值表达式代码
        if hasattr(self._value, 'to_code'):
            value_code = self._value.to_code()
        else:
            value_code = str(self._value)
        
        targets_str = ", ".join(target_codes)
        return f"{indent}{targets_str} = {value_code}"


class ASTIf(ASTNode):
    """if语句节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_test', '_body', '_orelse')
    
    def __init__(self, test: 'ASTNode' = None, body: 'ASTNode' = None, orelse: 'ASTNode' = None,
                 condition: 'ASTNode' = None, then: 'ASTNode' = None, else_block: 'ASTNode' = None):
        super().__init__(NodeType.NODE_BLOCK)
        self._test = test if test is not None else condition
        self._body = body if body is not None else (then if then is not None else ASTNodeList())
        self._orelse = orelse if orelse is not None else (else_block if else_block is not None else ASTNodeList())
    
    @property
    def test(self) -> 'ASTNode':
        return self._test
    
    @test.setter
    def test(self, value: 'ASTNode'):
        self._test = value
    
    @property
    def condition(self) -> 'ASTNode':
        """test的别名，保持向后兼容"""
        return self._test
    
    @condition.setter
    def condition(self, value: 'ASTNode'):
        """condition的setter，更新test"""
        self._test = value
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @property
    def then(self) -> 'ASTNode':
        """body的别名，保持向后兼容"""
        return self._body
    
    @property
    def orelse(self) -> 'ASTNode':
        return self._orelse
    
    @property
    def else_block(self) -> 'ASTNode':
        """orelse的别名，保持向后兼容"""
        return self._orelse
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成条件表达式
        test_code = self._test.to_code() if hasattr(self._test, 'to_code') else str(self._test)
        
        # 生成if主体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        # 生成if语句
        if_code = f"{indent}if {test_code}:\n{body_str}"
        
        # 处理else/elif分支
        else_code = ""
        if hasattr(self._orelse, 'nodes') and self._orelse.nodes:
            # 检查是否是elif结构
            # 🔧 修复：ASTIf节点使用_type属性而不是_node_type
            else_node = self._orelse.nodes[0]
            is_block_node = (hasattr(else_node, '_type') and else_node._type == NodeType.NODE_BLOCK)
            
            if len(self._orelse.nodes) == 1 and is_block_node:
                # 🔧 修复：检查是否是ASTIf节点（elif）
                # ASTIf节点有_test属性，而ASTBlock有_blk_type属性
                if hasattr(else_node, '_test') and hasattr(else_node, '_body'):
                    # 这是一个elif (ASTIf节点)
                    elif_test_code = else_node.test.to_code() if hasattr(else_node.test, 'to_code') else str(else_node.test)
                    # 生成elif的body，但不包括开头的"if"部分
                    if hasattr(else_node._body, 'to_code'):
                        elif_body_str = else_node._body.to_code(indent_level + 1)
                    else:
                        elif_body_str = "    " * (indent_level + 1) + "pass"
                    
                    # 递归处理elif的orelse（可能有多个elif或else）
                    elif_else_code = ""
                    if hasattr(else_node, '_orelse') and else_node._orelse:
                        if hasattr(else_node._orelse, 'nodes') and else_node._orelse.nodes:
                            # 递归生成elif的else/elif部分
                            elif_else_code = self._generate_orelse(else_node._orelse, indent_level)
                    
                    else_code = f"\n{indent}elif {elif_test_code}:\n{elif_body_str}{elif_else_code}"
                elif hasattr(else_node, '_blk_type'):
                    # 这是一个ASTBlock节点，可能是else块
                    if hasattr(self._orelse, 'to_code'):
                        else_code = "\n" + self._orelse.to_code(indent_level)
                else:
                    # 普通的else块
                    if hasattr(self._orelse, 'to_code'):
                        else_code = "\n" + self._orelse.to_code(indent_level)
            else:
                # 普通的else块
                if hasattr(self._orelse, 'to_code'):
                    else_code = "\n" + self._orelse.to_code(indent_level)
        
        return if_code + else_code
    
    def _generate_orelse(self, orelse, indent_level=0):
        """递归生成else/elif分支代码"""
        indent = "    " * indent_level
        result = ""
        
        if hasattr(orelse, 'nodes') and orelse.nodes:
            for node in orelse.nodes:
                if hasattr(node, '_test') and hasattr(node, '_body'):
                    # 这是一个elif (ASTIf节点)
                    test_code = node.test.to_code() if hasattr(node.test, 'to_code') else str(node.test)
                    if hasattr(node._body, 'to_code'):
                        body_str = node._body.to_code(indent_level + 1)
                    else:
                        body_str = "    " * (indent_level + 1) + "pass"
                    
                    result += f"\n{indent}elif {test_code}:\n{body_str}"
                    
                    # 递归处理这个elif的orelse（可能包含else分支）
                    if hasattr(node, '_orelse') and node._orelse:
                        # 检查orelse中的节点类型
                        if hasattr(node._orelse, 'nodes') and node._orelse.nodes:
                            # 如果orelse包含普通语句节点（不是ASTIf），则生成else块
                            has_if_node = any(hasattr(n, '_test') and hasattr(n, '_body') for n in node._orelse.nodes)
                            if not has_if_node:
                                # 生成else块
                                result += f"\n{indent}else:"
                                for stmt in node._orelse.nodes:
                                    if hasattr(stmt, 'to_code'):
                                        result += "\n" + stmt.to_code(indent_level + 1)
                                    else:
                                        result += f"\n{indent}    {stmt}"
                            else:
                                # 递归处理elif链
                                result += self._generate_orelse(node._orelse, indent_level)
                elif hasattr(node, '_blk_type'):
                    # 这是一个ASTBlock节点（else块）
                    if hasattr(node, 'to_code'):
                        result += "\n" + node.to_code(indent_level)
                    else:
                        # 手动生成else块
                        result += f"\n{indent}else:"
                        if hasattr(node, 'nodes') and node.nodes:
                            for stmt in node.nodes:
                                if hasattr(stmt, 'to_code'):
                                    result += "\n" + stmt.to_code(indent_level + 1)
                                else:
                                    result += f"\n{indent}    {stmt}"
                        else:
                            result += f"\n{indent}    pass"
                else:
                    # 普通语句节点，生成else块
                    result += f"\n{indent}else:"
                    if hasattr(node, 'to_code'):
                        result += "\n" + node.to_code(indent_level + 1)
                    else:
                        result += f"\n{indent}    {node}"
        
        return result


class ASTFor(ASTNode):
    """for循环节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_target', '_iter', '_body', '_else_block')
    
    def __init__(self, target: 'ASTNode', iter_node: Optional['ASTNode'] = None, body: Optional['ASTNode'] = None, 
                 else_block: Optional['ASTNode'] = None):
        super().__init__(NodeType.NODE_FOR)
        self._target = target
        self._iter = iter_node if iter_node is not None else ASTName("__iter__", "")
        self._body = body if body is not None else ASTNodeList()
        self._else_block = else_block
    
    @property
    def target(self) -> 'ASTNode':
        return self._target
    
    @target.setter
    def target(self, value: 'ASTNode') -> None:
        self._target = value
    
    @property
    def iter(self) -> 'ASTNode':
        return self._iter
    
    @iter.setter
    def iter(self, value: 'ASTNode') -> None:
        self._iter = value
    
    @property
    def iter_node(self) -> 'ASTNode':
        """iter的别名，保持向后兼容"""
        return self._iter
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @body.setter
    def body(self, value: 'ASTNode') -> None:
        self._body = value
    
    @property
    def else_block(self) -> 'ASTNode':
        return self._else_block
    
    @else_block.setter
    def else_block(self, value: 'ASTNode') -> None:
        self._else_block = value
    
    @else_block.setter
    def else_block(self, value: 'ASTNode') -> None:
        self._else_block = value
    
    @property
    def orelse(self) -> 'ASTNode':
        return self._else_block
    
    @property
    def test(self) -> 'ASTNode':
        """测试条件，用于向后兼容"""
        return self._iter
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成迭代目标
        target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        
        # 生成迭代器
        iter_code = self._iter.to_code() if hasattr(self._iter, 'to_code') else str(self._iter)
        
        # 生成for主体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        # 生成for语句
        for_code = f"{indent}for {target_code} in {iter_code}:\n{body_str}"
        
        # 处理else块
        else_code = ""
        if self._else_block:
            if hasattr(self._else_block, 'to_code'):
                else_str = self._else_block.to_code(indent_level)
            else:
                else_str = "    " * (indent_level + 1) + "pass"
            else_code = f"\n{indent}else:\n{else_str}"
        
        return for_code + else_code


class ASTWhile(ASTNode):
    """while循环节点"""
    
    def __init__(self, test: 'ASTNode' = None, body: 'ASTNode' = None, else_block: 'ASTNode' = None,
                 condition: 'ASTNode' = None):
        super().__init__(NodeType.NODE_BLOCK)
        self._test = test if test is not None else condition
        self._body = body if body is not None else ASTNodeList()
        self._else_block = else_block if else_block is not None else None
    
    @property
    def test(self) -> 'ASTNode':
        return self._test
    
    @property
    def condition(self) -> 'ASTNode':
        """test的别名，保持向后兼容"""
        return self._test
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @property
    def else_block(self) -> 'ASTNode':
        return self._else_block
    
    @property
    def orelse(self) -> 'ASTNode':
        return self._else_block
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成条件表达式
        test_code = self._test.to_code() if hasattr(self._test, 'to_code') else str(self._test)
        
        # 生成while主体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        # 生成while语句
        while_code = f"{indent}while {test_code}:\n{body_str}"
        
        # 处理else块
        else_code = ""
        if self._else_block:
            if hasattr(self._else_block, 'to_code'):
                else_str = self._else_block.to_code(indent_level)
            else:
                else_str = "    " * (indent_level + 1) + "pass"
            else_code = f"\n{indent}else:\n{else_str}"
        
        return while_code + else_code


class ASTWith(ASTNode):
    """with语句节点"""
    
    def __init__(self, context: 'ASTNode' = None, body: 'ASTNode' = None, optional_vars: 'ASTNode' = None,
                 items: List['ASTWithItem'] = None):
        super().__init__(NodeType.NODE_BLOCK)
        if items is not None:
            self._items = items
        elif context is not None:
            self._items = [ASTWithItem(context, optional_vars)]
        else:
            self._items = []
        self._body = body if body is not None else ASTNodeList()
    
    @property
    def items(self) -> List['ASTWithItem']:
        return self._items
    
    @property
    def context(self) -> 'ASTNode':
        """返回第一个with item的context_expr，保持向后兼容"""
        if self._items and hasattr(self._items[0], 'context_expr'):
            return self._items[0].context_expr
        return None
    
    @property
    def optional_vars(self) -> 'ASTNode':
        """返回第一个with item的optional_vars"""
        if self._items and hasattr(self._items[0], 'optional_vars'):
            return self._items[0].optional_vars
        return None
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成with语句
        if not self._items:
            # 如果没有items，生成空的with语句
            return f"{indent}with ():\n    " + "    " * (indent_level + 1) + "pass"
        
        # 生成with items
        item_codes = []
        for item in self._items:
            if hasattr(item, 'to_code'):
                item_codes.append(item.to_code())
            elif hasattr(item, 'context_expr'):
                # 基本的with item
                context_code = item.context_expr.to_code() if hasattr(item.context_expr, 'to_code') else str(item.context_expr)
                if hasattr(item, 'optional_vars') and item.optional_vars:
                    var_code = item.optional_vars.to_code() if hasattr(item.optional_vars, 'to_code') else str(item.optional_vars)
                    item_codes.append(f"{context_code} as {var_code}")
                else:
                    item_codes.append(context_code)
            else:
                item_codes.append(str(item))
        
        items_str = ", ".join(item_codes)
        
        # 生成with主体
        if hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        return f"{indent}with {items_str}:\n{body_str}"


class ASTTry(ASTNode):
    """try语句节点"""
    
    def __init__(self, body: 'ASTNodeList' = None, handlers: List['ASTNode'] = None, 
                 orelse: 'ASTNodeList' = None, finalbody: 'ASTNodeList' = None,
                 else_block: 'ASTNodeList' = None, finally_block: 'ASTNodeList' = None):
        super().__init__(NodeType.NODE_TRY)
        self._body = body
        self._handlers = handlers if handlers is not None else []
        self._orelse = orelse if orelse is not None else else_block
        self._finalbody = finalbody if finalbody is not None else finally_block
    
    @property
    def body(self) -> 'ASTNodeList':
        return self._body
    
    @property
    def handlers(self) -> List['ASTNode']:
        return self._handlers
    
    @property
    def orelse(self) -> 'ASTNodeList':
        return self._orelse
    
    @property
    def else_block(self) -> 'ASTNodeList':
        """orelse的别名，保持向后兼容"""
        return self._orelse
    
    @property
    def finalbody(self) -> 'ASTNodeList':
        return self._finalbody
    
    @property
    def finally_block(self) -> 'ASTNodeList':
        """finalbody的别名，保持向后兼容"""
        return self._finalbody
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        indent = "    " * indent_level
        
        # 生成try主体
        if hasattr(self._body, 'to_code'):
            try_body_str = self._body.to_code(indent_level + 1)
        else:
            try_body_str = "    " * (indent_level + 1) + "pass"
        
        # 生成try语句
        try_code = f"{indent}try:\n{try_body_str}"
        
        # 生成except handlers
        except_code = ""
        if self._handlers:
            for handler in self._handlers:
                if hasattr(handler, 'to_code'):
                    handler_str = handler.to_code(indent_level)
                else:
                    handler_str = f"{indent}    except:\n{indent}    " + "    " * (indent_level + 1) + "pass"
                except_code += "\n" + handler_str
        
        # 生成else块
        else_code = ""
        if self._orelse and (hasattr(self._orelse, 'nodes') and self._orelse.nodes):
            if hasattr(self._orelse, 'to_code'):
                else_str = self._orelse.to_code(indent_level)
            else:
                else_str = f"{indent}    pass"
            else_code = f"\n{indent}else:\n{else_str}"
        
        # 生成finally块
        finally_code = ""
        if self._finalbody and (hasattr(self._finalbody, 'nodes') and self._finalbody.nodes):
            if hasattr(self._finalbody, 'to_code'):
                finally_str = self._finalbody.to_code(indent_level)
            else:
                finally_str = f"{indent}    pass"
            finally_code = f"\n{indent}finally:\n{finally_str}"
        
        return try_code + except_code + else_code + finally_code


class ASTWithItem(ASTNode):
    """with语句项节点"""
    
    def __init__(self, context_expr: 'ASTNode', optional_vars: 'ASTNode'):
        super().__init__(NodeType.NODE_STORE)
        self._context_expr = context_expr
        self._optional_vars = optional_vars
    
    @property
    def context_expr(self) -> 'ASTNode':
        return self._context_expr
    
    @property
    def optional_vars(self) -> 'ASTNode':
        return self._optional_vars
    
    def to_code(self, indent_level=0):
        """生成with语句项代码"""
        # 生成上下文表达式代码
        if hasattr(self._context_expr, 'to_code'):
            context_code = self._context_expr.to_code()
        else:
            context_code = str(self._context_expr)
        
        if self._optional_vars is not None:
            # 有变量的情况：context as var
            if hasattr(self._optional_vars, 'to_code'):
                vars_code = self._optional_vars.to_code()
            else:
                vars_code = str(self._optional_vars)
            return f"{context_code} as {vars_code}"
        else:
            # 没有变量的情况：context
            return context_code


class ASTComprehension(ASTNode):
    """推导式节点"""
    
    def __init__(self, target: 'ASTNode', iter_node: 'ASTNode', ifs: List['ASTNode'] = None, is_async: bool = False):
        super().__init__(NodeType.NODE_COMPREHENSION)
        self._target = target
        self._iter = iter_node
        self._ifs = ifs if ifs is not None else []
        self._is_async = is_async
    
    @property
    def target(self) -> 'ASTNode':
        return self._target
    
    @property
    def iter_node(self) -> 'ASTNode':
        return self._iter
    
    @property
    def ifs(self) -> List['ASTNode']:
        return self._ifs
    
    @property
    def is_async(self) -> bool:
        return self._is_async
    
    def to_code(self, indent_level=0):
        """生成推导式代码"""
        target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        iter_code = self._iter.to_code() if hasattr(self._iter, 'to_code') else str(self._iter)
        
        # 构建条件
        ifs_code = ""
        if self._ifs:
            if_parts = []
            for if_expr in self._ifs:
                if_code = if_expr.to_code() if hasattr(if_expr, 'to_code') else str(if_expr)
                if_parts.append(if_code)
            ifs_code = " if " + " and ".join(if_parts)
        
        async_prefix = "async " if self._is_async else ""
        return f"{async_prefix}for {target_code} in {iter_code}{ifs_code}"


class ASTReturn(ASTNode):
    """返回节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_value', '_rettype')
    
    class RetType(Enum):
        RETURN = 0
        YIELD = 1
        YIELD_FROM = 2
    
    def __init__(self, value: 'ASTNode', rettype: 'ASTReturn.RetType' = None):
        super().__init__(NodeType.NODE_RETURN)
        self._value = value
        self._rettype = rettype if rettype is not None else ASTReturn.RetType.RETURN
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def rettype(self) -> 'ASTReturn.RetType':
        return self._rettype
    
    def to_code(self, indent_level=0):
        """生成return语句代码"""
        indent = "    " * indent_level
        if self._value is not None:
            # 🔧 修复：检查值是否为None，如果是则不生成return语句
            # Python中return None是隐式的，不需要显式写出
            if isinstance(self._value, ASTConstant) and self._value.value is None:
                return ""  # 不生成return None
            value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
            # 🔧 修复：再次检查生成的代码是否为"None"
            if value_code == "None":
                return ""  # 不生成return None
            return f"{indent}return {value_code}"
        else:
            return f"{indent}return"


class ASTYield(ASTNode):
    """Yield语句节点"""
    
    def __init__(self, value: Optional['ASTNode'] = None, is_from: bool = False):
        super().__init__(NodeType.NODE_YIELD)
        self._value = value
        self._is_from = is_from
    
    @property
    def value(self) -> Optional['ASTNode']:
        return self._value
    
    @property
    def is_from(self) -> bool:
        return self._is_from
    
    def to_code(self, indent_level=0):
        """生成yield语句代码"""
        prefix = "yield from " if self._is_from else "yield "
        if self._value is not None:
            if hasattr(self._value, 'to_code'):
                value_code = self._value.to_code()
            else:
                value_code = str(self._value)
            return f"{prefix}{value_code}"
        else:
            return prefix.strip()


class ASTFormattedValue(ASTNode):
    """格式化值节点（用于f-string）- 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_value', '_conversion', '_format_spec')
    
    def __init__(self, value: 'ASTNode', conversion: int = 0, format_spec: Optional['ASTNode'] = None):
        super().__init__(NodeType.NODE_FORMATTED_VALUE)
        self._value = value
        self._conversion = conversion  # 0=无, 1=str, 2=repr, 3=ascii
        self._format_spec = format_spec
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def conversion(self) -> int:
        return self._conversion
    
    @property
    def format_spec(self) -> Optional['ASTNode']:
        return self._format_spec
    
    def to_code(self, indent_level=0):
        """生成格式化值代码"""
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        
        # 添加转换说明符
        conversion_map = {1: "!s", 2: "!r", 3: "!a"}
        conversion_suffix = conversion_map.get(self._conversion, "")
        
        if self._format_spec:
            format_code = self._format_spec.to_code() if hasattr(self._format_spec, 'to_code') else str(self._format_spec)
            return f"{{{value_code}{conversion_suffix}:{format_code}}}"
        else:
            return f"{{{value_code}{conversion_suffix}}}"


class ASTJoinedStr(ASTNode):
    """连接的字符串节点（用于f-string）"""
    
    def __init__(self, values: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_JOINED_STR)
        self._values = values if values is not None else []
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    def to_code(self, indent_level=0):
        """生成f-string代码"""
        print(f"[DEBUG ASTJoinedStr] _values: {self._values}", flush=True)
        if not self._values:
            return '""'
        
        parts = []
        for value in self._values:
            print(f"[DEBUG ASTJoinedStr] value: {value}, type: {type(value).__name__}", flush=True)
            # 处理 ASTObject 类型的字符串
            if isinstance(value, ASTObject):
                if isinstance(value.object, str):
                    parts.append(value.object)
                elif hasattr(value.object, 'value') and isinstance(value.object.value, str):
                    parts.append(value.object.value)
            # 处理 ASTConstant 类型的字符串
            elif isinstance(value, ASTConstant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ASTFormattedValue):
                # 格式化值部分
                parts.append(value.to_code())
            elif isinstance(value, ASTAttribute):
                # 属性访问，如 self.name
                parts.append(f"{{{value.to_code()}}}")
            else:
                # 其他表达式
                value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
                parts.append(f"{{{value_code}}}")
        
        # 构建f-string
        if parts:
            return 'f"' + ''.join(parts) + '"'
        else:
            return '""'


class ASTExpr(ASTNode):
    """表达式语句节点"""
    
    def __init__(self, value: 'ASTNode'):
        super().__init__(NodeType.NODE_OBJECT)
        self._value = value
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成表达式语句代码"""
        if hasattr(self._value, 'to_code'):
            return self._value.to_code(indent_level)
        else:
            return str(self._value)


class ASTAttribute(ASTNode):
    """属性访问节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_value', '_attr', '_ctx')
    
    def __init__(self, value: 'ASTNode', attr: str, ctx: int):
        super().__init__(NodeType.NODE_ATTRIBUTE)
        self._value = value
        self._attr = attr
        self._ctx = ctx
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def attr(self) -> str:
        return self._attr
    
    @property
    def ctx(self) -> int:
        return self._ctx
    
    def to_code(self, indent_level=0):
        """生成属性访问代码"""
        # 生成值表达式代码
        if hasattr(self._value, 'to_code'):
            value_code = self._value.to_code()
        else:
            value_code = str(self._value)
        
        # 属性名应该直接使用字符串
        return f"{value_code}.{self._attr}"


class ASTDelete(ASTNode):
    """删除语句节点"""
    
    def __init__(self, targets: List['ASTNode']):
        super().__init__(NodeType.NODE_DELETE)
        self._targets = targets
    
    @property
    def targets(self) -> List['ASTNode']:
        return self._targets
    
    def to_code(self, indent_level=0):
        """生成delete语句代码"""
        if not self._targets:
            return "del"
        
        target_codes = []
        for target in self._targets:
            if hasattr(target, 'to_code'):
                target_codes.append(target.to_code())
            else:
                target_codes.append(str(target))
        
        return f"del {', '.join(target_codes)}"


class ASTGlobal(ASTNode):
    """global语句节点"""
    
    def __init__(self, names: List[str]):
        super().__init__(NodeType.NODE_GLOBAL)
        self._names = names
    
    @property
    def names(self) -> List[str]:
        return self._names
    
    def to_code(self, indent_level=0):
        """生成global语句代码"""
        if not self._names:
            return "global"
        return f"global {', '.join(self._names)}"


class ASTNonlocal(ASTNode):
    """nonlocal语句节点"""
    
    def __init__(self, names: List[str]):
        super().__init__(NodeType.NODE_NONLOCAL)
        self._names = names
    
    @property
    def names(self) -> List[str]:
        return self._names
    
    def to_code(self, indent_level=0):
        """生成nonlocal语句代码"""
        if not self._names:
            return "nonlocal"
        return f"nonlocal {', '.join(self._names)}"


class ASTImport(ASTNode):
    """import语句节点"""
    
    def __init__(self, names: Union[str, List[str]]):
        super().__init__(NodeType.NODE_IMPORT)
        if isinstance(names, str):
            self._names = [names]
            self.module_name = names  # 添加module_name属性
        else:
            self._names = names
            self.module_name = names[0] if names else None
    
    @property
    def names(self) -> List[str]:
        return self._names


class ASTImportFrom(ASTNode):
    """from import语句节点"""
    
    def __init__(self, module: str, names: Union[str, List[str]], level: int = 0):
        super().__init__(NodeType.NODE_IMPORT)
        self._module = module
        self.module_name = module  # 添加module_name属性
        if isinstance(names, str):
            self._names = [names]
        else:
            self._names = names
        self._level = level
    
    @property
    def module(self) -> str:
        return self._module
    
    @property
    def names(self) -> List[str]:
        return self._names
    
    @property
    def level(self) -> int:
        return self._level


class ASTAlias(ASTNode):
    """import别名节点"""
    
    def __init__(self, name: str, asname: str):
        super().__init__(NodeType.NODE_IMPORT)
        self._name = name
        self._asname = asname
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def asname(self) -> str:
        return self._asname
    
    def to_code(self, indent_level=0):
        """生成import别名代码"""
        if self._asname:
            # 有别名的情况：name as asname
            return f"{self._name} as {self._asname}"
        else:
            # 没有别名的情况：name
            return self._name


class ASTPass(ASTNode):
    """Pass语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_BLOCK)


class ASTBreak(ASTNode):
    """Break语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_BREAK)


class ASTContinue(ASTNode):
    """Continue语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_CONTINUE)


class ASTJump(ASTNode):
    """Jump语句节点（用于无条件跳转）"""
    
    def __init__(self, target: int = 0):
        super().__init__(NodeType.NODE_JUMP)
        self._target = target
    
    @property
    def target(self) -> int:
        return self._target
    
    def __str__(self):
        return f"JUMP to {self._target}"
    
    def to_code(self, indent_level=0):
        """生成jump语句代码"""
        # Jump语句通常对应控制流跳转，在源代码中可能表示为注释
        return f"# JUMP to {self._target}"


class ASTAssert(ASTNode):
    """assert语句节点"""
    
    def __init__(self, test: 'ASTNode', msg: 'ASTNode' = None):
        super().__init__(NodeType.NODE_ASSERT)
        self._test = test
        self._msg = msg
    
    @property
    def test(self) -> 'ASTNode':
        return self._test
    
    @property
    def msg(self) -> 'ASTNode':
        return self._msg
    
    def to_code(self, indent_level=0):
        """生成assert语句代码"""
        # 生成测试表达式代码
        if hasattr(self._test, 'to_code'):
            test_code = self._test.to_code()
        else:
            test_code = str(self._test)
        
        if self._msg is not None:
            # 有消息的情况：assert test, msg
            if hasattr(self._msg, 'to_code'):
                msg_code = self._msg.to_code()
            else:
                msg_code = str(self._msg)
            return f"assert {test_code}, {msg_code}"
        else:
            # 没有消息的情况：assert test
            return f"assert {test_code}"


class ASTAnnAssign(ASTNode):
    """带注解的赋值节点"""
    
    def __init__(self, target: 'ASTNode', annotation: 'ASTNode', value: 'ASTNode', simple: bool = False):
        super().__init__(NodeType.NODE_ANNOTATED_VAR)
        self._target = target
        self._annotation = annotation
        self._value = value
        self._simple = simple
    
    @property
    def target(self) -> 'ASTNode':
        return self._target
    
    @property
    def annotation(self) -> 'ASTNode':
        return self._annotation
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def simple(self) -> bool:
        return self._simple
    
    def to_code(self, indent_level=0):
        """生成带注解的赋值代码"""
        target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        annotation_code = self._annotation.to_code() if hasattr(self._annotation, 'to_code') else str(self._annotation)
        
        if self._value is not None:
            value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
            return f"{target_code}: {annotation_code} = {value_code}"
        else:
            return f"{target_code}: {annotation_code}"


class ASTAugAssign(ASTNode):
    """增量赋值节点 (+=, -=, *=, /=, //=, %=, **=, &=, |=, ^=, <<=, >>=, @=)"""
    
    # 操作符映射
    OP_MAP = {
        '+=': 'Add',
        '-=': 'Sub',
        '*=': 'Mult',
        '/=': 'Div',
        '//=': 'FloorDiv',
        '%=': 'Mod',
        '**=': 'Pow',
        '&=': 'BitAnd',
        '|=': 'BitOr',
        '^=': 'BitXor',
        '<<=': 'LShift',
        '>>=': 'RShift',
        '@=': 'MatMult',
    }
    
    def __init__(self, target: 'ASTNode', op: str, value: 'ASTNode'):
        super().__init__(NodeType.NODE_AUGASSIGN)
        self._target = target
        self._op = op
        self._value = value
    
    @property
    def target(self) -> 'ASTNode':
        return self._target
    
    @property
    def op(self) -> str:
        return self._op
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成增量赋值代码"""
        indent = "    " * indent_level
        target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        return f"{indent}{target_code} {self._op} {value_code}"


class ASTRaise(ASTNode):
    """异常抛出节点"""
    
    def __init__(self, exc: 'ASTNode' = None):
        super().__init__(NodeType.NODE_RAISE)
        self._exc = exc
    
    @property
    def exc(self) -> 'ASTNode':
        return self._exc
    
    def __eq__(self, other):
        """比较两个异常抛出节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTRaise):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return self._exc == other._exc
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成异常抛出节点的哈希值"""
        return hash((super().__hash__(), self._exc))
    
    def to_code(self, indent_level=0) -> str:
        """生成raise语句代码"""
        indent = "    " * indent_level
        if self._exc:
            if hasattr(self._exc, 'to_code'):
                exc_code = self._exc.to_code(0)
            else:
                exc_code = str(self._exc)
            return f"{indent}raise {exc_code}"
        else:
            return f"{indent}raise"


class ASTLambda(ASTNode):
    """Lambda函数节点"""
    
    def __init__(self, args: List['ASTNode'], body: 'ASTNode'):
        super().__init__(NodeType.NODE_LAMBDA)
        self._args = args if args is not None else []
        self._body = body
    
    @property
    def args(self) -> List['ASTNode']:
        return self._args
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    def __eq__(self, other):
        """比较两个Lambda节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTLambda):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._args == other._args and 
                    self._body == other._body)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成Lambda节点的哈希值"""
        return hash((super().__hash__(), tuple(self._args), self._body))
    
    def to_code(self, indent_level=0):
        """生成lambda表达式代码"""
        # 生成参数代码
        arg_codes = []
        for arg in self._args:
            if hasattr(arg, 'to_code'):
                arg_codes.append(arg.to_code())
            else:
                arg_codes.append(str(arg))
        
        args_str = ", ".join(arg_codes)
        
        # 生成函数体代码
        if hasattr(self._body, 'to_code'):
            body_code = self._body.to_code()
        else:
            body_code = str(self._body)
        
        return f"lambda {args_str}: {body_code}"


class ASTListComp(ASTNode):
    """列表推导式节点"""
    
    def __init__(self, elt: 'ASTNode', generators: List['ASTComprehension']):
        super().__init__(NodeType.NODE_LISTCOMP)
        self._elt = elt
        self._generators = generators if generators is not None else []
    
    @property
    def elt(self) -> 'ASTNode':
        return self._elt
    
    @property
    def generators(self) -> List['ASTComprehension']:
        return self._generators
    
    def __eq__(self, other):
        """比较两个列表推导式节点是否相等"""
        if not isinstance(other, ASTListComp):
            return False
        if not super().__eq__(other):
            return False
        return (self._elt == other._elt and 
                self._generators == other._generators)
    
    def __hash__(self):
        """生成列表推导式节点的哈希值"""
        return hash((super().__hash__(), self._elt, tuple(self._generators)))
    
    def to_code(self, indent_level=0):
        """生成列表推导式代码"""
        # 生成元素表达式
        elt_code = self._elt.to_code() if hasattr(self._elt, 'to_code') else str(self._elt)
        
        # 生成生成器部分
        generators_code = " ".join(
            g.to_code() if hasattr(g, 'to_code') else str(g) 
            for g in self._generators
        )
        
        return f"[{elt_code} {generators_code}]"


class ASTSetComp(ASTNode):
    """集合推导式节点"""
    
    def __init__(self, elt: 'ASTNode', generators: List['ASTComprehension']):
        super().__init__(NodeType.NODE_SETCOMP)
        self._elt = elt
        self._generators = generators if generators is not None else []
    
    @property
    def elt(self) -> 'ASTNode':
        return self._elt
    
    @property
    def generators(self) -> List['ASTComprehension']:
        return self._generators
    
    def __eq__(self, other):
        """比较两个集合推导式节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTSetComp):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._elt == other._elt and 
                    self._generators == other._generators)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成集合推导式节点的哈希值"""
        return hash((super().__hash__(), self._elt, tuple(self._generators)))
    
    def to_code(self, indent_level=0):
        """生成集合推导式代码"""
        # 生成元素表达式
        elt_code = self._elt.to_code() if hasattr(self._elt, 'to_code') else str(self._elt)
        
        # 生成生成器部分
        generators_code = " ".join(
            g.to_code() if hasattr(g, 'to_code') else str(g) 
            for g in self._generators
        )
        
        return f"{{{elt_code} {generators_code}}}"


class ASTDictComp(ASTNode):
    """字典推导式节点"""
    
    def __init__(self, key: 'ASTNode', value: 'ASTNode', generators: List['ASTComprehension']):
        super().__init__(NodeType.NODE_DICTCOMP)
        self._key = key
        self._value = value
        self._generators = generators if generators is not None else []
    
    @property
    def key(self) -> 'ASTNode':
        return self._key
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def generators(self) -> List['ASTComprehension']:
        return self._generators
    
    def __eq__(self, other):
        """比较两个字典推导式节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTDictComp):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._key == other._key and 
                    self._value == other._value and
                    self._generators == other._generators)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成字典推导式节点的哈希值"""
        return hash((super().__hash__(), self._key, self._value, tuple(self._generators)))
    
    def to_code(self, indent_level=0):
        """生成字典推导式代码"""
        # 生成键和值表达式
        key_code = self._key.to_code() if hasattr(self._key, 'to_code') else str(self._key)
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        
        # 生成生成器部分
        generators_code = " ".join(
            g.to_code() if hasattr(g, 'to_code') else str(g) 
            for g in self._generators
        )
        
        return f"{{{key_code}: {value_code} {generators_code}}}"


class ASTGenExpr(ASTNode):
    """生成器表达式节点"""
    
    def __init__(self, elt: 'ASTNode', generators: List['ASTComprehension']):
        super().__init__(NodeType.NODE_GENEXPR)
        self._elt = elt
        self._generators = generators if generators is not None else []
    
    @property
    def elt(self) -> 'ASTNode':
        return self._elt
    
    @property
    def generators(self) -> List['ASTComprehension']:
        return self._generators
    
    def __eq__(self, other):
        """比较两个生成器表达式节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTGenExpr):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._elt == other._elt and 
                    self._generators == other._generators)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成生成器表达式节点的哈希值"""
        return hash((super().__hash__(), self._elt, tuple(self._generators)))
    
    def to_code(self, indent_level=0):
        """生成生成器表达式代码"""
        # 生成元素表达式
        elt_code = self._elt.to_code() if hasattr(self._elt, 'to_code') else str(self._elt)
        
        # 生成生成器部分
        generators_code = " ".join(
            g.to_code() if hasattr(g, 'to_code') else str(g) 
            for g in self._generators
        )
        
        return f"({elt_code} {generators_code})"


class ASTConditionalExp(ASTNode):
    """条件表达式节点（三元运算符：a if condition else b）"""
    
    def __init__(self, condition: 'ASTNode', true_val: 'ASTNode', false_val: 'ASTNode'):
        super().__init__(NodeType.NODE_CONDITIONALEXP)
        self._condition = condition
        self._true_val = true_val
        self._false_val = false_val
    
    @property
    def condition(self) -> 'ASTNode':
        return self._condition
    
    @property
    def true_val(self) -> 'ASTNode':
        return self._true_val
    
    @property
    def false_val(self) -> 'ASTNode':
        return self._false_val
    
    def to_code(self, indent_level=0):
        """生成条件表达式代码"""
        true_code = self._true_val.to_code() if hasattr(self._true_val, 'to_code') else str(self._true_val)
        false_code = self._false_val.to_code() if hasattr(self._false_val, 'to_code') else str(self._false_val)
        condition_code = self._condition.to_code() if hasattr(self._condition, 'to_code') else str(self._condition)
        
        return f"{true_code} if {condition_code} else {false_code}"
    
    def __eq__(self, other):
        """比较两个条件表达式节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTConditionalExp):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._condition == other._condition and 
                    self._true_val == other._true_val and 
                    self._false_val == other._false_val)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成条件表达式节点的哈希值"""
        return hash((super().__hash__(), self._condition, self._true_val, self._false_val))


class ASTExceptHandler(ASTNode):
    """except处理器节点"""
    
    def __init__(self, type_node: 'ASTNode' = None, name: str = None, body: 'ASTNodeList' = None,
                 exc_type: 'ASTNode' = None):
        super().__init__(NodeType.NODE_EXCEPT)
        self._exception_type = type_node if type_node is not None else exc_type
        self._body = body
        self._name = name
    
    @property
    def exc_type(self) -> 'ASTNode':
        """返回异常类型"""
        return self._exception_type
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def body(self) -> 'ASTNodeList':
        return self._body
    
    def __eq__(self, other):
        """比较两个except处理器节点是否相等"""
        if not _check_depth():
            return False
        if not isinstance(other, ASTExceptHandler):
            return False
        if self is other:
            return True
        if not super().__eq__(other):
            return False
        _inc_depth()
        try:
            return (self._type == other._type and 
                    self._name == other._name and 
                    self._body == other._body)
        finally:
            _dec_depth()
    
    def __hash__(self):
        """生成except处理器节点的哈希值"""
        return hash((super().__hash__(), self._type, self._name, self._body))
    
    def to_code(self, indent_level=0):
        """生成except处理器代码"""
        indent = "    " * indent_level
        
        # 生成异常类型代码
        if self._exception_type is not None:
            if hasattr(self._exception_type, 'to_code'):
                type_code = self._exception_type.to_code()
            else:
                type_code = str(self._exception_type)
            
            if self._name is not None:
                # 有变量名的情况：except Exception as e:
                header = f"{indent}except {type_code} as {self._name}:"
            else:
                # 没有变量名的情况：except Exception:
                header = f"{indent}except {type_code}:"
        else:
            # 没有异常类型的情况：except:
            header = f"{indent}except:"
        
        # 生成body代码
        if self._body is not None and hasattr(self._body, 'to_code'):
            body_str = self._body.to_code(indent_level + 1)
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        return f"{header}\n{body_str}"


ASTBinOp = ASTBinary        
ASTUnaryOp = ASTUnary       
ASTBoolOp = ASTBinary
ASTFunction = ASTFunctionDef
ASTClass = ASTClassDef      
ASTExcept = ASTExceptHandler


class ASTMatchClass(ASTNode):
    """模式匹配中的类匹配节点"""
    
    def __init__(self, cls: 'ASTNode', patterns: List['ASTNode'] = None, guards: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_MATCH_CLASS)
        self._cls = cls
        self._patterns = patterns if patterns is not None else []
        self._guards = guards if guards is not None else []
    
    @property
    def cls(self) -> 'ASTNode':
        return self._cls
    
    @property
    def patterns(self) -> List['ASTNode']:
        return self._patterns
    
    @property
    def guards(self) -> List['ASTNode']:
        return self._guards
    
    def to_code(self, indent_level=0):
        """生成match class代码"""
        if hasattr(self._cls, 'to_code'):
            cls_code = self._cls.to_code()
        else:
            cls_code = str(self._cls)
        
        if self._patterns:
            pattern_codes = []
            for pattern in self._patterns:
                if hasattr(pattern, 'to_code'):
                    pattern_codes.append(pattern.to_code())
                else:
                    pattern_codes.append(str(pattern))
            patterns_str = ", ".join(pattern_codes)
            return f"{cls_code}({patterns_str})"
        else:
            return f"{cls_code}()"


class ASTMatchKeys(ASTNode):
    """模式匹配中的键匹配节点"""
    
    def __init__(self, keys: List['ASTNode']):
        super().__init__(NodeType.NODE_MATCH_KEYS)
        self._keys = keys if keys is not None else []
    
    @property
    def keys(self) -> List['ASTNode']:
        return self._keys


class ASTMatchMapping(ASTNode):
    """模式匹配中的字典/映射匹配节点"""
    
    def __init__(self, keys: List['ASTNode'], patterns: List['ASTNode']):
        super().__init__(NodeType.NODE_MATCH_MAPPING)
        self._keys = keys if keys is not None else []
        self._patterns = patterns if patterns is not None else []
    
    @property
    def keys(self) -> List['ASTNode']:
        return self._keys
    
    @property
    def patterns(self) -> List['ASTNode']:
        return self._patterns
    
    def to_code(self, indent_level=0):
        """生成match mapping代码"""
        if self._keys and self._patterns:
            mapping_items = []
            for key, pattern in zip(self._keys, self._patterns):
                key_code = key.to_code() if hasattr(key, 'to_code') else str(key)
                pattern_code = pattern.to_code() if hasattr(pattern, 'to_code') else str(pattern)
                mapping_items.append(f"{key_code}: {pattern_code}")
            return "{" + ", ".join(mapping_items) + "}"
        else:
            return "{}"


class ASTMatchSequence(ASTNode):
    """模式匹配中的序列匹配节点"""
    
    def __init__(self, patterns: List['ASTNode'], rest: str = None):
        super().__init__(NodeType.NODE_MATCH_SEQUENCE)
        self._patterns = patterns if patterns is not None else []
        self._rest = rest
    
    @property
    def patterns(self) -> List['ASTNode']:
        return self._patterns
    
    @property
    def rest(self) -> str:
        return self._rest
    
    def to_code(self, indent_level=0):
        """生成match sequence代码"""
        if self._patterns:
            pattern_codes = []
            for pattern in self._patterns:
                if hasattr(pattern, 'to_code'):
                    pattern_codes.append(pattern.to_code())
                else:
                    pattern_codes.append(str(pattern))
            
            patterns_str = ", ".join(pattern_codes)
            
            # 如果有rest参数，添加*rest
            if self._rest:
                patterns_str += f", *{self._rest}"
            
            return f"[{patterns_str}]"
        else:
            return "[]"


class ASTConstMap(ASTNode):
    """常量键映射节点（用于BUILD_CONST_KEY_MAP）"""
    
    def __init__(self, keys: 'ASTNode', values: List['ASTNode']):
        super().__init__(NodeType.NODE_CONST_MAP)
        self._keys = keys
        self._values = values if values is not None else []
    
    @property
    def keys(self) -> 'ASTNode':
        return self._keys
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    def to_code(self, indent_level=0):
        """生成字典创建代码"""
        if not self._values:
            return "{}"
        
        # 构建字典表达式
        parts = []
        for i, value in enumerate(self._values):
            # 获取键值
            if hasattr(self._keys, 'values') and len(self._keys.values()) > i:
                key_node = self._keys.values()[i]
            else:
                key_node = None
            
            # 生成键和值的代码
            if key_node and hasattr(key_node, 'to_code'):
                key_code = key_node.to_code()
            else:
                key_code = f"key_{i}"
            
            if hasattr(value, 'to_code'):
                value_code = value.to_code()
            else:
                value_code = str(value)
            
            parts.append(f"{key_code}: {value_code}")
        
        return "{" + ", ".join(parts) + "}"


class ASTAwaitable(ASTNode):
    """异步操作节点"""
    
    def __init__(self, value: 'ASTNode'):
        super().__init__(NodeType.NODE_AWAITABLE)
        self._value = value
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成await表达式代码"""
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        return f"await {value_code}"


class ASTLoadBuildClass(ASTNode):
    """类构建节点"""
    
    def __init__(self, obj):
        super().__init__(NodeType.NODE_LOAD_BUILD_CLASS)
        self._obj = obj
    
    @property
    def obj(self):
        return self._obj
    
    def to_code(self, indent_level=0):
        """生成类构建代码"""
        if hasattr(self._obj, 'to_code'):
            return self._obj.to_code()
        elif hasattr(self._obj, '__str__'):
            return str(self._obj)
        else:
            return repr(self._obj)


class ASTKwNamesMap(ASTNode):
    """关键字名称映射节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_KW_NAMES_MAP)
        self._values = []  # List of (key, value) tuples
    
    def add(self, key: 'ASTNode', value: 'ASTNode'):
        """添加键值对"""
        self._values.append((key, value))
    
    @property
    def values(self) -> List[Tuple['ASTNode', 'ASTNode']]:
        return self._values
    
    def to_code(self, indent_level=0):
        """生成字典创建代码"""
        if not self._values:
            return "{}"
        
        parts = []
        for key_node, value_node in self._values:
            key_code = key_node.to_code() if hasattr(key_node, 'to_code') else str(key_node)
            value_code = value_node.to_code() if hasattr(value_node, 'to_code') else str(value_node)
            parts.append(f"{key_code}: {value_code}")
        
        return "{" + ", ".join(parts) + "}"


class ASTPrint(ASTNode):
    """Print语句节点（Python 2兼容）"""
    
    def __init__(self, value: Optional['ASTNode'] = None, stream: Optional['ASTNode'] = None):
        super().__init__(NodeType.NODE_PRINT)
        self._values = []
        self._stream = stream
        self._eol = False
        
        if value is not None:
            self._values.append(value)
    
    def add_value(self, value: 'ASTNode'):
        """添加打印值"""
        self._values.append(value)
    
    def set_eol(self, eol: bool):
        """设置是否换行"""
        self._eol = eol
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    @property
    def stream(self) -> Optional['ASTNode']:
        return self._stream
    
    @property
    def eol(self) -> bool:
        return self._eol
    
    def to_code(self, indent_level=0):
        """生成print语句代码"""
        # 生成print函数调用
        args = []
        for value in self._values:
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
            args.append(value_code)
        
        if self._stream:
            stream_code = self._stream.to_code() if hasattr(self._stream, 'to_code') else str(self._stream)
            if not self._eol:
                return f"print({', '.join(args)}, file={stream_code})"
            else:
                return f"print({', '.join(args)}, file={stream_code}, end='')"
        else:
            if not self._eol:
                return f"print({', '.join(args)})"
            else:
                return f"print({', '.join(args)}, end='')"


class ASTConvert(ASTNode):
    """类型转换节点"""
    
    def __init__(self, name: 'ASTNode'):
        super().__init__(NodeType.NODE_CONVERT)
        self._name = name
    
    @property
    def name(self) -> 'ASTNode':
        return self._name
    
    def to_code(self, indent_level=0):
        """生成类型转换代码"""
        name_code = self._name.to_code() if hasattr(self._name, 'to_code') else str(self._name)
        return f"convert({name_code})"


class ASTMatchKeys(ASTNode):
    """模式匹配中的键匹配节点"""
    
    def __init__(self, keys: List['ASTNode']):
        super().__init__(NodeType.NODE_MATCH_KEYS)
        self._keys = keys if keys is not None else []
    
    @property
    def keys(self) -> List['ASTNode']:
        return self._keys
    
    def to_code(self, indent_level=0):
        """生成match keys代码"""
        if self._keys:
            key_codes = []
            for key in self._keys:
                if hasattr(key, 'to_code'):
                    key_codes.append(key.to_code())
                else:
                    key_codes.append(str(key))
            return "{" + ", ".join(key_codes) + "}"
        else:
            return "{}"


class ASTLocals(ASTNode):
    """局部变量节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_LOCALS)
    
    def to_code(self, indent_level=0):
        """生成locals()调用"""
        return "locals()"


# 添加一些常用的辅助函数
def create_comparison(left: 'ASTNode', right: 'ASTNode', op: int) -> 'ASTCompare':
    """创建比较表达式的辅助函数"""
    return ASTCompare(left, right, op)


def create_binary_op(left: 'ASTNode', right: 'ASTNode', op: int) -> 'ASTBinary':
    """创建二元操作表达式的辅助函数"""
    return ASTBinary(left, right, op)


def create_unary_op(operand: 'ASTNode', op: int) -> 'ASTUnary':
    """创建一元操作表达式的辅助函数"""
    return ASTUnary(operand, op)


def create_call(func: 'ASTNode', args: List['ASTNode'] = None, 
                keywords: List['ASTKeyword'] = None) -> 'ASTCall':
    """创建函数调用的辅助函数"""
    return ASTCall(func, args, keywords)


def create_name(name: str, ctx: int = 0) -> 'ASTName':
    """创建名称节点的辅助函数"""
    return ASTName(name, ctx)


def create_constant(value: Any) -> 'ASTObject':
    """创建常量节点的辅助函数"""
    return ASTObject(value)


# 增强的代码生成器
class CodeGenerator:
    """代码生成器类，用于生成格式良好的Python代码"""
    
    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self.line_prefix = " " * indent_size
    
    def generate_code(self, node: 'ASTNode', indent_level: int = 0) -> str:
        """生成代码"""
        if hasattr(node, 'to_code'):
            return node.to_code(indent_level)
        elif isinstance(node, str):
            return node
        else:
            return str(node)
    
    def generate_annotated_code(self, node: 'ASTNode', indent_level: int = 0) -> str:
        """生成带缩进的代码"""
        code = self.generate_code(node, indent_level)
        if indent_level > 0:
            return self.line_prefix * indent_level + code
        return code
    
    def generate_function_def(self, func_name: str, args: List[str], 
                              body: List[str], decorators: List[str] = None,
                              returns: str = None, indent_level: int = 0) -> str:
        """生成函数定义"""
        lines = []
        
        # 添加装饰器
        if decorators:
            for decorator in decorators:
                lines.append(self.line_prefix * indent_level + f"@{decorator}")
        
        # 函数签名
        args_str = ", ".join(args)
        func_def = f"def {func_name}({args_str})"
        
        if returns:
            func_def += f" -> {returns}"
        
        func_def += ":"
        lines.append(self.line_prefix * indent_level + func_def)
        
        # 函数体
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_class_def(self, class_name: str, bases: List[str] = None,
                          body: List[str] = None, decorators: List[str] = None,
                          metaclass: str = None, indent_level: int = 0) -> str:
        """生成类定义"""
        lines = []
        
        # 添加装饰器
        if decorators:
            for decorator in decorators:
                lines.append(self.line_prefix * indent_level + f"@{decorator}")
        
        # 类签名
        class_def = f"class {class_name}"
        
        # 基类
        if bases:
            bases_str = ", ".join(bases)
            class_def += f"({bases_str})"
        elif metaclass:
            class_def += f"(metaclass={metaclass})"
        
        class_def += ":"
        lines.append(self.line_prefix * indent_level + class_def)
        
        # 类体
        if body:
            for stmt in body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_import_statement(self, module: str, names: List[str] = None,
                                from_import: bool = True, alias: str = None,
                                indent_level: int = 0) -> str:
        """生成导入语句"""
        if from_import:
            if names:
                names_str = ", ".join(names)


class ASTTernary(ASTNode):
    """三元表达式节点（if-else表达式）"""
    
    def __init__(self, if_block: 'ASTNode', if_expr: 'ASTNode', else_expr: 'ASTNode'):
        super().__init__(NodeType.NODE_TERNARY)
        self._if_block = if_block  # 条件块
        self._if_expr = if_expr     # 真值表达式
        self._else_expr = else_expr # 假值表达式
    
    @property
    def if_block(self) -> 'ASTNode':
        return self._if_block
    
    @property
    def if_expr(self) -> 'ASTNode':
        return self._if_expr
    
    @property
    def else_expr(self) -> 'ASTNode':
        return self._else_expr
    
    def to_code(self, indent_level=0):
        """生成三元表达式代码"""
        if_expr_code = self._if_expr.to_code() if hasattr(self._if_expr, 'to_code') else str(self._if_expr)
        else_expr_code = self._else_expr.to_code() if hasattr(self._else_expr, 'to_code') else str(self._else_expr)
        
        # 获取条件代码（通常从if_block中提取）
        if hasattr(self._if_block, 'test'):
            condition = self._if_block.test
            if hasattr(condition, 'to_code'):
                condition_code = condition.to_code()
            else:
                condition_code = str(condition)
        else:
            condition_code = "condition"
        
        return f"{if_expr_code} if {condition_code} else {else_expr_code}"


class ASTAnnotatedVar(ASTNode):
    """注解变量节点"""
    
    def __init__(self, name: 'ASTNode', annotation: 'ASTNode'):
        super().__init__(NodeType.NODE_ANNOTATED_VAR)
        self._name = name
        self._annotation = annotation
    
    @property
    def name(self) -> 'ASTNode':
        return self._name
    
    @property
    def annotation(self) -> 'ASTNode':
        return self._annotation
    
    def to_code(self, indent_level=0):
        """生成注解变量代码"""
        name_code = self._name.to_code() if hasattr(self._name, 'to_code') else str(self._name)
        annotation_code = self._annotation.to_code() if hasattr(self._annotation, 'to_code') else str(self._annotation)
        return f"{name_code}: {annotation_code}"


class ASTChainStore(ASTNode):
    """链式存储节点"""
    
    def __init__(self, nodes: List['ASTNode'], src: 'ASTNode'):
        super().__init__(NodeType.NODE_CHAINSTORE)
        self._nodes = nodes if nodes is not None else []
        self._src = src
    
    @property
    def nodes(self) -> List['ASTNode']:
        return self._nodes
    
    @property
    def src(self) -> 'ASTNode':
        return self._src
    
    def to_code(self, indent_level=0):
        """生成链式存储代码"""
        if not self._nodes:
            return ""
        
        # 生成链式赋值
        src_code = self._src.to_code() if hasattr(self._src, 'to_code') else str(self._src)
        
        target_codes = []
        for node in self._nodes:
            target_code = node.to_code() if hasattr(node, 'to_code') else str(node)
            target_codes.append(target_code)
        
        targets = ", ".join(target_codes)
        return f"{targets} = {src_code}"


class ASTIs(ASTNode):
    """IS比较操作节点"""
    
    def __init__(self, left: 'ASTNode', right: 'ASTNode'):
        super().__init__(NodeType.NODE_COMPARE)
        self._left = left
        self._right = right
    
    @property
    def left(self) -> 'ASTNode':
        return self._left
    
    @property
    def right(self) -> 'ASTNode':
        return self._right
    
    def to_code(self, indent_level=0):
        """生成IS比较代码"""
        left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        return f"{left_code} is {right_code}"


class ASTIn(ASTNode):
    """IN比较操作节点"""
    
    def __init__(self, left: 'ASTNode', right: 'ASTNode'):
        super().__init__(NodeType.NODE_COMPARE)
        self._left = left
        self._right = right
    
    @property
    def left(self) -> 'ASTNode':
        return self._left
    
    @property
    def right(self) -> 'ASTNode':
        return self._right
    
    def to_code(self, indent_level=0):
        """生成IN比较代码"""
        left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        return f"{left_code} in {right_code}"


class ASTNotIn(ASTNode):
    """NOT IN比较操作节点"""
    
    def __init__(self, left: 'ASTNode', right: 'ASTNode'):
        super().__init__(NodeType.NODE_COMPARE)
        self._left = left
        self._right = right
    
    @property
    def left(self) -> 'ASTNode':
        return self._left
    
    @property
    def right(self) -> 'ASTNode':
        return self._right
    
    def to_code(self, indent_level=0):
        """生成NOT IN比较代码"""
        left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        return f"{left_code} not in {right_code}"


class ASTTryStar(ASTNode):
    """TryStar异常处理节点 (Python 3.11+)"""
    
    def __init__(self, body: 'ASTNodeList', handlers: List['ASTExceptHandler'], orelse: 'ASTNodeList' = None, finalbody: 'ASTNodeList' = None):
        super().__init__(NodeType.NODE_TRY)
        self._body = body
        self._handlers = handlers if handlers is not None else []
        self._orelse = orelse if orelse is not None else ASTNodeList([])
        self._finalbody = finalbody if finalbody is not None else ASTNodeList([])
    
    @property
    def body(self) -> 'ASTNodeList':
        return self._body
    
    @property
    def handlers(self) -> List['ASTExceptHandler']:
        return self._handlers
    
    @property
    def orelse(self) -> 'ASTNodeList':
        return self._orelse
    
    @property
    def finalbody(self) -> 'ASTNodeList':
        return self._finalbody
    
    def to_code(self, indent_level=0):
        """生成try*语句代码"""
        indent = "    " * (indent_level + 1)
        
        # 生成try*块
        code = "try:\n"
        code += self._body.to_code(indent_level)
        code += "\n"
        
        # 生成except*块
        for handler in self._handlers:
            if handler.exc_type:
                exc_type_code = handler.exc_type.to_code() if hasattr(handler.exc_type, 'to_code') else str(handler.exc_type)
                if handler.name:
                    code += f"{indent}except* {exc_type_code} as {handler.name}:\n"
                else:
                    code += f"{indent}except* {exc_type_code}:\n"
            else:
                code += f"{indent}except*:\n"
            
            if handler.body:
                code += handler.body.to_code(indent_level)
                code += "\n"
        
        # 生成else块
        if self._orelse and len(self._orelse) > 0:
            code += f"{indent}else:\n"
            code += self._orelse.to_code(indent_level)
            code += "\n"
        
        # 生成finally块
        if self._finalbody and len(self._finalbody) > 0:
            code += f"{indent}finally:\n"
            code += self._finalbody.to_code(indent_level)
            code += "\n"
        
        return code


class ASTTypeIgnore(ASTNode):
    """类型忽略节点"""
    
    def __init__(self, name: str = ""):
        super().__init__(NodeType.NODE_INVALID)  # 使用无效类型作为占位符
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    def to_code(self, indent_level=0):
        """生成类型忽略代码"""
        if self._name:
            return f"# type: ignore[{self._name}]"
        else:
            return "# type: ignore"


class ASTTypeComment(ASTNode):
    """类型注释节点"""
    
    def __init__(self, comment: str):
        super().__init__(NodeType.NODE_INVALID)  # 使用无效类型作为占位符
        self._comment = comment
    
    @property
    def comment(self) -> str:
        return self._comment
    
    def to_code(self, indent_level=0):
        """生成类型注释代码"""
        return f"# type: {self._comment}"


class ASTFormattedValue(ASTNode):
    """格式化值节点（用于f-string）"""
    
    def __init__(self, value: 'ASTNode', conversion: int = 0, format_spec: Optional['ASTNode'] = None):
        super().__init__(NodeType.NODE_FORMATTED_VALUE)
        self._value = value
        self._conversion = conversion  # 0=无, 1=str, 2=repr, 3=ascii
        self._format_spec = format_spec
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def conversion(self) -> int:
        return self._conversion
    
    @property
    def format_spec(self) -> Optional['ASTNode']:
        return self._format_spec
    
    def to_code(self, indent_level=0):
        """生成格式化值代码"""
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        
        # 添加转换说明符
        conversion_map = {1: "!s", 2: "!r", 3: "!a"}
        conversion_suffix = conversion_map.get(self._conversion, "")
        
        if self._format_spec:
            format_code = self._format_spec.to_code() if hasattr(self._format_spec, 'to_code') else str(self._format_spec)
            return f"{{{value_code}{conversion_suffix}:{format_code}}}"
        else:
            return f"{{{value_code}{conversion_suffix}}}"


class ASTJoinedStr(ASTNode):
    """连接的字符串节点（用于f-string）"""
    
    def __init__(self, values: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_JOINED_STR)
        self._values = values if values is not None else []
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    def to_code(self, indent_level=0):
        """生成f-string代码"""
        if not self._values:
            return '""'
        
        parts = []
        for value in self._values:
            # 检查是否是字符串（包括 PycString）
            is_string = False
            string_value = ""
            if isinstance(value, ASTObject):
                obj = value.value
                if isinstance(obj, str):
                    is_string = True
                    string_value = obj
                else:
                    # 检查是否是 PycString
                    from core.pyc_objects import PycString
                    if isinstance(obj, PycString):
                        is_string = True
                        string_value = obj.value
            
            if is_string:
                # 纯字符串部分
                parts.append(string_value)
            elif isinstance(value, ASTFormattedValue):
                # 格式化值部分
                parts.append(value.to_code())
            elif isinstance(value, ASTAttribute):
                # 属性访问，如 self.name
                parts.append(f"{{{value.to_code()}}}")
            else:
                # 其他表达式
                value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
                parts.append(f"{{{value_code}}}")
        
        # 如果有特殊字符或复杂结构，使用f-string
        if any('{' in part or '}' in part for part in parts if isinstance(part, str)):
            result = ''.join(parts)
            # 确保是有效的f-string
            return f'f"""{result}"""'
        else:
            return 'f"' + ''.join(parts) + '"'


class ASTConstMap(ASTNode):
    """常量映射节点"""
    
    def __init__(self, keys: 'ASTNode', values: List['ASTNode']):
        super().__init__(NodeType.NODE_CONST_MAP)
        self._keys = keys  # 通常是tuple
        self._values = values if values is not None else []
    
    @property
    def keys(self) -> 'ASTNode':
        return self._keys
    
    @property
    def values(self) -> List['ASTNode']:
        return self._values
    
    def to_code(self, indent_level=0):
        """生成字典创建代码"""
        if not self._values:
            return "{}"
        
        # 获取键（通常来自常量tuple）
        if isinstance(self._keys, ASTObject) and isinstance(self._keys.value, tuple):
            keys = self._keys.value
        elif hasattr(self._keys, 'values'):
            keys = self._keys.values
        else:
            # 如果无法获取键，生成占位符
            keys = [f"key_{i}" for i in range(len(self._values))]
        
        parts = []
        for i, (key, value) in enumerate(zip(keys, self._values)):
            key_code = key if isinstance(key, str) else str(key)
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
            parts.append(f"{key_code}: {value_code}")
        
        return "{" + ", ".join(parts) + "}"


class ASTAnnotatedVar(ASTNode):
    """注释变量节点"""
    
    def __init__(self, name: 'ASTNode', annotation: 'ASTNode'):
        super().__init__(NodeType.NODE_ANNOTATED_VAR)
        self._name = name
        self._annotation = annotation
    
    @property
    def name(self) -> 'ASTNode':
        return self._name
    
    @property
    def annotation(self) -> 'ASTNode':
        return self._annotation
    
    def to_code(self, indent_level=0):
        """生成注释变量代码"""
        name_code = self._name.to_code() if hasattr(self._name, 'to_code') else str(self._name)
        annotation_code = self._annotation.to_code() if hasattr(self._annotation, 'to_code') else str(self._annotation)
        return f"{name_code}: {annotation_code}"


class ASTLocals(ASTNode):
    """局部变量节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_LOCALS)
    
    def to_code(self, indent_level=0):
        """生成locals()调用"""
        return "locals()"


# 添加一些常用的辅助函数
def create_comparison(left: 'ASTNode', right: 'ASTNode', op: int) -> 'ASTCompare':
    """创建比较表达式的辅助函数"""
    return ASTCompare(left, right, op)


def create_binary_op(left: 'ASTNode', right: 'ASTNode', op: int) -> 'ASTBinary':
    """创建二元操作表达式的辅助函数"""
    return ASTBinary(left, right, op)


def create_unary_op(operand: 'ASTNode', op: int) -> 'ASTUnary':
    """创建一元操作表达式的辅助函数"""
    return ASTUnary(operand, op)


def create_call(func: 'ASTNode', args: List['ASTNode'] = None, 
                keywords: List['ASTKeyword'] = None) -> 'ASTCall':
    """创建函数调用的辅助函数"""
    return ASTCall(func, args, keywords)


def create_name(name: str, ctx: int = 0) -> 'ASTName':
    """创建名称节点的辅助函数"""
    return ASTName(name, ctx)


def create_constant(value: Any) -> 'ASTObject':
    """创建常量节点的辅助函数"""
    return ASTObject(value)


# 增强的代码生成器
class CodeGenerator:
    """代码生成器类，用于生成格式良好的Python代码"""
    
    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self.line_prefix = " " * indent_size
    
    def generate_code(self, node: 'ASTNode', indent_level: int = 0) -> str:
        """生成代码"""
        if hasattr(node, 'to_code'):
            return node.to_code(indent_level)
        elif isinstance(node, str):
            return node
        else:
            return str(node)
    
    def generate_annotated_code(self, node: 'ASTNode', indent_level: int = 0) -> str:
        """生成带缩进的代码"""
        code = self.generate_code(node, indent_level)
        if indent_level > 0:
            return self.line_prefix * indent_level + code
        return code
    
    def generate_function_def(self, func_name: str, args: List[str], 
                              body: List[str], decorators: List[str] = None,
                              returns: str = None, indent_level: int = 0) -> str:
        """生成函数定义"""
        lines = []
        
        # 添加装饰器
        if decorators:
            for decorator in decorators:
                lines.append(self.line_prefix * indent_level + f"@{decorator}")
        
        # 函数签名
        args_str = ", ".join(args)
        func_def = f"def {func_name}({args_str})"
        
        if returns:
            func_def += f" -> {returns}"
        
        func_def += ":"
        lines.append(self.line_prefix * indent_level + func_def)
        
        # 函数体
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_class_def(self, class_name: str, bases: List[str] = None,
                          body: List[str] = None, decorators: List[str] = None,
                          metaclass: str = None, indent_level: int = 0) -> str:
        """生成类定义"""
        lines = []
        
        # 添加装饰器
        if decorators:
            for decorator in decorators:
                lines.append(self.line_prefix * indent_level + f"@{decorator}")
        
        # 类签名
        class_def = f"class {class_name}"
        
        # 基类
        if bases:
            bases_str = ", ".join(bases)
            class_def += f"({bases_str})"
        elif metaclass:
            class_def += f"(metaclass={metaclass})"
        
        class_def += ":"
        lines.append(self.line_prefix * indent_level + class_def)
        
        # 类体
        if body:
            for stmt in body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_import_statement(self, module: str, names: List[str] = None,
                                from_import: bool = True, alias: str = None,
                                indent_level: int = 0) -> str:
        """生成导入语句"""
        if from_import:
            if names:
                names_str = ", ".join(names)
                if alias:
                    return self.line_prefix * indent_level + f"from {module} import {names_str} as {alias}"
                else:
                    return self.line_prefix * indent_level + f"from {module} import {names_str}"
            else:
                return self.line_prefix * indent_level + f"from {module} import *"
        else:
            if alias:
                return self.line_prefix * indent_level + f"import {module} as {alias}"
            else:
                return self.line_prefix * indent_level + f"import {module}"
    
    def generate_if_statement(self, condition: str, body: List[str],
                             elif_clauses: List[Tuple[str, List[str]]] = None,
                             else_body: List[str] = None, indent_level: int = 0) -> str:
        """生成if语句"""
        lines = []
        
        # 主if
        lines.append(self.line_prefix * indent_level + f"if {condition}:")
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # elif
        if elif_clauses:
            for elif_cond, elif_body in elif_clauses:
                lines.append(self.line_prefix * indent_level + f"elif {elif_cond}:")
                for stmt in elif_body:
                    lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # else
        if else_body:
            lines.append(self.line_prefix * indent_level + "else:")
            for stmt in else_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_for_statement(self, target: str, iterator: str, body: List[str],
                              else_body: List[str] = None, indent_level: int = 0,
                              is_async: bool = False) -> str:
        """生成for循环"""
        lines = []
        
        # for语句头
        async_prefix = "async " if is_async else ""
        lines.append(self.line_prefix * indent_level + f"{async_prefix}for {target} in {iterator}:")
        
        # 循环体
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # else
        if else_body:
            lines.append(self.line_prefix * indent_level + "else:")
            for stmt in else_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_while_statement(self, condition: str, body: List[str],
                               else_body: List[str] = None, indent_level: int = 0) -> str:
        """生成while循环"""
        lines = []
        
        # while语句头
        lines.append(self.line_prefix * indent_level + f"while {condition}:")
        
        # 循环体
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # else
        if else_body:
            lines.append(self.line_prefix * indent_level + "else:")
            for stmt in else_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_try_statement(self, body: List[str], handlers: List[Tuple[str, str, List[str]]],
                             else_body: List[str] = None, finally_body: List[str] = None,
                             indent_level: int = 0) -> str:
        """生成try语句"""
        lines = []
        
        # try
        lines.append(self.line_prefix * indent_level + "try:")
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # except
        for exc_type, exc_var, exc_body in handlers:
            if exc_var:
                handler_def = f"except {exc_type} as {exc_var}:"
            else:
                handler_def = f"except {exc_type}:"
            lines.append(self.line_prefix * indent_level + handler_def)
            for stmt in exc_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # else
        if else_body:
            lines.append(self.line_prefix * indent_level + "else:")
            for stmt in else_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        # finally
        if finally_body:
            lines.append(self.line_prefix * indent_level + "finally:")
            for stmt in finally_body:
                lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_with_statement(self, items: List[Tuple[str, str]], body: List[str],
                               indent_level: int = 0, is_async: bool = False) -> str:
        """生成with语句"""
        lines = []
        
        # with语句头
        items_str = ", ".join([f"{expr} as {var}" if var else expr for expr, var in items])
        async_prefix = "async " if is_async else ""
        lines.append(self.line_prefix * indent_level + f"{async_prefix}with {items_str}:")
        
        # with体
        for stmt in body:
            lines.append(self.line_prefix * (indent_level + 1) + stmt)
        
        return "\n".join(lines)
    
    def generate_comment(self, comment: str, indent_level: int = 0) -> str:
        """生成注释"""
        lines = comment.split('\n')
        return "\n".join([self.line_prefix * indent_level + f"# {line}" for line in lines])
    
    def generate_blank_line(self) -> str:
        """生成空行"""
        return ""


# 导出默认的代码生成器实例
default_generator = CodeGenerator()


# 增强的AST节点方法
def enhance_ast_nodes():
    """增强AST节点类的方法"""
    # 为ASTNode基类添加一些通用方法
    original_ast_node_to_code = ASTNode.to_code if hasattr(ASTNode, 'to_code') else lambda self, indent_level=0: "pass"
    
    def enhanced_to_code(self, indent_level=0):
        """增强的to_code方法"""
        # 首先尝试原始方法
        try:
            return original_ast_node_to_code(self, indent_level)
        except:
            pass
        
        # 如果原始方法失败，返回默认实现
        return f"# {self.__class__.__name__}"
    
    # 为所有AST节点类添加代码生成辅助方法
    ast_node_classes = [
        ASTName, ASTObject, ASTBinary, ASTUnary, ASTCompare, ASTCall,
        ASTFunctionDef, ASTClassDef, ASTIf, ASTFor, ASTWhile, ASTTry,
        ASTImport, ASTImportFrom, ASTReturn, ASTBreak, ASTContinue,
        ASTPass, ASTRaise, ASTWith, ASTBlock
    ]
    
    for cls in ast_node_classes:
        if hasattr(cls, 'to_code'):
            # 保持原有的to_code方法
            pass
        else:
            # 添加默认的to_code方法
            def default_to_code(self, indent_level=0):
                return f"# {self.__class__.__name__}"
            cls.to_code = default_to_code


# 调用增强函数
enhance_ast_nodes()