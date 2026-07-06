#!/usr/bin/env python3
"""
PYC文件解析模块
支持使用Python内置marshal进行解析
"""

import struct
import marshal
from typing import Optional
from .pyc_stream import PycFile, PycData, PycRef
from .pyc_objects import PycModule, PycCode, PycString, PycSequence, PycNumeric, PycObject, PycBytes


def marshal_to_pyc_obj(obj, module: PycModule) -> Optional[PycRef]:
    """将marshal对象转换为PycObject"""
    from .pyc_stream import PycRef as Ref
    
    if obj is None:
        return Ref(PycObject(PycObject.TYPE_NONE))
    elif isinstance(obj, bool):
        return Ref(PycObject(PycObject.TYPE_TRUE if obj else PycObject.TYPE_FALSE))
    elif isinstance(obj, int):
        result = PycNumeric(PycObject.TYPE_INT)
        result._value = obj
        return Ref(result)
    elif isinstance(obj, float):
        result = PycNumeric(PycObject.TYPE_FLOAT)
        result._value = obj
        return Ref(result)
    elif isinstance(obj, complex):
        result = PycNumeric(PycObject.TYPE_COMPLEX)
        result._value = obj
        return Ref(result)
    elif isinstance(obj, str):
        result = PycString(PycObject.TYPE_UNICODE)
        result._value = obj
        return Ref(result)
    elif isinstance(obj, bytes):
        # [关键修复] 使用PycBytes类存储字节串，而不是解码为字符串
        result = PycBytes(PycObject.TYPE_STRING)
        result._value = obj
        return Ref(result)
    elif isinstance(obj, tuple):
        result = PycSequence(PycObject.TYPE_TUPLE)
        result._values = [marshal_to_pyc_obj(item, module) for item in obj]
        return Ref(result)
    elif isinstance(obj, list):
        result = PycSequence(PycObject.TYPE_LIST)
        result._values = [marshal_to_pyc_obj(item, module) for item in obj]
        return Ref(result)
    elif isinstance(obj, dict):
        result = PycSequence(PycObject.TYPE_DICT)
        result._values = []
        for k, v in obj.items():
            result._values.append((marshal_to_pyc_obj(k, module), marshal_to_pyc_obj(v, module)))
        return Ref(result)
    elif isinstance(obj, frozenset):
        # 处理frozenset类型
        result = PycSequence(PycObject.TYPE_FROZENSET)
        result._values = [marshal_to_pyc_obj(item, module) for item in obj]
        return Ref(result)
    elif hasattr(obj, 'co_argcount') and hasattr(obj, 'co_code'):
        pyc_code = PycCode()
        pyc_code.arg_count = obj.co_argcount
        pyc_code.num_locals = obj.co_nlocals
        pyc_code.stack_size = obj.co_stacksize
        pyc_code.flags = obj.co_flags
        pyc_code.pos_only_arg_count = 0
        pyc_code.kw_only_arg_count = 0
        
        # [关键修复] 使用 PycBytes 类存储字节码，避免解码为字符串
        pyc_code.code = Ref(PycBytes(PycObject.TYPE_STRING))
        pyc_code.code.get()._value = obj.co_code
        
        pyc_code.consts = Ref(PycSequence(PycObject.TYPE_TUPLE))
        for c in obj.co_consts:
            pyc_code.consts.get()._values.append(marshal_to_pyc_obj(c, module))
        
        pyc_code.names = Ref(PycSequence(PycObject.TYPE_TUPLE))
        for n in obj.co_names:
            s = PycString(PycObject.TYPE_UNICODE)
            s._value = n
            pyc_code.names.get()._values.append(Ref(s))
        
        pyc_code.local_names = Ref(PycSequence(PycObject.TYPE_TUPLE))
        for v in obj.co_varnames:
            s = PycString(PycObject.TYPE_UNICODE)
            s._value = v
            pyc_code.local_names.get()._values.append(Ref(s))
        
        pyc_code.free_vars = Ref(PycSequence(PycObject.TYPE_TUPLE))
        for v in obj.co_freevars:
            s = PycString(PycObject.TYPE_UNICODE)
            s._value = v
            pyc_code.free_vars.get()._values.append(Ref(s))
        
        pyc_code.cell_vars = Ref(PycSequence(PycObject.TYPE_TUPLE))
        for v in obj.co_cellvars:
            s = PycString(PycObject.TYPE_UNICODE)
            s._value = v
            pyc_code.cell_vars.get()._values.append(Ref(s))
        
        pyc_code.file_name = Ref(PycString(PycObject.TYPE_UNICODE))
        pyc_code.file_name.get()._value = obj.co_filename
        
        pyc_code.name = Ref(PycString(PycObject.TYPE_UNICODE))
        pyc_code.name.get()._value = obj.co_name
        
        if hasattr(obj, 'co_qualname'):
            pyc_code.qual_name = Ref(PycString(PycObject.TYPE_UNICODE))
            pyc_code.qual_name.get()._value = obj.co_qualname
        else:
            pyc_code.qual_name = Ref(PycString(PycObject.TYPE_UNICODE))
            pyc_code.qual_name.get()._value = obj.co_name
        
        pyc_code.first_line = obj.co_firstlineno
        
        # [关键修复] 获取行号表（Python 3.11+使用co_linetable，旧版本使用co_lnotab）
        if hasattr(obj, 'co_linetable'):
            lnotab = obj.co_linetable
        elif hasattr(obj, 'co_lnotab'):
            lnotab = obj.co_lnotab
        else:
            lnotab = b''
        
        # [关键修复] 使用PycBytes存储行号表，保留原始字节数据
        pyc_code.ln_table = Ref(PycBytes(PycObject.TYPE_STRING))
        if isinstance(lnotab, bytes):
            pyc_code.ln_table.get()._value = lnotab
        else:
            pyc_code.ln_table.get()._value = lnotab.encode('latin-1') if isinstance(lnotab, str) else b''
        
        if hasattr(obj, 'co_exceptiontable'):
            except_data = obj.co_exceptiontable
            # [关键修复] 使用 PycBytes 存储异常表数据，保留二进制格式
            pyc_code.except_table = Ref(PycBytes(PycObject.TYPE_STRING))
            if isinstance(except_data, bytes):
                pyc_code.except_table.get()._value = except_data
            else:
                pyc_code.except_table.get()._value = except_data.encode('latin-1') if isinstance(except_data, str) else b''
        else:
            pyc_code.except_table = Ref(PycBytes(PycObject.TYPE_STRING))
            pyc_code.except_table.get()._value = b''
        
        return Ref(pyc_code)
    else:
        print(f"DEBUG: Unknown marshal type {type(obj)}")
        return None


