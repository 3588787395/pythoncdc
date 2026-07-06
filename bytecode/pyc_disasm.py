"""
字节码反汇编模块
负责将字节码反汇编为指令
支持Python 3.11+字节码格式
参照C++版pycdc实现
"""

from typing import List, Dict, Optional, Tuple
from bytecode.bytecode_ops import Opcode, opcode_name


class Instruction:
    """指令类 - 对应C++版本的指令结构"""
    
    def __init__(self, offset: int, opcode: int, opname: str, arg: int = 0, 
                 has_arg: bool = False, is_extended: bool = False):
        self.offset = offset
        self.opcode = opcode
        self.opname = opname
        self.arg = arg
        self.has_arg = has_arg
        self.is_extended = is_extended
        self.extended_arg = 0  # 用于EXTENDED_ARG累积
    
    def __repr__(self):
        if self.has_arg:
            return f"Instruction({self.offset}: {self.opname} {self.arg})"
        return f"Instruction({self.offset}: {self.opname})"
    
    def is_jump_instruction(self) -> bool:
        """判断是否为跳转指令"""
        jump_opcodes = {
            'JUMP_FORWARD_A', 'JUMP_BACKWARD_A', 'JUMP_BACKWARD_NO_INTERRUPT_A',
            'POP_JUMP_FORWARD_IF_TRUE_A', 'POP_JUMP_FORWARD_IF_FALSE_A',
            'POP_JUMP_BACKWARD_IF_TRUE_A', 'POP_JUMP_BACKWARD_IF_FALSE_A',
            'JUMP_IF_TRUE_A', 'JUMP_IF_FALSE_A',
            'POP_JUMP_IF_TRUE_A', 'POP_JUMP_IF_FALSE_A',
            'JUMP_IF_NOT_EXC_MATCH_A', 'POP_JUMP_FORWARD_IF_NOT_NONE_A',
            'POP_JUMP_FORWARD_IF_NONE_A', 'POP_JUMP_BACKWARD_IF_NOT_NONE_A',
            'POP_JUMP_BACKWARD_IF_NONE_A',
        }
        return self.opname in jump_opcodes
    
    @property
    def target(self):
        """跳转目标（如果有）
        
        参照C++ ASTree.cpp实现:
        - Python 3.10+: 跳转偏移量以2字节为单位
        - FORWARD跳转: target = offset + 2 + arg * 2
        - BACKWARD跳转: target = offset + 2 - arg * 2
        
        注意：+2是因为跳转是从当前指令结束后开始的
        """
        if self.is_jump_instruction() and self.has_arg:
            # 计算跳转目标
            # +2是因为跳转是从当前指令（2字节）结束后开始的
            if 'FORWARD' in self.opname:
                return self.offset + 2 + self.arg * 2
            elif 'BACKWARD' in self.opname:
                return self.offset + 2 - self.arg * 2
        return None
    
    def is_terminator(self) -> bool:
        """判断是否为终止指令"""
        terminator_opcodes = {
            'RETURN_VALUE', 'RETURN_GENERATOR', 'RAISE_VARARGS_A',
            'YIELD_VALUE', 'YIELD_FROM', 'POP_BLOCK', 'POP_EXCEPT',
        }
        return self.opname in terminator_opcodes


