# CFG模块用户使用手册

## 快速开始

### 1. 命令行使用

最简单的方式是通过命令行使用：

```bash
# 基本反编译（传统方法）
python pycdc.py input.pyc

# 使用CFG模式（推荐）
python pycdc.py --cfg-hybrid input.pyc

# 输出到文件
python pycdc.py --cfg-hybrid -o output.py input.pyc

# 显示详细信息
python pycdc.py --cfg --cfg-verbose input.pyc
```

### 2. 编程使用

在Python代码中使用：

```python
import sys
sys.path.insert(0, 'path/to/pythoncdc')

from core.config import enable_cfg
from pycdc import PycDecompiler

# 启用CFG模式
enable_cfg(verbose=True, use_v2=True)

# 创建反编译器
decompiler = PycDecompiler()
decompiler.load_file('input.pyc')

# 反编译
import io
output = io.StringIO()
decompiler.decompile(output)
print(output.getvalue())
```

## 功能介绍

### CFG模式

CFG（控制流图）模式通过分析代码的控制流来生成更准确的反编译结果。

**优点：**
- 更好的控制结构识别（if/while/for）
- 更准确的表达式重建
- 支持复杂代码模式

**使用场景：**
- 复杂函数的反编译
- 需要高质量输出的场景
- 分析代码结构

### 混合模式

混合模式结合传统方法和CFG方法的优点：

1. 首先尝试使用CFG方法
2. 如果失败，自动回退到传统方法

**推荐使用混合模式**，因为它既保证了质量又保证了可靠性。

## 配置选项

### 启用/禁用CFG

```python
from core.config import enable_cfg, disable_cfg

# 启用CFG V2版本
enable_cfg(verbose=True, use_v2=True)

# 禁用CFG（使用传统方法）
disable_cfg()
```

### 选择CFG版本

```python
from core.config import CFGVersion, set_cfg_version

# 使用V2版本（推荐）
set_cfg_version(CFGVersion.V2)

# 使用V1版本
set_cfg_version(CFGVersion.V1)
```

### 设置混合模式

```python
from core.config import set_hybrid_mode

# 启用混合模式
set_hybrid_mode(verbose=False, use_v2=True)
```

## 高级功能

### 1. 可视化CFG

```python
from core.cfg.cfg_builder import build_cfg
from core.cfg.cfg_visualizer import save_cfg_html, save_cfg_dot

# 构建CFG
cfg = build_cfg(code_obj, "my_function")

# 保存为HTML（交互式）
save_cfg_html(cfg, "cfg.html", "My CFG")

# 保存为DOT格式（可用Graphviz渲染）
save_cfg_dot(cfg, "cfg.dot")
```

### 2. 性能优化

```python
from core.cfg.cfg_optimizer import OptimizedCFGBuilder

# 创建优化构建器
builder = OptimizedCFGBuilder(use_cache=True, optimize_memory=True)

# 构建CFG（会自动缓存）
cfg = builder.build(code_obj)

# 再次构建同一code_obj会使用缓存（快132倍！）
cfg2 = builder.build(code_obj)
```

### 3. 分析代码结构

```python
from core.cfg.cfg_builder import build_cfg
from core.cfg.dominator_analyzer import analyze_dominators, analyze_loops

# 构建CFG
cfg = build_cfg(code_obj)

# 分析支配节点
dom_analyzer = analyze_dominators(cfg)

# 分析循环
loop_analyzer = analyze_loops(cfg, dom_analyzer)
loops = loop_analyzer.get_all_loops()

print(f"发现 {len(loops)} 个循环")
```

## 常见问题

### Q: CFG模式和传统模式有什么区别？

**A:** CFG模式通过分析代码的控制流图来生成更准确的反编译结果，特别适合复杂代码。传统模式使用更简单的方法，速度更快但准确性可能稍差。

### Q: 什么时候使用混合模式？

**A:** 推荐始终使用混合模式（`--cfg-hybrid`）。它会在CFG方法失败时自动回退到传统方法，既保证了质量又保证了可靠性。

### Q: V1和V2版本有什么区别？

**A:** V2版本提供了更好的表达式重建功能，可以处理更复杂的表达式。V1版本更简单但可能不够准确。推荐使用V2版本。

### Q: 如何可视化CFG？

**A:** 使用`save_cfg_html()`函数可以生成交互式HTML可视化，使用`save_cfg_dot()`可以生成DOT格式文件（需要Graphviz渲染）。

### Q: 性能如何优化？

**A:** 使用`OptimizedCFGBuilder`并启用缓存。对于重复构建同一code_obj，缓存可以提供132倍的加速。

### Q: 支持哪些Python版本？

**A:** 支持Python 3.8、3.9、3.10、3.11、3.12。

## 示例

### 示例1：基本反编译

```python
from core.config import enable_cfg
from pycdc import PycDecompiler
import io

# 启用CFG
enable_cfg()

# 反编译
decompiler = PycDecompiler()
decompiler.load_file('example.pyc')

output = io.StringIO()
decompiler.decompile(output)
print(output.getvalue())
```

### 示例2：可视化函数CFG

```python
from core.cfg.cfg_builder import build_cfg
from core.cfg.cfg_visualizer import save_cfg_html

def example(x, y):
    if x > 0:
        return x + y
    return x - y

cfg = build_cfg(example.__code__, "example")
save_cfg_html(cfg, "example_cfg.html")
print("可视化已保存到 example_cfg.html")
```

### 示例3：批量处理

```python
from core.cfg.cfg_optimizer import OptimizedCFGBuilder
from core.cfg.cfg_builder import build_cfg

builder = OptimizedCFGBuilder(use_cache=True)

for code_obj in code_objects:
    cfg = builder.build(code_obj)
    # 处理CFG...
```

## 故障排除

### 问题：Unicode编码错误

**解决：** 在Windows上，确保使用UTF-8编码：
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 问题：模块导入失败

**解决：** 确保项目路径正确添加：
```python
import sys
sys.path.insert(0, 'path/to/pythoncdc')
```

### 问题：CFG构建失败

**解决：** 使用混合模式自动回退：
```python
from core.config import set_hybrid_mode
set_hybrid_mode()
```

## 获取帮助

- 查看API文档：`docs/CFG_API_Reference.md`
- 查看完整总结：`CFG_COMPLETE_SUMMARY.md`
- 运行测试：`python run_all_tests.py`
- 查看示例：`demo_cfg.py`

## 贡献

如果您发现问题或有改进建议，欢迎提交Issue或Pull Request。

---

**祝您使用愉快！**
