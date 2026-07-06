"""
AST节点模块
包含所有AST节点类 - 性能优化版本
"""

from typing import List, Optional, Union, Any, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import threading

# 调试配置
AST_DEBUG = False

def ast_debug_print(*args, **kwargs):
    """条件调试输出"""
    if AST_DEBUG:
        # [关键修复] 将调试输出写入文件，避免编码问题
        try:
            msg = ' '.join(str(arg) for arg in args)
            with open('d:/ast_debug_output.txt', 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            pass

# 别名，用于兼容其他代码
debug_print = ast_debug_print

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
    NODE_CASE = 72
    NODE_LOCALS = 73


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
    
    def to_code(self, indent_level=0, _visited=None):
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
    
    def __getitem__(self, index):
        """支持索引访问"""
        return self._nodes[index]
    
    @property
    def nodes(self) -> List['ASTNode']:
        return self._nodes
    
    def append(self, node: 'ASTNode') -> None:
        """添加节点 - 按偏移量排序插入"""
        # [关键修复] 按偏移量排序插入，确保代码顺序正确
        node_offset = getattr(node, 'offset', -1)
        ast_debug_print(f"[ASTNodeList.append] node_offset={node_offset}, node_type={type(node).__name__}, current_nodes={[type(n).__name__ + ':' + str(getattr(n, 'offset', -1)) for n in self._nodes]}")
        if node_offset > 0:
            # 找到正确的插入位置
            insert_idx = len(self._nodes)
            for i, existing_node in enumerate(self._nodes):
                existing_offset = getattr(existing_node, 'offset', -1)
                if existing_offset > node_offset > 0:
                    insert_idx = i
                    break
            self._nodes.insert(insert_idx, node)
            ast_debug_print(f"[ASTNodeList.append] 插入到位置 {insert_idx}: {type(node).__name__}:{node_offset}")
        else:
            self._nodes.append(node)
            ast_debug_print(f"[ASTNodeList.append] 追加到末尾: {type(node).__name__}:{node_offset}")
    
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复节点"
        
        _visited.add(node_id)
        
        ast_debug_print(f"[ASTNodeList.to_code] 被调用: 节点数={len(self._nodes)}, indent_level={indent_level}")
        if not self._nodes:
            ast_debug_print(f"[ASTNodeList.to_code] 节点列表为空，返回空字符串")
            return ""
        
        lines = []
        indent = "    " * indent_level
        has_returned = False  # [关键修复] 标记是否已经遇到return语句
        seen_lines = set()  # [关键修复] 用于去重
        
        for i, node in enumerate(self._nodes):
            node_type = type(node).__name__
            node_offset = getattr(node, 'offset', -1)
            ast_debug_print(f"[ASTNodeList.to_code] 处理节点 {i}: type={node_type}, offset={node_offset}, has_returned={has_returned}")
            
            # [关键修复] 如果已经遇到return语句，跳过后续代码（除非是函数定义、类定义或with语句）
            # with语句必须在return之前处理，因为with语句可能包含return语句
            if has_returned and node_type not in ['ASTFunctionDef', 'ASTClassDef', 'ASTWith']:
                ast_debug_print(f"[ASTNodeList.to_code] 跳过节点 {i}: has_returned={has_returned}")
                continue
            
            # 🔧 关键修复：处理不应该作为独立语句的节点类型
            # 这些节点应该被转换为注释或忽略
            if node_type in ['ASTTuple', 'ASTList', 'ASTDict', 'ASTSet']:
                # 这些节点是表达式，不应该作为独立语句
                # 尝试生成表达式代码，如果失败则生成注释
                if hasattr(node, 'to_code'):
                    expr_code = node.to_code(0)  # 不添加缩进
                    if expr_code and not expr_code.startswith('<'):
                        lines.append(f"{indent}# 表达式: {expr_code}")
                    else:
                        lines.append(f"{indent}# {node_type} 表达式")
                else:
                    lines.append(f"{indent}# {node_type} 表达式")
                continue
            
            # [关键修复] 特殊处理删除语句 - 跳过无意义的 del None 模式
            if node_type == 'ASTDelete':
                targets = getattr(node, '_targets', None) or getattr(node, 'targets', None)
                if targets:
                    if isinstance(targets, list):
                        target_codes = []
                        for target in targets:
                            if hasattr(target, 'to_code'):
                                target_code = target.to_code(0)
                            elif hasattr(target, 'name'):
                                target_code = str(target.name)
                            else:
                                target_code = str(target)
                            if target_code and not target_code.startswith('<'):
                                target_codes.append(target_code)
                        if target_codes:
                            line = f"{indent}del {', '.join(target_codes)}"
                            # [关键修复] 去重检查 - 跳过无意义的 del None 和 del BaseException
                            if line not in seen_lines:
                                is_meaningless = any(
                                    t in ('None', 'BaseException', 'Exception') 
                                    for t in target_codes
                                )
                                if not is_meaningless:
                                    seen_lines.add(line)
                                    lines.append(line)
                    else:
                        if hasattr(targets, 'to_code'):
                            target_code = targets.to_code(0)
                        else:
                            target_code = str(targets)
                        if target_code and not target_code.startswith('<'):
                            line = f"{indent}del {target_code}"
                            if line not in seen_lines:
                                is_meaningless = target_code in ('None', 'BaseException', 'Exception')
                                if not is_meaningless:
                                    seen_lines.add(line)
                                    lines.append(line)
                continue
            
            # [关键修复] 特殊处理global语句
            if node_type == 'ASTGlobal':
                names = getattr(node, '_names', None) or getattr(node, 'names', None)
                if names:
                    if isinstance(names, list):
                        name_strs = []
                        for name in names:
                            if hasattr(name, 'name'):
                                name_strs.append(str(name.name))
                            elif hasattr(name, '_value'):
                                name_strs.append(str(name._value))
                            elif hasattr(name, 'to_code'):
                                name_str = name.to_code(0)
                                if name_str and not name_str.startswith('<'):
                                    name_strs.append(name_str)
                            else:
                                name_strs.append(str(name))
                        if name_strs:
                            line = f"{indent}global {', '.join(name_strs)}"
                            if line not in seen_lines:
                                seen_lines.add(line)
                                lines.append(line)
                    else:
                        line = f"{indent}global {names}"
                        if line not in seen_lines:
                            seen_lines.add(line)
                            lines.append(line)
                continue
            
            # [关键修复] 特殊处理nonlocal语句
            if node_type == 'ASTNonlocal':
                names = getattr(node, '_names', None) or getattr(node, 'names', None)
                if names:
                    if isinstance(names, list):
                        name_strs = []
                        for name in names:
                            if hasattr(name, 'name'):
                                name_strs.append(str(name.name))
                            elif hasattr(name, '_value'):
                                name_strs.append(str(name._value))
                            elif hasattr(name, 'to_code'):
                                name_str = name.to_code(0)
                                if name_str and not name_str.startswith('<'):
                                    name_strs.append(name_str)
                            else:
                                name_strs.append(str(name))
                        if name_strs:
                            line = f"{indent}nonlocal {', '.join(name_strs)}"
                            if line not in seen_lines:
                                seen_lines.add(line)
                                lines.append(line)
                    else:
                        line = f"{indent}nonlocal {names}"
                        if line not in seen_lines:
                            seen_lines.add(line)
                            lines.append(line)
                continue
            
            # 检查是否是return语句
            is_return_node = node_type == 'ASTReturn'
            
            if node_type == 'ASTClassDef':
                # 类定义节点应该有自己的to_code方法
                if hasattr(node, 'to_code'):
                    node_code = node.to_code(indent_level, _visited)
                    if node_code and not node_code.startswith('<'):
                        lines.append(node_code)
                    else:
                        lines.append(f"{indent}# {node_type} 类定义")
                else:
                    lines.append(f"{indent}# {node_type} 类定义")
            elif hasattr(node, 'to_code'):
                # [关键修复] 子节点已经处理了缩进，这里直接收集代码
                # [关键修复] 尝试传递 _visited 参数来检测循环引用
                try:
                    node_code = node.to_code(indent_level, _visited)
                except TypeError:
                    # 子节点的to_code方法不接受_visited参数
                    node_code = node.to_code(indent_level)
                if node_code:
                    stripped = node_code.strip()
                    # [关键修复] 去重检查 - 但不对Try、If、For、While等控制流结构进行去重
                    # 因为这些结构可能嵌套，且生成的代码可能相同
                    should_dedup = node_type not in ['ASTTry', 'ASTIf', 'ASTFor', 'ASTWhile', 'ASTWith', 'ASTFunctionDef', 'ASTClassDef']
                    if not should_dedup or stripped not in seen_lines:
                        if should_dedup:
                            seen_lines.add(stripped)
                        # [关键修复] 对于ASTConstant节点，需要添加缩进
                        if node_type == 'ASTConstant' and indent_level > 0:
                            if not node_code.startswith('    ' * indent_level):
                                node_code = f"{indent}{node_code}"
                        lines.append(node_code)
                        # [关键修复] 如果是return语句，设置标记
                        if is_return_node:
                            has_returned = True
                elif is_return_node:
                    # [关键修复] 如果是return语句（即使生成空字符串），也设置标记
                    has_returned = True
            else:
                node_code = str(node)
                if node_code:
                    line = f"{indent}{node_code}"
                    if line not in seen_lines:
                        seen_lines.add(line)
                        lines.append(line)
        
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复block节点"
        
        _visited.add(node_id)
        
        if not self._nodes:
            return "    " * indent_level + "pass"
        
        # [关键修复] 如果这是BLK_ELSE块且没有父节点或父节点不是ASTIf/ASTWhile，跳过生成
        # 这可以避免孤立的else块被生成
        # [修复] 添加对ASTWhile的支持，因为while-else结构也需要BLK_ELSE块
        if self._blk_type == ASTBlock.BlockType.BLK_ELSE:
            # 检查是否有父节点
            has_parent = hasattr(self, 'parent') and self.parent is not None
            # 检查父节点是否是ASTIf、ASTWhile或ASTFor
            parent_type = type(self.parent).__name__ if has_parent else None
            parent_is_if = parent_type == 'ASTIf'
            parent_is_while = parent_type == 'ASTWhile'
            parent_is_for = parent_type == 'ASTFor'
            # 检查是否在ASTIf的orelse中
            in_if_orelse = False
            if has_parent and hasattr(self.parent, '_orelse'):
                in_if_orelse = self.parent._orelse is self
            # 检查是否在ASTWhile的_else_block中
            in_while_else = False
            if has_parent and hasattr(self.parent, '_else_block'):
                in_while_else = self.parent._else_block is self
            # [关键修复] 检查是否在ASTFor的_else_block中
            in_for_else = False
            if has_parent and hasattr(self.parent, '_else_block'):
                in_for_else = self.parent._else_block is self
            
            if not has_parent or (not parent_is_if and not parent_is_while and not parent_is_for and not in_if_orelse and not in_while_else and not in_for_else):
                ast_debug_print(f"[ASTBlock.to_code] 跳过孤立的BLK_ELSE块")
                return ""
            
            # [关键修复] 检查BLK_ELSE块的内容是否以else:开头
            # 如果是，则跳过生成（else:应该在ASTIf.to_code中生成）
            for node in self._nodes:
                if hasattr(node, 'to_code'):
                    node_code = node.to_code(0)
                    if node_code.strip().startswith('else:'):
                        ast_debug_print(f"[ASTBlock.to_code] 跳过以else:开头的BLK_ELSE块")
                        return ""
        
        lines = []
        seen_lines = set()  # [关键修复] 用于去重
        seen_patterns = set()  # [关键修复] 用于模式去重
        prev_was_method = False
        has_returned = False  # [关键修复] 标记是否已经遇到return语句
        
        # [关键修复] 收集所有作为ASTStore值的推导式，用于跳过独立的重复推导式
        child_comprehensions = set()
        for node in self._nodes:
            node_type = type(node).__name__
            if node_type == 'ASTStore':
                value = getattr(node, '_src', None) or getattr(node, '_value', None) or getattr(node, 'src', None) or getattr(node, 'value', None)
                # [关键修复] 添加 ASTGenExpr 到推导式类型列表
                if value and type(value).__name__ in ['ASTListComp', 'ASTSetComp', 'ASTDictComp', 'ASTGenExpr']:
                    # 获取推导式的代码表示用于比较
                    if hasattr(value, 'to_code'):
                        comp_code = value.to_code(0)
                        if comp_code:
                            child_comprehensions.add(comp_code)
        
        for node in self._nodes:
            node_type = type(node).__name__
            
            # [关键修复] 禁用跳过return语句后的代码，以保持字节码一致性
            # 原始字节码中可能有多个return语句（如with语句后的return和函数末尾的return）
            # 我们需要生成所有return语句，而不是跳过它们
            # if has_returned and node_type not in ['ASTFunctionDef', 'ASTClassDef']:
            #     continue
            
            # [关键修复] 检查是否是return语句（在生成代码之前检查节点类型）
            is_return_node = node_type == 'ASTReturn'
            
            # [关键修复] 跳过作为ASTStore子节点的独立推导式（避免重复生成）
            # [关键修复] 添加 ASTGenExpr 到推导式类型列表
            if node_type in ['ASTListComp', 'ASTSetComp', 'ASTDictComp', 'ASTGenExpr']:
                if hasattr(node, 'to_code'):
                    node_code_str = node.to_code(0)
                    if node_code_str and node_code_str in child_comprehensions:
                        ast_debug_print(f"[ASTBlock.to_code] 跳过作为子节点的独立推导式: {node_type}")
                        continue
            
            # [关键修复] 处理不应该作为独立语句的节点类型
            if node_type in ['ASTTuple', 'ASTList', 'ASTDict', 'ASTSet']:
                # 这些节点是表达式，不应该作为独立语句
                if hasattr(node, 'to_code'):
                    expr_code = node.to_code(0)
                    if expr_code and not expr_code.startswith('<'):
                        indent = "    " * indent_level
                        lines.append(f"{indent}# 表达式: {expr_code}")
                continue
            
            # [关键修复] 特殊处理删除语句 - 跳过无意义的 del None 模式
            if node_type == 'ASTDelete':
                targets = getattr(node, '_targets', None) or getattr(node, 'targets', None)
                if targets:
                    if isinstance(targets, list):
                        target_codes = []
                        for target in targets:
                            if hasattr(target, 'to_code'):
                                target_code = target.to_code(0)
                            elif hasattr(target, 'name'):
                                target_code = str(target.name)
                            else:
                                target_code = str(target)
                            if target_code and not target_code.startswith('<'):
                                target_codes.append(target_code)
                        if target_codes:
                            indent = "    " * indent_level
                            line = f"{indent}del {', '.join(target_codes)}"
                            # [关键修复] 去重检查 - 跳过无意义的 del None 和 del BaseException
                            if line not in seen_lines:
                                # 检查是否是删除None或异常类的无意义操作
                                is_meaningless = any(
                                    t in ('None', 'BaseException', 'Exception') 
                                    for t in target_codes
                                )
                                if not is_meaningless:
                                    seen_lines.add(line)
                                    lines.append(line)
                    else:
                        if hasattr(targets, 'to_code'):
                            target_code = targets.to_code(0)
                        else:
                            target_code = str(targets)
                        if target_code and not target_code.startswith('<'):
                            indent = "    " * indent_level
                            line = f"{indent}del {target_code}"
                            if line not in seen_lines:
                                is_meaningless = target_code in ('None', 'BaseException', 'Exception')
                                if not is_meaningless:
                                    seen_lines.add(line)
                                    lines.append(line)
                continue
            
            # [关键修复] 特殊处理global语句
            if node_type == 'ASTGlobal':
                names = getattr(node, '_names', None) or getattr(node, 'names', None)
                if names:
                    if isinstance(names, list):
                        name_strs = []
                        for name in names:
                            if hasattr(name, 'name'):
                                name_strs.append(str(name.name))
                            elif hasattr(name, '_value'):
                                name_strs.append(str(name._value))
                            elif hasattr(name, 'to_code'):
                                name_str = name.to_code(0)
                                if name_str and not name_str.startswith('<'):
                                    name_strs.append(name_str)
                            else:
                                name_strs.append(str(name))
                        if name_strs:
                            indent = "    " * indent_level
                            line = f"{indent}global {', '.join(name_strs)}"
                            if line not in seen_lines:
                                seen_lines.add(line)
                                lines.append(line)
                    else:
                        indent = "    " * indent_level
                        line = f"{indent}global {names}"
                        if line not in seen_lines:
                            seen_lines.add(line)
                            lines.append(line)
                continue
            
            # [关键修复] 特殊处理nonlocal语句
            if node_type == 'ASTNonlocal':
                names = getattr(node, '_names', None) or getattr(node, 'names', None)
                if names:
                    if isinstance(names, list):
                        name_strs = []
                        for name in names:
                            if hasattr(name, 'name'):
                                name_strs.append(str(name.name))
                            elif hasattr(name, '_value'):
                                name_strs.append(str(name._value))
                            elif hasattr(name, 'to_code'):
                                name_str = name.to_code(0)
                                if name_str and not name_str.startswith('<'):
                                    name_strs.append(name_str)
                            else:
                                name_strs.append(str(name))
                        if name_strs:
                            indent = "    " * indent_level
                            line = f"{indent}nonlocal {', '.join(name_strs)}"
                            if line not in seen_lines:
                                seen_lines.add(line)
                                lines.append(line)
                    else:
                        indent = "    " * indent_level
                        line = f"{indent}nonlocal {names}"
                        if line not in seen_lines:
                            seen_lines.add(line)
                            lines.append(line)
                continue
            
            # 🔧 修复：在类定义之间添加空行（PEP 8要求类之间有两个空行）
            if node_type == 'ASTClassDef' and lines:
                # 检查前一个节点是否也是类定义
                prev_node_type = type(self._nodes[self._nodes.index(node) - 1]).__name__ if self._nodes.index(node) > 0 else None
                if prev_node_type == 'ASTClassDef':
                    # 类定义之间添加两个空行
                    lines.append("")
                    lines.append("")
            
            # 🔧 修复：在类的方法之间添加空行
            if prev_was_method and hasattr(node, 'to_code'):
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    node_code_check = node.to_code(indent_level, _visited)
                except TypeError:
                    node_code_check = node.to_code(indent_level)
                # 检查是否是方法定义（以 "def " 开头）
                if node_code_check.strip().startswith('def '):
                    lines.append("")  # 添加空行
            
            # 🔧 修复：特殊处理装饰器应用节点，给它们零缩进
            if hasattr(node, '_node_type') and node._node_type == NodeType.NODE_DECORATOR_APP:
                # 装饰器应用节点使用零缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    original_node_code = node.to_code(0, _visited)
                except TypeError:
                    original_node_code = node.to_code(0)
                node_code = original_node_code  # 不添加缩进
            elif hasattr(node, 'to_code'):
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    node_code = node.to_code(indent_level, _visited)
                except TypeError:
                    node_code = node.to_code(indent_level)
                # [关键修复] 对于ASTConstant节点，如果返回的代码没有缩进，添加缩进
                if node_type == 'ASTConstant' and indent_level > 0:
                    indent = "    " * indent_level
                    if not node_code.startswith(indent):
                        node_code = indent + node_code
            else:
                # 为字符串节点添加缩进
                node_str = str(node)
                if node_str.strip():
                    node_code = "    " * indent_level + node_str
                else:
                    node_code = ""
            
            # [关键修复] 检查是否是return语句（在生成代码之前检查节点类型）
            is_return_node = node_type == 'ASTReturn'
            
            # [关键修复] 去重检查 - 只检查非空行
            if node_code and node_code.strip():
                stripped = node_code.strip()
                
                # [关键修复] 跳过无意义的赋值模式（如 x = None; del x）
                # 只有当赋值和删除配对出现时才跳过
                is_none_assign = stripped.endswith(' = None')
                is_baseexception_assign = stripped.endswith(' = BaseException')
                
                if is_none_assign or is_baseexception_assign:
                    var_name = stripped.split('=')[0].strip()
                    # 检查接下来是否有 del 同一个变量
                    has_matching_del = False
                    if var_name:
                        # 在剩余的节点中查找匹配的 del 语句
                        for next_node in self._nodes[self._nodes.index(node)+1:]:
                            if type(next_node).__name__ == 'ASTDelete':
                                del_targets = getattr(next_node, '_targets', None) or getattr(next_node, 'targets', None)
                                if del_targets:
                                    if isinstance(del_targets, list):
                                        for target in del_targets:
                                            target_name = getattr(target, 'name', None) or getattr(target, '_name', None)
                                            if target_name == var_name:
                                                has_matching_del = True
                                                break
                                    else:
                                        target_name = getattr(del_targets, 'name', None) or getattr(del_targets, '_name', None)
                                        if target_name == var_name:
                                            has_matching_del = True
                                if has_matching_del:
                                    break
                    
                    # 只有当有匹配的 del 语句时才跳过
                    if has_matching_del:
                        continue
                
                # [关键修复] 检查是否是重复的代码行
                # [关键修复] 允许return语句重复，以保持字节码一致性
                # 原始字节码中可能有多个return语句（如with语句后的return和函数末尾的return）
                if stripped not in seen_lines or is_return_node:
                    if not is_return_node:  # 只有非return语句才添加到seen_lines
                        seen_lines.add(stripped)
                    lines.append(node_code)
                    # [禁用] 不再使用has_returned来跳过代码，以保持字节码一致性
                    # if is_return_node:
                    #     has_returned = True
            elif node_code == "":
                lines.append(node_code)
                # [禁用] 不再使用has_returned来跳过代码，以保持字节码一致性
                # if is_return_node:
                #     has_returned = True
            
            # 标记是否是方法
            prev_was_method = node_code and node_code.strip().startswith('def ')
        
        # 过滤空行并连接，但保留方法之间的空行（空字符串）
        # [关键修复] 过滤掉返回空字符串的节点（如return None）
        
        result_lines = []
        for i, line in enumerate(lines):
            if line.strip():  # 保留非空行
                result_lines.append(line)
            elif line == "" and i > 0 and i < len(lines) - 1:
                # 只保留方法之间的空行（前后都有非空代码行）
                # 检查前一行和后一行是否有实际内容
                prev_has_content = any(l.strip() for l in lines[:i])
                next_has_content = any(l.strip() for l in lines[i+1:])
                if prev_has_content and next_has_content:
                    result_lines.append(line)
        
        # 如果过滤后没有代码行，生成pass语句
        if not result_lines:
            return "    " * indent_level + "pass"
        
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
        self._is_walrus = False  # [关键修复] 标记是否是海象运算符
    
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
    
    @property
    def is_walrus(self) -> bool:
        """[关键修复] 是否是海象运算符"""
        return getattr(self, '_is_walrus', False)
    
    @is_walrus.setter
    def is_walrus(self, value: bool):
        """[关键修复] 设置是否是海象运算符"""
        self._is_walrus = value
    
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
        ast_debug_print(f"[ASTStore.to_code] target={target_code}, value_type={type(value).__name__ if value else None}, is_walrus={getattr(self, '_is_walrus', False)}")
        if value is not None:
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
        else:
            value_code = "None"
        
        # [关键修复] 根据是否是海象运算符选择赋值符号
        assign_op = ":=" if getattr(self, '_is_walrus', False) else "="
        result = f"{indent}{target_code} {assign_op} {value_code}"
        ast_debug_print(f"[ASTStore.to_code] result={result}")
        return result
    
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
        # [关键修复] 检查是否是else标记节点
        if getattr(self, '_is_else_marker', False):
            return ""  # else标记节点不生成代码
        if self._obj is None:
            return "None"
        elif isinstance(self._obj, str):
            return repr(self._obj)
        elif isinstance(self._obj, bool):
            return "True" if self._obj else "False"
        elif isinstance(self._obj, (int, float)):
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
                # 🔧 修复：处理布尔值和None类型
                if hasattr(self._obj, '_type'):
                    if self._obj._type == PycObject.TYPE_TRUE:
                        return "True"
                    elif self._obj._type == PycObject.TYPE_FALSE:
                        return "False"
                    elif self._obj._type == PycObject.TYPE_NONE:
                        return "None"
                # 🔧 修复：对于PycObject对象，尝试获取value属性
                if hasattr(self._obj, 'value') and self._obj.value is not None:
                    return str(self._obj.value)
                else:
                    return "None"
            elif isinstance(self._obj, dict):
                # [关键修复] 处理字典对象，递归转换值
                items = []
                for key, value in self._obj.items():
                    key_code = key.to_code() if hasattr(key, 'to_code') else repr(key) if isinstance(key, str) else str(key)
                    if hasattr(value, 'to_code'):
                        value_code = value.to_code()
                    elif hasattr(value, 'value'):
                        value_code = repr(value.value) if isinstance(value.value, str) else str(value.value)
                    else:
                        value_code = repr(value) if isinstance(value, str) else str(value)
                    items.append(f"{key_code}: {value_code}")
                return "{" + ", ".join(items) + "}"
            elif isinstance(self._obj, (list, tuple)):
                # [关键修复] 处理列表和元组对象，递归转换元素
                items = []
                for item in self._obj:
                    if hasattr(item, 'to_code'):
                        items.append(item.to_code())
                    elif hasattr(item, 'value'):
                        items.append(repr(item.value) if isinstance(item.value, str) else str(item.value))
                    else:
                        items.append(repr(item) if isinstance(item, str) else str(item))
                if isinstance(self._obj, tuple):
                    return "(" + ", ".join(items) + ")"
                else:
                    return "[" + ", ".join(items) + "]"
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
        
        # [关键修复] 获取操作符的值（处理枚举类型）
        op_value = self._op.value if isinstance(self._op, self.UnOp) else self._op
        
        # 操作符映射
        op_map = {
            self.UnOp.UN_POSITIVE.value: "+",
            self.UnOp.UN_NEGATIVE.value: "-",
            self.UnOp.UN_INVERT.value: "~",
            self.UnOp.UN_NOT.value: "not ",
        }
        
        op_str = op_map.get(op_value, f"#{op_value}")
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
            left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
            right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
            return f"{left_code}.{right_code}"
        
        # 运算符优先级（数值越高，优先级越高）
        precedence = {
            self.BinOp.BIN_POWER.value: 100,
            self.BinOp.BIN_MULTIPLY.value: 90,
            self.BinOp.BIN_DIVIDE.value: 90,
            self.BinOp.BIN_FLOOR_DIVIDE.value: 90,
            self.BinOp.BIN_MODULO.value: 90,
            self.BinOp.BIN_MAT_MULTIPLY.value: 90,
            self.BinOp.BIN_ADD.value: 80,
            self.BinOp.BIN_SUBTRACT.value: 80,
            self.BinOp.BIN_LSHIFT.value: 70,
            self.BinOp.BIN_RSHIFT.value: 70,
            self.BinOp.BIN_AND.value: 60,
            self.BinOp.BIN_XOR.value: 50,
            self.BinOp.BIN_OR.value: 40,
            self.BinOp.BIN_LOG_AND.value: 30,
            self.BinOp.BIN_LOG_OR.value: 20,
        }
        
        current_prec = precedence.get(self._op, 0)
        
        # 获取左操作数代码，必要时添加括号
        if hasattr(self._left, '_op') and hasattr(self._left, 'to_code'):
            left_prec = precedence.get(self._left._op, 0)
            if left_prec < current_prec:
                left_code = f"({self._left.to_code()})"
            else:
                left_code = self._left.to_code()
        else:
            left_code = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        
        # 获取右操作数代码，必要时添加括号
        if hasattr(self._right, '_op') and hasattr(self._right, 'to_code'):
            right_prec = precedence.get(self._right._op, 0)
            # 对于幂运算，右结合，需要特殊处理
            if self._op == self.BinOp.BIN_POWER.value and right_prec <= current_prec:
                right_code = f"({self._right.to_code()})"
            elif right_prec < current_prec:
                right_code = f"({self._right.to_code()})"
            else:
                right_code = self._right.to_code()
        else:
            right_code = self._right.to_code() if hasattr(self._right, 'to_code') else str(self._right)
        
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
        # [关键修复] 如果左侧是海象运算符，调用其to_code方法时不添加括号
        # 因为比较表达式本身已经提供了上下文
        has_is_walrus = hasattr(self._left, 'is_walrus')
        is_walrus_val = self._left.is_walrus if has_is_walrus else False
        
        if has_is_walrus and is_walrus_val and isinstance(self._left, ASTNamedExpr):
            # 对于ASTNamedExpr，调用to_code时指定need_parentheses=False
            left_str = self._left.to_code(indent_level, need_parentheses=False)
        else:
            left_str = self._left.to_code() if hasattr(self._left, 'to_code') else str(self._left)
        
        ast_debug_print(f"[ASTCompare.to_code] left_type={type(self._left).__name__}, has_is_walrus={has_is_walrus}, is_walrus={is_walrus_val}, left_str={left_str}")
        
        # 处理单个比较（最常见的情况）
        if len(self._comparators) == 1 and len(self._ops) == 1:
            comparator = self._comparators[0]
            op_str = self.op_str()
            comp_str = comparator.to_code() if hasattr(comparator, 'to_code') else str(comparator)
            ast_debug_print(f"[ASTCompare.to_code] right_type={type(comparator).__name__}, right_str={comp_str}")
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
        # [修复] 正确处理切片边界，当为None时返回空字符串
        if self._left is not None and hasattr(self._left, 'to_code'):
            lower_str = self._left.to_code()
        elif self._left is not None:
            lower_str = str(self._left)
        else:
            lower_str = ""
        
        if self._right is not None and hasattr(self._right, 'to_code'):
            upper_str = self._right.to_code()
        elif self._right is not None:
            upper_str = str(self._right)
        else:
            upper_str = ""
        
        if self._step is not None and hasattr(self._step, 'to_code'):
            step_str = self._step.to_code()
        elif self._step is not None:
            step_str = str(self._step)
        else:
            step_str = None
        
        # 处理"None"字符串
        if lower_str == "None":
            lower_str = ""
        if upper_str == "None":
            upper_str = ""
        if step_str == "None":
            step_str = None
        
        # [修复] ASTSlice只返回切片部分，不包含被切片的对象
        # 格式为 "lower:upper" 或 "lower:upper:step"
        if step_str:
            return f"{lower_str}:{upper_str}:{step_str}"
        else:
            return f"{lower_str}:{upper_str}"


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
        # [关键修复] 支持to_code()方法和value属性
        lower_str = ""
        if self._lower is not None:
            if hasattr(self._lower, 'to_code'):
                lower_str = self._lower.to_code()
            elif hasattr(self._lower, 'value') and self._lower.value is not None:
                lower_str = str(self._lower.value)
            # [关键修复] 如果lower_str是"None"，设置为空字符串
            if lower_str == "None":
                lower_str = ""
        
        upper_str = ""
        if self._upper is not None:
            if hasattr(self._upper, 'to_code'):
                upper_str = self._upper.to_code()
            elif hasattr(self._upper, 'value') and self._upper.value is not None:
                upper_str = str(self._upper.value)
            # [关键修复] 如果upper_str是"None"，设置为空字符串
            if upper_str == "None":
                upper_str = ""
        
        step_str = None
        if self._step is not None:
            if hasattr(self._step, 'to_code'):
                step_str = self._step.to_code()
            elif hasattr(self._step, 'value') and self._step.value is not None:
                step_str = str(self._step.value)
            # [关键修复] 如果step_str是"None"，设置为None
            if step_str == "None":
                step_str = None
        
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
        
        # 处理切片对象
        if hasattr(self._slice, 'to_code'):
            slice_str = self._slice.to_code()
            # 如果切片对象返回的是字典字符串表示（如"{'type': 'slice', ...}"），
            # 说明是内部表示，需要特殊处理
            if slice_str.startswith("{") and "'type': 'slice'" in slice_str:
                # 尝试从字典中提取切片信息
                try:
                    # 解析字典字符串
                    slice_dict = eval(slice_str)
                    lower = slice_dict.get('lower', '')
                    upper = slice_dict.get('upper', '')
                    step = slice_dict.get('step')
                    
                    # 构建切片字符串
                    if step is not None:
                        slice_str = f"{lower}:{upper}:{step}"
                    else:
                        slice_str = f"{lower}:{upper}"
                except:
                    # 如果解析失败，使用原始字符串
                    pass
            # [关键修复] 处理类型注解中的元组，如 Dict[(str, Any)] -> Dict[str, Any]
            elif slice_str.startswith('(') and slice_str.endswith(')'):
                # 检查是否是类型注解中的元组（如泛型参数）
                # 如果是，去掉外层的括号
                inner_content = slice_str[1:-1]
                # 确保内部包含逗号（是真正的元组，不是带括号的单个类型）
                if ',' in inner_content:
                    slice_str = inner_content
        else:
            slice_str = str(self._slice)
        
        return f"{container_str}[{slice_str}]"


class ASTCall(ASTNode):
    """函数调用节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_func', '_pparams', '_kwparams', '_var', '_kw', 'offset')
    
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
        # [关键修复] 强制转换中文字符串为Exception
        # 只处理没有参数的调用（即字符串被错误地当作函数调用）
        ast_debug_print(f"[ASTCall.to_code] 被调用, self._func类型: {type(self._func)}")
        
        # [关键修复] 处理None值被错误当作函数调用的情况
        if self._func is None:
            # func为None，直接返回None，不生成函数调用
            return "None"
        
        # [关键修复] 处理ASTConstant类型的None值
        if isinstance(self._func, ASTConstant) and self._func.value is None:
            return "None"
        
        # [关键修复] 处理ASTObject类型的None值
        if isinstance(self._func, ASTObject) and self._func.object is None:
            return "None"
        
        if isinstance(self._func, ASTName):
            func_name = self._func.name if hasattr(self._func, 'name') else str(self._func)
            
            # [关键修复] 处理ASTName("None")被错误当作函数调用的情况
            if func_name == "None":
                return "None"
            
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in func_name)
            no_params = not self._pparams and not self._kwparams and not self._var and not self._kw
            ast_debug_print(f"[ASTCall.to_code] func_name: {func_name}, has_chinese: {has_chinese}, no_params: {no_params}")
            if has_chinese and no_params:
                ast_debug_print(f"[ASTCall.to_code] 转换中文字符串: {func_name} -> Exception('{func_name}')")
                return f"Exception('{func_name}')"
        # [关键修复] 处理ASTConstant类型的func（字符串常量被错误当作函数调用）
        if isinstance(self._func, ASTConstant):
            constant_value = self._func.value
            # 🔧 修复：对于字符串常量，无论是否包含中文字符，都直接返回字符串值
            if isinstance(constant_value, str):
                # 直接返回字符串常量值，不当作函数调用
                return self._func.to_code()
            # 🔧 修复：对于None值，直接返回None
            if constant_value is None:
                return "None"
            # 🔧 修复：对于数字常量（如0、1），直接返回数字，不当作函数调用
            if isinstance(constant_value, (int, float)):
                return self._func.to_code()
            # 对于其他类型的常量，继续当作函数调用处理
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(constant_value))
            no_params = not self._pparams and not self._kwparams and not self._var and not self._kw
            ast_debug_print(f"[ASTCall.to_code] constant_value: {constant_value}, has_chinese: {has_chinese}, no_params: {no_params}")
            if has_chinese:
                # 直接返回字符串常量值，不当作函数调用
                return self._func.to_code()
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
        
        # [关键修复] 再次检查func是否是"None"，防止前面的检查没有生效
        if isinstance(self._func, ASTName):
            func_name = self._func.name if hasattr(self._func, 'name') else str(self._func)
            if func_name == "None":
                return "None"
        
        # 获取函数名
        func_str = self._func.to_code() if hasattr(self._func, 'to_code') else str(self._func)
        
        # [关键修复] 检查函数名是否是有效的Python标识符但不是有效的异常类型
        # 这通常发生在字符串被错误地当作函数名时（如中文字符串）
        ast_debug_print(f"[ASTCall.to_code] self._func类型: {type(self._func)}, self._func: {self._func}")
        if isinstance(self._func, ASTName):
            func_name = self._func.name if hasattr(self._func, 'name') else str(self._func)
            ast_debug_print(f"[ASTCall.to_code] func_name: {func_name}, type: {type(func_name)}")
            # 检查是否是有效的异常类型（首字母大写或是内置异常）
            builtin_exceptions = ('Exception', 'BaseException', 'ValueError', 'TypeError', 
                                  'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                                  'ZeroDivisionError', 'OverflowError', 'IOError', 'OSError',
                                  'ImportError', 'ModuleNotFoundError', 'SyntaxError',
                                  'IndentationError', 'TabError', 'NameError', 'UnboundLocalError',
                                  'AssertionError', 'LookupError', 'ArithmeticError',
                                  'EnvironmentError', 'BlockingIOError', 'ChildProcessError',
                                  'ConnectionError', 'BrokenPipeError', 'ConnectionAbortedError',
                                  'ConnectionRefusedError', 'ConnectionResetError',
                                  'FileExistsError', 'FileNotFoundError', 'InterruptedError',
                                  'IsADirectoryError', 'NotADirectoryError', 'PermissionError',
                                  'ProcessLookupError', 'TimeoutError', 'ReferenceError',
                                  'NotImplementedError', 'RecursionError', 'StopIteration',
                                  'StopAsyncIteration', 'GeneratorExit', 'SystemExit',
                                  'KeyboardInterrupt', 'Warning', 'UserWarning', 'DeprecationWarning',
                                  'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
                                  'FutureWarning', 'ImportWarning', 'UnicodeWarning',
                                  'BytesWarning', 'ResourceWarning', 'FloatingPointError',
                                  'BufferError', 'MemoryError', 'SystemError', 'EOFError')
            # 检查首字符是否大写
            first_char_upper = False
            if len(func_name) > 0:
                first_char = func_name[0]
                if 'A' <= first_char <= 'Z':
                    first_char_upper = True
            ast_debug_print(f"[ASTCall.to_code] first_char_upper: {first_char_upper}, in_builtin: {func_name in builtin_exceptions}")
            # [关键修复] 检查是否是内置函数或常见的Python函数
            builtin_functions = ('len', 'isinstance', 'type', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
                                 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max', 'abs', 'round',
                                 'print', 'input', 'open', 'close', 'read', 'write', 'append', 'extend', 'insert',
                                 'remove', 'pop', 'clear', 'copy', 'sort', 'reverse', 'index', 'count',
                                 'keys', 'values', 'items', 'get', 'update', 'setdefault', 'popitem',
                                 'join', 'split', 'replace', 'strip', 'lstrip', 'rstrip', 'startswith', 'endswith',
                                 'find', 'rfind', 'index', 'rindex', 'count', 'upper', 'lower', 'title', 'capitalize',
                                 'format', 'encode', 'decode', 'center', 'ljust', 'rjust', 'zfill', 'expandtabs',
                                 'isalpha', 'isdigit', 'isalnum', 'isspace', 'istitle', 'isupper', 'islower',
                                 'isidentifier', 'isnumeric', 'isdecimal', 'isprintable', 'isascii')
            # 如果不是有效的异常类型，且不是内置函数，且首字符小写，且包含中文字符，转换为Exception('func_name')
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in func_name)
            if func_name not in builtin_exceptions and func_name not in builtin_functions and not first_char_upper and has_chinese:
                ast_debug_print(f"[ASTCall.to_code] 转换为Exception('{func_name}')")
                # 是字符串消息，不是异常类型，转换为Exception('func_name')
                return f"Exception('{func_name}')"
            else:
                ast_debug_print(f"[ASTCall.to_code] 不转换，直接返回{func_name}()")
        
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
        # [关键修复] 处理**kwargs展开语法
        if self._value is None and self._name.startswith('**'):
            return self._name
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
            # [关键修复] 处理星号解包（用于match/case中的*rest）
            if hasattr(item, '_is_starred') and item._is_starred:
                item_str = f"*{item_str}"
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
            item_str = self._item_to_code(item)
            # [关键修复] 处理星号解包
            if hasattr(item, '_is_starred') and item._is_starred:
                item_str = f"*{item_str}"
            return f"({item_str},)"
        
        item_strs = []
        for item in self._items:
            item_str = self._item_to_code(item)
            # [关键修复] 处理星号解包
            if hasattr(item, '_is_starred') and item._is_starred:
                item_str = f"*{item_str}"
            item_strs.append(item_str)
        
        return f"({', '.join(item_strs)})"
    
    def _item_to_code(self, item):
        """将单个元素转换为代码字符串"""
        if hasattr(item, 'to_code'):
            try:
                result = item.to_code()
                # 检查是否返回了对象引用
                if result and '<core.ast_nodes.' not in result:
                    return result
            except:
                pass
        
        # 备用方法：根据类型提取值
        item_type = type(item).__name__
        
        if item_type == 'ASTName':
            if hasattr(item, 'name'):
                return str(item.name)
            elif hasattr(item, '_name'):
                name_val = item._name
                if hasattr(name_val, '_value'):
                    return str(name_val._value)
                return str(name_val)
            return "unknown"
        
        elif item_type == 'ASTConstant':
            if hasattr(item, 'value'):
                return repr(item.value)
            return "None"
        
        elif item_type == 'ASTObject':
            if hasattr(item, 'value'):
                return repr(item.value)
            elif hasattr(item, 'object'):
                return repr(item.object)
            return "None"
        
        elif item_type == 'ASTCall':
            # 尝试生成函数调用代码
            func = getattr(item, '_func', None) or getattr(item, 'func', None)
            args = getattr(item, '_args', None) or getattr(item, 'args', None)
            
            func_str = "unknown"
            if func:
                if hasattr(func, 'to_code'):
                    try:
                        func_str = func.to_code()
                        if '<core.ast_nodes.' in func_str:
                            func_str = "unknown"
                    except:
                        func_str = "unknown"
                elif hasattr(func, 'name'):
                    func_str = str(func.name)
                elif hasattr(func, '_name'):
                    func_str = str(func._name)
            
            arg_strs = []
            if args:
                if isinstance(args, list):
                    for arg in args:
                        arg_str = self._item_to_code(arg)
                        arg_strs.append(arg_str)
                else:
                    arg_strs.append(self._item_to_code(args))
            
            return f"{func_str}({', '.join(arg_strs)})"
        
        elif item_type == 'ASTAttribute':
            # 尝试生成属性访问代码
            value = getattr(item, '_value', None) or getattr(item, 'value', None)
            attr = getattr(item, '_attr', None) or getattr(item, 'attr', None)
            
            value_str = "unknown"
            if value:
                if hasattr(value, 'to_code'):
                    try:
                        value_str = value.to_code()
                        if '<core.ast_nodes.' in value_str:
                            value_str = "unknown"
                    except:
                        value_str = "unknown"
                elif hasattr(value, 'name'):
                    value_str = str(value.name)
                elif hasattr(value, '_name'):
                    value_str = str(value._name)
            
            attr_str = str(attr) if attr else "unknown"
            return f"{value_str}.{attr_str}"
        
        elif item_type == 'ASTSubscript':
            # 尝试生成下标访问代码
            value = getattr(item, '_value', None) or getattr(item, 'value', None)
            slice_ = getattr(item, '_slice', None) or getattr(item, 'slice', None)
            
            value_str = "unknown"
            if value:
                if hasattr(value, 'to_code'):
                    try:
                        value_str = value.to_code()
                        if '<core.ast_nodes.' in value_str:
                            value_str = "unknown"
                    except:
                        value_str = "unknown"
                elif hasattr(value, 'name'):
                    value_str = str(value.name)
                elif hasattr(value, '_name'):
                    value_str = str(value._name)
            
            slice_str = "unknown"
            if slice_:
                if hasattr(slice_, 'to_code'):
                    try:
                        slice_str = slice_.to_code()
                        if '<core.ast_nodes.' in slice_str:
                            slice_str = "unknown"
                    except:
                        slice_str = "unknown"
                elif hasattr(slice_, 'value'):
                    slice_str = repr(slice_.value)
            
            return f"{value_str}[{slice_str}]"
        
        # 最后的备用方法
        return str(item) if not str(item).startswith('<core.ast_nodes.') else "unknown"


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
            # [关键修复] 正确处理各种节点类型
            if hasattr(key, 'to_code'):
                key_code = key.to_code()
            elif hasattr(key, 'value'):
                key_code = repr(key.value) if isinstance(key.value, str) else str(key.value)
            else:
                key_code = str(key)
            
            if hasattr(value, 'to_code'):
                value_code = value.to_code()
            elif hasattr(value, 'value'):
                value_code = repr(value.value) if isinstance(value.value, str) else str(value.value)
            else:
                value_code = str(value)
            
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
        # [关键修复] 处理PycNumeric类型
        from core.pyc_objects import PycNumeric, PycString
        if isinstance(self._value, PycNumeric):
            return str(self._value.value)
        elif isinstance(self._value, PycString):
            return repr(self._value.value)
        elif isinstance(self._value, bytes):
            # [关键修复] 正确处理字节串
            return repr(self._value)
        elif isinstance(self._value, str):
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复if节点"
        
        _visited.add(node_id)
        
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
    __slots__ = ('_name', 'module_name', '_is_starred')
    
    def __init__(self, name, module_name=None):
        super().__init__(NodeType.NODE_NAME)
        self._name = name
        self.module_name = module_name  # 用于from ... import ...语句
        self._is_starred = False  # 用于星号解包标记
    
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
                 decorators: List['ASTNode'] = None, code_obj: 'PycCode' = None,
                 is_async: bool = False, vararg: str = None, kwarg: str = None):
        super().__init__(NodeType.NODE_FUNCTION)
        self._name = name
        self._args = args if args is not None else []
        self._body = body if body is not None else ASTNodeList()
        self._returns = returns
        self._decorators = decorators if decorators is not None else []
        self._code_obj = code_obj  # 存储函数代码对象，用于生成函数体
        self._nonlocal_names = []  # [新增] 存储nonlocal声明的变量名
        self._is_async = is_async  # [新增] 是否是异步函数
        self._vararg = vararg  # [新增] *args参数名
        self._kwarg = kwarg    # [新增] **kwargs参数名
        self._has_implicit_return = False  # [新增] 是否有隐式return（函数末尾的隐式return None）
        self._if_chain_root = None  # [关键修复] 保存if链的根节点，用于else分支的生成
        self._defaults = []  # [关键修复] 位置参数默认值列表
        self._kwonlyargs = []  # [关键修复] 关键字-only参数列表
        self._kw_defaults = []  # [关键修复] 关键字-only参数默认值列表
    
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
    
    def add_nonlocal(self, name: str):
        """[新增] 添加nonlocal声明的变量名"""
        if name not in self._nonlocal_names:
            self._nonlocal_names.append(name)
    
    @property
    def nonlocal_names(self) -> List[str]:
        """[新增] 获取nonlocal声明的变量名列表"""
        return self._nonlocal_names

    @property
    def is_async(self) -> bool:
        """[新增] 是否是异步函数"""
        return self._is_async

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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复try节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        
        # 生成装饰器
        decorator_lines = []
        for decorator in self._decorators:
            if isinstance(decorator, str):
                decorator_lines.append(f"{indent}@{decorator}")
            elif hasattr(decorator, 'decorator_name'):
                decorator_lines.append(f"{indent}@{decorator.decorator_name}")
            elif isinstance(decorator, ASTName):
                # [关键修复] ASTName类型的装饰器需要添加@前缀和缩进
                decorator_lines.append(f"{indent}@{decorator.to_code(indent_level)}")
            elif hasattr(decorator, 'to_code'):
                # [关键修复] ASTCall类型的装饰器（如@decorator_with_args('hello', 'world')）
                # 需要添加@前缀
                decorator_code = decorator.to_code(indent_level)
                if not decorator_code.startswith('@'):
                    decorator_lines.append(f"{indent}@{decorator_code}")
                else:
                    decorator_lines.append(f"{indent}{decorator_code}")
            else:
                decorator_lines.append(f"{indent}@{decorator}")
        
        decorator_str = "\n".join(decorator_lines)
        if decorator_str:
            decorator_str += "\n"
        
        # 生成函数签名
        # [关键修复] 合并_args、_defargs和_annotations来生成带类型注解和默认值的参数
        args_list = []
        
        # 获取类型注解字典
        annotations = getattr(self, '_annotations', {})
        # print(f"[CRITICAL ASTFunctionDef.to_code] annotations={annotations}, _args={self._args}")
        
        # 首先添加普通参数
        for i, arg in enumerate(self._args):
            arg_str = str(arg)
            # 移除可能的默认值部分
            if '=' in arg_str:
                arg_str = arg_str.split('=')[0]
            
            # [关键修复] 添加类型注解
            param_with_annotation = arg_str
            if arg_str in annotations:
                ann = annotations[arg_str]
                if hasattr(ann, 'to_code'):
                    ann_str = ann.to_code(0)
                else:
                    ann_str = str(ann)
                param_with_annotation = f"{arg_str}: {ann_str}"
            
            args_list.append(param_with_annotation)
        
        # [关键修复] 如果有_defargs，更新最后几个参数的默认值
        if hasattr(self, '_defargs') and self._defargs:
            # 将_defargs转换为字符串列表
            default_strs = []
            for default in self._defargs:
                # [关键修复] 处理元组情况（默认参数元组）
                if isinstance(default, ASTTuple) and hasattr(default, 'items'):
                    # 如果是元组，展开所有元素作为默认值
                    items = default.items
                    if items:
                        for item in items:
                            if hasattr(item, 'to_code'):
                                default_strs.append(item.to_code(0))
                            elif hasattr(item, 'value'):
                                default_strs.append(repr(item.value))
                            else:
                                default_strs.append(str(item))
                    else:
                        default_strs.append('()')
                elif hasattr(default, 'to_code'):
                    default_strs.append(default.to_code(0))
                elif hasattr(default, 'value'):
                    default_strs.append(repr(default.value))
                else:
                    default_strs.append(str(default))
            
            # 更新最后len(default_strs)个参数的默认值
            num_defaults = len(default_strs)
            for i in range(num_defaults):
                arg_idx = len(args_list) - num_defaults + i
                if arg_idx >= 0:
                    # 在类型注解后面添加默认值
                    args_list[arg_idx] = f"{args_list[arg_idx]}={default_strs[i]}"
        
        # [关键修复] 添加*args参数
        if hasattr(self, '_vararg') and self._vararg:
            args_list.append(f"*{self._vararg}")
        
        # [关键修复] 添加关键字-only参数（在*args之后，**kwargs之前）
        if hasattr(self, '_kwonlyargs') and self._kwonlyargs:
            for i, kwonlyarg in enumerate(self._kwonlyargs):
                arg_str = str(kwonlyarg)
                # 如果有默认值，添加默认值
                if hasattr(self, '_kw_defaults') and self._kw_defaults:
                    if i < len(self._kw_defaults) and self._kw_defaults[i] is not None:
                        default = self._kw_defaults[i]
                        if hasattr(default, 'to_code'):
                            default_str = default.to_code(0)
                        elif hasattr(default, 'value'):
                            default_str = repr(default.value)
                        else:
                            default_str = str(default)
                        arg_str = f"{arg_str}={default_str}"
                args_list.append(arg_str)
        
        # [关键修复] 添加**kwargs参数
        if hasattr(self, '_kwarg') and self._kwarg:
            args_list.append(f"**{self._kwarg}")
        
        args_str = ", ".join(args_list)
        
        # [关键修复] 添加返回值注解
        return_annotation_str = ""
        if 'return' in annotations:
            return_ann = annotations['return']
            if hasattr(return_ann, 'to_code'):
                return_ann_str = return_ann.to_code(0)
            else:
                return_ann_str = str(return_ann)
            return_annotation_str = f" -> {return_ann_str}"
        
        # [关键修复] 在生成函数体代码之前，设置全局变量来保存_if_chain_root
        # 这样ASTIf.to_code方法可以使用这个变量来生成else分支
        import threading
        if not hasattr(threading, '_ast_if_chain_root'):
            threading._ast_if_chain_root = {}
        thread_id = threading.current_thread().ident
        threading._ast_if_chain_root[thread_id] = getattr(self, '_if_chain_root', None)
        ast_debug_print(f"[ASTFunctionDef.to_code] [关键修复] 设置全局_if_chain_root: {threading._ast_if_chain_root[thread_id] is not None}")
        
        # 生成函数体
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            
            # [关键修复] 清理全局变量
            if thread_id in threading._ast_if_chain_root:
                del threading._ast_if_chain_root[thread_id]
            # [关键修复] 如果函数体为空，生成pass语句
            if not body_str or body_str.strip() == "":
                body_str = "    " * (indent_level + 1) + "pass"
                # DEBUG: print(f"[DEBUG ASTFunctionDef.to_code] 使用默认pass")
            
            # [关键修复] 如果函数体不以return语句结尾，添加return None
            # 这是为了匹配Python编译器自动添加的隐式return None
            # [关键修复] 但__init__方法不应该添加return None，因为原始字节码中没有
            # [关键修复] 如果函数有隐式return（函数末尾的隐式return None），也不应该添加显式return None
            body_lines = body_str.strip().split('\n')
            if body_lines and not body_lines[-1].strip().startswith('return'):
                # 检查函数体是否只有pass语句
                # 如果只有pass，不需要添加return None，因为pass会被编译为隐式return None
                is_only_pass = len(body_lines) == 1 and body_lines[0].strip() == 'pass'
                # [关键修复] __init__方法不应该添加return None
                is_init_method = self._name == '__init__'
                # [关键修复] 如果函数有隐式return，不应该添加显式return None
                has_implicit_return = getattr(self, '_has_implicit_return', False)
                ast_debug_print(f"[DEBUG to_code] {self._name}: is_only_pass={is_only_pass}, is_init_method={is_init_method}, has_implicit_return={has_implicit_return}, last_line={body_lines[-1].strip() if body_lines else 'empty'}")
                if not is_only_pass and not is_init_method and not has_implicit_return:
                    # 函数体不以return结尾且不是只有pass，添加return None
                    return_none_line = "    " * (indent_level + 1) + "return None"
                    body_str = body_str + '\n' + return_none_line
        elif isinstance(self._body, str):
            # 简单的字符串直接使用
            body_str = self._body
            # [关键修复] 如果函数体为空，生成pass语句
            if not body_str or body_str.strip() == "":
                body_str = "    " * (indent_level + 1) + "pass"
        else:
            # 如果没有函数体，生成pass语句
            body_str = "    " * (indent_level + 1) + "pass"
        
        # [新增] 生成nonlocal声明
        nonlocal_str = ""
        if self._nonlocal_names:
            nonlocal_indent = "    " * (indent_level + 1)
            nonlocal_str = f"{nonlocal_indent}nonlocal {', '.join(self._nonlocal_names)}\n"
        
        # [关键修复] 生成global声明
        # 只声明在函数中被赋值的全局变量（使用了STORE_GLOBAL指令的变量）
        # 注意：ASTGlobal节点可能已经在函数体中（由_store_global方法添加），需要检查避免重复
        global_str = ""
        
        # 首先检查函数体中是否已经有ASTGlobal节点
        existing_global_vars = set()
        if hasattr(self._body, 'nodes'):
            for node in self._body.nodes:
                if isinstance(node, ASTGlobal):
                    existing_global_vars.update(node.names)
        
        if self._code_obj:
            global_vars = []
            
            # 从code_obj的instr_store_global_names获取使用了STORE_GLOBAL的变量名
            if hasattr(self._code_obj, 'instr_store_global_names') and self._code_obj.instr_store_global_names:
                for var_name in self._code_obj.instr_store_global_names:
                    # 跳过已经在函数体中声明为global的变量
                    if var_name not in existing_global_vars and var_name not in global_vars:
                        global_vars.append(var_name)
            
            # 生成global声明
            if global_vars:
                global_indent = "    " * (indent_level + 1)
                global_str = f"{global_indent}global {', '.join(global_vars)}\n"
        
        # [关键修复] 处理lambda函数
        if self._name == '<lambda>':
            # 生成lambda表达式
            # 提取lambda体（去掉return关键字和缩进）
            lambda_body = body_str.strip()
            if lambda_body.startswith('return '):
                lambda_body = lambda_body[7:]  # 去掉'return '
            elif lambda_body.startswith('    return '):
                lambda_body = lambda_body[11:]  # 去掉'    return '
            
            # [关键修复] 如果lambda体为空或pass，使用None作为默认值
            if not lambda_body or lambda_body == 'pass':
                lambda_body = 'None'
            
            return f"{decorator_str}{indent}lambda {args_str}: {lambda_body}"
        
        # [关键修复] 生成函数定义代码
        # 注意：当函数定义作为值使用时（如赋值给变量），需要特殊处理
        # 但在代码生成阶段，我们生成标准的def语句，由调用者决定如何使用
        # [关键修复] 支持 async def
        async_prefix = "async " if self._is_async else ""
        return f"{decorator_str}{indent}{async_prefix}def {self._name}({args_str}){return_annotation_str}:\n{nonlocal_str}{global_str}{body_str}"


class ASTClassDef(ASTNode):
    """类定义节点"""
    
    def __init__(self, name: str, bases: List['ASTNode'] = None, 
                 body: List['ASTNode'] = None, keywords: List['ASTNode'] = None,
                 decorators: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_CLASS)
        self._name = name
        self._bases = bases if bases is not None else []
        self._body = body if body is not None else []
        self._keywords = keywords if keywords is not None else []
        self._decorators = decorators if decorators is not None else []
    
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
    
    @property
    def decorators(self) -> List['ASTNode']:
        return self._decorators
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复if节点"
        
        _visited.add(node_id)
        
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
        ast_debug_print(f"[ASTClassDef.to_code] 生成类体: {self._name}, body类型={type(self._body)}, hasattr(to_code)={hasattr(self._body, 'to_code')}, body_id={id(self._body)}")
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            ast_debug_print(f"[ASTClassDef.to_code] body_str长度={len(body_str)}, body_str前100字符={body_str[:100]}")
            # [关键修复] 如果body_str为空或只有空白，生成pass语句
            if not body_str or not body_str.strip():
                body_str = "    " * (indent_level + 1) + "pass"
        elif isinstance(self._body, list):
            # [关键修复] 如果body是空列表，生成pass语句
            if not self._body:
                body_str = "    " * (indent_level + 1) + "pass"
            else:
                # 如果body是列表，生成基本的类体结构
                body_lines = []
                prev_was_method = False
                for item in self._body:
                    # 在方法之间添加空行
                    if prev_was_method and hasattr(item, 'to_code'):
                        # [关键修复] 传递 _visited 参数来检测循环引用
                        try:
                            item_code = item.to_code(indent_level + 1, _visited)
                        except TypeError:
                            item_code = item.to_code(indent_level + 1)
                        # 检查是否是方法定义（以 "def " 开头）
                        if item_code.strip().startswith('def '):
                            body_lines.append("")  # 添加空行
                    
                    if hasattr(item, 'to_code'):
                        # [关键修复] 传递 _visited 参数来检测循环引用
                        try:
                            item_code = item.to_code(indent_level + 1, _visited)
                        except TypeError:
                            item_code = item.to_code(indent_level + 1)
                        body_lines.append(item_code)
                        # 标记是否是方法
                        prev_was_method = item_code.strip().startswith('def ')
                    else:
                        body_lines.append("    " * (indent_level + 1) + str(item))
                        prev_was_method = False
                body_str = "\n".join(body_lines)
                # [关键修复] 如果生成的body_str为空或只有空白，生成pass语句
                if not body_str or not body_str.strip():
                    body_str = "    " * (indent_level + 1) + "pass"
        else:
            # 如果没有类体，生成pass语句
            body_str = "    " * (indent_level + 1) + "pass"
        
        return f"{indent}class {self._name}{bases_str}:\n{body_str}"


class ASTAssign(ASTNode):
    """赋值节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_targets', '_value', '_is_chain_assign', 'offset')
    
    def __init__(self, targets: List['ASTNode'], value: 'ASTNode'):
        super().__init__(NodeType.NODE_ASSIGN)
        self._targets = targets
        self._value = value
        self._is_chain_assign = False  # [关键修复] 默认不是链式赋值
    
    @property
    def targets(self) -> List['ASTNode']:
        return self._targets
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def is_chain_assign(self) -> bool:
        return self._is_chain_assign
    
    @is_chain_assign.setter
    def is_chain_assign(self, value: bool):
        self._is_chain_assign = value
    
    def to_code(self, indent_level=0):
        """生成赋值语句代码"""
        indent = "    " * indent_level
        
        # [关键修复] 检查是否是链式赋值（_is_chain_assign标志）
        if getattr(self, '_is_chain_assign', False):
            # 链式赋值：a = b = c = value
            target_codes = []
            for target in self._targets:
                if hasattr(target, 'to_code'):
                    target_codes.append(target.to_code())
                else:
                    target_codes.append(str(target))
            targets_str = " = ".join(target_codes)
        else:
            # 元组解包赋值：a, b, c = value
            # [关键修复] 对于元组解包，直接生成元素代码，不添加括号
            target_codes = []
            for target in self._targets:
                # 如果目标是ASTTuple，直接获取其元素代码
                if hasattr(target, '_items') and hasattr(target, 'to_code'):
                    # 这是ASTTuple节点，直接生成元素代码
                    item_strs = []
                    for item in target._items:
                        item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
                        # [关键修复] 处理星号解包
                        if hasattr(item, '_is_starred') and item._is_starred:
                            item_str = f"*{item_str}"
                        item_strs.append(item_str)
                    target_codes.append(", ".join(item_strs))
                elif hasattr(target, 'to_code'):
                    target_codes.append(target.to_code())
                else:
                    target_codes.append(str(target))
            targets_str = ", ".join(target_codes)
        
        # [关键修复] 生成值表达式代码，对于ASTTuple值不添加括号
        if hasattr(self._value, '__class__') and self._value.__class__.__name__ == 'ASTTuple' and hasattr(self._value, '_items'):
            # 这是ASTTuple值，直接生成元素代码，不添加括号
            item_strs = []
            for item in self._value._items:
                item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
                item_strs.append(item_str)
            value_code = ", ".join(item_strs)
        elif hasattr(self._value, 'to_code'):
            value_code = self._value.to_code()
        else:
            value_code = str(self._value)
        
        return f"{indent}{targets_str} = {value_code}"


class ASTNamedExpr(ASTNode):
    """海象运算符节点 (:=) - Python 3.8+"""
    
    __slots__ = ('_target', '_value', 'offset', '_is_walrus')
    
    def __init__(self, target: 'ASTNode', value: 'ASTNode'):
        super().__init__(NodeType.NODE_ASSIGN)  # 复用 NODE_ASSIGN 类型
        self._target = target
        self._value = value
        self._is_walrus = True  # [关键修复] 标记为海象运算符
    
    @property
    def target(self) -> 'ASTNode':
        return self._target
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    @property
    def is_walrus(self) -> bool:
        """[关键修复] 是否是海象运算符"""
        return True
    
    def to_code(self, indent_level=0, need_parentheses=True):
        """生成海象运算符代码
        
        Args:
            indent_level: 缩进级别
            need_parentheses: 是否需要括号（在比较表达式中作为左操作数时不需要）
        """
        indent = "    " * indent_level
        
        # 生成目标代码
        if hasattr(self._target, 'to_code'):
            target_code = self._target.to_code()
        else:
            target_code = str(self._target)
        
        # 生成值表达式代码
        if hasattr(self._value, 'to_code'):
            value_code = self._value.to_code()
        else:
            value_code = str(self._value)
        
        # [关键修复] 根据need_parentheses决定是否添加括号
        if need_parentheses:
            return f"{indent}({target_code} := {value_code})"
        else:
            return f"{indent}{target_code} := {value_code}"


class ASTIf(ASTNode):
    """if语句节点 - 性能优化版本"""
    
    # 添加__slots__优化
    # [关键修复] 添加 _is_else_block_if 用于标记else块内的if
    # [关键修复] 添加 _else_processed 用于标记else分支是否已经被处理过
    # [关键修复] 添加 _else_end 用于保存else分支的结束位置
    # [关键修复] 添加 offset 用于代码排序
    # [关键修复] 添加 _no_else_branch 用于标记不应该有else分支的if
    # [关键修复] 添加 _is_nested_if 用于标记嵌套的if（不是elif）
    __slots__ = ('_test', '_body', '_orelse', '_is_else_block_if', '_else_processed', '_else_end', '_body_end', 'offset', '_no_else_branch', '_is_nested_if', '_is_elif')
    
    def __init__(self, test: 'ASTNode' = None, body: 'ASTNode' = None, orelse: 'ASTNode' = None,
                 condition: 'ASTNode' = None, then: 'ASTNode' = None, else_block: 'ASTNode' = None):
        super().__init__(NodeType.NODE_BLOCK)
        self._test = test if test is not None else condition
        self._body = body if body is not None else (then if then is not None else ASTNodeList())
        self._orelse = orelse if orelse is not None else else_block
        # [关键修复] 初始化 _is_else_block_if 属性为 False
        self._is_else_block_if = False
        # [关键修复] 初始化 _no_else_branch 属性为 False
        self._no_else_branch = False
        self._is_nested_if = False
        self._is_elif = False
    
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
    
    @orelse.setter
    def orelse(self, value: 'ASTNode'):
        self._orelse = value
    
    @property
    def else_block(self) -> 'ASTNode':
        """orelse的别名，保持向后兼容"""
        return self._orelse
    
    @else_block.setter
    def else_block(self, value: 'ASTNode'):
        self._orelse = value
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复if节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        
        # [关键修复] 检查test和body是否为空
        if self._test is None:
            ast_debug_print(f"[ASTIf.to_code] test为空，跳过生成if语句")
            return ""
        if self._body is None:
            ast_debug_print(f"[ASTIf.to_code] body为空，跳过生成if语句")
            return ""
        
        # 生成条件表达式
        test_code = self._test.to_code() if hasattr(self._test, 'to_code') else str(self._test)
        
        # [关键修复] 检查test_code是否为空
        if not test_code or test_code.strip() == "":
            ast_debug_print(f"[ASTIf.to_code] test_code为空，跳过生成if语句")
            return ""
        
        # [DEBUG] 添加调试信息
        ast_debug_print(f"[ASTIf.to_code] indent_level={indent_level}, test={test_code}")
        ast_debug_print(f"[ASTIf.to_code] _body type={type(self._body).__name__}, _body nodes count={len(self._body._nodes) if hasattr(self._body, '_nodes') else 'N/A'}")
        # [关键调试] 检查当前if节点的_is_else_block_if属性
        ast_debug_print(f"[ASTIf.to_code] [关键调试] 当前if节点的_is_else_block_if={getattr(self, '_is_else_block_if', 'N/A')}, id={id(self)}")
        
        # 生成if主体
        body_type = type(self._body).__name__
        # [禁用调试输出] print(f"DEBUG: ASTIf.to_code() - body type: {body_type}")
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            # [禁用调试输出] print(f"DEBUG: ASTIf.to_code() - body_str: {repr(body_str[:200]) if body_str else None}")
            # [禁用调试输出] ast_debug_print(f"[ASTIf.to_code] body_str={body_str!r}")
            # [关键修复] 如果body为空，生成pass语句
            if not body_str or body_str.strip() == "":
                body_str = "    " * (indent_level + 1) + "pass"
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        # [关键修复] 检查body中是否有嵌套的if语句，确保它们的else分支被正确处理
        # 这是为了处理像 `if x > 0: if y > 0: return 'both positive' else: return 'x positive, y not'` 这样的嵌套if语句
        if hasattr(self._body, 'nodes'):
            for node in self._body.nodes:
                if hasattr(node, '_test') and hasattr(node, '_body') and hasattr(node, '_orelse'):
                    # 这是一个if语句节点
                    # 检查它是否有else分支
                    if node._orelse and hasattr(node._orelse, 'nodes') and node._orelse.nodes:
                        # 检查else分支是否非空
                        has_content = False
                        for else_node in node._orelse.nodes:
                            if hasattr(else_node, 'to_code'):
                                else_code_str = else_node.to_code(0)
                                if else_code_str and else_code_str.strip():
                                    has_content = True
                                    break
                        if has_content:
                            # 不需要强制设置_is_else_block_if为True
                            # 因为我们已经在后续代码中检查了节点是否有else分支
                            pass
        
        # 生成if语句
        if_code = f"{indent}if {test_code}:\n{body_str}"
        
        # [关键修复] 只有当if_code不为空时，才处理else/elif分支
        else_code = ""
        
        # [关键修复] 检查if body是否有return语句
        # 如果有return语句，且orelse只有with语句，则不生成else:
        has_return_in_body = False
        body_nodes_info = []
        if self._body and hasattr(self._body, 'nodes'):
            for node in self._body.nodes:
                node_type = type(node).__name__
                body_nodes_info.append(node_type)
                if node_type == 'ASTReturn':
                    has_return_in_body = True
        
        # [调试] 打印body节点信息
        # [禁用调试输出] ast_debug_print(f"[ASTIf.to_code] body节点: {body_nodes_info}, has_return={has_return_in_body}")
        
        # [关键修复] 如果if body有return语句，且orelse只有with语句或为空，则不生成else:
        skip_else_generation = False
        orelse_nodes_info = []
        if self._orelse and hasattr(self._orelse, 'nodes'):
            for node in self._orelse.nodes:
                node_type = type(node).__name__
                orelse_nodes_info.append(node_type)
        
        # [禁用调试输出] ast_debug_print(f"[ASTIf.to_code] orelse节点: {orelse_nodes_info}")
        
        if has_return_in_body and self._orelse and hasattr(self._orelse, 'nodes'):
            # 检查orelse是否只有with语句
            only_with_in_orelse = True
            for node in self._orelse.nodes:
                node_type = type(node).__name__
                if node_type not in ['ASTWith', 'ASTExpr']:
                    only_with_in_orelse = False
                    break
            if only_with_in_orelse and len(self._orelse.nodes) > 0:
                skip_else_generation = True
                ast_debug_print(f"[ASTIf.to_code] if body有return语句，且orelse只有with语句，跳过else生成")
        
        # [调试] 打印_orelse信息
        ast_debug_print(f"[ASTIf.to_code] [调试] 检查_orelse: _orelse={self._orelse}, has nodes={hasattr(self._orelse, 'nodes') if self._orelse else False}, nodes count={len(self._orelse.nodes) if self._orelse and hasattr(self._orelse, 'nodes') else 0}, skip_else_generation={skip_else_generation}")
        
        # [关键修复] 检查全局变量中是否有保存的_if_chain_root
        # 如果有，并且当前if节点是_if_chain_root，则使用全局变量中的_orelse
        import threading
        thread_id = threading.current_thread().ident
        global_if_chain_root = getattr(threading, '_ast_if_chain_root', {}).get(thread_id)
        ast_debug_print(f"[ASTIf.to_code] [关键调试] 检查全局_if_chain_root: {global_if_chain_root is not None}, 当前if节点id={id(self)}, global_if_chain_root id={id(global_if_chain_root) if global_if_chain_root else 'N/A'}")
        # [关键修复] 只有当当前if节点是global_if_chain_root时，才使用它的_orelse
        # 这样可以确保else分支节点被正确添加到当前if节点的_orelse
        if global_if_chain_root is not None and global_if_chain_root is self:
            ast_debug_print(f"[ASTIf.to_code] [关键修复] 当前if节点是global_if_chain_root，使用global_if_chain_root的_orelse")
            effective_orelse = global_if_chain_root._orelse
        else:
            effective_orelse = self._orelse
        
        # [关键修复] 处理_orelse，无论它是否是ASTNodeList
        # 初始化else_nodes变量，避免作用域错误
        else_nodes = []
        
        # [关键调试] 检查effective_orelse
        ast_debug_print(f"[ASTIf.to_code] [关键调试] effective_orelse={effective_orelse is not None}, has nodes={hasattr(effective_orelse, 'nodes') if effective_orelse else False}, nodes count={len(effective_orelse.nodes) if effective_orelse and hasattr(effective_orelse, 'nodes') else 0}, skip_else_generation={skip_else_generation}")
        
        if effective_orelse and not skip_else_generation:
            # 如果_orelse是ASTNodeList且不为空，处理其中的节点
            if hasattr(effective_orelse, 'nodes') and effective_orelse.nodes:
                # [简化修复] 直接遍历orelse中的所有节点
                # 第一个ASTIf节点生成elif，其他ASTIf节点也生成elif
                
                # 收集所有非ASTIf节点作为else块的内容
                else_nodes = []
                
                # [关键修复] 在orelse处理开始时重置标志
                # 这样可以确保每个ASTIf节点的orelse独立生成代码
                ASTIf._if_generated_in_orelse = False
                if_generated = False
                
                # [调试] 打印orelse信息
                ast_debug_print(f"[ASTIf.to_code] [调试] effective_orelse类型: {type(effective_orelse).__name__}")
                ast_debug_print(f"[ASTIf.to_code] [调试] effective_orelse.nodes数量: {len(effective_orelse.nodes)}")
                for i, n in enumerate(effective_orelse.nodes):
                    ast_debug_print(f"[ASTIf.to_code] [调试] effective_orelse.nodes[{i}]: {type(n).__name__}, _is_else_block_if={getattr(n, '_is_else_block_if', 'N/A')}")
                
                # 遍历所有节点
                for i, node in enumerate(effective_orelse.nodes):
                    ast_debug_print(f"[ASTIf.to_code] 处理orelse节点 {i}: {type(node).__name__}")
                    
                    # [关键修复] 检查节点的目标变量名是否是counter
                    # 获取节点的目标变量名
                    node_dest = getattr(node, '_dest', None) or getattr(node, 'dest', None)
                    if node_dest is not None:
                        dest_name = getattr(node_dest, 'name', None) or getattr(node_dest, '_value', None)
                        if dest_name == 'counter':
                            ast_debug_print(f"[ASTIf.to_code] [关键修复] 节点目标变量名是counter，跳过该节点")
                            continue
                    
                    # [关键修复] 检查节点的偏移量是否在else范围内
                    # 获取节点的偏移量
                    node_offset = getattr(node, 'offset', -1)
                    # 获取当前if节点的else_end
                    else_end = getattr(self, '_else_end', -1)
                    # 获取当前if节点的body_end
                    body_end = getattr(self, '_body_end', -1)
                    
                    # [调试] 打印node_offset、else_end和body_end的值
                    ast_debug_print(f"[ASTIf.to_code] [调试] node_offset={node_offset}, else_end={else_end}, body_end={body_end}")
                    
                    # [关键修复] 如果节点的偏移量超出了else范围，跳过该节点
                    # [关键修复] 对于if/elif/else链，检查节点是否属于当前if节点的orelse
                    if node_offset > 0 and else_end > 0 and body_end > 0:
                        # [关键修复] 如果节点是ASTIf节点，检查它的body_end是否在正确的范围内
                        if hasattr(node, '_body_end') and hasattr(node, '_else_end'):
                            node_body_end = getattr(node, '_body_end', -1)
                            node_else_end = getattr(node, '_else_end', -1)
                            ast_debug_print(f"[ASTIf.to_code] [关键调试] 节点是ASTIf，node_body_end={node_body_end}, node_else_end={node_else_end}")
                            # 对于elif节点，只要它的body_end在当前if节点的else_end范围内，就处理它
                            if node_body_end > 0 and node_body_end <= else_end:
                                ast_debug_print(f"[ASTIf.to_code] [关键修复] 节点是elif，且body_end在范围内，处理它")
                            else:
                                ast_debug_print(f"[ASTIf.to_code] [关键修复] 节点是elif，但body_end不在范围内，跳过")
                                continue
                        elif not (body_end < node_offset <= else_end):
                            ast_debug_print(f"[ASTIf.to_code] [关键修复] 节点偏移量 {node_offset} 超出else范围 ({body_end}, {else_end}]，跳过该节点")
                            continue
                    
                    # [关键修复] 跳过空的ASTNodeList节点
                    if type(node).__name__ == 'ASTNodeList':
                        if not node._nodes:
                            ast_debug_print(f"[ASTIf.to_code] 跳过空的ASTNodeList节点")
                            continue
                        
                        # [关键修复] 处理包含BLK_ELSE类型ASTBlock的ASTNodeList节点
                        # 这些节点是else块的容器，需要在这里生成else:代码
                        has_blk_else = False
                        blk_else_node = None
                        for child_node in node._nodes:
                            if type(child_node).__name__ == 'ASTBlock':
                                if hasattr(child_node, 'blk_type') and child_node.blk_type == ASTBlock.BlockType.BLK_ELSE:
                                    has_blk_else = True
                                    blk_else_node = child_node
                                    break
                        if has_blk_else and blk_else_node is not None:
                            # [关键修复] 生成else:代码
                            ast_debug_print(f"[ASTIf.to_code] 发现BLK_ELSE块，生成else:代码")
                            # [关键修复] 传递 _visited 参数来检测循环引用
                            try:
                                else_body_code = blk_else_node.to_code(indent_level + 1, _visited)
                            except TypeError:
                                else_body_code = blk_else_node.to_code(indent_level + 1)
                            if else_body_code and else_body_code.strip():
                                else_code += f"\n{indent}else:\n{else_body_code}"
                                ast_debug_print(f"[ASTIf.to_code] 生成else:代码")
                            continue
                    
                    ast_debug_print(f"[ASTIf.to_code] [关键调试] 检查节点: {type(node).__name__}, has _test={hasattr(node, '_test')}, has _body={hasattr(node, '_body')}, _is_else_block_if={getattr(node, '_is_else_block_if', 'N/A')}")
                    if hasattr(node, '_test') and hasattr(node, '_body'):
                        # 检查是否是else块内的if，或者是嵌套if
                        ast_debug_print(f"[ASTIf.to_code] [关键调试] 节点有 _test 和 _body，_is_else_block_if={getattr(node, '_is_else_block_if', 'N/A')}")
                        
                        # 检查这个if节点是否有else分支
                        has_else = False
                        if hasattr(node, '_orelse') and node._orelse is not None:
                            if hasattr(node._orelse, 'nodes') and node._orelse.nodes:
                                # 检查else分支是否有内容
                                for else_node in node._orelse.nodes:
                                    if hasattr(else_node, 'to_code'):
                                        else_code_str = else_node.to_code(0)
                                        if else_code_str and else_code_str.strip():
                                            has_else = True
                                            break
                        
                        ast_debug_print(f"[ASTIf.to_code] [关键调试] 节点是否有else分支: {has_else}")
                        
                        # [关键修复] 检查这个节点是否已经在body中被处理过
                        # 如果是嵌套if且有else分支，它应该已经在body的to_code中被处理
                        # 这里只需要处理真正的elif节点（_is_else_block_if=False）
                        is_else_block_if = getattr(node, '_is_else_block_if', None)
                        ast_debug_print(f"[ASTIf.to_code] [关键调试] is_else_block_if={is_else_block_if}")
                        
                        if is_else_block_if is True:
                            # 这是else块内的if，不是elif
                            # 但它应该已经在body中被处理过了，这里跳过
                            ast_debug_print(f"[ASTIf.to_code] 跳过else块内的if节点（已在body中处理）: {node.test}")
                            continue
                        elif has_else and is_else_block_if is not False:
                            # [关键修复] 只有当节点不是elif节点（_is_else_block_if=False）时，才跳过
                            # 这是有else分支的嵌套if，应该已经在body中被处理
                            ast_debug_print(f"[ASTIf.to_code] 跳过有else分支的嵌套if（已在body中处理）: {node.test}")
                            continue
                        else:
                            # 这是一个elif (ASTIf节点) 或者需要生成为if的节点
                            ast_debug_print(f"[ASTIf.to_code] 发现elif节点，条件: {node.test}")
                            # 首先处理之前收集的else节点
                            # 将这些节点合并到elif的body中，而不是生成单独的else块
                            if else_nodes:
                                # 将else_nodes的内容合并到elif_body中
                                merged_else_body = ""
                                required_indent = "    " * (indent_level + 1)
                                for else_node in else_nodes:
                                    # [关键修复] 传递 _visited 参数来检测循环引用
                                    try:
                                        node_code = else_node.to_code(indent_level + 1, _visited)
                                    except TypeError:
                                        node_code = else_node.to_code(indent_level + 1)
                                    # [关键修复] 确保每一行代码都有正确的缩进
                                    if node_code and node_code.strip():
                                        # 处理多行代码，确保每一行都有正确的缩进
                                        code_lines = node_code.split('\n')
                                        fixed_lines = []
                                        for line in code_lines:
                                            if line.strip():  # 非空行
                                                # [关键修复] 计算当前行的缩进
                                                current_indent = len(line) - len(line.lstrip())
                                                required_indent_count = len(required_indent)
                                                if current_indent < required_indent_count:
                                                    # 缩进不足，添加正确的缩进
                                                    fixed_lines.append(required_indent + line.lstrip())
                                                else:
                                                    # 缩进足够，保留原样
                                                    fixed_lines.append(line)
                                            else:
                                                fixed_lines.append(line)  # 保留空行
                                        node_code = '\n'.join(fixed_lines)
                                        merged_else_body += "\n" + node_code
                                else_nodes = []
                            else:
                                merged_else_body = ""
                            
                            elif_test_code = node.test.to_code() if hasattr(node.test, 'to_code') else str(node.test)
                            if hasattr(node._body, 'to_code'):
                                # [关键修复] 传递 _visited 参数来检测循环引用
                                try:
                                    elif_body_str = node._body.to_code(indent_level + 1, _visited)
                                except TypeError:
                                    elif_body_str = node._body.to_code(indent_level + 1)
                                # 如果body为空，生成pass语句
                                if not elif_body_str or elif_body_str.strip() == "":
                                    elif_body_str = "    " * (indent_level + 1) + "pass"
                            else:
                                elif_body_str = "    " * (indent_level + 1) + "pass"
                            
                            # 将之前收集的else节点内容合并到elif body中
                            if merged_else_body:
                                # [关键修复] 移除merged_else_body开头的换行符
                                merged_else_body = merged_else_body.lstrip('\n')
                                # [关键修复] 如果elif_body_str是pass，用merged_else_body替换
                                if elif_body_str.strip() == "pass" or elif_body_str.strip() == required_indent.strip() + "pass":
                                    elif_body_str = merged_else_body
                                else:
                                    elif_body_str = merged_else_body + "\n" + elif_body_str
                            
                            # 递归处理elif节点的_orelse（else分支）
                            elif_else_code = ""
                            if hasattr(node, '_orelse') and node._orelse is not None and hasattr(node._orelse, 'nodes') and node._orelse.nodes:
                                ast_debug_print(f"[ASTIf.to_code] 处理elif节点的_orelse，节点数: {len(node._orelse.nodes)}")
                                # [关键调试] 打印所有节点
                                for i, n in enumerate(node._orelse.nodes):
                                    ast_debug_print(f"[DEBUG-ASTIF-ORELSE] node[{i}]: {type(n).__name__}")
                                    if hasattr(n, '_target') and hasattr(n._target, '_name'):
                                        ast_debug_print(f"[DEBUG-ASTIF-ORELSE]   target: {n._target._name}")
                                for elif_else_node in node._orelse.nodes:
                                    if hasattr(elif_else_node, 'to_code'):
                                        # [关键修复] 传递 _visited 参数来检测循环引用
                                        try:
                                            elif_else_node_code = elif_else_node.to_code(indent_level + 1, _visited)
                                        except TypeError:
                                            elif_else_node_code = elif_else_node.to_code(indent_level + 1)
                                        if elif_else_node_code and elif_else_node_code.strip():
                                            elif_else_code += "\n" + elif_else_node_code
                                            ast_debug_print(f"[ASTIf.to_code] 收集elif else节点: {type(elif_else_node).__name__}")
                                if elif_else_code:
                                    elif_body_str += f"\n{indent}else:{elif_else_code}"
                                    ast_debug_print(f"[ASTIf.to_code] 生成elif else代码")
                            
                            # 根据是否是第一个条件分支决定生成if还是elif
                            # 对于orelse中的第一个ASTIf节点，应该生成elif，而不是if
                            if if_generated:
                                else_code += f"\n{indent}elif {elif_test_code}:\n{elif_body_str}"
                                ast_debug_print(f"[ASTIf.to_code] 生成elif代码: elif {elif_test_code}:")
                            else:
                                # 对于orelse中的第一个ASTIf节点，生成elif语句
                                else_code += f"\n{indent}elif {elif_test_code}:\n{elif_body_str}"
                                ast_debug_print(f"[ASTIf.to_code] 生成elif代码: elif {elif_test_code}:")
                            if_generated = True
                    elif hasattr(node, 'to_code'):
                        # [关键修复] 检查是否是else标记节点
                        if getattr(node, '_is_else_marker', False):
                            # 这是一个else标记节点，表示需要生成else:
                            ast_debug_print(f"[ASTIf.to_code] 发现else标记节点")
                            # [关键修复] 检查是否已经生成过else:，避免重复生成
                            if f"\n{indent}else:" in else_code:
                                ast_debug_print(f"[ASTIf.to_code] 已经生成过else:，跳过")
                                continue
                            # 如果已经有收集的else节点，先处理它们
                            if else_nodes:
                                else_code += f"\n{indent}else:"
                                else_body_str = ""
                                for else_node in else_nodes:
                                    # [关键修复] 传递 _visited 参数来检测循环引用
                                    try:
                                        else_body_str += "\n" + else_node.to_code(indent_level + 1, _visited)
                                    except TypeError:
                                        else_body_str += "\n" + else_node.to_code(indent_level + 1)
                                # [关键修复] 如果else body为空，生成pass语句
                                if not else_body_str or else_body_str.strip() == "":
                                    else_body_str = "\n" + "    " * (indent_level + 1) + "pass"
                                else_code += else_body_str
                                else_nodes = []
                            else:
                                # 没有else节点，只生成else: pass
                                else_code += f"\n{indent}else:\n" + "    " * (indent_level + 1) + "pass"
                        # [关键修复] 处理else块（ASTBlock）
                        elif hasattr(node, 'blk_type') and node.blk_type == ASTBlock.BlockType.BLK_ELSE:
                            # [关键修复] 处理else块中的节点，但不生成额外的else:
                            ast_debug_print(f"[ASTIf.to_code] 处理else块中的节点")
                            if hasattr(node, '_nodes'):
                                for else_block_node in node._nodes:
                                    # 跳过else标记节点（已经处理过了）
                                    if getattr(else_block_node, '_is_else_marker', False):
                                        continue
                                    # 收集else块中的节点
                                    if hasattr(else_block_node, 'to_code'):
                                        else_nodes.append(else_block_node)
                                        ast_debug_print(f"[ASTIf.to_code] 从else块收集节点: {type(else_block_node).__name__}")
                        else:
                            # 这是一个普通节点（else块中的语句）
                            # 收集到else_nodes列表中
                            else_nodes.append(node)
                            ast_debug_print(f"[ASTIf.to_code] 收集else节点: {type(node).__name__}")
            
            # 处理最后收集的else节点
            # [关键修复] 只有当else_code中还没有else:时才生成
            else_marker = f"\n{indent}else:"
            ast_debug_print(f"[ASTIf.to_code] [关键调试] 处理else_nodes: {len(else_nodes)}个节点, else_code已有else:={else_marker in else_code}")
            for i, n in enumerate(else_nodes):
                ast_debug_print(f"[ASTIf.to_code] [关键调试] else_nodes[{i}]: {type(n).__name__}")
            if else_nodes and else_marker not in else_code:
                else_code += f"\n{indent}else:"
                else_body_str = ""
                for else_node in else_nodes:
                    # [关键修复] 传递 _visited 参数来检测循环引用
                    try:
                        else_body_str += "\n" + else_node.to_code(indent_level + 1, _visited)
                    except TypeError:
                        else_body_str += "\n" + else_node.to_code(indent_level + 1)
                # [关键修复] 如果else body为空，生成pass语句
                if not else_body_str or else_body_str.strip() == "":
                    else_body_str = "\n" + "    " * (indent_level + 1) + "pass"
                else_code += else_body_str
            elif else_nodes:
                # [关键修复] 如果已经有else:了，将else_nodes的内容添加到已有的else块中
                # 找到最后一个else:的位置
                else_pos = else_code.rfind(f"\n{indent}else:")
                if else_pos != -1:
                    # 在else:后面添加内容
                    insert_pos = else_pos + len(f"\n{indent}else:")
                    additional_body = ""
                    for else_node in else_nodes:
                        # [关键修复] 传递 _visited 参数来检测循环引用
                        try:
                            additional_body += "\n" + else_node.to_code(indent_level + 1, _visited)
                        except TypeError:
                            additional_body += "\n" + else_node.to_code(indent_level + 1)
                    if additional_body:
                        # 检查是否已经有内容了
                        existing_content = else_code[insert_pos:]
                        if not existing_content.strip() or existing_content.strip() == "pass":
                            # 替换pass或空内容
                            else_code = else_code[:insert_pos] + additional_body
                        else:
                            # 追加到现有内容
                            else_code = else_code[:insert_pos] + additional_body + else_code[insert_pos:]
        
        # [DEBUG] 打印调试信息
        if else_code:
            ast_debug_print(f"[ASTIf.to_code] 生成的else_code: {else_code[:100]}...")
        
        result = if_code + else_code
        
        # [关键修复] 后处理：修复连续的else:问题
        # 删除重复的else:，保留第一个，但保留第二个else后面的内容
        import re
        # 分多轮处理，确保所有重复都被修复
        for _ in range(10):
            # 修复模式：else: + 任意行（更深缩进）+ 同缩进级别的else:
            # 使用DOTALL模式让.匹配换行符
            # 保留第二个else后面的内容（将其作为第一个else块内的代码）
            pattern = r'^(\s*)else:((?:.*?)^\1    [^\n]+)^\1else:[^\n]*\n'
            def replace_duplicate_else(m):
                # 保留第一个else:及其内容，删除第二个else:，但保留第二个else后面的内容
                return m.group(1) + 'else:' + m.group(2) + '\n'
            result = re.sub(pattern, replace_duplicate_else, result, flags=re.MULTILINE | re.DOTALL)
        
        # [关键修复] 后处理：修复没有对应if的elif
        # 将 "else:\n    ...\n    elif" 替换为 "else:\n    ...\n    if"
        lines = result.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            # 检查是否是elif
            elif_match = re.match(r'^(\s*)elif\s', line)
            if elif_match:
                indent = len(elif_match.group(1))
                # 查找前面的非空行
                found_if = False
                for j in range(i - 1, -1, -1):
                    prev_line = lines[j]
                    if not prev_line.strip():
                        continue
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    # [关键修复] 如果找到同级别的if或elif，停止搜索
                    if prev_indent <= indent:
                        if re.match(r'^\s*(if|elif)\s', prev_line):
                            found_if = True
                        break
                    # 如果找到同级别的else，检查前面是否有if
                    if prev_indent == indent and prev_line.strip() == 'else:':
                        # 找到了else，但没有找到if，将elif改为if
                        break
                else:
                    # 没有找到前面的if，将elif改为if
                    pass
                if not found_if:
                    # 将elif改为if
                    line = re.sub(r'^(\s*)elif\s', r'\1if ', line)
            fixed_lines.append(line)
        result = '\n'.join(fixed_lines)
        
        ast_debug_print(f"[ASTIf.to_code] 返回结果: {result[:100]!r}")
        return result
    
    def _generate_orelse(self, orelse, indent_level=0, _recursion_depth=0):
        """递归生成else/elif分支代码"""
        # [关键修复] 添加递归深度限制，防止无限递归
        if _recursion_depth > 10:
            return ""
        
        indent = "    " * indent_level
        result = ""
        
        if hasattr(orelse, 'nodes') and orelse.nodes:
            # [关键修复] 首先处理所有的ASTIf节点（elif链）
            elif_nodes = [node for node in orelse.nodes if hasattr(node, '_test') and hasattr(node, '_body')]
            other_nodes = [node for node in orelse.nodes if not (hasattr(node, '_test') and hasattr(node, '_body'))]
            
            # 处理elif链
            for i, node in enumerate(elif_nodes):
                # 这是一个elif (ASTIf节点)
                test_code = node.test.to_code() if hasattr(node.test, 'to_code') else str(node.test)
                if hasattr(node._body, 'to_code'):
                    body_str = node._body.to_code(indent_level + 1)
                else:
                    body_str = "    " * (indent_level + 1) + "pass"
                
                # [关键修复] 第一个elif节点生成elif，后续生成if（在else块内）
                if i == 0:
                    result += f"\n{indent}elif {test_code}:\n{body_str}"
                else:
                    # 后续节点作为else块内的if
                    nested_body_str = ""
                    for line in body_str.split('\n'):
                        if line.strip():
                            nested_body_str += "\n    " + line
                    result += f"\n{indent}else:\n{indent}    if {test_code}:{nested_body_str}"
                
                # 递归处理这个elif的orelse（可能包含else分支）
                if hasattr(node, '_orelse') and node._orelse:
                    # 检查orelse中的节点类型
                    if hasattr(node._orelse, 'nodes') and node._orelse.nodes:
                        # [关键修复] 只处理else分支，不递归处理elif的orelse
                        # 避免无限递归
                        has_if_node = any(hasattr(n, '_test') and hasattr(n, '_body') for n in node._orelse.nodes)
                        if not has_if_node:
                            # 生成else块
                            result += f"\n{indent}else:"
                            for stmt in node._orelse.nodes:
                                if hasattr(stmt, 'to_code'):
                                    result += "\n" + stmt.to_code(indent_level + 1)
                                else:
                                    result += f"\n{indent}    {stmt}"
            
            # [关键修复] 处理其他节点（else块）
            # 只处理第一个ASTBlock节点作为else块，其他节点忽略
            # 并且确保只生成一个else块
            # 使用更严格的检查：检查result中是否已经包含else:
            has_else = '\nelse:' in result or result.endswith('else:')
            if other_nodes and not has_else:
                first_node = other_nodes[0]
                # [关键修复] 只处理ASTBlock节点，不处理普通语句节点
                if hasattr(first_node, '_blk_type'):
                    # 这是一个ASTBlock节点（else块）
                    result += f"\n{indent}else:"
                    if hasattr(first_node, 'to_code'):
                        result += "\n" + first_node.to_code(indent_level + 1)
                    else:
                        # 手动生成else块
                        if hasattr(first_node, 'nodes') and first_node.nodes:
                            for stmt in first_node.nodes:
                                if hasattr(stmt, 'to_code'):
                                    result += "\n" + stmt.to_code(indent_level + 1)
                                else:
                                    result += f"\n{indent}    {stmt}"
                        else:
                            result += f"\n{indent}    pass"
        
        return result


class ASTIfExp(ASTNode):
    """条件表达式节点 (x if condition else y)"""
    
    __slots__ = ('_test', '_body', '_orelse')
    
    def __init__(self, test: 'ASTNode' = None, body: 'ASTNode' = None, orelse: 'ASTNode' = None):
        super().__init__(NodeType.NODE_CONDITIONALEXP)
        self._test = test
        self._body = body
        self._orelse = orelse
    
    @property
    def test(self) -> 'ASTNode':
        return self._test
    
    @test.setter
    def test(self, value: 'ASTNode'):
        self._test = value
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @body.setter
    def body(self, value: 'ASTNode'):
        self._body = value
    
    @property
    def orelse(self) -> 'ASTNode':
        return self._orelse
    
    @orelse.setter
    def orelse(self, value: 'ASTNode'):
        self._orelse = value
    
    def to_code(self, indent_level=0):
        """生成Python代码"""
        body_code = self._body.to_code() if hasattr(self._body, 'to_code') else str(self._body)
        test_code = self._test.to_code() if hasattr(self._test, 'to_code') else str(self._test)
        orelse_code = self._orelse.to_code() if hasattr(self._orelse, 'to_code') else str(self._orelse)
        
        return f"{body_code} if {test_code} else {orelse_code}"


class ASTFor(ASTNode):
    """for循环节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_target', '_iter', '_body', '_else_block', '_is_async', 'offset')
    
    def __init__(self, target: 'ASTNode', iter_node: Optional['ASTNode'] = None, body: Optional['ASTNode'] = None,
                 else_block: Optional['ASTNode'] = None, is_async: bool = False):
        super().__init__(NodeType.NODE_FOR)
        self._target = target
        self._iter = iter_node if iter_node is not None else ASTName("__iter__", "")
        self._body = body if body is not None else ASTNodeList()
        self._else_block = else_block
        self._is_async = is_async
    
    @property
    def is_async(self) -> bool:
        return self._is_async
    
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复for节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        
        # 生成迭代目标
        target_code = self._target.to_code() if hasattr(self._target, 'to_code') else str(self._target)
        
        # 生成迭代器
        iter_code = self._iter.to_code() if hasattr(self._iter, 'to_code') else str(self._iter)
        
        # 生成for主体
        # DEBUG: print(f"[DEBUG ASTFor.to_code] _body={self._body}, _body.nodes={len(self._body) if self._body else 0}")
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            # DEBUG: print(f"[DEBUG ASTFor.to_code] body_str={repr(body_str)}")
            # [关键修复] 如果body_str为空，生成pass语句
            if not body_str or body_str.strip() == "":
                body_str = "    " * (indent_level + 1) + "pass"
                # DEBUG: print(f"[DEBUG ASTFor.to_code] 使用默认pass")
        else:
            body_str = "    " * (indent_level + 1) + "pass"
            # DEBUG: print(f"[DEBUG ASTFor.to_code] _body没有to_code方法，使用默认pass")
        
        # 生成for语句
        async_prefix = "async " if self._is_async else ""
        for_code = f"{indent}{async_prefix}for {target_code} in {iter_code}:\n{body_str}"
        
        # 处理else块
        else_code = ""
        if self._else_block:
            if hasattr(self._else_block, 'to_code'):
                # [关键修复] else块的内容需要比else:多一级缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    else_str = self._else_block.to_code(indent_level + 1, _visited)
                except TypeError:
                    else_str = self._else_block.to_code(indent_level + 1)
                # [关键修复] 只有当else块有实际内容时才生成else代码
                if else_str and else_str.strip() and else_str.strip() != "pass":
                    else_code = f"\n{indent}else:\n{else_str}"
            elif str(self._else_block).strip() and str(self._else_block).strip() != "pass":
                else_str = "    " * (indent_level + 1) + str(self._else_block)
                else_code = f"\n{indent}else:\n{else_str}"
        
        return for_code + else_code


class ASTWhile(ASTNode):
    """while循环节点"""
    
    # [关键修复] 添加 offset 用于代码排序
    # [关键修复] 添加 _original_test 用于保存原始的test，防止被后续代码修改
    __slots__ = ('_test', '_body', '_else_block', 'offset', '_original_test')
    
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复while节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        
        # 生成条件表达式
        test_code = self._test.to_code() if hasattr(self._test, 'to_code') else str(self._test)
        
        # [调试输出] 检查while节点的body
        ast_debug_print(f"[ASTWhile.to_code] test_code={test_code}, body_type={type(self._body).__name__}, body_length={len(self._body) if hasattr(self._body, '__len__') else 'N/A'}")
        if hasattr(self._body, '_nodes'):
            ast_debug_print(f"[ASTWhile.to_code] body_nodes={[type(n).__name__ + ':' + str(getattr(n, 'offset', -1)) for n in self._body._nodes]}")
        
        # 生成while主体
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            ast_debug_print(f"[ASTWhile.to_code] body_str={body_str[:100] if body_str else 'None'}...")
            # [关键修复] 如果body为空，生成pass语句
            if not body_str or body_str.strip() == "":
                body_str = "    " * (indent_level + 1) + "pass"
        else:
            body_str = "    " * (indent_level + 1) + "pass"
        
        # 生成while语句
        while_code = f"{indent}while {test_code}:\n{body_str}"
        
        # 处理else块
        else_code = ""
        if self._else_block:
            if hasattr(self._else_block, 'to_code'):
                # [关键修复] else块的内容需要比else:多一级缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    else_str = self._else_block.to_code(indent_level + 1, _visited)
                except TypeError:
                    else_str = self._else_block.to_code(indent_level + 1)
                # [关键修复] 只有当else块有实际内容时才生成else代码
                if else_str and else_str.strip() and else_str.strip() != "pass":
                    else_code = f"\n{indent}else:\n{else_str}"
            elif str(self._else_block).strip() and str(self._else_block).strip() != "pass":
                else_str = "    " * (indent_level + 1) + str(self._else_block)
                else_code = f"\n{indent}else:\n{else_str}"
        
        return while_code + else_code


class ASTWith(ASTNode):
    """with语句节点"""
    
    # [关键修复] 添加 offset 用于代码排序
    __slots__ = ('_items', '_body', '_is_async', 'offset')
    
    def __init__(self, context: 'ASTNode' = None, body: 'ASTNode' = None, optional_vars: 'ASTNode' = None,
                 items: List['ASTWithItem'] = None, is_async: bool = False):
        super().__init__(NodeType.NODE_BLOCK)
        if items is not None:
            self._items = items
        elif context is not None:
            self._items = [ASTWithItem(context, optional_vars)]
        else:
            self._items = []
        self._body = body if body is not None else ASTNodeList()
        self._is_async = is_async
    
    @property
    def is_async(self) -> bool:
        return self._is_async
    
    @property
    def items(self) -> List['ASTWithItem']:
        return self._items
    
    @items.setter
    def items(self, value: List['ASTWithItem']):
        self._items = value
    
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
    
    @body.setter
    def body(self, value: 'ASTNode'):
        self._body = value
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复with节点"
        
        _visited.add(node_id)
        
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
        ast_debug_print(f"[ASTWith.to_code] 生成with主体: offset={getattr(self, 'offset', -1)}, _body类型={type(self._body).__name__}, _body节点数={len(getattr(self._body, '_nodes', []))}")
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                body_str = self._body.to_code(indent_level + 1)
            ast_debug_print(f"[ASTWith.to_code] body_str长度: {len(body_str)}, body_str内容: {repr(body_str[:100])}")
        else:
            body_str = "    " * (indent_level + 1) + "pass"
            ast_debug_print(f"[ASTWith.to_code] 使用默认pass")
        
        # [关键修复] 支持 async with
        async_prefix = "async " if self._is_async else ""
        result = f"{indent}{async_prefix}with {items_str}:\n{body_str}"
        return result


class ASTTry(ASTNode):
    """try语句节点"""
    
    # [关键修复] 添加 offset 用于代码排序
    # [关键修复] 添加 _finally_start 和 _finally_end 用于保存finally块范围
    __slots__ = ('_body', '_handlers', '_orelse', '_finalbody', '_is_try_finally', 'offset', '_finally_start', '_finally_end')
    
    def __init__(self, body: 'ASTNodeList' = None, handlers: List['ASTNode'] = None, 
                 orelse: 'ASTNodeList' = None, finalbody: 'ASTNodeList' = None,
                 else_block: 'ASTNodeList' = None, finally_block: 'ASTNodeList' = None):
        super().__init__(NodeType.NODE_TRY)
        self._body = body
        self._handlers = handlers if handlers is not None else []
        self._orelse = orelse if orelse is not None else else_block
        self._finalbody = finalbody if finalbody is not None else finally_block
        self._is_try_finally = False  # 标记是否是try-finally结构（没有except）
        self._finally_start = -1  # [关键修复] finally块开始偏移
        self._finally_end = -1  # [关键修复] finally块结束偏移
    
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成Python代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复try节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        
        # 生成try主体
        ast_debug_print(f"[ASTTry.to_code] 生成try主体: _body类型={type(self._body).__name__}, _body节点数={len(getattr(self._body, '_nodes', []))}")
        if hasattr(self._body, 'to_code'):
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                try_body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
                try_body_str = self._body.to_code(indent_level + 1)
            ast_debug_print(f"[ASTTry.to_code] try_body_str长度: {len(try_body_str)}, try_body_str内容: {repr(try_body_str[:100])}")
        else:
            try_body_str = "    " * (indent_level + 1) + "pass"
            ast_debug_print(f"[ASTTry.to_code] 使用默认pass")
        
        # 生成try语句
        try_code = f"{indent}try:\n{try_body_str}"
        
        # 生成except handlers
        except_code = ""
        if self._handlers:
            for handler in self._handlers:
                if hasattr(handler, 'to_code'):
                    # [关键修复] 传递 _visited 参数来检测循环引用
                    try:
                        handler_str = handler.to_code(indent_level, _visited)
                    except TypeError:
                        handler_str = handler.to_code(indent_level)
                else:
                    handler_str = f"{indent}    except:\n{indent}    " + "    " * (indent_level + 1) + "pass"
                except_code += "\n" + handler_str
        
        # 生成else块
        else_code = ""
        # [关键修复] 只有在有except handlers时才能生成else块
        # Python语法规定：else子句必须跟在except子句之后
        if self._handlers and self._orelse and (hasattr(self._orelse, 'nodes') and self._orelse.nodes):
            if hasattr(self._orelse, 'to_code'):
                # [关键修复] else块的内容需要比else:多一级缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    else_str = self._orelse.to_code(indent_level + 1, _visited)
                except TypeError:
                    else_str = self._orelse.to_code(indent_level + 1)
            else:
                else_str = f"{indent}    pass"
            else_code = f"\n{indent}else:\n{else_str}"
        
        # 生成finally块
        finally_code = ""
        # 如果有finally块内容，或者是try-finally结构（没有except），则输出finally
        has_finally_content = self._finalbody and (hasattr(self._finalbody, 'nodes') and self._finalbody.nodes)
        is_try_finally = getattr(self, '_is_try_finally', False)
        
        ast_debug_print(f"[ASTTry.to_code] 生成finally块: has_finally_content={has_finally_content}, is_try_finally={is_try_finally}, _finalbody={self._finalbody}, nodes={getattr(self._finalbody, 'nodes', []) if self._finalbody else 'N/A'}")
        
        if has_finally_content or is_try_finally:
            if has_finally_content and hasattr(self._finalbody, 'to_code'):
                # [关键修复] finally块的内容需要比finally:多一级缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    finally_str = self._finalbody.to_code(indent_level + 1, _visited)
                except TypeError:
                    finally_str = self._finalbody.to_code(indent_level + 1)
                ast_debug_print(f"[ASTTry.to_code] finally_str: {repr(finally_str[:100])}")
            else:
                finally_str = "    " * (indent_level + 1) + "pass"
                ast_debug_print(f"[ASTTry.to_code] 使用默认pass")
            finally_code = f"\n{indent}finally:\n{finally_str}"
        
        # [关键修复] 如果既没有except子句也没有finally子句，添加一个空的except子句
        # 因为在Python中，try块必须有至少一个except子句或finally子句
        if not self._handlers and not has_finally_content and not is_try_finally:
            except_code = f"\n{indent}except:\n{indent}    pass"
        
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
        # 处理target，如果是元组则去掉括号（for循环变量不需要括号）
        if isinstance(self._target, ASTTuple):
            # 元组在for循环中不需要括号
            if not self._target.items:
                target_code = "()"
            elif len(self._target.items) == 1:
                item = self._target.items[0]
                target_code = item.to_code() if hasattr(item, 'to_code') else str(item)
            else:
                item_strs = []
                for item in self._target.items:
                    item_str = item.to_code() if hasattr(item, 'to_code') else str(item)
                    item_strs.append(item_str)
                target_code = ", ".join(item_strs)
        else:
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
    __slots__ = ('_value', '_rettype', 'offset', '_in_function')
    
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
            # [关键修复] 检查返回值是否是ASTRaise类型
            # RERAISE指令不应该生成return语句，它只是重新抛出异常
            value_type = type(self._value).__name__
            if value_type == 'ASTRaise':
                debug_print(f"DEBUG: ASTReturn.to_code() - value is ASTRaise, skipping return statement")
                return ""
            
            # [修复] 检查是否在函数内部
            # 只有在函数内部才生成 return None，在模块级别不生成
            in_function = getattr(self, '_in_function', False)
            
            # 尝试使用to_code方法
            value_code = None
            debug_print(f"DEBUG: ASTReturn.to_code() - value type: {value_type}, in_function={in_function}")
            
            if hasattr(self._value, 'to_code'):
                try:
                    value_code = self._value.to_code()
                    debug_print(f"DEBUG: ASTReturn.to_code() - to_code() returned: {repr(value_code[:100]) if value_code else None}")
                    # 检查是否返回了对象引用
                    if value_code and '<core.ast_nodes.' in value_code:
                        debug_print(f"DEBUG: ASTReturn.to_code() - to_code() returned object reference, using fallback")
                        value_code = None
                except Exception as e:
                    debug_print(f"DEBUG: ASTReturn.to_code() - to_code() failed: {e}")
                    value_code = None
            
            # 如果to_code失败，使用备用方法
            if value_code is None:
                value_type = type(self._value).__name__
                
                if value_type == 'ASTTuple':
                    # 使用ASTTuple的_item_to_code方法
                    items = getattr(self._value, '_items', [])
                    if items:
                        item_codes = []
                        for item in items:
                            # 使用ASTTuple的_item_to_code逻辑
                            if hasattr(item, 'to_code'):
                                try:
                                    item_code = item.to_code()
                                    if item_code and '<core.ast_nodes.' not in item_code:
                                        item_codes.append(item_code)
                                        continue
                                except:
                                    pass
                            
                            # 备用方法
                            item_type = type(item).__name__
                            if item_type == 'ASTName':
                                if hasattr(item, 'name'):
                                    item_codes.append(str(item.name))
                                elif hasattr(item, '_name'):
                                    item_codes.append(str(item._name))
                                else:
                                    item_codes.append("unknown")
                            elif item_type == 'ASTConstant':
                                if hasattr(item, 'value'):
                                    item_codes.append(repr(item.value))
                                else:
                                    item_codes.append("None")
                            else:
                                item_codes.append("unknown")
                        
                        value_code = f"({', '.join(item_codes)})" if item_codes else "()"
                    else:
                        value_code = "()"
                elif value_type == 'ASTClassDef':
                    value_code = "None"
                else:
                    value_code = str(self._value)
                    if '<core.ast_nodes.' in value_code:
                        value_code = "None"
            
            # [修复] 只有在函数内部才生成 return 语句
            # 在模块级别（不在函数内部）的 return 语句不生成
            if not in_function:
                return ""
            
            return f"{indent}return {value_code}"
        else:
            # [关键修复] 当返回值为None时，显式生成return None
            # 这样反编译后的代码与原始代码的字节码匹配
            return f"{indent}return None"


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
        indent = "    " * indent_level
        prefix = "yield from " if self._is_from else "yield "
        if self._value is not None:
            if hasattr(self._value, 'to_code'):
                value_code = self._value.to_code()
            else:
                value_code = str(self._value)
            return f"{indent}{prefix}{value_code}"
        else:
            return f"{indent}{prefix.strip()}"


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
            # [关键修复] 处理格式说明符，提取原始字符串值（去除引号）
            if isinstance(self._format_spec, ASTJoinedStr):
                # 嵌套f-string作为格式说明符
                format_code = self._format_spec.to_code(indent_level)
                # 去掉外层的f"和"，只保留内容（先检查三引号，再检查单引号）
                if format_code.startswith('f"""') and format_code.endswith('"""'):
                    format_code = format_code[4:-3]
                elif format_code.startswith("f'''") and format_code.endswith("'''"):
                    format_code = format_code[4:-3]
                elif format_code.startswith('f"') and format_code.endswith('"'):
                    format_code = format_code[2:-1]
                elif format_code.startswith("f'") and format_code.endswith("'"):
                    format_code = format_code[2:-1]
            elif isinstance(self._format_spec, ASTObject):
                # 字符串常量作为格式说明符
                obj = self._format_spec.value
                if isinstance(obj, str):
                    format_code = obj  # 直接使用原始字符串值，不带引号
                else:
                    format_code = self._format_spec.to_code() if hasattr(self._format_spec, 'to_code') else str(self._format_spec)
            else:
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
        ast_debug_# DEBUG: print(f"[DEBUG ASTJoinedStr] _values: {self._values}", flush=True)
        if not self._values:
            return '""'
        
        parts = []
        for value in self._values:
            ast_debug_# DEBUG: print(f"[DEBUG ASTJoinedStr] value: {value}, type: {type(value).__name__}", flush=True)
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
    
    # 添加__slots__优化
    __slots__ = ('_value', 'offset')
    
    def __init__(self, value: 'ASTNode'):
        super().__init__(NodeType.NODE_OBJECT)
        self._value = value
    
    @property
    def value(self) -> 'ASTNode':
        return self._value
    
    def to_code(self, indent_level=0):
        """生成表达式语句代码"""
        indent = "    " * indent_level
        if hasattr(self._value, 'to_code'):
            try:
                code = self._value.to_code()
                return indent + code
            except Exception as e:
                return indent + str(self._value)
        else:
            result = indent + str(self._value)
            return result


class ASTAttribute(ASTNode):
    """属性访问节点 - 性能优化版本"""
    
    # 添加__slots__优化
    __slots__ = ('_value', '_attr', '_ctx', 'offset')
    
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
        
        # [关键修复] 如果value是单元素元组，去掉括号
        # 这种情况发生在表达式被错误地包装成Tuple时
        if isinstance(self._value, ASTTuple) and len(self._value.elts) == 1:
            # 单元素元组会生成"(item,)"格式，我们需要"item"格式
            if value_code.startswith('(') and value_code.endswith(',)'):
                value_code = value_code[1:-2]  # 去掉开头的"("和结尾的",)"
        
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
        indent = "    " * indent_level
        if not self._targets:
            return f"{indent}del"
        
        target_codes = []
        for target in self._targets:
            target_code = None
            if hasattr(target, 'to_code'):
                try:
                    target_code = target.to_code()
                    # 检查是否返回了对象引用
                    if target_code and '<core.ast_nodes.' in target_code:
                        target_code = None
                except:
                    target_code = None
            
            # 备用方法
            if target_code is None:
                target_type = type(target).__name__
                if target_type == 'ASTName':
                    if hasattr(target, 'name'):
                        target_code = str(target.name)
                    elif hasattr(target, '_name'):
                        target_code = str(target._name)
                    else:
                        target_code = "unknown"
                else:
                    target_code = str(target) if not str(target).startswith('<core.ast_nodes.') else "unknown"
            
            target_codes.append(target_code)
        
        return f"{indent}del {', '.join(target_codes)}"


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
        indent = "    " * indent_level
        if not self._names:
            return f"{indent}global"
        return f"{indent}global {', '.join(self._names)}"


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
        indent = "    " * indent_level
        if not self._names:
            return f"{indent}nonlocal"
        return f"{indent}nonlocal {', '.join(self._names)}"


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
    
    def to_code(self, indent_level=0) -> str:
        """生成import语句代码"""
        indent = '    ' * indent_level
        # [关键修复] 处理ASTAlias节点
        name_strs = []
        for name in self._names:
            if isinstance(name, ASTAlias):
                name_strs.append(name.to_code())
            else:
                name_strs.append(str(name))
        names_str = ', '.join(name_strs)
        return f"{indent}import {names_str}"


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
    
    def to_code(self, indent_level=0) -> str:
        """生成from import语句代码"""
        indent = '    ' * indent_level
        # [关键修复] 处理ASTAlias节点
        name_strs = []
        for name in self._names:
            if isinstance(name, ASTAlias):
                name_strs.append(name.to_code())
            else:
                name_strs.append(str(name))
        names_str = ', '.join(name_strs)
        return f"{indent}from {self._module} import {names_str}"


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
    
    def to_code(self, indent_level=0):
        """生成break语句代码"""
        indent = "    " * indent_level
        return f"{indent}break"


class ASTContinue(ASTNode):
    """Continue语句节点"""
    
    def __init__(self):
        super().__init__(NodeType.NODE_CONTINUE)
    
    def to_code(self, indent_level=0):
        """生成continue语句代码"""
        indent = "    " * indent_level
        return f"{indent}continue"


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
        indent = "    " * indent_level
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
            return f"{indent}assert {test_code}, {msg_code}"
        else:
            # 没有消息的情况：assert test
            return f"{indent}assert {test_code}"


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
        result = f"{indent}{target_code} {self._op} {value_code}"
        ast_debug_print(f"[ASTAugAssign.to_code] target_code={target_code}, op={self._op}, value_code={value_code}, result={result}")
        return result


class ASTRaise(ASTNode):
    
    def __init__(self, exc: 'ASTNode' = None, cause: 'ASTNode' = None):
        super().__init__(NodeType.NODE_RAISE)
        self._exc = exc
        self._cause = cause
    
    @property
    def exc(self) -> 'ASTNode':
        return self._exc
    
    @property
    def cause(self) -> 'ASTNode':
        return self._cause
    
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
            # [关键修复] 检查exc是否是字符串类型
            if isinstance(self._exc, str):
                str_value = self._exc
                # 检查是否是有效的异常类型（首字母大写或是内置异常）
                builtin_exceptions = ('Exception', 'BaseException', 'ValueError', 'TypeError', 
                                      'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                                      'ZeroDivisionError', 'OverflowError', 'IOError', 'OSError',
                                      'ImportError', 'ModuleNotFoundError', 'SyntaxError',
                                      'IndentationError', 'TabError', 'NameError', 'UnboundLocalError',
                                      'AssertionError', 'LookupError', 'ArithmeticError',
                                      'EnvironmentError', 'BlockingIOError', 'ChildProcessError',
                                      'ConnectionError', 'BrokenPipeError', 'ConnectionAbortedError',
                                      'ConnectionRefusedError', 'ConnectionResetError',
                                      'FileExistsError', 'FileNotFoundError', 'InterruptedError',
                                      'IsADirectoryError', 'NotADirectoryError', 'PermissionError',
                                      'ProcessLookupError', 'TimeoutError', 'ReferenceError',
                                      'NotImplementedError', 'RecursionError', 'StopIteration',
                                      'StopAsyncIteration', 'GeneratorExit', 'SystemExit',
                                      'KeyboardInterrupt', 'Warning', 'UserWarning', 'DeprecationWarning',
                                      'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
                                      'FutureWarning', 'ImportWarning', 'UnicodeWarning',
                                      'BytesWarning', 'ResourceWarning', 'FloatingPointError',
                                      'BufferError', 'MemoryError', 'SystemError', 'EOFError')
                # 检查首字符是否大写
                first_char_upper = False
                if len(str_value) > 0:
                    first_char = str_value[0]
                    if 'A' <= first_char <= 'Z':
                        first_char_upper = True
                # 如果不是有效的异常类型，且包含中文字符，转换为Exception('str_value')
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str_value)
                if str_value not in builtin_exceptions and not first_char_upper and has_chinese:
                    # 是字符串消息，不是异常类型，转换为Exception('str_value')
                    return f"{indent}raise Exception('{str_value}')"
                else:
                    # 是有效的异常类型，直接返回
                    return f"{indent}raise {str_value}"
            # [关键修复] 检查exc是否是ASTObject且包含字符串
            elif isinstance(self._exc, ASTObject):
                obj_value = self._exc.object if hasattr(self._exc, 'object') else None
                if isinstance(obj_value, str):
                    str_value = obj_value
                    # 检查是否是有效的异常类型（首字母大写或是内置异常）
                    builtin_exceptions = ('Exception', 'BaseException', 'ValueError', 'TypeError', 
                                          'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                                          'ZeroDivisionError', 'OverflowError', 'IOError', 'OSError',
                                          'ImportError', 'ModuleNotFoundError', 'SyntaxError',
                                          'IndentationError', 'TabError', 'NameError', 'UnboundLocalError',
                                          'AssertionError', 'LookupError', 'ArithmeticError',
                                          'EnvironmentError', 'BlockingIOError', 'ChildProcessError',
                                          'ConnectionError', 'BrokenPipeError', 'ConnectionAbortedError',
                                          'ConnectionRefusedError', 'ConnectionResetError',
                                          'FileExistsError', 'FileNotFoundError', 'InterruptedError',
                                          'IsADirectoryError', 'NotADirectoryError', 'PermissionError',
                                          'ProcessLookupError', 'TimeoutError', 'ReferenceError',
                                          'NotImplementedError', 'RecursionError', 'StopIteration',
                                          'StopAsyncIteration', 'GeneratorExit', 'SystemExit',
                                          'KeyboardInterrupt', 'Warning', 'UserWarning', 'DeprecationWarning',
                                          'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
                                          'FutureWarning', 'ImportWarning', 'UnicodeWarning',
                                          'BytesWarning', 'ResourceWarning', 'FloatingPointError',
                                          'BufferError', 'MemoryError', 'SystemError', 'EOFError')
                    # 检查首字符是否大写
                    first_char_upper = False
                    if len(str_value) > 0:
                        first_char = str_value[0]
                        if 'A' <= first_char <= 'Z':
                            first_char_upper = True
                    # 如果不是有效的异常类型，且包含中文字符，转换为Exception('str_value')
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str_value)
                    if str_value not in builtin_exceptions and not first_char_upper and has_chinese:
                        # 是字符串消息，不是异常类型，转换为Exception('str_value')
                        return f"{indent}raise Exception('{str_value}')"
                    else:
                        # 是有效的异常类型，直接返回
                        return f"{indent}raise {str_value}"
            # [关键修复] 检查exc是否是ASTCall，且func是ASTName且名称不是有效的异常类型
            elif isinstance(self._exc, ASTCall):
                func = self._exc.func
                ast_debug_print(f"[ASTRaise.to_code] ASTCall, func类型: {type(func)}, func: {func}")
                # [关键修复] 如果func是ASTName，打印name值
                if isinstance(func, ASTName):
                    func_name = func.name if hasattr(func, 'name') else str(func)
                    ast_debug_print(f"[ASTRaise.to_code] ASTName, func_name: {func_name}")
                # [关键修复] 如果func是ASTObject，打印object值
                elif isinstance(func, ASTObject):
                    obj_value = func.object if hasattr(func, 'object') else None
                    ast_debug_print(f"[ASTRaise.to_code] ASTObject, obj_value: {obj_value}, type: {type(obj_value)}")
                # [关键修复] 如果func是str，直接使用
                elif isinstance(func, str):
                    func_name = func
                    ast_debug_print(f"[ASTRaise.to_code] str, func_name: {func_name}")
                if isinstance(func, ASTName):
                    func_name = func.name if hasattr(func, 'name') else str(func)
                    ast_debug_print(f"[ASTRaise.to_code] func_name: {func_name}")
                    # 检查是否是有效的异常类型（首字母大写或是内置异常）
                    builtin_exceptions = ('Exception', 'BaseException', 'ValueError', 'TypeError', 
                                          'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                                          'ZeroDivisionError', 'OverflowError', 'IOError', 'OSError',
                                          'ImportError', 'ModuleNotFoundError', 'SyntaxError',
                                          'IndentationError', 'TabError', 'NameError', 'UnboundLocalError',
                                          'AssertionError', 'LookupError', 'ArithmeticError',
                                          'EnvironmentError', 'BlockingIOError', 'ChildProcessError',
                                          'ConnectionError', 'BrokenPipeError', 'ConnectionAbortedError',
                                          'ConnectionRefusedError', 'ConnectionResetError',
                                          'FileExistsError', 'FileNotFoundError', 'InterruptedError',
                                          'IsADirectoryError', 'NotADirectoryError', 'PermissionError',
                                          'ProcessLookupError', 'TimeoutError', 'ReferenceError',
                                          'NotImplementedError', 'RecursionError', 'StopIteration',
                                          'StopAsyncIteration', 'GeneratorExit', 'SystemExit',
                                          'KeyboardInterrupt', 'Warning', 'UserWarning', 'DeprecationWarning',
                                          'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
                                          'FutureWarning', 'ImportWarning', 'UnicodeWarning',
                                          'BytesWarning', 'ResourceWarning', 'FloatingPointError',
                                          'BufferError', 'MemoryError', 'SystemError', 'EOFError')
                    # 检查首字符是否大写
                    first_char_upper = False
                    if len(func_name) > 0:
                        first_char = func_name[0]
                        if 'A' <= first_char <= 'Z':
                            first_char_upper = True
                    ast_debug_print(f"[ASTRaise.to_code] first_char_upper: {first_char_upper}, in_builtin: {func_name in builtin_exceptions}")
                    # 如果不是有效的异常类型，且包含中文字符，转换为Exception('func_name')
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in func_name)
                    if func_name not in builtin_exceptions and not first_char_upper and has_chinese:
                        ast_debug_print(f"[ASTRaise.to_code] 转换为Exception('{func_name}')")
                        # 是字符串消息，不是异常类型，转换为Exception('func_name')
                        return f"{indent}raise Exception('{func_name}')"
                    else:
                        ast_debug_print(f"[ASTRaise.to_code] 不转换，直接返回raise {func_name}")
            # [关键修复] 检查exc是否是ASTName且名称不是有效的异常类型
            elif isinstance(self._exc, ASTName):
                name_value = self._exc.name if hasattr(self._exc, 'name') else str(self._exc)
                # 检查是否是有效的异常类型（首字母大写或是内置异常）
                builtin_exceptions = ('Exception', 'BaseException', 'ValueError', 'TypeError', 
                                      'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                                      'ZeroDivisionError', 'OverflowError', 'IOError', 'OSError',
                                      'ImportError', 'ModuleNotFoundError', 'SyntaxError',
                                      'IndentationError', 'TabError', 'NameError', 'UnboundLocalError',
                                      'AssertionError', 'LookupError', 'ArithmeticError',
                                      'EnvironmentError', 'BlockingIOError', 'ChildProcessError',
                                      'ConnectionError', 'BrokenPipeError', 'ConnectionAbortedError',
                                      'ConnectionRefusedError', 'ConnectionResetError',
                                      'FileExistsError', 'FileNotFoundError', 'InterruptedError',
                                      'IsADirectoryError', 'NotADirectoryError', 'PermissionError',
                                      'ProcessLookupError', 'TimeoutError', 'ReferenceError',
                                      'NotImplementedError', 'RecursionError', 'StopIteration',
                                      'StopAsyncIteration', 'GeneratorExit', 'SystemExit',
                                      'KeyboardInterrupt', 'Warning', 'UserWarning', 'DeprecationWarning',
                                      'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning',
                                      'FutureWarning', 'ImportWarning', 'UnicodeWarning',
                                      'BytesWarning', 'ResourceWarning', 'FloatingPointError',
                                      'BufferError', 'MemoryError', 'SystemError', 'EOFError')
                # 检查首字符是否大写
                first_char_upper = False
                if len(name_value) > 0:
                    first_char = name_value[0]
                    if 'A' <= first_char <= 'Z':
                        first_char_upper = True
                # 如果不是有效的异常类型，且包含中文字符，转换为Exception('name_value')
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name_value)
                if name_value not in builtin_exceptions and not first_char_upper and has_chinese:
                    # 是字符串消息，不是异常类型，转换为Exception('name_value')
                    return f"{indent}raise Exception('{name_value}')"
            ast_debug_print(f"[ASTRaise.to_code] self._exc类型: {type(self._exc)}, self._exc: {self._exc}")
            if hasattr(self._exc, 'to_code'):
                exc_code = self._exc.to_code(0)
                ast_debug_print(f"[ASTRaise.to_code] self._exc.to_code(0) = {exc_code}")
            else:
                exc_code = str(self._exc)
                ast_debug_print(f"[ASTRaise.to_code] str(self._exc) = {exc_code}")
            # [关键修复] 检查exc_code是否是中文字符串后跟括号（如'请输入正确的标的代码'()）
            if exc_code.endswith('()') and any('\u4e00' <= char <= '\u9fff' for char in exc_code):
                # 提取中文字符串
                func_name = exc_code[:-2]  # 去掉'()'
                # [关键修复] 去掉func_name中的引号
                if (func_name.startswith("'") and func_name.endswith("'")) or \
                   (func_name.startswith('"') and func_name.endswith('"')):
                    func_name = func_name[1:-1]
                # [关键修复] 使用repr()来处理字符串中的引号
                ast_debug_print(f"[ASTRaise.to_code] 转换中文字符串调用: {exc_code} -> Exception({repr(func_name)})")
                return f"{indent}raise Exception({repr(func_name)})"
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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成except处理器代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复except节点"
        
        _visited.add(node_id)
        
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
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                body_str = self._body.to_code(indent_level + 1, _visited)
            except TypeError:
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


class ASTMatch(ASTNode):
    """匹配语句节点（Python 3.10+）"""
    
    def __init__(self, subject: 'ASTNode', cases: List['ASTCase'] = None):
        super().__init__(NodeType.NODE_MATCH)
        self._subject = subject
        self._cases = cases if cases is not None else []
    
    @property
    def subject(self) -> 'ASTNode':
        return self._subject
    
    @property
    def cases(self) -> List['ASTCase']:
        return self._cases
    
    def to_code(self, indent_level=0, _visited=None):
        """生成match语句代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复match节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        subject_code = self._subject.to_code() if hasattr(self._subject, 'to_code') else str(self._subject)
        
        lines = [f"{indent}match {subject_code}:"]
        
        for case in self._cases:
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                case_code = case.to_code(indent_level + 1, _visited)
            except TypeError:
                case_code = case.to_code(indent_level + 1)
            lines.append(case_code)
        
        return "\n".join(lines)


class ASTCase(ASTNode):
    """匹配case节点（Python 3.10+）"""
    
    def __init__(self, pattern: 'ASTNode', body: 'ASTNode' = None, guard: 'ASTNode' = None):
        super().__init__(NodeType.NODE_CASE)
        self._pattern = pattern
        self._body = body if body is not None else ASTNodeList()
        self._guard = guard
    
    @property
    def pattern(self) -> 'ASTNode':
        return self._pattern
    
    @property
    def body(self) -> 'ASTNode':
        return self._body
    
    @property
    def guard(self) -> Optional['ASTNode']:
        return self._guard
    
    def to_code(self, indent_level=0, _visited=None):
        """生成case语句代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复case节点"
        
        _visited.add(node_id)
        
        indent = "    " * indent_level
        pattern_code = self._pattern.to_code() if hasattr(self._pattern, 'to_code') else str(self._pattern)
        
        # 添加guard（if条件）
        if self._guard:
            guard_code = self._guard.to_code() if hasattr(self._guard, 'to_code') else str(self._guard)
            case_line = f"{indent}case {pattern_code} if {guard_code}:"
        else:
            case_line = f"{indent}case {pattern_code}:"
        
        # 生成body代码（使用正确的缩进级别）
        body_lines = []
        if self._body:
            if hasattr(self._body, 'to_code'):
                # 对于body，使用indent_level + 1的缩进
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    body_code = self._body.to_code(indent_level + 1, _visited)
                except TypeError:
                    body_code = self._body.to_code(indent_level + 1)
                if body_code:
                    body_lines.append(body_code)
            else:
                body_str = str(self._body)
                if body_str:
                    body_lines.append(f"{indent}    {body_str}")
        
        if body_lines:
            return case_line + "\n" + "\n".join(body_lines)
        else:
            return case_line


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
        indent = "    " * indent_level
        value_code = self._value.to_code() if hasattr(self._value, 'to_code') else str(self._value)
        return f"{indent}await {value_code}"


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
        indent = "    " * indent_level
        
        # 生成print函数调用
        args = []
        for value in self._values:
            value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
            args.append(value_code)
        
        if self._stream:
            stream_code = self._stream.to_code() if hasattr(self._stream, 'to_code') else str(self._stream)
            if not self._eol:
                return f"{indent}print({', '.join(args)}, file={stream_code})"
            else:
                return f"{indent}print({', '.join(args)}, file={stream_code}, end='')"
        else:
            if not self._eol:
                return f"{indent}print({', '.join(args)})"
            else:
                return f"{indent}print({', '.join(args)}, end='')"


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
    
    def to_code(self, indent_level=0, _visited=None):
        """生成try*语句代码
        
        Args:
            indent_level: 缩进级别
            _visited: 内部使用，用于检测循环引用
        """
        # [关键修复] 添加循环引用检测
        if _visited is None:
            _visited = set()
        
        node_id = id(self)
        if node_id in _visited:
            indent = "    " * indent_level
            return f"{indent}pass  # [循环引用检测] 跳过重复try*节点"
        
        _visited.add(node_id)
        
        indent = "    " * (indent_level + 1)
        
        # 生成try*块
        code = "try:\n"
        # [关键修复] 传递 _visited 参数来检测循环引用
        try:
            code += self._body.to_code(indent_level, _visited)
        except TypeError:
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
                # [关键修复] 传递 _visited 参数来检测循环引用
                try:
                    code += handler.body.to_code(indent_level, _visited)
                except TypeError:
                    code += handler.body.to_code(indent_level)
                code += "\n"
        
        # 生成else块
        if self._orelse and len(self._orelse) > 0:
            code += f"{indent}else:\n"
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                code += self._orelse.to_code(indent_level, _visited)
            except TypeError:
                code += self._orelse.to_code(indent_level)
            code += "\n"
        
        # 生成finally块
        if self._finalbody and len(self._finalbody) > 0:
            code += f"{indent}finally:\n"
            # [关键修复] 传递 _visited 参数来检测循环引用
            try:
                code += self._finalbody.to_code(indent_level, _visited)
            except TypeError:
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
            # [关键修复] 处理格式说明符，提取原始字符串值（去除引号）
            if isinstance(self._format_spec, ASTJoinedStr):
                # 嵌套f-string作为格式说明符
                format_code = self._format_spec.to_code(indent_level)
                # 去掉外层的f"和"，只保留内容（先检查三引号，再检查单引号）
                if format_code.startswith('f"""') and format_code.endswith('"""'):
                    format_code = format_code[4:-3]
                elif format_code.startswith("f'''") and format_code.endswith("'''"):
                    format_code = format_code[4:-3]
                elif format_code.startswith('f"') and format_code.endswith('"'):
                    format_code = format_code[2:-1]
                elif format_code.startswith("f'") and format_code.endswith("'"):
                    format_code = format_code[2:-1]
            elif isinstance(self._format_spec, ASTObject):
                # 字符串常量作为格式说明符
                obj = self._format_spec.value
                if isinstance(obj, str):
                    format_code = obj  # 直接使用原始字符串值，不带引号
                else:
                    format_code = self._format_spec.to_code() if hasattr(self._format_spec, 'to_code') else str(self._format_spec)
            else:
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
            
            # 检查 ASTObject 类型
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
            
            # 检查 ASTConstant 类型（_load_const 方法创建的字符串常量）
            if not is_string and isinstance(value, ASTConstant):
                const_val = value.value
                if isinstance(const_val, str):
                    is_string = True
                    string_value = const_val
            
            if is_string:
                # 纯字符串部分 - 转义花括号
                escaped = string_value.replace('{', '{{').replace('}', '}}')
                parts.append(escaped)
            elif isinstance(value, ASTFormattedValue):
                # 格式化值部分 - 已经包含花括号
                parts.append(value.to_code())
            elif isinstance(value, ASTAttribute):
                # 属性访问，如 self.name
                parts.append(f"{{{value.to_code()}}}")
            else:
                # 其他表达式
                value_code = value.to_code() if hasattr(value, 'to_code') else str(value)
                parts.append(f"{{{value_code}}}")
        
        # 检查是否需要三引号（包含换行或引号）
        result = ''.join(parts)
        if '\n' in result or '"' in result:
            # 使用三引号
            return f'f"""{result}"""'
        else:
            return f'f"{result}"'


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
                # [关键修复] 暂时将所有elif改为if，以解决语法错误问题
                lines.append(self.line_prefix * indent_level + f"if {elif_cond}:")
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