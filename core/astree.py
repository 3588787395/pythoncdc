"""
AST构建和反编译模块
从字节码构建AST并生成可读的Python源代码
"""

from typing import List, Optional, Any, Tuple
import sys
from collections import deque
from enum import Enum

from .ast_nodes import *
from .pyc_stream import PycRef
from .fast_stack import FastStack


class BlockType:
    """块类型枚举，类似于C++版本的ASTBlock::BLK_*"""
    BLK_MAIN = 0
    BLK_FUNCTION = 1
    BLK_CLASS = 2
    BLK_LAMBDA = 3
    BLK_LIST_COMPREHENSION = 4
    BLK_SET_COMPREHENSION = 5
    BLK_DICT_COMPREHENSION = 6
    BLK_GENERATOR_EXPRESSION = 7
    BLK_IF = 8
    BLK_ELSE = 9
    BLK_ELIF = 10
    BLK_WHILE = 11
    BLK_FOR = 12
    BLK_TRY = 13
    BLK_EXCEPT = 14
    BLK_FINALLY = 15
    BLK_WITH = 16
    BLK_IMPORT = 17
    BLK_IMPORT_AS = 18
    BLK_IMPORT_FROM = 19
    BLK_ANNOTATION = 20
    BLK_COMPREHENSION = 21
    BLK_EXCEPT = 22
    BLK_ASYNC_FOR = 23
    BLK_ASYNC_WITH = 24
    BLK_ASYNC_LIST_COMPREHENSION = 25
    BLK_ASYNC_SET_COMPREHENSION = 26
    BLK_ASYNC_DICT_COMPREHENSION = 27
    BLK_ASYNC_GENERATOR_EXPRESSION = 28
    BLK_AWAIT = 29
    BLK_YIELD = 30
    BLK_YIELD_FROM = 31
    BLK_ANNOTATED = 32
    BLK_FSTRING = 33
    BLK_PATTERN_MATCH = 34
    BLK_PATTERN_CASE = 35
    BLK_PATTERN_GUARD = 36
    BLK_MATCH_CLASS = 37
    BLK_MATCH_AS = 38
    BLK_MATCH_OR = 39
    BLK_PATTERN_WILDCARD = 40
    BLK_PATTERN_SEQUENCE = 41
    BLK_PATTERN_MAPPING = 42
    BLK_PATTERN_VALUE = 43
    BLK_PATTERN_SINGLETON = 44
    BLK_PATTERN_SEQUENCE_ITEM = 45
    BLK_PATTERN_KEY_VALUE = 46
    BLK_PATTERN_CAPTURE = 47
    BLK_PATTERN_DOUBLE_STAR = 48
    BLK_CONTAINER = 99


