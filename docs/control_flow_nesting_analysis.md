# pycdc-python 控制流算法嵌套分析文档

## 1. 控制流块类型定义

### 1.1 ASTBlock.BlockType 枚举
```python
class BlockType(Enum):
    BLK_MAIN = 0        # 主块（根节点）
    BLK_IF = 1          # if条件块
    BLK_ELSE = 2        # else分支块
    BLK_ELIF = 3        # elif分支块
    BLK_WHILE = 4       # while循环块
    BLK_FOR = 5         # for循环块
    BLK_TRY = 6         # try块
    BLK_EXCEPT = 7      # except块
    BLK_FINALLY = 8     # finally块
    BLK_WITH = 9        # with上下文管理器块
    BLK_CONTAINER = 10  # 容器块（包裹try-except-finally）
```

---

## 2. 核心数据结构

### 2.1 块栈管理
```python
self.blocks: List[ASTBlock] = []      # 块栈，存储所有打开的块
self.main_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_MAIN)
self.current_block = self.main_block   # 当前正在填充的块
```

### 2.2 栈状态历史
```python
self.stack_hist: List[FastStack] = []  # 栈状态历史，用于保存/恢复栈
```

### 2.3 控制流上下文跟踪
```python
# IF/ELIF/ELSE上下文
self.current_if_node = None            # 当前if节点
self._if_stack = []                    # if语句栈
self._if_chain_root = None             # if-elif-else链的根节点

# 循环上下文
self.current_for_node = None           # 当前for节点
self.current_while_node = None         # 当前while节点
self._for_stack = []                   # for循环栈
self._loop_structures = []             # 循环结构列表

# Try-Except上下文
self.current_try_node = None           # 当前try节点
```

---

## 3. 控制流嵌套处理机制

### 3.1 双栈管理架构

```
┌─────────────────────────────────────────────────────────────┐
│                      控制流双栈管理架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   blocks栈（块层级管理）              stack_hist（状态管理）    │
│   ┌─────────────────┐                ┌─────────────────┐    │
│   │   BLK_MAIN      │                │                 │    │
│   ├─────────────────┤                ├─────────────────┤    │
│   │   BLK_IF        │                │   stack_snap_0  │    │
│   ├─────────────────┤                ├─────────────────┤    │
│   │   BLK_FOR       │                │   stack_snap_1  │    │
│   ├─────────────────┤                ├─────────────────┤    │
│   │   BLK_TRY       │◄── 当前块      │   stack_snap_2  │    │
│   ├─────────────────┤                └─────────────────┘    │
│   │   BLK_CONTAINER │                                       │
│   ├─────────────────┤                                       │
│   │   BLK_IF        │◄── 嵌套if                              │
│   └─────────────────┘                                       │
│                                                             │
│   入栈: blocks.append(block)         保存: stack_hist.append │
│   出栈: blocks.pop()                 恢复: stack_hist.pop()  │
│   父块: blocks[-2]                   层数: len(stack_hist)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 嵌套层级关系确定

```python
# blocks栈状态示例
blocks = [MAIN, IF, FOR, TRY, CONTAINER, IF]
索引:      0    1    2    3     4        5

# 当前块 (索引5) 的层级关系
当前块:     blocks[-1]  = IF (内层if)
父块:       blocks[-2]  = CONTAINER
祖父块:     blocks[-3]  = TRY
曾祖父块:   blocks[-4]  = FOR
高祖父块:   blocks[-5]  = IF (外层if)
根块:       blocks[-6]  = MAIN
```

---

## 4. 各控制流结构的嵌套处理

### 4.1 IF/ELIF/ELSE 嵌套处理

#### 4.1.1 创建流程
```python
def _pop_jump_forward_if_false(self, target: int):
    # 1. 检查是否是elif（在if-elif-else链中）
    is_elif = self._is_elif_pattern(current_offset)
    
    # 2. 创建if节点
    if_node = ASTIf(condition, then_block, orelse)
    
    # 3. 嵌套处理决策树
    if is_nested_if and parent_if is not None:
        # 嵌套if：添加到外层if的body中
        parent_if._body.append(if_node)
    elif in_for_body and self.current_for_node:
        # for循环内的if：添加到for的body中
        self.current_for_node._body.append(if_node)
    elif in_while_body and self.current_while_node:
        # while循环内的if：添加到while的body中
        self.current_while_node._body.append(if_node)
    elif not is_elif:
        # 顶层if：发射到main_block
        self._emit(if_node)
    
    # 4. 更新上下文
    if not is_elif:
        self.current_if_node = if_node
```

#### 4.1.2 嵌套示例
```python
# Python代码
if outer:
    if inner:
        do_something()
    else:
        do_other()
