# PythonCDC 控制流图(CFG)实施完整规划

## 1. 现状分析

### 1.1 现有控制流分析的问题

当前代码已有 `ControlFlowAnalyzer` 类，但存在以下问题：

```python
# 问题1：检测逻辑过于简单
# 循环检测只是检查向后跳转
if jump_target < offset:
    # 认为是循环，但没有支配节点验证

# 问题2：缺少支配树计算
# 没有实现dominator算法，无法准确识别控制流层次

# 问题3：状态管理混乱
# 大量状态变量：current_if_node, current_for_node, _if_stack等

# 问题4：模式匹配不系统
# 每个控制流类型都有独立的检测函数，没有统一框架
```

### 1.2 现有双栈机制

```python
# blocks栈：管理块层级
self.blocks: List[ASTBlock] = []

# stack_hist：管理栈状态
self.stack_hist: List[FastStack] = []

# 大量状态变量
self.current_if_node = None
self.current_for_node = None
self.current_while_node = None
self._if_stack = []
self._for_stack = []
```

---

## 2. 实施目标

### 2.1 核心目标

1. **用状态变量禁用原有双栈机制**
2. **实施完整的控制流图(CFG)方法**
3. **实现支配树计算和结构化分解**
4. **保持向后兼容性**

### 2.2 预期效果

```
原有代码：18000+ 行，大量"关键修复"
改进后：5000-8000 行，系统化算法

原有：手动管理块层级和状态
改进后：自动分析控制流结构

原有：难以处理复杂嵌套
改进后：递归分解天然支持任意嵌套
```

---

## 3. 状态变量禁用机制设计

### 3.1 禁用开关

```python
# core/config.py
class Config:
    """全局配置"""
    
    # 控制流算法选择
    USE_CFG_ALGORITHM = True  # True: 使用CFG算法, False: 使用原有双栈算法
    
    # 调试配置
    DEBUG_CFG = False
    DEBUG_DOMINATORS = False
    DEBUG_STRUCTURED = False
```

### 3.2 ASTBuilder改造

```python
# parsers/ast_builder.py

class ASTBuilder:
    def __init__(self, use_cfg=True):
        self.use_cfg = use_cfg
        
        if self.use_cfg:
            # 使用新的CFG算法
            self.cfg_builder = CFGBuiler()
            self.dominator_analyzer = DominatorAnalyzer()
            self.structured_analyzer = StructuredAnalyzer()
            self.ast_generator = ASTGenerator()
            
            # 禁用原有双栈机制
            self._disable_legacy_stacks()
        else:
            # 使用原有双栈算法
            self._init_legacy_stacks()
    
    def _disable_legacy_stacks(self):
        """禁用原有双栈机制"""
        # 不初始化blocks和stack_hist
        # 使用CFG替代
        self.blocks = None
        self.stack_hist = None
        self.current_if_node = None
        self.current_for_node = None
        self.current_while_node = None
        self._if_stack = None
        self._for_stack = None
    
    def _init_legacy_stacks(self):
        """初始化原有双栈机制"""
        from utils.stack import FastStack
        self.blocks = [self.main_block]
        self.stack_hist = []
        self.current_if_node = None
        self.current_for_node = None
        self.current_while_node = None
        self._if_stack = []
        self._for_stack = []
```

### 3.3 双栈方法禁用标记

```python
# 在原有方法中添加禁用检查

def _push_block(self, block):
    """压入块（原有方法）"""
    if self.use_cfg:
        # CFG算法不使用此方法
        return
    # 原有逻辑...

def _pop_block(self):
    """弹出块（原有方法）"""
    if self.use_cfg:
        # CFG算法不使用此方法
        return
    # 原有逻辑...

def _setup_finally(self, target):
    """设置finally块（原有方法）"""
    if self.use_cfg:
        # CFG算法不使用此方法
        return
    # 原有逻辑...
```

---

## 4. 控制流图(CFG)架构设计

### 4.1 模块结构