class BlockState:
    """块状态类，类似于ASTBlock"""
    def __init__(self, blktype: int, end: int = 0, is_except: bool = False):
        self.blktype = blktype
        self.end = end
        self.is_except = is_except
        self.nodes: List[ASTNode] = []
        self.processed = False
        
    def type_str(self) -> str:
        """获取块类型字符串"""
        type_map = {
            BlockType.BLK_MAIN: "MAIN",
            BlockType.BLK_FUNCTION: "FUNCTION",
            BlockType.BLK_CLASS: "CLASS",
            BlockType.BLK_LAMBDA: "LAMBDA",
            BlockType.BLK_LIST_COMPREHENSION: "LIST_COMPREHENSION",
            BlockType.BLK_SET_COMPREHENSION: "SET_COMPREHENSION",
            BlockType.BLK_DICT_COMPREHENSION: "DICT_COMPREHENSION",
            BlockType.BLK_GENERATOR_EXPRESSION: "GENERATOR_EXPRESSION",
            BlockType.BLK_IF: "IF",
            BlockType.BLK_ELSE: "ELSE",
            BlockType.BLK_ELIF: "ELIF",
            BlockType.BLK_WHILE: "WHILE",
            BlockType.BLK_FOR: "FOR",
            BlockType.BLK_TRY: "TRY",
            BlockType.BLK_EXCEPT: "EXCEPT",
            BlockType.BLK_FINALLY: "FINALLY",
            BlockType.BLK_WITH: "WITH",
            BlockType.BLK_IMPORT: "IMPORT",
            BlockType.BLK_IMPORT_AS: "IMPORT_AS",
            BlockType.BLK_IMPORT_FROM: "IMPORT_FROM",
            BlockType.BLK_ANNOTATION: "ANNOTATION",
            BlockType.BLK_COMPREHENSION: "COMPREHENSION",
            BlockType.BLK_ASYNC_FOR: "ASYNC_FOR",
            BlockType.BLK_ASYNC_WITH: "ASYNC_WITH",
            BlockType.BLK_ASYNC_LIST_COMPREHENSION: "ASYNC_LIST_COMPREHENSION",
            BlockType.BLK_ASYNC_SET_COMPREHENSION: "ASYNC_SET_COMPREHENSION",
            BlockType.BLK_ASYNC_DICT_COMPREHENSION: "ASYNC_DICT_COMPREHENSION",
            BlockType.BLK_ASYNC_GENERATOR_EXPRESSION: "ASYNC_GENERATOR_EXPRESSION",
            BlockType.BLK_AWAIT: "AWAIT",
            BlockType.BLK_YIELD: "YIELD",
            BlockType.BLK_YIELD_FROM: "YIELD_FROM",
            BlockType.BLK_ANNOTATED: "ANNOTATED",
            BlockType.BLK_FSTRING: "FSTRING",
            BlockType.BLK_PATTERN_MATCH: "PATTERN_MATCH",
            BlockType.BLK_PATTERN_CASE: "PATTERN_CASE",
            BlockType.BLK_PATTERN_GUARD: "PATTERN_GUARD",
            BlockType.BLK_MATCH_CLASS: "MATCH_CLASS",
            BlockType.BLK_MATCH_AS: "MATCH_AS",
            BlockType.BLK_MATCH_OR: "MATCH_OR",
            BlockType.BLK_PATTERN_WILDCARD: "PATTERN_WILDCARD",
            BlockType.BLK_PATTERN_SEQUENCE: "PATTERN_SEQUENCE",
            BlockType.BLK_PATTERN_MAPPING: "PATTERN_MAPPING",
            BlockType.BLK_PATTERN_VALUE: "PATTERN_VALUE",
            BlockType.BLK_PATTERN_SINGLETON: "PATTERN_SINGLETON",
            BlockType.BLK_PATTERN_SEQUENCE_ITEM: "PATTERN_SEQUENCE_ITEM",
            BlockType.BLK_PATTERN_KEY_VALUE: "PATTERN_KEY_VALUE",
            BlockType.BLK_PATTERN_CAPTURE: "PATTERN_CAPTURE",
            BlockType.BLK_PATTERN_DOUBLE_STAR: "PATTERN_DOUBLE_STAR",
            BlockType.BLK_CONTAINER: "CONTAINER"
        }
        return type_map.get(self.blktype, f"UNKNOWN({self.blktype})")
    
    def append(self, node: ASTNode) -> None:
        """添加节点到块"""
        self.nodes.append(node)
        
    def init(self) -> None:
        """初始化块"""
        self.processed = False
        self.nodes = []
        
    def removeLast(self) -> None:
        """移除最后一个节点"""
        if self.nodes:
            self.nodes.pop()


# 全局状态变量
_clean_build = True


class ASTCondBlock(ASTNodeList):
    """条件块节点，类似于C++版本的ASTCondBlock"""
    
    class InitCond(Enum):
        UNINITED = 0
        POPPED = 1
        PRE_POPPED = 2
    
    def __init__(self, blk_type: int, end: int, condition: ASTNode, negative: bool = False):
        super().__init__([])
        self._blk_type = blk_type
        self._end = end
        self._condition = condition
        self._negative = negative
        self._initialized = False
    
    @property
    def condition(self) -> ASTNode:
        return self._condition
    
    @property
    def negative(self) -> bool:
        return self._negative
    
    @property
    def initialized(self) -> bool:
        return self._initialized
    
    def init(self) -> None:
        """初始化条件块"""
        self._initialized = True
        super().init()
    
    def to_code(self, indent_level=0):
        """生成条件块代码"""
        if not self._condition:
            return ""
        
        condition_code = self._condition.to_code() if hasattr(self._condition, 'to_code') else str(self._condition)
        
        # 处理否定条件
        if self._negative:
            condition_code = f"not ({condition_code})"
        
        # 根据块类型生成代码
        if self._blk_type == BlockType.BLK_IF:
            return "    " * indent_level + f"if {condition_code}:"
        elif self._blk_type == BlockType.BLK_ELIF:
            return "    " * indent_level + f"elif {condition_code}:"
        elif self._blk_type == BlockType.BLK_WHILE:
            return "    " * indent_level + f"while {condition_code}:"
        else:
            return "    " * indent_level + f"if {condition_code}:"


