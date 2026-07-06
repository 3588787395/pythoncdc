import sys
"""
核心数据结构模块
包含PycObject、ASTNode等核心类
"""

from typing import Any, List, Optional, Dict, Union, Tuple
from abc import ABC, abstractmethod
import weakref


class PycObject(ABC):
    """PYC对象基类"""
    
    TYPE_NULL = '0'
    TYPE_NONE = 'N'
    TYPE_FALSE = 'F'
    TYPE_TRUE = 'T'
    TYPE_STOPITER = 'S'
    TYPE_ELLIPSIS = '.'
    TYPE_INT = 'i'
    TYPE_INT64 = 'I'
    TYPE_FLOAT = 'f'
    TYPE_BINARY_FLOAT = 'g'
    TYPE_COMPLEX = 'x'
    TYPE_BINARY_COMPLEX = 'y'
    TYPE_LONG = 'l'
    TYPE_STRING = 's'
    TYPE_INTERNED = 't'
    TYPE_STRINGREF = 'R'
    TYPE_OBREF = 'r'
    TYPE_TUPLE = '('
    TYPE_LIST = '['
    TYPE_DICT = '{'
    TYPE_CODE = 'c'
    TYPE_CODE2 = 'C'
    TYPE_UNICODE = 'u'
    TYPE_UNKNOWN = '?'
    TYPE_SET = '<'
    TYPE_FROZENSET = '>'
    TYPE_ASCII = 'a'
    TYPE_ASCII_INTERNED = 'A'
    TYPE_SMALL_TUPLE = ')'
    TYPE_SHORT_ASCII = 'z'
    TYPE_SHORT_ASCII_INTERNED = 'Z'
    
    # Python 3.11+ numeric types
    TYPE_REF_NULL = 0x00
    TYPE_REF_NONE = 0x01
    TYPE_REF_FALSE = 0x02
    TYPE_REF_TRUE = 0x03
    TYPE_REF_STOPITERATION = 0x04
    TYPE_REF_ELLIPSIS = 0x05
    TYPE_REF_INT = 0x06
    TYPE_REF_INT64 = 0x07
    TYPE_REF_FLOAT = 0x08
    TYPE_REF_COMPLEX = 0x09
    TYPE_REF_LONG = 0x0A
    TYPE_REF_CODE = 0x0B
    TYPE_REF_UNICODE = 0x0C
    TYPE_REF_TUPLE = 0x0D
    TYPE_REF_LIST = 0x0E
    TYPE_REF_DICT = 0x0F
    TYPE_REF_SET = 0x10
    TYPE_REF_FROZENSET = 0x11
    TYPE_REF_BYTES = 0x12
    TYPE_REF_BYTEARRAY = 0x13
    TYPE_REF_MEMORYVIEW = 0x14
    
    def __init__(self, obj_type: str = TYPE_UNKNOWN):
        self._type = obj_type
        self._refs = 0
    
    @property
    def type(self) -> str:
        return self._type
    
    def add_ref(self) -> None:
        """增加引用计数"""
        self._refs += 1
    
    def del_ref(self) -> None:
        """减少引用计数，如果为0则删除对象"""
        self._refs -= 1
        if self._refs <= 0:
            del self
    
    def is_equal(self, other: 'PycObject') -> bool:
        """比较两个对象是否相等"""
        return self is other
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载数据"""
        pass
    
    def __str__(self) -> str:
        """字符串表示"""
        # 根据类型返回相应的字符串表示
        if self._type == PycObject.TYPE_TRUE:
            return "True"
        elif self._type == PycObject.TYPE_FALSE:
            return "False"
        elif self._type == PycObject.TYPE_NONE:
            return "None"
        elif self._type == PycObject.TYPE_NULL:
            return "NULL"
        elif self._type == PycObject.TYPE_ELLIPSIS:
            return "..."
        elif self._type == PycObject.TYPE_STOPITER:
            return "StopIteration"
        else:
            # 默认返回类型名
            return f"PycObject({self._type})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()


class PycRef:
    """智能指针类，管理PycObject的生命周期"""
    
    def __init__(self, obj: Optional[PycObject] = None):
        self._obj = obj
        if obj is not None:
            obj.add_ref()
    
    def __del__(self):
        if self._obj is not None:
            self._obj.del_ref()
    
    def __copy__(self):
        return PycRef(self._obj)
    
    def __deepcopy__(self, memo):
        return PycRef(self._obj)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, PycRef):
            return self._obj is other._obj
        return self._obj is other
    
    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
    
    def __bool__(self) -> bool:
        return self._obj is not None
    
    def __getattr__(self, name):
        return getattr(self._obj, name)
    
    def __call__(self, *args, **kwargs):
        return self._obj(*args, **kwargs)
    
    def get(self) -> Optional[PycObject]:
        """获取内部对象"""
        return self._obj
    
    def cast(self, target_type):
        """转换为指定类型"""
        if not isinstance(self._obj, target_type):
            raise TypeError(f"Cannot cast {type(self._obj)} to {target_type}")
        return self._obj
    
    def try_cast(self, target_type):
        """尝试转换为指定类型"""
        if isinstance(self._obj, target_type):
            return self._obj
        return None


class PycCode(PycObject):
    """Python代码对象"""
    
    def __init__(self, obj_type: str = PycObject.TYPE_CODE):
        super().__init__(obj_type)
        self.arg_count = 0
        self.pos_only_arg_count = 0
        self.kw_only_arg_count = 0
        self.num_locals = 0
        self.stack_size = 0
        self.flags = 0
        self.code: Optional[PycRef] = None
        self.consts: Optional[PycRef] = None
        self.names: Optional[PycRef] = None
        self.local_names: Optional[PycRef] = None
        self.local_kinds: Optional[PycRef] = None
        self.free_vars: Optional[PycRef] = None
        self.cell_vars: Optional[PycRef] = None
        self.file_name: Optional[PycRef] = None
        self.name: Optional[PycRef] = None
        self.qual_name: Optional[PycRef] = None
        self.first_line = 0
        self.ln_table: Optional[PycRef] = None
        self.except_table: Optional[PycRef] = None
        self.globals_used: List[PycRef] = []
        self.instr_store_global_names: List[str] = []  # 存储使用了STORE_GLOBAL指令的变量名
    
    @classmethod
    def from_python_code(cls, py_code) -> 'PycCode':
        """从Python的code对象创建PycCode实例
        
        用于测试和调试
        """
        pyc_code = cls()
        pyc_code.arg_count = py_code.co_argcount
        pyc_code.pos_only_arg_count = getattr(py_code, 'co_posonlyargcount', 0)
        pyc_code.kw_only_arg_count = getattr(py_code, 'co_kwonlyargcount', 0)
        pyc_code.num_locals = py_code.co_nlocals
        pyc_code.stack_size = py_code.co_stacksize
        pyc_code.flags = py_code.co_flags
        pyc_code.first_line = py_code.co_firstlineno
        
        # 设置字节码
        bytecode_str = PycString(PycObject.TYPE_STRING)
        bytecode_str.value = bytes(py_code.co_code)
        pyc_code.code = PycRef(bytecode_str)
        
        # 设置常量
        consts_seq = PycSequence(PycObject.TYPE_TUPLE)
        for const in py_code.co_consts:
            if isinstance(const, str):
                const_str = PycString(PycObject.TYPE_STRING)
                const_str.value = const
                consts_seq.add(PycRef(const_str))
            elif isinstance(const, int):
                const_int = PycNumeric(PycObject.TYPE_INT)
                const_int.value = const
                consts_seq.add(PycRef(const_int))
            elif hasattr(const, 'co_code'):  # code对象
                nested_code = cls.from_python_code(const)
                consts_seq.add(PycRef(nested_code))
            else:
                const_str = PycString(PycObject.TYPE_STRING)
                const_str.value = str(const)
                consts_seq.add(PycRef(const_str))
        pyc_code.consts = PycRef(consts_seq)
        
        # 设置名称
        names_seq = PycSequence(PycObject.TYPE_TUPLE)
        for name in py_code.co_names:
            name_str = PycString(PycObject.TYPE_STRING)
            name_str.value = name
            names_seq.add(PycRef(name_str))
        pyc_code.names = PycRef(names_seq)
        
        # 设置局部变量名
        local_names_seq = PycSequence(PycObject.TYPE_TUPLE)
        for name in py_code.co_varnames:
            name_str = PycString(PycObject.TYPE_STRING)
            name_str.value = name
            local_names_seq.add(PycRef(name_str))
        pyc_code.local_names = PycRef(local_names_seq)
        
        # 设置函数名
        name_str = PycString(PycObject.TYPE_STRING)
        name_str.value = py_code.co_name
        pyc_code.name = PycRef(name_str)
        
        # 设置文件名
        file_str = PycString(PycObject.TYPE_STRING)
        file_str.value = py_code.co_filename
        pyc_code.file_name = PycRef(file_str)
        
        return pyc_code

    def to_python_code(self) -> 'types.CodeType':
        import types as _types

        def _resolve_ref(ref):
            if ref is None:
                return None
            obj = ref.get() if hasattr(ref, 'get') else ref
            if obj is None:
                return None
            if isinstance(obj, PycObject):
                if obj._type == PycObject.TYPE_NONE:
                    return None
                if obj._type == PycObject.TYPE_TRUE:
                    return True
                if obj._type == PycObject.TYPE_FALSE:
                    return False
                if obj._type == PycObject.TYPE_ELLIPSIS:
                    return ...
            if isinstance(obj, PycString):
                return obj.value
            if isinstance(obj, PycNumeric):
                return obj.value
            if isinstance(obj, PycCode):
                return obj.to_python_code()
            if isinstance(obj, PycSequence):
                return tuple(_resolve_ref(obj.get(i)) for i in range(obj.size()))
            if hasattr(obj, 'value'):
                return obj.value
            return obj

        def _resolve_bytes(ref):
            if ref is None:
                return b''
            obj = ref.get() if hasattr(ref, 'get') else ref
            if isinstance(obj, (PycString, PycBytes)):
                if hasattr(obj, 'raw_bytes') and obj.raw_bytes is not None:
                    return obj.raw_bytes
                val = obj.value
                if isinstance(val, bytes):
                    return val
                if isinstance(val, str):
                    return val.encode('latin-1')
                return b''
            if isinstance(obj, bytes):
                return obj
            return b''

        def _resolve_tuple(ref):
            val = _resolve_ref(ref)
            if val is None:
                return ()
            if isinstance(val, tuple):
                return val
            return ()

        def _resolve_str(ref):
            val = _resolve_ref(ref)
            if val is None:
                return ''
            if isinstance(val, str):
                return val
            return str(val)

        co_argcount = self.arg_count
        co_posonlyargcount = self.pos_only_arg_count
        co_kwonlyargcount = self.kw_only_arg_count
        co_nlocals = self.num_locals
        co_stacksize = self.stack_size
        co_flags = self.flags
        co_code = _resolve_bytes(self.code)
        co_consts = _resolve_tuple(self.consts)
        co_names = _resolve_tuple(self.names)
        co_varnames = _resolve_tuple(self.local_names)
        co_filename = _resolve_str(self.file_name)
        co_name = _resolve_str(self.name)
        co_firstlineno = self.first_line
        co_lnotab = _resolve_bytes(self.ln_table)
        co_freevars = _resolve_tuple(self.free_vars)
        co_cellvars = _resolve_tuple(self.cell_vars)

        if sys.version_info >= (3, 11):
            co_exceptiontable = _resolve_bytes(self.except_table)
            try:
                return _types.CodeType(
                    co_argcount, co_posonlyargcount, co_kwonlyargcount,
                    co_nlocals, co_stacksize, co_flags, co_code,
                    co_consts, co_names, co_varnames,
                    co_filename, co_name, co_name,
                    co_firstlineno, co_lnotab,
                    co_exceptiontable, co_freevars, co_cellvars
                )
            except TypeError:
                return _types.CodeType(
                    co_argcount, co_posonlyargcount, co_kwonlyargcount,
                    co_nlocals, co_stacksize, co_flags, co_code,
                    co_consts, co_names, co_varnames,
                    co_filename, co_name, co_name,
                    co_firstlineno, co_lnotab,
                    co_freevars, co_cellvars
                )
        elif sys.version_info >= (3, 8):
            return _types.CodeType(
                co_argcount, co_posonlyargcount, co_kwonlyargcount,
                co_nlocals, co_stacksize, co_flags, co_code,
                co_consts, co_names, co_varnames,
                co_filename, co_name, co_firstlineno, co_lnotab,
                co_freevars, co_cellvars
            )
        else:
            return _types.CodeType(
                co_argcount, co_kwonlyargcount, co_nlocals,
                co_stacksize, co_flags, co_code,
                co_consts, co_names, co_varnames,
                co_filename, co_name, co_firstlineno, co_lnotab,
                co_freevars, co_cellvars
            )

    def get_const(self, idx: int) -> Optional[PycRef]:
        """获取常量"""
        if self.consts and self.consts.get():
            const_obj = self.consts.get()
            if isinstance(const_obj, PycSequence):
                return const_obj.get(idx)
        return None
    
    def get_name(self, idx: int) -> Optional[PycRef]:
        """获取名称"""
        if self.names and self.names.get():
            names_obj = self.names.get()
            if isinstance(names_obj, PycSequence):
                return names_obj.get(idx)
        return None
    
    def get_local(self, idx: int) -> Optional[PycRef]:
        """获取局部变量"""
        if self.local_names and self.local_names.get():
            local_names_obj = self.local_names.get()
            if isinstance(local_names_obj, PycSequence):
                return local_names_obj.get(idx)
            elif isinstance(local_names_obj, PycString):
                names_str = local_names_obj.value
                names = names_str.split('\x00')
                if 0 <= idx < len(names):
                    return PycRef(PycString(PycObject.TYPE_STRING))
        return None
    
    def mark_global(self, varname: PycRef) -> None:
        """标记全局变量"""
        self.globals_used.append(varname)
    
    def get_cell_var(self, module: 'PycModule', idx: int) -> Optional[PycRef]:
        """获取cell变量（用于闭包）
        
        根据C++版本的实现：
        - 对于LOAD_DEREF，应该使用free_vars
        - 对于LOAD_CLOSURE/MAKE_CELL，应该使用cell_vars/local_names
        """
        # 首先尝试从free_vars获取（用于LOAD_DEREF）
        if self.free_vars and self.free_vars.get():
            free_vars_obj = self.free_vars.get()
            if isinstance(free_vars_obj, PycSequence):
                if 0 <= idx < free_vars_obj.size():
                    return free_vars_obj.get(idx)
        
        # 然后尝试从cell_vars获取（早期版本）
        if self.cell_vars and self.cell_vars.get():
            cell_vars_obj = self.cell_vars.get()
            if isinstance(cell_vars_obj, PycSequence):
                if 0 <= idx < cell_vars_obj.size():
                    return cell_vars_obj.get(idx)
        
        # 最后尝试从local_names获取（Python 3.11+的cell变量）
        if module.ver_compare(3, 11) >= 0:
            return self.get_local(idx)
        
        return None
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载代码对象"""
        from .pyc_stream import load_object, PycRef
        
        is_py311 = module.ver_compare(3, 11) >= 0
        if is_py311:
            # Python 3.11 格式 (根据C++版本pyc_code.cpp):
            # arg_count (4), pos_only (4), kw_only (4), nlocals (4), stack_size (4), flags (4)
            self.arg_count = stream.get32()
            self.pos_only_arg_count = stream.get32()
            self.kw_only_arg_count = stream.get32()
            self.num_locals = stream.get32()  # Python 3.11中nlocals存在
            self.stack_size = stream.get32()  # Python 3.11中是4字节，不是uleb128
            self.flags = stream.get32()
        else:
            # 传统格式
            if module.ver_compare(1, 3) >= 0 and module.ver_compare(2, 3) < 0:
                self.arg_count = stream.get16()
            elif module.ver_compare(2, 3) >= 0:
                self.arg_count = stream.get32()
            
            if module.ver_compare(3, 8) >= 0:
                self.pos_only_arg_count = stream.get32()
            else:
                self.pos_only_arg_count = 0
            
            if module.major >= 3:
                self.kw_only_arg_count = stream.get32()
            else:
                self.kw_only_arg_count = 0
            
            if module.ver_compare(1, 3) >= 0 and module.ver_compare(2, 3) < 0:
                self.num_locals = stream.get16()
            elif module.ver_compare(2, 3) >= 0:
                self.num_locals = stream.get32()
            else:
                self.num_locals = 0
            
            if module.ver_compare(1, 5) >= 0 and module.ver_compare(2, 3) < 0:
                self.stack_size = stream.get16()
            elif module.ver_compare(2, 3) >= 0:
                self.stack_size = stream.get32()
            else:
                self.stack_size = 0
            
            if module.ver_compare(1, 3) >= 0 and module.ver_compare(2, 3) < 0:
                self.flags = stream.get16()
            elif module.ver_compare(2, 3) >= 0:
                self.flags = stream.get32()
            else:
                self.flags = 0
            
            if module.ver_compare(3, 8) < 0 and module.ver_compare(2, 3) >= 0:
                if self.flags & 0xF0000000:
                    raise ValueError("Cannot remap unexpected flags")
                self.flags = (self.flags & 0xFFFF) | ((self.flags & 0xFFF0000) << 4)
        
        if is_py311:
            # Python 3.11: 代码对象格式
            # 所有字段都作为marshal对象加载
            self.code = load_object(stream, module)
            self.consts = load_object(stream, module)
            self.names = load_object(stream, module)
            self.local_names = load_object(stream, module)
            self.local_kinds = load_object(stream, module)
            # Python 3.11中free_vars和cell_vars是空元组，不从流中加载
            self.free_vars = PycRef(PycSequence(PycObject.TYPE_TUPLE))
            self.cell_vars = PycRef(PycSequence(PycObject.TYPE_TUPLE))
            self.file_name = load_object(stream, module)
            self.name = load_object(stream, module)
            self.qual_name = load_object(stream, module)
            self.first_line = stream.get32()
            self.ln_table = load_object(stream, module)
            self.except_table = load_object(stream, module)
        else:
            # 旧版本使用marshal对象
            self.code = load_object(stream, module)
            self.consts = load_object(stream, module)
            self.names = load_object(stream, module)
            
            if module.ver_compare(1, 3) >= 0:
                self.local_names = load_object(stream, module)
            else:
                self.local_names = PycRef(PycSequence(PycObject.TYPE_TUPLE))
            
            if module.ver_compare(3, 11) >= 0:
                self.local_kinds = load_object(stream, module)
            else:
                self.local_kinds = PycRef(PycString())
            
            if module.ver_compare(2, 1) >= 0 and module.ver_compare(3, 11) < 0:
                self.free_vars = load_object(stream, module)
            else:
                self.free_vars = PycRef(PycSequence(PycObject.TYPE_TUPLE))
            
            if module.ver_compare(2, 1) >= 0 and module.ver_compare(3, 11) < 0:
                self.cell_vars = load_object(stream, module)
            else:
                self.cell_vars = PycRef(PycSequence(PycObject.TYPE_TUPLE))
            
            self.file_name = load_object(stream, module)
            self.name = load_object(stream, module)
            
            if module.ver_compare(3, 11) >= 0:
                self.qual_name = load_object(stream, module)
            else:
                self.qual_name = PycRef(PycString())
            
            if module.ver_compare(1, 5) >= 0 and module.ver_compare(2, 3) < 0:
                self.first_line = stream.get16()
            elif module.ver_compare(2, 3) >= 0:
                self.first_line = stream.get32()
            
            if module.ver_compare(1, 5) >= 0:
                self.ln_table = load_object(stream, module)
            else:
                self.ln_table = PycRef(PycString())
            
            if module.ver_compare(3, 11) >= 0:
                self.except_table = load_object(stream, module)
            else:
                self.except_table = PycRef(PycString())
    
    def _parse_varint(self, data: bytes, pos: int) -> Tuple[int, int]:
        """解析变长整数 (varint)
        
        根据C++实现，Python异常表使用特殊的varint编码:
        - 使用6位存储数据 (0x3F掩码)
        - 使用第7位(0x40)作为继续标志
        - 数据向左移位6位来累积
        
        返回 (值, 新位置)
        """
        if pos >= len(data):
            return 0, pos
        
        b = data[pos]
        pos += 1
        
        val = b & 0x3F
        while b & 0x40:
            if pos >= len(data):
                break
            val <<= 6
            b = data[pos]
            pos += 1
            val |= (b & 0x3F)
        
        return val, pos
    
    def exception_table_entries(self) -> List[Dict]:
        """解析异常表条目
        
        根据C++版本的PycCode::exceptionTableEntries实现
        Python 3.11+ 使用新的异常表格式
        
        返回异常表条目列表，每个条目包含:
        - start_offset: 受保护代码块的起始偏移（包含）
        - end_offset: 受保护代码块的结束偏移（不包含）
        - target: 异常处理器的偏移
        - stack_depth: 栈深度
        - push_lasti: 是否压入最后一条指令的偏移
        """
        entries = []
        
        if not self.except_table or not self.except_table.get():
            return entries
        
        except_data = self.except_table.get()
        if not hasattr(except_data, 'value') and not hasattr(except_data, '_value'):
            return entries
        
        # 获取异常表数据
        if hasattr(except_data, 'value'):
            data = except_data.value
        else:
            data = except_data._value
        
        if isinstance(data, str):
            data = data.encode('latin-1')
        
        if not data or len(data) == 0:
            return entries
        
        # 解析异常表条目
        # 格式（根据C++实现）:
        # - start: varint * 2
        # - length: varint * 2
        # - target: varint * 2
        # - dl: varint (depth << 1 | lasti)
        pos = 0
        while pos < len(data):
            try:
                start, pos = self._parse_varint(data, pos)
                start *= 2
                
                length, pos = self._parse_varint(data, pos)
                length *= 2
                end = start + length
                
                target, pos = self._parse_varint(data, pos)
                target *= 2
                
                dl, pos = self._parse_varint(data, pos)
                depth = dl >> 1
                lasti = bool(dl & 1)
                
                entries.append({
                    'start_offset': start,
                    'end_offset': end,
                    'target': target,
                    'stack_depth': depth,
                    'push_lasti': lasti
                })
            except Exception:
                # 解析失败，跳出循环
                break
        
        return entries

    def __str__(self) -> str:
        """字符串表示 - 显示函数名"""
        # 尝试获取函数名
        func_name = None
        
        if self.name and self.name.get():
            name_obj = self.name.get()
            if hasattr(name_obj, 'value'):
                func_name = name_obj.value
            elif hasattr(name_obj, '_value'):
                func_name = name_obj._value
        
        if func_name:
            return f"<code '{func_name}'>"
        else:
            return "<code object>"