```
core/
├── __init__.py
├── cfg/                          # 新增CFG模块
│   ├── __init__.py
│   ├── basic_block.py            # 基本块定义
│   ├── cfg_builder.py            # CFG构建器
│   ├── dominator_analyzer.py     # 支配树分析器
│   ├── structured_analyzer.py    # 结构化分析器
│   ├── pattern_matcher.py        # 模式匹配器
│   └── ast_generator.py          # AST生成器
├── control_flow.py               # 保留原有（向后兼容）
└── ast_nodes.py                  # AST节点定义

parsers/
├── __init__.py
├── ast_builder.py                # 改造后的主入口
└── ...
```

### 4.2 核心类设计

```python
# core/cfg/basic_block.py

class BasicBlock:
    """基本块"""
    
    def __init__(self, start_offset: int, end_offset: int = None):
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.instructions: List[Dict] = []
        
        # 控制流边
        self.successors: List[BasicBlock] = []    # 后继块
        self.predecessors: List[BasicBlock] = []  # 前驱块
        
        # 支配树
        self.dominators: Set[BasicBlock] = set()  # 支配集
        self.immediate_dominator: BasicBlock = None  # 直接支配者
        self.dominated_blocks: Set[BasicBlock] = set()  # 被支配块
        
        # 循环信息
        self.is_loop_header = False
        self.loop_depth = 0
        
        # 异常处理
        self.is_exception_handler = False
        self.exception_range = None
    
    def add_successor(self, block: 'BasicBlock'):
        """添加后继块"""
        if block not in self.successors:
            self.successors.append(block)
            block.predecessors.append(self)
    
    def __repr__(self):
        return f"BB({self.start_offset}-{self.end_offset})"


# core/cfg/cfg_builder.py

class CFGBuiler:
    """控制流图构建器"""
    
    def __init__(self):
        self.blocks: Dict[int, BasicBlock] = {}  # 偏移 -> 基本块
        self.entry_block: BasicBlock = None
        self.exit_block: BasicBlock = None
        self.instructions: List[Dict] = []
    
    def build(self, instructions: List[Dict]) -> 'CFGBuiler':
        """从指令列表构建CFG"""
        self.instructions = instructions
        
        # 1. 识别基本块边界
        self._identify_block_boundaries()
        
        # 2. 创建基本块
        self._create_basic_blocks()
        
        # 3. 连接基本块
        self._connect_blocks()
        
        # 4. 设置入口和出口
        self._set_entry_exit()
        
        return self
    
    def _identify_block_boundaries(self):
        """识别基本块边界"""
        # 基本块开始位置：
        # 1. 第一条指令
        # 2. 跳转目标
        # 3. 跳转指令后的指令
        
        leaders = {0}  # 第一条指令是leader
        
        for i, instr in enumerate(self.instructions):
            offset = instr['offset']
            opcode = instr['opcode']
            
            # 跳转指令的目标
            if self._is_jump_instruction(opcode):
                target = self._get_jump_target(instr)
                if target is not None:
                    leaders.add(target)
                
                # 跳转指令后的指令也是leader
                if i + 1 < len(self.instructions):
                    leaders.add(self.instructions[i + 1]['offset'])
        
        self.leaders = sorted(leaders)
    
    def _create_basic_blocks(self):
        """创建基本块"""
        for i, leader_offset in enumerate(self.leaders):
            block = BasicBlock(leader_offset)
            
            # 收集该基本块的指令
            start_idx = self._find_instruction_index(leader_offset)
            if start_idx is None:
                continue
            
            # 找到该块的结束位置
            end_offset = self.leaders[i + 1] if i + 1 < len(self.leaders) else float('inf')
            
            for j in range(start_idx, len(self.instructions)):
                instr = self.instructions[j]
                if instr['offset'] >= end_offset:
                    break
                block.instructions.append(instr)
                block.end_offset = instr['offset']
            
            self.blocks[leader_offset] = block
    
    def _connect_blocks(self):
        """连接基本块"""
        for block in self.blocks.values():
            if not block.instructions:
                continue
            
            last_instr = block.instructions[-1]
            opcode = last_instr['opcode']
            
            # 处理跳转指令
            if self._is_jump_instruction(opcode):
                target = self._get_jump_target(last_instr)
                if target is not None and target in self.blocks:
                    block.add_successor(self.blocks[target])
                
                # 条件跳转还有fall-through边
                if self._is_conditional_jump(opcode):
                    next_offset = last_instr['offset'] + self._get_instruction_size(last_instr)
                    if next_offset in self.blocks:
                        block.add_successor(self.blocks[next_offset])
            
            # 非跳转指令：顺序执行
            elif not self._is_return_instruction(opcode):
                next_offset = last_instr['offset'] + self._get_instruction_size(last_instr)
                if next_offset in self.blocks:
                    block.add_successor(self.blocks[next_offset])
    
    def _is_jump_instruction(self, opcode: int) -> bool:
        """检查是否是跳转指令"""
        jump_opcodes = {
            Opcode.JUMP_FORWARD, Opcode.JUMP_BACKWARD, Opcode.JUMP_ABSOLUTE,
            Opcode.POP_JUMP_IF_FALSE, Opcode.POP_JUMP_IF_TRUE,
            Opcode.JUMP_IF_FALSE_OR_POP, Opcode.JUMP_IF_TRUE_OR_POP,
            # Python 3.11+
            Opcode.POP_JUMP_FORWARD_IF_FALSE, Opcode.POP_JUMP_FORWARD_IF_TRUE,
            Opcode.POP_JUMP_BACKWARD_IF_FALSE, Opcode.POP_JUMP_BACKWARD_IF_TRUE,
        }
        return opcode in jump_opcodes
    
    def _is_conditional_jump(self, opcode: int) -> bool:
        """检查是否是条件跳转"""
        conditional_opcodes = {
            Opcode.POP_JUMP_IF_FALSE, Opcode.POP_JUMP_IF_TRUE,
            Opcode.JUMP_IF_FALSE_OR_POP, Opcode.JUMP_IF_TRUE_OR_POP,
            Opcode.POP_JUMP_FORWARD_IF_FALSE, Opcode.POP_JUMP_FORWARD_IF_TRUE,
            Opcode.POP_JUMP_BACKWARD_IF_FALSE, Opcode.POP_JUMP_BACKWARD_IF_TRUE,
        }
        return opcode in conditional_opcodes
    
    def _get_jump_target(self, instr: Dict) -> Optional[int]:
        """获取跳转目标"""
        opcode = instr['opcode']
        operand = instr.get('operand', 0)
        offset = instr['offset']
        
        if opcode in [Opcode.JUMP_FORWARD, Opcode.POP_JUMP_IF_FALSE, Opcode.POP_JUMP_IF_TRUE]:
            return offset + operand + 2
        elif opcode == Opcode.JUMP_BACKWARD:
            return offset - operand - 2
        elif opcode == Opcode.JUMP_ABSOLUTE:
            return operand
        
        return None


# core/cfg/dominator_analyzer.py

class DominatorAnalyzer:
    """支配树分析器"""
    
    def __init__(self, cfg: CFGBuiler):
        self.cfg = cfg
    
    def analyze(self):
        """计算支配树"""
        # 1. 计算支配集
        self._compute_dominators()
        
        # 2. 计算直接支配者
        self._compute_immediate_dominators()
        
        # 3. 构建支配树
        self._build_dominator_tree()
    
    def _compute_dominators(self):
        """计算每个基本块的支配集"""
        all_blocks = set(self.cfg.blocks.values())
        
        # 初始化
        for block in self.cfg.blocks.values():
            if block == self.cfg.entry_block:
                block.dominators = {block}
            else:
                block.dominators = all_blocks.copy()
        
        # 迭代计算
        changed = True
        while changed:
            changed = False
            for block in self.cfg.blocks.values():
                if block == self.cfg.entry_block:
                    continue
                
                # 交集：所有前驱的支配集的交集
                new_doms = all_blocks.copy()
                for pred in block.predecessors:
                    new_doms &= pred.dominators
                new_doms.add(block)
                
                if new_doms != block.dominators:
                    block.dominators = new_doms
                    changed = True
    
    def _compute_immediate_dominators(self):
        """计算直接支配者"""
        for block in self.cfg.blocks.values():
            if block == self.cfg.entry_block:
                continue
            
            # 直接支配者是支配集中最接近的节点
            for dom in block.dominators:
                if dom == block:
                    continue
                
                # 检查是否是直接支配者
                is_immediate = True
                for other_dom in block.dominators:
                    if other_dom != block and other_dom != dom:
                        if dom in other_dom.dominators:
                            is_immediate = False
                            break
                
                if is_immediate:
                    block.immediate_dominator = dom
                    dom.dominated_blocks.add(block)
                    break
    
    def _build_dominator_tree(self):
        """构建支配树（用于调试）"""
        self.dominator_tree = {}
        for block in self.cfg.blocks.values():
            if block.immediate_dominator:
                parent = block.immediate_dominator
                if parent not in self.dominator_tree:
                    self.dominator_tree[parent] = []
                self.dominator_tree[parent].append(block)


# core/cfg/structured_analyzer.py

class StructuredAnalyzer:
    """结构化分析器"""
    
    def __init__(self, cfg: CFGBuiler, dominator: DominatorAnalyzer):
        self.cfg = cfg
        self.dominator = dominator
        self.structured_nodes: List[StructuredNode] = []
    
    def analyze(self) -> List[StructuredNode]:
        """分析结构化控制流"""
        # 1. 识别循环（基于回边）
        loops = self._identify_loops()
        
        # 2. 识别条件分支
        branches = self._identify_branches()
        
        # 3. 识别异常处理
        exceptions = self._identify_exceptions()
        
        # 4. 递归分解
        self.structured_nodes = self._decompose_region(
            self.cfg.entry_block, loops, branches, exceptions
        )
        
        return self.structured_nodes
    
    def _identify_loops(self) -> List[Loop]:
        """识别循环（基于回边）"""
        loops = []
        
        for block in self.cfg.blocks.values():
            for succ in block.successors:
                # 回边：succ支配block
                if succ in block.dominators:
                    loop = Loop(header=succ, back_edge=block)
                    loop.body = self._compute_loop_body(succ, block)
                    loops.append(loop)
                    
                    # 标记循环头
                    succ.is_loop_header = True
                    for b in loop.body:
                        b.loop_depth += 1
        
        return loops
    
    def _compute_loop_body(self, header: BasicBlock, back_edge_node: BasicBlock) -> Set[BasicBlock]:
        """计算循环体"""
        body = {header, back_edge_node}
        
        # 从回边起点反向遍历
        worklist = [back_edge_node]
        while worklist:
            block = worklist.pop()
            for pred in block.predecessors:
                if pred not in body and pred != header:
                    body.add(pred)
                    worklist.append(pred)
        
        return body
    
    def _identify_branches(self) -> List[Branch]:
        """识别条件分支"""
        branches = []
        
        for block in self.cfg.blocks.values():
            if len(block.successors) == 2:
                # 条件分支
                branch = Branch(
                    condition_block=block,
                    true_branch=block.successors[0],
                    false_branch=block.successors[1]
                )
                branches.append(branch)
        
        return branches
    
    def _identify_exceptions(self) -> List[ExceptionHandler]:
        """识别异常处理"""
        handlers = []
        
        for block in self.cfg.blocks.values():
            if block.is_exception_handler:
                handler = ExceptionHandler(
                    handler_block=block,
                    protected_range=block.exception_range
                )
                handlers.append(handler)
        
        return handlers
    
    def _decompose_region(self, entry: BasicBlock, loops, branches, exceptions) -> List[StructuredNode]:
        """递归分解区域"""
        nodes = []
        current = entry
        
        while current:
            # 检查是否是循环头
            for loop in loops:
                if loop.header == current:
                    node = self._decompose_loop(loop)
                    nodes.append(node)
                    current = self._get_exit_block(loop)
                    break
            else:
                # 检查是否是条件分支
                for branch in branches:
                    if branch.condition_block == current:
                        node = self._decompose_if(branch)
                        nodes.append(node)
                        current = self._get_merge_block(branch)
                        break
                else:
                    # 顺序执行
                    node = self._create_sequence_node(current)
                    nodes.append(node)
                    current = current.successors[0] if current.successors else None
        
        return nodes
    
    def _decompose_loop(self, loop: Loop) -> StructuredNode:
        """分解循环"""
        # 识别循环类型（while/for）
        loop_type = self._identify_loop_type(loop)
        
        # 分解循环体
        body_nodes = self._decompose_region(
            list(loop.body)[0], [], [], []
        )
        
        return StructuredNode(
            type=loop_type,
            header=loop.header,
            body=body_nodes
        )
    
    def _decompose_if(self, branch: Branch) -> StructuredNode:
        """分解条件分支"""
        # 分解then分支
        then_nodes = self._decompose_region(branch.true_branch, [], [], [])
        
        # 分解else分支（如果有）
        else_nodes = []
        if branch.false_branch:
            else_nodes = self._decompose_region(branch.false_branch, [], [], [])
        
        return StructuredNode(
            type='if',
            condition=branch.condition_block,
            then_branch=then_nodes,
            else_branch=else_nodes
        )


# core/cfg/ast_generator.py

class ASTGenerator:
    """AST生成器"""
    
    def generate(self, structured_nodes: List[StructuredNode]) -> ASTNode:
        """从结构化节点生成AST"""
        if not structured_nodes:
            return ASTNodeList([])
        
        if len(structured_nodes) == 1:
            return self._generate_node(structured_nodes[0])
        
        # 多个节点：创建节点列表
        return ASTNodeList([self._generate_node(n) for n in structured_nodes])
    
    def _generate_node(self, node: StructuredNode) -> ASTNode:
        """生成单个节点"""
        if node.type == 'sequence':
            return self._generate_sequence(node)
        elif node.type == 'if':
            return self._generate_if(node)
        elif node.type == 'while':
            return self._generate_while(node)
        elif node.type == 'for':
            return self._generate_for(node)
        elif node.type == 'try':
            return self._generate_try(node)
        else:
            return self._generate_expression(node)
    
    def _generate_if(self, node: StructuredNode) -> ASTIf:
        """生成if语句"""
        condition = self._extract_condition(node.condition)
        then_body = self.generate(node.then_branch)
        else_body = self.generate(node.else_branch) if node.else_branch else None
        
        return ASTIf(condition, then_body, else_body)
    
    def _generate_while(self, node: StructuredNode) -> ASTWhile:
        """生成while语句"""
        condition = self._extract_condition(node.header)
        body = self.generate(node.body)
        
        return ASTWhile(condition, body, None)
    
    def _generate_for(self, node: StructuredNode) -> ASTFor:
        """生成for语句"""
        iter_var = self._extract_iter_var(node.header)
        iter_expr = self._extract_iter_expr(node.header)
        body = self.generate(node.body)
        
        return ASTFor(iter_var, iter_expr, body, None)
```

