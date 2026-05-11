"""
基本块模块 - 定义控制流图中的基本块

基本块是控制流图的基本单元，包含一段顺序执行的指令序列。
每个基本块有一个入口和一个出口，内部没有分支或跳转。
"""

from typing import List, Set, Optional, Dict, Any, Iterator
from dataclasses import dataclass, field
import dis


@dataclass
class Instruction:
    """表示单条字节码指令"""
    offset: int
    opcode: int
    opname: str
    arg: Optional[int] = None
    argval: Any = None
    starts_line: Optional[int] = None
    is_jump_target: bool = False
    
    def __hash__(self):
        return hash(self.offset)
    
    def __eq__(self, other):
        if not isinstance(other, Instruction):
            return False
        return self.offset == other.offset
    
    def __repr__(self):
        if self.arg is not None:
            return f"Instruction({self.offset}: {self.opname} {self.arg})"
        return f"Instruction({self.offset}: {self.opname})"


class BasicBlock:
    """
    控制流图中的基本块
    
    基本块是一组顺序执行的指令，具有以下特性：
    - 只有一个入口点（第一条指令）
    - 只有一个出口点（最后一条指令）
    - 内部没有分支、跳转或标签
    """
    
    _id_counter = 0
    
    def __init__(self, start_offset: int = 0):
        """
        初始化基本块
        
        Args:
            start_offset: 基本块在字节码中的起始偏移量
        """
        BasicBlock._id_counter += 1
        self._id = BasicBlock._id_counter
        
        self.start_offset = start_offset
        self.end_offset = start_offset
        
        self.instructions: List[Instruction] = []
        
        self.predecessors: Set['BasicBlock'] = set()
        self.successors: Set['BasicBlock'] = set()
        self.exception_successors: Set['BasicBlock'] = set()
        
        self.is_entry = False
        self.is_exit = False
        
        self.dominators: Set['BasicBlock'] = set()
        self.immediate_dominator: Optional['BasicBlock'] = None
        self.dominated_blocks: Set['BasicBlock'] = set()

        self.post_dominators: Set['BasicBlock'] = set()
        self.immediate_post_dominator: Optional['BasicBlock'] = None
        
        self.loop_header = False
        self.loop_depth = 0
        self.in_loop: Optional['BasicBlock'] = None
        
        self.exception_handler = False
        self.exception_type: Optional[str] = None
        
        self.visited = False
        self.marked = False
        
        self.annotations: Dict[str, Any] = {}
    
    @property
    def conditional_successors(self) -> Set['BasicBlock']:
        return set(self.successors) - self.exception_successors

    @property
    def id(self) -> int:
        """返回基本块的唯一标识符"""
        return self._id
    
    @classmethod
    def reset_id_counter(cls):
        """重置ID计数器（用于测试）"""
        cls._id_counter = 0
    
    def add_instruction(self, instruction: Instruction) -> None:
        """
        向基本块添加指令
        
        Args:
            instruction: 要添加的指令
        """
        if not self.instructions:
            self.start_offset = instruction.offset
        
        self.instructions.append(instruction)
        self.end_offset = instruction.offset
    
    def add_instructions(self, instructions: List[Instruction]) -> None:
        """
        批量添加指令
        
        Args:
            instructions: 指令列表
        """
        for instr in instructions:
            self.add_instruction(instr)
    
    def get_first_instruction(self) -> Optional[Instruction]:
        """获取基本块的第一条指令"""
        return self.instructions[0] if self.instructions else None
    
    def get_last_instruction(self) -> Optional[Instruction]:
        """获取基本块的最后一条指令"""
        return self.instructions[-1] if self.instructions else None
    
    def add_predecessor(self, block: 'BasicBlock') -> None:
        """
        添加前驱基本块
        
        Args:
            block: 前驱基本块
        """
        self.predecessors.add(block)
    
    def add_successor(self, block: 'BasicBlock') -> None:
        """
        添加后继基本块
        
        Args:
            block: 后继基本块
        """
        self.successors.add(block)
        block.add_predecessor(self)
    
    def remove_predecessor(self, block: 'BasicBlock') -> None:
        """
        移除前驱基本块
        
        Args:
            block: 要移除的前驱基本块
        """
        self.predecessors.discard(block)
    
    def remove_successor(self, block: 'BasicBlock') -> None:
        """
        移除后继基本块
        
        Args:
            block: 要移除的后继基本块
        """
        self.successors.discard(block)
        block.remove_predecessor(self)
    
    def is_conditional(self) -> bool:
        """
        检查基本块是否以条件分支结束
        
        Returns:
            如果是条件分支则返回True
        """
        if not self.instructions:
            return False
        
        last = self.get_last_instruction()
        if last is None:
            return False
        
        conditional_ops = {
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
            'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        }
        
        if last.opname in conditional_ops:
            return True
        
        return len(self.successors) > 1
    
    def is_unconditional_jump(self) -> bool:
        """
        检查基本块是否以无条件跳转结束
        
        Returns:
            如果是无条件跳转则返回True
        """
        if not self.instructions:
            return False
        
        last = self.get_last_instruction()
        if last is None:
            return False
        
        jump_ops = {'JUMP_FORWARD', 'JUMP_ABSOLUTE'}
        
        return last.opname in jump_ops
    
    def is_return(self) -> bool:
        """
        检查基本块是否以返回指令结束
        
        Returns:
            如果是返回指令则返回True
        """
        if not self.instructions:
            return False
        
        last = self.get_last_instruction()
        if last is None:
            return False
        
        return last.opname in {'RETURN_VALUE', 'RETURN_CONST'}
    
    def is_raise(self) -> bool:
        """
        检查基本块是否以抛出异常结束
        
        Returns:
            如果是抛出异常则返回True
        """
        if not self.instructions:
            return False
        
        last = self.get_last_instruction()
        if last is None:
            return False
        
        return last.opname in {'RAISE_VARARGS', 'RERAISE'}
    
    def has_jump_instruction(self) -> bool:
        """
        检查基本块是否包含跳转指令
        
        Returns:
            如果包含跳转指令则返回True
        """
        jump_ops = {
            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
            'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        }
        
        return any(instr.opname in jump_ops for instr in self.instructions)
    
    def get_jump_targets(self) -> List[int]:
        """
        获取基本块中所有跳转指令的目标偏移量
        
        Returns:
            目标偏移量列表
        """
        targets = []
        jump_ops = {
            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
            'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        }
        
        for instr in self.instructions:
            if instr.opname in jump_ops and instr.argval is not None:
                if isinstance(instr.argval, int):
                    targets.append(instr.argval)
        
        return targets
    
    def dominates(self, other: 'BasicBlock') -> bool:
        """
        检查当前基本块是否支配另一个基本块
        
        Args:
            other: 另一个基本块
            
        Returns:
            如果支配则返回True
        """
        return self in other.dominators
    
    def strictly_dominates(self, other: 'BasicBlock') -> bool:
        return self != other and self.dominates(other)

    def post_dominates(self, other: 'BasicBlock') -> bool:
        return self in other.post_dominators

    def strictly_post_dominates(self, other: 'BasicBlock') -> bool:
        return self != other and self.post_dominates(other)
    
    def __iter__(self) -> Iterator[Instruction]:
        """迭代基本块中的指令"""
        return iter(self.instructions)
    
    def __len__(self) -> int:
        """返回基本块中的指令数量"""
        return len(self.instructions)
    
    def __bool__(self) -> bool:
        """检查基本块是否非空"""
        return bool(self.instructions)
    
    def __hash__(self):
        return hash(self._id)
    
    def __eq__(self, other):
        if not isinstance(other, BasicBlock):
            return False
        return self._id == other._id
    
    def __repr__(self):
        return f"BasicBlock({self._id}, offset={self.start_offset}-{self.end_offset}, instrs={len(self.instructions)})"
    
    def __str__(self):
        lines = [f"Block {self._id} (offset {self.start_offset}-{self.end_offset}):"]
        
        if self.is_entry:
            lines.append("  [ENTRY]")
        if self.is_exit:
            lines.append("  [EXIT]")
        if self.loop_header:
            lines.append(f"  [LOOP HEADER, depth={self.loop_depth}]")
        if self.exception_handler:
            lines.append(f"  [EXCEPTION HANDLER: {self.exception_type}]")
        
        for instr in self.instructions:
            line_info = f"L{instr.starts_line:3}" if instr.starts_line else "   "
            target_marker = ">" if instr.is_jump_target else " "
            arg_str = f" {instr.arg}" if instr.arg is not None else ""
            lines.append(f"  {line_info} {target_marker} {instr.offset:3}: {instr.opname}{arg_str}")
        
        if self.predecessors:
            pred_ids = [str(p._id) for p in self.predecessors]
            lines.append(f"  Predecessors: {', '.join(pred_ids)}")
        
        if self.successors:
            succ_ids = [str(s._id) for s in self.successors]
            lines.append(f"  Successors: {', '.join(succ_ids)}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将基本块转换为字典表示
        
        Returns:
            包含基本块信息的字典
        """
        return {
            'id': self._id,
            'start_offset': self.start_offset,
            'end_offset': self.end_offset,
            'is_entry': self.is_entry,
            'is_exit': self.is_exit,
            'loop_header': self.loop_header,
            'loop_depth': self.loop_depth,
            'exception_handler': self.exception_handler,
            'instruction_count': len(self.instructions),
            'predecessor_ids': [p._id for p in self.predecessors],
            'successor_ids': [s._id for s in self.successors],
        }
