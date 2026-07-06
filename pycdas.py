#!/usr/bin/env python3
"""
Python版本的PYC反汇编器 (pycdas.py)
对应C++版本的pycdas.cpp
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, TextIO

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.pyc_loader_v2 import load_pyc_file_v2
from bytecode.pyc_disasm import PycDisassembler


class PycDisas:
    """PYC反汇编器主类"""

    def __init__(self):
        self.module = None
        self.disassembler = None

    def load_file(self, filepath: str, marshalled: bool = False, 
                 version: Optional[str] = None) -> bool:
        """加载PYC文件"""
        try:
            if marshalled:
                if not version:
                    print("Error: Opening raw code objects requires a version to be specified", 
                          file=sys.stderr)
                    return False
                
                try:
                    major, minor = map(int, version.split('.'))
                    # 使用load_pyc_file_v2处理marshalled代码
                    self.module = load_pyc_file_v2(filepath)
                    if self.module:
                        self.module.set_version_from_string(version)
                    return True
                except ValueError:
                    print("Error: Unable to parse version string (use format x.y)", 
                          file=sys.stderr)
                    return False
            else:
                self.module = load_pyc_file_v2(filepath)
                return self.module is not None
            
        except Exception as e:
            print(f"Error loading file {filepath}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def disassemble(self, output: TextIO, show_extra: bool = False, 
                  show_caches: bool = False) -> None:
        """反汇编PYC文件"""
        if not self.module or not self.module.code:
            print("Error: Invalid module", file=sys.stderr)
            return

        try:
            code_obj = self.module.code.get() if self.module.code else None
            if not code_obj:
                print("Error: No code object found", file=sys.stderr)
                return
            
            bytecode = code_obj.code.get()._value if code_obj.code else b''
            version = (self.module.major_version, self.module.minor_version)
            
            self.disassembler = PycDisassembler(bytecode, self.module, version, code_obj)
            
            if hasattr(self.disassembler, 'disassemble_to_text'):
                output.write(self.disassembler.disassemble_to_text())
            else:
                instructions = self.disassembler.disassemble()
                for instr in instructions:
                    line = f"{instr['offset']:4d}: {instr['opcode_name']}"
                    if instr.get('has_arg', False):
                        line += f" ({instr['operand']})"
                    output.write(line + '\n')
                    
        except Exception as e:
            print(f"Error disassembling: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


def print_flag_names(flags: int) -> str:
    """打印代码对象标志"""
    flag_names = [
        "CO_OPTIMIZED", "CO_NEWLOCALS", "CO_VARARGS", "CO_VARKEYWORDS",
        "CO_NESTED", "CO_GENERATOR", "CO_NOFREE", "CO_COROUTINE",
        "CO_ITERABLE_COROUTINE", "CO_ASYNC_GENERATOR", "<0x400>", "<0x800>",
        "CO_GENERATOR_ALLOWED", "<0x2000>", "<0x4000>", "<0x8000>",
        "<0x10000>", "CO_FUTURE_DIVISION", "CO_FUTURE_ABSOLUTE_IMPORT", 
        "CO_FUTURE_WITH_STATEMENT",
        "CO_FUTURE_PRINT_FUNCTION", "CO_FUTURE_UNICODE_LITERALS", 
        "CO_FUTURE_BARRY_AS_BDFL",
        "CO_FUTURE_GENERATOR_STOP",
        "CO_FUTURE_ANNOTATIONS", "CO_NO_MONITORING_EVENTS", "<0x4000000>", 
        "<0x8000000>",
        "<0x10000000>", "<0x20000000>", "<0x40000000>", "<0x80000000>"
    ]
    
    if flags == 0:
        return ""
    
    result = []
    for i, name in enumerate(flag_names):
        if flags & (1 << i):
            result.append(name)
    
    return f" ({' | '.join(result)})" if result else ""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Python PYC Disassembler - 反汇编Python字节码文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pyc                    # 反汇编到标准输出
  %(prog)s -o output.txt input.pyc      # 反汇编到文件
  %(prog)s -c -v 3.11 code.pyc        # 反汇编编译的代码对象
  %(prog)s --pycode-extra input.pyc     # 显示额外的PyCode字段
        """
    )
    
    parser.add_argument('input', nargs='?', help='输入的.pyc文件路径')
    parser.add_argument('-o', '--output', metavar='filename',
                      help='写入输出到指定文件（默认：标准输出）')
    parser.add_argument('-c', '--compiled', action='store_true',
                      help='指定加载编译的代码对象（需要设置版本）')
    parser.add_argument('-v', '--version', metavar='x.y',
                      help='为编译的代码对象指定Python版本')
    parser.add_argument('--pycode-extra', action='store_true',
                      help='在PyCode对象转储中显示额外字段')
    parser.add_argument('--show-caches', action='store_true',
                      help='在Python 3.11+反汇编中不抑制CACHE指令')
    
    args = parser.parse_args()
    
    if not args.input:
        parser.print_help()
        return 1
    
    # 设置输出
    if args.output:
        try:
            output = open(args.output, 'w', encoding='utf-8')
        except IOError as e:
            print(f"Error opening file '{args.output}' for writing: {e}", 
                  file=sys.stderr)
            return 1
    else:
        output = sys.stdout
    
    try:
        # 创建反汇编器
        disas = PycDisas()
        
        # 加载文件
        if not disas.load_file(args.input, args.compiled, args.version):
            return 1
        
        # 显示文件信息
        dispname = os.path.basename(args.input)
        module = disas.module
        unicode_suffix = " -U" if (module.major_version < 3 and 
                                   module.is_unicode) else ""
        output.write(f"{dispname} (Python {module.major_version}."
                   f"{module.minor_version}{unicode_suffix})\n")
        
        # 反汇编
        disas.disassemble(output, args.pycode_extra, args.show_caches)
        
        return 0
        
    except Exception as e:
        print(f"Error disassembling {args.input}: {e}", file=sys.stderr)
        return 1
    finally:
        if args.output:
            output.close()


if __name__ == '__main__':
    sys.exit(main())
