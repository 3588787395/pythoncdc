import sys
"""
PYC流处理模块
处理PYC文件的数据流和对象加载
"""

import struct
from typing import Optional, BinaryIO, TYPE_CHECKING

if TYPE_CHECKING:
    from .pyc_objects import PycModule


class PycData:
    """PYC数据源基类"""
    
    def __init__(self):
        pass
    
    def is_open(self) -> bool:
        """检查是否打开"""
        raise NotImplementedError
    
    def get_byte(self) -> int:
        """读取一个字节"""
        raise NotImplementedError
    
    def get_bytes(self, size: int) -> bytes:
        """读取指定大小的字节"""
        raise NotImplementedError
    
    def get16(self) -> int:
        """读取16位整数"""
        raise NotImplementedError
    
    def get32(self) -> int:
        """读取32位整数"""
        raise NotImplementedError
    
    def get_uleb128(self) -> int:
        """读取unsigned LEB128编码的整数"""
        raise NotImplementedError
    
    def get64(self) -> int:
        """读取64位整数"""
        raise NotImplementedError
    
    def get_buffer(self, size: int) -> bytes:
        """读取缓冲区"""
        raise NotImplementedError
    
    def tell(self) -> int:
        """获取当前位置"""
        raise NotImplementedError
    
    def seek(self, pos: int) -> None:
        """移动到指定位置"""
        raise NotImplementedError


class PycFile(PycData):
    """PYC文件数据源"""
    
    def __init__(self, filepath: str):
        super().__init__()
        self._filepath = filepath
        self._stream: Optional[BinaryIO] = None
        self._pos = 0
    
    def open(self) -> None:
        """打开文件"""
        if self._stream is None:
            self._stream = open(self._filepath, 'rb')
    
    def close(self) -> None:
        """关闭文件"""
        if self._stream is not None:
            self._stream.close()
            self._stream = None
    
    def is_open(self) -> bool:
        """检查是否打开"""
        return self._stream is not None
    
    def get_byte(self) -> int:
        """读取一个字节"""
        if not self.is_open():
            raise ValueError("File not open")
        byte = self._stream.read(1)
        if not byte:
            raise EOFError("Unexpected end of file")
        self._pos += 1
        return byte[0]
    
    def get_bytes(self, size: int) -> bytes:
        """读取指定大小的字节"""
        if not self.is_open():
            raise ValueError("File not open")
        data = self._stream.read(size)
        if len(data) != size:
            raise EOFError("Unexpected end of file")
        self._pos += size
        return data
    
    def get16(self) -> int:
        """读取16位整数（小端序）"""
        buffer = self.get_bytes(2)
        return struct.unpack('<H', buffer)[0]
    
    def get32(self) -> int:
        """读取32位整数（小端序）"""
        buffer = self.get_bytes(4)
        return struct.unpack('<I', buffer)[0]
    
    def get32_be(self) -> int:
        """读取32位整数（大端序）"""
        buffer = self.get_bytes(4)
        return struct.unpack('>I', buffer)[0]
    
    def get_varint(self) -> int:
        """读取varint（可变长度整数）"""
        byte = self.get_byte()
        value = byte & 0x3F
        while byte & 0x40:
            value <<= 6
            byte = self.get_byte()
            value |= (byte & 0x3F)
        return value
    
    def get_uleb128(self) -> int:
        """读取unsigned LEB128编码的整数"""
        result = 0
        shift = 0
        while True:
            try:
                byte = self.get_byte()
            except EOFError:
                return 0
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return result
    
    def get64(self) -> int:
        """读取64位整数（小端序）"""
        buffer = self.get_bytes(8)
        return struct.unpack('<Q', buffer)[0]
    
    def get_buffer(self, size: int) -> bytes:
        """读取缓冲区"""
        return self.get_bytes(size)
    
    def read_all(self) -> bytes:
        """读取剩余所有数据"""
        if not self.is_open():
            raise ValueError("File not open")
        data = self._stream.read()
        self._pos += len(data)
        return data
    
    def tell(self) -> int:
        """获取当前位置"""
        if not self.is_open():
            raise ValueError("File not open")
        return self._stream.tell()
    
    def seek(self, pos: int) -> None:
        """移动到指定位置"""
        if not self.is_open():
            raise ValueError("File not open")
        self._stream.seek(pos)
        self._pos = pos
    
    def __del__(self):
        """析构函数，自动关闭文件"""
        self.close()


