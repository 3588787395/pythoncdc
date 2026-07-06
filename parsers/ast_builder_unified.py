"""
统一AST构建器

该模块提供一个统一的AST构建器接口，整合基于CFG和传统方法的AST构建。
"""

import types
from typing import Optional, Dict, Any, Union
from enum import Enum, auto


class BuilderMode(Enum):
    """构建器模式"""
    CFG = auto()
    TRADITIONAL = auto()
    HYBRID = auto()


class UnifiedASTBuilder:
    """
    统一AST构建器
    
    提供统一的接口来使用不同的AST构建方法。
    """
    
    def __init__(self, mode: BuilderMode = BuilderMode.CFG, verbose: bool = False):
        """
        初始化统一构建器
        
        Args:
            mode: 构建模式
            verbose: 是否输出详细信息
        """
        self.mode = mode
        self.verbose = verbose
        self._cfg_builder = None
        self._traditional_builder = None
    
    def build(self, code_obj: types.CodeType, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        构建AST
        
        Args:
            code_obj: Python代码对象
            name: 代码名称
            
        Returns:
            AST字典
        """
        if self.mode == BuilderMode.CFG:
            return self._build_with_cfg(code_obj, name)
        elif self.mode == BuilderMode.TRADITIONAL:
            return self._build_traditional(code_obj, name)
        else:
            return self._build_hybrid(code_obj, name)
    
    def build_from_function(self, func: types.FunctionType) -> Optional[Dict[str, Any]]:
        """
        从函数构建AST
        
        Args:
            func: Python函数
            
        Returns:
            AST字典
        """
        return self.build(func.__code__, func.__name__)
    
    def build_from_source(self, source: str, name: str = "<module>") -> Optional[Dict[str, Any]]:
        """
        从源代码构建AST
        
        Args:
            source: Python源代码
            name: 模块名称
            
        Returns:
            AST字典
        """
        try:
            code_obj = compile(source, name, 'exec')
            return self.build(code_obj, name)
        except SyntaxError:
            return None
    
    def _build_with_cfg(self, code_obj: types.CodeType, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """使用CFG方法构建"""
        try:
            from parsers.ast_builder_cfg import CFGASTBuilder
            self._cfg_builder = CFGASTBuilder(verbose=self.verbose)
            return self._cfg_builder.build_from_code(code_obj, name)
        except ImportError:
            if self.verbose:
                print("CFG builder not available, falling back to traditional")
            return self._build_traditional(code_obj, name)
    
    def _build_traditional(self, code_obj: types.CodeType, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """使用传统方法构建"""
        try:
            from parsers.ast_builder import ASTBuilder
            self._traditional_builder = ASTBuilder()
            return self._traditional_builder.build(code_obj, name)
        except ImportError:
            return None
    
    def _build_hybrid(self, code_obj: types.CodeType, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """使用混合方法构建"""
        cfg_result = self._build_with_cfg(code_obj, name)
        if cfg_result:
            return cfg_result
        return self._build_traditional(code_obj, name)
    
    def set_mode(self, mode: BuilderMode) -> None:
        """
        设置构建模式
        
        Args:
            mode: 新模式
        """
        self.mode = mode
    
    def get_mode(self) -> BuilderMode:
        """
        获取当前构建模式
        
        Returns:
            当前模式
        """
        return self.mode


def build_ast(code_obj: types.CodeType, 
              mode: BuilderMode = BuilderMode.CFG,
              verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    便捷函数：构建AST
    
    Args:
        code_obj: Python代码对象
        mode: 构建模式
        verbose: 是否输出详细信息
        
    Returns:
        AST字典
    """
    builder = UnifiedASTBuilder(mode=mode, verbose=verbose)
    return builder.build(code_obj)


def build_ast_from_function(func: types.FunctionType,
                            mode: BuilderMode = BuilderMode.CFG,
                            verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    便捷函数：从函数构建AST
    
    Args:
        func: Python函数
        mode: 构建模式
        verbose: 是否输出详细信息
        
    Returns:
        AST字典
    """
    builder = UnifiedASTBuilder(mode=mode, verbose=verbose)
    return builder.build_from_function(func)


def build_ast_from_source(source: str,
                          name: str = "<module>",
                          mode: BuilderMode = BuilderMode.CFG,
                          verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    便捷函数：从源代码构建AST
    
    Args:
        source: Python源代码
        name: 模块名称
        mode: 构建模式
        verbose: 是否输出详细信息
        
    Returns:
        AST字典
    """
    builder = UnifiedASTBuilder(mode=mode, verbose=verbose)
    return builder.build_from_source(source, name)
