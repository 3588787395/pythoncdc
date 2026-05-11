# PyCDC-Python 控制流算法完整分析文档

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
class ASTBuilder:
    def __init__(self):
        self.blocks: List[ASTBlock] = []           # 块栈
        self.main_block = ASTBlock(BlockType.BLK_MAIN)  # 主块
        self.blocks.append(self.main_block)
        self.current_block = self.main_block       # 当前块
        
        self.stack_hist: List[FastStack] = []      # 栈状态历史
        self.else_pop = False                      # else分支结束标志
        self.need_try = False                      # 需要创建try块标志
```

### 2.2 控制流上下文跟踪
```python
# 循环上下文
self.current_for_node = None       # 当前for循环节点
self.current_while_node = None     # 当前while循环节点
self._for_stack = []               # for循环栈
self._loop_structures = []         # 循环结构列表

# 条件上下文
self.current_if_node = None        # 当前if节点
self._if_stack = []                # if语句栈
self._if_chain_root = None         # if-elif-else链根节点
self._elif_nodes = {}              # elif节点映射

# Try-Except上下文
self.current_try_node = None       # 当前try节点
self._exception_blocks = []        # 异常处理块列表
```

---

## 3. 控制流处理核心机制

### 3.1 块栈操作

#### 压入块
```python
def _push_block(self, block: ASTBlock) -> None:
    """将块压入块栈"""
    self.blocks.append(block)
    self.current_block = block
```

#### 弹出块到当前位置
```python
def _pop_blocks_to_current_pos(self, current_pos: int) -> None:
    """
    弹出块栈直到当前位置
    当块的end < current_pos且不是主块时，弹出块并添加到父块
    """
    while (prev_block.end < current_pos and 
           prev_block.blk_type != BlockType.BLK_MAIN):
        
        # 恢复栈状态
        if prev_block.blk_type != BlockType.BLK_CONTAINER:
            if self.stack_hist:
                self.stack_hist.pop()
        
        # 弹出块并添加到父块
        self.blocks.pop()
        self.current_block = self.blocks[-1]
        self.current_block.append(prev_block)
```

### 3.2 POP_BLOCK指令处理

```python
def _handle_pop_block(self) -> None:
    """
    处理POP_BLOCK指令 - 参考C++ ASTree.cpp第1592-1688行
    
    处理逻辑：
    1. 跳过CONTAINER/FINALLY/WITH块（由专用指令处理）
    2. 移除块末尾的KEYWORD节点
    3. 恢复IF/ELIF/ELSE/TRY/EXCEPT/FINALLY块的栈状态
    4. 弹出当前块并追加到父块
    5. FOR/WHILE循环：创建else块（如果有）
    6. TRY块：特殊处理，可能需要创建EXCEPT/FINALLY块
    7. CONTAINER块：根据情况弹出或创建FINALLY块
    """
```

---

## 4. 各控制流结构处理

### 4.1 If-Elif-Else 处理

#### 识别模式
```python
# if语句特征：
# 1. POP_JUMP_FORWARD_IF_FALSE / POP_JUMP_IF_FALSE 指令
# 2. 跳转目标之后是if体代码
# 3. if体结束处有JUMP_FORWARD（跳转到else之后）

# elif语句特征：
# 1. 当前已有if节点