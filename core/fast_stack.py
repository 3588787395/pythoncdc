"""
FastStack模块
快速堆栈实现，类似于C++版本的FastStack
用于高效地管理字节码解析过程中的堆栈操作
"""

from typing import Any, Optional, List
from collections import deque
import copy


class FastStack:
    """
    快速堆栈类
    提供高效的堆栈操作，支持预分配内存以提高性能
    基于C++版本的FastStack.h实现
    """
    
    def __init__(self, initial_size: int = 20):
        """
        初始化FastStack
        
        Args:
            initial_size: 初始堆栈大小（预分配）
        """
        # 预分配内存，类似于C++版本的m_stack.resize(size)
        self._stack: List[Any] = [None] * initial_size
        self._ptr: int = -1  # 栈指针，类似于C++版本的m_ptr
        self._initial_size: int = initial_size
        self._debug: bool = False  # 调试模式开关
        
    def _debug_print(self, message: str) -> None:
        """调试信息输出"""
        if self._debug:
            print(f"[FastStack Debug] {message}")
        
    def push(self, item: Any) -> None:
        """
        将元素推入堆栈
        
        Args:
            item: 要推入的元素
        """
        # 检查是否需要扩容
        if self._ptr + 1 >= len(self._stack):
            # 扩容，类似于C++版本的m_stack.emplace_back(nullptr)
            self._stack.append(None)
            self._debug_print(f"Stack resized to {len(self._stack)}")
        
        # 推入元素并移动指针
        self._ptr += 1
        self._stack[self._ptr] = item
        self._debug_print(f"Pushed item, ptr={self._ptr}")
        
    def pop(self) -> Any:
        """
        从堆栈中弹出元素
        
        Returns:
            栈顶元素
            
        Raises:
            IndexError: 如果堆栈为空
        """
        if self._ptr <= -1:
            error_msg = "pop from empty stack"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        # 弹出元素并清空位置
        item = self._stack[self._ptr]
        self._stack[self._ptr] = None  # 类似于C++版本的m_stack[m_ptr--] = nullptr
        self._ptr -= 1
        self._debug_print(f"Popped item, ptr={self._ptr}")
        return item
        
    def top(self, i: int = 1) -> Any:
        """
        查看栈顶元素（支持批量访问）
        
        Args:
            i: 从栈顶开始的位置（1=栈顶，2=次栈顶，...）
            
        Returns:
            第i个栈顶元素
            
        Raises:
            IndexError: 如果访问位置无效
        """
        if i > 0:
            idx = self._ptr + 1 - i
            if self._ptr > -1 and idx >= 0:
                return self._stack[idx]
            else:
                error_msg = f"insufficient values on stack (ptr={self._ptr}, requested={i})"
                self._debug_print(error_msg)
                raise IndexError(error_msg)
        else:
            error_msg = f"incorrect operand {i}"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
    
    def peek(self) -> Any:
        """
        查看栈顶元素（等效于top(1)）
        
        Returns:
            栈顶元素
            
        Raises:
            IndexError: 如果堆栈为空
        """
        return self.top(1)
        
    def empty(self) -> bool:
        """
        检查堆栈是否为空（基于C++版本的实现）
        
        Returns:
            如果堆栈为空返回True，否则返回False
        """
        # 类似于C++版本的return m_ptr == -1;
        return self._ptr == -1
        
    def size(self) -> int:
        """
        获取堆栈大小
        
        Returns:
            堆栈中的元素数量
        """
        return self._ptr + 1 if self._ptr >= 0 else 0
        
    def clear(self) -> None:
        """
        清空堆栈并重置指针
        """
        # 重置栈指针和清空内容
        self._ptr = -1
        # 清空已使用的部分
        for i in range(len(self._stack)):
            self._stack[i] = None
        self._debug_print("Stack cleared")
        
    def copy(self) -> 'FastStack':
        """
        复制堆栈（优化版本，避免深拷贝）
        
        Returns:
            堆栈的浅拷贝（高效复制）
        """
        # 类似于C++版本的拷贝构造函数
        new_stack = FastStack.__new__(FastStack)
        new_stack._stack = self._stack.copy()  # 浅拷贝
        new_stack._ptr = self._ptr
        new_stack._initial_size = self._initial_size
        new_stack._debug = False  # 新堆栈默认关闭调试
        return new_stack
        
    def get_ptr(self) -> int:
        """
        获取当前栈指针位置（用于调试）
        
        Returns:
            当前栈指针位置
        """
        return self._ptr
        
    def set_debug(self, debug: bool = True) -> None:
        """
        设置调试模式
        
        Args:
            debug: 是否启用调试模式
        """
        self._debug = debug
        
    def slice(self, start: int, end: int) -> List[Any]:
        """
        获取堆栈片段
        
        Args:
            start: 开始位置（从0开始）
            end: 结束位置（不包含）
            
        Returns:
            堆栈片段的列表
        """
        if start < 0 or end > self.size() or start >= end:
            return []
        return self._stack[start:end]
        
    def to_list(self) -> List[Any]:
        """
        将堆栈转换为列表（仅包含有效元素）
        
        Returns:
            包含所有有效元素的列表
        """
        return self._stack[:self._ptr + 1] if self._ptr >= 0 else []
        
    def __len__(self) -> int:
        """返回堆栈大小（有效元素数量）"""
        return self.size()
        
    def __str__(self) -> str:
        """返回堆栈的字符串表示"""
        return f"FastStack(ptr={self._ptr}, size={self.size()})"
        
    def __repr__(self) -> str:
        """返回堆栈的详细字符串表示"""
        return f"FastStack(ptr={self._ptr}, size={self.size()}, initial_size={self._initial_size})"
        
    def batch_push(self, items: List[Any]) -> None:
        """
        批量推入元素（高性能）
        
        Args:
            items: 要推入的元素列表
        """
        if not items:
            return
            
        # 检查是否有足够空间
        needed_space = len(items)
        current_capacity = len(self._stack) - self._ptr - 1
        
        if current_capacity < needed_space:
            # 扩容，分配足够空间
            additional_space = needed_space - current_capacity
            self._stack.extend([None] * additional_space)
            self._debug_print(f"Stack batch resized to {len(self._stack)}")
        
        # 批量推入
        for i, item in enumerate(items):
            self._ptr += 1
            self._stack[self._ptr] = item
            
        self._debug_print(f"Batch pushed {len(items)} items, ptr={self._ptr}")
        
    def batch_pop(self, count: int) -> List[Any]:
        """
        批量弹出元素（高性能）
        
        Args:
            count: 要弹出的元素数量
            
        Returns:
            弹出的元素列表
            
        Raises:
            IndexError: 如果弹出数量超过栈中元素数量
        """
        if count <= 0:
            return []
            
        if self.size() < count:
            error_msg = f"insufficient values on stack for batch_pop (size={self.size()}, requested={count})"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        # 批量弹出
        popped_items = []
        for _ in range(count):
            item = self._stack[self._ptr]
            self._stack[self._ptr] = None
            popped_items.append(item)
            self._ptr -= 1
            
        # 不需要反转，因为我们是按正确的顺序弹出的
        self._debug_print(f"Batch popped {count} items, ptr={self._ptr}")
        return popped_items
        
    def swap(self, i: int = 1) -> None:
        """
        交换栈顶元素位置
        
        Args:
            i: 要与栈顶交换的位置（1=栈顶与自己交换，即无操作，2=栈顶与次栈顶交换）
            
        Raises:
            IndexError: 如果栈中元素不足
        """
        if i <= 1:
            # i=1表示与自己交换，无需操作
            return
            
        if self.size() < i:
            error_msg = f"insufficient values on stack for swap (size={self.size()}, requested={i})"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        # 计算位置
        idx1 = self._ptr  # 栈顶位置
        idx2 = self._ptr + 1 - i  # 要交换的位置
        
        # 交换元素
        self._stack[idx1], self._stack[idx2] = self._stack[idx2], self._stack[idx1]
        self._debug_print(f"Swapped positions {idx1} and {idx2}")
        
    def rot(self, count: int = 2) -> None:
        """
        旋转堆栈元素（类似于Python的ROT_TWO, ROT_THREE等）
        
        Python字节码ROT操作的行为：
        - ROT_TWO: 将栈顶两个元素顺序反转
        - ROT_THREE: 将栈顶三个元素向上旋转一层
        
        Args:
            count: 旋转的元素数量（2=ROT_TWO, 3=ROT_THREE等）
            
        Raises:
            IndexError: 如果栈中元素不足
        """
        if count <= 1:
            # 1或更少，无需旋转
            return
            
        if self.size() < count:
            error_msg = f"insufficient values on stack for rot (size={self.size()}, requested={count})"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        if count == 2:
            # ROT_TWO: 交换栈顶两个元素
            self.swap(2)
        elif count == 3:
            # ROT_THREE: 栈顶三个元素旋转
            # Python字节码ROT_THREE的行为：
            # 将栈顶三个元素旋转，使栈顶元素上移到第三个位置
            # 例如：[1, 2, 3, 4, 5] 其中5是栈顶 -> [1, 2, 5, 3, 4]
            if self.size() < 3:
                error_msg = "ROT_THREE requires at least 3 elements"
                self._debug_print(error_msg)
                raise IndexError(error_msg)
            
            # 保存栈顶三个元素
            top = self._stack[self._ptr]        # 5
            second = self._stack[self._ptr - 1]  # 4  
            third = self._stack[self._ptr - 2]   # 3
            
            # ROT_THREE: 将栈顶元素(5)移到第三个位置
            # 位置关系：
            # ptr-2: third(3) -> 变为 top(5)
            # ptr-1: second(4) -> 保持不变
            # ptr:   top(5)    -> 变为 second(4)
            
            # 重新排列：
            self._stack[self._ptr - 2] = top     # 3 -> 5
            self._stack[self._ptr] = third        # 5 -> 3
            
            # 4保持在ptr-1位置不变
            
            self._debug_print("ROT_THREE applied")
        elif count == 4:
            # ROT_FOUR: 栈顶四个元素旋转
            if self.size() < 4:
                error_msg = "ROT_FOUR requires at least 4 elements"
                self._debug_print(error_msg)
                raise IndexError(error_msg)
            
            # 保存栈顶四个元素
            top = self._stack[self._ptr]
            second = self._stack[self._ptr - 1]
            third = self._stack[self._ptr - 2]
            fourth = self._stack[self._ptr - 3]
            
            # 重新排列：fourth, third, second, top -> third, fourth, top, second
            self._stack[self._ptr - 3] = third
            self._stack[self._ptr - 2] = fourth
            self._stack[self._ptr - 1] = top
            self._stack[self._ptr] = second
            
            self._debug_print("ROT_FOUR applied")
        else:
            # 对于其他数量的旋转，使用通用算法
            # 将栈顶count个元素向上旋转一层
            temp = self._stack[self._ptr - count + 1:self._ptr + 1]
            # 临时变量保存栈顶元素
            top_element = temp[-1]
            # 移动元素
            temp[1:] = temp[:-1]
            # 将原栈顶元素放到第count个位置
            temp[0] = top_element
            # 写回堆栈
            for i, val in enumerate(temp):
                self._stack[self._ptr - count + 1 + i] = val
            
            self._debug_print(f"Rotated {count} elements")

        
    def dup(self) -> None:
        """
        复制栈顶元素（类似于Python的DUP_TOP）
        """
        if self.empty():
            error_msg = "cannot dup from empty stack"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        # 复制栈顶元素
        top_item = self.top(1)
        self.push(top_item)
        self._debug_print("Duplicated top element")
        
    def dup_top_two(self) -> None:
        """
        复制栈顶两个元素（类似于Python的DUP_TOP_TWO）
        """
        if self.size() < 2:
            error_msg = f"insufficient values on stack for dup_top_two (size={self.size()})"
            self._debug_print(error_msg)
            raise IndexError(error_msg)
        
        # 复制栈顶两个元素
        item1 = self.top(1)
        item2 = self.top(2)
        
        self.push(item2)
        self.push(item1)
        self._debug_print("Duplicated top two elements")

        
    def __str__(self) -> str:
        """返回堆栈的字符串表示"""
        return f"FastStack({self._stack})"
        
    def __repr__(self) -> str:
        """返回堆栈的详细字符串表示"""
        return f"FastStack(size={len(self._stack)}, initial_size={self._initial_size}, stack={self._stack})"


