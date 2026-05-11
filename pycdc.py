#!/usr/bin/env python3
"""
Python版本的PYC反编译器 (pycdc.py)
对应C++版本的pycdc.cpp
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
from core.control_flow import ControlFlowAnalyzer
from bytecode.pyc_disasm import PycDisassembler


class PycDecompiler:
    """PYC反编译器主类"""

    def __init__(self):
        self.module = None
        self.code_obj = None
        self.disassembler = None
        self.control_flow = None

    def load_file(self, filepath: str, marshalled: bool = False, 
                 version: Optional[str] = None) -> bool:
        """加载PYC文件"""
        try:
            self.module = load_pyc_file_v2(filepath)
            
            if not self.module:
                print(f"Error: Failed to load {filepath}", file=sys.stderr)
                return False
            
            if marshalled and version:
                self.module.set_version_from_string(version)
            
            return True
            
        except Exception as e:
            print(f"Error loading file {filepath}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def decompile(self, output: TextIO, use_cfg: bool = False,
                  cfg_hybrid: bool = False, use_region: bool = False,
                  verbose: bool = False) -> bool:
        """反编译PYC文件"""
        if not self.module or not self.module.code:
            print("Error: Invalid module", file=sys.stderr)
            return False

        try:
            # [修复] 处理 module.code 可能是 PycCode 或 PycRef 的情况
            if hasattr(self.module.code, 'get'):
                self.code_obj = self.module.code.get()
            else:
                self.code_obj = self.module.code

            if not self.code_obj:
                print("Error: No code object found", file=sys.stderr)
                return False

            if use_region:
                try:
                    import types as _types

                    if hasattr(self.code_obj, 'to_python_code'):
                        actual_code = self.code_obj.to_python_code()
                    elif isinstance(self.code_obj, _types.CodeType):
                        actual_code = self.code_obj
                    else:
                        print("Error: Cannot convert code object to CodeType", file=sys.stderr)
                        return False

                    from core.cfg import build_cfg
                    from core.cfg.region_ast_generator import RegionASTGenerator
                    from core.cfg.ast_converter import CFGASTConverter
                    from core.cfg.code_generator import CFGCodeGenerator

                    cfg = build_cfg(actual_code)
                    gen = RegionASTGenerator(cfg, top_level_code=actual_code if actual_code.co_name == '<module>' else None)
                    ast_dict = gen.generate()
                    converter = CFGASTConverter()
                    py_ast = converter.convert(ast_dict)
                    code_gen = CFGCodeGenerator()
                    source = code_gen.generate(py_ast)

                    if source is not None:
                        try:
                            if source:
                                compile(source, '<decompiled>', 'exec')
                            output.write(source)
                            output.flush()
                            return True
                        except SyntaxError as e:
                            if verbose:
                                print(f"Warning: Region-based code has syntax error: {e}", file=sys.stderr)
                            output.write(source)
                            output.flush()
                            return True
                    else:
                        print("Error: Region-based decompilation failed", file=sys.stderr)
                        return False

                except Exception as e:
                    if verbose:
                        import traceback as tb
                        tb.print_exc()
                    print(f"Error: Region-based decompilation exception: {e}", file=sys.stderr)
                    return False

            # [CFG完整实现] 优先使用新的CFG统一生成器
            if use_cfg or cfg_hybrid:
                try:
                    from parsers.unified_generator import UnifiedASTGenerator
                    import types

                    generator = UnifiedASTGenerator(verbose=verbose, use_cfg=True)

                    # 辅助函数：从PycCode递归创建Python CodeType对象
                    def pyc_to_code(pyc_code, py_version):
                        """将PycCode对象转换为Python CodeType对象"""
                        # 获取字节码
                        bytecode = b''
                        if hasattr(pyc_code, 'code') and pyc_code.code:
                            code_obj = pyc_code.code.get()
                            if hasattr(code_obj, '_value'):
                                bytecode = code_obj._value
                            elif hasattr(code_obj, 'value'):
                                bytecode = code_obj.value
                        
                        # 递归提取常量（处理嵌套的code对象）
                        co_consts = []
                        if hasattr(pyc_code, 'consts') and pyc_code.consts:
                            consts_obj = pyc_code.consts.get()
                            if consts_obj:
                                # PycSequence使用_values存储项目
                                items = getattr(consts_obj, '_values', getattr(consts_obj, 'items', []))
                                for item in items:
                                    const_val = item.get() if hasattr(item, 'get') else item
                                    if const_val is None:
                                        co_consts.append(None)
                                    elif hasattr(const_val, 'code'):  # 嵌套的PycCode
                                        # 递归转换嵌套code对象
                                        nested_code = pyc_to_code(const_val, py_version)
                                        co_consts.append(nested_code)
                                    elif hasattr(const_val, '_type'):
                                        # [关键修复] 处理 PycObject 类型的特殊值（True, False, None）
                                        # _type 可能是字符串 'F' 或整数 ord('F')=70
                                        type_val = const_val._type
                                        if type_val == 'F' or type_val == ord('F'):  # TYPE_FALSE
                                            co_consts.append(False)
                                        elif type_val == 'T' or type_val == ord('T'):  # TYPE_TRUE
                                            co_consts.append(True)
                                        elif type_val == 'N' or type_val == ord('N'):  # TYPE_NONE
                                            co_consts.append(None)
                                        elif const_val.__class__.__name__ in ('PycString', 'PycUnicode'):
                                            # [关键修复] 处理PycString（字符串）
                                            if hasattr(const_val, 'value'):
                                                co_consts.append(const_val.value)
                                            else:
                                                co_consts.append('')
                                        elif const_val.__class__.__name__ == 'PycSequence':
                                            # [关键修复] 处理PycSequence（列表、元组、字典等）
                                            # 递归转换序列中的元素
                                            seq_values = []
                                            if hasattr(const_val, '_values'):
                                                for item in const_val._values:
                                                    item_val = item.get() if hasattr(item, 'get') else item
                                                    if item_val is None:
                                                        seq_values.append(None)
                                                    elif hasattr(item_val, '_type'):
                                                        # [关键修复] 处理PycObject类型的特殊值（True, False, None）
                                                        type_val = item_val._type
                                                        if type_val == 'F' or type_val == ord('F'):  # TYPE_FALSE
                                                            seq_values.append(False)
                                                        elif type_val == 'T' or type_val == ord('T'):  # TYPE_TRUE
                                                            seq_values.append(True)
                                                        elif type_val == 'N' or type_val == ord('N'):  # TYPE_NONE
                                                            seq_values.append(None)
                                                        elif hasattr(item_val, 'value'):
                                                            seq_values.append(item_val.value)
                                                        else:
                                                            seq_values.append(str(item_val))
                                                    elif hasattr(item_val, 'value'):
                                                        seq_values.append(item_val.value)
                                                    elif hasattr(item_val, 'code'):
                                                        # 嵌套code对象
                                                        nested = pyc_to_code(item_val, py_version)
                                                        seq_values.append(nested)
                                                    elif isinstance(item_val, tuple) and len(item_val) == 2:
                                                        # 字典的键值对 (key, val)
                                                        key, val = item_val
                                                        key_obj = key.get() if hasattr(key, 'get') else key
                                                        val_obj = val.get() if hasattr(val, 'get') else val
                                                        
                                                        key_value = None
                                                        val_value = None
                                                        
                                                        if key_obj and hasattr(key_obj, 'value'):
                                                            key_value = key_obj.value
                                                        if val_obj and hasattr(val_obj, 'value'):
                                                            val_value = val_obj.value
                                                        
                                                        seq_values.append((key_value, val_value))
                                                    else:
                                                        seq_values.append(str(item_val))
                                            # 根据类型创建Python对象
                                            if const_val._type == '{':
                                                # 字典
                                                dict_values = {}
                                                for item in seq_values:
                                                    if isinstance(item, tuple) and len(item) == 2:
                                                        dict_values[item[0]] = item[1]
                                                co_consts.append(dict_values)
                                            elif const_val._type == '(':
                                                co_consts.append(tuple(seq_values))
                                            elif const_val._type == '[':
                                                co_consts.append(seq_values)
                                            elif const_val._type == '<':
                                                co_consts.append(set(seq_values))
                                            elif const_val._type == '>':
                                                co_consts.append(frozenset(seq_values))
                                            else:
                                                co_consts.append(tuple(seq_values))
                                        elif hasattr(const_val, 'value'):
                                            val = const_val.value
                                            # [关键修复] 确保值是Python原生类型
                                            if type(val).__name__ in ('PycObject', 'PycSequence', 'PycTuple', 'PycList', 'PycSet', 'PycDict'):
                                                # 对于复杂类型，跳过（设为None）
                                                # 这些类型不应该出现在常量池中
                                                co_consts.append(None)
                                            else:
                                                co_consts.append(val)
                                        else:
                                            co_consts.append(None)
                                    elif hasattr(const_val, 'value'):
                                        val = const_val.value
                                        # [关键修复] 确保值是Python原生类型
                                        if type(val).__name__ in ('PycObject', 'PycSequence', 'PycTuple', 'PycList', 'PycSet', 'PycDict'):
                                            # 对于复杂类型，跳过（设为None）
                                            # 这些类型不应该出现在常量池中
                                            co_consts.append(None)
                                        else:
                                            co_consts.append(val)
                                    else:
                                        co_consts.append(None)
                        co_consts = tuple(co_consts)
                        
                        # 提取名称
                        co_names = []
                        if hasattr(pyc_code, 'names') and pyc_code.names:
                            names_obj = pyc_code.names.get()
                            if names_obj:
                                items = getattr(names_obj, '_values', getattr(names_obj, 'items', []))
                                for item in items:
                                    name_val = item.get() if hasattr(item, 'get') else item
                                    if name_val and hasattr(name_val, 'value'):
                                        co_names.append(name_val.value)
                                    else:
                                        co_names.append(str(name_val) if name_val else '')
                        co_names = tuple(co_names)
                        
                        # 提取局部变量名
                        co_varnames = []
                        if hasattr(pyc_code, 'local_names') and pyc_code.local_names:
                            varnames_obj = pyc_code.local_names.get()
                            if varnames_obj:
                                items = getattr(varnames_obj, '_values', getattr(varnames_obj, 'items', []))
                                for item in items:
                                    var_val = item.get() if hasattr(item, 'get') else item
                                    if var_val and hasattr(var_val, 'value'):
                                        co_varnames.append(var_val.value)
                                    else:
                                        co_varnames.append(str(var_val) if var_val else '')
                        co_varnames = tuple(co_varnames)
                        
                        # 提取文件名
                        co_filename = '<unknown>'
                        if hasattr(pyc_code, 'file_name') and pyc_code.file_name:
                            file_obj = pyc_code.file_name.get()
                            if file_obj and hasattr(file_obj, 'value'):
                                co_filename = file_obj.value
                        
                        # 提取函数名
                        co_name = '<module>'
                        if hasattr(pyc_code, 'name') and pyc_code.name:
                            name_obj = pyc_code.name.get()
                            if name_obj and hasattr(name_obj, 'value'):
                                co_name = name_obj.value
                        
                        # 基础参数
                        argcount = getattr(pyc_code, 'arg_count', 0)
                        posonlyargcount = getattr(pyc_code, 'pos_only_arg_count', 0)
                        kwonlyargcount = getattr(pyc_code, 'kw_only_arg_count', 0)
                        nlocals = getattr(pyc_code, 'num_locals', 0)
                        stacksize = getattr(pyc_code, 'stack_size', 0)
                        flags = getattr(pyc_code, 'flags', 0)
                        firstlineno = getattr(pyc_code, 'first_line', 1)
                        
                        # 提取行号表（lnotab/linetable）
                        lnotab = b''
                        if hasattr(pyc_code, 'ln_table') and pyc_code.ln_table:
                            line_table_obj = pyc_code.ln_table.get()
                            if line_table_obj:
                                # [关键修复] 优先使用PycBytes的_value（原始字节）
                                if hasattr(line_table_obj, '_value'):
                                    val = line_table_obj._value
                                    if isinstance(val, bytes):
                                        lnotab = val
                                    elif isinstance(val, str):
                                        lnotab = val.encode('latin-1')
                                elif hasattr(line_table_obj, 'value'):
                                    val = line_table_obj.value
                                    if isinstance(val, bytes):
                                        lnotab = val
                                    elif isinstance(val, str):
                                        lnotab = val.encode('latin-1')
                        
                        # 提取异常表（exceptiontable）- Python 3.11+
                        exceptiontable = b''
                        if py_version >= (3, 11) and hasattr(pyc_code, 'except_table'):
                            exc_table = pyc_code.except_table
                            if exc_table and hasattr(exc_table, 'get'):
                                exc_obj = exc_table.get()
                                if exc_obj:
                                    if hasattr(exc_obj, '_value'):
                                        val = exc_obj._value
                                        exceptiontable = val.encode('utf-8') if isinstance(val, str) else val
                                    elif hasattr(exc_obj, 'value'):
                                        val = exc_obj.value
                                        # [关键修复] PycBytes.value 返回 bytes，不需要编码
                                        if isinstance(val, str):
                                            exceptiontable = val.encode('utf-8')
                                        elif isinstance(val, bytes):
                                            exceptiontable = val
                                        else:
                                            exceptiontable = b''
                        
                        # 提取 freevars 和 cellvars
                        co_freevars = ()
                        if hasattr(pyc_code, 'free_vars') and pyc_code.free_vars:
                            freevars_obj = pyc_code.free_vars.get()
                            if freevars_obj:
                                items = getattr(freevars_obj, '_values', [])
                                co_freevars = tuple(
                                    item.get().value if hasattr(item.get(), 'value') else str(item.get())
                                    for item in items
                                )
                        
                        co_cellvars = ()
                        if hasattr(pyc_code, 'cell_vars') and pyc_code.cell_vars:
                            cellvars_obj = pyc_code.cell_vars.get()
                            if cellvars_obj:
                                items = getattr(cellvars_obj, '_values', [])
                                co_cellvars = tuple(
                                    item.get().value if hasattr(item.get(), 'value') else str(item.get())
                                    for item in items
                                )
                        
                        # 根据Python版本创建CodeType
                        if py_version >= (3, 11):
                            # Python 3.11+ 参数: argcount, posonlyargcount, kwonlyargcount, nlocals, stacksize, flags,
                            #                   codestring, constants, names, varnames, filename, name, qualname,
                            #                   firstlineno, linetable, exceptiontable, freevars=(), cellvars=()
                            return types.CodeType(
                                argcount,
                                posonlyargcount,
                                kwonlyargcount,
                                nlocals,
                                stacksize,
                                flags,
                                bytecode,
                                co_consts,
                                co_names,
                                co_varnames,
                                co_filename,
                                co_name,
                                co_name,  # qualname
                                firstlineno,
                                lnotab,   # linetable
                                exceptiontable,
                                co_freevars,
                                co_cellvars
                            )
                        elif py_version >= (3, 8):
                            # Python 3.8-3.10
                            return types.CodeType(
                                argcount, posonlyargcount, kwonlyargcount, nlocals,
                                stacksize, flags, bytecode, co_consts, co_names, co_varnames,
                                co_filename, co_name, firstlineno, lnotab, co_freevars, co_cellvars
                            )
                        else:
                            # Python 3.7及以下
                            return types.CodeType(
                                argcount, kwonlyargcount, nlocals, stacksize, flags,
                                bytecode, co_consts, co_names, co_varnames,
                                co_filename, co_name, firstlineno, lnotab, co_freevars, co_cellvars
                            )
                    
                    # 获取Python版本
                    _py_version = sys.version_info
                    
                    # 转换PycCode到Python CodeType
                    try:
                        actual_code = pyc_to_code(self.code_obj, _py_version)
                        co_name = actual_code.co_name
                        if verbose:
                            print(f"成功创建CodeType: {co_name}", file=sys.stderr)
                        


                    except Exception as code_err:
                        if verbose:
                            print(f"创建CodeType失败: {code_err}", file=sys.stderr)
                            import traceback as tb
                            tb.print_exc()
                        raise NotImplementedError(f"PYC代码对象处理失败: {code_err}")

                    source = generator.decompile(actual_code, co_name)

                    # [关键修复] source可以是空字符串（空模块），这是合法的
                    if source is not None:
                        # 验证生成的代码语法是否正确（空字符串也是合法的）
                        try:
                            if source:  # 非空才需要验证语法
                                compile(source, '<decompiled>', 'exec')
                            # 语法正确或为空，写入输出
                            output.write(source)
                            output.flush()
                            return True
                        except SyntaxError as e:
                            if cfg_hybrid:
                                if verbose:
                                    print(f"CFG方法生成的代码有语法错误: {e}，回退到传统方法", file=sys.stderr)
                                # 继续执行传统方法
                            else:
                                # 纯CFG模式：输出代码并显示警告
                                if verbose:
                                    print(f"Warning: CFG生成的代码有语法错误: {e}", file=sys.stderr)
                                output.write(source)
                                output.flush()
                                return True
                    elif cfg_hybrid:
                        # CFG失败，回退到传统方法
                        if verbose:
                            print("CFG方法失败，回退到传统方法", file=sys.stderr)
                    else:
                        print("Error: CFG反编译失败", file=sys.stderr)
                        return False

                except Exception as e:
                    if cfg_hybrid:
                        if verbose:
                            print(f"CFG方法异常: {e}，回退到传统方法", file=sys.stderr)
                    else:
                        raise

            # 传统反编译方法
            bytecode = self.code_obj.code.get()._value if self.code_obj.code else b''
            version = (self.module.major_version, self.module.minor_version)

            # 反汇编字节码
            self.disassembler = PycDisassembler(bytecode, self.module, version, self.code_obj)
            instructions = self.disassembler.disassemble()

            # 控制流分析 - 使用原始指令
            from core.control_flow import Instruction as CFInstruction
            cf_instructions = []
            for instr in instructions:
                if isinstance(instr, dict):
                    cf_instr = CFInstruction(
                        offset=instr.get('offset', 0),
                        opcode=instr.get('opcode', 0),
                        opname=instr.get('opcode_name', 'UNKNOWN'),
                        arg=instr.get('operand', 0)
                    )
                    cf_instructions.append(cf_instr)
                elif hasattr(instr, 'offset') and hasattr(instr, 'opcode'):
                    cf_instructions.append(instr)

            self.control_flow = ControlFlowAnalyzer(cf_instructions)
            self.control_flow.analyze()

            # 构建AST - 使用parsers.ast_builder.ASTBuilder
            from parsers.ast_builder import ASTBuilder
            ast_builder = ASTBuilder(self.module, self.code_obj)
            ast_root = ast_builder.build_from_code(self.code_obj)
            
            # 生成Python源代码
            from parsers.code_generator import CodeGenerator
            
            code_gen = CodeGenerator(version)
            
            # 生成模块代码
            code_gen.new_line()
            code_gen.add_token("# Decompiled by PyCDC Python")
            code_gen.new_line()
            
            # 使用AST生成代码
            if ast_root:
                # 直接使用AST生成代码
                generated_lines = []
                
                # [关键修复] 处理ASTFunctionDef对象（直接反编译函数代码对象的情况）
                from core.ast_nodes import ASTFunctionDef, ASTClassDef
                if isinstance(ast_root, ASTFunctionDef):
                    # 如果是函数定义节点，直接生成函数代码
                    if hasattr(ast_root, 'to_code'):
                        code = ast_root.to_code()
                        if code:
                            generated_lines.append(code)
                elif isinstance(ast_root, ASTClassDef):
                    # [关键修复] 如果是类定义节点，直接生成类代码
                    if hasattr(ast_root, 'to_code'):
                        code = ast_root.to_code()
                        if code:
                            generated_lines.append(code)
                elif hasattr(ast_root, 'nodes'):
                    # 如果是ASTBlock，直接使用其to_code方法（包含推导式去重等优化）
                    if hasattr(ast_root, 'to_code'):
                        code = ast_root.to_code()
                        if code:
                            generated_lines.append(code)
                generated_code = '\n'.join(generated_lines)
                # 直接写入，处理Unicode编码
                # [关键修复] 强制使用UTF-8编码，避免管道导致的编码问题
                try:
                    # [关键修复] 对于文件输出，确保使用UTF-8编码
                    if hasattr(output, 'encoding') and output.encoding:
                        # 如果文件已经以UTF-8打开，直接写入
                        output.write(generated_code)
                    elif hasattr(output, 'buffer'):
                        # 对于二进制模式，使用UTF-8编码
                        output.buffer.write(generated_code.encode('utf-8', 'replace'))
                    else:
                        # 其他情况，尝试直接写入
                        output.write(generated_code)
                except (AttributeError, UnicodeEncodeError) as e:
                    # 如果写入失败，使用替代字符
                    safe_code = generated_code.encode('utf-8', 'replace').decode('utf-8')
                    try:
                        output.write(safe_code)
                    except UnicodeEncodeError:
                        # 如果仍然失败，使用ASCII替代字符
                        ascii_code = generated_code.encode('ascii', 'replace').decode('ascii')
                        output.write(ascii_code)
                output.flush()  # 确保数据写入文件
            else:
                code_gen.add_token("# Failed to build AST from bytecode")
                code_gen.new_line()
                
                # 写入输出
                output.write(code_gen.output.getvalue() if hasattr(code_gen.output, 'getvalue') else str(code_gen.output))
            return True
                
        except Exception as e:
            try:
                error_msg = str(e)
                # 处理Unicode字符
                error_msg = error_msg.encode('ascii', 'replace').decode('ascii')
                print(f"Error decompiling: {error_msg}")
            except Exception:
                print("Error decompiling: Unknown error")
            import traceback
            import io
            # 捕获traceback并处理Unicode字符
            tb_buffer = io.StringIO()
            traceback.print_exc(file=tb_buffer)
            tb_str = tb_buffer.getvalue()
            tb_str = tb_str.encode('ascii', 'replace').decode('ascii')
            print(tb_str)
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Python PYC Decompiler - 反编译Python字节码文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.pyc                    # 反编译到标准输出
  %(prog)s -o output.py input.pyc      # 反编译到文件
  %(prog)s -c -v 3.11 code.pyc        # 反编译编译的代码对象
  %(prog)s --verbose input.pyc           # 显示详细输出
  %(prog)s --cfg input.pyc              # 使用CFG模块反编译
  %(prog)s --cfg-hybrid input.pyc       # 使用CFG混合模式
        """
    )
    
    parser.add_argument('input', nargs='?', help='输入的.pyc文件路径')
    parser.add_argument('-o', '--output', metavar='filename',
                      help='写入输出到指定文件（默认：标准输出）')
    parser.add_argument('-c', '--compiled', action='store_true',
                      help='指定加载编译的代码对象（需要设置版本）')
    parser.add_argument('-v', '--version', metavar='x.y',
                      help='为编译的代码对象指定Python版本')
    parser.add_argument('--verbose', action='store_true',
                      help='显示详细输出信息')
    parser.add_argument('--cfg', action='store_true',
                      help='使用CFG模块进行反编译（实验性功能）')
    parser.add_argument('--cfg-hybrid', action='store_true',
                      help='使用CFG混合模式（优先使用CFG，失败时回退到传统方法）')
    parser.add_argument('--region', action='store_true', default=True,
                      help='使用基于区域归约算法的反编译（无补丁，算法驱动）')
    parser.add_argument('--cfg-verbose', action='store_true',
                      help='显示CFG详细输出信息')
    
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
        # [CFG集成] 配置CFG模式
        if args.cfg or args.cfg_hybrid:
            try:
                from core.config import Config
                if args.cfg_hybrid:
                    Config.set_hybrid_mode(verbose=args.cfg_verbose)
                    if args.verbose:
                        print("CFG混合模式已启用", file=sys.stderr)
                else:
                    Config.enable_cfg(verbose=args.cfg_verbose)
                    if args.verbose:
                        print("CFG模式已启用", file=sys.stderr)
            except ImportError:
                print("警告: CFG模块不可用，回退到传统模式", file=sys.stderr)
        
        # 创建反编译器
        decompiler = PycDecompiler()
        
        # 加载文件
        if not decompiler.load_file(args.input, args.compiled, args.version):
            return 1
        
        # 显示文件信息
        dispname = os.path.basename(args.input)
        module = decompiler.module
        unicode_suffix = " Unicode" if (module.major < 3 and 
                                       module.is_unicode()) else ""
        output.write(f"# Source Generated with Decompyle++ (Python version)\n")
        output.write(f"# File: {dispname} (Python {module.major}."
                   f"{module.minor}{unicode_suffix})\n\n")
        
        if args.verbose:
            print(f"Decompiling: {args.input}", file=sys.stderr)
            print(f"Python version: {module.major}.{module.minor}", 
                  file=sys.stderr)
            print(f"Unicode: {module.is_unicode()}", file=sys.stderr)
        
        # 反编译
        if decompiler.decompile(output, use_cfg=args.cfg, cfg_hybrid=args.cfg_hybrid, use_region=args.region, verbose=args.verbose or args.cfg_verbose):
            if args.verbose:
                print("Decompilation completed successfully", file=sys.stderr)
            return 0
        else:
            return 1
        
    except Exception as e:
        print(f"Error decompiling {args.input}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if args.output:
            output.close()


def decompile_pyc(pyc_file: str, use_cfg: bool = False, cfg_hybrid: bool = False) -> str:
    """反编译PYC文件并返回源代码字符串"""
    import io
    
    # 创建反编译器
    decompiler = PycDecompiler()
    
    # 加载文件
    if not decompiler.load_file(pyc_file):
        raise RuntimeError(f"Failed to load {pyc_file}")
    
    # 创建字符串输出流
    output = io.StringIO()
    
    # 写入文件头
    module = decompiler.module
    dispname = os.path.basename(pyc_file)
    unicode_suffix = " Unicode" if (module.major < 3 and module.is_unicode()) else ""
    output.write(f"# Source Generated with Decompyle++ (Python version)\n")
    output.write(f"# File: {dispname} (Python {module.major}.{module.minor}{unicode_suffix})\n\n")
    
    # 反编译 - 使用区域模式
    if decompiler.decompile(output, use_cfg=use_cfg, cfg_hybrid=cfg_hybrid, use_region=True):
        result = output.getvalue()
        if result is None:
            raise RuntimeError(f"Decompilation returned None for {pyc_file}")
        return result
    else:
        raise RuntimeError(f"Failed to decompile {pyc_file}")


if __name__ == '__main__':
    # [关键修复] 设置Windows控制台为UTF-8编码
    import sys
    import io
    if sys.platform == 'win32':
        # 设置标准输出和标准错误为UTF-8编码
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