---

## 5. 实施步骤

### 阶段1：基础架构（第1-2周）

#### 任务1.1：创建CFG模块
```
- 创建 core/cfg/ 目录
- 实现 basic_block.py
- 实现 cfg_builder.py
```

#### 任务1.2：实现支配树算法
```
- 实现 dominator_analyzer.py
- 编写单元测试
- 验证支配树计算正确性
```

#### 任务1.3：状态变量禁用机制
```
- 添加 Config 类
- 改造 ASTBuilder.__init__
- 添加 _disable_legacy_stacks 方法
```

**验收标准：**
- CFG构建正确
- 支配树计算正确
- 状态变量禁用开关工作正常

### 阶段2：结构化分析（第3-4周）

#### 任务2.1：实现循环识别
```
- 实现回边分析
- 实现循环体计算
- 区分while/for循环
```

#### 任务2.2：实现条件分支识别
```
- 识别if-then-else结构
- 识别if-elif-else链
- 处理短路逻辑
```

#### 任务2.3：实现异常处理识别
```
- 识别try-except
- 识别try-finally
- 识别try-except-finally
```

**验收标准：**
- 能正确识别各种控制流结构
- 单元测试通过

### 阶段3：AST生成（第5-6周）

#### 任务3.1：实现AST生成器
```
- 实现 ast_generator.py
- 实现各控制流结构的AST生成
- 处理表达式和语句
```