class PycDisassembler:
    """PYC字节码反汇编器 - 参照C++版实现"""
    
    # Python 3.11+ 无参数指令集合
    # 格式: [opcode][cache]
    # [关键修复] 只包含真正无参数的指令
    NO_ARG_OPCODES = frozenset({
        Opcode.CACHE,           # 0x00 - 缓存
        Opcode.POP_TOP,         # 0x01 - 弹出栈顶
        Opcode.PUSH_NULL,       # 0x02 - 推入NULL
        Opcode.NOP,             # 0x09 - 空操作
        Opcode.UNARY_POSITIVE,  # 0x0A - 一元正
        Opcode.UNARY_NEGATIVE,  # 0x0B - 一元负
        Opcode.UNARY_NOT,       # 0x0C - 一元非
        Opcode.UNARY_INVERT,    # 0x0F - 一元按位取反
        Opcode.BINARY_SUBSCR,   # 0x19 - 二元下标
        Opcode.GET_LEN,         # 0x1E - 获取长度
        Opcode.MATCH_MAPPING,   # 0x1F - 匹配映射
        Opcode.MATCH_SEQUENCE,  # 0x20 - 匹配序列
        Opcode.MATCH_KEYS,      # 0x21 - 匹配键
        Opcode.PUSH_EXC_INFO,   # 0x23 - 推入异常信息
        Opcode.CHECK_EXC_MATCH, # 0x24 - 检查异常匹配
        Opcode.CHECK_EG_MATCH,  # 0x25 - 检查异常组匹配
        Opcode.WITH_EXCEPT_START,  # 0x31 - with异常处理开始
        Opcode.GET_AITER,       # 0x32
        Opcode.GET_ANEXT,       # 0x33
        Opcode.BEFORE_ASYNC_WITH,  # 0x34
        Opcode.BEFORE_WITH,     # 0x35 - with语句准备
        Opcode.END_ASYNC_FOR,   # 0x36
        Opcode.STORE_SUBSCR,    # 0x3C - 存储下标
        Opcode.DELETE_SUBSCR,   # 0x3D - 删除下标
        Opcode.GET_ITER,        # 0x44 - 获取迭代器
        Opcode.GET_YIELD_FROM_ITER,  # 0x45
        Opcode.PRINT_EXPR,      # 0x46 - 打印表达式
        Opcode.LOAD_BUILD_CLASS, # 0x47 - 加载__build_class__
        Opcode.GET_AWAITABLE,   # 0x49
        Opcode.LOAD_ASSERTION_ERROR,  # 0x4A - 加载AssertionError
        Opcode.RETURN_GENERATOR,   # 0x4B
        Opcode.RETURN_VALUE,    # 0x53 - 返回值
        Opcode.IMPORT_STAR,     # 0x54 - 导入全部
        Opcode.SETUP_ANNOTATIONS,  # 0x55 - 设置注解
        Opcode.YIELD_VALUE,     # 0x56 - 产生值
        Opcode.ASYNC_GEN_WRAP,  # 0x57
        Opcode.PREP_RERAISE_STAR,  # 0x58
        Opcode.POP_EXCEPT,      # 0x59 - 弹出异常
    })
    
    def __init__(self, bytecode: bytes, module, version=(3, 11), code_obj=None):
        self.bytecode = bytecode
        self.module = module
        self.code_obj = code_obj
        self.pos = 0
        self.length = len(bytecode)
        self.version = version
        self.instructions: List[Instruction] = []
        self.extended_arg = 0  # 累积的扩展参数
    
    def disassemble(self, exception_table: bytes = None) -> List[Instruction]:
        """反汇编字节码 - 参照C++版bc_next实现
        
        Args:
            exception_table: Python 3.11+ 的异常表字节串
        """
        self.instructions = []
        self.pos = 0
        self.extended_arg = 0
        
        while self.pos < self.length:
            instr = self._next_instruction()
            if instr:
                self.instructions.append(instr)
        
        # [关键修复] Python 3.11+ 从异常表生成虚拟的 PUSH_EXC_INFO 指令
        if exception_table and self.version >= (3, 11):
            self._add_exception_table_instructions(exception_table)
        
        # 按偏移量排序指令
        self.instructions.sort(key=lambda i: i.offset)
        
        return self.instructions
    
    def _add_exception_table_instructions(self, exception_table: bytes) -> None:
        """从异常表生成虚拟的 PUSH_EXC_INFO 指令
        
        注意：对于多个 except 块，只有一个 PUSH_EXC_INFO（在第一个 except 块的开始处）
        其他 except 块共享同一个异常处理代码，不需要额外的 PUSH_EXC_INFO
        """
        from bytecode.exception_table import parse_exception_table
        
        entries = parse_exception_table(exception_table)
        
        # 只处理 depth=0 的条目（try 块对应的 PUSH_EXC_INFO）
        # 对于多个 except 块，只有一个 PUSH_EXC_INFO
        for entry in entries:
            if entry.depth == 0:  # 只处理 try 块的异常表条目
                # 检查是否已经有 PUSH_EXC_INFO 在这个位置
                existing = [i for i in self.instructions if i.offset == entry.target]
                if not existing:
                    # 创建虚拟的 PUSH_EXC_INFO 指令
                    virt_instr = Instruction(
                        offset=entry.target,
                        opcode=Opcode.PUSH_EXC_INFO,
                        opname='PUSH_EXC_INFO',
                        arg=0,
                        has_arg=False
                    )
                    self.instructions.append(virt_instr)
    
    def _next_instruction(self) -> Optional[Instruction]:
        """获取下一条指令 - 参照C++版实现"""
        if self.pos >= self.length:
            return None
        
        # [关键修复] 跳过所有连续的CACHE指令，与dis模块保持一致
        # 注意：CACHE指令(0x00)用于填充，不应该被当作普通指令
        # Python 3.11+ 中，CALL 等指令后面可能有多个 CACHE 指令用于缓存
        while self.pos < self.length and self.bytecode[self.pos] == Opcode.CACHE:
            self.pos += 2  # CACHE指令占2字节
        if self.pos >= self.length:
            return None
        
        start_pos = self.pos
        opcode_byte = self.bytecode[self.pos]
        self.pos += 1
        
        opcode = opcode_byte
        operand = 0
        # [关键修复] Python 3.11+ 所有指令都是2字节格式
        # 但无参数指令的第二个字节是cache，应该被忽略
        has_arg = opcode not in self.NO_ARG_OPCODES
        is_extended = False
        
        # Python 3.11+ 字节码格式处理
        if self.version >= (3, 11):
            # Python 3.11+ 指令格式：
            # - 有参数指令: [opcode][oparg] (2字节)
            # - 无参数指令: [opcode][cache] (2字节)，但cache被忽略
            if self.pos < self.length:
                if has_arg:
                    operand = self.bytecode[self.pos]
                # 无论是否有参数，都跳过第二个字节
                self.pos += 1
            
            # 处理EXTENDED_ARG - 累积扩展参数
            if opcode == Opcode.EXTENDED_ARG_A:
                self.extended_arg = (self.extended_arg << 8) | operand
                is_extended = True
            else:
                # 合并扩展参数
                if self.extended_arg > 0:
                    operand = (self.extended_arg << 8) | operand
                    is_extended = True
                self.extended_arg = 0
        
        else:
            # 旧版Python字节码格式 (< 3.11)
            if opcode >= Opcode.PYC_HAVE_ARG:
                if self.pos + 1 >= self.length:
                    return None
                
                # 处理EXTENDED_ARG
                if opcode == Opcode.EXTENDED_ARG_A:
                    self.extended_arg = (self.extended_arg << 16) | \
                                       (self.bytecode[self.pos] | 
                                        (self.bytecode[self.pos + 1] << 8))
                    self.pos += 2
                    is_extended = True
                    operand = self.extended_arg
                else:
                    operand = self.bytecode[self.pos] | (self.bytecode[self.pos + 1] << 8)
                    self.pos += 2
                    
                    # 合并之前累积的扩展参数
                    if self.extended_arg > 0:
                        operand = self.extended_arg | operand
                        is_extended = True
                        self.extended_arg = 0
        
        return Instruction(
            offset=start_pos,
            opcode=opcode,
            opname=opcode_name(opcode, self.version),
            arg=operand,
            has_arg=has_arg,
            is_extended=is_extended
        )
    
    def disassemble_to_text(self) -> str:
        """反汇编为文本格式"""
        instructions = self.disassemble()
        lines = []
        
        for instr in instructions:
            line = f"{instr.offset:4d}: {instr.opname}"
            if instr.has_arg:
                line += f" {instr.arg}"
                # 尝试解析参数含义
                arg_desc = self._describe_operand(instr.opcode, instr.arg)
                if arg_desc:
                    line += f" ({arg_desc})"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _describe_operand(self, opcode: int, operand: int) -> Optional[str]:
        """描述操作数的含义"""
        code_obj = self.code_obj if self.code_obj else \
                   (self.module.code.get() if self.module and self.module.code else None)
        
        if not code_obj:
            return None
        
        try:
            # LOAD_CONST - 常量
            if opcode == Opcode.LOAD_CONST_A:
                if hasattr(code_obj, 'co_consts'):
                    consts = list(code_obj.co_consts)
                    if 0 <= operand < len(consts):
                        const = consts[operand]
                        if const is None:
                            return "None"
                        elif isinstance(const, (int, float, str, bool)):
                            return repr(const)[:50]
                        elif hasattr(const, 'co_name'):
                            return f"code:{const.co_name}"
                elif hasattr(code_obj, 'consts') and code_obj.consts:
                    consts_obj = code_obj.consts.get()
                    if consts_obj and hasattr(consts_obj, 'get') and operand < consts_obj.size():
                        const = consts_obj.get(operand)
                        if const:
                            return str(const.get())[:50]
            
            # LOAD_NAME, STORE_NAME, LOAD_ATTR, STORE_ATTR - 名称
            elif opcode in (Opcode.LOAD_NAME_A, Opcode.STORE_NAME_A, 
                           Opcode.LOAD_ATTR_A, Opcode.STORE_ATTR_A,
                           Opcode.LOAD_GLOBAL_A, Opcode.STORE_GLOBAL_A,
                           Opcode.LOAD_METHOD_A):
                if hasattr(code_obj, 'co_names'):
                    names = list(code_obj.co_names)
                    if 0 <= operand < len(names):
                        return names[operand]
                elif hasattr(code_obj, 'names') and code_obj.names:
                    names_obj = code_obj.names.get()
                    if names_obj and hasattr(names_obj, 'get') and operand < names_obj.size():
                        name = names_obj.get(operand)
                        if name:
                            return str(name.get())
            
            # LOAD_FAST, STORE_FAST - 局部变量
            elif opcode in (Opcode.LOAD_FAST_A, Opcode.STORE_FAST_A):
                if hasattr(code_obj, 'co_varnames'):
                    varnames = list(code_obj.co_varnames)
                    if 0 <= operand < len(varnames):
                        return varnames[operand]
                elif hasattr(code_obj, 'local_names') and code_obj.local_names:
                    locals_obj = code_obj.local_names.get()
                    if locals_obj and hasattr(locals_obj, 'get') and operand < locals_obj.size():
                        local = locals_obj.get(operand)
                        if local:
                            return str(local.get())
            
            # 跳转指令 - 计算目标地址
            elif opcode in (Opcode.JUMP_FORWARD_A, Opcode.FOR_ITER_A,
                           Opcode.POP_JUMP_FORWARD_IF_FALSE_A,
                           Opcode.POP_JUMP_FORWARD_IF_TRUE_A,
                           Opcode.POP_JUMP_FORWARD_IF_NONE_A,
                           Opcode.POP_JUMP_FORWARD_IF_NOT_NONE_A):
                # Python 3.10+: 相对跳转，以2字节为单位
                # 参照C++ ASTree.cpp: target = pos + operand * 2
                if self.version >= (3, 10):
                    # 注意：self.pos在反汇编完成后是指向下一个指令的位置
                    # 我们需要使用当前指令的offset来计算目标
                    # 目标 = 当前指令位置 + 操作数 * 2
                    target = self.pos + operand * 2 - 2  # 减去2是因为self.pos已经前进过
                    return f"to {target}"
                else:
                    target = self.pos + operand - 2
                    return f"to {target}"
            
            elif opcode in (Opcode.JUMP_BACKWARD_A, 
                           Opcode.POP_JUMP_BACKWARD_IF_FALSE_A,
                           Opcode.POP_JUMP_BACKWARD_IF_TRUE_A,
                           Opcode.POP_JUMP_BACKWARD_IF_NONE_A,
                           Opcode.POP_JUMP_BACKWARD_IF_NOT_NONE_A,
                           Opcode.JUMP_BACKWARD_NO_INTERRUPT_A):
                # 向后跳转
                if self.version >= (3, 10):
                    target = self.pos - operand * 2 - 2
                    return f"to {target}"
                else:
                    target = self.pos - operand - 2
                    return f"to {target}"
            
            # 比较操作
            elif opcode == Opcode.COMPARE_OP_A:
                compare_ops = ['<', '<=', '==', '!=', '>', '>=', 'in', 'not in', 'is', 'is not', 'exception match']
                if 0 <= operand < len(compare_ops):
                    return compare_ops[operand]
            
            # 二元操作
            elif opcode == Opcode.BINARY_OP_A:
                binary_ops = ['+', '&', '//', '<<', '@', '*', '%', '|', '**', '>>', '-', '/', '^']
                if 0 <= operand < len(binary_ops):
                    return binary_ops[operand]
        
        except Exception:
            pass
        
        return None
    
    def get_instruction_at(self, offset: int) -> Optional[Instruction]:
        """获取指定偏移处的指令"""
        for instr in self.instructions:
            if instr.offset == offset:
                return instr
        return None