class PycRef:
    """PYC对象引用"""
    
    def __init__(self, obj):
        self._obj = obj
    
    def get(self):
        """获取引用的对象"""
        return self._obj
    
    def set(self, obj) -> None:
        """设置引用的对象"""
        self._obj = obj


def create_object(obj_type: str) -> Optional['PycObject']:
    """根据类型创建PYC对象"""
    from .pyc_objects import PycObject, PycCode, PycString, PycSequence, PycNumeric
    
    if obj_type == PycObject.TYPE_CODE:
        return PycCode()
    elif obj_type in (PycObject.TYPE_STRING, PycObject.TYPE_UNICODE,
                     PycObject.TYPE_ASCII, PycObject.TYPE_SHORT_ASCII,
                     PycObject.TYPE_INTERNED, PycObject.TYPE_ASCII_INTERNED,
                     PycObject.TYPE_SHORT_ASCII_INTERNED):
        return PycString(obj_type)
    elif obj_type in (PycObject.TYPE_TUPLE, PycObject.TYPE_LIST, 
                     PycObject.TYPE_SMALL_TUPLE):
        return PycSequence(obj_type)
    elif obj_type == PycObject.TYPE_DICT:
        return PycSequence(obj_type)
    elif obj_type in (PycObject.TYPE_INT, PycObject.TYPE_INT64):
        return PycNumeric(obj_type)
    elif obj_type in (PycObject.TYPE_FLOAT, PycObject.TYPE_BINARY_FLOAT):
        return PycNumeric(obj_type)
    elif obj_type == PycObject.TYPE_NONE:
        return PycObject(PycObject.TYPE_NONE)
    else:
        return None


def load_object(stream: PycData, module: 'PycModule') -> Optional[PycRef]:
    """从流中加载PYC对象"""
    
    from .pyc_objects import PycObject, PycCode, PycString, PycSequence, PycNumeric
    
    try:
        obj_type_byte = stream.get_byte()
    except EOFError:
        return None
    
    # 只在出错时打印
    # if obj_type_byte in [0xE3, 0x06, 0x10, 0x73, 0x74]:
    #     print("DEBUG load_object: type byte = 0x{:02X} at pos {}".format(obj_type_byte, stream.tell() - 1))
    
    # 检查是否是OBREF类型 (Python 3.4+: 'r' = 0x72)
    if obj_type_byte == 0x72 or obj_type_byte == 0xF2:
        # OBREF: 读取32位索引
        index = stream.get32()
        return module.get_ref(index)
    
    # Python 3.11 REF types (0x08-0x17)
    # 这些类型读取32位索引并返回缓存对象的引用
    if 0x08 <= obj_type_byte <= 0x17:
        index = stream.get32()
        ref = module.get_ref(index)
        if ref is not None and hasattr(ref, 'get') and ref.get() is not None:
            obj = ref.get()
            print(f"[DEBUG load_object] REF type: obj_type_byte=0x{obj_type_byte:02X}, index={index}, type={type(obj).__name__}", file=sys.stderr)
        return ref
    
    # 对于所有其他类型，剥离高位标志位 (0x80)
    # Python 3.11的0xE3 (TYPE_CODE with ref flag) 应该被当作0x63处理
    obj_type = obj_type_byte & 0x7F
    
    # 检查reference标志
    is_ref = (obj_type_byte & 0x80) != 0
    
    # Python 3.11: 检查特殊引用标记 (不带ref标志的)
    # 这些是真正的特殊类型，不是带标志的标准类型
    if module.ver_compare(3, 11) >= 0:
        if obj_type_byte in [0x04, 0x13, 0x00]:
            if obj_type_byte == 0x04:
                cached_tuple = PycSequence(PycObject.TYPE_TUPLE)
                cached_tuple._values = []
                return PycRef(cached_tuple)
            elif obj_type_byte == 0x13:
                cached_string = PycString(PycObject.TYPE_STRING)
                cached_string._value = ""
                cached_string._raw_bytes = b""  # [关键修复] 初始化raw_bytes
                return PycRef(cached_string)
            elif obj_type_byte == 0x00:
                return None
    
    # 创建对象
    obj = create_object_numeric(obj_type)
    
    if obj is None:
        # 未知类型，回退stream位置
        stream.seek(stream.tell() - 1)
        return None
    
    try:
        obj.load(stream, module)
        # 如果设置了reference标志，注册对象引用
        if is_ref:
            module.ref_object(PycRef(obj))
    except Exception as e:
        import traceback
        error_msg = str(e)
        if not error_msg:
            error_msg = type(e).__name__
        print("DEBUG load_object: Error loading object type 0x{:02X}: {} {}".format(obj_type_byte, type(e).__name__, error_msg))
        traceback.print_exc()
        # 出错时回退stream位置
        stream.seek(stream.tell() - 1)
        return None
    
    return PycRef(obj)