#### 任务3.2：集成到ASTBuilder
```
- 修改 ASTBuilder.build 方法
- 添加CFG算法分支
- 保持向后兼容
```

#### 任务3.3：测试和调试
```
- 编写综合测试用例
- 对比新旧算法输出
- 修复问题
```

**验收标准：**
- AST生成正确
- 与原有算法输出一致
- 所有测试通过

### 阶段4：优化和文档（第7-8周）

#### 任务4.1：性能优化
```
- 优化支配树算法
- 优化结构化分解
- 添加缓存机制
```

#### 任务4.2：完善文档
```
- 编写API文档
- 编写使用指南
- 编写架构说明
```

#### 任务4.3：清理和发布
```
- 删除临时文件
- 整理代码结构
- 准备发布
```

**验收标准：**
- 性能优于原有算法
- 文档完整
- 代码整洁

---

## 6. 防止半途而废的策略

### 6.1 阶段性里程碑

```
每2周一个里程碑，必须完成才能继续：

里程碑1（第2周末）：CFG构建 + 支配树
├── 必须有可运行的demo
├── 必须通过单元测试
└── 必须提交代码审查

里程碑2（第4周末）：结构化分析
├── 必须能识别所有控制流类型
├── 必须有可视化工具（CFG图）
└── 必须通过集成测试

里程碑3（第6周末）：AST生成
├── 必须能生成正确的AST
├── 必须与原有算法输出一致
└── 必须通过回归测试

里程碑4（第8周末）：完成
├── 性能测试通过
├── 文档完整
└── 代码审查通过
```

