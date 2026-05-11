"""
操作码特征检测器 - 替代所有硬编码操作码名称

提供统一的操作码特征检测接口，避免在代码中直接使用硬编码的操作码名称字符串。
支持 Python 3.8-3.11 所有操作码。

使用方式：
    旧: if opname == 'POP_JUMP_IF_FALSE'
    新: if detector.is_conditional_jump(instr)

理论依据：
    - 编译器设计：操作码分类是编译器优化的基础（参考 Dragon Book Ch.8）
    - 字节码分析：基于 Python 官方 dis 模块的操作码定义
    - 版本兼容：覆盖 Python 3.8-3.11 的所有操作码变体

设计原则：
    - 单一职责：每个检测方法只负责一种特征判断
    - 开闭原则：新增操作码只需扩展集合，无需修改检测逻辑
    - 依赖倒置：高层模块依赖抽象接口，不依赖具体操作码名称
"""

import dis
import sys
import os
from typing import Optional, Set, Any, Union
from enum import Enum


class OpcodeCategory(Enum):
    """操作码类别枚举"""
    CONDITIONAL_JUMP = "conditional_jump"
    UNCONDITIONAL_JUMP = "unconditional_jump"
    LOOP_HEADER = "loop_header"
    SHORT_CIRCUIT_JUMP = "short_circuit_jump"
    EXCEPTION_RELATED = "exception_related"
    SETUP_INSTRUCTION = "setup_instruction"
    OTHER = "other"