def convert_python_obj(python_obj, module: 'PycModule') -> Optional['PycObject']:
    """将Python对象转换为PycObject"""
    from .pyc_objects import PycObject, PycCode, PycString, PycSequence, PycNumeric
    
    if python_obj is None:
        return PycObject(PycObject.TYPE_NONE)
    elif isinstance(python_obj, bool):
        return PycObject(PycObject.TYPE_TRUE if python_obj else PycObject.TYPE_FALSE)
    elif isinstance(python_obj, int):
        result = PycNumeric(PycObject.TYPE_INT)
        result._value = python_obj
        return result
    elif isinstance(python_obj, float):
        result = PycNumeric(PycObject.TYPE_FLOAT)
        result._value = python_obj
        return result
    elif isinstance(python_obj, complex):
        result = PycNumeric(PycObject.TYPE_COMPLEX)
        result._value = python_obj
        return result
    elif isinstance(python_obj, str):
        result = PycString(PycObject.TYPE_UNICODE)
        result._value = python_obj
        return result
    elif isinstance(python_obj, bytes):
        result = PycString(PycObject.TYPE_STRING)
        result._value = python_obj.decode('latin-1')
        return result
    elif isinstance(python_obj, tuple):
        result = PycSequence(PycObject.TYPE_TUPLE)
        result._values = [PycRef(convert_python_obj(item, module)) for item in python_obj]
        return result
    elif isinstance(python_obj, list):
        result = PycSequence(PycObject.TYPE_LIST)
        result._values = [PycRef(convert_python_obj(item, module)) for item in python_obj]
        return result
    else:
        print(f"DEBUG convert_python_obj: 未知类型 {type(python_obj)}")
        return None