def load_pyc_file_v2(filepath: str) -> Optional[PycModule]:
    """使用marshal加载PYC文件"""
    try:
        with open(filepath, 'rb') as f:
            stream = PycFile(filepath)
            stream.open()
            
            module = PycModule()
            
            magic = stream.get32()
            module.set_version(magic)
            
            if not module.is_valid():
                print(f"Unsupported magic number: 0x{magic:08X}")
                return None
            
            # Python 3.11+ header format:
            # magic (4) + null (4) + size (8) = 16 bytes total
            if module.ver_compare(3, 11) >= 0:
                # Skip null padding (4 bytes)
                stream.get32()
                # Skip size field (8 bytes)
                stream.get64()
            elif module.ver_compare(3, 7) >= 0:
                flags = stream.get32()
                
                if flags & 0x8:
                    stream.get32()
                    stream.get32()
                else:
                    stream.get32()
                    if module.ver_compare(3, 3) >= 0:
                        stream.get32()
                    else:
                        stream.get16()
            else:
                if module.ver_compare(3, 3) >= 0:
                    stream.get32()
                    stream.get32()
                elif module.ver_compare(2, 3) >= 0:
                    stream.get32()
                    stream.get16()
                else:
                    stream.get32()
            
            data = stream.read_all()
            code_obj = marshal.loads(data)
            
            module.code = marshal_to_pyc_obj(code_obj, module)
            
            stream.close()
            return module
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else r'd:\Desktop\ptrade相关\new_test_file.pyc'
    module = load_pyc_file_v2(filepath)
    if module and module.code and module.code.get():
        code = module.code.get()
        print('Loaded successfully!')
        print('arg_count:', code.arg_count)
        print('nlocals:', code.num_locals)
        print('stack_size:', code.stack_size)
        print('flags: 0x{:08X}'.format(code.flags))
        
        if code.consts and code.consts.get():
            consts = code.consts.get()
            if hasattr(consts, '_values'):
                print('\nConsts ({})'.format(len(consts._values)))
                for i, c in enumerate(consts._values[:10]):
                    if c and c.get():
                        obj = c.get()
                        print('  [{}]: {}'.format(i, type(obj).__name__))
        
        if code.names and code.names.get():
            names = code.names.get()
            if hasattr(names, '_values'):
                print('\nNames ({})'.format(len(names._values)))
                for i, n in enumerate(names._values[:15]):
                    if n and n.get():
                        obj = n.get()
                        if isinstance(obj, PycString):
                            print('  [{}]: {}'.format(i, obj._value))