### 6.2 每日检查清单

```python
# daily_checklist.py

DAILY_TASKS = {
    "代码": [
        "编写/修改代码",
        "运行单元测试",
        "提交到版本控制"
    ],
    "文档": [
        "更新设计文档",
        "记录遇到的问题",
        "更新进度表"
    ],
    "测试": [
        "测试新功能",
        "对比新旧算法",
        "记录测试结果"
    ]
}
```

### 6.3 风险管理

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| 支配树算法复杂 | 中 | 高 | 先实现简单版本，再优化 |
| 循环识别不准确 | 中 | 高 | 增加测试用例，逐步完善 |
| 与原有代码集成困难 | 低 | 中 | 保持向后兼容，逐步替换 |
| 性能不如原有算法 | 低 | 中 | 添加缓存，优化算法 |
| 时间超出预期 | 中 | 中 | 分阶段交付，优先核心功能 |

### 6.4 代码审查机制

```
每周五进行代码审查：

审查内容：
1. 代码是否符合设计
2. 是否有单元测试
3. 是否有文档
4. 是否有性能问题

审查人：自己（先自查）+ AI助手
```

### 6.5 备份和回滚策略

```python
# 每个阶段结束时创建备份

BACKUP_POINTS = [
    "stage1_cfg_complete",      # 阶段1完成
    "stage2_structured_complete", # 阶段2完成
    "stage3_ast_complete",      # 阶段3完成
    "stage4_final",             # 最终版本
]

# 如果出现问题，可以回滚到最近的备份点
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# tests/test_cfg.py

class TestCFGBuiler(unittest.TestCase):
    def test_simple_if(self):
        """测试简单if语句的CFG构建"""
        code = """
if x > 0:
    print("positive")
"""
        cfg = build_cfg(code)
        self.assertEqual(len(cfg.blocks), 3)  # entry, if-body, exit
    
    def test_while_loop(self):
        """测试while循环的CFG构建"""
        code = """
while x < 10:
    x += 1
"""
        cfg = build_cfg(code)
        self.assertEqual(len(cfg.blocks), 3)  # entry, loop-body, exit

class TestDominatorAnalyzer(unittest.TestCase):
    def test_dominator_tree(self):
        """测试支配树计算"""
        code = """
if x:
    a = 1
else:
    a = 2
print(a)
"""
        cfg = build_cfg(code)
        analyzer = DominatorAnalyzer(cfg)
        analyzer.analyze()
        
        # 验证支配关系
        entry = cfg.entry_block
        for block in cfg.blocks.values():
            self.assertIn(entry, block.dominators)
```