class ASTIterBlock(ASTNodeList):
    """迭代块节点，类似于C++版本的ASTIterBlock"""
    
    def __init__(self, blk_type: int, start: int, end: int, iter_node: ASTNode):
        super().__init__([])
        self._blk_type = blk_type
        self._start = start
        self._end = end
        self._iter = iter_node
        self._index = None
        self._condition = None
        self._is_comprehension = False
        self._initialized = False
    
    @property
    def iter_node(self) -> ASTNode:
        return self._iter
    
    @property
    def index(self) -> Optional[ASTNode]:
        return self._index
    
    @property
    def condition(self) -> Optional[ASTNode]:
        return self._condition
    
    @property
    def is_comprehension(self) -> bool:
        return self._is_comprehension
    
    @property
    def start(self) -> int:
        return self._start
    
    def set_index(self, index: ASTNode) -> None:
        """设置索引"""
        self._index = index
        self.init()
    
    def set_condition(self, condition: ASTNode) -> None:
        """设置条件"""
        self._condition = condition
    
    def set_comprehension(self, is_comprehension: bool) -> None:
        """设置是否为推导式"""
        self._is_comprehension = is_comprehension
    
    def init(self) -> None:
        """初始化迭代块"""
        self._initialized = True
        super().init()
    
    def to_code(self, indent_level=0):
        """生成迭代块代码"""
        if not self._iter:
            return ""
        
        iter_code = self._iter.to_code() if hasattr(self._iter, 'to_code') else str(self._iter)
        
        # 根据块类型生成代码
        if self._blk_type == BlockType.BLK_FOR:
            if self._index:
                index_code = self._index.to_code() if hasattr(self._index, 'to_code') else str(self._index)
                return "    " * indent_level + f"for {index_code} in {iter_code}:"
            else:
                return "    " * indent_level + f"for item in {iter_code}:"
        elif self._blk_type == BlockType.BLK_ASYNC_FOR:
            if self._index:
                index_code = self._index.to_code() if hasattr(self._index, 'to_code') else str(self._index)
                return "    " * indent_level + f"async for {index_code} in {iter_code}:"
            else:
                return "    " * indent_level + f"async for item in {iter_code}:"
        else:
            return "    " * indent_level + f"for item in {iter_code}:"


class ASTWithBlock(ASTNodeList):
    """with块节点，类似于C++版本的ASTWithBlock"""
    
    def __init__(self, end: int):
        super().__init__([])
        self._end = end
        self._expr = None
        self._var = None
        self._initialized = False
    
    @property
    def expr(self) -> Optional[ASTNode]:
        return self._expr
    
    @property
    def var(self) -> Optional[ASTNode]:
        return self._var
    
    def set_expr(self, expr: ASTNode) -> None:
        """设置表达式"""
        self._expr = expr
        self.init()
    
    def set_var(self, var: ASTNode) -> None:
        """设置变量"""
        self._var = var
    
    def init(self) -> None:
        """初始化with块"""
        self._initialized = True
        super().init()
    
    def to_code(self, indent_level=0):
        """生成with块代码"""
        if not self._expr:
            return ""
        
        expr_code = self._expr.to_code() if hasattr(self._expr, 'to_code') else str(self._expr)
        
        if self._var:
            var_code = self._var.to_code() if hasattr(self._var, 'to_code') else str(self._var)
            return "    " * indent_level + f"with {expr_code} as {var_code}:"
        else:
            return "    " * indent_level + f"with {expr_code}:"


class ASTContainerBlock(ASTNodeList):
    """容器块节点，类似于C++版本的ASTContainerBlock"""
    
    def __init__(self, finally_offset: int, except_offset: int = 0):
        super().__init__([])
        self._finally_offset = finally_offset
        self._except_offset = except_offset
    
    @property
    def has_finally(self) -> bool:
        return self._finally_offset != 0
    
    @property
    def has_except(self) -> bool:
        return self._except_offset != 0
    
    @property
    def finally_offset(self) -> int:
        return self._finally_offset
    
    @property
    def except_offset(self) -> int:
        return self._except_offset
    
    def set_except(self, except_offset: int) -> None:
        """设置except偏移"""
        self._except_offset = except_offset
    
    def to_code(self, indent_level=0):
        """生成容器块代码"""
        # 容器块通常不直接生成代码，而是包含其他块
        return ""
_in_lambda = False
_print_docstring_and_globals = False
_print_class_docstring = True


def stack_pop_top(stack: FastStack) -> ASTNode:
    """出栈操作，类似于C++版本的StackPopTop"""
    node = stack.top()
    stack.pop()
    return node


def check_if_expr(stack: FastStack, curblock: BlockState) -> None:
    """
    检测三元表达式
    参考C++版本：ASTree.cpp::CheckIfExpr
    编译器为if/else语句块和if-expression（ternary operator）生成非常相似的字节码
    这里尝试猜测刚刚完成的else语句是否是if-expression的一部分
    如果是，从块中移除语句并将三元节点推入栈顶
    """
    if stack.empty():
        return
    if len(curblock.nodes) < 2:
        return
    
    # 获取块中的节点
    nodes = curblock.nodes
    
    # 最后一个应该是"else"块，前一个应该是"if"（可能是"for"等）
    if len(nodes) >= 2:
        last_node = nodes[-1]
        second_last_node = nodes[-2]
        
        # 检查是否是if-else模式
        if (isinstance(last_node, BlockState) and 
            isinstance(second_last_node, BlockState) and
            last_node.blktype == BlockType.BLK_ELSE and
            second_last_node.blktype == BlockType.BLK_IF):
            
            else_expr = stack_pop_top(stack)
            curblock.removeLast()
            
            if_block = curblock.nodes[-1] if curblock.nodes else None
            if_expr = stack_pop_top(stack)
            curblock.removeLast()
            
            # 创建三元表达式节点
            ternary_node = ASTTernary(if_block, if_expr, else_expr)
            stack.push(ternary_node)


