"""
统一AST生成器 - 完整的CFG反编译流程

集成CFG分析、AST转换和代码生成，提供端到端的反编译能力。
"""

import types
from typing import Dict, Any, Optional, Union, Tuple
import logging

from core.ast_nodes import ASTNode, ASTBlock, ASTFunctionDef, ASTClassDef
from core.cfg.ast_converter import CFGASTConverter, convert_cfg_ast
from core.cfg.code_generator import CFGCodeGenerator, generate_code
from core.bytecode_matcher import BytecodeMatcher, recommend_method

logger = logging.getLogger(__name__)


class UnifiedASTGenerator:
    """
    统一AST生成器
    
    提供完整的CFG反编译流程：
    1. CFG构建和分析
    2. AST转换（CFG字典 -> 项目AST）
    3. 代码生成（AST -> Python源代码）
    
    这是CFG模块完善到100%后的统一入口。
    """
    
    def __init__(self, verbose: bool = False, use_cfg: bool = True):
        self.verbose = verbose
        self.use_cfg = use_cfg
        self.matcher = BytecodeMatcher()
        self.ast_converter = CFGASTConverter(verbose=verbose)
        self.code_generator = CFGCodeGenerator(verbose=verbose)
    
    def decompile(self, code_obj: types.CodeType, 
                  name: Optional[str] = None) -> Optional[str]:
        """
        反编译代码对象为Python源代码
        
        Args:
            code_obj: Python代码对象
            name: 代码名称（用于调试）
            
        Returns:
            反编译后的Python源代码，失败返回None
        """
        if self.verbose:
            logger.info(f"[UnifiedASTGenerator] 开始反编译: {name or code_obj.co_name}")
        
        # 1. 生成AST
        ast_node = self.generate_ast(code_obj, name)
        if not ast_node:
            logger.error("AST生成失败")
            return None
        
        # 2. 生成代码
        try:
            # [关键修复] 根据代码对象类型决定是否在函数上下文中
            # 模块级别代码应该使用 in_function=False
            # [关键修复] 推导式函数（<listcomp>等）需要设置 in_function=True
            # 因为它们的AST包含 return 语句，需要在函数上下文中生成
            func_name = code_obj.co_name
            is_module = func_name == '<module>'
            is_comprehension = func_name in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>')
            source_code = self.code_generator.generate(ast_node, in_function=(not is_module) or is_comprehension)
            if self.verbose:
                logger.info("代码生成成功")
            return source_code
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return None
    
    def generate_ast(self, code_obj: types.CodeType,
                     name: Optional[str] = None) -> Optional[ASTNode]:
        """
        生成AST（CFG方法）

        Args:
            code_obj: Python代码对象
            name: 代码名称

        Returns:
            项目AST节点
        """
        if not self.use_cfg:
            return self._generate_with_traditional(code_obj, name)

        try:
            # 1. 构建CFG
            from core.cfg.cfg_builder import build_cfg
            cfg = build_cfg(code_obj, name or code_obj.co_name)

            if self.verbose:
                logger.info(f"CFG构建完成: {len(cfg.blocks)} 个基本块")

            # 2. 生成CFG AST（字典格式）
            from core.cfg.ast_generator_v2 import generate_ast_v2
            cfg_ast_dict = generate_ast_v2(cfg)

            if not cfg_ast_dict:
                logger.error("CFG AST生成失败")
                return None

            if self.verbose:
                logger.info("CFG AST生成完成")

            # 3. 转换为项目AST
            ast_node = self.ast_converter.convert(cfg_ast_dict)

            if ast_node and self.verbose:
                logger.info("AST转换完成")

            # 4. 包装为函数定义（如果是代码对象）
            # [关键修复] 只有当AST节点不是函数定义或类定义时才包装
            # 避免对已经生成的函数定义或类定义再次包装
            # [关键修复] 跳过推导式函数（<listcomp>, <dictcomp>, <setcomp>, <genexpr>）
            # 这些函数应该由推导式处理逻辑处理，而不是包装为普通函数
            func_name = code_obj.co_name
            is_comprehension = func_name in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>')
            if ast_node and func_name != '<module>' and not is_comprehension:
                if not isinstance(ast_node, (ASTFunctionDef, ASTClassDef)):
                    ast_node = self._wrap_function_def(ast_node, code_obj, name)

            return ast_node

        except Exception as e:
            logger.error(f"CFG AST生成失败: {e}")
            if self.verbose:
                logger.exception("详细错误信息")
            return None

    def _wrap_function_def(self, body_node: ASTNode, code_obj: types.CodeType,
                           name: Optional[str] = None) -> ASTNode:
        """
        将代码体包装为函数定义或类定义

        Args:
            body_node: 函数体AST节点
            code_obj: Python代码对象
            name: 函数名称

        Returns:
            ASTFunctionDef或ASTClassDef节点
        """
        func_name = name or code_obj.co_name

        # [关键修复] 检测是否是推导式函数，如果是则不包装
        # 推导式函数（<listcomp>, <dictcomp>, <setcomp>, <genexpr>）
        # 应该由推导式处理逻辑处理，而不是包装为普通函数
        if func_name in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>'):
            # 返回原始body_node，让推导式逻辑处理
            return body_node

        # [关键修复] 检测是否是类代码对象
        # 类代码对象的特征：
        # 1. 参数数量为0（类定义本身没有参数）
        # 2. 代码对象名称以大写字母开头（Python命名约定）
        # 3. 代码对象包含 __module__ 和 __qualname__ 的设置
        is_class = self._is_class_code_object(code_obj)

        if is_class:
            # 创建类定义
            return self._wrap_class_def(body_node, code_obj, func_name)
        
        # 提取参数名称列表
        varnames = list(code_obj.co_varnames)
        argcount = code_obj.co_argcount
        posonlyargcount = getattr(code_obj, 'co_posonlyargcount', 0)
        kwonlyargcount = getattr(code_obj, 'co_kwonlyargcount', 0)
        arg_names = varnames[:argcount]

        # 创建参数节点列表 (使用ASTName作为参数)
        from core.ast_nodes import ASTName
        args = [ASTName(name) for name in arg_names]

        # [关键修复] 提取*args和**kwargs
        CO_VARARGS = 0x0004
        CO_VARKEYWORDS = 0x0008
        flags = code_obj.co_flags

        vararg = None
        kwarg = None

        # [关键修复] Python 3.11+ 的参数顺序：
        # varnames = [posonly_args..., normal_args..., kwonly_args..., *args, **kwargs, local_vars...]
        # 其中：
        # - 前 argcount 个是位置参数（包括posonly和normal）
        # - 接下来 kwonlyargcount 个是keyword-only参数
        # - 然后是 *args（如果有 CO_VARARGS）
        # - 然后是 **kwargs（如果有 CO_VARKEYWORDS）
        # - 最后是局部变量

        idx = argcount  # 当前索引，从位置参数之后开始

        # [关键修复] 跳过keyword-only参数（在Python 3.11+中，kwonly参数在*args之前）
        idx += kwonlyargcount

        # 提取*args
        if flags & CO_VARARGS:
            if idx < len(varnames):
                vararg = varnames[idx]
                idx += 1

        # [关键修复] 提取**kwargs（使用计算出的索引，而不是总是取最后一个）
        if flags & CO_VARKEYWORDS:
            if idx < len(varnames):
                kwarg = varnames[idx]
                # idx += 1  # 不需要，因为kwargs后面都是局部变量

        # 确保body是ASTBlock
        if isinstance(body_node, ASTBlock):
            body = body_node
        else:
            body = ASTBlock()
            body.append(body_node)

        # [关键修复] 提取文档字符串
        # 在Python中，函数的文档字符串存储在co_consts[0]中
        docstring = None
        if (hasattr(code_obj, 'co_consts') and 
            len(code_obj.co_consts) > 0 and 
            isinstance(code_obj.co_consts[0], str)):
            # 检查co_consts[0]是否是文档字符串
            # 文档字符串通常是函数的第一条语句
            docstring = code_obj.co_consts[0]
        
        # [关键修复] 如果存在文档字符串，添加到函数体的开头
        if docstring:
            from core.ast_nodes import ASTConstant, ASTExpr
            doc_node = ASTExpr(ASTConstant(docstring))
            # 将文档字符串插入到body的开头
            new_body = ASTBlock()
            new_body.append(doc_node)
            for node in body.nodes:
                new_body.append(node)
            body = new_body

        # [异步] 检测是否是异步函数
        # CO_COROUTINE = 128 (0x80)
        # CO_ITERABLE_COROUTINE = 256 (0x100)
        is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100)
        
        # 创建函数定义
        func_def = ASTFunctionDef(
            name=func_name,
            args=args,
            body=body,
            vararg=vararg,
            kwarg=kwarg,
            is_async=is_async  # [异步] 传递异步标志
        )

        return func_def
    
    def _is_class_code_object(self, code_obj: types.CodeType) -> bool:
        """
        检测代码对象是否是类代码对象
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            是否是类代码对象
        """
        # 类代码对象的特征：
        # 1. 参数数量为0（类定义本身没有参数）
        if code_obj.co_argcount != 0:
            return False
        
        # 2. 代码对象名称以大写字母开头（Python命名约定）
        if not code_obj.co_name[0].isupper():
            return False
        
        # 3. 代码对象包含 __module__ 和 __qualname__ 的设置
        # 检查常量中是否有类名
        has_qualname = False
        for const in code_obj.co_consts:
            if isinstance(const, str) and const == code_obj.co_name:
                has_qualname = True
                break
        
        if not has_qualname:
            return False
        
        # 4. 检查是否有 __module__ 和 __qualname__ 在 names 中
        has_module = '__module__' in code_obj.co_names
        has_qualname_name = '__qualname__' in code_obj.co_names
        
        return has_module and has_qualname_name
    
    def _wrap_class_def(self, body_node: ASTNode, code_obj: types.CodeType,
                        class_name: str) -> ASTNode:
        """
        将代码体包装为类定义
        
        Args:
            body_node: 类体AST节点
            code_obj: Python代码对象
            class_name: 类名称
            
        Returns:
            ASTClassDef节点
        """
        from core.ast_nodes import ASTClassDef, ASTBlock, ASTPass
        
        # 确保body是ASTBlock
        if isinstance(body_node, ASTBlock):
            body = body_node
        else:
            body = ASTBlock()
            if body_node:
                body.append(body_node)
        
        # 如果body为空，添加pass
        if not body.nodes:
            body.append(ASTPass())
        
        # 创建类定义
        class_def = ASTClassDef(
            name=class_name,
            bases=[],  # 基类需要从代码中解析
            body=body
        )
        
        return class_def
    
    def _generate_with_traditional(self, code_obj: types.CodeType, 
                                   name: Optional[str] = None) -> Optional[ASTNode]:
        """
        使用传统方法生成AST（回退方案）
        
        Args:
            code_obj: Python代码对象
            name: 代码名称
            
        Returns:
            项目AST节点
        """
        try:
            from parsers.ast_builder import ASTBuilder
            from core.pyc_objects import PycModule
            
            # 创建最小化的模块对象
            module = PycModule()
            
            builder = ASTBuilder(module, code_obj)
            ast_node = builder.build_from_code(code_obj)
            
            if self.verbose:
                logger.info("传统方法AST生成完成")
            
            return ast_node
            
        except Exception as e:
            logger.error(f"传统方法AST生成失败: {e}")
            return None
    
    def generate_source(self, ast_node: ASTNode) -> str:
        """
        从AST生成源代码
        
        Args:
            ast_node: AST节点
            
        Returns:
            Python源代码
        """
        return self.code_generator.generate(ast_node)


