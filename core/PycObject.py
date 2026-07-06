#!/usr/bin/env python3
"""
PycObject.py - Python version of pyc_object.h
Python对象基类和引用计数系统

Original C++ header:
#ifndef _PYC_OBJECT_H
#define _PYC_OBJECT_H

#include <typeinfo>
"""

from typing import Any, Optional, Union, Dict, List
import weakref
import sys


class PycRef:
    """
    Python版本的智能指针类，对应C++的PycRef
    提供引用计数和类型安全的对象访问
    """
    
    def __init__(self, obj: Optional['PycObject'] = None):
        """初始化引用指针"""
        self._obj = obj
        if obj is not None:
            obj.add_ref()
    
    def __init__(self, obj: 'PycObject'):
        """从PycObject对象初始化"""
        self._obj = obj
        if obj is not None:
            obj.add_ref()
    
    def __copy__(self):
        """创建副本，增加引用计数"""
        if self._obj is not None:
            self._obj.add_ref()
        return PycRef(self._obj)
    
    def __deepcopy__(self, memo):
        """深度复制"""
        return self.__copy__()
    
    def __eq__(self, other) -> bool:
        """相等比较"""
        if isinstance(other, PycRef):
            return self._obj is other._obj
        return False
    
    def __ne__(self, other) -> bool:
        """不相等比较"""
        return not self.__eq__(other)
    
    def __str__(self) -> str:
        """字符串表示"""
        if self._obj is None:
            return "PycRef(None)"
        return f"PycRef({self._obj})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return self.__str__()
    
    def __bool__(self) -> bool:
        """布尔值测试"""
        return self._obj is not None
    
    def get(self) -> Optional['PycObject']:
        """获取内部对象"""
        return self._obj
    
    def try_cast(self, target_type) -> 'PycRef':
        """尝试类型转换"""
        if self._obj is None:
            return PycRef(None)
        
        # 在Python中，我们使用isinstance检查类型
        if isinstance(self._obj, target_type):
            return PycRef(self._obj)
        return PycRef(None)
    
    def cast(self, target_type) -> 'PycRef':
        """强制类型转换"""
        if self._obj is None:
            raise ValueError("Cannot cast null reference")
        
        if not isinstance(self._obj, target_type):
            raise TypeError(f"Cannot cast {type(self._obj).__name__} to {target_type.__name__}")
        
        return PycRef(self._obj)
    
    def is_identical(self, other) -> bool:
        """检查是否为同一对象"""
        if isinstance(other, PycRef):
            return self._obj is other._obj
        return False
    
    @property
    def type(self) -> int:
        """获取对象类型"""
        if self._obj is None:
            return PycObject.TYPE_NULL
        return self._obj.type()


class PycObject:
    """
    Python对象基类，对应C++的PycObject
    提供引用计数管理和基本对象功能
    """
    
    # Python Marshallers中的类型定义
    TYPE_NULL = ord('0')                    # Python 1.0 ->
    TYPE_NONE = ord('N')                   # Python 1.0 ->
    TYPE_FALSE = ord('F')                  # Python 2.3 ->
    TYPE_TRUE = ord('T')                   # Python 2.3 ->
    TYPE_STOPITER = ord('S')               # Python 2.2 ->
    TYPE_ELLIPSIS = ord('.')               # Python 1.4 ->
    TYPE_INT = ord('i')                    # Python 1.0 ->
    TYPE_INT64 = ord('I')                  # Python 1.5 - 3.3
    TYPE_FLOAT = ord('f')                  # Python 1.0 ->
    TYPE_BINARY_FLOAT = ord('g')           # Python 2.5 ->
    TYPE_COMPLEX = ord('x')                # Python 1.4 ->
    TYPE_BINARY_COMPLEX = ord('y')         # Python 2.5 ->
    TYPE_LONG = ord('l')                  # Python 1.0 ->
    TYPE_STRING = ord('s')                 # Python 1.0 ->
    TYPE_INTERNED = ord('t')               # Python 2.4 - 2.7, 3.4 ->
    TYPE_STRINGREF = ord('R')              # Python 2.4 - 2.7
    TYPE_OBREF = ord('r')                 # Python 3.4 ->
    TYPE_TUPLE = ord('(')                 # Python 1.0 ->
    TYPE_LIST = ord('[')                  # Python 1.0 ->
    TYPE_DICT = ord('{')                  # Python 1.0 ->
    TYPE_CODE = ord('c')                  # Python 1.3 ->
    TYPE_CODE2 = ord('C')                 # Python 1.0 - 1.2
    TYPE_UNICODE = ord('u')              # Python 1.6 ->
    TYPE_UNKNOWN = ord('?')               # Python 1.0 ->
    TYPE_SET = ord('<')                   # Python 2.5 ->
    TYPE_FROZENSET = ord('>')            # Python 2.5 ->
    TYPE_ASCII = ord('a')                # Python 3.4 ->
    TYPE_ASCII_INTERNED = ord('A')       # Python 3.4 ->
    TYPE_SMALL_TUPLE = ord(')')          # Python 3.4 ->
    TYPE_SHORT_ASCII = ord('z')          # Python 3.4 ->
    TYPE_SHORT_ASCII_INTERNED = ord('Z') # Python 3.4 ->
    
    def __init__(self, type_: int = TYPE_UNKNOWN):
        """初始化Python对象"""
        self._refs = 0
        self._type = type_
    
    @property
    def type(self) -> int:
        """获取对象类型"""
        return self._type
    
    def is_equal(self, other: 'PycObject') -> bool:
        """检查对象是否相等"""
        if isinstance(other, PycRef):
            return self is other.get()
        return self is other
    
    def load(self, stream: Any, module: Any) -> None:
        """从数据流加载对象（子类可重写）"""
        pass
    
    def add_ref(self) -> None:
        """增加引用计数"""
        self._refs += 1
    
    def del_ref(self) -> None:
        """减少引用计数，必要时自动删除"""
        self._refs -= 1
        if self._refs <= 0:
            # 在Python中，我们依赖垃圾回收器
            # 但我们可以调用析构函数
            if hasattr(self, '__del__'):
                try:
                    self.__del__()
                except:
                    pass
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(type={self._type})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return self.__str__()