def append_to_chain_store(chain_store: ASTNode, item: ASTNode, 
                         stack: FastStack, curblock: BlockState) -> None:
    """
    添加到链式存储
    参考C++版本：ASTree.cpp::append_to_chain_store
    """
    try:
        # 如果链式存储不存在，创建新的
        if chain_store is None:
            chain_store = ASTChainStore([], item)
            stack.push(chain_store)
        else:
            # 添加项目到现有的链式存储
            if isinstance(chain_store, ASTChainStore):
                # 获取当前节点列表并添加新项目
                nodes = chain_store.nodes()[:]  # 复制列表
                nodes.append(item)
                
                # 创建新的链式存储
                new_chain_store = ASTChainStore(nodes, chain_store.src())
                stack.push(new_chain_store)
            else:
                # 如果不是链式存储，则创建新的
                new_chain_store = ASTChainStore([item], item)
                stack.push(new_chain_store)
                
    except Exception as e:
        # 错误处理
        print(f"Error in append_to_chain_store: {e}")
        # 错误时至少将项目推入栈
        stack.push(item)


def build_from_code(code: PycRef, mod: Any) -> ASTNode:
    """
    从字节码构建AST
    这是核心函数，将Python字节码转换为抽象语法树
    参考C++版本：ASTree.cpp::BuildFromCode (约300行)
    """
    # 创建字节码缓冲区
    from .pyc_stream import PycBuffer
    source = PycBuffer(code.code().value(), code.code().length())
    
    # 创建堆栈
    stack_size = 20 if mod.major_ver() == 1 else code.stack_size()
    stack = FastStack(stack_size)
    
    # 堆栈历史记录
    stack_hist = []
    
    # 块栈
    blocks = []
    defblock = BlockState(BlockType.BLK_MAIN)
    defblock.init()
    curblock = defblock
    blocks.append(defblock)
    
    # 解析参数
    opcode = 0
    operand = 0
    curpos = 0
    pos = 0
    unpack = 0
    else_pop = False
    need_try = False
    variable_annotations = False
    
    # 字节码映射
    from ..bytecode.bytecode_ops import Opcode
    
    while not source.at_eof():
        curpos = pos
        
        # 读取下一条字节码
        opcode, operand, pos = bc_next(source, mod, pos)
        
        # 处理异常
        if need_try and opcode != Opcode.SETUP_EXCEPT_A:
            need_try = False
            
            # 为except/finally语句存储当前堆栈
            stack_hist.append(stack.copy())
            tryblock = BlockState(BlockType.BLK_TRY, curblock.end, True)
            blocks.append(tryblock)
            curblock = blocks[-1]
        
        # 处理else分支
        elif else_pop and opcode not in [
            Opcode.JUMP_FORWARD_A,
            Opcode.JUMP_IF_FALSE_A,
            Opcode.JUMP_IF_FALSE_OR_POP_A,
            Opcode.POP_JUMP_IF_FALSE_A,
            Opcode.POP_JUMP_FORWARD_IF_FALSE_A,
            Opcode.JUMP_IF_TRUE_A,
            Opcode.JUMP_IF_TRUE_OR_POP_A,
            Opcode.POP_JUMP_IF_TRUE_A,
            Opcode.POP_JUMP_FORWARD_IF_TRUE_A,
            Opcode.POP_BLOCK
        ]:
            else_pop = False
            
            prev = curblock
            while prev.end < pos and prev.blktype != BlockType.BLK_MAIN:
                if prev.blktype != BlockType.BLK_CONTAINER:
                    if prev.end == 0:
                        break
                    
                    # 从历史记录中弹出
                    if stack_hist:
                        stack_hist.pop()
                
                blocks.pop()
                
                if not blocks:
                    break
                
                curblock = blocks[-1]
                curblock.append(prev.cast(ASTNode))
                
                prev = curblock
                
                check_if_expr(stack, curblock)
        
        # 处理各种字节码指令
        result = handle_opcode(opcode, operand, stack, curblock, source, mod, blocks, pos)
        if result is not None:
            opcode, operand = result
    
    # 构建最终的AST根节点
    if curblock.nodes:
        return curblock.nodes[0] if len(curblock.nodes) == 1 else ASTNodeList(curblock.nodes)
    
    return ASTNode()


