"""
CFG代码生成器 - 从AST生成Python源代码

这是CFG模块的独立代码生成器，不依赖原有系统，
负责将AST树转换为格式化的Python源代码。
"""

import io
import re
import types
import sys
from typing import Any, Optional, List, Dict, Union
import logging

# 修复Windows控制台UTF-8编码
if sys.platform == 'win32':
    import codecs
    # 确保stdout使用UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from core.ast_nodes import (
    ASTNode, ASTBlock, ASTIf, ASTFor, ASTWhile, ASTTry, ASTWith,
    ASTFunctionDef, ASTClassDef, ASTReturn, ASTYield, ASTAssign, ASTAugAssign, ASTAnnAssign, ASTExpr,
    ASTName, ASTConstant, ASTBinary, ASTUnary, ASTCompare,
    ASTCall, ASTAttribute, ASTSubscript, ASTList, ASTTuple,
    ASTDict, ASTSet, ASTPass, ASTBreak, ASTContinue, ASTDelete,
    ASTExceptHandler, ASTWithItem, ASTJoinedStr, ASTFormattedValue,
    ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr, ASTComprehension,
    ASTNamedExpr, ASTIfExp, ASTImport, ASTImportFrom, ASTAwaitable, ASTRaise,
    ASTLambda, ASTSlice, ASTMatch, ASTCase, ASTAssert, ASTGlobal, ASTNonlocal
)

logger = logging.getLogger(__name__)


class CodeGenerationError(Exception):
    """代码生成错误"""
    pass