class PycString(PycObject):
    """字符串对象"""
    
    def __init__(self, obj_type: str = PycObject.TYPE_STRING):
        super().__init__(obj_type)
        self._value = ""
        self._raw_bytes: Optional[bytes] = None  # [关键修复] 保留原始字节数据
    
    @property
    def value(self) -> str:
        return self._value
    
    @value.setter
    def value(self, val: str):
        self._value = val
    
    @property
    def raw_bytes(self) -> Optional[bytes]:
        """[关键修复] 获取原始字节数据（用于行号表等二进制数据）"""
        return self._raw_bytes
    
    def length(self) -> int:
        return len(self._value)
    
    def __len__(self) -> int:
        """支持len()函数调用"""
        return len(self._value)
    
    def __getitem__(self, key):
        """支持索引访问"""
        return self._value[key]
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载字符串"""
        if self._type == PycObject.TYPE_STRINGREF:
            ref = module.get_intern(stream.get32())
            if ref and ref.get():
                self._type = ref.get()._type
                self._value = ref.get()._value
                self._raw_bytes = getattr(ref.get(), '_raw_bytes', None)
        else:
            if self._type in (PycObject.TYPE_SHORT_ASCII, PycObject.TYPE_SHORT_ASCII_INTERNED):
                length = stream.get_byte()
            else:
                length = stream.get32()
            
            if length < 0:
                raise ValueError("Invalid string length")
            
            if length > 1000000:
                raise ValueError("String length too large: {}".format(length))
            
            data = stream.get_buffer(length)
            # [关键修复] 保留原始字节数据
            self._raw_bytes = data
            
            if self._type in (PycObject.TYPE_ASCII, PycObject.TYPE_ASCII_INTERNED,
                            PycObject.TYPE_SHORT_ASCII, PycObject.TYPE_SHORT_ASCII_INTERNED):
                try:
                    self._value = data.decode('ascii')
                except UnicodeDecodeError:
                    raise ValueError("Invalid bytes in ASCII string")
            else:
                if module.str_is_unicode():
                    self._value = data.decode('utf-8')
                else:
                    self._value = data.decode('latin-1')
            
            if self._type in (PycObject.TYPE_INTERNED, PycObject.TYPE_ASCII_INTERNED,
                            PycObject.TYPE_SHORT_ASCII_INTERNED):
                from .pyc_stream import PycRef
                module.intern(PycRef(self))


class PycBytes(PycObject):
    """字节对象（用于存储字节码等二进制数据）"""
    
    def __init__(self, obj_type: str = PycObject.TYPE_STRING):
        super().__init__(obj_type)
        self._value = b""
    
    @property
    def value(self) -> bytes:
        return self._value
    
    @value.setter
    def value(self, val: bytes):
        self._value = val
    
    def length(self) -> int:
        return len(self._value)
    
    def __len__(self) -> int:
        """支持len()函数调用"""
        return len(self._value)
    
    def __getitem__(self, key):
        """支持索引访问"""
        return self._value[key]
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载字节数据"""
        if self._type in (PycObject.TYPE_SHORT_ASCII, PycObject.TYPE_SHORT_ASCII_INTERNED):
            length = stream.get_byte()
        else:
            length = stream.get32()
        
        if length < 0:
            raise ValueError("Invalid bytes length")
        
        if length > 10000000:  # 10MB limit
            raise ValueError("Bytes length too large: {}".format(length))
        
        # 直接读取原始字节数据，不进行解码
        self._value = stream.get_buffer(length)