def handle_opcode(opcode: int, operand: int, stack: FastStack, curblock: BlockState,
                  source: Any, mod: Any, blocks: List[BlockState], pos: int) -> Tuple[int, int]:
    """
    处理字节码指令
    这是主要的字节码解析循环
    """
    from ..bytecode.bytecode_ops import Opcode
    
    if opcode in [Opcode.BINARY_OP_A]:
        # 处理二元操作符
        from .ast_nodes import ASTBinary
        
        if opcode == Opcode.BINARY_OP_A:
            op = ASTBinary.from_binary_op(operand)
            if op == ASTBinary.BIN_INVALID:
                print(f"Unsupported BINARY_OP operand value: {operand}")
            
            right = stack.top()
            stack.pop()
            left = stack.top()
            stack.pop()
            stack.push(ASTBinary(left, right, op))
    
    elif opcode in [
        Opcode.BINARY_ADD, Opcode.BINARY_AND, Opcode.BINARY_DIVIDE,
        Opcode.BINARY_FLOOR_DIVIDE, Opcode.BINARY_LSHIFT, Opcode.BINARY_MODULO,
        Opcode.BINARY_MULTIPLY, Opcode.BINARY_OR, Opcode.BINARY_POWER,
        Opcode.BINARY_RSHIFT, Opcode.BINARY_SUBTRACT, Opcode.BINARY_TRUE_DIVIDE,
        Opcode.BINARY_XOR, Opcode.BINARY_MATRIX_MULTIPLY,
        Opcode.INPLACE_ADD, Opcode.INPLACE_AND, Opcode.INPLACE_DIVIDE,
        Opcode.INPLACE_FLOOR_DIVIDE, Opcode.INPLACE_LSHIFT, Opcode.INPLACE_MODULO,
        Opcode.INPLACE_MULTIPLY, Opcode.INPLACE_OR, Opcode.INPLACE_POWER,
        Opcode.INPLACE_RSHIFT, Opcode.INPLACE_SUBTRACT, Opcode.INPLACE_TRUE_DIVIDE,
        Opcode.INPLACE_XOR, Opcode.INPLACE_MATRIX_MULTIPLY
    ]:
        # 处理二进制操作符
        from .ast_nodes import ASTBinary
        
        op = ASTBinary.from_opcode(opcode)
        if op == ASTBinary.BIN_INVALID:
            raise RuntimeError("Unhandled opcode from ASTBinary::from_opcode")
        
        right = stack.top()
        stack.pop()
        left = stack.top()
        stack.pop()
        stack.push(ASTBinary(left, right, op))
    
    elif opcode == Opcode.BINARY_SUBSCR:
        # 处理下标操作
        subscr = stack.top()
        stack.pop()
        src = stack.top()
        stack.pop()
        stack.push(ASTSubscr(src, subscr))
    
    elif opcode == Opcode.BREAK_LOOP:
        # 处理break语句
        curblock.append(ASTKeyword("break"))
    
    elif opcode == Opcode.BUILD_CLASS:
        # 处理类构建
        class_code = stack.top()
        stack.pop()
        bases = stack.top()
        stack.pop()
        name = stack.top()
        stack.pop()
        stack.push(ASTClass(class_code, bases, name))
    
    elif opcode == Opcode.BUILD_FUNCTION:
        # 处理函数构建
        fun_code = stack.top()
        stack.pop()
        stack.push(ASTFunction(fun_code, [], []))
    
    elif opcode == Opcode.BUILD_LIST_A:
        # 处理列表构建
        values = []
        for i in range(operand):
            values.insert(0, stack.top())
            stack.pop()
        stack.push(ASTList(values))
    
    elif opcode == Opcode.BUILD_SET_A:
        # 处理集合构建
        values = []
        for i in range(operand):
            values.insert(0, stack.top())
            stack.pop()
        stack.push(ASTSet(values))
    
    elif opcode == Opcode.BUILD_MAP_A:
        # 处理字典构建
        from .ast_nodes import ASTMap
        
        if mod.ver_compare(3, 5) >= 0:
            map_node = ASTMap()
            for i in range(operand):
                value = stack.top()
                stack.pop()
                key = stack.top()
                stack.pop()
                map_node.add(key, value)
            stack.push(map_node)
        else:
            if stack.top().type() == NodeType.NODE_CHAINSTORE:
                stack.pop()
            stack.push(ASTMap())
    
    elif opcode == Opcode.BUILD_CONST_KEY_MAP_A:
        # 处理常量键映射
        keys = stack.top()
        stack.pop()
        values = []
        for i in range(operand):
            value = stack.top()
            stack.pop()
            values.append(value)
        stack.push(ASTConstMap(keys, values))
    
    elif opcode == Opcode.BUILD_SLICE_A:
        # 处理切片构建
        if operand == 3:
            start = stack.top()
            stack.pop()
            stop = stack.top()
            stack.pop()
            step = stack.top()
            stack.pop()
            stack.push(ASTSlice(ASTSlice.SLICE3, start, stop, step))
        elif operand == 2:
            start = stack.top()
            stack.pop()
            stop = stack.top()
            stack.pop()
            stack.push(ASTSlice(ASTSlice.SLICE2, start, stop))
        else:
            start = stack.top()
            stack.pop()
            stack.push(ASTSlice(ASTSlice.SLICE1, start))
    
    elif opcode == Opcode.BUILD_STRING_A:
        # 处理字符串构建
        parts = []
        for i in range(operand):
            parts.insert(0, stack.top())
            stack.pop()
        # 合并为单个字符串
        result = ""
        for part in parts:
            if isinstance(part, ASTObject) and isinstance(part.object(), str):
                result += part.object()
            else:
                # 这可能是一个f-string，需要特殊处理
                return handle_fstring_build(parts)
        stack.push(ASTObject(result))
    
    elif opcode == Opcode.CALL_A:
        # 处理函数调用
        args = []
        for i in range(operand):
            args.insert(0, stack.top())
            stack.pop()
        func = stack.top()
        stack.pop()
        stack.push(ASTCall(func, args, []))
    
    elif opcode == Opcode.CALL_FUNCTION_A:
        # 处理函数调用（Python 3.6+）
        num_args = operand & 0xFF
        num_kwargs = (operand >> 8) & 0xFF
        
        args = []
        for i in range(num_args):
            args.insert(0, stack.top())
            stack.pop()
        
        keywords = []
        for i in range(num_kwargs):
            keywords.insert(0, stack.top())
            stack.pop()
        
        func = stack.top()
        stack.pop()
        stack.push(ASTCall(func, args, keywords))
    
    elif opcode == Opcode.CALL_FUNCTION_KW_A:
        # 处理带关键字参数的函数调用
        kw_name = stack.top()
        stack.pop()
        value = stack.top()
        stack.pop()
        
        # 这需要特殊处理，可能需要KW_NAMES
        stack.push(ASTCall(ASTName("function"), [], [ASTKeyword(kw_name.object(), value)]))
    
    elif opcode == Opcode.CALL_FUNCTION_EX_A:
        # 处理扩展的函数调用
        # 读取额外的操作数
        argcount = operand & 0xFFFF
        kwnames = (operand >> 16) & 0xFFFF
        
        args = []
        for i in range(argcount):
            args.insert(0, stack.top())
            stack.pop()
        
        keywords = []
        for i in range(kwnames):
            keywords.insert(0, stack.top())
            stack.pop()
        
        func = stack.top()
        stack.pop()
        stack.push(ASTCall(func, args, keywords))
    
    elif opcode == Opcode.COMPARE_OP_A:
        # 处理比较操作
        if operand < len(ASTCompare.CMP_LESS):
            right = stack.top()
            stack.pop()
            left = stack.top()
            stack.pop()
            stack.push(ASTCompare(left, right, operand))
    
    elif opcode == Opcode.DUP_TOP:
        # 复制栈顶元素
        top = stack.top()
        stack.push(top)
    
    elif opcode == Opcode.DUP_TOP_TWO:
        # 复制栈顶两个元素
        first = stack.top()
        stack.pop()
        second = stack.top()
        stack.pop()
        stack.push(second)
        stack.push(first)
        stack.push(second)
        stack.push(first)
    
    elif opcode == Opcode.DUP_TOP_THREE:
        # 复制栈顶三个元素
        first = stack.top()
        stack.pop()
        second = stack.top()
        stack.pop()
        third = stack.top()
        stack.pop()
        stack.push(third)
        stack.push(second)
        stack.push(first)
        stack.push(third)
        stack.push(second)
        stack.push(first)
    
    elif opcode == Opcode.FORMAT_VALUE_A:
        # 处理格式化值（f-string）
        conversion = (operand >> 3) & 0x7
        format_spec = operand & 0x7
        
        if format_spec == 0:
            value = stack.top()
            stack.pop()
            stack.push(ASTFormattedValue(value, conversion, None))
        elif format_spec == 1:
            # 这里应该有format_spec节点
            format_spec_node = stack.top()
            stack.pop()
            value = stack.top()
            stack.pop()
            stack.push(ASTFormattedValue(value, conversion, format_spec_node))
    
    elif opcode == Opcode.JOIN_STRINGS_A:
        # 连接字符串
        values = []
        for i in range(operand):
            values.insert(0, stack.top())
            stack.pop()
        stack.push(ASTJoinedStr(values))
    
    elif opcode == Opcode.LOAD_BUILD_CLASS:
        # 处理类构建
        class_info = stack.top()
        stack.pop()
        stack.push(ASTLoadBuildClass(class_info))
    
    elif opcode == Opcode.LOAD_CLOSURE:
        # 加载闭包变量
        name = bc_load_name(code, mod, operand)
        stack.push(ASTName(name, LoadContext()))
    
    elif opcode == Opcode.LOAD_CONST:
        # 加载常量
        const_obj = bc_load_const(code, mod, operand)
        stack.push(ASTObject(const_obj))
    
    elif opcode == Opcode.LOAD_DEREF:
        # 加载自由变量
        name = bc_load_deref(code, mod, operand)
        stack.push(ASTName(name, LoadContext()))
    
    elif opcode == Opcode.LOAD_FAST:
        # 加载局部变量
        name = bc_load_fast(code, mod, operand)
        stack.push(ASTName(name, LoadContext()))
    
    elif opcode == Opcode.LOAD_GLOBAL:
        # 加载全局变量
        name = bc_load_global(code, mod, operand)
        stack.push(ASTName(name, LoadContext()))
    
    elif opcode == Opcode.LOAD_NAME:
        # 加载名称
        name = bc_load_name(code, mod, operand)
        stack.push(ASTName(name, LoadContext()))
    
    elif opcode == Opcode.MAKE_CLOSURE_A:
        # 创建闭包
        num_defaults = operand & 0xFF
        kwdefaults = (operand >> 8) & 0xFF
        annotations = (operand >> 16) & 0xFFFF
        
        # 处理默认值
        defaults = []
        for i in range(num_defaults):
            defaults.insert(0, stack.top())
            stack.pop()
        
        # 处理关键字默认值
        kwdefault_list = []
        for i in range(kwdefaults):
            kwdefault_list.insert(0, stack.top())
            stack.pop()
        
        # 处理注释
        annotation_list = []
        for i in range(annotations):
            annotation_list.insert(0, stack.top())
            stack.pop()
        
        qualname = stack.top()
        stack.pop()
        closure_tuple = stack.top()
        stack.pop()
        code_obj = stack.top()
        stack.pop()
        
        # 创建闭包函数
        func = ASTFunction(code_obj, defaults, kwdefault_list)
        stack.push(func)
    
    elif opcode == Opcode.MATCH_CLASS_A:
        # 处理模式匹配类
        num_patterns = operand & 0xFF
        num_keys = (operand >> 8) & 0xFF
        
        patterns = []
        for i in range(num_patterns):
            patterns.insert(0, stack.top())
            stack.pop()
        
        keys = []
        for i in range(num_keys):
            keys.insert(0, stack.top())
            stack.pop()
        
        type_node = stack.top()
        stack.pop()
        
        stack.push(ASTMatchClass(type_node, keys, patterns))
    
    elif opcode == Opcode.POP_TOP:
        # 弹出栈顶元素
        stack.pop()
    
    elif opcode == Opcode.PRINT_EXPR_A:
        # 处理print表达式
        value = stack.top()
        stack.pop()
        curblock.append(ASTPrint(None, [value]))
    
    elif opcode == Opcode.RETURN_VALUE:
        # 处理返回值
        value = stack.top()
        stack.pop()
        curblock.append(ASTReturn(value))
    
    elif opcode == Opcode.ROT_TWO:
        # 交换栈顶两个元素
        first = stack.top()
        stack.pop()
        second = stack.top()
        stack.pop()
        stack.push(first)
        stack.push(second)
    
    elif opcode == Opcode.ROT_THREE:
        # 旋转栈顶三个元素
        first = stack.top()
        stack.pop()
        second = stack.top()
        stack.pop()
        third = stack.top()
        stack.pop()
        stack.push(first)
        stack.push(second)
        stack.push(third)
    
    elif opcode == Opcode.ROT_FOUR:
        # 旋转栈顶四个元素
        first = stack.top()
        stack.pop()
        second = stack.top()
        stack.pop()
        third = stack.top()
        stack.pop()
        fourth = stack.top()
        stack.pop()
        stack.push(first)
        stack.push(second)
        stack.push(third)
        stack.push(fourth)
    
    elif opcode == Opcode.STORE_ATTR:
        # 存储属性
        attr = stack.top()
        stack.pop()
        obj = stack.top()
        stack.pop()
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTSubscr(obj, ASTName(attr.object(), StoreContext())), value))
    
    elif opcode == Opcode.STORE_DEREF:
        # 存储自由变量
        name = bc_load_name(code, mod, operand)
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTName(name, StoreContext()), value))
    
    elif opcode == Opcode.STORE_FAST:
        # 存储局部变量
        name = bc_load_fast(code, mod, operand)
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTName(name, StoreContext()), value))
    
    elif opcode == Opcode.STORE_GLOBAL:
        # 存储全局变量
        name = bc_load_global(code, mod, operand)
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTName(name, StoreContext()), value))
    
    elif opcode == Opcode.STORE_NAME:
        # 存储名称
        name = bc_load_name(code, mod, operand)
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTName(name, StoreContext()), value))
    
    elif opcode == Opcode.STORE_SUBSCR:
        # 存储下标
        index = stack.top()
        stack.pop()
        obj = stack.top()
        stack.pop()
        value = stack.top()
        stack.pop()
        curblock.append(ASTStore(ASTSubscr(obj, index), value))
    
    elif opcode == Opcode.UNPACK_EX:
        # 解包操作
        unpack = operand
        values = []
        for i in range(unpack):
            values.insert(0, stack.top())
            stack.pop()
        
        if unpack > 0:
            stack.push(ASTTuple(values))
    
    elif opcode == Opcode.UNPACK_SEQUENCE_A:
        # 解包序列
        unpack = operand
        values = []
        for i in range(unpack):
            values.insert(0, stack.top())
            stack.pop()
        
        if unpack > 0:
            stack.push(ASTTuple(values))
    
    elif opcode == Opcode.UNPACK_WITH_ARGUMENT_A:
        # 带参数的解包
        unpack = operand & 0xFF
        star_count = (operand >> 8) & 0xFF
        
        values = []
        for i in range(unpack):
            values.insert(0, stack.top())
            stack.pop()
        
        if unpack > 0:
            stack.push(ASTTuple(values))
    
    else:
        # 未知或未实现的操作码
        # 这里应该记录未实现的操作码，但不影响执行
        pass
    
    return None