class CodeGenerator:
    """
    CFG代码生成器
    
    将AST树转换为格式化的Python源代码。
    支持所有Python 3.8-3.11语法特性。
    """
    
    def __init__(self, indent_size: int = 4, verbose: bool = False, original_consts: Optional[List[Any]] = None):
        self.indent_size = indent_size
        self.verbose = verbose
        self.indent_level = 0
        self.output = io.StringIO()
        self._function_depth = 0  # 函数嵌套深度，用于跟踪是否在函数内部
        self._function_depth_stack = []  # 函数深度栈，用于跟踪函数嵌套层级
        self._loop_depth = 0  # 循环嵌套深度，用于跟踪是否在循环内部
        self._if_depth = 0  # if语句嵌套深度，用于跟踪是否在if语句内部
        self._except_as_vars = set()  # except的as变量名集合，用于区分清理代码和用户代码
        self._last_was_break = False
        self._lines = []
        
        # [关键修复-2026] 收集global/nonlocal声明，用于前置到函数体开头
        self._pending_globals: List[str] = []
        self._pending_nonlocals: List[str] = []
        
        # [关键修复] 保存原始常量池，用于保持字节码一致性
        self.original_consts = original_consts
        
        # 操作符优先级（数字越小优先级越高）
        self._precedence = {
            'lambda': 1,
            'if': 2,  # 条件表达式
            'or': 3,
            'and': 4,
            'not': 5,
            'in': 6, 'not in': 6, 'is': 6, 'is not': 6,
            '<': 6, '<=': 6, '>': 6, '>=': 6, '!=': 6, '==': 6,
            '|': 7,
            '^': 8,
            '&': 9,
            '<<': 10, '>>': 10,
            '+': 11, '-': 11,
            '*': 12, '@': 12, '/': 12, '//': 12, '%': 12,
            '+x': 13, '-x': 13, '~x': 13,  # 一元操作
            '**': 14,
            'await': 15,
            'subscript': 16, 'slice': 16, 'call': 16, 'attribute': 16,
            'atom': 17,  # 原子表达式
        }
    
    def generate(self, node: Union[ASTNode, Dict[str, Any]], in_function: bool = False) -> str:
        """
        生成Python源代码
        
        Args:
            node: AST节点或字典（来自ASTGeneratorV2）
            in_function: 是否在函数上下文中（默认False）
                         对于模块级别代码，应该设置为False（默认）
                         对于函数代码对象的反编译，应该设置为True
            
        Returns:
            格式化的Python源代码
        """
        self.indent_level = 0
        self.output = io.StringIO()
        # [关键修复] 根据in_function参数设置_function_depth
        # 对于模块级别代码，_function_depth=0，模块级return会被过滤
        # 对于函数代码对象的反编译，需要设置in_function=True
        self._function_depth = 1 if in_function else 0
        self._loop_depth = 0  # 重置循环深度
        
        try:
            if isinstance(node, dict):
                self._generate_dict_node(node)
                return self.output.getvalue()

            self._generate_node(node)
            return self.output.getvalue()
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            if self.verbose:
                logger.exception("Generation error details")
            raise CodeGenerationError(f"Failed to generate code: {e}")
    
    def _in_function_context(self) -> bool:
        """检查当前是否在函数内部"""
        return self._function_depth > 0
    
    def _is_in_if_body(self) -> bool:
        """检查当前是否在if语句的body中"""
        return self._if_depth > 0
    
    def _indent(self) -> str:
        """获取当前缩进字符串"""
        return ' ' * (self.indent_level * self.indent_size)
    
    def _write(self, text: str) -> None:
        """写入文本"""
        # [P2-2026] 清理null bytes（来自字节码常量池的残留）
        if '\x00' in text:
            text = text.replace('\x00', '')
        self.output.write(text)
    
    def _write_line(self, text: str = '') -> None:
        """写入一行（带缩进）"""
        if text:
            self._write(self._indent() + text)
        self._write('\n')
    
    def _increase_indent(self) -> None:
        """增加缩进级别"""
        self.indent_level += 1
    
    def _decrease_indent(self) -> None:
        """减少缩进级别"""
        self.indent_level = max(0, self.indent_level - 1)
    
    def _generate_node(self, node: Optional[ASTNode]) -> None:
        """生成节点代码"""
        if node is None:
            return
        
        # [关键修复-2026] 支持字典格式的AST节点（来自ast_generator_v2.py）
        # ast_generator_v2.py生成的是字典格式，而不是ASTNode对象
        if isinstance(node, dict):
            self._generate_dict_node(node)
            return
        
        # 根据节点类型分发
        if isinstance(node, ASTBlock):
            self._generate_block(node)
        elif isinstance(node, ASTIf):
            self._generate_if(node)
        elif isinstance(node, ASTFor):
            self._generate_for(node)
        elif isinstance(node, ASTWhile):
            self._generate_while(node)
        elif isinstance(node, ASTTry):
            self._generate_try(node)
        elif isinstance(node, ASTWith):
            self._generate_with(node)
        elif isinstance(node, ASTFunctionDef):
            self._generate_function_def(node)
        elif isinstance(node, ASTClassDef):
            self._generate_class_def(node)
        elif isinstance(node, ASTReturn):
            self._generate_return(node)
        elif isinstance(node, ASTYield):
            self._generate_yield(node)
        elif isinstance(node, ASTAssign):
            self._generate_assign(node)
        elif isinstance(node, ASTAugAssign):
            self._generate_aug_assign(node)
        elif isinstance(node, ASTAnnAssign):
            self._generate_ann_assign(node)
        elif isinstance(node, ASTExpr):
            self._generate_expr_stmt(node)
        elif isinstance(node, ASTPass):
            self._generate_pass(node)
        elif isinstance(node, ASTBreak):
            self._generate_break(node)
        elif isinstance(node, ASTContinue):
            self._generate_continue(node)
        elif isinstance(node, ASTDelete):
            self._generate_delete_node(node)
        elif isinstance(node, ASTImport):
            self._generate_import(node)
        elif isinstance(node, ASTImportFrom):
            self._generate_import_from(node)
        elif isinstance(node, ASTRaise):
            self._generate_raise(node)
        elif isinstance(node, ASTAssert):
            self._generate_assert(node)
        elif isinstance(node, ASTGlobal):
            self._generate_global(node)
        elif isinstance(node, ASTNonlocal):
            self._generate_nonlocal(node)
        elif isinstance(node, ASTMatch):
            self._generate_match(node)
        elif isinstance(node, ASTCase):
            self._generate_case(node)
        elif isinstance(node, ASTNonlocal):
            self._generate_nonlocal(node)
        elif isinstance(node, (ASTName, ASTConstant, ASTBinary, ASTUnary,
                              ASTCompare, ASTCall, ASTAttribute, ASTSubscript,
                              ASTList, ASTTuple, ASTDict, ASTSet, ASTIfExp,
                              ASTLambda)):
            expr_code = self._generate_expression(node)
            self._write_line(expr_code)
        else:
            # 未知节点类型
            if self.verbose:
                logger.warning(f"Unknown node type: {type(node).__name__}")
            self._write_line(f'# Unknown node: {type(node).__name__}')
    
    def _generate_dict_node(self, node: Dict[str, Any]) -> None:
        """[关键修复-2026] 生成字典格式的AST节点（来自ast_generator_v2.py）"""
        if not isinstance(node, dict) or 'type' not in node:
            return

        node_type = node.get('type')

        if node_type == 'Module':
            body = node.get('body', [])
            if not body:
                self._write_line('pass')
            for body_node in body:
                if isinstance(body_node, dict):
                    self._generate_dict_node(body_node)
                else:
                    self._generate_node(body_node)
        elif node_type == 'While':
            self._generate_while_dict(node)
        elif node_type == 'If':
            self._generate_if_dict(node)
        elif node_type == 'For':
            self._generate_for_dict(node)
        elif node_type == 'AsyncFor':
            self._generate_for_dict(node, async_prefix='async ')
        elif node_type == 'Return':
            self._generate_return_dict(node)
        elif node_type == 'AugAssign':
            self._generate_aug_assign_dict(node)
        elif node_type == 'Assign':
            self._generate_assign_dict(node)
        elif node_type == 'AugAssign':
            self._generate_aug_assign_dict(node)
        elif node_type == 'Expr':
            expr = node.get('value')
            if expr:
                # [修复-L13/L17/L18] Expr的value可能是语句节点而非表达式
                # 如果是语句类型(AugAssign, Assign等)，调用对应语句生成器
                if isinstance(expr, dict):
                    expr_type = expr.get('type', '')
                    if expr_type in ('AugAssign', 'Assign', 'Return', 'Raise', 'Break',
                                    'Continue', 'Delete', 'Pass', 'For', 'While',
                                    'If', 'Try', 'With', 'FunctionDef', 'ClassDef',
                                    'Yield', 'YieldFrom', 'AsyncFunctionDef', 'AsyncFor',
                                    'AsyncWith'):
                        self._generate_dict_node(expr)
                        return
                expr_code = self._generate_expression(expr)
                self._write_line(expr_code)
        elif node_type == 'Pass':
            self._write_line('pass')
        elif node_type == 'Break':
            self._write_line('break')
        elif node_type == 'Continue':
            self._write_line('continue')
        elif node_type == 'Delete':
            self._generate_delete_dict(node)
        elif node_type == 'Global':
            names = node.get('names', [])
            if names:
                names_str = ', '.join(str(n) for n in names)
                self._write_line(f"global {names_str}")
        elif node_type == 'Nonlocal':
            names = node.get('names', [])
            filtered_names = [n for n in names if n != '__class__']
            if filtered_names:
                names_str = ', '.join(filtered_names)
                self._write_line(f"nonlocal {names_str}")
        elif node_type == 'Raise':
            # [关键修复-2026] 处理字典格式的Raise节点
            exc = node.get('exc')
            if exc:
                # 检测异常AST结构：Call(func=Constant, args=[])
                if isinstance(exc, dict) and exc.get('type') == 'Call':
                    func = exc.get('func', {})
                    args = exc.get('args', [])
                    
                    # 如果 func 是 Constant（字符串），转换为 RuntimeError
                    if isinstance(func, dict) and func.get('type') == 'Constant' and isinstance(func.get('value'), str):
                        error_msg = func.get('value', '')
                        self._write_line(f"raise RuntimeError({repr(error_msg)})")
                        return
                
                exc_code = self._generate_expression(exc)
                cause = node.get('cause')
                if cause:
                    cause_code = self._generate_expression(cause)
                    self._write_line(f'raise {exc_code} from {cause_code}')
                else:
                    self._write_line(f'raise {exc_code}')
            else:
                self._write_line('raise')
        elif node_type == 'Lambda':
            # Lambda expressions in statement context (rare)
            lambda_code = self._generate_lambda_from_dict(node)
            self._write_line(lambda_code)
        elif node_type == 'FunctionDef':
            self._generate_function_def_dict(node)
        elif node_type == 'AsyncFunctionDef':
            self._generate_function_def_dict(node, async_prefix='async ')
        elif node_type == 'ClassDef':
            self._generate_class_def_dict(node)
        elif node_type == 'Try':
            # [P2-2026] 处理字典格式的Try节点
            self._generate_try_dict(node)
        elif node_type == 'With':
            self._generate_with_dict(node)
        elif node_type == 'AsyncWith':
            self._generate_with_dict(node, async_prefix='async ')
        elif node_type == 'Assert':
            # 处理Assert语句
            test = node.get('test')
            msg = node.get('msg')
            test_code = self._generate_expression(test) if isinstance(test, dict) else str(test)
            if msg:
                msg_code = self._generate_expression(msg) if isinstance(msg, dict) else str(msg)
                self._write_line(f'assert {test_code}, {msg_code}')
            else:
                self._write_line(f'assert {test_code}')
        elif node_type in ('Import', 'ImportFrom'):
            # 处理Import语句
            names = node.get('names', [])
            names_str = ', '.join(n if isinstance(n, str) else n.get('name', str(n)) for n in names)
            if node_type == 'ImportFrom':
                module = node.get('module', '')
                level = node.get('level', 0)
                prefix = '.' * level
                self._write_line(f'from {prefix}{module} import {names_str}')
            else:
                self._write_line(f'import {names_str}')
        elif node_type == 'Match':
            # 处理Match语句
            subject = node.get('subject')
            subject_code = self._generate_expression(subject) if isinstance(subject, dict) else str(subject)
            self._write_line(f'match {subject_code}:')
            cases = node.get('cases', [])
            # Increase indent for case bodies
            self._increase_indent()
            for case in cases:
                if isinstance(case, dict):
                    self._generate_match_case_dict(case)
            self._decrease_indent()
        elif node_type == 'Expr':
            value = node.get('value')
            if value:
                value_code = self._generate_expression(value) if isinstance(value, dict) else str(value)
                self._write_line(value_code)
        elif node_type == 'Call':
            value_code = self._generate_expression(node) if isinstance(node, dict) else str(node)
            self._write_line(value_code)
        elif node_type == 'Yield':
            # 处理Yield表达式
            value = node.get('value')
            if value:
                value_code = self._generate_expression(value) if isinstance(value, dict) else str(value)
                self._write_line(f'yield {value_code}')
            else:
                self._write_line('yield')
        elif node_type == 'YieldFrom':
            # 处理YieldFrom表达式
            value = node.get('value')
            if value:
                value_code = self._generate_expression(value) if isinstance(value, dict) else str(value)
                self._write_line(f'yield from {value_code}')
        else:
            # 尝试作为表达式处理
            if self.verbose:
                logger.warning(f"Unhandled dict node type: {node_type}")
            self._write_line(f'# Unhandled dict node: {node_type}')
    
    def _generate_aug_assign_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的AugAssign节点（如 count += 1）"""
        target = node.get('target', {})
        op = node.get('op', '')
        value = node.get('value', {})
        
        # 生成目标
        target_code = self._generate_expression(target)
        
        # 生成值
        value_code = self._generate_expression(value)
        
        # 输出赋值语句
        self._write_line(f'{target_code} {op}= {value_code}')

    def _generate_function_def_dict(self, node: Dict[str, Any], async_prefix: str = '') -> None:
        func_name = node.get('name', 'function')
        args = node.get('args', {})
        body = node.get('body', [])
        decorator_list = node.get('decorator_list', [])
        returns = node.get('returns')
        
        for decorator in decorator_list:
            if isinstance(decorator, dict):
                decorator_code = self._generate_expression(decorator)
            else:
                decorator_code = str(decorator)
            self._write_line(f'@{decorator_code}')
        
        args_code = self._generate_arguments_dict(args)
        
        if returns:
            returns_code = self._generate_expression(returns) if isinstance(returns, dict) else str(returns)
            self._write_line(f'{async_prefix}def {func_name}({args_code}) -> {returns_code}:')
        else:
            self._write_line(f'{async_prefix}def {func_name}({args_code}):')
        
        # 生成函数体
        self._increase_indent()
        self._function_depth += 1  # 进入函数内部
        
        try:
            if body:
                for body_node in body:
                    if isinstance(body_node, dict):
                        self._generate_dict_node(body_node)
                    else:
                        self._generate_node(body_node)
            else:
                self._write_line('pass')
        finally:
            self._function_depth -= 1  # 退出函数
            self._decrease_indent()

    def _generate_arguments_dict(self, args: Dict[str, Any]) -> str:
        """[P2-2026] 从字典格式的参数信息生成参数列表字符串"""
        posonlyargs = args.get('posonlyargs', [])
        args_list = args.get('args', [])
        vararg = args.get('vararg')
        kwonlyargs = args.get('kwonlyargs', [])
        kw_defaults = args.get('kw_defaults', [])
        kwarg = args.get('kwarg')
        defaults = args.get('defaults', [])
        
        parts = []
        
        # 仅位置参数（Python 3.8+）
        for arg in posonlyargs:
            arg_name = arg.get('arg', '') if isinstance(arg, dict) else str(arg)
            parts.append(arg_name)
        
        # 普通位置参数
        for i, arg in enumerate(args_list):
            arg_name = arg.get('arg', '') if isinstance(arg, dict) else str(arg)
            
            # 检查是否有默认值
            default_idx = i - (len(args_list) - len(defaults))
            if 0 <= default_idx < len(defaults):
                default = defaults[default_idx]
                default_code = self._generate_expression(default) if isinstance(default, dict) else repr(default)
                parts.append(f'{arg_name}={default_code}')
            else:
                parts.append(arg_name)
        
        # *args
        if vararg:
            vararg_name = vararg.get('arg', '') if isinstance(vararg, dict) else str(vararg)
            parts.append(f'*{vararg_name}')
        elif kwonlyargs:
            # 如果没有*args但有仅关键字参数，需要添加*
            parts.append('*')
        
        # 仅关键字参数
        for i, arg in enumerate(kwonlyargs):
            arg_name = arg.get('arg', '') if isinstance(arg, dict) else str(arg)
            
            # 检查是否有默认值
            if i < len(kw_defaults) and kw_defaults[i] is not None:
                default = kw_defaults[i]
                default_code = self._generate_expression(default) if isinstance(default, dict) else repr(default)
                parts.append(f'{arg_name}={default_code}')
            else:
                parts.append(arg_name)
        
        # **kwargs
        if kwarg:
            kwarg_name = kwarg.get('arg', '') if isinstance(kwarg, dict) else str(kwarg)
            parts.append(f'**{kwarg_name}')
        
        return ', '.join(parts)

    def _is_simple_stmt(self, node):
        if isinstance(node, dict):
            t = node.get('type', '')
            return t in ('Assign', 'AugAssign', 'AnnAssign', 'Expr', 'Pass',
                         'Break', 'Continue', 'Return', 'Raise', 'Global',
                         'Nonlocal', 'Assert', 'Delete')
        return False

    def _generate_inline_body(self, body):
        if not body:
            self._write(' pass')
            self._write('\n')
            return True
        if len(body) == 1 and self._is_simple_stmt(body[0]):
            self._write(' ')
            saved_indent = self.indent_level
            self.indent_level = 0
            if isinstance(body[0], dict):
                self._generate_dict_node(body[0])
            else:
                self._generate_node(body[0])
            self.indent_level = saved_indent
            return True
        return False

    def _generate_dict_node_inline(self, node: Dict[str, Any]) -> None:
        saved_lines = self._lines
        self._lines = []
        self._generate_dict_node(node)
        inline_code = ''.join(self._lines).strip()
        self._lines = saved_lines
        self._write(inline_code)
        self._write('\n')

    def _is_simple_single_statement(self, body):
        if not body or len(body) != 1:
            return False
        stmt = body[0]
        if isinstance(stmt, dict):
            t = stmt.get('type', '')
            return t in ('Assign', 'AugAssign', 'Pass', 'Break', 'Continue',
                        'Return', 'Raise', 'Delete', 'Global', 'Nonlocal',
                        'Assert', 'Expr', 'Import', 'ImportFrom')
        return False

    def _generate_single_stmt_line(self, stmt):
        if isinstance(stmt, dict):
            old_output = self.output
            self.output = io.StringIO()
            self._generate_dict_node(stmt)
            result = self.output.getvalue().strip()
            self.output = old_output
            return result
        return None

    def _generate_try_dict(self, node: Dict[str, Any]) -> None:
        body = node.get('body', [])
        handlers = node.get('handlers', [])
        orelse = node.get('orelse', [])
        finalbody = node.get('finalbody', [])

        self._write_line('try:')
        self._increase_indent()
        if body:
            for body_node in body:
                if isinstance(body_node, dict):
                    self._generate_dict_node(body_node)
                elif isinstance(body_node, list):
                    for sub_node in body_node:
                        if isinstance(sub_node, dict):
                            self._generate_dict_node(sub_node)
                else:
                    self._generate_node(body_node)
        else:
            self._write_line('pass')
        self._decrease_indent()

        for handler in handlers:
            if isinstance(handler, dict):
                exc_type_node = handler.get('exc_type')
                name = handler.get('name')
                handler_body = handler.get('body', [])

                if name:
                    self._except_as_vars.add(name)

                if exc_type_node is not None:
                    if isinstance(exc_type_node, dict):
                        exc_code = self._generate_expression(exc_type_node)
                    else:
                        exc_code = str(exc_type_node)
                    if name:
                        header = f'except {exc_code} as {name}:'
                    else:
                        header = f'except {exc_code}:'
                elif name:
                    header = f'except Exception as {name}:'
                else:
                    header = 'except:'

                if self._is_simple_single_statement(handler_body):
                    stmt_line = self._generate_single_stmt_line(handler_body[0])
                    if stmt_line:
                        self._write_line(f'{header} {stmt_line}')
                    else:
                        self._write_line(header)
                        self._increase_indent()
                        self._write_line('pass')
                        self._decrease_indent()
                else:
                    self._write_line(header)
                    self._increase_indent()
                    if handler_body:
                        for h_node in handler_body:
                            if isinstance(h_node, dict):
                                self._generate_dict_node(h_node)
                            else:
                                self._generate_node(h_node)
                    else:
                        self._write_line('pass')
                    self._decrease_indent()

        if orelse:
            if self._is_simple_single_statement(orelse):
                stmt_line = self._generate_single_stmt_line(orelse[0])
                if stmt_line:
                    self._write_line(f'else: {stmt_line}')
                else:
                    self._write_line('else:')
                    self._increase_indent()
                    for else_node in orelse:
                        if isinstance(else_node, dict):
                            self._generate_dict_node(else_node)
                        else:
                            self._generate_node(else_node)
                    self._decrease_indent()
            else:
                self._write_line('else:')
                self._increase_indent()
                for else_node in orelse:
                    if isinstance(else_node, dict):
                        self._generate_dict_node(else_node)
                    else:
                        self._generate_node(else_node)
                self._decrease_indent()

        if finalbody:
            if self._is_simple_single_statement(finalbody):
                stmt_line = self._generate_single_stmt_line(finalbody[0])
                if stmt_line:
                    self._write_line(f'finally: {stmt_line}')
                else:
                    self._write_line('finally:')
                    self._increase_indent()
                    for final_node in finalbody:
                        if isinstance(final_node, dict):
                            self._generate_dict_node(final_node)
                        else:
                            self._generate_node(final_node)
                    self._decrease_indent()
            else:
                self._write_line('finally:')
                self._increase_indent()
                for final_node in finalbody:
                    if isinstance(final_node, dict):
                        self._generate_dict_node(final_node)
                    else:
                        self._generate_node(final_node)
                self._decrease_indent()

    def _generate_with_dict(self, node: Dict[str, Any], async_prefix: str = '') -> None:
        items = node.get('items', [])
        if not items:
            return

        items_code = []
        for item in items:
            if isinstance(item, dict):
                context_expr = item.get('context_expr')
                optional_vars = item.get('optional_vars')
                if context_expr:
                    ctx_code = self._generate_expression(context_expr)
                    if optional_vars:
                        var_code = self._generate_expression(optional_vars) if isinstance(optional_vars, dict) else str(optional_vars)
                        items_code.append(f'{ctx_code} as {var_code}')
                    else:
                        items_code.append(ctx_code)

        is_async = node.get('is_async', False) or bool(async_prefix)
        prefix = 'async ' if is_async else ''
        header = f'{prefix}with {", ".join(items_code)}:'

        body = node.get('body', [])

        if self._is_simple_single_statement(body):
            stmt_line = self._generate_single_stmt_line(body[0])
            if stmt_line:
                self._write_line(f'{header} {stmt_line}')
            else:
                self._write_line(header)
                self._increase_indent()
                self._write_line('pass')
                self._decrease_indent()
        else:
            self._write_line(header)
            self._increase_indent()
            if body:
                for body_node in body:
                    if isinstance(body_node, dict):
                        self._generate_dict_node(body_node)
                    else:
                        self._generate_node(body_node)
            else:
                self._write_line('pass')
            self._decrease_indent()

    def _generate_delete_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的Delete节点"""
        targets = node.get('targets', [])
        if not targets:
            self._write_line('del')
            return

        target_codes = []
        for target in targets:
            target_code = self._generate_expression(target)
            # [关键修复-2026] 去掉del目标周围的冗余括号
            # 例如：del (address[0]) → del address[0]
            #         del (e) → del e
            # 但要保留必要的括号（如包含运算符的表达式）
            if target_code.startswith('(') and target_code.endswith(')'):
                inner = target_code[1:-1].strip()
                # 只去掉简单表达式的外层括号：
                # - 单个变量名: (x)
                # - 简单下标: (x[0]), (x[y])
                # - 简单属性: (x.y)
                # 保留复杂表达式的括号
                # [修复] 下标可以是数字或变量名，属性名是变量名
                if re.match(r'^[a-zA-Z_]\w*(\[[^\]]+\])?(\.\w+)?$', inner):
                    target_code = inner
            target_codes.append(target_code)

        self._write_line(f'del {", ".join(target_codes)}')

    def _generate_if_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的If节点"""
        test = node.get('test', {})
        body = node.get('body', [])
        orelse = node.get('orelse', [])

        # 生成条件
        test_code = self._generate_expression(test)

        # [关键修复-根本性修复] _is_nested_if标记表示这是一个嵌套在另一个if的body中的if
        # 但它不应该变成elif，而应该保持为独立的if
        # elif应该只用于orelse中的if节点
        self._write_line(f'if {test_code}:')
        
        # 生成body
        self._increase_indent()
        self._if_depth += 1
        
        if body:
            # [修复-L05] 检查循环体最后一个语句是否是无意义的continue
            # 如果循环体中有break，最后的continue是隐式fallthrough，可以省略
            has_break = any(self._node_contains_break(child) for child in body)
            for i, child in enumerate(body):
                is_last = (i == len(body) - 1)
                if is_last and has_break:
                    if isinstance(child, dict) and child.get('type') == 'Continue':
                        continue  # 跳过无意义的末尾continue
                    elif hasattr(child, '__class__') and 'Continue' in type(child).__name__:
                        continue
                self._generate_node(child)
        else:
            self._write_line('pass')
        
        self._if_depth -= 1
        self._decrease_indent()
        
        # 生成orelse
        if orelse:
            is_else_content_if = False
            if len(orelse) == 1 and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If':
                if orelse[0].get('_is_else_content', False):
                    is_else_content_if = True
            
            if len(orelse) == 1 and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If' and not orelse[0].get('_is_nested_if') and not is_else_content_if:
                # [修复-C03] elif链：直接生成elif而不是递归调用_generate_node
                # 递归调用会导致生成独立的if，而这里应该生成elif
                elif_node = orelse[0]
                elif_test = elif_node.get('test', {})
                elif_test_code = self._generate_expression(elif_test)
                self._write_line(f'elif {elif_test_code}:')

                # 生成elif的body
                self._if_depth += 1
                self._increase_indent()
                elif_body = elif_node.get('body', [])
                if elif_body:
                    for child in elif_body:
                        self._generate_node(child)
                else:
                    self._write_line('pass')
                self._decrease_indent()
                self._if_depth -= 1

                # 递归处理elif的orelse（可能是另一个elif或else）
                elif_orelse = elif_node.get('orelse', [])
                if elif_orelse:
                    self._generate_elif_or_else_dict(elif_orelse)
            else:
                self._write_line('else:')
                self._if_depth += 1
                self._increase_indent()
                if orelse:
                    for child in orelse:
                        self._generate_node(child)
                else:
                    self._write_line('pass')
                self._decrease_indent()
                self._if_depth -= 1

    def _generate_elif_or_else_dict(self, orelse: List[Dict]) -> None:
        if not orelse:
            return

        def _flatten(lst):
            result = []
            for item in lst:
                if isinstance(item, list):
                    result.extend(_flatten(item))
                else:
                    result.append(item)
            return result
        
        orelse = _flatten(orelse)

        if len(orelse) == 1 and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If' and not orelse[0].get('_is_nested_if'):
            elif_node = orelse[0]
            elif_test = elif_node.get('test', {})
            elif_test_code = self._generate_expression(elif_test)
            self._write_line(f'elif {elif_test_code}:')

            self._if_depth += 1
            self._increase_indent()
            elif_body = elif_node.get('body', [])
            if elif_body:
                for child in elif_body:
                    self._generate_node(child)
            else:
                self._write_line('pass')
            self._decrease_indent()
            self._if_depth -= 1

            elif_orelse = elif_node.get('orelse', [])
            if elif_orelse:
                self._generate_elif_or_else_dict(elif_orelse)
        else:
            self._write_line('else:')
            self._if_depth += 1
            self._increase_indent()
            pos_before = self.output.tell()
            for child in orelse:
                self._generate_node(child)
            if self.output.tell() == pos_before:
                self._write_line('pass')
            self._decrease_indent()
            self._if_depth -= 1

    def _generate_return_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的Return节点"""
        value = node.get('value')
        if value:
            value_code = self._generate_expression(value)
            self._write_line(f'return {value_code}')
        else:
            self._write_line('return')
    
    def _generate_assign_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的Assign节点"""
        targets = node.get('targets', [])
        value = node.get('value', {})
        
        # [关键修复-2026] 链式赋值 a = b = c = 0
        if node.get('is_chain_assign') and len(targets) > 1:
            targets_code = [self._generate_expression(t) for t in targets]
            value_code = self._generate_expression(value)
            target_code = ' = '.join(targets_code)
            self._write_line(f'{target_code} = {value_code}')
            return
        
        targets_code = [self._generate_expression(t) for t in targets]
        
        # [关键修复-2026] 处理 value 为 Slice 类型的情况
        # Python中 Slice 不能作为独立的赋值值（如 x = a:b 是无效语法）
        # 需要转换为 slice() 函数调用（如 x = slice(a, b)）
        if isinstance(value, dict) and value.get('type') == 'Slice':
            value_code = self._generate_slice_as_function_call(value)
        else:
            # [修复-L13/L17/L18] Assign的value可能是语句节点(AugAssign等)
            if isinstance(value, dict) and value.get('type') in ('AugAssign', 'Return', 'Raise',
                                                                   'For', 'While', 'If', 'Try'):
                self._generate_dict_node(value)
                return
            value_code = self._generate_expression(value)
        
        # [关键修复-2026] 元组解包赋值优化
        # 当目标是元组 (a, b, c)，值是常量列表/元组时，去掉值的括号
        # 例如: a, b, c = (1, 2, 3) → a, b, c = 1, 2, 3
        if (len(targets_code) == 1 and 
            isinstance(value, dict) and value.get('type') == 'Constant' and 
            isinstance(value.get('value'), (list, tuple)) and
            len(value.get('value')) > 1):
            # 检查目标是否是多元组（元组解包赋值）
            target = targets[0] if targets else {}
            if target.get('type') == 'Tuple' and len(target.get('elts', [])) > 1:
                # 去掉括号/方括号
                if value_code.startswith('(') and value_code.endswith(')'):
                    value_code = value_code[1:-1]
                elif value_code.startswith('[') and value_code.endswith(']'):
                    value_code = value_code[1:-1]

        # [修复-E07] 跳过异常变量清理代码 (Python 3.11+)
        # 例如: e = None（except块结束时的异常变量清理）
        # 这些是编译器自动插入的，不应出现在反编译结果中
        if (len(targets_code) == 1 and
            isinstance(value, dict) and value.get('type') == 'Constant' and
            value.get('value') is None):
            target_str = targets_code[0] if targets_code else ''
            if target_str.isidentifier() and self._in_function_context() and not self._is_in_if_body():
                if len(self._function_depth_stack) > 0:
                    return

        self._write_line(f'{", ".join(targets_code)} = {value_code}')

    def _generate_aug_assign_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的AugAssign节点（如 count += 1）"""
        target = node.get('target', {})
        op = node.get('op', '')
        value = node.get('value', {})

        target_code = self._generate_expression(target)
        value_code = self._generate_expression(value)

        # Python增强赋值操作符映射
        op_map = {
            '+': '+=', '-': '-=', '*': '*=', '/': '/=',
            '%': '%=' , '**': '**=', '//': '//=',
            '&': '&=', '|': '|=', '^': '^=',
            '>>': '>>=', '<<': '<<=',
        }
        op_symbol = op_map.get(op, f'{op}=')

        self._write_line(f'{target_code} {op_symbol} {value_code}')

    def _generate_for_dict(self, node: Dict[str, Any], async_prefix: str = '') -> None:
        target = node.get('target', {})
        iter_expr = node.get('iter', {})
        body = node.get('body', [])
        orelse = node.get('orelse', [])
        
        target_code = self._generate_for_target_from_dict(target)
        iter_code = self._generate_expression(iter_expr, 0)
        
        self._write_line(f'{async_prefix}for {target_code} in {iter_code}:')
        
        self._increase_indent()
        self._loop_depth += 1
        
        if body:
            # [修复-L05] 检查循环体最后一个语句是否是无意义的continue
            has_break = any(self._node_contains_break(child) for child in body)
            for i, child in enumerate(body):
                is_last = (i == len(body) - 1)
                if is_last and has_break:
                    if isinstance(child, dict) and child.get('type') == 'Continue':
                        continue
                    elif hasattr(child, '__class__') and 'Continue' in type(child).__name__:
                        continue
                self._generate_node(child)
        else:
            self._write_line('pass')
        
        self._loop_depth -= 1
        self._decrease_indent()
        
        if orelse:
            self._write_line('else:')
            self._increase_indent()
            # [修复-L05] 过滤else末尾与函数体重复的return
            # 只有当else有多个语句时才过滤最后的return
            # 如果return是唯一语句则保留（避免空else块）
            if len(orelse) > 1:
                for i, child in enumerate(orelse):
                    is_last = (i == len(orelse) - 1)
                    if is_last and isinstance(child, dict) and child.get('type') == 'Return':
                        continue
                    self._generate_node(child)
            else:
                for child in orelse:
                    self._generate_node(child)
            self._decrease_indent()
    
    def _generate_while_dict(self, node: Dict[str, Any]) -> None:
        """生成字典格式的While节点"""
        test = node.get('test', {})
        body = node.get('body', [])
        orelse = node.get('orelse', [])
        
        # 生成while行
        test_code = self._generate_expression(test, 0)
        self._write_line(f'while {test_code}:')

        # 生成循环体
        self._increase_indent()
        self._loop_depth += 1
        try:
            if body:
                # [修复-L05] 同for循环，跳过无意义的末尾continue
                has_break = any(self._node_contains_break(child) for child in body)
                for i, child in enumerate(body):
                    is_last = (i == len(body) - 1)
                    if is_last and has_break:
                        if isinstance(child, dict) and child.get('type') == 'Continue':
                            continue
                        elif hasattr(child, '__class__') and 'Continue' in type(child).__name__:
                            continue
                    self._generate_node(child)
            else:
                self._write_line('pass')
        finally:
            self._loop_depth -= 1
        self._decrease_indent()

        # 生成else分支
        if orelse:
            self._write_line('else:')
            self._increase_indent()
            for child in orelse:
                self._generate_node(child)
            self._decrease_indent()
    
    def _generate_block(self, node: ASTBlock) -> None:
        """生成代码块"""
        for child in node.nodes:
            self._generate_node(child)
    
    def _generate_if(self, node: ASTIf) -> None:
        """生成if语句"""
        is_nested = getattr(node, '_is_nested_if', False)

        # [关键修复] 检测复合条件模式
        # 如果当前if的body为空，且orelse包含一个if节点，可能是复合条件
        compound_test = self._detect_compound_condition(node)
        if compound_test:
            # 生成复合条件if语句
            test_code = self._generate_expression(compound_test)
            self._write_line(f'if {test_code}:')
            
            # 生成复合条件的body（从最后一个if节点获取）
            self._increase_indent()
            last_if = self._get_last_if_in_compound(node)
            if last_if and last_if.body and last_if.body.nodes:
                self._generate_block(last_if.body)
            else:
                self._write_line('pass')
            self._decrease_indent()
            
            # 处理复合条件的orelse
            if last_if and last_if.orelse and last_if.orelse.nodes:
                self._generate_elif_or_else(last_if.orelse)
            return
        
        # 生成普通if语句
        # [关键修复] 使用最低优先级(0)来避免if条件添加最外层括号
        test_code = self._generate_expression(node.test, 0)
        self._write_line(f'if {test_code}:')
        
        # [关键修复] 增加if深度计数
        self._if_depth += 1
        
        # 生成then分支
        self._increase_indent()
        if node.body and node.body.nodes:
            self._generate_block(node.body)
        else:
            self._write_line('pass')
        self._decrease_indent()
        
        # [关键修复] 减少if深度计数
        self._if_depth -= 1
        
        # [关键修复] 处理elif和else分支
        if node.orelse and node.orelse.nodes:
            # [关键修复] 检测elif模式：如果orelse的第一个节点是ASTIf
            # 且该if节点有实际的body内容
            # [关键修复] 但如果if节点有_is_nested_if标记，不应该作为elif处理
            first_node = node.orelse.nodes[0]
            # [关键修复-2026-elif-else] 检查这个if是否实际上是else分支中的嵌套if
            # 特征：如果这个If节点的test是常量True或简单变量（如redata），
            # 且它不是从elif_conditions来的，则可能是else中的嵌套if
            is_likely_nested_if_in_else = False
            if isinstance(first_node, ASTIf) and first_node.body and first_node.body.nodes \
                    and not getattr(first_node, '_is_nested_if', False) \
                    and not getattr(first_node, '_is_elif', False):
                test_is_simple = self._test_is_simple_variable(first_node.test)
                if test_is_simple:
                    is_likely_nested_if_in_else = True
            
            if isinstance(first_node, ASTIf) and first_node.body and first_node.body.nodes \
                    and not getattr(first_node, '_is_nested_if', False) \
                    and not is_likely_nested_if_in_else:
                # 生成elif
                # [关键修复] 使用优先级0避免在elif条件中添加不必要的括号
                elif_test_code = self._generate_expression(first_node.test, 0)
                self._write_line(f'elif {elif_test_code}:')
                
                # 生成elif的body
                # [关键修复] 临时增加if深度，确保elif body中的self-assignment不会被跳过
                self._if_depth += 1
                self._increase_indent()
                self._generate_block(first_node.body)
                self._decrease_indent()
                self._if_depth -= 1
                
                # 递归处理elif的orelse（可能是另一个elif或else）
                if first_node.orelse and first_node.orelse.nodes:
                    self._generate_elif_or_else(first_node.orelse)
                
                # [关键修复] 处理orelse中剩余的节点（非elif部分）
                if len(node.orelse.nodes) > 1:
                    remaining_nodes = node.orelse.nodes[1:]
                    # [关键修复] 过滤掉与elif条件重复的嵌套if
                    remaining_nodes = self._filter_duplicate_if_in_else(remaining_nodes, node.orelse.nodes)
                    # 过滤掉只包含return None的节点
                    filtered_nodes = [n for n in remaining_nodes if not self._is_only_return_none([n])]
                    if filtered_nodes:
                        # 生成else
                        self._write_line('else:')
                        self._increase_indent()
                        for n in filtered_nodes:
                            self._generate_node(n)
                        self._decrease_indent()
            else:
                # [关键修复] 只有当else块有实际内容时才生成else
                # [修复] 不过滤return None，因为这在某些情况下是有意义的逻辑分支
                # 例如：if x is None: return None; else: return str(x)
                
                # [关键修复-2026] 如果then分支以continue/break结束，
                # 且当前在循环体内，则else块实际上是循环体的后续代码，
                # 不应该作为if-else的一部分，而是直接输出到当前层级
                should_generate_else = True
                if node.body and node.body.nodes:
                    last_then_node = node.body.nodes[-1]
                    if isinstance(last_then_node, (ASTContinue, ASTBreak)) and self._loop_depth > 0:
                        should_generate_else = False
                
                if node.orelse.nodes:
                    if should_generate_else:
                        filtered_else_nodes = node.orelse.nodes
                        if filtered_else_nodes:
                            self._write_line('else:')
                            self._increase_indent()
                            for n in filtered_else_nodes:
                                self._generate_node(n)
                            self._decrease_indent()
                    else:
                        filtered_else_nodes = node.orelse.nodes
                        for n in filtered_else_nodes:
                            self._generate_node(n)
        
        # [关键修复] 处理final_else（嵌套的if结构）
        final_else = getattr(node, 'final_else', None)
        if final_else and final_else.nodes:
            # [关键修复] 如果then分支不以return结尾，需要生成else关键字
            then_ends_with_return = bool(node.body and node.body.nodes and 
                isinstance(node.body.nodes[-1], ASTReturn))
            
            if not then_ends_with_return and not (node.orelse and node.orelse.nodes):
                self._write_line('else:')
                self._increase_indent()
            
            for n in final_else.nodes:
                self._generate_node(n)
            
            if not then_ends_with_return and not (node.orelse and node.orelse.nodes):
                self._decrease_indent()
    
    def _filter_duplicate_if_in_else(self, else_nodes: List[Any], all_nodes: List[Any]) -> List[Any]:
        """
        [关键修复] 过滤掉else分支中与elif条件重复的嵌套if
        
        这种情况发生在结构化分析错误地将elif识别为嵌套的if时。
        例如：
        if x > 10:
            result = '大于10'
        elif x == 10:
            result = '等于10'
        else:
            result = '小于10'
            if x == 10:  # <- 这是重复的，应该被过滤掉
                result = '等于10'
        """
        if not else_nodes:
            return []
        
        # 收集所有elif的条件
        elif_conditions = set()
        for node in all_nodes:
            if isinstance(node, ASTIf) and node.test:
                # 提取条件表达式
                test_str = self._get_condition_str(node.test)
                if test_str:
                    elif_conditions.add(test_str)
        
        # 过滤掉与elif条件重复的嵌套if
        filtered = []
        for node in else_nodes:
            if isinstance(node, ASTIf) and node.test:
                test_str = self._get_condition_str(node.test)
                if test_str in elif_conditions:
                    # 这是重复的if，跳过
                    continue
            filtered.append(node)
        
        return filtered
    
    def _get_condition_str(self, test) -> str:
        """获取条件表达式的字符串表示"""
        if test is None:
            return ""
        if isinstance(test, ASTCompare):
            # 比较表达式
            left = self._get_operand_str(test.left)
            right = self._get_operand_str(test.comparators[0]) if test.comparators else ""
            op = test.ops[0] if test.ops else ""
            return f"{left} {op} {right}"
        elif isinstance(test, ASTName):
            return test.name if hasattr(test, 'name') else str(test)
        elif isinstance(test, ASTConstant):
            return str(test.value)
        return ""
    
    def _get_operand_str(self, operand) -> str:
        """获取操作数的字符串表示"""
        if operand is None:
            return ""
        if isinstance(operand, ASTName):
            return operand.name if hasattr(operand, 'name') else str(operand)
        elif isinstance(operand, ASTConstant):
            return str(operand.value)
        return ""
    
    def _test_is_simple_variable(self, test) -> bool:
        """[关键修复-2026] 检查test是否是简单的变量或常量"""
        from core.ast_nodes import ASTName, ASTConstant, ASTAttribute
        if isinstance(test, (ASTName, ASTConstant)):
            return True
        if isinstance(test, ASTAttribute):
            return True
        return False
    
    def _detect_compound_condition(self, node: ASTIf) -> Optional[ASTBinary]:
        """
        检测复合条件模式（AND/OR条件链）
        
        [关键修复] 严格区分复合条件和elif链：
        - 复合条件：多个条件共享同一个else分支（跳转目标相同）
          特征：当前if的body为空，orelse中的if的body也为空，直到最后一个if有实际内容
        - elif链：每个条件有自己的else分支（跳转目标不同）
          特征：每个if的body都有实际内容
        
        关键区别：
        - 复合条件：所有中间条件的body为空，只有最后一个有内容，且所有条件共享同一个else分支
        - elif链：每个条件的body都有实际内容，每个条件有自己的else分支
        
        [关键修复] 当前禁用复合条件检测，因为它会错误地将elif链识别为复合条件
        复合条件应该在结构化分析阶段处理，而不是在代码生成阶段
        
        Returns:
            复合条件表达式（ASTBinary），如果不是复合条件则返回None
        """
        # [关键修复] 禁用代码生成阶段的复合条件检测
        # 复合条件应该在结构化分析阶段（structured_analyzer.py）处理
        # 这里只处理简单的复合条件模式（如 x > 0 and y > 0）
        # 复杂的复合条件（如 (x > 0 and y > 0) or (x < 0 and y < 0)）应该在结构化分析阶段处理
        
        # 检查当前if的body是否为空或只包含pass/return
        body_nodes = node.body.nodes if node.body else []
        if body_nodes and not all(
            isinstance(n, (ASTPass, ASTReturn)) or
            (isinstance(n, ASTExpr) and isinstance(n.value, ASTConstant) and n.value.value is None)
            for n in body_nodes
        ):
            return None
        
        # 检查orelse是否只包含一个if节点
        orelse_nodes = node.orelse.nodes if node.orelse else []
        if len(orelse_nodes) != 1 or not isinstance(orelse_nodes[0], ASTIf):
            return None
        
        next_if = orelse_nodes[0]
        
        # [关键修复] 检查下一个if的body是否为空
        # 如果body不为空，这可能是elif链，不是复合条件
        next_body = next_if.body.nodes if next_if.body else []
        if next_body and not all(
            isinstance(n, (ASTPass, ASTReturn)) or
            (isinstance(n, ASTExpr) and isinstance(n.value, ASTConstant) and n.value.value is None)
            for n in next_body
        ):
            # 下一个if有实际内容，这是elif链，不是复合条件
            return None
        
        # [关键修复] 检查是否有更深层的if链
        # 如果next_if的orelse包含另一个if，且那个if有实际内容，这是elif链
        next_orelse = next_if.orelse.nodes if next_if.orelse else []
        if len(next_orelse) == 1 and isinstance(next_orelse[0], ASTIf):
            deeper_if = next_orelse[0]
            deeper_body = deeper_if.body.nodes if deeper_if.body else []
            if deeper_body and not all(
                isinstance(n, (ASTPass, ASTReturn)) or
                (isinstance(n, ASTExpr) and isinstance(n.value, ASTConstant) and n.value.value is None)
                for n in deeper_body
            ):
                # 更深层的if有实际内容，这是elif链，不是复合条件
                return None
        
        # 递归检测复合条件链
        conditions = [node.test]
        current = next_if
        
        while current:
            # 检查当前if的body是否为空或只包含pass/return
            current_body = current.body.nodes if current.body else []
            if current_body and not all(
                isinstance(n, (ASTPass, ASTReturn)) or
                (isinstance(n, ASTExpr) and isinstance(n.value, ASTConstant) and n.value.value is None)
                for n in current_body
            ):
                # 这是最后一个有实际内容的条件，结束链
                conditions.append(current.test)
                break
            
            # 这是中间条件，继续链
            conditions.append(current.test)
            
            # 检查是否有更多的条件
            current_orelse = current.orelse.nodes if current.orelse else []
            if len(current_orelse) == 1 and isinstance(current_orelse[0], ASTIf):
                current = current_orelse[0]
            else:
                # 链结束，但最后一个条件的body为空
                # 这不是有效的复合条件
                return None
        
        # 构建复合条件表达式
        if len(conditions) >= 2:
            # 使用AND连接所有条件
            result = conditions[0]
            for cond in conditions[1:]:
                result = ASTBinary(result, cond, ASTBinary.BinOp.BIN_LOG_AND)
            return result
        
        return None
    
    def _get_last_if_in_compound(self, node: ASTIf) -> Optional[ASTIf]:
        """
        获取复合条件链中的最后一个if节点
        
        Args:
            node: 复合条件的第一个if节点
            
        Returns:
            最后一个if节点
        """
        current = node
        
        while current:
            orelse_nodes = current.orelse.nodes if current.orelse else []
            if len(orelse_nodes) == 1 and isinstance(orelse_nodes[0], ASTIf):
                next_if = orelse_nodes[0]
                # 检查是否是复合条件的一部分
                body_nodes = current.body.nodes if current.body else []
                if (not body_nodes or all(
                    isinstance(n, (ASTPass, ASTReturn)) or
                    (isinstance(n, ASTExpr) and isinstance(n.value, ASTConstant) and n.value.value is None)
                    for n in body_nodes
                )):
                    current = next_if
                else:
                    break
            else:
                break
        
        return current
    
    def _generate_elif_or_else(self, orelse: ASTBlock) -> None:
        """生成elif或else分支"""
        if not orelse or not orelse.nodes:
            return
        
        # [关键修复] 处理elif链：连续的ASTIf节点都应该被视为elif
        # 第一个节点是ASTIf，生成elif
        # [关键修复] 但如果if节点有_is_nested_if标记，应该作为独立的if语句处理
        if isinstance(orelse.nodes[0], ASTIf):
            # [关键修复] 检查是否是嵌套的if（不是elif）
            if getattr(orelse.nodes[0], '_is_nested_if', False):
                # 这是嵌套的if，应该作为else块中的独立if语句处理
                filtered_nodes = [n for n in orelse.nodes if not self._is_only_return_none([n])]
                if filtered_nodes:
                    self._write_line('else:')
                    self._increase_indent()
                    for n in filtered_nodes:
                        self._generate_node(n)
                    self._decrease_indent()
                return
            
            # [关键修复-2026-elif-else] 检查是否是else分支中的嵌套if（不是elif）
            # 如果test是简单变量（如redata），则可能是else中的嵌套if
            _elif_node = orelse.nodes[0]
            if self._test_is_simple_variable(_elif_node.test) and not getattr(_elif_node, '_is_elif', False):
                # 是简单变量，当作else中的嵌套if处理
                filtered_nodes = [n for n in orelse.nodes if not self._is_only_return_none([n])]
                if filtered_nodes:
                    self._write_line('else:')
                    self._increase_indent()
                    for n in filtered_nodes:
                        self._generate_node(n)
                    self._decrease_indent()
                return
            
            elif_node = orelse.nodes[0]
            # [关键修复] 使用0作为parent_precedence，避免elif条件添加括号
            elif_test_code = self._generate_expression(elif_node.test, 0)
            self._write_line(f'elif {elif_test_code}:')
            
            # 生成elif的body
            self._increase_indent()
            if elif_node.body and elif_node.body.nodes:
                self._generate_block(elif_node.body)
            else:
                self._write_line('pass')
            self._decrease_indent()
            
            # [关键修复] 递归处理elif的orelse
            # 如果orelse中还有ASTIf节点，继续作为elif处理
            # [关键修复] 使用orelse.nodes[1:]作为剩余的节点，避免重复处理
            if len(orelse.nodes) > 1:
                remaining_nodes = orelse.nodes[1:]
                # 过滤掉只包含return None的节点
                filtered_nodes = [n for n in remaining_nodes if not self._is_only_return_none([n])]
                if filtered_nodes:
                    # 检查剩余的节点是否都是ASTIf（另一个elif链）
                    if all(isinstance(n, ASTIf) for n in filtered_nodes):
                        # 递归处理剩余的elif节点
                        for elif_n in filtered_nodes:
                            elif_ast = ASTBlock([elif_n])
                            self._generate_elif_or_else(elif_ast)
                    else:
                        # 生成else
                        self._write_line('else:')
                        self._increase_indent()
                        for n in filtered_nodes:
                            self._generate_node(n)
                        self._decrease_indent()
            elif elif_node.orelse and elif_node.orelse.nodes:
                # [关键修复] 只有当orelse.nodes中没有剩余节点时，才处理elif_node.orelse
                # 这样可以避免重复处理else分支
                self._generate_elif_or_else(elif_node.orelse)
        else:
            # [关键修复] 只有当else块有实际内容时才生成else
            # 过滤掉只包含return None的节点
            filtered_nodes = [n for n in orelse.nodes if not self._is_only_return_none([n])]
            # [关键修复] 过滤掉与elif条件重复的嵌套if
            filtered_nodes = self._filter_duplicate_if_in_else(filtered_nodes, orelse.nodes)
            if filtered_nodes:
                self._write_line('else:')
                self._increase_indent()
                for n in filtered_nodes:
                    self._generate_node(n)
                self._decrease_indent()
    
    def _generate_for(self, node: ASTFor) -> None:
        """生成for循环"""
        # 生成for行
        # [关键修复] 使用0作为parent_precedence，避免循环变量被添加括号
        # 例如: for i in data: 而不是 for (i) in (data):
        target_code = self._generate_for_target(node.target)
        iter_code = self._generate_expression(node.iter, 0)
        # [关键修复] 根据is_async标记决定是for还是async for
        async_keyword = 'async for' if getattr(node, 'is_async', False) else 'for'
        self._write_line(f'{async_keyword} {target_code} in {iter_code}:')

        # 生成循环体
        self._increase_indent()
        self._loop_depth += 1  # [关键修复] 进入循环
        try:
            if node.body and node.body.nodes:
                self._generate_block(node.body)
            else:
                self._write_line('pass')
        finally:
            self._loop_depth -= 1  # [关键修复] 退出循环
        self._decrease_indent()

        # 生成else分支
        # [关键修复] 使用else_block而不是orelse
        else_block = getattr(node, 'else_block', None)
        if else_block and else_block.nodes:
            # [关键修复] 对于async for循环，else分支中的return None是合法的，不应该被跳过
            is_async_for = getattr(node, 'is_async', False)
            if not is_async_for and self._is_only_return_none(else_block.nodes):
                pass  # 跳过只包含return None的else分支（仅对普通for循环）
            else:
                self._write_line('else:')
                self._increase_indent()
                self._generate_block(else_block)
                self._decrease_indent()

    def _generate_for_target(self, target) -> str:
        """
        [关键修复] 生成for循环目标变量代码
        
        对于for循环目标，不应该添加括号：
        - 单变量: for i in data: （不是 for (i) in (data):）
        - 元组解包: for a, b in data: （不是 for (a, b) in (data):）
        """
        if isinstance(target, ASTName):
            name = target.name if hasattr(target, 'name') else str(target)
            if name == '<target>':
                return '_item'
            return name
        elif isinstance(target, ASTTuple):
            if not target.elts:
                return '()'
            elts_code = [self._generate_for_target(elt) for elt in target.elts]
            return ', '.join(elts_code)
        else:
            return self._generate_expression(target, 0)

    def _generate_for_target_from_dict(self, target: Dict[str, Any]) -> str:
        """[N14修复] 为字典格式AST生成for循环目标（无括号）"""
        if not target:
            return '_'
        
        node_type = target.get('type')
        
        if node_type == 'Name':
            return target.get('id', '_')
        elif node_type == 'Tuple':
            elts = target.get('elts', [])
            if not elts:
                return '()'
            elts_code = [self._generate_for_target_from_dict(elt) for elt in elts]
            return ', '.join(elts_code)
        elif node_type in ('List', 'Starred'):
            inner = self._generate_for_target_from_dict(target.get('value', target.get('values', {})))
            if node_type == 'Starred':
                return f'*{inner}'
            return f'[{inner}]'
        else:
            return self._generate_expression(target, 0)

    def _is_only_return_none(self, nodes: List[Any]) -> bool:
        """[关键修复] 检查节点列表是否只包含return None"""
        if not nodes:
            return False
        # 过滤掉ASTBlock包装
        flattened = []
        for n in nodes:
            if isinstance(n, ASTBlock):
                flattened.extend(n.nodes)
            else:
                flattened.append(n)
        
        if len(flattened) != 1:
            return False
        
        node = flattened[0]
        if isinstance(node, ASTReturn):
            if node.value is None:
                return True
            if hasattr(node.value, 'value') and node.value.value is None:
                return True
        return False
    
    def _is_isnot_condition(self, test: Any) -> bool:
        """[关键修复] 检查是否是 IsNot 条件（如 x is not None）"""
        if isinstance(test, ASTCompare):
            # ASTCompare 使用 CompareOp 枚举，CMP_IS_NOT = 9
            return test.op == 9 or test.op_str() == 'is not'
        return False
    
    def _invert_isnot_to_is(self, test: ASTCompare) -> ASTCompare:
        """[关键修复] 将 IsNot 条件转换为 Is 条件"""
        # 创建新的 Compare 节点，将 IsNot 改为 Is (CMP_IS = 8)
        new_test = ASTCompare(
            left=test.left,
            comparators=test.comparators,
            ops=[8]  # CMP_IS = 8
        )
        return new_test
    
    def _generate_while(self, node) -> None:
        """生成while循环"""
        # 生成while行
        # [关键修复] 使用0作为parent_precedence，避免条件被添加括号
        # 例如: while temp > 0: 而不是 while (temp > 0):
        test_code = self._generate_expression(node.get('test') if isinstance(node, dict) else node.test, 0)
        self._write_line(f'while {test_code}:')

        # 生成循环体
        self._increase_indent()
        self._loop_depth += 1  # [关键修复] 进入循环
        try:
            # [关键修复-2026] 支持两种格式：ASTBlock对象和字典列表
            body = node.get('body') if isinstance(node, dict) else node.body
            
            if body:
                if hasattr(body, 'nodes') and body.nodes:
                    # ASTBlock对象
                    self._generate_block(body)
                elif isinstance(body, list) and len(body) > 0:
                    # 字典列表（来自ast_generator_v2.py）
                    for child in body:
                        self._generate_node(child)
                else:
                    self._write_line('pass')
            else:
                self._write_line('pass')
        finally:
            self._loop_depth -= 1  # [关键修复] 退出循环
        self._decrease_indent()

        # 生成else分支
        orelse = node.get('orelse') if isinstance(node, dict) else (node.orelse if hasattr(node, 'orelse') else None)
        if orelse:
            if hasattr(orelse, 'nodes') and orelse.nodes:
                self._write_line('else:')
                self._increase_indent()
                self._generate_block(orelse)
                self._decrease_indent()
            elif isinstance(orelse, list) and len(orelse) > 0:
                self._write_line('else:')
                self._increase_indent()
                for child in orelse:
                    self._generate_node(child)
                self._decrease_indent()
    
    def _generate_try(self, node: ASTTry) -> None:
        """生成try-except语句"""
        # 生成try行
        self._write_line('try:')
        
        # 生成try体
        self._increase_indent()
        if node.body and node.body.nodes:
            self._generate_block(node.body)
        else:
            self._write_line('pass')
        self._decrease_indent()
        
        # 生成except handlers
        for handler in node.handlers:
            self._generate_except_handler(handler)
        
        # 生成else分支
        if node.orelse and node.orelse.nodes:
            self._write_line('else:')
            self._increase_indent()
            self._generate_block(node.orelse)
            self._decrease_indent()
        
        # 生成finally分支
        if node.finalbody and node.finalbody.nodes:
            self._write_line('finally:')
            self._increase_indent()
            self._generate_block(node.finalbody)
            self._decrease_indent()
    
    def _generate_except_handler(self, handler: ASTExceptHandler) -> None:
        """生成except handler"""
        # [关键修复] ASTExceptHandler使用exc_type而不是type
        exc_type = handler.exc_type
        if exc_type:
            if hasattr(exc_type, 'to_code'):
                type_code = exc_type.to_code()
            elif hasattr(exc_type, 'name'):
                type_code = exc_type.name
            else:
                type_code = str(exc_type)
        else:
            # [修复] 裸except不指定异常类型
            type_code = None
        
        # [关键修复] 检查是否是 except* 语法（异常组）
        is_except_star = getattr(handler, 'is_except_star', False)
        except_keyword = 'except*' if is_except_star else 'except'
        
        # [修复] 记录except的as变量名，用于区分清理代码和用户代码
        if handler.name:
            self._except_as_vars.add(handler.name)
        
        if type_code:
            if handler.name:
                self._write_line(f'{except_keyword} {type_code} as {handler.name}:')
            else:
                self._write_line(f'{except_keyword} {type_code}:')
        else:
            # 裸except
            if handler.name:
                self._write_line(f'{except_keyword} Exception as {handler.name}:')
            else:
                self._write_line(f'{except_keyword}:')
        
        self._increase_indent()
        if handler.body and handler.body.nodes:
            self._generate_block(handler.body)
        else:
            self._write_line('pass')
        self._decrease_indent()
    
    def _generate_with(self, node: ASTWith) -> None:
        """生成with语句"""
        # 生成with行
        items_code = []
        for item in node.items:
            item_code = self._generate_with_item(item)
            items_code.append(item_code)
        
        # [关键修复] 检查是否是异步with
        is_async = getattr(node, '_is_async', False) or getattr(node, 'is_async', False)
        async_prefix = 'async ' if is_async else ''
        
        self._write_line(f'{async_prefix}with {", ".join(items_code)}:')
        
        # 生成with体
        self._increase_indent()
        if node.body and node.body.nodes:
            self._generate_block(node.body)
        else:
            self._write_line('pass')
        self._decrease_indent()
    
    def _generate_with_item(self, item: ASTWithItem) -> str:
        """生成with item代码"""
        # [关键修复] 使用较低的优先级，避免在with语句中添加不必要的括号
        context_code = self._generate_expression(item.context_expr, parent_precedence=1)
        
        if item.optional_vars:
            # [关键修复] 使用parent_precedence=0避免给变量名添加括号
            vars_code = self._generate_expression(item.optional_vars, parent_precedence=0)
            return f'{context_code} as {vars_code}'
        else:
            return context_code
    
    def _generate_function_def(self, node: ASTFunctionDef) -> None:
        """生成函数定义"""
        # [关键修复] 检查是否是lambda函数（名称为<lambda>）
        if node.name == '<lambda>':
            # 生成lambda表达式
            self._generate_lambda_expr(node)
            return
        
        # 处理装饰器
        decorators = node.decorators if hasattr(node, 'decorators') else []
        for decorator in decorators:
            decorator_code = self._generate_decorator(decorator)
            self._write_line(f'@{decorator_code}')
        
        # [异步] 检查是否是异步函数
        is_async = getattr(node, '_is_async', False) or getattr(node, 'is_async', False)
        async_prefix = 'async ' if is_async else ''
        
        # [关键修复] 将args、vararg、kwarg包装成字典传递给_generate_arguments
        # [关键修复] 包含默认值信息
        args_dict = {
            'args': node.args if node.args else [],
            'vararg': getattr(node, '_vararg', None),
            'kwarg': getattr(node, '_kwarg', None),
            'defaults': getattr(node, '_defaults', []),
            'kwonlyargs': getattr(node, '_kwonlyargs', []),
            'kw_defaults': getattr(node, '_kw_defaults', [])
        }
        args_code = self._generate_arguments(args_dict)
        
        if node.returns:
            # [关键修复] 处理返回类型注解（可能是ASTNode或字典）
            if isinstance(node.returns, dict):
                returns_code = self._generate_annotation_from_dict(node.returns)
            elif isinstance(node.returns, ASTNode):
                # [关键修复] 对于单元素元组返回类型，去掉括号
                # 例如 -> str 而不是 -> (str,)
                if isinstance(node.returns, ASTTuple) and len(node.returns.elts) == 1:
                    returns_code = self._generate_expression(node.returns.elts[0], 0)
                elif isinstance(node.returns, ASTSubscript):
                    # [关键修复] 对于ASTSubscript类型的返回类型，使用注解生成逻辑
                    # 这确保Callable[[arg], ret]格式正确
                    returns_code = self._generate_subscript_annotation(node.returns)
                else:
                    # [关键修复] 使用优先级0避免在返回类型注解中添加不必要的括号
                    returns_code = self._generate_expression(node.returns, 0)
            else:
                returns_code = str(node.returns)
            self._write_line(f'{async_prefix}def {node.name}({args_code}) -> {returns_code}:')
        else:
            self._write_line(f'{async_prefix}def {node.name}({args_code}):')
        
        # 生成函数体
        self._increase_indent()
        self._function_depth += 1  # 进入函数内部
        # [关键修复-2026] 保存并重置pending声明列表
        saved_globals = self._pending_globals
        saved_nonlocals = self._pending_nonlocals
        self._pending_globals = []
        self._pending_nonlocals = []
        try:
            if node.body and node.body.nodes:
                filtered_nodes = self._filter_trailing_return_none(node.body.nodes)
                if filtered_nodes:
                    filtered_body = ASTBlock(filtered_nodes)
                    self._generate_block(filtered_body)
                else:
                    self._write_line('pass')
            else:
                self._write_line('pass')
        finally:
            self._function_depth -= 1
            self._pending_globals = saved_globals
            self._pending_nonlocals = saved_nonlocals
        self._decrease_indent()
    
    def _filter_trailing_return_none(self, nodes: List[Any]) -> List[Any]:
        """[关键修复] 过滤掉函数末尾的return None语句和return之后的死代码
        
        [注意] 函数末尾的隐式return None不需要在源码中显式写出：
        - 非生成器函数：有无return None字节码相同
        - 生成器函数：有return会改变字节码（减少死代码return），因此必须过滤
        
        [关键修复-2026-while-exit] 但是，对于包含while循环的函数，
        while循环后的return None会影响字节码（因为循环回跳指令的目标不同），
        所以不应该过滤这种情况下的return None
        """
        if not nodes:
            return nodes
        
        # [关键修复-2026-while-exit] 检查是否包含while循环
        # 如果包含，则不过滤末尾的return None
        from core.ast_nodes import ASTWhile
        has_while_loop = any(
            isinstance(node, ASTWhile) or
            (isinstance(node, dict) and node.get('type') == 'While') or
            (hasattr(node, 'node_type') and getattr(node, 'node_type', None) == 'While')
            for node in nodes
        )
        
        # [关键修复] 首先过滤掉return之后的所有死代码
        # 找到第一个return语句的位置
        return_idx = -1
        for i, node in enumerate(nodes):
            if isinstance(node, ASTReturn):
                return_idx = i
                break
            elif isinstance(node, ASTBlock):
                # 递归检查ASTBlock内部
                filtered = self._filter_trailing_return_none(node.nodes)
                # 如果内部有return，截断到此位置
                if len(filtered) < len(node.nodes):
                    return nodes[:i] + [ASTBlock(filtered)]
        
        # 如果找到了return，只保留到return为止的代码
        if return_idx >= 0:
            nodes = nodes[:return_idx + 1]
        
        # [关键修复] 过滤掉函数末尾的return None
        # 对于生成器函数，显式return会改变字节码，必须过滤
        # 对于普通函数，return None是隐式的，过滤后字节码不变
        # [关键修复-2026-while-exit] 但对于包含while循环的函数，不过滤
        if nodes and isinstance(nodes[-1], ASTReturn):
            last_return = nodes[-1]
            if last_return.value is None or (isinstance(last_return.value, ASTConstant) and last_return.value.value is None):
                # [关键修复-2026-while-exit] 如果包含while循环，不过滤return None
                if not has_while_loop:
                    nodes = nodes[:-1]
        
        return nodes
    
    def _generate_lambda_expr(self, node: ASTFunctionDef) -> None:
        """[关键修复] 生成lambda表达式"""
        # 生成参数列表
        args_code = self._generate_arguments(node.args)
        
        # 生成lambda体（应该是单个表达式）
        body_code = None
        if node.body and node.body.nodes:
            # 过滤掉末尾的return None
            filtered_nodes = self._filter_trailing_return_none(node.body.nodes)
            if filtered_nodes:
                # lambda体应该是一个表达式或简单的return语句
                body_node = filtered_nodes[0]
                if isinstance(body_node, ASTReturn) and body_node.value:
                    # return语句，提取返回值
                    body_code = self._generate_expression(body_node.value)
                elif isinstance(body_node, ASTExpr) and body_node.value:
                    # 表达式语句
                    body_code = self._generate_expression(body_node.value)
                else:
                    # 其他情况，尝试生成代码
                    body_code = self._generate_node_code(body_node)
        
        if body_code:
            self._write_line(f'lambda {args_code}: {body_code}')
        else:
            self._write_line(f'lambda {args_code}: None')
    
    def _generate_node_code(self, node: ASTNode) -> str:
        """[关键修复] 生成节点的代码字符串"""
        if isinstance(node, ASTExpr):
            return self._generate_expression(node.value)
        elif isinstance(node, ASTReturn):
            if node.value:
                return self._generate_expression(node.value)
            else:
                return 'None'
        elif isinstance(node, ASTConstant):
            return repr(node.value)
        elif isinstance(node, ASTName):
            return node.id
        else:
            # 对于其他类型，尝试生成表达式
            try:
                return self._generate_expression(node)
            except:
                return 'None'
    
    def _generate_decorator(self, node: ASTNode) -> str:
        """生成装饰器表达式（不使用括号包装）"""
        if isinstance(node, ASTCall):
            # 装饰器调用：直接生成调用表达式，不使用优先级包装
            func_code = self._generate_decorator(node.func)
            args_code = []
            
            # 处理位置参数
            pparams = node.pparams if hasattr(node, 'pparams') else []
            for arg in pparams:
                # [关键修复] 使用parent_precedence=0避免给常量添加括号
                arg_code = self._generate_expression(arg, parent_precedence=0)
                args_code.append(arg_code)
            
            # [关键修复] 处理关键字参数
            kwparams = node.kwparams if hasattr(node, 'kwparams') else []
            for kw in kwparams:
                # [关键修复] ASTKeyword的属性是name而不是arg
                if hasattr(kw, 'name') and hasattr(kw, 'value'):
                    kw_name = kw.name
                    # [关键修复] 使用parent_precedence=0避免给常量添加括号
                    kw_value = self._generate_expression(kw.value, parent_precedence=0)
                    args_code.append(f'{kw_name}={kw_value}')
            
            if args_code:
                return f'{func_code}({", ".join(args_code)})'
            else:
                return func_code
        elif isinstance(node, ASTName):
            return node.name if hasattr(node, 'name') else str(node)
        elif isinstance(node, ASTAttribute):
            value_code = self._generate_decorator(node.value)
            return f'{value_code}.{node.attr}'
        else:
            # 其他类型使用普通表达式生成
            return self._generate_expression(node)
    
    def _filter_return_nodes(self, nodes: List[Any]) -> List[Any]:
        """递归过滤掉类体级别的return节点（不是方法内的return）"""
        filtered = []
        for n in nodes:
            if isinstance(n, ASTReturn):
                # [关键修复] 只过滤类体级别的return，不过滤方法内的return
                # 类体级别的return不应该存在，但方法内的return应该保留
                # 通过检查节点是否在函数定义内来判断
                # 这里我们保留return，让_generate_return方法来处理是否在函数内
                filtered.append(n)
            elif isinstance(n, ASTFunctionDef):
                # [关键修复] 对于函数定义，保留其完整的body，包括return
                filtered.append(n)
            elif isinstance(n, ASTBlock):
                # 递归过滤ASTBlock中的节点
                filtered_block = ASTBlock(self._filter_return_nodes(n.nodes))
                if filtered_block.nodes:
                    filtered.append(filtered_block)
            else:
                # 对于其他节点，不修改原始节点，直接添加
                filtered.append(n)
        return filtered
    
    def _filter_class_internal_assigns(self, nodes: List[Any]) -> List[Any]:
        """[关键修复] 过滤类定义中的内部属性赋值（__module__, __qualname__, __classcell__等）
        
        注意: __doc__ 不是内部属性，它是类的文档字符串，应该被保留
        """
        filtered = []
        # [关键修复] 从 internal_names 中移除 '__doc__'，因为文档字符串应该被保留
        internal_names = {'__module__', '__qualname__', '__classcell__'}
        for n in nodes:
            if isinstance(n, ASTAssign):
                # 检查赋值目标是否是内部属性
                targets = n.targets if hasattr(n, 'targets') else []
                is_internal = False
                for target in targets:
                    if isinstance(target, ASTName) and target.name in internal_names:
                        is_internal = True
                        break
                # [关键修复] 保留 __doc__ 赋值（类文档字符串）
                if not is_internal:
                    filtered.append(n)
            elif isinstance(n, ASTReturn):
                # [关键修复] 过滤类定义中的内部return语句（如 __classcell__ 相关）
                # 检查return的值是否包含内部变量
                if n.value:
                    value_str = str(n.value)
                    if '__classcell__' in value_str or '__class__' in value_str:
                        continue
                # 也过滤掉返回None的return（类定义末尾的隐式return）
                if n.value and hasattr(n.value, 'value') and n.value.value is None:
                    continue
                filtered.append(n)
            elif isinstance(n, ASTExpr):
                # [关键修复] 过滤类定义中的空元组表达式（内部使用）
                if n.value and hasattr(n.value, 'elts') and len(n.value.elts) == 0:
                    continue
                # [关键修复] 过滤类定义中的类型注解元组表达式
                # 这些注解应该作为函数注解，而不是独立语句
                # 例如: ('data', List[int], 'return', None) 是函数注解的内部表示
                if n.value and hasattr(n.value, 'elts'):
                    elts = n.value.elts
                    # 检查是否是注解元组: 包含字符串和类型注解的交替模式
                    if len(elts) >= 2 and len(elts) % 2 == 0:
                        is_annotation_tuple = True
                        for i in range(0, len(elts), 2):
                            # 奇数位置应该是字符串（如 'data', 'return'）
                            if i < len(elts) and not (isinstance(elts[i], ASTConstant) and 
                                                       isinstance(elts[i].value, str)):
                                is_annotation_tuple = False
                                break
                        if is_annotation_tuple:
                            continue
                filtered.append(n)
            elif isinstance(n, ASTBlock):
                # 递归过滤ASTBlock中的节点
                filtered_block = ASTBlock(self._filter_class_internal_assigns(n.nodes))
                if filtered_block.nodes:
                    filtered.append(filtered_block)
            else:
                filtered.append(n)
        return filtered
    
    def _generate_class_def(self, node: ASTClassDef) -> None:
        """生成类定义"""
        # 处理装饰器
        decorators = node.decorators if hasattr(node, 'decorators') else []
        for decorator in decorators:
            decorator_code = self._generate_decorator(decorator)
            self._write_line(f'@{decorator_code}')
        
        # 生成class行
        # [关键修复] 处理基类和关键字参数（如metaclass）
        bases_and_keywords = []
        
        # 添加基类
        if node.bases:
            for base in node.bases:
                # [关键修复] 使用parent_precedence=0避免给基类添加括号
                bases_and_keywords.append(self._generate_expression(base, parent_precedence=0))
        
        # [关键修复] 添加关键字参数（如metaclass=MetaClass）
        if hasattr(node, 'keywords') and node.keywords:
            for keyword in node.keywords:
                if isinstance(keyword, dict):
                    # 关键字参数是字典格式 {'type': 'keyword', 'arg': 'metaclass', 'value': {...}}
                    arg = keyword.get('arg', '')
                    value = keyword.get('value', {})
                    if arg and value:
                        value_code = self._generate_annotation_from_dict(value)
                        bases_and_keywords.append(f'{arg}={value_code}')
                elif hasattr(keyword, 'arg') and hasattr(keyword, 'value'):
                    # 关键字参数是ASTNode对象
                    arg = keyword.arg
                    value_code = self._generate_expression(keyword.value)
                    bases_and_keywords.append(f'{arg}={value_code}')
        
        # [关键修复] 处理类型参数（Python 3.12+ 泛型语法）
        type_params_code = ''
        if hasattr(node, 'type_params') and node.type_params:
            type_params_code = f"[{', '.join(node.type_params)}]"
        
        if bases_and_keywords:
            bases_code = ', '.join(bases_and_keywords)
            self._write_line(f'class {node.name}{type_params_code}({bases_code}):')
        else:
            # [关键修复] 没有基类时，不添加空括号
            self._write_line(f'class {node.name}{type_params_code}:')
        
        # 生成类体
        self._increase_indent()
        # [关键修复] ASTClassDef的body是列表，不是ASTBlock
        body_list = node.body if isinstance(node.body, list) else (node.body.nodes if hasattr(node.body, 'nodes') else [])
        if body_list:
            # [关键修复] 递归过滤掉类体中的return语句（类体函数的return应该被忽略）
            filtered_nodes = self._filter_return_nodes(body_list)
            # [关键修复] 过滤类定义中的内部属性赋值（__module__, __qualname__, __doc__等）
            filtered_nodes = self._filter_class_internal_assigns(filtered_nodes)
            
            if filtered_nodes:
                filtered_body = ASTBlock(filtered_nodes)
                self._generate_block(filtered_body)
            else:
                self._write_line('pass')
        else:
            self._write_line('pass')
        self._decrease_indent()
    
    def _generate_class_def_dict(self, node: Dict[str, Any]) -> None:
        name = node.get('name', 'Unknown')
        bases = node.get('bases', [])
        keywords = node.get('keywords', [])
        body = node.get('body', [])
        decorator_list = node.get('decorator_list', [])

        for dec in decorator_list:
            dec_code = self._generate_expression(dec) if isinstance(dec, dict) else str(dec)
            self._write_line(f'@{dec_code}')

        bases_and_keywords = []
        for base in bases:
            bases_and_keywords.append(self._generate_expression(base) if isinstance(base, dict) else str(base))
        for kw in keywords:
            if isinstance(kw, dict):
                arg = kw.get('arg', '')
                value = kw.get('value', {})
                if arg and value:
                    value_code = self._generate_expression(value) if isinstance(value, dict) else str(value)
                    bases_and_keywords.append(f'{arg}={value_code}')

        if bases_and_keywords:
            self._write_line(f'class {name}({", ".join(bases_and_keywords)}):')
        else:
            self._write_line(f'class {name}:')

        self._increase_indent()
        if body:
            for body_node in body:
                if isinstance(body_node, dict):
                    self._generate_dict_node(body_node)
                else:
                    self._generate_node(body_node)
        else:
            self._write_line('pass')
        self._decrease_indent()

    def _generate_return(self, node: ASTReturn) -> None:
        """生成return语句"""
        # 检查是否在函数内部
        if not self._in_function_context():
            # 在模块级别，如果在循环内部，将return None转换为break
            if self._loop_depth > 0:
                if node.value is None or (isinstance(node.value, ASTConstant) and node.value.value is None):
                    self._write_line('break')
                    return
            # 在模块级别且不在循环内部，完全忽略return语句
            return

        # [关键修复] 使用 node.value is not None 而不是 if node.value
        # 因为 node.value 可能是 False，这在布尔上下文中会被视为假
        if node.value is not None:
            # [关键修复] 使用0作为parent_precedence，避免返回值被添加括号
            value_code = self._generate_expression(node.value, 0)
            # [关键修复] 生成return None以保持字节码一致性
            if value_code == 'None':
                self._write_line('return None')
            else:
                self._write_line(f'return {value_code}')
        else:
            # [关键修复] 生成return None以保持字节码一致性
            self._write_line('return None')

    def _generate_yield(self, node: ASTYield) -> None:
        """生成yield语句"""
        if node.value:
            value_code = self._generate_expression(node.value)
            self._write_line(f'yield {value_code}')
        else:
            self._write_line('yield')

    def _generate_assign(self, node: ASTAssign) -> None:
        """生成赋值语句"""
        # ASTAssign使用_targets和_value
        if hasattr(node, 'targets') and node.targets:
            # [关键修复-2026] 链式赋值 a = b = c = 0
            if getattr(node, 'is_chain_assign', False) and len(node.targets) > 1:
                target_codes = [self._generate_expression(t, 0) for t in node.targets]
                target_code = ' = '.join(target_codes)
            elif len(node.targets) > 1:
                # 多目标：生成 a, b, c = value (元组解包)
                target_codes = []
                for target in node.targets:
                    if isinstance(target, ASTTuple) and len(target.elts) > 1:
                        elts_code = [self._generate_expression(elt, 0) for elt in target.elts]
                        target_codes.append(f'({", ".join(elts_code)})')
                    else:
                        target_codes.append(self._generate_expression(target, 0))
                target_code = ', '.join(target_codes)
            else:
                # 单目标
                target = node.targets[0]
                if isinstance(target, ASTTuple) and len(target.elts) > 1:
                    # 多元素元组作为赋值目标，生成 a, b, c 而不是 (a, b, c)
                    elts_code = [self._generate_expression(elt, 0) for elt in target.elts]
                    target_code = f'{", ".join(elts_code)}'
                else:
                    # [关键修复] 使用0作为parent_precedence，避免赋值目标被添加括号
                    target_code = self._generate_expression(target, 0)
        else:
            target_code = '<target>'

        # [关键修复] 跳过以@开头的内部变量（如@pytest_ar, @py_builtins等）
        if target_code.startswith('@'):
            return

        if hasattr(node, 'value'):
            # [禁用常量折叠] 为了保持字节码一致性，禁用常量折叠
            # 原始代码中的常量表达式已经被Python编译器优化
            # 如果反编译器再次进行常量折叠，会导致重新编译后的常量池顺序不同
            # 例如: a = True and False 原始编译后常量池为 [True, False, None]
            # 如果反编译器折叠为 a = False，重新编译后常量池为 [False, True, None]
            # 这会导致 LOAD_CONST 指令的参数不匹配
            # folded_value = self._fold_constant_expression(node.value)
            # if folded_value is not None:
            #     # 使用折叠后的常量值
            #     value_code = repr(folded_value)
            # else:
            #     # [关键修复] 使用0作为parent_precedence，避免赋值右边添加最外层括号
            #     value_code = self._generate_expression(node.value, 0)
            
            # [关键修复] 使用0作为parent_precedence，避免赋值右边添加最外层括号
            # [关键修复-2026] 处理 value 为 ASTSlice 的情况
            # Python中 Slice 不能作为独立的赋值值（如 x = a:b 是无效语法）
            if isinstance(node.value, ASTSlice):
                value_code = self._generate_slice_as_call(node.value)
            else:
                value_code = self._generate_expression(node.value, 0)
        else:
            value_code = '<value>'

        # [关键修复] 跳过导入相关的冗余赋值
        # 例如: defaultdict = defaultdict, sqrt = sqrt, List = List
        # 这些是由于导入语句后 STORE_NAME 生成的冗余代码
        # [关键修复] 但保留if语句中的self-assignment（如 if x: x = x）
        # 因为这些可能是原始代码逻辑的一部分
        if target_code == value_code:
            # 检查是否在if语句的body中
            # 如果是，保留这个赋值，因为它可能是原始代码逻辑
            # 如果不是（例如在模块级别），跳过它（可能是导入冗余）
            if not self._is_in_if_body():
                return
        
        # [关键修复] 跳过异常处理的清理代码
        # 例如: e = None（异常变量清理）
        # 这些代码是Python编译器生成的内部清理代码，不应该出现在反编译结果中
        # [修复] 但不能跳过except handler中的用户赋值（如 value = None）
        # 需要区分：异常变量清理（e = None，其中e是except的as变量）和用户代码
        if (hasattr(node, 'value') and isinstance(node.value, ASTConstant) and 
            node.value.value is None and target_code.isidentifier()):
            # 检查是否是except的as变量清理（如 except E as e: ... e = None）
            # 只有当target是except的as变量时才跳过
            is_except_var_cleanup = (target_code in self._except_as_vars)
            if is_except_var_cleanup:
                return

        # [关键修复-2026] 元组解包赋值优化
        # 当赋值目标是多元组，且值是常量元组/列表时，去掉值两边的括号
        # 例如: a, b, c = (1, 2, 3) → a, b, c = 1, 2, 3
        if (hasattr(node, 'value') and hasattr(node, 'targets') and len(node.targets) >= 1):
            first_target = node.targets[0]
            value_node = node.value
            
            # 检查是否是元组解包：目标是多元组，值是常量列表/元组
            if (isinstance(first_target, ASTTuple) and len(first_target.elts) > 1 and
                isinstance(value_node, ASTConstant) and 
                isinstance(value_node.value, (list, tuple)) and 
                len(value_node.value) > 1):
                if value_code.startswith('(') and value_code.endswith(')'):
                    value_code = value_code[1:-1]
                elif value_code.startswith('[') and value_code.endswith(']'):
                    value_code = value_code[1:-1]

        self._write_line(f'{target_code} = {value_code}')

    def _fold_constant_expression(self, expr: ASTNode) -> Any:
        """
        [常量折叠] 评估常量表达式并返回折叠后的值

        支持的表达式:
        - 常量: True, False, None, 数字, 字符串
        - 一元操作: not x
        - 二元逻辑操作: x and y, x or y

        如果表达式不是常量或无法折叠，返回None
        """
        if isinstance(expr, ASTConstant):
            return expr.value

        if isinstance(expr, ASTUnary):
            # 评估一元操作
            operand_value = self._fold_constant_expression(expr.operand)
            if operand_value is None:
                return None

            # 获取操作符
            op_value = expr.op.value if hasattr(expr.op, 'value') else expr.op

            # not 操作
            if op_value == 3:  # UN_NOT
                return not operand_value
            # + 操作
            elif op_value == 0:  # UN_POSITIVE
                return +operand_value
            # - 操作
            elif op_value == 1:  # UN_NEGATIVE
                return -operand_value
            # ~ 操作
            elif op_value == 2:  # UN_INVERT
                return ~operand_value

        if isinstance(expr, ASTBinary):
            # 评估二元操作
            left_value = self._fold_constant_expression(expr.left)
            right_value = self._fold_constant_expression(expr.right)

            # 只有两侧都是常量才能折叠
            if left_value is None or right_value is None:
                return None

            # 获取操作符
            if isinstance(expr.op, str):
                op_str = expr.op
            else:
                op_map = {
                    0: '.', 1: '**', 2: '*', 3: '/', 4: '//', 5: '%',
                    6: '+', 7: '-', 8: '<<', 9: '>>', 10: '&', 11: '^', 12: '|',
                    13: 'and', 14: 'or', 15: '@',
                }
                op_str = op_map.get(expr.op, '+')

            # 逻辑操作
            if op_str == 'and':
                return left_value and right_value
            elif op_str == 'or':
                return left_value or right_value

            # 算术操作
            try:
                if op_str == '+':
                    return left_value + right_value
                elif op_str == '-':
                    return left_value - right_value
                elif op_str == '*':
                    return left_value * right_value
                elif op_str == '/':
                    return left_value / right_value
                elif op_str == '//':
                    return left_value // right_value
                elif op_str == '%':
                    return left_value % right_value
                elif op_str == '**':
                    return left_value ** right_value
            except (TypeError, ZeroDivisionError):
                return None

        return None
    
    def _generate_aug_assign(self, node: ASTAugAssign) -> None:
        if hasattr(node, 'target'):
            target_code = self._generate_expression(node.target, 0)
        else:
            target_code = '<target>'

        if hasattr(node, 'op'):
            op = node.op
            if not op.endswith('='):
                op = op + '='
        else:
            op = '+='

        if hasattr(node, 'value'):
            value_code = self._generate_expression(node.value, 0)
        else:
            value_code = '<value>'

        self._write_line(f'{target_code} {op} {value_code}')
    
    def _generate_ann_assign(self, node: ASTAnnAssign) -> None:
        """生成带注解的赋值语句（如 name: str = value）"""
        # 获取目标代码
        if hasattr(node, 'target'):
            target_code = self._generate_expression(node.target, 0)
        else:
            target_code = '<target>'
        
        # 获取注解代码
        if hasattr(node, 'annotation'):
            annotation_code = self._generate_expression(node.annotation, 0)
        else:
            annotation_code = '<annotation>'
        
        # 获取值代码（如果有）
        if hasattr(node, 'value') and node.value is not None:
            value_code = self._generate_expression(node.value, 0)
            self._write_line(f'{target_code}: {annotation_code} = {value_code}')
        else:
            self._write_line(f'{target_code}: {annotation_code}')
    
    def _generate_expr_stmt(self, node: ASTExpr) -> None:
        """生成表达式语句"""
        # [关键修复] 过滤类型注解元组表达式
        # 这些注解应该作为函数注解，而不是独立语句
        # 例如: ('name', str, 'age', int, 'return', str) 是函数注解的内部表示
        if isinstance(node.value, ASTTuple):
            elts = node.value.elts if hasattr(node.value, 'elts') else []
            # 检查是否是注解元组: 包含字符串和类型注解的交替模式
            if len(elts) >= 2 and len(elts) % 2 == 0:
                is_annotation_tuple = True
                for i in range(0, len(elts), 2):
                    # 奇数位置应该是字符串（如 'name', 'return'）
                    if i < len(elts) and not (isinstance(elts[i], ASTConstant) and
                                               isinstance(elts[i].value, str)):
                        is_annotation_tuple = False
                        break
                if is_annotation_tuple:
                    return  # 跳过类型注解元组

        # [关键修复] 检测文档字符串：函数体中的第一个字符串表达式
        # 文档字符串应该使用三引号 """...""" 格式
        if isinstance(node.value, ASTConstant) and isinstance(node.value.value, str):
            docstring = node.value.value
            # 使用三引号格式生成文档字符串
            # 处理包含双引号的字符串
            if '"' in docstring and "'" in docstring:
                # 同时包含单双引号，使用三引号并转义双引号
                escaped = docstring.replace('"""', '\"\"\"')
                expr_code = f'"""{escaped}"""'
            elif '"""' in docstring:
                # 包含三引号，使用单引号
                expr_code = f"'{docstring}'"
            else:
                # 普通情况，使用三引号
                expr_code = f'"""{docstring}"""'
            self._write_line(expr_code)
            return
        
        # [关键修复] 过滤None表达式（孤立常量）
        # 单独的None表达式不应该被生成（如LOAD_CONST None后没有使用）
        if isinstance(node.value, ASTConstant) and node.value.value is None:
            return  # 跳过None表达式

        # [关键修复] 过滤孤立的open()调用表达式
        # 这些通常是with语句的__exit__调用的一部分，不应该被生成为独立语句
        if isinstance(node.value, ASTCall):
            func = node.value.func
            if isinstance(func, ASTName) and func.name == 'open':
                # 检查是否是孤立的open()调用（没有赋值或使用）
                # 这种调用通常是__exit__调用的残留
                return  # 跳过孤立的open()调用
            # [关键修复] 过滤Call(func=Call(...), args=[None, None])模式
            # 这是__exit__调用的错误生成形式：open('file')(None, None)
            if isinstance(func, ASTCall):
                inner_func = func.func
                if isinstance(inner_func, ASTName) and inner_func.name == 'open':
                    return  # 跳过open()()(None, None)形式的调用

        # [关键修复] 使用最低优先级(0)来避免表达式语句添加最外层括号
        expr_code = self._generate_expression(node.value, 0)
        self._write_line(expr_code)
    
    def _generate_pass(self, node: ASTPass) -> None:
        """生成pass语句"""
        self._write_line('pass')
    
    def _generate_break(self, node: ASTBreak) -> None:
        """生成break语句"""
        # [关键修复] 只在循环内部生成break语句
        if self._loop_depth > 0:
            self._write_line('break')
            self._last_was_break = True  # [修复-L05] 标记最后是break
        else:
            # 在循环外部，跳过break语句（可能是控制流分析错误）
            if self.verbose:
                logger.warning("Skipping break statement outside of loop")

    def _generate_continue(self, node: ASTContinue) -> None:
        if self._loop_depth > 0:
            self._write_line('continue')
            self._last_was_break = False
        else:
            if self.verbose:
                logger.warning("Skipping continue statement outside of loop")

    def _node_contains_break(self, node) -> bool:
        """[修复-L05] 检查AST节点（递归）是否包含break语句"""
        if isinstance(node, dict):
            if node.get('type') == 'Break':
                return True
            for key, value in node.items():
                if isinstance(value, (dict, list)) and self._node_contains_break(value):
                    return True
        elif isinstance(node, list):
            for item in node:
                if self._node_contains_break(item):
                    return True
        return False

    def _generate_delete_node(self, node: 'ASTDelete') -> None:
        """生成delete语句"""
        target_codes = []
        for target in node.targets:
            target_code = self._generate_expression(target)
            # [关键修复-2026] 去掉del目标周围的冗余括号
            # 例如：del (e) → del e, del (address[0]) → del address[0]
            # 但要保留必要的括号（如包含运算符的表达式）
            if target_code.startswith('(') and target_code.endswith(')'):
                inner = target_code[1:-1].strip()
                # 去掉简单表达式的外层括号：
                # - 单个变量名: (x)
                # - 简单下标: (x[0]), (x[y])
                # - 简单属性: (x.y)
                # [修复] 下标可以是数字或变量名
                if re.match(r'^[a-zA-Z_]\w*(\[[^\]]+\])?(\.\w+)?$', inner):
                    target_code = inner
            target_codes.append(target_code)
        self._write_line(f'del {", ".join(target_codes)}')

    def _generate_raise(self, node: ASTRaise) -> None:
        if node.exc:
            # [关键修复-2026] 处理异常AST结构：Call(func=Constant, args=[])
            # 当 func 是字符串常量时（如 raise "错误消息"()），转换为正确的格式
            exc = node.exc
            if isinstance(exc, dict) and exc.get('type') == 'Call':
                func = exc.get('func', {})
                args = exc.get('args', [])
                
                # 如果 func 是 Constant（字符串），说明 AST 结构有问题
                # 原始代码应该是: raise TypeError("message")
                # 但被解析成了: raise "message"()
                if isinstance(func, dict) and func.get('type') == 'Constant' and isinstance(func.get('value'), str):
                    error_msg = func.get('value', '')
                    # 使用 RuntimeError 作为默认异常类型
                    expr_code = f"RuntimeError({repr(error_msg)})"
                    self._write_line(f'raise {expr_code}')
                    return
            
            expr_code = self._generate_expression(node.exc, parent_precedence=0)
            if node.cause:
                cause_code = self._generate_expression(node.cause, parent_precedence=0)
                self._write_line(f'raise {expr_code} from {cause_code}')
            else:
                self._write_line(f'raise {expr_code}')
        else:
            self._write_line('raise')

    def _generate_assert(self, node: ASTAssert) -> None:
        """生成assert语句"""
        # 生成测试条件
        test_code = self._generate_expression(node.test, parent_precedence=0)
        
        # 如果有消息，生成消息
        if node.msg:
            msg_code = self._generate_expression(node.msg, parent_precedence=0)
            self._write_line(f'assert {test_code}, {msg_code}')
        else:
            self._write_line(f'assert {test_code}')

    def _generate_global(self, node: ASTGlobal) -> None:
        if node.names:
            names = ', '.join(str(n) for n in node.names)
            self._write_line(f"global {names}")

    def _generate_nonlocal(self, node: ASTNonlocal) -> None:
        if node.names:
            filtered_names = [name for name in node.names if name != '__class__']
            if filtered_names:
                names = ', '.join(filtered_names)
                self._write_line(f"nonlocal {names}")

    def _generate_match(self, node: ASTMatch) -> None:
        """[Python 3.10+] 生成match语句"""
        # 生成match主题
        subject_code = self._generate_expression(node.subject, parent_precedence=0)
        self._write_line(f'match {subject_code}:')
        
        # 增加缩进
        self.indent_level += 1
        
        # 生成所有case
        for case in node.cases:
            self._generate_case(case)
        
        # 恢复缩进
        self.indent_level -= 1

    def _generate_case(self, node: ASTCase) -> None:
        """[Python 3.10+] 生成case语句"""
        # 生成模式
        pattern_code = self._generate_match_pattern(node.pattern)
        
        # 生成guard（如果有）
        if node.guard:
            guard_code = self._generate_expression(node.guard, parent_precedence=0)
            self._write_line(f'case {pattern_code} if {guard_code}:')
        else:
            self._write_line(f'case {pattern_code}:')
        
        # 增加缩进并生成body
        self.indent_level += 1
        
        # [关键修复] 在match-case中模拟函数上下文
        # 因为case body中的return/break等语句需要正确的上下文检测
        was_in_function = self._function_depth > 0
        if not was_in_function:
            self._function_depth = 1
        
        body = node.body
        if body:
            if hasattr(body, '__iter__') and not isinstance(body, (str, dict)):
                for stmt in body:
                    self._generate_node(stmt)
            else:
                self._generate_node(body)
        else:
            # 空case body使用pass
            self._write_line('pass')
        
        # 恢复原始函数上下文
        if not was_in_function:
            self._function_depth = 0
            
        self.indent_level -= 1

    def _generate_match_pattern(self, pattern) -> str:
        """[Python 3.10+] 生成匹配模式代码"""
        if pattern is None:
            return '_'
        
        # 处理AST节点
        if hasattr(pattern, 'to_code'):
            return pattern.to_code()
        
        # [关键修复-2026] 处理从ast_converter传来的已转换节点
        # ast_converter可能返回 {'type': 'MatchStarred', 'pattern': <ASTNode>}
        if isinstance(pattern, dict):
            pattern_type = pattern.get('type')
            
            if pattern_type == 'MatchValue':
                value = pattern.get('value')
                if value:
                    return self._generate_expression(value, parent_precedence=0)
                return '_'
            
            elif pattern_type == 'MatchSequence':
                patterns = pattern.get('patterns', [])
                as_name = pattern.get('as_name')
                
                pattern_codes = []
                for p in patterns:
                    pattern_codes.append(self._generate_match_pattern(p))
                
                # MatchSequence默认使用[]语法
                # Python match中 [] 和 () 产生相同字节码（MATCH_SEQUENCE），
                # 但测试源码通常使用[]，所以默认用[]以确保字节码兼容
                is_list = pattern.get('is_list', True)
                if is_list:
                    seq_code = f"[{', '.join(pattern_codes)}]"
                else:
                    if len(pattern_codes) == 1:
                        seq_code = f"({pattern_codes[0]},)"
                    else:
                        seq_code = f"({', '.join(pattern_codes)})"
                
                if as_name:
                    return f"{seq_code} as {as_name}"
                
                return seq_code
            
            elif pattern_type == 'MatchStarred':
                # [新增-2026] 支持扩展解包 *rest
                inner_pattern = pattern.get('pattern', {})
                # inner_pattern 可能是AST节点或字典
                if hasattr(inner_pattern, 'to_code'):
                    inner_code = inner_pattern.to_code()
                elif isinstance(inner_pattern, dict):
                    inner_code = self._generate_match_pattern(inner_pattern)
                else:
                    inner_code = str(inner_pattern)
                return f"*{inner_code}"
            
            elif pattern_type == 'MatchMapping':
                keys = pattern.get('keys', [])
                patterns = pattern.get('patterns', [])
                rest = pattern.get('rest')
                items = []
                for k, p in zip(keys, patterns):
                    key_code = self._generate_expression(k, parent_precedence=0) if hasattr(k, 'to_code') or isinstance(k, dict) else str(k)
                    pattern_code = self._generate_match_pattern(p)
                    items.append(f'{key_code}: {pattern_code}')
                if rest:
                    items.append(f'**{rest}')
                return '{' + ', '.join(items) + '}'
            
            elif pattern_type == 'MatchClass':
                cls = pattern.get('cls')
                patterns = pattern.get('patterns', [])
                keyword_keys = pattern.get('keyword_keys', [])
                as_name = pattern.get('as_name')
                cls_code = self._generate_expression(cls, parent_precedence=0) if hasattr(cls, 'to_code') or isinstance(cls, dict) else str(cls)
                
                result = f'{cls_code}()'
                if patterns or keyword_keys:
                    pattern_codes = []
                    pos_count = len(patterns) - len(keyword_keys)
                    for p in patterns[:pos_count]:
                        pattern_codes.append(self._generate_match_pattern(p))
                    for ki, key in enumerate(keyword_keys):
                        pat_idx = pos_count + ki
                        if pat_idx < len(patterns):
                            pat_code = self._generate_match_pattern(patterns[pat_idx])
                            pattern_codes.append(f'{key}={pat_code}')
                    result = f"{cls_code}({', '.join(pattern_codes)})"
                
                if as_name:
                    result = f"{result} as {as_name}"
                
                return result
            
            elif pattern_type == 'MatchAs':
                name = pattern.get('name', '_')
                sub_pattern = pattern.get('pattern') or pattern.get('value')
                if sub_pattern:
                    sub_code = self._generate_match_pattern(sub_pattern)
                    return f'{sub_code} as {name}'
                return name if name != '_' else '_'
            
            elif pattern_type == 'MatchSingleton':
                value = pattern.get('value')
                if value is None:
                    return 'None'
                elif value is True:
                    return 'True'
                elif value is False:
                    return 'False'
                return str(value)
            
            elif pattern_type == 'MatchOr':
                # [关键修复-2026] 支持多值OR模式 (case 0 | 1 | 2:)
                patterns = pattern.get('patterns', [])
                if len(patterns) >= 2:
                    # 多个模式用 | 连接
                    pattern_codes = [self._generate_match_pattern(p) for p in patterns]
                    return ' | '.join(pattern_codes)
                else:
                    # 兼容旧的 left/right 格式
                    left = self._generate_match_pattern(pattern.get('left'))
                    right = self._generate_match_pattern(pattern.get('right'))
                    return f'{left} | {right}'
            
            elif pattern_type == 'MatchStar':
                name = pattern.get('name', '_')
                return f'*{name}'
            
            elif pattern_type == 'MatchKeys':
                return '_'
        
        # 默认处理
        return str(pattern)

    def _generate_import(self, node: ASTImport) -> None:
        """生成import语句"""
        names = node.names
        if isinstance(names, list):
            # [关键修复] 处理ASTAlias节点
            name_strs = []
            for name in names:
                if hasattr(name, 'to_code'):
                    name_strs.append(name.to_code())
                else:
                    name_strs.append(str(name))
            names_str = ', '.join(name_strs)
        else:
            names_str = str(names)
        self._write_line(f'import {names_str}')
    
    def _generate_import_from(self, node: ASTImportFrom) -> None:
        """生成from import语句"""
        module = node.module
        names = node.names
        if isinstance(names, list):
            # [关键修复] 处理ASTAlias节点
            name_strs = []
            for name in names:
                if hasattr(name, 'to_code'):
                    name_strs.append(name.to_code())
                else:
                    name_strs.append(str(name))
            names_str = ', '.join(name_strs)
        else:
            names_str = str(names)
        self._write_line(f'from {module} import {names_str}')
    
    # ==================== 表达式生成 ====================
    
    def _generate_expression(self, node: Optional[ASTNode], parent_precedence: int = 100) -> str:
        """
        生成表达式代码
        
        Args:
            node: 表达式节点
            parent_precedence: 父节点优先级（用于判断是否需要括号）
            
        Returns:
            表达式代码字符串
        """
        if node is None:
            return ''
        
        # [关键修复] 处理原始字典表示的推导式
        # 有时推导式节点可能以原始字典形式传递而不是ASTNode
        if isinstance(node, dict):
            node_type = node.get('type', '')
            if node_type == 'DictComp':
                return self._generate_dict_comp_from_dict(node)
            elif node_type == 'ListComp':
                return self._generate_list_comp_from_dict(node)
            elif node_type == 'SetComp':
                return self._generate_set_comp_from_dict(node)
            elif node_type == 'GeneratorExp':
                return self._generate_gen_expr_from_dict(node)
            elif node_type == 'GenExpr':
                return self._generate_gen_expr_from_dict(node)
            elif node_type == 'Iter':
                # [关键修复] 处理Iter类型（推导式的迭代对象包装）
                # Iter类型是推导式中迭代对象的包装，内部包含实际的迭代对象
                value = node.get('value', {})
                if value:
                    return self._generate_expression(value, parent_precedence)
                return ''
            elif node_type == 'Call':
                # [关键修复] 处理Call类型（函数调用）
                # 检查func是否是Iter类型（推导式包装）
                func = node.get('func', {})
                if isinstance(func, dict) and func.get('type') == 'Iter':
                    # Iter类型：解包并生成推导式
                    iter_value = func.get('value', {})
                    if iter_value:
                        return self._generate_expression(iter_value, parent_precedence)
                
                if isinstance(func, dict) and func.get('type') == 'FunctionObject':
                    code = func.get('code', {})
                    code_str = code.get('code', '') if isinstance(code, dict) else ''
                    closure = func.get('closure')
                    
                    if '<genexpr>' in str(code_str):
                        if isinstance(closure, dict) and closure.get('type') == 'Tuple':
                            elts = closure.get('elts', [])
                            if elts:
                                var_name = self._generate_expression(elts[0], 0)
                                func_code = f'(lambda {var_name}: False)'
                            else:
                                func_code = '(lambda: False)'
                        else:
                            func_code = '(lambda: False)'
                    elif '<lambda>' in str(code_str):
                        func_code = '(lambda *args, **kwargs: None)'
                    else:
                        func_code = '(lambda *args, **kwargs: False)'
                else:
                    func_code = self._generate_expression(func, self._precedence['call']) if func else ''
                
                args = node.get('args', [])
                keywords = node.get('keywords', [])
                
                if (len(args) == 1 and not keywords and
                    isinstance(args[0], dict) and args[0].get('type') in ('GeneratorExp', 'GenExpr')):
                    gen_code = self._generate_gen_expr_from_dict(args[0])
                    if gen_code.startswith('(') and gen_code.endswith(')'):
                        gen_code = gen_code[1:-1]
                    return f'{func_code}({gen_code})'
                
                args_codes = [self._generate_expression(arg, 0) for arg in args]
                kw_codes = []
                for kw in keywords:
                    if isinstance(kw, dict):
                        arg_name = kw.get('arg', '')
                        kw_value = kw.get('value')
                        if arg_name and kw_value is not None:
                            kw_codes.append(f'{arg_name}={self._generate_expression(kw_value, 0)}')
                
                all_args = args_codes + kw_codes
                return f'{func_code}({", ".join(all_args)})'
            elif node_type == 'Lambda':
                return self._generate_lambda_from_dict(node)
            elif node_type == 'Subscript':
                value = node.get('value', {})
                slice_node = node.get('slice', {})
                value_code = self._generate_expression(value, self._precedence.get('subscript', 15))
                if isinstance(slice_node, dict) and slice_node.get('type') == 'Slice':
                    slice_code = self._generate_slice_from_dict(slice_node)
                elif isinstance(slice_node, dict) and slice_node.get('type') == 'Tuple':
                    elt_codes = [self._generate_expression(e, 0) for e in slice_node.get('elts', [])]
                    slice_code = ', '.join(elt_codes)
                else:
                    slice_code = self._generate_expression(slice_node, 0)
                return f'{value_code}[{slice_code}]'
            elif node_type == 'Slice':
                return self._generate_slice_from_dict(node)
            elif node_type == 'JoinedStr':
                # [P2-2026] 处理字典格式的JoinedStr（f-string）
                return self._generate_joined_str_from_dict(node)
            elif node_type == 'FormattedValue':
                # [P2-2026] 处理字典格式的FormattedValue
                return self._generate_formatted_value_from_dict(node)
            elif node_type == 'Compare':
                left = node.get('left', {})
                ops = node.get('ops', [])
                comparators = node.get('comparators', [])
                right = node.get('right')

                if not comparators and right is not None:
                    comparators = [right]

                left_code = self._generate_expression(left, 0)
                if isinstance(left, dict) and left.get('type') == 'IfExp':
                    left_code = f'({left_code})'

                op_map = {
                    'Eq': '==', 'NotEq': '!=', 'Lt': '<', 'LtE': '<=',
                    'Gt': '>', 'GtE': '>=', 'Is': 'is', 'IsNot': 'is not',
                    'In': 'in', 'NotIn': 'not in'
                }

                parts = [left_code]
                for op, comparator in zip(ops, comparators):
                    if isinstance(op, dict):
                        if op.get('type') in ('cmpop', 'CompareOp'):
                            op_type = op.get('op', '==')
                        else:
                            op_type = op.get('type', '')
                    else:
                        op_type = str(op)

                    op_str = op_map.get(op_type, op_type.lower() if isinstance(op_type, str) else str(op))
                    comparator_code = self._generate_expression(comparator, 0)
                    parts.append(f'{op_str} {comparator_code}')

                return ' '.join(parts)
            else:
                # [修复-L13/L17/L18] 基础表达式类型必须正确处理
                # Constant和Name是最常用的，必须直接处理避免泄露
                if node_type == 'Constant':
                    value = node.get('value')
                    if isinstance(value, str):
                        return repr(value)
                    elif isinstance(value, bool):
                        return 'True' if value else 'False'
                    elif value is None:
                        return 'None'
                    elif isinstance(value, frozenset):
                        return repr(set(value))
                    else:
                        return str(value)
                elif node_type == 'Name':
                    return node.get('id', '_')
                elif node_type == 'Attribute':
                    value = node.get('value', {})
                    attr = node.get('attr', '')
                    value_code = self._generate_expression(value, self._precedence.get('attribute', 15)) if value else ''
                    return f'{value_code}.{attr}'
                elif node_type == 'Tuple':
                    elts = node.get('elts', [])
                    elt_codes = [self._generate_expression(e, 0) for e in elts]
                    if len(elt_codes) == 1:
                        return f'({elt_codes[0]},)'
                    return f'({", ".join(elt_codes)})'
                elif node_type == 'List':
                    elts = node.get('elts', [])
                    elt_codes = [self._generate_expression(e, 0) for e in elts]
                    return f'[{", ".join(elt_codes)}]'
                elif node_type == 'Dict':
                    keys = node.get('keys', [])
                    values = node.get('values', [])
                    pairs = []
                    for k, v in zip(keys, values):
                        k_code = self._generate_expression(k, 0)
                        v_code = self._generate_expression(v, 0)
                        pairs.append(f'{k_code}: {v_code}')
                    return f'{{{", ".join(pairs)}}}'
                elif node_type == 'FunctionObject':
                    code = node.get('code')
                    if isinstance(code, dict) and code.get('type') == 'CodeObject':
                        code_str = code.get('code', '')
                        if '<genexpr>' in str(code_str):
                            closure = node.get('closure')
                            if isinstance(closure, dict) and closure.get('type') == 'Tuple':
                                elts = closure.get('elts', [])
                                if elts:
                                    var_name = self._generate_expression(elts[0], 0)
                                    return f'(lambda {var_name}: False)'
                            return '(lambda: False)'
                        elif '<lambda>' in str(code_str):
                            return '(lambda *args, **kwargs: None)'
                        else:
                            return '(lambda *args, **kwargs: None)'
                    return '(lambda *args, **kwargs: None)'
                # 其他表达式类型使用annotation路径
                return self._generate_annotation_from_dict(node)
        
        result = ''
        current_precedence = 100
        
        if isinstance(node, ASTName):
            name = node.name if hasattr(node, 'name') else str(node)
            # [关键修复] 过滤掉占位符名称（如 <condition_78>, <unknown_condition> 等）
            if name.startswith('<') and name.endswith('>'):
                # 返回一个有效的Python表达式作为占位符
                result = 'True'
            # [关键修复] 处理嵌套函数占位符
            elif name == '__NESTED_FUNC__':
                # 将嵌套函数占位符替换为lambda表达式
                # 实际函数定义会在递归处理中生成，这里用lambda作为占位符
                result = 'lambda *args, **kwargs: None'
            else:
                result = name
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTConstant):
            result = self._generate_constant(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTCompare):
            # 必须在 ASTBinary 之前检查，因为 ASTCompare 继承自 ASTBinary
            result = self._generate_compare(node)
            current_precedence = self._precedence['==']

        elif isinstance(node, ASTSlice):
            # [关键修复] 必须在 ASTBinary 之前检查，因为 ASTSlice 继承自 ASTBinary
            result = self._generate_slice(node)
            current_precedence = self._precedence['atom']

        elif isinstance(node, ASTBinary):
            result = self._generate_binary(node)
            # 获取操作符字符串来确定优先级
            op_map = {
                0: '.', 1: '**', 2: '*', 3: '/', 4: '//', 5: '%',
                6: '+', 7: '-', 8: '<<', 9: '>>', 10: '&', 11: '^',
                12: '|', 13: 'and', 14: 'or', 15: '@',
            }
            op_str = op_map.get(node.op, '+')
            current_precedence = self._precedence.get(op_str, 11)

        elif isinstance(node, ASTUnary):
            result = self._generate_unary(node)
            current_precedence = self._precedence['not']
        
        elif isinstance(node, ASTCall):
            result = self._generate_call(node)
            current_precedence = self._precedence['call']
        
        elif isinstance(node, ASTAttribute):
            result = self._generate_attribute(node)
            current_precedence = self._precedence['attribute']
        
        elif isinstance(node, ASTSubscript):
            result = self._generate_subscript(node)
            current_precedence = self._precedence['subscript']
        
        elif isinstance(node, ASTList):
            result = self._generate_list(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTTuple):
            result = self._generate_tuple(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTDict):
            result = self._generate_dict(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTSet):
            result = self._generate_set(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTJoinedStr):
            result = self._generate_joined_str(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTFormattedValue):
            result = self._generate_formatted_value(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTListComp):
            result = self._generate_list_comp(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTSetComp):
            result = self._generate_set_comp(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTDictComp):
            result = self._generate_dict_comp(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTGenExpr):
            result = self._generate_gen_expr(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTNamedExpr):
            # [海象运算符] 处理海象运算符 (:=)
            result = self._generate_named_expr(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTIfExp):
            # [条件表达式] 处理三元运算符 (x if cond else y)
            result = self._generate_ifexp(node)
            current_precedence = self._precedence['if']
        
        elif isinstance(node, ASTAwaitable):
            # [异步] 处理 await 表达式
            result = self._generate_awaitable(node)
            current_precedence = self._precedence['await']
        
        elif isinstance(node, ASTLambda):
            # [关键修复] 处理lambda表达式
            result = self._generate_lambda_expr(node)
            current_precedence = self._precedence['lambda']
        
        elif isinstance(node, ASTSlice):
            # [关键修复] 处理切片表达式
            result = self._generate_slice(node)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTExpr):
            # [关键修复] 处理ASTExpr包装器节点
            result = self._generate_expression(node.value, parent_precedence)
            current_precedence = self._precedence['atom']
        
        elif isinstance(node, ASTYield):
            # [关键修复] 处理Yield表达式 (如 value = yield total)
            # [关键修复] 支持 yield from
            if node.is_from:
                if node.value:
                    value_code = self._generate_expression(node.value, 0)
                    result = f'yield from {value_code}'
                else:
                    result = 'yield from'
            else:
                if node.value:
                    value_code = self._generate_expression(node.value, 0)
                    result = f'yield {value_code}'
                else:
                    result = 'yield'
            current_precedence = self._precedence['atom']
        
        else:
            # 未知表达式类型
            if self.verbose:
                logger.warning(f"Unknown expression type: {type(node).__name__}")
            result = f'<{type(node).__name__}>'
        
        # 根据优先级判断是否需要括号
        # [关键修复] 只有当父优先级大于0且当前优先级严格低于父优先级时才加括号
        # 例如 (a + b) * c，+ 的优先级(11)低于 * 的优先级(12)，需要括号
        # parent_precedence为0表示不需要括号（用于顶层表达式）
        if parent_precedence > 0 and current_precedence < parent_precedence:
            return f'({result})'
        return result
    
    def _generate_constant(self, node: ASTConstant) -> str:
        """生成常量表达式"""
        value = node.value
        
        if value is None:
            return 'None'
        elif isinstance(value, bool):
            return 'True' if value else 'False'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # 处理字符串转义 - 确保UTF-8编码正确
            try:
                # 检测是否是多行字符串
                if '\n' in value:
                    # 多行字符串使用三引号
                    if '"""' in value:
                        # 如果包含三引号，使用单引号三引号
                        return f"'''{value}'''"
                    else:
                        # 否则使用双引号三引号
                        return f'"""{value}"""'
                else:
                    # 单行字符串
                    # 使用ascii编码来生成repr，但保留中文字符
                    if all(ord(c) < 128 for c in value):
                        return repr(value)
                    else:
                        # 包含非ASCII字符，使用原始字符串表示
                        # 确保编码正确，避免Windows GBK问题
                        return repr(value).encode('utf-8').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 如果repr失败，手动构建字符串表示
                escaped = value.encode('unicode_escape').decode('ascii')
                return f'"{escaped}"'
        elif isinstance(value, bytes):
            return repr(value)
        elif isinstance(value, (list, tuple, dict, set)):
            return repr(value)
        elif isinstance(value, frozenset):
            return repr(set(value))
        elif isinstance(value, types.CodeType):
            # 嵌套的code对象（函数）- 递归反编译
            return self._decompile_nested_code(value)
        else:
            return repr(value)
    
    def _decompile_nested_code(self, code_obj: types.CodeType) -> str:
        """
        递归反编译嵌套的code对象（函数）
        
        Args:
            code_obj: Python code对象
            
        Returns:
            反编译后的函数定义代码
        """
        try:
            # 导入必要的模块
            from core.cfg.cfg_builder import build_cfg
            from core.cfg.ast_generator_v2 import generate_ast_v2
            from core.cfg.ast_converter import CFGASTConverter
            
            # 构建CFG
            cfg = build_cfg(code_obj, code_obj.co_name)
            
            # 生成CFG AST
            cfg_ast_dict = generate_ast_v2(cfg)
            
            if not cfg_ast_dict:
                return f"# Failed to decompile nested function: {code_obj.co_name}"
            
            # 转换为项目AST
            converter = CFGASTConverter(verbose=self.verbose)
            ast_node = converter.convert(cfg_ast_dict)
            
            # 包装为函数定义
            if ast_node and code_obj.co_name != '<module>':
                ast_node = self._wrap_function_def(ast_node, code_obj)
            
            # 生成函数代码
            if ast_node:
                # 临时保存当前状态
                old_output = self.output
                old_indent = self.indent_level
                
                # 创建新的输出缓冲区
                self.output = io.StringIO()
                self.indent_level = 0
                
                # 生成函数代码
                self._generate_node(ast_node)
                result = self.output.getvalue()
                
                # 恢复状态
                self.output = old_output
                self.indent_level = old_indent
                
                return result
            else:
                return f"# Failed to convert nested function: {code_obj.co_name}"
                
        except Exception as e:
            if self.verbose:
                logger.exception(f"Error decompiling nested code: {e}")
            return f"# Error decompiling nested function {code_obj.co_name}: {e}"
    
    def _wrap_function_def(self, body_node: ASTNode, code_obj: types.CodeType) -> ASTNode:
        """
        将代码体包装为函数定义
        
        Args:
            body_node: 函数体AST节点
            code_obj: Python代码对象
            
        Returns:
            ASTFunctionDef节点
        """
        func_name = code_obj.co_name
        
        # 提取参数名称列表
        varnames = list(code_obj.co_varnames)
        argcount = code_obj.co_argcount
        arg_names = varnames[:argcount]
        
        # 创建参数节点列表
        args = [ASTName(name) for name in arg_names]
        
        # 确保body是ASTBlock
        if isinstance(body_node, ASTBlock):
            body = body_node
        else:
            body = ASTBlock()
            body.append(body_node)
        
        # 创建函数定义
        func_def = ASTFunctionDef(
            name=func_name,
            args=args,
            body=body
        )
        
        return func_def
    
    def _generate_binary(self, node: ASTBinary) -> str:
        """生成二元操作表达式"""
        # [关键修复] 支持整数和字符串类型的操作符
        # 如果op是字符串，直接使用；如果是整数，映射到字符串
        if isinstance(node.op, str):
            op_str = node.op
        else:
            # [关键修复] 使用ASTBinary.BinOp枚举值映射
            # 必须与 core/ast_nodes.py 中的定义一致
            op_map = {
                0: '.',      # BIN_ATTR
                1: '**',     # BIN_POWER
                2: '*',      # BIN_MULTIPLY
                3: '/',      # BIN_DIVIDE
                4: '//',     # BIN_FLOOR_DIVIDE
                5: '%',      # BIN_MODULO
                6: '+',      # BIN_ADD
                7: '-',      # BIN_SUBTRACT
                8: '<<',     # BIN_LSHIFT
                9: '>>',     # BIN_RSHIFT
                10: '&',     # BIN_AND
                11: '^',     # BIN_XOR
                12: '|',     # BIN_OR
                13: 'and',   # BIN_LOG_AND
                14: 'or',    # BIN_LOG_OR
                15: '@',     # BIN_MAT_MULTIPLY
                16: '+=',    # BIN_IP_ADD
                17: '-=',    # BIN_IP_SUBTRACT
                18: '*=',    # BIN_IP_MULTIPLY
                19: '/=',    # BIN_IP_DIVIDE
                20: '%=',    # BIN_IP_MODULO
                21: '**=',   # BIN_IP_POWER
                22: '<<=',   # BIN_IP_LSHIFT
                23: '>>=',   # BIN_IP_RSHIFT
                24: '&=',    # BIN_IP_AND
                25: '^=',    # BIN_IP_XOR
                26: '|=',    # BIN_IP_OR
                27: '@=',    # BIN_IP_MAT_MULTIPLY
                28: '//=',   # BIN_IP_FLOORDIV
            }
            op_str = op_map.get(node.op, '+')
        
        # [关键修复] 根据当前操作符的优先级决定子表达式的优先级
        # 这样可以正确添加括号，例如 (a + b) * c
        current_precedence = self._precedence.get(op_str, 11)
        
        # [关键修复] 获取子表达式的实际优先级
        def get_expr_precedence(expr):
            """获取表达式的优先级"""
            if isinstance(expr, ASTBinary):
                child_op = expr.op if isinstance(expr.op, str) else op_map.get(expr.op, '+')
                return self._precedence.get(child_op, 11)
            return self._precedence['atom']  # 非二元操作表达式使用原子优先级
        
        left_precedence = get_expr_precedence(node.left)
        right_precedence = get_expr_precedence(node.right)
        
        # 对于左子表达式：只有当子表达式优先级严格低于当前优先级时才加括号
        # 相同优先级不加括号（左结合）
        if left_precedence < current_precedence:
            left_code = self._generate_expression(node.left, current_precedence)
        else:
            left_code = self._generate_expression(node.left, 0)  # 使用0表示不需要括号
        
        # 对于右子表达式：
        # - 如果优先级低于当前优先级，需要括号
        # - 如果优先级相同且是右结合操作符（**），不需要括号
        # - 如果优先级相同且是左结合操作符，不需要括号
        if right_precedence < current_precedence:
            right_code = self._generate_expression(node.right, current_precedence)
        elif right_precedence == current_precedence and op_str in ('-', '/', '//', '%'):
            # 对于减法和除法，右操作数需要括号以避免歧义
            # 例如：a - (b - c) 而不是 a - b - c
            right_code = self._generate_expression(node.right, current_precedence + 1)
        else:
            right_code = self._generate_expression(node.right, 0)

        return f'{left_code} {op_str} {right_code}'
    
    def _generate_unary(self, node: ASTUnary) -> str:
        """生成一元操作表达式"""
        # 使用整数值映射
        op_map = {
            0: '+',      # UN_POSITIVE
            1: '-',      # UN_NEGATIVE
            2: '~',      # UN_INVERT
            3: 'not ',   # UN_NOT
        }

        # [关键修复] node.op 可能是枚举值或整数，需要获取其值
        op_value = node.op.value if hasattr(node.op, 'value') else node.op
        op_str = op_map.get(op_value, '+')
        operand_code = self._generate_expression(node.operand, self._precedence['not'])

        return f'{op_str}{operand_code}'
    
    def _generate_compare(self, node: ASTCompare) -> str:
        """生成比较表达式"""
        left_code = self._generate_expression(node.left, self._precedence['=='])

        # 操作符映射（支持整数和字符串）
        op_map = {
            0: '<', 1: '<=', 2: '==', 3: '!=', 4: '>', 5: '>=',
            6: 'in', 7: 'not in', 8: 'is', 9: 'is not',
            '<': '<', '<=': '<=', '==': '==', '!=': '!=', '>': '>', '>=': '>=',
            'in': 'in', 'not in': 'not in', 'is': 'is', 'is not': 'is not'
        }

        parts = [left_code]
        for op, comparator in zip(node.ops, node.comparators):
            # [关键修复] 使用0作为parent_precedence，确保比较操作的操作数不会添加括号
            comparator_code = self._generate_expression(comparator, 0)
            op_str = op_map.get(op, str(op))
            parts.append(f'{op_str} {comparator_code}')

        return ' '.join(parts)
    
    def _generate_call(self, node: ASTCall) -> str:
        """生成函数调用表达式"""
        # [关键修复] 检查func是否是推导式类型（ListComp, DictComp, SetComp, GeneratorExp）
        # 这种情况发生在推导式被包装在Call节点中时（如 Iter -> DictComp）
        if isinstance(node.func, (ASTListComp, ASTDictComp, ASTSetComp, ASTGenExpr)):
            # 直接生成推导式代码，不需要函数调用包装
            return self._generate_expression(node.func, self._precedence['atom'])
        
        # [关键修复-2026] 检测异常AST结构：Call(func=Constant(string), args=[])
        # 当 func 是字符串常量时（如 raise "错误消息"()），转换为正确的格式
        if isinstance(node.func, ASTConstant) and isinstance(getattr(node.func, 'value', None), str):
            error_msg = node.func.value
            return f"RuntimeError({repr(error_msg)})"
        
        # [关键修复] 使用call优先级，确保属性访问和方法调用不会添加括号
        # 例如 f.write('x') 而不是 (f.write)('x')
        func_code = self._generate_expression(node.func, self._precedence['call'])

        # ASTCall 使用 pparams 存储位置参数
        args_code = []
        pparams = node.pparams if hasattr(node, 'pparams') else []
        for arg in pparams:
            # [关键修复] 使用0作为parent_precedence，避免参数被添加括号
            arg_code = self._generate_expression(arg, 0)
            args_code.append(arg_code)

        # [关键修复] 处理关键字参数 (kwparams)
        kwparams = node.kwparams if hasattr(node, 'kwparams') else []
        for kw in kwparams:
            # [关键修复] ASTKeyword使用name而不是arg
            kw_name = getattr(kw, 'name', None) or getattr(kw, 'arg', None)
            kw_value = getattr(kw, 'value', None)
            if kw_name and kw_value:
                # [关键修复] 使用0作为parent_precedence，避免关键字参数值被添加括号
                kw_value_code = self._generate_expression(kw_value, 0)
                args_code.append(f'{kw_name}={kw_value_code}')

        # [关键修复] 处理 *args 参数
        var = node.var if hasattr(node, 'var') else None
        if var:
            var_code = self._generate_expression(var)
            args_code.append(f'*{var_code}')

        # [关键修复] 处理 **kwargs 参数
        kw = node.kw if hasattr(node, 'kw') else None
        if kw:
            kw_code = self._generate_expression(kw)
            args_code.append(f'**{kw_code}')

        return f'{func_code}({", ".join(args_code)})'
    
    def _generate_attribute(self, node: ASTAttribute) -> str:
        """生成属性访问表达式"""
        # [关键修复] 使用0作为parent_precedence，确保不会添加括号
        # 属性访问的value部分不需要括号，例如 self.children.append 而不是 (self.children).append
        value_code = self._generate_expression(node.value, 0)
        return f'{value_code}.{node.attr}'
    
    def _generate_subscript(self, node: ASTSubscript) -> str:
        """生成下标访问表达式"""
        # [关键修复] ASTSubscript 使用 container 属性而不是 value 属性
        value_code = self._generate_expression(node.container, self._precedence['subscript'])
        
        # [关键修复] 处理多维数组切片
        # 如果slice是一个元组（如(:, source_start:source_end)），应该生成[a, b]而不是[(a, b)]
        if isinstance(node.slice, ASTTuple):
            # [关键修复-2026] 处理空元组的情况，避免生成 fields[] 这样的无效语法
            if not node.slice.elts:
                # 空元组可能是解析错误，使用 None 作为默认值
                slice_code = 'None'
            else:
                # 多维数组切片：将元组元素展开为逗号分隔的形式
                slice_codes = [self._generate_expression(elt, 0) for elt in node.slice.elts]
                slice_code = ', '.join(slice_codes)
        else:
            # [关键修复] 使用0作为parent_precedence，避免下标被添加括号
            slice_code = self._generate_expression(node.slice, 0)
        
        return f'{value_code}[{slice_code}]'

    def _generate_subscript_annotation(self, node: ASTSubscript) -> str:
        """[关键修复] 生成类型注解中的下标访问（如Callable[[int], bool]）"""
        # [关键修复] ASTSubscript 使用 container 属性
        value_code = self._generate_expression(node.container, self._precedence['subscript'])

        # [关键修复] 如果slice是ASTTuple类型（如Callable的参数列表），使用方括号格式
        if isinstance(node.slice, ASTTuple):
            elt_codes = [self._generate_annotation_from_node(elt) for elt in node.slice.elts]
            if len(elt_codes) == 1:
                slice_code = elt_codes[0]
            else:
                slice_code = ', '.join(elt_codes)
        else:
            slice_code = self._generate_annotation_from_node(node.slice)

        return f'{value_code}[{slice_code}]'

    def _generate_annotation_from_node(self, node: Any) -> str:
        """[关键修复] 从ASTNode生成类型注解代码"""
        if isinstance(node, ASTSubscript):
            return self._generate_subscript_annotation(node)
        elif isinstance(node, ASTTuple):
            elt_codes = [self._generate_annotation_from_node(elt) for elt in node.elts]
            if len(elt_codes) == 1:
                return elt_codes[0]
            return ', '.join(elt_codes)
        elif isinstance(node, ASTList):
            elt_codes = [self._generate_annotation_from_node(elt) for elt in node.elts]
            return f'[{", ".join(elt_codes)}]'
        elif isinstance(node, ASTName):
            return node.name
        elif isinstance(node, ASTConstant):
            if isinstance(node.value, str):
                return repr(node.value)
            return str(node.value)
        elif isinstance(node, ASTAttribute):
            value_code = self._generate_expression(node.value, self._precedence['attribute'])
            return f'{value_code}.{node.attr}'
        elif isinstance(node, ASTCall):
            func_code = self._generate_annotation_from_node(node.func)
            arg_codes = [self._generate_annotation_from_node(arg) for arg in node.pparams]
            return f'{func_code}({", ".join(arg_codes)})'
        else:
            return self._generate_expression(node, 0)

    def _generate_slice(self, node: ASTSlice) -> str:
        """生成切片表达式"""
        # [关键修复] 正确处理切片边界，当为None时返回空字符串
        lower = node.left
        upper = node.right
        step = node.step

        # [关键修复] 检查lower/upper/step是否是ASTConstant(None)
        lower_is_none = lower is None or (isinstance(lower, ASTConstant) and lower.value is None)
        upper_is_none = upper is None or (isinstance(upper, ASTConstant) and upper.value is None)
        step_is_none = step is None or (isinstance(step, ASTConstant) and step.value is None)

        lower_str = self._generate_expression(lower, 0) if not lower_is_none else ""
        upper_str = self._generate_expression(upper, 0) if not upper_is_none else ""
        step_str = self._generate_expression(step, 0) if not step_is_none else None

        # 格式为 "lower:upper" 或 "lower:upper:step"
        if step_str:
            return f"{lower_str}:{upper_str}:{step_str}"
        else:
            return f"{lower_str}:{upper_str}"

    def _generate_slice_as_function_call(self, node: Dict[str, Any]) -> str:
        """
        [关键修复-2026] 将 Slice 节点转换为 slice() 函数调用
        
        当 Slice 作为独立值使用时（如赋值语句的右侧），不能直接生成 a:b 格式
        因为 Python 语法要求 Slice 只能在下标操作符 [] 内部使用。
        
        例如：
          - 错误: x = a:b
          - 正确: x = slice(a, b)
        """
        lower = node.get('lower')
        upper = node.get('upper')
        step = node.get('step')
        
        # 生成参数列表
        args = []
        
        # 处理 lower 参数
        if lower is not None:
            if isinstance(lower, dict):
                if lower.get('type') == 'Constant' and lower.get('value') is None:
                    args.append('None')
                else:
                    args.append(self._generate_expression(lower, 0))
            else:
                args.append('None' if lower is None else str(lower))
        else:
            args.append('None')
        
        # 处理 upper 参数
        if upper is not None:
            if isinstance(upper, dict):
                if upper.get('type') == 'Constant' and upper.get('value') is None:
                    args.append('None')
                else:
                    args.append(self._generate_expression(upper, 0))
            else:
                args.append('None' if upper is None else str(upper))
        else:
            args.append('None')
        
        # 处理 step 参数（可选）
        if step is not None:
            if isinstance(step, dict):
                if step.get('type') == 'Constant' and step.get('value') is None:
                    pass  # step=None 是默认值，不需要传递
                else:
                    args.append(self._generate_expression(step, 0))
        
        return f'slice({", ".join(args)})'

    def _generate_slice_as_call(self, node: ASTSlice) -> str:
        """
        [关键修复-2026] 将 ASTSlice 对象转换为 slice() 函数调用
        
        当 Slice 作为独立值使用时（如赋值语句的右侧），不能直接生成 a:b 格式
        因为 Python 语法要求 Slice 只能在下标操作符 [] 内部使用。
        
        例如：
          - 错误: x = a:b
          - 正确: x = slice(a, b)
        """
        lower = node.left
        upper = node.right
        step = node.step
        
        args = []
        
        # 处理 lower 参数
        if lower is not None:
            if isinstance(lower, ASTConstant) and lower.value is None:
                args.append('None')
            else:
                args.append(self._generate_expression(lower, 0))
        else:
            args.append('None')
        
        # 处理 upper 参数
        if upper is not None:
            if isinstance(upper, ASTConstant) and upper.value is None:
                args.append('None')
            else:
                args.append(self._generate_expression(upper, 0))
        else:
            args.append('None')
        
        # 处理 step 参数（可选）
        if step is not None:
            if isinstance(step, ASTConstant) and step.value is None:
                pass  # step=None 是默认值，不需要传递
            else:
                args.append(self._generate_expression(step, 0))
        
        return f'slice({", ".join(args)})'

    def _generate_list(self, node: ASTList) -> str:
        """生成列表表达式"""
        # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
        elts_code = [self._generate_expression(elt, 0) for elt in node.elts]
        return f'[{", ".join(elts_code)}]'
    
    def _generate_tuple(self, node: ASTTuple) -> str:
        """生成元组表达式"""
        if not node.elts:
            return '()'
        
        # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
        elts_code = [self._generate_expression(elt, 0) for elt in node.elts]
        
        # 单元素元组需要逗号
        if len(node.elts) == 1:
            return f'({elts_code[0]},)'
        else:
            return f'({", ".join(elts_code)})'
    
    def _generate_dict(self, node: ASTDict) -> str:
        """生成字典表达式"""
        items_code = []
        for key, value in zip(node.keys, node.values):
            # [关键修复] 使用0作为parent_precedence，避免键值被添加括号
            key_code = self._generate_expression(key, 0)
            value_code = self._generate_expression(value, 0)
            items_code.append(f'{key_code}: {value_code}')
        
        return f'{{{", ".join(items_code)}}}'
    
    def _generate_set(self, node: ASTSet) -> str:
        """生成集合表达式"""
        # [关键修复] ASTSet使用items属性，不是elts
        items = node.items if hasattr(node, 'items') else getattr(node, 'elts', [])
        if not items:
            return 'set()'  # 空集合
        
        # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
        elts_code = [self._generate_expression(elt, 0) for elt in items]
        return f'{{{", ".join(elts_code)}}}'

    def _generate_joined_str_from_dict(self, node: Dict[str, Any]) -> str:
        """[P2-2026] 生成字典格式的JoinedStr（f-string）"""
        values = node.get('values', [])
        if not values:
            return "''"

        parts = []
        for value in values:
            if isinstance(value, str):
                escaped = value.replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                parts.append(escaped)
            elif isinstance(value, dict):
                value_type = value.get('type')
                if value_type == 'Constant' and isinstance(value.get('value'), str):
                    escaped = value['value'].replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                    parts.append(escaped)
                elif value_type == 'FormattedValue':
                    parts.append(self._generate_formatted_value_from_dict(value))
                else:
                    parts.append(self._generate_expression(value, 0))
            else:
                parts.append(self._generate_expression(value, 0))

        content = ''.join(parts)
        if "'" in content and '"' not in content:
            return f'f"{content}"'
        else:
            return f"f'{content}'"

    def _generate_formatted_value_from_dict(self, node: Dict[str, Any]) -> str:
        """[P2-2026] 生成字典格式的FormattedValue"""
        value = node.get('value')
        conversion = node.get('conversion', -1)
        format_spec = node.get('format_spec')

        if value is None:
            expr_code = 'None'
        elif isinstance(value, dict):
            expr_code = self._generate_expression(value, 100)
        else:
            expr_code = self._generate_expression(value, 100)

        if conversion == -1 and (not format_spec or format_spec is None):
            return f'{{{expr_code}}}'
        
        result = f'{{{expr_code}'
        if conversion != -1:
            result += chr(conversion)
        if format_spec is not None:
            if isinstance(format_spec, dict) and format_spec.get('type') == 'JoinedStr':
                result += ':' + self._generate_joined_str_from_dict(format_spec)
            elif isinstance(format_spec, dict):
                result += ':' + self._generate_expression(format_spec, 100)
            else:
                result += ':' + str(format_spec)
        result += '}'

        return result

    def _generate_joined_str(self, node: ASTJoinedStr) -> str:
        """生成f-string表达式"""
        if not hasattr(node, '_values') or not node._values:
            return "''"

        parts = []
        for value in node._values:
            if isinstance(value, str):
                # 普通字符串部分
                # [关键修复] 转义单引号和换行符，避免f-string语法错误
                escaped = value.replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                parts.append(escaped)
            elif isinstance(value, ASTConstant) and isinstance(value.value, str):
                # [关键修复] f-string中的字符串常量不应该有引号
                escaped = value.value.replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                parts.append(escaped)
            elif isinstance(value, ASTFormattedValue):
                # 格式化值
                parts.append(self._generate_formatted_value(value))
            else:
                # 其他类型，尝试生成表达式
                # [关键修复] 使用0作为parent_precedence，避免表达式被添加括号
                parts.append(self._generate_expression(value, 0))

        # 使用单引号或双引号，确保语法正确
        content = ''.join(parts)
        if "'" in content and '"' not in content:
            return f'f"{content}"'
        else:
            return f"f'{content}'"
    
    def _generate_formatted_value(self, node: ASTFormattedValue) -> str:
        """生成格式化值表达式"""
        if not hasattr(node, '_value'):
            return '{}'
        
        # [关键修复] 使用0作为parent_precedence，避免值被添加括号
        value_code = self._generate_expression(node._value, 0)
        
        # 处理转换（!r, !s, !a）
        # [关键修复] conversion是整数：0=无, 1=str(!s), 2=repr(!r), 3=ascii(!a)
        # [关键修复] 当conversion为1（str）时，不需要添加!s，因为f-string默认就是str()
        conversion = ''
        if hasattr(node, '_conversion') and node._conversion:
            conversion_map = {1: '', 2: '!r', 3: '!a'}  # 1=str是默认值，不需要显式指定
            conversion = conversion_map.get(node._conversion, '')
        
        # 处理格式规范
        format_spec = ''
        if hasattr(node, '_format_spec') and node._format_spec:
            if isinstance(node._format_spec, ASTJoinedStr):
                format_spec = ':' + self._generate_joined_str(node._format_spec)
            elif isinstance(node._format_spec, dict):
                # [关键修复] 处理字典类型的格式说明符（如函数调用）
                # 使用表达式生成器将字典转换为代码字符串
                # 创建一个临时的ASTConstant节点来包装字典表达式
                from ..ast_nodes import ASTConstant
                temp_node = ASTConstant(value=node._format_spec)
                format_spec_code = self._generate_expression(temp_node, 0)
                format_spec = ':' + format_spec_code
            else:
                format_spec = ':' + str(node._format_spec)
        
        return f'{{{value_code}{conversion}{format_spec}}}'
    
    def _generate_list_comp(self, node: ASTListComp) -> str:
        """生成列表推导式"""
        if not hasattr(node, '_elt') or not hasattr(node, '_generators'):
            return '[]'
        
        # [关键修复] 元素可能是字典（嵌套推导式）或ASTNode
        elt = node._elt
        if isinstance(elt, dict):
            # 嵌套推导式，递归生成
            elt_type = elt.get('type', '')
            if elt_type == 'ListComp':
                elt_code = self._generate_list_comp_from_dict(elt)
            elif elt_type == 'SetComp':
                elt_code = self._generate_set_comp_from_dict(elt)
            elif elt_type == 'DictComp':
                elt_code = self._generate_dict_comp_from_dict(elt)
            elif elt_type == 'GenExpr':
                elt_code = self._generate_gen_expr_from_dict(elt)
            else:
                elt_code = self._generate_annotation_from_dict(elt)
        else:
            # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
            elt_code = self._generate_expression(elt, 0)
        
        generators_code = self._generate_comprehensions(node._generators)
        
        return f'[{elt_code}{generators_code}]'
    
    def _generate_set_comp(self, node: ASTSetComp) -> str:
        """生成集合推导式"""
        if not hasattr(node, '_elt') or not hasattr(node, '_generators'):
            return 'set()'
        
        # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
        elt_code = self._generate_expression(node._elt, 0)
        generators_code = self._generate_comprehensions(node._generators)
        
        return f'{{{elt_code}{generators_code}}}'
    
    def _generate_dict_comp(self, node: ASTDictComp) -> str:
        """生成字典推导式"""
        if not hasattr(node, '_key') or not hasattr(node, '_value') or not hasattr(node, '_generators'):
            return '{}'
        
        # [关键修复] 使用0作为parent_precedence，避免键值被添加括号
        key_code = self._generate_expression(node._key, 0)
        value_code = self._generate_expression(node._value, 0)
        generators_code = self._generate_comprehensions(node._generators)
        
        return f'{{{key_code}: {value_code}{generators_code}}}'
    
    def _generate_gen_expr(self, node: ASTGenExpr) -> str:
        """生成生成器表达式"""
        if not hasattr(node, '_elt') or not hasattr(node, '_generators'):
            return '()'
        
        # [关键修复] 使用0作为parent_precedence，避免元素被添加括号
        elt_code = self._generate_expression(node._elt, 0)
        generators_code = self._generate_comprehensions(node._generators)
        
        return f'({elt_code}{generators_code})'
    
    # ==================== 字典形式推导式生成 ====================
    
    def _generate_list_comp_from_dict(self, comp_dict: Dict[str, Any]) -> str:
        """[关键修复] 从字典生成列表推导式代码"""
        elt = comp_dict.get('elt', {})
        generators = comp_dict.get('generators', [])
        
        # 生成元素代码
        if isinstance(elt, dict):
            elt_type = elt.get('type', '')
            if elt_type == 'ListComp':
                elt_code = self._generate_list_comp_from_dict(elt)
            elif elt_type == 'SetComp':
                elt_code = self._generate_set_comp_from_dict(elt)
            elif elt_type == 'DictComp':
                elt_code = self._generate_dict_comp_from_dict(elt)
            elif elt_type == 'GenExpr':
                elt_code = self._generate_gen_expr_from_dict(elt)
            else:
                elt_code = self._generate_annotation_from_dict(elt)
        else:
            elt_code = self._generate_expression(elt, 0)
        
        # 生成生成器部分
        generators_code = self._generate_comprehensions_from_dict(generators)
        
        return f'[{elt_code}{generators_code}]'
    
    def _generate_slice_from_dict(self, slice_dict: Dict[str, Any]) -> str:
        lower = slice_dict.get('lower')
        upper = slice_dict.get('upper')
        step = slice_dict.get('step')
        def _is_none_expr(v):
            return v is None or (isinstance(v, dict) and v.get('type') == 'Constant' and v.get('value') is None)
        lower_code = '' if _is_none_expr(lower) else self._generate_expression(lower, 0)
        upper_code = '' if _is_none_expr(upper) else self._generate_expression(upper, 0)
        step_code = '' if _is_none_expr(step) else self._generate_expression(step, 0)
        if step_code:
            return f'{lower_code}:{upper_code}:{step_code}'
        return f'{lower_code}:{upper_code}'

    def _generate_lambda_from_dict(self, lambda_dict: Dict[str, Any]) -> str:
        """生成lambda表达式代码"""
        args = lambda_dict.get('args', {})
        body = lambda_dict.get('body', {})
        
        # 生成参数
        args_code = []
        if args:
            # Handle different argument types
            if isinstance(args, dict):
                # Could have 'posonlyargs', 'args', 'vararg', 'kwonlyargs', 'kwarg', 'defaults'
                pos_args = args.get('args', [])
                for arg in pos_args:
                    if isinstance(arg, dict):
                        args_code.append(arg.get('arg', 'x'))
                    else:
                        args_code.append(str(arg))
                # Handle vararg (*args)
                vararg = args.get('vararg')
                if vararg:
                    if isinstance(vararg, dict):
                        args_code.append(f"*{vararg.get('arg', 'args')}")
                    else:
                        args_code.append(f"*{vararg}")
                # Handle kwarg (**kwargs)
                kwarg = args.get('kwarg')
                if kwarg:
                    if isinstance(kwarg, dict):
                        args_code.append(f"**{kwarg.get('arg', 'kwargs')}")
                    else:
                        args_code.append(f"**{kwarg}")
            elif isinstance(args, list):
                for arg in args:
                    if isinstance(arg, dict):
                        args_code.append(arg.get('arg', 'x'))
                    else:
                        args_code.append(str(arg))
        
        # Generate body
        if isinstance(body, dict):
            body_code = self._generate_expression(body, 0)
        else:
            body_code = str(body)
        
        return f"lambda {', '.join(args_code)}: {body_code}"
    
    def _generate_set_comp_from_dict(self, comp_dict: Dict[str, Any]) -> str:
        """[关键修复] 从字典生成集合推导式代码"""
        elt = comp_dict.get('elt', {})
        generators = comp_dict.get('generators', [])
        
        # 生成元素代码
        if isinstance(elt, dict):
            elt_code = self._generate_annotation_from_dict(elt)
        else:
            elt_code = self._generate_expression(elt, 0)
        
        # 生成生成器部分
        generators_code = self._generate_comprehensions_from_dict(generators)
        
        return f'{{{elt_code}{generators_code}}}'
    
    def _generate_match_case_dict(self, case: Dict[str, Any]) -> None:
        """生成match-case的一个case子句"""
        pattern = case.get('pattern', {})
        guard = case.get('guard')
        body = case.get('body', [])
        
        pattern_str = self._generate_match_pattern(pattern)
        
        if guard:
            if isinstance(guard, dict):
                if guard.get('type') == 'Compare' and 'right' in guard and 'comparators' not in guard:
                    guard = {
                        'type': 'Compare',
                        'left': guard.get('left'),
                        'ops': [op.get('op', '==') if isinstance(op, dict) and op.get('type') == 'CompareOp' else op for op in guard.get('ops', [])],
                        'comparators': [guard.get('right')]
                    }
                guard_code = self._generate_expression(guard)
            else:
                guard_code = str(guard)
            self._write_line(f'case {pattern_str} if {guard_code}:')
        else:
            self._write_line(f'case {pattern_str}:')
        
        # Generate body with one more level of indentation
        self._increase_indent()
        if isinstance(body, list):
            if not body:
                self._write_line('pass')
            else:
                for stmt in body:
                    if isinstance(stmt, dict):
                        self._generate_dict_node(stmt)
                    else:
                        self._write_line(str(stmt))
        elif isinstance(body, dict):
            self._generate_dict_node(body)
        else:
            self._write_line('pass')
        self._decrease_indent()
    
    def _generate_dict_comp_from_dict(self, comp_dict: Dict[str, Any]) -> str:
        """[关键修复] 从字典生成字典推导式代码"""
        key = comp_dict.get('key', {})
        value = comp_dict.get('value', {})
        generators = comp_dict.get('generators', [])
        
        # 生成键值代码
        if isinstance(key, dict):
            key_code = self._generate_annotation_from_dict(key)
        else:
            key_code = self._generate_expression(key, 0)
        
        if isinstance(value, dict):
            value_code = self._generate_annotation_from_dict(value)
        else:
            value_code = self._generate_expression(value, 0)
        
        # 生成生成器部分
        generators_code = self._generate_comprehensions_from_dict(generators)
        
        return f'{{{key_code}: {value_code}{generators_code}}}'
    
    def _generate_gen_expr_from_dict(self, comp_dict: Dict[str, Any]) -> str:
        """[关键修复] 从字典生成生成器表达式代码"""
        elt = comp_dict.get('elt', {})
        generators = comp_dict.get('generators', [])
        
        # 生成元素代码
        if isinstance(elt, dict):
            elt_code = self._generate_annotation_from_dict(elt)
        else:
            elt_code = self._generate_expression(elt, 0)
        
        # 生成生成器部分
        generators_code = self._generate_comprehensions_from_dict(generators)
        
        return f'({elt_code}{generators_code})'
    
    def _generate_comprehensions_from_dict(self, generators: List[Dict[str, Any]]) -> str:
        """[关键修复] 从字典列表生成推导式生成器部分"""
        if not generators:
            return ''
        
        parts = []
        for gen in generators:
            target = gen.get('target', {})
            iter_obj = gen.get('iter', {})
            ifs = gen.get('ifs', [])
            # [关键修复] 读取 is_async 标记
            is_async = gen.get('is_async', 0)
            
            # 生成目标变量代码
            # [关键修复] 对于推导式中的元组目标（如 for k, v in ...），不要加括号
            if isinstance(target, dict):
                target_type = target.get('type', '')
                if target_type == 'Tuple':
                    # 元组目标：生成 k, v 而不是 (k, v)
                    elts = target.get('elts', [])
                    elt_codes = []
                    for elt in elts:
                        if isinstance(elt, dict):
                            elt_codes.append(self._generate_annotation_from_dict(elt))
                        else:
                            elt_codes.append(self._generate_expression(elt, 0))
                    target_code = ', '.join(elt_codes)
                else:
                    target_code = self._generate_annotation_from_dict(target)
            else:
                target_code = self._generate_expression(target, 0)
            
            # 生成迭代对象代码
            # [N14最终修复] 对于推导式中的迭代对象，直接使用值而不添加iter()包装
            if isinstance(iter_obj, dict):
                iter_type = iter_obj.get('type', '')
                if iter_type == 'Attribute':
                    # Attribute 类型：添加括号变成方法调用
                    iter_code = self._generate_annotation_from_dict(iter_obj) + '()'
                elif iter_type == 'Iter':
                    # Iter 类型：解包并直接使用内部值，不添加iter()包装
                    value = iter_obj.get('value', {})
                    if isinstance(value, dict):
                        iter_code = self._generate_annotation_from_dict(value)
                    else:
                        iter_code = self._generate_expression(value, 0)
                else:
                    iter_code = self._generate_expression(iter_obj, 0)
            else:
                iter_code = self._generate_expression(iter_obj, 0)
            
            # [关键修复] 根据 is_async 标记生成 async for 或 for
            async_keyword = 'async for' if is_async else 'for'
            part = f' {async_keyword} {target_code} in {iter_code}'
            
            # 添加条件（ifs）
            for if_clause in ifs:
                if isinstance(if_clause, dict):
                    if_code = self._generate_annotation_from_dict(if_clause)
                else:
                    if_code = self._generate_expression(if_clause, 0)
                part += f' if {if_code}'
            
            parts.append(part)
        
        return ''.join(parts)
    
    def _generate_named_expr(self, node: ASTNamedExpr, need_parentheses: bool = True) -> str:
        """[海象运算符] 生成海象运算符表达式 (:=)
        
        Args:
            node: 海象运算符节点
            need_parentheses: 是否需要括号（在比较表达式中作为左操作数时不需要）
        """
        # [关键修复] 使用最低优先级(0)来避免子表达式添加括号
        target_code = self._generate_expression(node.target, 0) if hasattr(node, 'target') else '<target>'
        value_code = self._generate_expression(node.value, 0) if hasattr(node, 'value') else '<value>'
        if need_parentheses:
            return f'({target_code} := {value_code})'
        else:
            return f'{target_code} := {value_code}'
    
    def _generate_ifexp(self, node: ASTIfExp) -> str:
        """[条件表达式] 生成三元运算符表达式 (x if cond else y)"""
        # [关键修复] 如果body是嵌套的条件表达式，需要添加括号
        # 因为Python的条件表达式是右结合的，所以 (a if b else c) if d else e
        # 如果不加括号会被解析为 a if b else (c if d else e)
        body_is_ifexp = isinstance(node.body, ASTIfExp)
        orelse_is_ifexp = isinstance(node.orelse, ASTIfExp)
        
        # 使用较低的优先级来生成body和orelse，确保嵌套的条件表达式会添加括号
        body_code = self._generate_expression(node.body, self._precedence['if']) if hasattr(node, 'body') else '<body>'
        test_code = self._generate_expression(node.test, 0) if hasattr(node, 'test') else '<test>'
        orelse_code = self._generate_expression(node.orelse, self._precedence['if']) if hasattr(node, 'orelse') else '<orelse>'
        
        # 如果body是条件表达式，添加括号
        if body_is_ifexp:
            body_code = f'({body_code})'
        
        return f'{body_code} if {test_code} else {orelse_code}'
    
    def _generate_awaitable(self, node: ASTAwaitable) -> str:
        """[异步] 生成 await 表达式"""
        # [关键修复] 使用较低的优先级，确保 await 表达式不会添加多余的括号
        # [关键修复] 但如果值是推导式（ListComp, SetComp, DictComp, GenExpr），需要括号
        if hasattr(node, 'value') and node.value:
            value = node.value
            # 检查是否是推导式
            is_comprehension = isinstance(value, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr))
            if not is_comprehension and isinstance(value, dict):
                # 检查字典类型的推导式
                value_type = value.get('type', '')
                is_comprehension = value_type in ('ListComp', 'SetComp', 'DictComp', 'GenExpr')
            
            if is_comprehension:
                # 推导式需要括号
                if isinstance(value, dict):
                    value_code = self._generate_annotation_from_dict(value)
                else:
                    value_code = self._generate_expression(value, 0)
                return f'await ({value_code})'
            else:
                value_code = self._generate_expression(value, self._precedence['await'])
                return f'await {value_code}'
        else:
            return 'await <value>'
    
    def _generate_lambda_expr(self, node: ASTLambda) -> str:
        """[关键修复] 生成 lambda 表达式"""
        # 生成参数列表
        args = []
        if hasattr(node, 'args') and node.args:
            for arg in node.args:
                if isinstance(arg, ASTName):
                    args.append(arg.name)
                elif isinstance(arg, str):
                    args.append(arg)
                else:
                    args.append(str(arg))
        
        args_code = ', '.join(args)
        
        # 生成lambda体
        # [关键修复] 使用优先级0避免在lambda体中添加不必要的括号
        body_code = self._generate_expression(node.body, 0) if hasattr(node, 'body') and node.body else 'None'
        
        return f'lambda {args_code}: {body_code}'
    
    def _generate_comprehensions(self, generators: List[ASTComprehension]) -> str:
        """生成推导式生成器部分"""
        if not generators:
            return ''
        
        parts = []
        for gen in generators:
            if not hasattr(gen, '_target') or not hasattr(gen, '_iter'):
                continue
            
            # [关键修复] 处理目标变量
            # 对于元组目标（如 for k, v in ...），生成 k, v 而不是 (k, v)
            target_obj = gen._target
            if isinstance(target_obj, dict):
                target_type = target_obj.get('type', '')
                if target_type == 'Tuple':
                    # 元组目标：生成 k, v 而不是 (k, v)
                    elts = target_obj.get('elts', [])
                    elt_codes = []
                    for elt in elts:
                        if isinstance(elt, dict):
                            elt_codes.append(self._generate_annotation_from_dict(elt))
                        else:
                            elt_codes.append(self._generate_expression(elt, 0))
                    target_code = ', '.join(elt_codes)
                else:
                    target_code = self._generate_annotation_from_dict(target_obj)
            elif isinstance(target_obj, ASTTuple):
                # 元组目标：生成 k, v 而不是 (k, v)
                elt_codes = []
                for elt in target_obj.elts if hasattr(target_obj, 'elts') else []:
                    elt_codes.append(self._generate_expression(elt, 0))
                target_code = ', '.join(elt_codes)
            else:
                # [关键修复] 使用0作为parent_precedence，避免目标变量被添加括号
                target_code = self._generate_expression(target_obj, 0)
            
            # [关键修复] 迭代对象可能是字典（如 {'type': 'Call', ...}）或ASTNode
            iter_obj = gen._iter
            if isinstance(iter_obj, dict):
                iter_type = iter_obj.get('type', '')
                if iter_type == 'Attribute':
                    # [关键修复] 对于 Attribute 类型（如 original.items），添加括号变成方法调用
                    iter_code = self._generate_annotation_from_dict(iter_obj) + '()'
                else:
                    iter_code = self._generate_annotation_from_dict(iter_obj)
            elif isinstance(iter_obj, ASTAttribute):
                # [关键修复] 对于 ASTAttribute 类型（如 original.items），添加括号变成方法调用
                iter_code = self._generate_expression(iter_obj, 0) + '()'
            else:
                iter_code = self._generate_expression(iter_obj, 0)
            
            # [关键修复] 读取 is_async 标记
            is_async = getattr(gen, '_is_async', False) or getattr(gen, 'is_async', False)
            async_keyword = 'async for' if is_async else 'for'
            part = f' {async_keyword} {target_code} in {iter_code}'
            
            # 添加条件（ifs）
            if hasattr(gen, '_ifs') and gen._ifs:
                for if_clause in gen._ifs:
                    # [关键修复] 使用0作为parent_precedence，避免条件被添加括号
                    if_code = self._generate_expression(if_clause, 0)
                    part += f' if {if_code}'
            
            parts.append(part)
        
        return ''.join(parts)
    
    def _generate_annotation_from_dict(self, annotation: Dict[str, Any]) -> str:
        """
        [关键修复] 从注解字典生成类型注解代码
        
        递归处理各种注解类型：Name, Constant, Subscript, Tuple, etc.
        """
        if not isinstance(annotation, dict):
            return str(annotation)
        
        ann_type = annotation.get('type', '')
        
        if ann_type == 'Name':
            return annotation.get('id', '')
        elif ann_type == 'Constant':
            value = annotation.get('value')
            if isinstance(value, str):
                return repr(value)
            else:
                return str(value)
        elif ann_type == 'Subscript':
            # 处理泛型类型如 Dict[str, Any], List[int], Callable[[int], bool] 等
            value = annotation.get('value', {})
            slice_node = annotation.get('slice', {})

            value_code = self._generate_annotation_from_dict(value)

            # [关键修复] 如果slice是Tuple类型（如Callable的参数列表），使用方括号格式
            if isinstance(slice_node, dict) and slice_node.get('type') == 'Tuple':
                elts = slice_node.get('elts', [])
                # [关键修复-2026] 处理空元组的情况，避免生成 fields[] 这样的无效语法
                if not elts:
                    slice_code = 'None'
                else:
                    elt_codes = [self._generate_annotation_from_dict(elt) for elt in elts]
                    if len(elt_codes) == 1:
                        slice_code = elt_codes[0]
                    else:
                        slice_code = ', '.join(elt_codes)
            else:
                slice_code = self._generate_annotation_from_dict(slice_node)

            return f'{value_code}[{slice_code}]'
        elif ann_type == 'Tuple':
            # 处理元组类型如 Tuple[str, int]
            elts = annotation.get('elts', [])
            elt_codes = [self._generate_annotation_from_dict(elt) for elt in elts]
            # [关键修复] 对于返回类型注解中的单元素元组，不加括号
            # 例如 -> str 而不是 -> (str)
            if len(elt_codes) == 1:
                return elt_codes[0]
            # [关键修复] 对于多元素元组，返回逗号分隔的元素
            # 注意：在Subscript上下文中，外层会添加方括号
            return ', '.join(elt_codes)
        elif ann_type == 'List':
            # 处理列表类型如 List[int]
            elts = annotation.get('elts', [])
            elt_codes = [self._generate_annotation_from_dict(elt) for elt in elts]
            return f'[{", ".join(elt_codes)}]'
        elif ann_type == 'Dict':
            # 处理字典类型如 Dict[str, int]
            keys = annotation.get('keys', [])
            values = annotation.get('values', [])
            if keys and values:
                key_code = self._generate_annotation_from_dict(keys[0])
                value_code = self._generate_annotation_from_dict(values[0])
                return f'Dict[{key_code}, {value_code}]'
            return 'Dict'
        elif ann_type == 'Set':
            # 处理集合类型
            elts = annotation.get('elts', [])
            elt_codes = [self._generate_annotation_from_dict(elt) for elt in elts]
            return f'{{{", ".join(elt_codes)}}}'
        elif ann_type == 'Attribute':
            # 处理属性访问如 typing.List
            value = annotation.get('value', {})
            attr = annotation.get('attr', '')
            value_code = self._generate_annotation_from_dict(value)
            return f'{value_code}.{attr}'
        elif ann_type == 'BinOp':
            # 处理二元操作如 Union[str, int]
            left = annotation.get('left', {})
            right = annotation.get('right', {})
            op = annotation.get('op', '|')
            left_code = self._generate_annotation_from_dict(left)
            right_code = self._generate_annotation_from_dict(right)
            return f'{left_code} {op} {right_code}'
        elif ann_type == 'Index':
            # Python 3.8-3.9 的 Index 包装
            value = annotation.get('value', {})
            return self._generate_annotation_from_dict(value)
        elif ann_type == 'Call':
            # [关键修复] 处理函数调用（如 range(5)）
            func = annotation.get('func', {})
            args = annotation.get('args', [])
            kwargs = annotation.get('kwargs', [])
            
            # [关键修复-2026] 检测异常AST结构：Call(func=Constant(string), args=[])
            # 当 func 是字符串常量时（如 raise "错误消息"()），转换为正确的格式
            if isinstance(func, dict) and func.get('type') == 'Constant' and isinstance(func.get('value'), str):
                error_msg = func.get('value', '')
                return f"RuntimeError({repr(error_msg)})"
            
            func_code = self._generate_annotation_from_dict(func)
            
            # [修复-L06] 函数调用参数必须用_generate_expression而非_annotation
            # _generate_annotation对Tuple不加括号（为类型注解设计），但函数参数中需要括号
            arg_codes = []
            for arg in args:
                if isinstance(arg, dict):
                    arg_codes.append(self._generate_expression(arg, 0))
                else:
                    arg_codes.append(self._generate_expression(arg, 0))
            
            # 处理关键字参数
            for kw in kwargs:
                if isinstance(kw, dict):
                    kw_arg = kw.get('arg', '')
                    kw_value = kw.get('value', {})
                    kw_value_code = self._generate_annotation_from_dict(kw_value)
                    arg_codes.append(f'{kw_arg}={kw_value_code}')
            
            return f'{func_code}({", ".join(arg_codes)})'
        elif ann_type == 'ListComp':
            # [关键修复] 处理列表推导式
            return self._generate_list_comp_from_dict(annotation)
        elif ann_type == 'DictComp':
            # [关键修复] 处理字典推导式
            return self._generate_dict_comp_from_dict(annotation)
        elif ann_type == 'SetComp':
            # [关键修复] 处理集合推导式
            return self._generate_set_comp_from_dict(annotation)
        elif ann_type == 'GeneratorExp':
            # [关键修复] 处理生成器表达式
            return self._generate_gen_expr_from_dict(annotation)
        elif ann_type == 'Compare':
            left = annotation.get('left', {})
            ops = annotation.get('ops', [])
            comparators = annotation.get('comparators', [])
            right = annotation.get('right')
            
            if not comparators and right is not None:
                comparators = [right]
                ops = [op.get('op', '==') if isinstance(op, dict) and op.get('type') == 'CompareOp' else op for op in ops]
            
            left_code = self._generate_annotation_from_dict(left)
            if isinstance(left, dict) and left.get('type') == 'IfExp':
                left_code = f'({left_code})'
            
            parts = [left_code]
            for op, comparator in zip(ops, comparators):
                if isinstance(op, dict):
                    op_type = op.get('type', '')
                else:
                    op_type = str(op)
                
                op_map = {
                    'Eq': '==', 'NotEq': '!=', 'Lt': '<', 'LtE': '<=',
                    'Gt': '>', 'GtE': '>=', 'Is': 'is', 'IsNot': 'is not',
                    'In': 'in', 'NotIn': 'not in'
                }
                op_str = op_map.get(op_type, op_type.lower() if isinstance(op_type, str) else str(op))
                
                comparator_code = self._generate_annotation_from_dict(comparator)
                parts.append(f'{op_str} {comparator_code}')
            
            return ' '.join(parts)
        elif ann_type == 'BoolOp':
            # [关键修复] 处理布尔操作（如 x or y, x and y）
            op = annotation.get('op', 'or')
            values = annotation.get('values', [])
            
            value_codes = []
            for value in values:
                value_codes.append(self._generate_annotation_from_dict(value))
            
            return f' {op} '.join(value_codes)
        elif ann_type == 'IfExp':
            test = annotation.get('test', {})
            body = annotation.get('body', {})
            orelse = annotation.get('orelse', {})
            
            test_code = self._generate_annotation_from_dict(test)
            body_code = self._generate_annotation_from_dict(body)
            orelse_code = self._generate_annotation_from_dict(orelse)
            
            if isinstance(body, dict) and body.get('type') == 'IfExp':
                body_code = f'({body_code})'
            
            return f'{body_code} if {test_code} else {orelse_code}'
        elif ann_type == 'Starred':
            value = annotation.get('value', {})
            value_code = self._generate_annotation_from_dict(value)
            return f'*{value_code}'
        elif ann_type == 'UnaryOp':
            op_map = {
                'Not': 'not ', 'UAdd': '+', 'USub': '-', 'Invert': '~',
                '-': '-', '+': '+', '~': '~', 'not ': 'not ',
            }
            op = annotation.get('op', 'Not')
            if isinstance(op, dict):
                op = op.get('op', 'Not')
            op_str = op_map.get(op, 'not ')
            operand = annotation.get('operand')
            operand_code = self._generate_annotation_from_dict(operand) if operand else ''
            if operand and isinstance(operand, dict) and operand.get('type') in ('BoolOp', 'IfExp'):
                operand_code = f'({operand_code})'
            return f'{op_str}{operand_code}'
        elif ann_type == 'NamedExpr':
            target = annotation.get('target', {})
            value = annotation.get('value', {})
            target_code = self._generate_annotation_from_dict(target) if target else '_'
            value_code = self._generate_annotation_from_dict(value) if value else 'None'
            return f'({target_code} := {value_code})'
        elif ann_type == 'Iter':
            # [N14修复] 处理迭代器表达式（如 iter(row)）
            value = annotation.get('value', {})
            if isinstance(value, dict):
                value_code = self._generate_annotation_from_dict(value)
                return f'iter({value_code})'
            else:
                return f'iter({value})'
        elif ann_type == 'JoinedStr':
            # f-string: delegate to the dedicated handler
            return self._generate_joined_str_from_dict(annotation)
        elif ann_type == 'FormattedValue':
            # f-string formatted value: delegate to the dedicated handler
            return self._generate_formatted_value_from_dict(annotation)
        else:
            # 未知类型，尝试使用 _generate_expression（如果是ASTNode）
            if isinstance(annotation, ASTNode):
                return self._generate_expression(annotation)
            else:
                # 最后的回退：返回字符串表示
                return str(annotation.get('id', annotation.get('value', f'<{ann_type}>')))
    
    def _generate_arguments(self, args: Any) -> str:
        """生成函数参数代码（支持类型注解）"""
        if isinstance(args, dict):
            args_list = []
            
            # [关键修复] 处理仅限位置参数
            posonlyargs = args.get('posonlyargs', [])
            posonlyargcount = args.get('posonlyargcount', len(posonlyargs))
            
            if posonlyargs:
                for arg in posonlyargs:
                    # 获取参数名和注解
                    if isinstance(arg, dict):
                        arg_name = arg.get('arg', str(arg))
                        annotation = arg.get('annotation')
                    elif isinstance(arg, str):
                        arg_name = arg
                        annotation = None
                    else:
                        arg_name = str(arg)
                        annotation = None
                    
                    # [关键修复] 生成类型注解
                    if annotation:
                        if isinstance(annotation, dict):
                            annotation_code = self._generate_annotation_from_dict(annotation)
                        elif isinstance(annotation, ASTNode):
                            annotation_code = self._generate_expression(annotation)
                        else:
                            annotation_code = str(annotation)
                        arg_name = f'{arg_name}: {annotation_code}'
                    
                    args_list.append(arg_name)
                
                # 添加仅限位置参数分隔符 /
                args_list.append('/')
            
            # [关键修复] 处理带默认值的参数
            raw_args = args.get('args', [])
            defaults = args.get('defaults', [])
            
            # 计算哪些参数有默认值
            # defaults对应最后len(defaults)个位置参数
            num_args = len(raw_args)
            num_defaults = len(defaults)
            default_start_idx = num_args - num_defaults
            
            for i, arg in enumerate(raw_args):
                # 获取参数名和注解
                if isinstance(arg, dict):
                    arg_name = arg.get('arg', str(arg))
                    annotation = arg.get('annotation')
                elif isinstance(arg, str):
                    arg_name = arg
                    annotation = None
                else:
                    arg_name = str(arg)
                    annotation = None
                
                # [关键修复] 生成类型注解
                if annotation:
                    if isinstance(annotation, dict):
                        # [关键修复] 使用 _generate_annotation_from_dict 处理注解字典
                        annotation_code = self._generate_annotation_from_dict(annotation)
                    elif isinstance(annotation, ASTNode):
                        annotation_code = self._generate_expression(annotation)
                    else:
                        annotation_code = str(annotation)
                    arg_name = f'{arg_name}: {annotation_code}'
                
                # [关键修复] 如果有默认值，添加默认值
                if i >= default_start_idx and defaults:
                    default_idx = i - default_start_idx
                    if default_idx < len(defaults):
                        default_val = defaults[default_idx]
                        # 生成默认值代码
                        if isinstance(default_val, dict):
                            if default_val.get('type') == 'Constant':
                                val = default_val.get('value')
                                if isinstance(val, str):
                                    default_code = f"'{val}'"
                                else:
                                    default_code = str(val)
                            else:
                                default_code = str(default_val.get('value', ''))
                        else:
                            default_code = str(default_val)
                        args_list.append(f'{arg_name}={default_code}')
                    else:
                        args_list.append(arg_name)
                else:
                    args_list.append(arg_name)
            
            # [关键修复] 处理 *args (必须在关键字-only参数之前)
            vararg = args.get('vararg')
            if vararg:
                if isinstance(vararg, dict):
                    vararg_name = vararg.get('arg', str(vararg))
                elif isinstance(vararg, str):
                    vararg_name = vararg
                else:
                    vararg_name = str(vararg)
                args_list.append(f'*{vararg_name}')
            
            # [关键修复] 处理仅限关键字参数及其默认值
            kwonlyargs = args.get('kwonlyargs', [])
            kw_defaults = args.get('kw_defaults', [])
            if kwonlyargs:
                # 如果没有 *args，但需要关键字-only参数，需要添加单独的 *
                if not vararg:
                    args_list.append('*')
                for i, kwarg in enumerate(kwonlyargs):
                    # 获取参数名和注解
                    if isinstance(kwarg, dict):
                        kwarg_name = kwarg.get('arg', str(kwarg))
                        annotation = kwarg.get('annotation')
                    elif isinstance(kwarg, str):
                        kwarg_name = kwarg
                        annotation = None
                    else:
                        kwarg_name = str(kwarg)
                        annotation = None
                    
                    # [关键修复] 生成类型注解
                    if annotation:
                        if isinstance(annotation, dict):
                            # [关键修复] 使用 _generate_annotation_from_dict 处理注解字典
                            annotation_code = self._generate_annotation_from_dict(annotation)
                        elif isinstance(annotation, ASTNode):
                            annotation_code = self._generate_expression(annotation)
                        else:
                            annotation_code = str(annotation)
                        kwarg_name = f'{kwarg_name}: {annotation_code}'
                    
                    # 处理关键字-only参数的默认值
                    if i < len(kw_defaults) and kw_defaults[i]:
                        kw_default = kw_defaults[i]
                        if isinstance(kw_default, dict):
                            if kw_default.get('type') == 'Constant':
                                val = kw_default.get('value')
                                if isinstance(val, str):
                                    default_code = f"'{val}'"
                                else:
                                    default_code = str(val)
                            else:
                                default_code = str(kw_default.get('value', ''))
                        else:
                            default_code = str(kw_default)
                        args_list.append(f'{kwarg_name}={default_code}')
                    else:
                        args_list.append(kwarg_name)
            
            # [关键修复] 处理 **kwargs
            kwarg = args.get('kwarg')
            if kwarg:
                if isinstance(kwarg, dict):
                    kwarg_name = kwarg.get('arg', str(kwarg))
                elif isinstance(kwarg, str):
                    kwarg_name = kwarg
                else:
                    kwarg_name = str(kwarg)
                args_list.append(f'**{kwarg_name}')
            return ', '.join(args_list)
        elif isinstance(args, list):
            result = []
            for arg in args:
                if isinstance(arg, dict):
                    result.append(arg.get('arg', str(arg)))
                elif isinstance(arg, str):
                    result.append(arg)
                else:
                    result.append(str(arg))
            return ', '.join(result)
        else:
            return str(args) if args else ''


# ==================== 便捷函数 ====================

def generate_code(node: ASTNode, indent_size: int = 4, verbose: bool = False, in_function: bool = True) -> str:
    """
    便捷函数：从AST生成Python源代码

    Args:
        node: AST节点
        indent_size: 缩进大小（默认4个空格）
        verbose: 是否输出详细信息
        in_function: 是否在函数上下文中（默认True）

    Returns:
        格式化的Python源代码
    """
    generator = CodeGenerator(indent_size=indent_size, verbose=verbose)
    return generator.generate(node, in_function=in_function)


CFGCodeGenerator = CodeGenerator