class StackHistory:
    """
    堆栈历史记录类
    用于保存堆栈的状态历史，在异常处理等情况下恢复堆栈状态
    """
    
    def __init__(self):
        """初始化堆栈历史记录"""
        self._history: List[FastStack] = []
        
    def push(self, stack: FastStack) -> None:
        """
        将当前堆栈状态推入历史记录
        
        Args:
            stack: 当前堆栈
        """
        self._history.append(stack.copy())
        
    def pop(self) -> Optional[FastStack]:
        """
        从历史记录中弹出堆栈状态
        
        Returns:
            之前保存的堆栈状态，如果历史记录为空则返回None
        """
        if not self._history:
            return None
        return self._history.pop()
        
    def empty(self) -> bool:
        """
        检查历史记录是否为空
        
        Returns:
            如果历史记录为空返回True，否则返回False
        """
        return len(self._history) == 0
        
    def size(self) -> int:
        """
        获取历史记录大小
        
        Returns:
            历史记录中的堆栈状态数量
        """
        return len(self._history)
        
    def clear(self) -> None:
        """
        清空历史记录
        """
        self._history.clear()


class StackOperation:
    """
    堆栈操作类
    提供堆栈操作的封装，包含调试信息
    """
    
    def __init__(self, operation: str, value: Any = None):
        """
        初始化堆栈操作记录
        
        Args:
            operation: 操作名称（如'push', 'pop', 'top'）
            value: 操作值
        """
        self.operation = operation
        self.value = value
        
    def __str__(self) -> str:
        """返回操作的字符串表示"""
        if self.value is not None:
            return f"{self.operation}({self.value})"
        return self.operation