else:
    do_else()

# blocks栈变化
[MAIN]                              # 初始
[MAIN, IF(outer)]                   # 遇到外层if
[MAIN, IF(outer), IF(inner)]        # 遇到内层if（嵌套）
[MAIN, IF(outer)]                   # 退出内层if
[MAIN, IF(outer), ELSE(inner)]      # 进入内层else
[MAIN, IF(outer)]                   # 退出内层else
[MAIN]                              # 退出外层if
[MAIN, ELSE(outer)]                 # 进入外层else
[MAIN]                              # 退出外层else
```

### 4.2 FOR循环嵌套处理

#### 4.2.1 创建流程
```python
def _for_iter(self, end: int):
    # 1. 创建for节点
    for_node = ASTFor(iter_var, iter_expr, body, orelse)
    
    # 2. 处理嵌套位置
    if self.current_if_node and in_if_body:
        # if语句内的for：添加到if的body中
        self.current_if_node._body.append(for_node)
    elif self.current_for_node and in_for_body:
        # for循环内的for（嵌套循环）：添加到外层for的body中
        self.current_for_node._body.append(for_node)
    else:
        # 顶层for：发射到main_block
        self._emit(for_node)
    
    # 3. 创建for块并压栈
    for_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_FOR, end=end)
    self._push_block(for_block)
    
    # 4. 更新上下文
    self.current_for_node = for_node
    self._for_stack.append({
        'node': for_node,
        'body_end': end,
        'has_else': has_else
    })
```

#### 4.2.2 嵌套示例
```python
# Python代码
for i in range(10):
    for j in range(5):
        if i > j:
            print(i, j)

# blocks栈变化
[MAIN]
[MAIN, FOR(i)]                      # 外层for
[MAIN, FOR(i), FOR(j)]              # 内层for（嵌套）
[MAIN, FOR(i), FOR(j), IF]          # 内层if
[MAIN, FOR(i), FOR(j)]              # 退出if
[MAIN, FOR(i)]                      # 退出内层for
[MAIN]                              # 退出外层for
```

### 4.3 WHILE循环嵌套处理

#### 4.3.1 创建流程
```python
def _pop_jump_if_false(self, target: int):
    # 1. 检查是否是while循环模式
    if self._is_while_loop_pattern(current_offset):
        # 2. 创建while节点
        while_node = ASTWhile(condition, body, orelse)
        
        # 3. 处理嵌套位置（类似if/for）
        if self.current_if_node and in_if_body:
            self.current_if_node._body.append(while_node)
        elif self.current_for_node and in_for_body:
            self.current_for_node._body.append(while_node)
        else:
            self._emit(while_node)
        
        # 4. 创建while块并压栈
        while_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_WHILE, end=target)
        self._push_block(while_block)
        
        # 5. 更新上下文
        self.current_while_node = while_node
```

### 4.4 TRY-EXCEPT-FINALLY 嵌套处理

#### 4.4.1 创建流程
```python
def _setup_finally(self, target: int):
    # 1. 创建CONTAINER块（包裹try-except-finally）
    container = ASTContainerBlock(finally_pos=target)
    self._push_block(container)
    self.need_try = True  # 延迟创建TRY块

def _on_next_opcode(self):
    # 2. 延迟创建TRY块
    if self.need_try:
        try_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_TRY)
        self._push_block(try_block)
        self.stack_hist.append(self.stack.copy())  # 保存栈状态
        self.need_try = False
```

#### 4.4.2 嵌套示例
```python
# Python代码
try:
    for i in range(10):
        try:
            risky_op(i)
        except InnerError:
            handle_inner(i)
except OuterError:
    handle_outer()
finally:
    cleanup()