def bc_next(source: Any, mod: Any, pos: int) -> Tuple[int, int, int]:
    """
    读取下一条字节码指令
    类似于C++版本的bc_next函数
    """
    if source.at_eof():
        return 0, 0, pos
    
    opcode = source.read_byte()
    operand = 0
    pos += 1
    
    # 检查是否有操作数
    if source.at_eof():
        return opcode, operand, pos
    
    if opcode >= 90:  # PYC_HAVE_ARG
        operand = source.read_uint16()
        pos += 2
    
    return opcode, operand, pos


def bc_load_name(code: Any, mod: Any, idx: int) -> str:
    """加载名称"""
    if idx < len(code.names()):
        return code.names()[idx].value()
    return f"<unknown_{idx}>"


def bc_load_global(code: Any, mod: Any, idx: int) -> str:
    """加载全局变量"""
    if idx < len(code.globals()):
        return code.globals()[idx].value()
    return f"<global_{idx}>"


def bc_load_const(code: Any, mod: Any, idx: int) -> Any:
    """加载常量"""
    if idx < len(code.consts()):
        return code.consts()[idx]
    return None


def bc_load_fast(code: Any, mod: Any, idx: int) -> str:
    """加载局部变量"""
    if idx < len(code.varnames()):
        return code.varnames()[idx].value()
    return f"<fast_{idx}>"