class DebugStack(FastStack):
    """
    调试版本堆栈
    提供详细的调试信息，包括操作历史和状态跟踪
    """
    
    def __init__(self, initial_size: int = 20):
        """
        初始化调试堆栈
        
        Args:
            initial_size: 初始堆栈大小
        """
        super().__init__(initial_size)
        self._operation_history: List[StackOperation] = []
        self._operation_count = 0
        
    def push(self, item: Any) -> None:
        """推入元素并记录操作"""
        super().push(item)
        self._record_operation('push', item)
        
    def pop(self) -> Any:
        """弹出元素并记录操作"""
        result = super().pop()
        self._record_operation('pop', result)
        return result
        
    def top(self) -> Any:
        """查看栈顶元素并记录操作"""
        result = super().top()
        self._record_operation('top', result)
        return result
        
    def _record_operation(self, operation: str, value: Any = None) -> None:
        """记录堆栈操作"""
        self._operation_history.append(StackOperation(operation, value))
        self._operation_count += 1
        
    def get_operation_history(self) -> List[StackOperation]:
        """
        获取操作历史
        
        Returns:
            操作历史记录列表
        """
        return self._operation_history.copy()
        
    def get_operation_count(self) -> int:
        """
        获取操作计数
        
        Returns:
            总操作次数
        """
        return self._operation_count
        
    def reset_operations(self) -> None:
        """重置操作历史"""
        self._operation_history.clear()
        self._operation_count = 0
        
    def __repr__(self) -> str:
        """返回调试堆栈的详细字符串表示"""
        return (f"DebugStack(size={len(self._stack)}, initial_size={self._initial_size}, "
                f"operations={self._operation_count}, stack={self._stack})")


