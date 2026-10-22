# Source Generated with Decompyle++ (Python version)
# File: repo_core_config.pyc (Python 3.11)

__doc__ = """
配置模块

提供全局配置选项，包括CFG模块的启用/禁用。
"""
from typing import Optional
from enum import Enum, auto
class CFGMode(Enum):
    __doc__ = 'CFG模式'
    DISABLED = auto()
    ENABLED = auto()
    HYBRID = auto()
class CFGVersion(Enum):
    __doc__ = 'CFG版本'
    V1 = auto()
    V2 = auto()
class Config:
    __doc__ = """
    全局配置类
    
    用于控制反编译器的各种选项。
    """
    cfg_mode: CFGMode = CFGMode.DISABLED
    cfg_verbose: bool = False
    cfg_version: CFGVersion = CFGVersion.V2
    debug: bool = False
    debug_filter: list = []
    @classmethod
    def enable_cfg(cls, verbose: bool=False):
        """
        启用CFG模块
        
        Args:
            verbose: 是否输出详细信息
        """
        cls.cfg_mode = CFGMode.ENABLED
        cls.cfg_verbose = verbose
    @classmethod
    def disable_cfg(cls):
        """禁用CFG模块"""
        cls.cfg_mode = CFGMode.DISABLED
    @classmethod
    def set_hybrid_mode(cls, verbose: bool=False):
        """
        设置混合模式
        
        Args:
            verbose: 是否输出详细信息
        """
        cls.cfg_mode = CFGMode.HYBRID
        cls.cfg_verbose = verbose
    @classmethod
    def is_cfg_enabled(cls) -> bool:
        """
        检查CFG是否启用
        
        Returns:
            如果CFG启用返回True
        """
        return cls.cfg_mode in (CFGMode.ENABLED, CFGMode.HYBRID)
    @classmethod
    def is_hybrid_mode(cls) -> bool:
        """
        检查是否为混合模式
        
        Returns:
            如果是混合模式返回True
        """
        return cls.cfg_mode == CFGMode.HYBRID
    @classmethod
    def set_cfg_version(cls, version: CFGVersion):
        """
        设置CFG版本
        
        Args:
            version: CFG版本
        """
        cls.cfg_version = version
    @classmethod
    def use_cfg_v2(cls) -> bool:
        """
        检查是否使用CFG V2版本
        
        Returns:
            如果使用V2返回True
        """
        return cls.cfg_version == CFGVersion.V2
def enable_cfg(verbose: bool=False, use_v2: bool=True):
    """启用CFG模块
    
    Args:
        verbose: 是否输出详细信息
        use_v2: 是否使用V2版本（默认True）
    """
    Config.enable_cfg(verbose)
    if use_v2:
        Config.cfg_version = CFGVersion.V2
        return None
    else:
        Config.cfg_version = CFGVersion.V1
def disable_cfg():
    """禁用CFG模块"""
    Config.disable_cfg()
def set_hybrid_mode(verbose: bool=False, use_v2: bool=True):
    """设置混合模式
    
    Args:
        verbose: 是否输出详细信息
        use_v2: 是否使用V2版本（默认True）
    """
    Config.set_hybrid_mode(verbose)
    if use_v2:
        Config.cfg_version = CFGVersion.V2
        return None
    else:
        Config.cfg_version = CFGVersion.V1
def set_cfg_version(version: CFGVersion):
    """设置CFG版本"""
    Config.set_cfg_version(version)