# blocks栈变化
[MAIN]
[MAIN, CONTAINER(outer)]            # 外层try容器
[MAIN, CONTAINER(outer), TRY]       # 外层try块
[MAIN, CONTAINER(outer), TRY, FOR]  # for循环
[MAIN, CONTAINER(outer), TRY, FOR, CONTAINER(inner)]  # 内层try容器
[MAIN, CONTAINER(outer), TRY, FOR, CONTAINER(inner), TRY]  # 内层try块
[MAIN, CONTAINER(outer), TRY, FOR, CONTAINER(inner), TRY, EXCEPT]  # 内层except
[MAIN, CONTAINER(outer), TRY, FOR]  # 退出内层try-except
[MAIN, CONTAINER(outer), TRY]       # 退出for
[MAIN, CONTAINER(outer), TRY, EXCEPT]  # 外层except
[MAIN, CONTAINER(outer)]            # 退出外层try/except
[MAIN, CONTAINER(outer), FINALLY]   # 外层finally
[MAIN]                              # 退出外层容器
```

---

## 5. 块弹出与状态恢复机制

### 5.1 POP_BLOCK处理流程

```python
def _handle_pop_block(self) -> None:
    """处理POP_BLOCK指令 - 弹出代码块"""
    
    # 1. 跳过特殊块类型
    if curblock.blk_type in [BLK_CONTAINER, BLK_FINALLY, BLK_WITH]:
        return  # 这些块由其他指令处理
    
    # 2. 恢复栈状态（对于特定块类型）
    if curblock.blk_type in [BLK_IF, BLK_ELIF, BLK_ELSE, BLK_TRY, BLK_EXCEPT, BLK_FINALLY]:
        if self.stack_hist:
            self.stack = self.stack_hist.pop()
    
    # 3. 弹出当前块
    tmp = curblock
    self.blocks.pop()
    self.current_block = self.blocks[-1]
    
    # 4. 添加到父块（跳过空ELSE块）
    if not (tmp.blk_type == BLK_ELSE and len(tmp.nodes) == 0):
        self.current_block.append(tmp)
    
    # 5. 特殊处理：循环ELSE块创建
    if tmp.blk_type in [BLK_FOR, BLK_WHILE] and tmp.end >= pos:
        else_block = ASTBlock(blk_type=BLK_ELSE, end=tmp.end)
        self._push_block(else_block)
        return
    
    # 6. 特殊处理：TRY块后的EXCEPT/FINALLY
    if self.current_block.blk_type == BLK_TRY:
        # 弹出TRY块，创建EXCEPT或FINALLY
        ...
    
    # 7. 特殊处理：CONTAINER块
    if self.current_block.blk_type == BLK_CONTAINER:
        # 根据情况弹出容器或创建FINALLY
        ...
```

### 5.2 else_pop机制（块结束检测）

```python
def _pop_blocks_to_current_pos(self, current_pos: int) -> None:
    """弹出所有结束位置 <= 当前位置的块"""
    
    prev_block = self.current_block
    while (prev_block.end < current_pos and 
           prev_block.blk_type != BLK_MAIN):
        
        # 恢复栈历史
        if prev_block.blk_type != BLK_CONTAINER:
            if self.stack_hist:
                self.stack_hist.pop()
        
        # 弹出块
        self.blocks.pop()
        self.current_block = self.blocks[-1]
        
        # 添加到父块
        self.current_block.append(prev_block)
        
        prev_block = self.current_block
```

---

## 6. 复杂嵌套场景分析

### 6.1 场景1：IF内嵌套FOR，FOR内嵌套TRY

```python
# Python代码
if condition:
    for i in range(10):
        try:
            process(i)
        except Error:
            handle(i)

# blocks栈变化时序
[MAIN]
[MAIN, IF]                          # 进入if
[MAIN, IF, FOR]                     # 进入for（嵌套在if内）
[MAIN, IF, FOR, CONTAINER]          # 进入try容器
[MAIN, IF, FOR, CONTAINER, TRY]     # 进入try块
[MAIN, IF, FOR, CONTAINER, TRY, EXCEPT]  # 进入except
[MAIN, IF, FOR]                     # 退出try-except
[MAIN, IF]                          # 退出for
[MAIN]                              # 退出if
```

### 6.2 场景2：嵌套TRY-EXCEPT with FINALLY

```python
# Python代码
try:
    try:
        inner_risky()
    except InnerError:
        handle_inner()
    finally:
        inner_cleanup()
    outer_risky()
except OuterError:
    handle_outer()
finally:
    outer_cleanup()

# blocks栈变化时序
[MAIN]
[MAIN, CONTAINER(outer)]
[MAIN, CONTAINER(outer), TRY]
[MAIN, CONTAINER(outer), TRY, CONTAINER(inner)]
[MAIN, CONTAINER(outer), TRY, CONTAINER(inner), TRY]
[MAIN, CONTAINER(outer), TRY, CONTAINER(inner), TRY, EXCEPT]
[MAIN, CONTAINER(outer), TRY, CONTAINER(inner)]
[MAIN, CONTAINER(outer), TRY, CONTAINER(inner), FINALLY]
[MAIN, CONTAINER(outer), TRY]       # 内层完成
[MAIN, CONTAINER(outer), TRY, EXCEPT]
[MAIN, CONTAINER(outer)]
[MAIN, CONTAINER(outer), FINALLY]
[MAIN]                              # 外层完成
```

### 6.3 场景3：WHILE-ELSE with BREAK

```python
# Python代码
while condition:
    if should_break:
        break
    do_work()
