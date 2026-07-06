"""
Python 3.11+ 异常表解析模块

异常表格式（参考 Python 源码）:
- 每个条目是变长编码
- 第一个字节：类型 + 标志
- 后续字节：start, end, target 的变长编码
"""

from typing import List, Optional, NamedTuple
from enum import IntEnum


class ExceptionHandlerType(IntEnum):
    """异常处理器类型"""
    TRY_EXCEPT = 0  # 常规 try-except
    TRY_FINALLY = 1  # try-finally
    WITH = 2  # with 语句
    ASYNC_WITH = 3  # async with 语句


class ExceptionTableEntry(NamedTuple):
    """异常表条目"""
    start: int  # 受保护代码的起始偏移
    end: int    # 受保护代码的结束偏移
    target: int  # 异常处理代码的起始偏移
    depth: int   # 异常处理深度
    lasti: bool  # 是否是 lasti 条目
    type: int    # 处理器类型


class ExceptionTableParser:
    """异常表解析器 - 使用 Python 内置的 _parse_exception_table"""
    
    def __init__(self, data: bytes):
        self.data = data
        self.entries: List[ExceptionTableEntry] = []
    
    def parse(self) -> List[ExceptionTableEntry]:
        """解析异常表"""
        if not self.data:
            return []
        
        self.entries = []
        
        # 使用 Python 的 dis 模块来解析
        try:
            from dis import _parse_exception_table
            import types
            
            # 创建一个临时代码对象来解析异常表
            # Python 3.11+ 的 CodeType 参数: 
            # (argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags,
            #  codestring, constants, names, varnames, filename, name, qualname,
            #  firstlineno, linetable, exceptiontable, freevars=(), cellvars=())
            code = types.CodeType(
                0, 0, 0, 0, 0, 0,
                b'', (), (), (),
                '<generated>', '<generated>', '<generated>',
                0, b'', self.data,
                (), ()
            )
            
            py_entries = _parse_exception_table(code)
            
            for entry in py_entries:
                self.entries.append(ExceptionTableEntry(
                    start=entry.start,
                    end=entry.end,
                    target=entry.target,
                    depth=entry.depth,
                    lasti=entry.lasti,
                    type=0
                ))
            
            return self.entries
        except Exception as e:
            # 如果失败，返回空列表
            print(f"[WARN] 异常表解析失败: {e}")
            return []


def parse_exception_table(data: bytes) -> List[ExceptionTableEntry]:
    """解析异常表的便捷函数"""
    parser = ExceptionTableParser(data)
    return parser.parse()


# 测试代码
if __name__ == "__main__":
    import marshal
    
    # 测试用例
    test_code = """
try:
    x = 1 / 0
except ZeroDivisionError:
    print('Error')
"""
    
    # 编译并获取异常表
    compiled = compile(test_code, '<test>', 'exec')
    func_code = compiled.co_consts[0]
    
    if hasattr(func_code, 'co_exceptiontable'):
        exc_table = func_code.co_exceptiontable
        print(f"Exception table: {exc_table.hex()}")
        
        parser = ExceptionTableParser(exc_table)
        entries = parser.parse()
        
        print(f"\nParsed {len(entries)} entries:")
        for i, entry in enumerate(entries):
            print(f"  Entry {i}: start={entry.start}, end={entry.end}, target={entry.target}, "
                  f"depth={entry.depth}, lasti={entry.lasti}, type={entry.type}")