# 兼容性别名
stackhist_t = StackHistory  # 类似于C++版本的typedef


def create_stack(initial_size: int = 20) -> FastStack:
    """
    创建FastStack的工厂函数
    
    Args:
        initial_size: 初始堆栈大小
        
    Returns:
        新的FastStack实例
    """
    return FastStack(initial_size)


def create_debug_stack(initial_size: int = 20) -> DebugStack:
    """
    创建DebugStack的工厂函数
    
    Args:
        initial_size: 初始堆栈大小
        
    Returns:
        新的DebugStack实例
    """
    return DebugStack(initial_size)


def stack_peek(stack: FastStack, offset: int = 0) -> Any:
    """
    查看堆栈中的元素（不弹出）
    
    Args:
        stack: 目标堆栈
        offset: 偏移量，0表示栈顶，1表示次栈顶，以此类推
        
    Returns:
        指定位置的堆栈元素
        
    Raises:
        IndexError: 如果偏移量超出堆栈范围
    """
    if offset < 0:
        raise IndexError("negative offset not supported")
    
    index = len(stack) - 1 - offset
    if index < 0:
        raise IndexError("stack underflow")
    
    return stack._stack[index]


def stack_swap(stack: FastStack) -> None:
    """
    交换栈顶两个元素
    
    Args:
        stack: 目标堆栈
        
    Raises:
        IndexError: 如果堆栈元素少于两个
    """
    if len(stack) < 2:
        raise IndexError("stack must have at least 2 elements")
    
    top = stack._stack[-1]
    second = stack._stack[-2]
    stack._stack[-1] = second
    stack._stack[-2] = top