else:
    no_break_occurred()

# blocks栈变化时序（正常退出）
[MAIN]
[MAIN, WHILE]
[MAIN, WHILE, IF]                   # 进入if
[MAIN, WHILE]                       # 退出if
[MAIN, WHILE, ELSE]                 # while正常结束，创建else块
[MAIN]                              # 退出while-else

# blocks栈变化时序（break退出）
[MAIN]
[MAIN, WHILE]
[MAIN, WHILE, IF]                   # 进入if
# break触发：强制弹出到MAIN
[MAIN]                              # break_active强制弹出所有循环块
```

---

## 7. 关键算法规律总结

### 7.1 核心设计原则

| 原则 | 说明 |
|------|------|
| **双栈管理** | `blocks`管理块层级，`stack_hist`管理栈状态 |
| **延迟创建** | `need_try`等标志实现块的延迟创建 |
| **位置驱动** | `else_pop`根据`end <= pos`判断块结束 |
| **父子关系** | `blocks[-2]`是`blocks[-1]`的父块 |
| **上下文跟踪** | `current_*_node`跟踪当前控制流节点 |
| **状态隔离** | 每层控制流保存独立的栈快照 |

### 7.2 嵌套处理通用模式

```python
# 1. 创建控制流节点
control_node = ASTXXX(...)

# 2. 确定嵌套位置（决策树）
if self.current_if_node and in_if_body:
    # 添加到if的body
    self.current_if_node._body.append(control_node)
elif self.current_for_node and in_for_body:
    # 添加到for的body
    self.current_for_node._body.append(control_node)
elif self.current_while_node and in_while_body:
    # 添加到while的body
    self.current_while_node._body.append(control_node)
else:
    # 顶层：发射到main_block
    self._emit(control_node)

# 3. 创建块并压栈（如果需要）
block = ASTBlock(blk_type=BLK_XXX, end=end_pos)
self._push_block(block)

# 4. 保存栈状态（对于try等需要恢复栈的）
self.stack_hist.append(self.stack.copy())

# 5. 更新上下文
self.current_xxx_node = control_node
```

### 7.3 块退出通用模式

```python
# 1. 恢复栈状态（如果需要）
if self.stack_hist:
    self.stack = self.stack_hist.pop()

# 2. 弹出当前块
popped_block = self.blocks.pop()
self.current_block = self.blocks[-1]

# 3. 添加到父块
self.current_block.append(popped_block)

# 4. 创建后续块（ELSE/FINALLY/EXCEPT等）
next_block = ASTBlock(blk_type=BLK_YYY, end=end_pos)
self._push_block(next_block)

# 5. 更新上下文
if should_clear_context:
    self.current_xxx_node = None
```

---

## 8. 调试技巧

### 8.1 开启调试输出
```python
DEBUG_OUTPUT = True
DEBUG_FILTER_STRINGS = [
    "POP_BLOCK",
    "JUMP_FORWARD",
    "IF",
    "FOR",
    "WHILE",
    "TRY",
    "CONTAINER"
]
```

### 8.2 关键调试点
- 块创建：`[_push_block]`
- 块弹出：`[_handle_pop_block]`, `[_pop_blocks_to_current_pos]`
- IF处理：`[_pop_jump_forward_if_false]`
- FOR处理：`[_for_iter]`
- WHILE处理：`[_pop_jump_if_false]`, `[_pop_jump_backward_if_false]`
- TRY处理：`[_setup_finally]`, `[_setup_except]`

### 8.3 栈状态检查
```python
# 打印当前blocks栈
print(f"blocks栈: {[b.blk_type.name for b in self.blocks]}")

# 打印当前stack_hist深度
print(f"stack_hist深度: {len(self.stack_hist)}")

# 打印当前上下文
print(f"current_if_node: {self.current_if_node}")
print(f"current_for_node: {self.current_for_node}")
print(f"current_while_node: {self.current_while_node}")
```

---

## 9. 总结

pycdc-python的控制流嵌套处理采用**双栈管理架构**：

1. **blocks栈**负责管理块的层级关系，确保正确的父子关系
2. **stack_hist栈**负责保存和恢复栈状态，确保变量可见性
3. **上下文跟踪变量**（`current_*_node`）负责确定节点应该添加到哪个父节点
4. **延迟创建机制**（`need_try`等标志）确保块在正确的时机创建

这种设计可以正确处理任意深度的控制流嵌套，包括：
- IF/ELIF/ELSE链的嵌套
- FOR/WHILE循环的嵌套
- TRY-EXCEPT-FINALLY的嵌套
- 上述所有结构的任意组合嵌套