class SmartDecompiler:
    """
    智能反编译器
    
    根据字节码特征自动选择最优方法，
    并确保输出质量。
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.matcher = BytecodeMatcher()
        self.cfg_generator = UnifiedASTGenerator(verbose=verbose, use_cfg=True)
        self.traditional_generator = UnifiedASTGenerator(verbose=verbose, use_cfg=False)
    
    def decompile(self, code_obj: types.CodeType, 
                  name: Optional[str] = None) -> Tuple[Optional[str], str]:
        """
        智能反编译
        
        Args:
            code_obj: Python代码对象
            name: 代码名称
            
        Returns:
            (源代码, 使用的方法) 元组
        """
        # 分析字节码，选择方法
        method = recommend_method(code_obj)
        
        if self.verbose:
            logger.info(f"[SmartDecompiler] 推荐方法: {method}")
        
        if method == 'cfg':
            # 尝试CFG方法
            result = self.cfg_generator.decompile(code_obj, name)
            if result:
                self.matcher.update_history(code_obj.co_name, 'cfg', True)
                return result, 'cfg'
            else:
                # CFG失败，回退到传统方法
                if self.verbose:
                    logger.info("CFG失败，回退到传统方法")
                result = self.traditional_generator.decompile(code_obj, name)
                self.matcher.update_history(code_obj.co_name, 'cfg', False)
                return result, 'traditional'
        else:
            # 直接使用传统方法
            result = self.traditional_generator.decompile(code_obj, name)
            self.matcher.update_history(code_obj.co_name, 'traditional', result is not None)
            return result, 'traditional'


# ==================== 便捷函数 ====================

def decompile_code(code_obj: types.CodeType, 
                   name: Optional[str] = None,
                   verbose: bool = False,
                   use_cfg: bool = True) -> Optional[str]:
    """
    便捷函数：反编译代码对象
    
    Args:
        code_obj: Python代码对象
        name: 代码名称
        verbose: 是否输出详细信息
        use_cfg: 是否使用CFG方法
        
    Returns:
        反编译后的Python源代码
    """
    generator = UnifiedASTGenerator(verbose=verbose, use_cfg=use_cfg)
    return generator.decompile(code_obj, name)


def decompile_function(func: types.FunctionType,
                       verbose: bool = False,
                       use_cfg: bool = True) -> Optional[str]:
    """
    便捷函数：反编译函数
    
    Args:
        func: Python函数
        verbose: 是否输出详细信息
        use_cfg: 是否使用CFG方法
        
    Returns:
        反编译后的Python源代码
    """
    return decompile_code(func.__code__, func.__name__, verbose, use_cfg)


def smart_decompile(code_obj: types.CodeType,
                    name: Optional[str] = None,
                    verbose: bool = False) -> Tuple[Optional[str], str]:
    """
    便捷函数：智能反编译（自动选择方法）
    
    Args:
        code_obj: Python代码对象
        name: 代码名称
        verbose: 是否输出详细信息
        
    Returns:
        (源代码, 使用的方法) 元组
    """
    decompiler = SmartDecompiler(verbose=verbose)
    return decompiler.decompile(code_obj, name)