def bc_load_deref(code: Any, mod: Any, idx: int) -> str:
    """加载自由变量"""
    if idx < len(code.freevars()):
        return code.freevars()[idx].value()
    if idx < len(code.cellvars()):
        return code.cellvars()[idx].value()
    return f"<deref_{idx}>"


def handle_fstring_build(parts: List[ASTNode]) -> ASTNode:
    """
    处理f-string构建
    这是一个复杂的功能，需要将字符串片段和表达式组合成f-string
    """
    # 简化实现 - 实际上这需要更复杂的解析逻辑
    if len(parts) == 1 and isinstance(parts[0], ASTObject):
        return parts[0]
    
    # 创建ASTJoinedStr节点
    return ASTJoinedStr(parts)


def print_src(node: ASTNode, mod: Any, output: Any) -> None:
    """
    打印源代码
    参考C++版本：ASTree.cpp::print_src相关函数
    将AST节点转换为可读的Python源代码
    """
    from .ast_nodes import default_generator
    
    try:
        # 生成代码
        if hasattr(node, 'to_code'):
            source_code = node.to_code()
        else:
            source_code = "# 未实现的AST节点"
        
        # 写入输出
        output.write(source_code)
        
    except Exception as e:
        # 错误处理
        output.write(f"# 源代码生成错误: {e}\n")