class PycSequence(PycObject):
    """序列对象（列表、元组等）"""
    
    def __init__(self, obj_type: str = PycObject.TYPE_LIST):
        super().__init__(obj_type)
        self._values: List[PycRef] = []
    
    def add(self, value: PycRef) -> None:
        """添加元素"""
        self._values.append(value)
    
    def get(self, idx: int) -> Optional[PycRef]:
        """获取元素"""
        if 0 <= idx < len(self._values):
            return self._values[idx]
        return None
    
    def size(self) -> int:
        """获取大小"""
        return len(self._values)
    
    def values(self) -> List[PycRef]:
        """获取所有值"""
        return self._values
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载序列"""
        from .pyc_stream import load_object
        
        if self._type == PycObject.TYPE_SMALL_TUPLE:
            size = stream.get_byte()
        elif self._type == PycObject.TYPE_DICT:
            size = None
        elif self._type == PycObject.TYPE_TUPLE and module.ver_compare(3, 11) >= 0:
            size = stream.get_uleb128()
        else:
            size = stream.get32()
        
        if size is not None and size > 10000:
            raise ValueError("Sequence size too large: {}".format(size))
        
        self._values.clear()
        
        if self._type == PycObject.TYPE_DICT:
            while True:
                key = load_object(stream, module)
                if not key:
                    break
                val = load_object(stream, module)
                self._values.append((key, val))
        else:
            for i in range(size):
                self._values.append(load_object(stream, module))


class PycNumeric(PycObject):
    """数值对象基类"""
    
    def __init__(self, obj_type: str = PycObject.TYPE_INT):
        super().__init__(obj_type)
        self._value = 0
    
    @property
    def value(self) -> Union[int, float]:
        return self._value
    
    @value.setter
    def value(self, val: Union[int, float]):
        self._value = val
    
    def load(self, stream: 'PycData', module: 'PycModule') -> None:
        """从流中加载数值"""
        if self._type in (PycObject.TYPE_INT, PycObject.TYPE_INT64):
            if self._type == PycObject.TYPE_INT64:
                lo = stream.get32()
                hi = stream.get32()
                self._value = (hi << 32) | lo
            else:
                self._value = stream.get32()
        elif self._type in (PycObject.TYPE_FLOAT, PycObject.TYPE_BINARY_FLOAT):
            import struct
            if self._type == PycObject.TYPE_FLOAT:
                length = stream.get_byte()
                if length < 0:
                    raise ValueError("Invalid float length")
                data = stream.get_buffer(length)
                self._value = float(data.decode('ascii'))
            else:
                data = stream.get_buffer(8)
                self._value = struct.unpack('<d', data)[0]
    
    def __str__(self) -> str:
        """字符串表示"""
        return str(self._value)
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"PycNumeric({self._value})"


class PycModule:
    """PYC模块"""
    
    MAGIC_VERSIONS = {
        0x00999902: (1, 0),
        0x00999903: (1, 1),
        0x0A0D2E89: (1, 3),
        0x0A0D1704: (1, 4),
        0x0A0D4E99: (1, 5),
        0x0A0DC4FC: (1, 6),
        0x0A0DC687: (2, 0),
        0x0A0DEB2A: (2, 1),
        0x0A0DED2D: (2, 2),
        0x0A0DF23B: (2, 3),
        0x0A0DF26D: (2, 4),
        0x0A0DF2B3: (2, 5),
        0x0A0DF2D1: (2, 6),
        0x0A0DF303: (2, 7),
        0x0A0D0C3A: (3, 0),
        0x0A0D0C4E: (3, 1),
        0x0A0D0C6C: (3, 2),
        0x0A0D0C9E: (3, 3),
        0x0A0D0CEE: (3, 4),
        0x0A0D0D16: (3, 5),
        0x0A0D0D17: (3, 5, 3),
        0x0A0D0D33: (3, 6),
        0x0A0D0D42: (3, 7),
        0x0A0D0D55: (3, 8),
        0x0A0D0D61: (3, 9),
        0x0A0D0D6F: (3, 10),
        0x0A0D0DA7: (3, 11),
        0x0A0D0DCB: (3, 12),
        0x0A0D0DF3: (3, 13),
    }
    
    def __init__(self):
        self.major = -1
        self.minor = -1
        self.unicode = False
        self.code: Optional[PycRef] = None
        self.interns: List[PycRef] = []
        self.refs: List[PycRef] = []
    
    @property
    def major_version(self) -> int:
        """主版本号（兼容性）"""
        return self.major
    
    @property
    def minor_version(self) -> int:
        """次版本号（兼容性）"""
        return self.minor
    
    def is_valid(self) -> bool:
        """检查模块是否有效"""
        return self.major >= 0 and self.minor >= 0
    
    def ver_compare(self, maj: int, min: int) -> int:
        """比较版本"""
        if self.major > maj:
            return 1
        elif self.major < maj:
            return -1
        else:
            return self.minor - min
    
    def is_unicode(self) -> bool:
        """是否使用Unicode"""
        return self.unicode
    
    def str_is_unicode(self) -> bool:
        """字符串是否使用Unicode"""
        return (self.major >= 3) or (self.code and self.code.get().flags & 0x200000 != 0)
    
    def intern(self, string: PycRef) -> None:
        """添加到内部字符串表"""
        self.interns.append(string)
    
    def get_intern(self, ref: int) -> Optional[PycRef]:
        """获取内部字符串"""
        if 0 <= ref < len(self.interns):
            return self.interns[ref]
        return None
    
    def ref_object(self, obj: PycRef) -> None:
        """添加到对象引用表"""
        self.refs.append(obj)
    
    def get_ref(self, ref: int) -> Optional[PycRef]:
        """获取对象引用"""
        if 0 <= ref < len(self.refs):
            return self.refs[ref]
        return None
    
    def load(self, stream) -> None:
        """从流中加载PYC模块"""
        self._load_from_stream(stream)
    
    @staticmethod
    def is_supported_version(major: int, minor: int) -> bool:
        """检查版本是否支持"""
        return (major, minor) in [(1, 0), (1, 1), (1, 3), (1, 4), (1, 5), (1, 6),
                                (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
                                (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
                                (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13)]
    
    def load_from_file(self, filename: str) -> None:
        """从文件加载PYC模块"""
        from .pyc_stream import PycFile, load_object
        
        stream = PycFile(filename)
        stream.open()
        if not stream.is_open():
            raise ValueError(f"Cannot open file: {filename}")
        
        try:
            self._load_from_stream(stream)
        finally:
            if stream._stream:
                stream._stream.close()
    
    def _load_from_stream(self, stream) -> None:
        """从流加载PYC模块"""
        import struct
        from .pyc_stream import load_object
        
        magic = stream.get32()
        self.set_version(magic)
        
        if not self.is_valid():
            raise ValueError(f"Unsupported magic number: 0x{magic:08X}")
        
        # Python 3.7+: 读取flags
        if self.ver_compare(3, 7) >= 0:
            flags = stream.get32()
            
            if flags & 0x8:
                # Bit 0x8 set: 读取source hash和source size (两个30-bit字段)
                source_size_hash1 = stream.get32()
                source_size_hash2 = stream.get32()
            else:
                # Bit 0x8 not set: 读取timestamp和source size
                timestamp = stream.get32()
                
                if self.ver_compare(3, 3) >= 0:
                    source_size = stream.get32()
                else:
                    source_size = stream.get16()
        else:
            # Python 3.7以下版本
            if self.ver_compare(3, 3) >= 0:
                timestamp = stream.get32()
                source_size = stream.get32()
            elif self.ver_compare(2, 3) >= 0:
                timestamp = stream.get32()
                source_size = stream.get16()
            else:
                timestamp = stream.get32()
                source_size = 0
        
        # 使用marshal加载（支持所有Python版本）
        try:
            import marshal
            # 修复Python 3.11 PYC文件头部读取
            if self.ver_compare(3, 11) >= 0:
                # Python 3.11+ 文件格式：直接读取剩余数据
                data = stream.read_all()
            else:
                # 旧版本可能需要不同的处理
                data = stream.read_all()
            
            if not data:
                raise ValueError("No data remaining to parse")
                
            code_obj = marshal.loads(data)
            
            from .pyc_loader_v2 import marshal_to_pyc_obj
            self.code = marshal_to_pyc_obj(code_obj, self)
        except ImportError:
            # 如果marshal不可用，使用原有的load_object
            self.code = load_object(stream, self)
        except Exception as e:
            # 调试信息，帮助定位问题
            print(f"Debug: Failed to load PYC data: {e}")
            raise
        
        if not self.code or not self.code.get():
            raise ValueError("No code object found")
    
    def set_version(self, magic: int) -> None:
        """根据magic number设置版本"""
        version = self.MAGIC_VERSIONS.get(magic)
        if version:
            self.major, self.minor = version
        else:
            self.major = -1
            self.minor = -1
    
    def set_version_from_string(self, version_str: str) -> None:
        """从版本字符串设置版本"""
        try:
            parts = version_str.split('.')
            if len(parts) == 2:
                major = int(parts[0])
                minor = int(parts[1])
                self.major = major
                self.minor = minor
            else:
                raise ValueError(f"Invalid version string: {version_str}")
        except ValueError as e:
            raise ValueError(f"Invalid version string: {version_str}")
