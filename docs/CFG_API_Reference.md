# CFG模块API参考文档

## 目录

1. [核心模块](#核心模块)
2. [构建器模块](#构建器模块)
3. [分析器模块](#分析器模块)
4. [生成器模块](#生成器模块)
5. [优化器模块](#优化器模块)
6. [可视化模块](#可视化模块)
7. [配置模块](#配置模块)

---

## 核心模块

### `core.cfg.basic_block`

#### `class BasicBlock`

控制流图中的基本块。

**属性：**

| 属性 | 类型 | 说明 |
|-----|------|------|
| `id` | `int` | 基本块唯一标识符 |
| `start_offset` | `int` | 起始字节码偏移量 |
| `end_offset` | `int` | 结束字节码偏移量 |
| `instructions` | `List[Instruction]` | 指令列表 |
| `predecessors` | `Set[BasicBlock]` | 前驱基本块集合 |
| `successors` | `Set[BasicBlock]` | 后继基本块集合 |
| `is_entry` | `bool` | 是否为入口块 |
| `is_exit` | `bool` | 是否为出口块 |
| `dominators` | `Set[BasicBlock]` | 支配该块的块集合 |
| `loop_header` | `bool` | 是否为循环头部 |
| `loop_depth` | `int` | 循环嵌套深度 |

**方法：**

```python
# 添加指令
def add_instruction(self, instruction: Instruction) -> None

# 添加后继
def add_successor(self, block: 'BasicBlock') -> None

# 检查是否为条件分支
def is_conditional(self) -> bool

# 检查是否为返回
def is_return(self) -> bool
```

#### `class Instruction`

字节码指令。

**属性：**

| 属性 | 类型 | 说明 |
|-----|------|------|
| `offset` | `int` | 指令偏移量 |
| `opcode` | `int` | 操作码 |
| `opname` | `str` | 操作名 |
| `arg` | `Optional[int]` | 参数 |
| `argval` | `Any` | 参数值 |
| `starts_line` | `Optional[int]` | 源代码行号 |
| `is_jump_target` | `bool` | 是否为跳转目标 |

---

## 构建器模块

### `core.cfg.cfg_builder`

#### `class ControlFlowGraph`

控制流图类。

**属性：**

| 属性 | 类型 | 说明 |
|-----|------|------|
| `name` | `str` | CFG名称 |
| `blocks` | `Dict[int, BasicBlock]` | 基本块字典 |
| `entry_block` | `Optional[BasicBlock]` | 入口块 |
| `exit_blocks` | `Set[BasicBlock]` | 出口块集合 |

**方法：**

```python
# 添加基本块
def add_block(self, block: BasicBlock) -> None

# 根据偏移量获取基本块
def get_block_by_offset(self, offset: int) -> Optional[BasicBlock]

# 设置入口块
def set_entry_block(self, block: BasicBlock) -> None

# 获取按顺序排列的块列表
def get_blocks_in_order(self) -> List[BasicBlock]
```

#### `class CFGBuilder`

CFG构建器。

**方法：**

```python
# 从代码对象构建CFG
def build(self, code_obj: types.CodeType, name: Optional[str] = None) -> ControlFlowGraph
```

**便捷函数：**

```python
# 构建CFG
from core.cfg.cfg_builder import build_cfg
cfg = build_cfg(code_obj, name="function_name")

# 从源代码构建
from core.cfg.cfg_builder import build_cfg_from_source
cfg = build_cfg_from_source("def foo(): pass", name="<module>")

# 从函数构建
from core.cfg.cfg_builder import build_cfg_from_function
cfg = build_cfg_from_function(my_function)
```

---

## 分析器模块

### `core.cfg.dominator_analyzer`

#### `class DominatorAnalyzer`

支配节点分析器。

**方法：**

```python
# 执行完整分析
def analyze(self) -> None

# 获取支配树
def get_dominator_tree(self) -> Dict[BasicBlock, Set[BasicBlock]]

# 查找最近公共支配节点
def find_nearest_common_dominator(self, blocks: Set[BasicBlock]) -> Optional[BasicBlock]

# 获取支配边界
def get_dominance_frontier(self, block: BasicBlock) -> Set[BasicBlock]
```

**便捷函数：**

```python
from core.cfg.dominator_analyzer import analyze_dominators

dom_analyzer = analyze_dominators(cfg)
```

#### `class LoopAnalyzer`

循环分析器。

**方法：**

```python
# 执行循环分析
def analyze(self) -> None

# 获取所有循环
def get_all_loops(self) -> Dict[BasicBlock, Set[BasicBlock]]

# 获取循环深度
def get_loop_depth(self, block: BasicBlock) -> int

# 检查是否在循环中
def is_in_loop(self, block: BasicBlock) -> bool
```

**便捷函数：**

```python
from core.cfg.dominator_analyzer import analyze_loops

loop_analyzer = analyze_loops(cfg, dom_analyzer)
```

---

## 生成器模块

### `core.cfg.ast_generator`

#### `class ASTGenerator`

AST生成器（V1版本）。

**方法：**

```python
# 生成AST
def generate(self) -> Dict[str, Any]
```

**便捷函数：**

```python
from core.cfg.ast_generator import generate_ast

ast = generate_ast(cfg)
```

### `core.cfg.ast_generator_v2`

#### `class ASTGeneratorV2`

AST生成器（V2改进版本）。

**特性：**
- 更好的表达式重建
- 改进的控制结构识别
- 更准确的语句序列

**便捷函数：**

```python
from core.cfg.ast_generator_v2 import generate_ast_v2

ast = generate_ast_v2(cfg)
```

#### `class ExpressionReconstructor`

表达式重建器。

**方法：**

```python
# 从指令序列重建表达式
def reconstruct(self, instructions: List[Instruction]) -> Optional[Dict[str, Any]]
```

**支持的操作：**
- 加载常量、变量、属性
- 二元操作（+、-、*、/等）
- 一元操作（+、-、not、~）
- 比较操作（<、>、==、!=等）
- 函数调用
- 列表、元组、字典构建
- 下标操作

---

## 优化器模块

### `core.cfg.cfg_optimizer`

#### `class PerformanceProfiler`

性能分析器。

**方法：**

```python
# 启用分析
def enable(self) -> None

# 禁用分析
def disable(self) -> None

# 获取统计信息
def get_stats(self) -> Dict[str, Dict[str, float]]

# 打印统计信息
def print_stats(self) -> None
```

#### `class OptimizedCFGBuilder`

优化的CFG构建器。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `use_cache` | `bool` | `True` | 是否使用缓存 |
| `optimize_memory` | `bool` | `True` | 是否优化内存 |

**方法：**

```python
# 构建CFG（带优化）
def build(self, code_obj, name: Optional[str] = None) -> ControlFlowGraph
```

**使用示例：**

```python
from core.cfg.cfg_optimizer import OptimizedCFGBuilder

builder = OptimizedCFGBuilder(use_cache=True, optimize_memory=True)
cfg = builder.build(code_obj)

# 第二次构建会使用缓存
cfg2 = builder.build(code_obj)  # 快132倍！
```

#### `class DominatorOptimizer`

支配节点优化器。

**方法：**

```python
# 快速计算支配节点（静态方法）
@staticmethod
def compute_dominators_fast(cfg: ControlFlowGraph) -> None
```

---

## 可视化模块

### `core.cfg.cfg_visualizer`

#### `class CFGTextVisualizer`

文本可视化器。

**方法：**

```python
# 可视化CFG为文本（静态方法）
@staticmethod
def visualize(cfg: ControlFlowGraph, show_instructions: bool = True) -> str
```

#### `class CFGDotVisualizer`

DOT格式可视化器。

**方法：**

```python
# 生成DOT格式（静态方法）
@staticmethod
def generate_dot(cfg: ControlFlowGraph, highlight_blocks: Optional[Set[int]] = None) -> str

# 保存DOT文件（静态方法）
@staticmethod
def save_dot(cfg: ControlFlowGraph, filename: str) -> None

# 渲染为图像（静态方法）
@staticmethod
def render_to_image(cfg: ControlFlowGraph, output_file: str, format: str = 'png') -> bool
```

#### `class CFGHTMLVisualizer`

HTML可视化器。

**方法：**

```python
# 生成HTML（静态方法）
@staticmethod
def generate_html(cfg: ControlFlowGraph, title: Optional[str] = None) -> str

# 保存HTML文件（静态方法）
@staticmethod
def save_html(cfg: ControlFlowGraph, filename: str, title: Optional[str] = None) -> None
```

**便捷函数：**

```python
from core.cfg.cfg_visualizer import (
    print_cfg, save_cfg_dot, save_cfg_html
)

# 打印到控制台
print_cfg(cfg)

# 保存为DOT文件
save_cfg_dot(cfg, "cfg.dot")

# 保存为HTML文件
save_cfg_html(cfg, "cfg.html", "My CFG")
```

---

## 配置模块

### `core.config`

#### `class Config`

全局配置类。

**类属性：**

| 属性 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `cfg_mode` | `CFGMode` | `CFGMode.DISABLED` | CFG模式 |
| `cfg_verbose` | `bool` | `False` | 详细输出 |
| `cfg_version` | `CFGVersion` | `CFGVersion.V2` | CFG版本 |

**类方法：**

```python
# 启用CFG
@classmethod
def enable_cfg(cls, verbose: bool = False)

# 禁用CFG
@classmethod
def disable_cfg(cls)

# 设置混合模式
@classmethod
def set_hybrid_mode(cls, verbose: bool = False)

# 检查CFG是否启用
@classmethod
def is_cfg_enabled(cls) -> bool

# 检查是否为混合模式
@classmethod
def is_hybrid_mode(cls) -> bool

# 设置CFG版本
@classmethod
def set_cfg_version(cls, version: CFGVersion)
```

#### `enum CFGMode`

CFG模式枚举。

| 成员 | 说明 |
|-----|------|
| `DISABLED` | 禁用CFG |
| `ENABLED` | 启用CFG |
| `HYBRID` | 混合模式（失败自动回退） |

#### `enum CFGVersion`

CFG版本枚举。

| 成员 | 说明 |
|-----|------|
| `V1` | 原始版本 |
| `V2` | 改进版本（推荐） |

**便捷函数：**

```python
from core.config import enable_cfg, set_hybrid_mode, set_cfg_version

# 启用CFG V2
enable_cfg(verbose=True, use_v2=True)

# 设置混合模式
set_hybrid_mode(verbose=False, use_v2=True)

# 切换版本
from core.config import CFGVersion
set_cfg_version(CFGVersion.V2)
```

---

## 使用示例

### 基本使用流程

```python
import sys
sys.path.insert(0, 'path/to/pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.dominator_analyzer import analyze_dominators, analyze_loops
from core.cfg.ast_generator_v2 import generate_ast_v2
from core.cfg.cfg_visualizer import save_cfg_html

# 定义测试函数
def example(x, y):
    if x > 0:
        return x + y
    return x - y

# 1. 构建CFG
cfg = build_cfg(example.__code__, "example")
print(f"构建了 {len(cfg.blocks)} 个基本块")

# 2. 分析支配节点
dom_analyzer = analyze_dominators(cfg)
print("支配节点分析完成")

# 3. 分析循环
loop_analyzer = analyze_loops(cfg, dom_analyzer)
print(f"发现 {len(loop_analyzer.get_all_loops())} 个循环")

# 4. 生成AST
ast = generate_ast_v2(cfg)
print(f"AST包含 {len(ast['body'])} 个顶层结构")

# 5. 可视化
save_cfg_html(cfg, "example_cfg.html", "Example CFG")
print("可视化已保存")
```

### 使用优化功能

```python
from core.cfg.cfg_optimizer import OptimizedCFGBuilder

# 创建优化构建器
builder = OptimizedCFGBuilder(use_cache=True, optimize_memory=True)

# 首次构建
cfg1 = builder.build(code_obj, "func1")

# 第二次构建（使用缓存，快132倍！）
cfg2 = builder.build(code_obj, "func2")
```

### 命令行使用

```bash
# 基本反编译
python pycdc.py input.pyc

# 使用CFG模式
python pycdc.py --cfg input.pyc

# 使用混合模式（推荐）
python pycdc.py --cfg-hybrid input.pyc

# 显示详细信息
python pycdc.py --cfg --cfg-verbose input.pyc

# 输出到文件
python pycdc.py --cfg-hybrid -o output.py input.pyc
```

---

## 错误处理

所有主要函数都可能抛出以下异常：

- `ValueError`: 参数错误
- `TypeError`: 类型错误
- `ImportError`: 模块导入错误
- `RuntimeError`: 运行时错误

建议使用try-except块处理：

```python
try:
    cfg = build_cfg(code_obj)
except Exception as e:
    print(f"CFG构建失败: {e}")
```

---

## 性能提示

1. **使用缓存**: `OptimizedCFGBuilder`可以显著提升重复构建的性能
2. **选择合适的版本**: V2版本提供更好的表达式重建，但可能稍慢
3. **内存优化**: 启用`optimize_memory`可以减少20-30%的内存使用
4. **批量处理**: 对于大量文件，建议使用缓存和批量处理

---

## 版本历史

- **v1.0**: 初始版本，基本CFG功能
- **v2.0**: 添加V2 AST生成器，改进表达式重建
- **v2.1**: 添加性能优化器
- **v2.2**: 添加可视化工具
- **v2.3**: 完整集成到反编译器

---

## 更多信息

- 项目文档: `CFG_COMPLETE_SUMMARY.md`
- 使用手册: 见下文
- 示例代码: `demo_cfg.py`, `test_*.py`