def create_object_numeric(obj_type: int) -> Optional['PycObject']:
    """根据数字类型创建PYC对象"""
    from .pyc_objects import PycObject, PycCode, PycString, PycSequence, PycNumeric
    
    # Python 3.11 marshal types
    if obj_type == 0x00:  # NULL
        return PycObject(PycObject.TYPE_NULL)
    elif obj_type == 0x4E:  # NONE ('N')
        return PycObject(PycObject.TYPE_NONE)
    elif obj_type == 0x46:  # FALSE ('F')
        return PycObject(PycObject.TYPE_FALSE)
    elif obj_type == 0x54:  # TRUE ('T')
        return PycObject(PycObject.TYPE_TRUE)
    elif obj_type == 0x53:  # STOPITERATION ('S')
        return PycObject(PycObject.TYPE_STOPITER)
    elif obj_type == 0x2E:  # ELLIPSIS ('.')
        return PycObject(PycObject.TYPE_ELLIPSIS)
    elif obj_type == 0x69:  # INT ('i')
        return PycNumeric(PycObject.TYPE_INT)
    elif obj_type == 0x49:  # INT64 ('I')
        return PycNumeric(PycObject.TYPE_INT64)
    elif obj_type == 0x66:  # FLOAT ('f')
        return PycNumeric(PycObject.TYPE_FLOAT)
    elif obj_type == 0x67:  # BINARY_FLOAT ('g')
        return PycNumeric(PycObject.TYPE_BINARY_FLOAT)
    elif obj_type == 0x78:  # COMPLEX ('x')
        return PycNumeric(PycObject.TYPE_COMPLEX)
    elif obj_type == 0x79:  # BINARY_COMPLEX ('y')
        return PycNumeric(PycObject.TYPE_BINARY_COMPLEX)
    elif obj_type == 0x6C:  # LONG ('l')
        return PycNumeric(PycObject.TYPE_LONG)
    elif obj_type == 0x73:  # STRING ('s')
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x74:  # INTERNED ('t')
        return PycString(PycObject.TYPE_INTERNED)
    elif obj_type == 0x52:  # STRINGREF ('R')
        return PycString(PycObject.TYPE_STRINGREF)
    elif obj_type == 0x75:  # UNICODE ('u')
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0x61:  # ASCII ('a')
        return PycString(PycObject.TYPE_ASCII)
    elif obj_type == 0x41:  # ASCII_INTERNED ('A')
        return PycString(PycObject.TYPE_ASCII_INTERNED)
    elif obj_type == 0x7A:  # SHORT_ASCII ('z')
        return PycString(PycObject.TYPE_SHORT_ASCII)
    elif obj_type == 0x5A:  # SHORT_ASCII_INTERNED ('Z')
        return PycString(PycObject.TYPE_SHORT_ASCII_INTERNED)
    elif obj_type == 0x06:  # TUPLE (Python 3.11)
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x28:  # TUPLE ('(')
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x29:  # SMALL_TUPLE (')')
        return PycSequence(PycObject.TYPE_SMALL_TUPLE)
    elif obj_type == 0xAB:  # TUPLE (Python 3.11+)
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0xA9:  # TUPLE (Python 3.11 alternate)
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x5B:  # LIST ('[')
        return PycSequence(PycObject.TYPE_LIST)
    elif obj_type == 0xDB:  # LIST (Python 3.11+)
        return PycSequence(PycObject.TYPE_LIST)
    elif obj_type == 0x7B:  # DICT ('{')
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0xFB:  # DICT (Python 3.11+)
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0x64:  # DICT ('d' in Python 3.11+)
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0x63:  # CODE ('c')
        return PycCode()
    elif obj_type == 0x3C:  # SET ('<')
        return PycSequence(PycObject.TYPE_SET)
    elif obj_type == 0xBC:  # SET (Python 3.11+)
        return PycSequence(PycObject.TYPE_SET)
    elif obj_type == 0x3E:  # FROZENSET ('>')
        return PycSequence(PycObject.TYPE_FROZENSET)
    elif obj_type == 0xBE:  # FROZENSET (Python 3.11+)
        return PycSequence(PycObject.TYPE_FROZENSET)
    elif obj_type == 0x72:  # OBREF ('r') - 但这个不应该到这里，因为我们在load_object中处理
        return PycObject(PycObject.TYPE_OBREF)
    elif obj_type == 0x6E:  # TYPE_CODE ('n') - Python 3.11+
        return PycCode()
    # Python 3.11 reference types (0x00-0x14)
    elif obj_type == 0x00:  # REF_NULL
        return PycObject(PycObject.TYPE_NULL)
    elif obj_type == 0x01:  # REF_FALSE
        return PycObject(PycObject.TYPE_FALSE)
    elif obj_type == 0x02:  # REF_TRUE
        return PycObject(PycObject.TYPE_TRUE)
    elif obj_type == 0x03:  # REF_STOPITERATION
        return PycObject(PycObject.TYPE_STOPITER)
    elif obj_type == 0x04:  # REF_TUPLE
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x05:  # REF_ELLIPSIS
        return PycObject(PycObject.TYPE_ELLIPSIS)
    elif obj_type == 0x06:  # REF_INT
        return PycNumeric(PycObject.TYPE_INT)
    elif obj_type == 0x07:  # REF_INT64
        return PycNumeric(PycObject.TYPE_INT64)
    elif obj_type == 0x08:  # REF_FLOAT
        return PycNumeric(PycObject.TYPE_FLOAT)
    elif obj_type == 0x09:  # REF_COMPLEX
        return PycNumeric(PycObject.TYPE_COMPLEX)
    elif obj_type == 0x0A:  # REF_LONG
        return PycNumeric(PycObject.TYPE_LONG)
    elif obj_type == 0x0B:  # REF_CODE
        return PycCode()
    elif obj_type == 0x0C:  # REF_UNICODE
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0x0D:  # REF_TUPLE2
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x0E:  # REF_LIST
        return PycSequence(PycObject.TYPE_LIST)
    elif obj_type == 0x0F:  # REF_DICT
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0x10:  # REF_SET
        return PycSequence(PycObject.TYPE_SET)
    elif obj_type == 0x11:  # REF_FROZENSET
        return PycSequence(PycObject.TYPE_FROZENSET)
    elif obj_type == 0x12:  # REF_BYTES
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x13:  # REF_STRING
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x16:  # REF_LONG alternate
        return PycNumeric(PycObject.TYPE_LONG)
    elif obj_type == 0x17:  # REF_TUPLE (alternate)
        return PycSequence(PycObject.TYPE_TUPLE)
    elif obj_type == 0x18:  # REF_INT64 alternate
        return PycNumeric(PycObject.TYPE_INT64)
    elif obj_type == 0x19:  # REF_FROZENSET
        return PycSequence(PycObject.TYPE_FROZENSET)
    elif obj_type == 0x1A:  # REF_COMPLEX alternate
        return PycNumeric(PycObject.TYPE_COMPLEX)
    elif obj_type == 0x1B:  # TYPE_UNKNOWN
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x1C:  # TYPE_BOOL
        return PycObject(PycObject.TYPE_TRUE)
    elif obj_type == 0x1D:  # TYPE_BOUND_METHOD
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x1F:  # TYPE_GENERATOR
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x20:  # TYPE_STR (unicode interned)
        return PycString(PycObject.TYPE_INTERNED)
    elif obj_type == 0x21:  # TYPE_STR (unicode short)
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0x23:  # TYPE_STR (short ASCII interned)
        return PycString(PycObject.TYPE_ASCII_INTERNED)
    elif obj_type == 0x24:  # TYPE_STR (short Unicode)
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0x26:  # TYPE_STR (bytes ref)
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x27:  # TYPE_STR (short bytes)
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x2A:  # TYPE_CODE (0x2A = '*')
        return PycCode()
    elif obj_type == 0x32:  # TYPE_INT (alternate)
        return PycNumeric(PycObject.TYPE_INT)
    elif obj_type == 0x36:  # TYPE_STR (UTF-8)
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0x40:  # TYPE_OBJECT
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x44:  # TYPE_DICT ('D')
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0x50:  # TYPE_TYPE
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x51:  # TYPE_SET
        return PycSequence(PycObject.TYPE_SET)
    elif obj_type == 0x57:  # TYPE_FROZENSET
        return PycSequence(PycObject.TYPE_FROZENSET)
    elif obj_type == 0x5D:  # TYPE_CELL
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x5F:  # TYPE_FUNC
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x60:  # TYPE_STR (base string)
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0x65:  # TYPE_ELLIPSIS ('e')
        return PycObject(PycObject.TYPE_ELLIPSIS)
    elif obj_type == 0x6A:  # TYPE_JUMPDEST
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x6D:  # TYPE_DICT ('d')
        return PycSequence(PycObject.TYPE_DICT)
    elif obj_type == 0x70:  # TYPE_LABEL
        return PycObject(PycObject.TYPE_UNKNOWN)
    elif obj_type == 0x7F:  # TYPE_QUALNAME
        return PycString(PycObject.TYPE_UNICODE)
    elif obj_type == 0xA6:  # TYPE_BYTES ref
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0xAB:  # TUPLE ref
        return PycSequence(PycObject.TYPE_TUPLE)
    # Python 3.11 additional types
    elif obj_type == 0xE7:  # FLOAT (Python 3.11+)
        return PycNumeric(PycObject.TYPE_FLOAT)
    elif obj_type == 0xE9:  # INT (Python 3.11+)
        return PycNumeric(PycObject.TYPE_INT)
    elif obj_type == 0xF3:  # BYTES (Python 3.11+)
        return PycString(PycObject.TYPE_STRING)
    elif obj_type == 0xDA:  # UNICODE (Python 3.11+)
        return PycString(PycObject.TYPE_UNICODE)
    else:
        print(f"DEBUG create_object_numeric: Unknown type 0x{obj_type:02X}")
        return None


def load_string(stream: PycData, module: 'PycModule', length: int) -> str:
    """加载字符串"""
    data = stream.get_buffer(length)
    if module.str_is_unicode():
        return data.decode('utf-8')
    else:
        return data.decode('latin-1')


def load_int(stream: PycData, module: 'PycModule') -> int:
    """加载整数"""
    return stream.get32()