def stack_dup(stack: FastStack) -> None:
    """
    复制栈顶元素
    
    Args:
        stack: 目标堆栈
        
    Raises:
        IndexError: 如果堆栈为空
    """
    if len(stack) == 0:
        raise IndexError("stack is empty")
    
    top = stack._stack[-1]
    stack._stack.append(top)


def stack_rot_two(stack: FastStack) -> None:
    """
    旋转栈顶两个元素（与swap相同）
    
    Args:
        stack: 目标堆栈
    """
    stack_swap(stack)


def stack_rot_three(stack: FastStack) -> None:
    """
    旋转栈顶三个元素
    
    原来的栈: [A, B, C, D] (栈顶为D)
    旋转后: [A, C, B, D]
    
    Args:
        stack: 目标堆栈
    """
    if len(stack) < 3:
        raise IndexError("stack must have at least 3 elements")
    
    # 获取栈顶三个元素
    top = stack._stack[-1]
    second = stack._stack[-2]
    third = stack._stack[-3]
    
    # 重新排列
    stack._stack[-1] = second
    stack._stack[-2] = third
    stack._stack[-3] = top


def stack_rot_four(stack: FastStack) -> None:
    """
    旋转栈顶四个元素
    
    原来的栈: [A, B, C, D, E] (栈顶为E)
    旋转后: [A, D, C, B, E]
    
    Args:
        stack: 目标堆栈
    """
    if len(stack) < 4:
        raise IndexError("stack must have at least 4 elements")
    
    # 获取栈顶四个元素
    top = stack._stack[-1]
    second = stack._stack[-2]
    third = stack._stack[-3]
    fourth = stack._stack[-4]
    
    # 重新排列
    stack._stack[-1] = second
    stack._stack[-2] = third
    stack._stack[-3] = fourth
    stack._stack[-4] = top


# 堆栈验证函数
def validate_stack_state(stack: FastStack, expected_size: int) -> bool:
    """
    验证堆栈状态
    
    Args:
        stack: 目标堆栈
        expected_size: 期望的堆栈大小
        
    Returns:
        如果堆栈大小匹配返回True，否则返回False
    """
    return len(stack) == expected_size


def stack_summary(stack: FastStack) -> str:
    """
    获取堆栈摘要信息
    
    Args:
        stack: 目标堆栈
        
    Returns:
        堆栈摘要字符串
    """
    if len(stack) == 0:
        return "Stack: empty"
    elif len(stack) == 1:
        return f"Stack: 1 element: {stack._stack[-1]}"
    else:
        top = stack._stack[-1]
        second = stack._stack[-2] if len(stack) >= 2 else None
        if second:
            return f"Stack: {len(stack)} elements, top: {top}, second: {second}"
        else:
            return f"Stack: {len(stack)} elements, top: {top}"