class OpcodeFeatureDetector:
    """
    操作码特征检测器 - 替代所有硬编码操作码名称

    提供语义化的操作码特征检测方法，替代直接的字符串比较。

    Attributes:
        python_version: 当前检测器适配的 Python 版本元组
        CONDITIONAL_JUMP_OPCODES: 条件跳转操作码集合
        UNCONDITIONAL_JUMP_OPCODES: 无条件跳转操作码集合
        LOOP_HEADER_OPCODES: 循环头指令集合
        SHORT_CIRCUIT_JUMP_OPCODES: 短路求值跳转集合
        EXCEPTION_OPCODES: 异常相关指令集合
        SETUP_OPCODES: SETUP指令集合

    Example:
        >>> detector = OpcodeFeatureDetector()
        >>> instr = type('Instruction', (), {'opcode': 114, 'opname': 'POP_JUMP_FORWARD_IF_FALSE'})()
        >>> detector.is_conditional_jump(instr)
        True
        >>> detector.get_opcode_category(instr)
        <OpcodeCategory.CONDITIONAL_JUMP: 'conditional_jump'>
    """

    def __init__(self, python_version: tuple = None):
        """初始化，根据Python版本加载操作码集合

        Args:
            python_version: 指定Python版本元组，如 (3, 11)。
                          为None时自动检测当前运行版本，
                          也可通过环境变量 PYTHON_VERSION_OVERRIDE 覆盖。
        """
        env_version = os.environ.get('PYTHON_VERSION_OVERRIDE')
        if env_version:
            try:
                parts = env_version.split('.')
                self.python_version = (int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                self.python_version = python_version or sys.version_info[:2]
        else:
            self.python_version = python_version or sys.version_info[:2]

        self._init_opcode_sets()

    def _get_opcode(self, name: str) -> Optional[int]:
        """获取操作码数值，兼容不同Python版本

        Args:
            name: 操作码名称

        Returns:
            操作码数值，如果不存在返回None
        """
        # 优先从 dis 模块属性获取（Python 3.11+ 部分操作码）
        if hasattr(dis, name):
            return getattr(dis, name)

        # 从 opmap 字典获取（Python 3.11 的完整操作码映射）
        if hasattr(dis, 'opmap') and isinstance(dis.opmap, dict):
            return dis.opmap.get(name)

        return None

    def _init_opcode_sets(self):
        """初始化所有操作码集合，支持多版本兼容"""
        major, minor = self.python_version

        # 1. 条件跳转操作码集合
        # 理论依据：条件跳转是控制流分支的基础（Dragon Book Ch.9）
        self.CONDITIONAL_JUMP_OPCODES: Set[int] = {
            self._get_opcode('POP_JUMP_IF_FALSE'),
            self._get_opcode('POP_JUMP_IF_TRUE'),
            self._get_opcode('JUMP_IF_FALSE_OR_POP'),
            self._get_opcode('JUMP_IF_TRUE_OR_POP'),
            self._get_opcode('JUMP_BACKWARD'),
            # Python 3.11+ 新增的变体
            self._get_opcode('POP_JUMP_FORWARD_IF_FALSE'),
            self._get_opcode('POP_JUMP_FORWARD_IF_TRUE'),
            self._get_opcode('POP_JUMP_BACKWARD_IF_FALSE'),
            self._get_opcode('POP_JUMP_BACKWARD_IF_TRUE'),
            self._get_opcode('POP_JUMP_FORWARD_IF_NONE'),
            self._get_opcode('POP_JUMP_FORWARD_IF_NOT_NONE'),
            self._get_opcode('POP_JUMP_BACKWARD_IF_NONE'),
            self._get_opcode('POP_JUMP_BACKWARD_IF_NOT_NONE'),
        } - {None}

        # 2. 无条件跳转操作码集合
        # 包含所有绝对/相对跳转指令
        self.UNCONDITIONAL_JUMP_OPCODES: Set[int] = {
            self._get_opcode('JUMP_FORWARD'),
            self._get_opcode('JUMP_ABSOLUTE'),
            self._get_opcode('JUMP_BACKWARD'),
            self._get_opcode('JUMP_BACKWARD_NO_INTERRUPT'),
            self._get_opcode('CONTINUE_LOOP'),  # Python 3.8-3.10
            self._get_opcode('JUMP_NOT_EXC_MATCH'),  # Python 3.11+
        } - {None}

        # 3. 循环头指令集合
        # 理论依据：循环迭代器的入口点（编译原理：循环优化）
        self.LOOP_HEADER_OPCODES: Set[int] = {
            self._get_opcode('FOR_ITER'),
            self._get_opcode('GET_ANEXT'),  # 异步迭代
            self._get_opcode('GET_ITER'),
            self._get_opcode('GET_AITER'),  # 异步迭代器获取
        } - {None}

        # 4. 短路求值跳转集合
        # 用于 and/or 表达式的短路求值优化
        self.SHORT_CIRCUIT_JUMP_OPCODES: Set[int] = {
            self._get_opcode('JUMP_IF_FALSE_OR_POP'),
            self._get_opcode('JUMP_IF_TRUE_OR_POP'),
            self._get_opcode('JUMP_BACKWARD'),  # 当用于短路时
        } - {None}

        # 5. 异常相关指令集合
        # 理论依据：异常处理机制（Dragon Book Ch.7）
        self.EXCEPTION_OPCODES: Set[int] = {
            self._get_opcode('PUSH_EXC_INFO'),
            self._get_opcode('CHECK_EXC_MATCH'),
            self._get_opcode('CHECK_EG_MATCH'),
            self._get_opcode('RERAISE'),
            self._get_opcode('WITH_EXCEPT_START'),
            self._get_opcode('BEFORE_WITH'),
            self._get_opcode('BEFORE_ASYNC_WITH'),
            self._get_opcode('SETUP_FINALLY'),
            self._get_opcode('SETUP_EXCEPT'),
            self._get_opcode('SETUP_WITH'),
            self._get_opcode('SETUP_ASYNC_WITH'),
            self._get_opcode('POP_EXCEPT'),
            self._get_opcode('END_ASYNC_FOR'),
        } - {None}

        # 6. SETUP指令集合（旧版异常处理）
        # Python 3.8-3.10 使用基于栈的异常处理
        self.SETUP_OPCODES: Set[int] = {
            self._get_opcode('SETUP_FINALLY'),
            self._get_opcode('SETUP_EXCEPT'),
            self._get_opcode('SETUP_WITH'),
            self._get_opcode('SETUP_ASYNC_WITH'),
            self._get_opcode('SETUP_LOOP'),  # Python 3.7及更早
        } - {None}

    def is_conditional_jump(self, instr: Any) -> bool:
        """检测是否是条件跳转（不关心具体名称）

        Args:
            instr: 指令对象，需包含 opcode 属性

        Returns:
            bool: 如果是条件跳转返回True

        Example:
            >>> detector.is_conditional_jump(instr_with_pop_jump_if_false)
            True
        """
        return getattr(instr, 'opcode', None) in self.CONDITIONAL_JUMP_OPCODES

    def is_unconditional_jump(self, instr: Any) -> bool:
        """检测是否是无条件跳转

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是无条件跳转返回True
        """
        return getattr(instr, 'opcode', None) in self.UNCONDITIONAL_JUMP_OPCODES

    def is_loop_header_opcode(self, instr: Any) -> bool:
        """检测是否是循环头指令（FOR_ITER/GET_ANEXT）

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是循环头指令返回True
        """
        return getattr(instr, 'opcode', None) in self.LOOP_HEADER_OPCODES

    def is_for_iter(self, instr: Any) -> bool:
        """检测是否是FOR_ITER指令（for循环迭代器）

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是FOR_ITER返回True
        """
        return getattr(instr, 'opname', None) == 'FOR_ITER'

    def is_get_anext(self, instr: Any) -> bool:
        """检测是否是GET_ANEXT指令（异步for循环）

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是GET_ANEXT返回True
        """
        return getattr(instr, 'opname', None) == 'GET_ANEXT'

    def is_iterator_setup_opcode(self, instr: Any) -> bool:
        """检测是否是迭代器设置指令（GET_ITER/GET_AITER等）

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是迭代器设置指令返回True
        """
        opname = getattr(instr, 'opname', None)
        return opname in ('GET_ITER', 'GET_AITER')

    def is_send(self, instr: Any) -> bool:
        """检测是否是SEND指令（生成器send）

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是SEND返回True
        """
        return getattr(instr, 'opname', None) == 'SEND'

    def is_yield_value(self, instr: Any) -> bool:
        """检测是否是YIELD_VALUE指令

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是YIELD_VALUE返回True
        """
        return getattr(instr, 'opname', None) == 'YIELD_VALUE'

    def is_jump_backward_no_interrupt(self, instr: Any) -> bool:
        """检测是否是JUMP_BACKWARD_NO_INTERRUPT指令

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是JUMP_BACKWARD_NO_INTERRUPT返回True
        """
        return getattr(instr, 'opname', None) == 'JUMP_BACKWARD_NO_INTERRUPT'

    def is_get_yield_from_iter(self, instr: Any) -> bool:
        """检测是否是GET_YIELD_FROM_ITER指令

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是GET_YIELD_FROM_ITER返回True
        """
        return getattr(instr, 'opname', None) == 'GET_YIELD_FROM_ITER'

    def is_short_circuit_jump(self, instr: Any) -> bool:
        """检测是否是短路求值跳转（JUMP_IF_FALSE_OR_POP等）

        用于 and/or 布尔表达式的短路求值优化。

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是短路跳转返回True
        """
        return getattr(instr, 'opcode', None) in self.SHORT_CIRCUIT_JUMP_OPCODES

    def is_exception_related(self, instr: Any) -> bool:
        """检测是否是异常相关指令

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是异常相关指令返回True
        """
        return getattr(instr, 'opcode', None) in self.EXCEPTION_OPCODES

    def is_setup_instruction(self, instr: Any) -> bool:
        """检测是否是SETUP_*指令（旧版异常处理）

        Python 3.11+ 已移除大部分SETUP指令，改用异常表。

        Args:
            instr: 指令对象

        Returns:
            bool: 如果是SETUP指令返回True
        """
        return getattr(instr, 'opcode', None) in self.SETUP_OPCODES

    def get_opcode_category(self, instr: Any) -> OpcodeCategory:
        """返回操作码类别字符串

        按优先级顺序检测：条件跳转 > 无条件跳转 > 循环头 > 短路 > 异常 > SETUP > 其他

        Args:
            instr: 指令对象

        Returns:
            OpcodeCategory: 操作码类别枚举值
        """
        if self.is_conditional_jump(instr):
            return OpcodeCategory.CONDITIONAL_JUMP
        elif self.is_unconditional_jump(instr):
            return OpcodeCategory.UNCONDITIONAL_JUMP
        elif self.is_loop_header_opcode(instr):
            return OpcodeCategory.LOOP_HEADER
        elif self.is_short_circuit_jump(instr):
            return OpcodeCategory.SHORT_CIRCUIT_JUMP
        elif self.is_exception_related(instr):
            return OpcodeCategory.EXCEPTION_RELATED
        elif self.is_setup_instruction(instr):
            return OpcodeCategory.SETUP_INSTRUCTION
        else:
            return OpcodeCategory.OTHER

    def is_python311_plus(self) -> bool:
        """检测当前是否为Python 3.11+

        Python 3.11 引入了重要的字节码变更：
        - 移除SETUP_*指令
        - 新增异常表机制
        - 操作码编号重新分配

        Returns:
            bool: 如果版本 >= 3.11 返回True
        """
        return self.python_version >= (3, 11)

    def get_opcode_name(self, opcode: int) -> str:
        """获取操作码的可读名称

        Args:
            opcode: 操作码数值

        Returns:
            str: 操作码名称，未知则返回 'UNKNOWN'
        """
        try:
            if isinstance(dis.opname, list):
                if 0 <= opcode < len(dis.opname):
                    return dis.opname[opcode]
            elif isinstance(dis.opname, dict):
                return dis.opname.get(opcode, f'UNKNOWN({opcode})')
        except (IndexError, TypeError):
            pass
        return f'UNKNOWN({opcode})'

    def get_all_opcodes_in_category(self, category: OpcodeCategory) -> Set[int]:
        """获取指定类别的所有操作码

        Args:
            category: 操作码类别

        Returns:
            Set[int]: 该类别包含的所有操作码集合
        """
        category_map = {
            OpcodeCategory.CONDITIONAL_JUMP: self.CONDITIONAL_JUMP_OPCODES,
            OpcodeCategory.UNCONDITIONAL_JUMP: self.UNCONDITIONAL_JUMP_OPCODES,
            OpcodeCategory.LOOP_HEADER: self.LOOP_HEADER_OPCODES,
            OpcodeCategory.SHORT_CIRCUIT_JUMP: self.SHORT_CIRCUIT_JUMP_OPCODES,
            OpcodeCategory.EXCEPTION_RELATED: self.EXCEPTION_OPCODES,
            OpcodeCategory.SETUP_INSTRUCTION: self.SETUP_OPCODES,
        }
        return category_map.get(category, set())

    def _get_opname(self, instr: Any) -> Optional[str]:
        """获取指令的opname属性"""
        return getattr(instr, 'opname', None)

    def _is_opname(self, instr: Any, name: str) -> bool:
        """检查指令opname是否匹配指定名称"""
        return self._get_opname(instr) == name

    def _is_opname_in(self, instr: Any, names: tuple) -> bool:
        """检查指令opname是否在指定名称集合中"""
        return self._get_opname(instr) in names

    def _opname_startswith(self, instr: Any, prefix: str) -> bool:
        """检查指令opname是否以指定前缀开头"""
        opname = self._get_opname(instr)
        return isinstance(opname, str) and opname.startswith(prefix)

    def is_store_instruction(self, instr: Any) -> bool:
        """检测是否是任何存储指令（STORE_*）"""
        return self._opname_startswith(instr, 'STORE_')

    def is_store_fast(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_FAST')

    def is_store_name(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_NAME')

    def is_store_global(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_GLOBAL')

    def is_store_deref(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_DEREF')

    def is_store_subscr(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_SUBSCR')

    def is_store_attr(self, instr: Any) -> bool:
        return self._is_opname(instr, 'STORE_ATTR')

    def is_any_store(self, instr: Any) -> bool:
        """检测是否是任何存储操作（STORE_FAST/NAME/GLOBAL/DEREF/SUBSCR/ATTR）"""
        return self._is_opname_in(instr, ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                          'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR'))

    def is_load_instruction(self, instr: Any) -> bool:
        """检测是否是任何加载指令（LOAD_*）"""
        return self._opname_startswith(instr, 'LOAD_')

    def is_load_const(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_CONST')

    def is_load_fast(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_FAST')

    def is_load_name(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_NAME')

    def is_load_global(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_GLOBAL')

    def is_load_deref(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_DEREF')

    def is_load_attr(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_ATTR')

    def is_load_method(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_METHOD')

    def is_load_assertion_error(self, instr: Any) -> bool:
        return self._is_opname(instr, 'LOAD_ASSERTION_ERROR')

    def is_any_load(self, instr: Any) -> bool:
        """检测是否是通用加载操作（用于表达式重建等场景）"""
        return self._is_opname_in(instr, ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',
                                          'LOAD_GLOBAL', 'LOAD_DEREF', 'LOAD_ATTR',
                                          'LOAD_METHOD'))

    def is_return_instruction(self, instr: Any) -> bool:
        """检测是否是任何返回指令"""
        return self._is_opname_in(instr, ('RETURN_VALUE', 'RETURN_CONST', 'RETURN_GENERATOR'))

    def is_return_value(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RETURN_VALUE')

    def is_return_const(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RETURN_CONST')

    def is_return_generator(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RETURN_GENERATOR')

    def is_jump_forward(self, instr: Any) -> bool:
        return self._is_opname(instr, 'JUMP_FORWARD')

    def is_jump_backward(self, instr: Any) -> bool:
        return self._is_opname(instr, 'JUMP_BACKWARD')

    def is_jump_absolute(self, instr: Any) -> bool:
        return self._is_opname(instr, 'JUMP_ABSOLUTE')

    def is_build_list(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BUILD_LIST')

    def is_build_tuple(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BUILD_TUPLE')

    def is_build_set(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BUILD_SET')

    def is_build_map(self, instr: Any) -> bool:
        return self._is_opname_in(instr, ('BUILD_MAP', 'BUILD_CONST_KEY_MAP'))

    def is_build_string(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BUILD_STRING')

    def is_any_build(self, instr: Any) -> bool:
        """检测是否是任何构建容器指令"""
        return self._is_opname_in(instr, ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET',
                                          'BUILD_MAP', 'BUILD_CONST_KEY_MAP', 'BUILD_STRING'))

    def is_pop_top(self, instr: Any) -> bool:
        return self._is_opname(instr, 'POP_TOP')

    def is_nop(self, instr: Any) -> bool:
        return self._is_opname(instr, 'NOP')

    def is_resume(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RESUME')

    def is_cache(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CACHE')

    def is_copy(self, instr: Any) -> bool:
        return self._is_opname(instr, 'COPY')

    def is_swap(self, instr: Any) -> bool:
        return self._is_opname(instr, 'SWAP')

    def is_compare_op(self, instr: Any) -> bool:
        return self._is_opname(instr, 'COMPARE_OP')

    def is_is_op(self, instr: Any) -> bool:
        return self._is_opname(instr, 'IS_OP')

    def is_contains_op(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CONTAINS_OP')

    def is_any_compare(self, instr: Any) -> bool:
        """检测是否是比较操作（COMPARE_OP/IS_OP/CONTAINS_OP）"""
        return self._is_opname_in(instr, ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'))

    def is_call(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CALL')

    def is_call_function(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CALL_FUNCTION')

    def is_call_method(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CALL_METHOD')

    def is_precall(self, instr: Any) -> bool:
        return self._is_opname(instr, 'PRECALL')

    def is_any_call(self, instr: Any) -> bool:
        """检测是否是函数调用相关指令"""
        return self._is_opname_in(instr, ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'PRECALL'))

    def is_pop_except(self, instr: Any) -> bool:
        return self._is_opname(instr, 'POP_EXCEPT')

    def is_push_exc_info(self, instr: Any) -> bool:
        return self._is_opname(instr, 'PUSH_EXC_INFO')

    def is_reraise(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RERAISE')

    def is_raise_varargs(self, instr: Any) -> bool:
        return self._is_opname(instr, 'RAISE_VARARGS')

    def is_end_async_for(self, instr: Any) -> bool:
        return self._is_opname(instr, 'END_ASYNC_FOR')

    def is_check_exc_match(self, instr: Any) -> bool:
        return self._is_opname(instr, 'CHECK_EXC_MATCH')

    def is_with_except_start(self, instr: Any) -> bool:
        return self._is_opname(instr, 'WITH_EXCEPT_START')

    def is_exception_handling(self, instr: Any) -> bool:
        """检测是否是异常处理相关指令（广泛匹配）"""
        return self._is_opname_in(instr, ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                          'RERAISE', 'WITH_EXCEPT_START', 'BEFORE_WITH',
                                          'BEFORE_ASYNC_WITH', 'POP_EXCEPT', 'END_ASYNC_FOR',
                                          'RAISE_VARARGS'))

    def is_import_name(self, instr: Any) -> bool:
        return self._is_opname(instr, 'IMPORT_NAME')

    def is_import_from(self, instr: Any) -> bool:
        return self._is_opname(instr, 'IMPORT_FROM')

    def is_make_function(self, instr: Any) -> bool:
        return self._is_opname(instr, 'MAKE_FUNCTION')

    def is_unpack_sequence(self, instr: Any) -> bool:
        return self._is_opname(instr, 'UNPACK_SEQUENCE')

    def is_unpack_ex(self, instr: Any) -> bool:
        return self._is_opname(instr, 'UNPACK_EX')

    def is_delete_subscr(self, instr: Any) -> bool:
        return self._is_opname(instr, 'DELETE_SUBSCR')

    def is_delete_attr(self, instr: Any) -> bool:
        return self._is_opname(instr, 'DELETE_ATTR')

    def is_delete_name(self, instr: Any) -> bool:
        return self._is_opname(instr, 'DELETE_NAME')

    def is_delete_global(self, instr: Any) -> bool:
        return self._is_opname(instr, 'DELETE_GLOBAL')

    def is_get_iter(self, instr: Any) -> bool:
        return self._is_opname(instr, 'GET_ITER')

    def is_get_aiter(self, instr: Any) -> bool:
        return self._is_opname(instr, 'GET_AITER')

    def is_before_with(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BEFORE_WITH')

    def is_before_async_with(self, instr: Any) -> bool:
        return self._is_opname(instr, 'BEFORE_ASYNC_WITH')

    def is_push_null(self, instr: Any) -> bool:
        return self._is_opname(instr, 'PUSH_NULL')

    def is_noise_instruction(self, instr: Any) -> bool:
        """检测是否是噪声指令（不影响语义的填充指令）"""
        return self._is_opname_in(instr, ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'))

    def is_debug_or_noise(self, instr: Any) -> bool:
        """检测是否是调试或噪声指令（更广泛的噪声定义）"""
        return self._is_opname_in(instr, ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))

    def has_for_iter_in_opname(self, instr: Any) -> bool:
        """检测opname中是否包含FOR_ITER（如FOR_ITER_RANGE）"""
        opname = self._get_opname(instr)
        return isinstance(opname, str) and 'FOR_ITER' in opname

    def is_loop_back_jump(self, instr: Any) -> bool:
        """检测是否是循环回跳指令（JUMP_BACKWARD/JUMP_BACKWARD_NO_INTERRUPT）"""
        return self._is_opname_in(instr, ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'))

    def is_forward_jump(self, instr: Any) -> bool:
        """检测是否是前向跳转（JUMP_FORWARD + 前向条件跳转）"""
        return self._is_opname_in(instr, ('JUMP_FORWARD', 'POP_JUMP_FORWARD_IF_FALSE',
                                          'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_NONE',
                                          'POP_JUMP_FORWARD_IF_NOT_NONE'))

    def is_backward_jump(self, instr: Any) -> bool:
        """检测是否是后向跳转（JUMP_BACKWARD系列）"""
        opname = self._get_opname(instr)
        if not isinstance(opname, str):
            return False
        return 'BACKWARD' in opname or opname == 'CONTINUE_LOOP'

    def is_terminator(self, instr: Any) -> bool:
        """检测是否是基本块终止符（返回/ raise/无条件跳转）"""
        return self.is_return_instruction(instr) or \
               self._is_opname_in(instr, ('RAISE_VARARGS', 'RERAISE')) or \
               self.is_unconditional_jump(instr)

    def __repr__(self) -> str:
        return (f"OpcodeFeatureDetector(python_version={self.python_version}, "
                f"categories={len([c for c in OpcodeCategory if c != OpcodeCategory.OTHER])})")


# 创建全局单例实例供模块级别使用
_global_detector_instance: Optional[OpcodeFeatureDetector] = None


def get_opcode_detector(python_version: tuple = None) -> OpcodeFeatureDetector:
    """获取全局操作码检测器单例

    Args:
        python_version: 可选的Python版本覆盖

    Returns:
        OpcodeFeatureDetector: 全局单例实例

    Example:
        >>> detector = get_opcode_detector()
        >>> detector.is_conditional_jump(some_instruction)
    """
    global _global_detector_instance
    if _global_detector_instance is None or python_version is not None:
        _global_detector_instance = OpcodeFeatureDetector(python_version)
    return _global_detector_instance


def create_opcode_detector(python_version: tuple = None) -> OpcodeFeatureDetector:
    """创建新的操作码检测器实例（用于测试或多版本场景）

    Args:
        python_version: 目标Python版本

    Returns:
        OpcodeFeatureDetector: 新创建的检测器实例
    """
    return OpcodeFeatureDetector(python_version)