### 7.2 集成测试

```python
# tests/test_integration.py

class TestControlFlowReconstruction(unittest.TestCase):
    def test_nested_if(self):
        """测试嵌套if"""
        code = """
if x:
    if y:
        print("both")
    else:
        print("only x")
else:
    print("neither")
"""
        ast = decompile(code, use_cfg=True)
        # 验证AST结构
    
    def test_complex_nested(self):
        """测试复杂嵌套"""
        code = """
for i in range(10):
    if i > 5:
        while x < i:
            try:
                risky()
            except Error:
                handle()
"""
        ast = decompile(code, use_cfg=True)
        # 验证AST结构
```

### 7.3 回归测试

```python
# tests/test_regression.py

class TestRegression(unittest.TestCase):
    """回归测试：确保新算法与旧算法输出一致"""
    
    def test_all_control_flow_types(self):
        """测试所有控制流类型"""
        test_cases = load_test_cases()
        
        for case in test_cases:
            old_ast = decompile(case.code, use_cfg=False)
            new_ast = decompile(case.code, use_cfg=True)
            
            self.assertEqual(
                ast_to_string(old_ast),
                ast_to_string(new_ast),
                f"Mismatch in {case.name}"
            )
```

---

## 8. 文档清单

### 8.1 必须完成的文档

