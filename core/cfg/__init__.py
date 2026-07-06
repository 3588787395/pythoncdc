"""
控制流图(CFG)模块

提供控制流图的构建、分析和结构化功能。

核心组件（基于区域归约算法，无补丁）：
- BasicBlock: 基本块定义
- Instruction: 指令定义
- CFGBuilder: 控制流图构建器
- DominatorAnalyzer: 支配树分析器（标准回边检测算法）
- LoopAnalyzer: 循环分析器（自然循环算法）
- CFGRegionAnalyzer: 区域分析器（区域归约算法）
- RegionASTGenerator: 基于区域的AST生成器
- OpcodeFeatureDetector: 操作码特征检测器（替代硬编码操作码名称）

使用示例：
    from core.cfg import build_cfg, CFGRegionAnalyzer, RegionASTGenerator

    cfg = build_cfg(code_obj)

    analyzer = CFGRegionAnalyzer(cfg)
    regions = analyzer.analyze()

    gen = RegionASTGenerator(cfg)
    ast_dict = gen.generate()

OpcodeFeatureDetector 使用示例：
    from core.cfg import get_opcode_detector

    detector = get_opcode_detector()
    if detector.is_conditional_jump(instruction):
        # 处理条件跳转...
"""

from .basic_block import BasicBlock, Instruction
from .cfg_builder import CFGBuilder, ControlFlowGraph, build_cfg
from .dominator_analyzer import DominatorAnalyzer, LoopAnalyzer

try:
    from .opcode_feature_detector import (
        OpcodeFeatureDetector,
        OpcodeCategory,
        get_opcode_detector,
        create_opcode_detector,
    )
    HAS_OPCODE_DETECTOR = True
except ImportError:
    HAS_OPCODE_DETECTOR = False

from .region_analyzer import (
    RegionAnalyzer as CFGRegionAnalyzer,
    Region,
    RegionType,
    IfRegion,
    LoopRegion,
    TryExceptRegion,
    WithRegion,
    MatchRegion,
    AssertRegion,
)
from .region_ast_generator import (
    RegionASTGenerator,
    generate_ast_from_regions,
)

from .structured_analyzer import (
    StructuredAnalyzer,
    ControlStructure,
    ControlStructureType,
    IfStructure,
    LoopStructure,
    TryExceptStructure,
)

try:
    from .ast_generator_v2 import (
        ASTGeneratorV2,
        ExpressionReconstructor,
        generate_ast_v2
    )
    HAS_V2 = True
except ImportError:
    HAS_V2 = False

try:
    from .ast_generator import ASTGenerator, ASTBuilder, generate_ast
    HAS_V1 = True
except ImportError:
    HAS_V1 = False
    if HAS_V2:
        ASTGenerator = ASTGeneratorV2
        generate_ast = generate_ast_v2

try:
    from .cfg_optimizer import (
        PerformanceProfiler,
        MemoryOptimizer,
        CFGCache,
        OptimizedCFGBuilder,
        DominatorOptimizer,
        optimize_cfg_building,
        profiler
    )
    HAS_OPTIMIZER = True
except ImportError:
    HAS_OPTIMIZER = False

try:
    from .cfg_visualizer import (
        CFGTextVisualizer,
        CFGDotVisualizer,
        CFGHTMLVisualizer,
        visualize_cfg,
        print_cfg,
        save_cfg_dot,
        save_cfg_html
    )
    HAS_VISUALIZER = True
except ImportError:
    HAS_VISUALIZER = False

__all__ = [
    'BasicBlock',
    'Instruction',
    'CFGBuilder',
    'ControlFlowGraph',
    'build_cfg',
    'DominatorAnalyzer',
    'LoopAnalyzer',
    'OpcodeFeatureDetector',
    'OpcodeCategory',
    'get_opcode_detector',
    'create_opcode_detector',
    'CFGRegionAnalyzer',
    'Region',
    'RegionType',
    'IfRegion',
    'LoopRegion',
    'TryExceptRegion',
    'WithRegion',
    'MatchRegion',
    'AssertRegion',
    'RegionASTGenerator',
    'generate_ast_from_regions',
    'StructuredAnalyzer',
    'ControlStructure',
    'ControlStructureType',
    'IfStructure',
    'LoopStructure',
    'TryExceptStructure',
    'ASTGenerator',
    'ASTBuilder',
    'generate_ast',
]

if HAS_V2:
    __all__.extend([
        'ASTGeneratorV2',
        'ExpressionReconstructor',
        'generate_ast_v2',
    ])

if HAS_OPTIMIZER:
    __all__.extend([
        'PerformanceProfiler',
        'MemoryOptimizer',
        'CFGCache',
        'OptimizedCFGBuilder',
        'DominatorOptimizer',
        'optimize_cfg_building',
        'profiler',
    ])

if HAS_VISUALIZER:
    __all__.extend([
        'CFGTextVisualizer',
        'CFGDotVisualizer',
        'CFGHTMLVisualizer',
        'visualize_cfg',
        'print_cfg',
        'save_cfg_dot',
        'save_cfg_html',
    ])


def decompile(source: str, filename: str = '<string>', use_region: bool = True) -> str:
    import types

    code_obj = compile(source, filename, 'exec')

    cfg = build_cfg(code_obj)

    if use_region:
        from .region_ast_generator import RegionASTGenerator
        from .ast_converter import CFGASTConverter
        from .code_generator import CodeGenerator

        gen = RegionASTGenerator(cfg)
        ast_dict = gen.generate()
        converter = CFGASTConverter()
        py_ast = converter.convert(ast_dict)
        generator = CodeGenerator()
        return generator.generate(py_ast)
    elif HAS_V2:
        from .ast_generator_v2 import generate_ast_v2
        from .ast_converter import CFGASTConverter
        from .code_generator import CodeGenerator

        ast_dict = generate_ast_v2(cfg)
        converter = CFGASTConverter()
        py_ast = converter.convert(ast_dict)
        generator = CodeGenerator()
        return generator.generate(py_ast)
    else:
        from .ast_converter import CFGASTConverter
        from .code_generator import CodeGenerator

        ast_dict = generate_ast(cfg)
        converter = CFGASTConverter()
        py_ast = converter.convert(ast_dict)
        generator = CodeGenerator()
        return generator.generate(py_ast)

def decompile_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return decompile(source, filepath)

__all__.extend(['decompile', 'decompile_file'])