# 单例对象的全局实例
class SingletonObjects:
    """管理Python单例对象的容器"""
    
    def __init__(self):
        self._objects: Dict[int, PycObject] = {}
    
    def get_object(self, type_: int) -> PycRef:
        """获取指定类型的单例对象"""
        if type_ not in self._objects:
            # 创建对应的单例对象
            if type_ == PycObject.TYPE_NONE:
                self._objects[type_] = PycNone()
            elif type_ == PycObject.TYPE_ELLIPSIS:
                self._objects[type_] = PycEllipsis()
            elif type_ == PycObject.TYPE_STOPITER:
                self._objects[type_] = PycStopIteration()
            elif type_ == PycObject.TYPE_FALSE:
                self._objects[type_] = PycFalse()
            elif type_ == PycObject.TYPE_TRUE:
                self._objects[type_] = PycTrue()
            else:
                # 创建通用单例
                self._objects[type_] = PycObject(type_)
        
        return PycRef(self._objects[type_])


# 单例对象类
class PycNone(PycObject):
    """None对象"""
    
    def __init__(self):
        super().__init__(PycObject.TYPE_NONE)
    
    def __str__(self) -> str:
        return "None"


class PycEllipsis(PycObject):
    """Ellipsis对象"""
    
    def __init__(self):
        super().__init__(PycObject.TYPE_ELLIPSIS)
    
    def __str__(self) -> str:
        return "..."


class PycStopIteration(PycObject):
    """StopIteration对象"""
    
    def __init__(self):
        super().__init__(PycObject.TYPE_STOPITER)
    
    def __str__(self) -> str:
        return "StopIteration"


class PycFalse(PycObject):
    """False对象"""
    
    def __init__(self):
        super().__init__(PycObject.TYPE_FALSE)
    
    def __str__(self) -> str:
        return "False"


class PycTrue(PycObject):
    """True对象"""
    
    def __init__(self):
        super().__init__(PycObject.TYPE_TRUE)
    
    def __str__(self) -> str:
        return "True"


# 全局单例对象实例
_SINGLETONS = SingletonObjects()

# 全局单例对象引用（与C++兼容）
Pyc_None = _SINGLETONS.get_object(PycObject.TYPE_NONE)
Pyc_Ellipsis = _SINGLETONS.get_object(PycObject.TYPE_ELLIPSIS)
Pyc_StopIteration = _SINGLETONS.get_object(PycObject.TYPE_STOPITER)
Pyc_False = _SINGLETONS.get_object(PycObject.TYPE_FALSE)
Pyc_True = _SINGLETONS.get_object(PycObject.TYPE_TRUE)


# 工具函数
def create_object(type_: int) -> PycRef:
    """创建指定类型的对象"""
    # 这里应该根据类型创建具体的对象实例
    # 实际实现应该在子类中完成
    return PycRef(PycObject(type_))


def load_object(stream: Any, module: Any) -> PycRef:
    """从数据流加载对象"""
    # 这里需要从数据流读取类型标识符
    # 然后创建相应的对象
    # 实际实现在data.py中完成
    raise NotImplementedError("load_object should be implemented in data.py")


# 类型检查工具函数
def is_integer_type(type_: int) -> bool:
    """检查是否为整数类型"""
    return type_ in (PycObject.TYPE_INT, PycObject.TYPE_INT64, PycObject.TYPE_LONG)