- [ ] 架构设计文档（本文档）
- [ ] API文档（每个模块的接口说明）
- [ ] 使用指南（如何使用新算法）
- [ ] 测试报告（测试结果和覆盖率）
- [ ] 迁移指南（从旧算法迁移到新算法）

### 8.2 代码注释要求

```python
# 每个公共方法必须有文档字符串
def analyze(self) -> List[StructuredNode]:
    """
    分析结构化控制流
    
    Returns:
        结构化节点列表，表示控制流的层次结构
        
    Example:
        >>> analyzer = StructuredAnalyzer(cfg, dominator)
        >>> nodes = analyzer.analyze()
        >>> print(nodes[0].type)
        'if'
    """
    pass
```

---

## 9. 总结

### 9.1 关键决策

1. **使用状态变量禁用原有双栈机制** - 保持向后兼容
2. **实施完整的CFG方法** - 系统化解决控制流问题
3. **分8周4个阶段实施** - 确保每个阶段都有明确目标
4. **建立防止半途而废的机制** - 里程碑、检查清单、风险管理

### 9.2 成功标准

- [ ] 代码行数从18000+减少到8000-
- [ ] 消除所有"关键修复"标记
- [ ] 支持任意复杂的控制流嵌套
- [ ] 性能优于原有算法
- [ ] 通过所有回归测试

### 9.3 下一步行动

1. **立即开始**：创建core/cfg/目录和基础文件
2. **本周完成**：CFG构建和支配树计算
3. **提交审查**：每周五提交代码审查

---

**文档创建时间：** 2026-03-15
**计划完成时间：** 2026-05-10（8周后）
**负责人：** AI助手 + 用户