def decompyle(code: PycRef, mod: Any, output: Any) -> None:
    """
    反编译函数
    参考C++版本：pycdc.cpp::main中的decompyle调用
    主要的反编译入口函数
    """
    global _clean_build
    
    try:
        # 构建AST
        ast_node = build_from_code(code, mod)
        
        # 打印源代码
        print_src(ast_node, mod, output)
        
    except Exception as e:
        # 错误处理
        print(f"Error during decompilation: {e}", file=sys.stderr)
        _clean_build = False


# 上下文类定义
class LoadContext:
    """加载上下文"""
    def __repr__(self):
        return "LoadContext"


class StoreContext:
    """存储上下文"""
    def __repr__(self):
        return "StoreContext"


# 辅助类
class ASTBlock(ASTNode):
    """AST块节点"""
    def __init__(self, blktype: int, end: int = 0, is_except: bool = False):
        super().__init__(NodeType.NODE_BLOCK)
        self.blktype = blktype
        self.end = end
        self.is_except = is_except
        self.nodes = []
    
    def blktype(self) -> int:
        return self.blktype
    
    def end(self) -> int:
        return self.end
    
    def nodes(self) -> List[ASTNode]:
        return self.nodes
    
    def append(self, node: ASTNode) -> None:
        self.nodes.append(node)


# 补充缺失的AST节点类
class ASTMatchClass(ASTNode):
    """模式匹配类节点"""
    def __init__(self, type_node: ASTNode, keys: List[ASTNode], patterns: List[ASTNode]):
        super().__init__(NodeType.NODE_MATCH_CLASS)
        self.type_node = type_node
        self.keys = keys
        self.patterns = patterns


class ASTLoadBuildClass(ASTNode):
    """加载构建类节点"""
    def __init__(self, class_info: Any):
        super().__init__(NodeType.NODE_LOAD_BUILD_CLASS)
        self.class_info = class_info