def is_float_type(type_: int) -> bool:
    """检查是否为浮点类型"""
    return type_ in (PycObject.TYPE_FLOAT, PycObject.TYPE_BINARY_FLOAT)


def is_complex_type(type_: int) -> bool:
    """检查是否为复数类型"""
    return type_ in (PycObject.TYPE_COMPLEX, PycObject.TYPE_BINARY_COMPLEX)


def is_string_type(type_: int) -> bool:
    """检查是否为字符串类型"""
    return type_ in (
        PycObject.TYPE_STRING, PycObject.TYPE_INTERNED, PycObject.TYPE_STRINGREF,
        PycObject.TYPE_OBREF, PycObject.TYPE_UNICODE, PycObject.TYPE_ASCII,
        PycObject.TYPE_ASCII_INTERNED, PycObject.TYPE_SHORT_ASCII,
        PycObject.TYPE_SHORT_ASCII_INTERNED
    )


def is_sequence_type(type_: int) -> bool:
    """检查是否为序列类型"""
    return type_ in (PycObject.TYPE_TUPLE, PycObject.TYPE_LIST, PycObject.TYPE_SMALL_TUPLE)


def is_mapping_type(type_: int) -> bool:
    """检查是否为映射类型"""
    return type_ == PycObject.TYPE_DICT


def is_set_type(type_: int) -> bool:
    """检查是否为集合类型"""
    return type_ in (PycObject.TYPE_SET, PycObject.TYPE_FROZENSET)


def is_code_type(type_: int) -> bool:
    """检查是否为代码对象类型"""
    return type_ in (PycObject.TYPE_CODE, PycObject.TYPE_CODE2)


def get_type_name(type_: int) -> str:
    """获取类型的字符串名称"""
    type_names = {
        PycObject.TYPE_NULL: "NULL",
        PycObject.TYPE_NONE: "None",
        PycObject.TYPE_FALSE: "False",
        PycObject.TYPE_TRUE: "True",
        PycObject.TYPE_STOPITER: "StopIteration",
        PycObject.TYPE_ELLIPSIS: "Ellipsis",
        PycObject.TYPE_INT: "int",
        PycObject.TYPE_INT64: "int64",
        PycObject.TYPE_FLOAT: "float",
        PycObject.TYPE_BINARY_FLOAT: "binary_float",
        PycObject.TYPE_COMPLEX: "complex",
        PycObject.TYPE_BINARY_COMPLEX: "binary_complex",
        PycObject.TYPE_LONG: "long",
        PycObject.TYPE_STRING: "string",
        PycObject.TYPE_INTERNED: "interned",
        PycObject.TYPE_STRINGREF: "stringref",
        PycObject.TYPE_OBREF: "obreference",
        PycObject.TYPE_TUPLE: "tuple",
        PycObject.TYPE_LIST: "list",
        PycObject.TYPE_DICT: "dict",
        PycObject.TYPE_CODE: "code",
        PycObject.TYPE_CODE2: "code2",
        PycObject.TYPE_UNICODE: "unicode",
        PycObject.TYPE_UNKNOWN: "unknown",
        PycObject.TYPE_SET: "set",
        PycObject.TYPE_FROZENSET: "frozenset",
        PycObject.TYPE_ASCII: "ascii",
        PycObject.TYPE_ASCII_INTERNED: "ascii_interned",
        PycObject.TYPE_SMALL_TUPLE: "small_tuple",
        PycObject.TYPE_SHORT_ASCII: "short_ascii",
        PycObject.TYPE_SHORT_ASCII_INTERNED: "short_ascii_interned",
    }
    return type_names.get(type_, f"unknown({type_})")


if __name__ == "__main__":
    # 简单测试
    print("PycObject.py - Python版本的Python对象基类")
    print(f"单例对象测试:")
    print(f"Pyc_None: {Pyc_None}")
    print(f"Pyc_Ellipsis: {Pyc_Ellipsis}")
    print(f"Pyc_True: {Pyc_True}")
    print(f"Pyc_False: {Pyc_False}")
    
    print(f"\n类型测试:")
    print(f"TYPE_INT 是整数类型: {is_integer_type(PycObject.TYPE_INT)}")
    print(f"TYPE_STRING 是字符串类型: {is_string_type(PycObject.TYPE_STRING)}")
    print(f"TYPE_TUPLE 是序列类型: {is_sequence_type(PycObject.TYPE_TUPLE)}")
    
    print(f"\n类型名称:")
    print(f"TYPE_INT: {get_type_name(PycObject.TYPE_INT)}")
    print(f"TYPE_STRING: {get_type_name(PycObject.TYPE_STRING)}")