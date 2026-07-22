"""CPython peephole 优化器模式库（Phase 2.5.1 基础设施）。

识别 CPython 3.11+ peephole 优化器产生的"反归约"字节码模式，将优化后的
字节码模式映射回源码结构。模式匹配是纯结构性的——基于字节码指令序列
模板与不变量断言，不依赖跨区域跨层次的启发式规则。

匹配结果用作区域识别的预处理输入，不改变区域归约算法本身（识别阶段一次
正确，无后处理补丁）。模式库不引入硬编码上限，对嵌套结构保持天然支持。

Phase 2.5.1: 基础设施 + P1 模式（双 RETURN_VALUE 三元）
Phase 2.5.2: 实施 P1（修复 _block_is_return_body 误判 + _generate_ternary
             虚拟 merge 处理）
Phase 2.5.4: P3 模式枚举（while-true + break：NOP 头 + JUMP_BACKWARD 回边）
Phase 2.5.5: P4 模式枚举（chained compare：SWAP/COPY/COMPARE_OP 降级）
Phase 2.5.6: P5+ 模式枚举（BoolOp 短路独立 exit / not X 跳转反转 /
             while 条件 back-edge 重查 / 隐式 return None）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set


# 复用 region_analyzer 的常量定义（避免循环导入，本地副本）
NOISE_OPS = frozenset({'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'})

RETURN_OPS = frozenset({'RETURN_VALUE', 'RETURN_CONST'})

FORWARD_CONDITIONAL_JUMP_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
})

BACKWARD_CONDITIONAL_JUMP_OPS = frozenset({
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
})

BACKWARD_JUMP_OPS = frozenset({
    'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
}) | BACKWARD_CONDITIONAL_JUMP_OPS

# 链式比较相关指令
COMPARE_OPS = frozenset({'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'})

# 单 LOAD 值表达式允许的操作码
LOAD_VALUE_OPS = frozenset({
    'LOAD_NAME', 'LOAD_CONST', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
    'LOAD_CLOSURE', 'LOAD_CLASSDEREF',
})

# 副作用指令（出现则不是单值表达式块）
SIDE_EFFECT_OPS = frozenset({
    'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF',
    'STORE_ATTR', 'STORE_SUBSCR',
    'DELETE_NAME', 'DELETE_FAST', 'DELETE_GLOBAL', 'DELETE_ATTR',
    'RAISE_VARARGS', 'YIELD_VALUE', 'YIELD_FROM',
    'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
    'GLOBAL', 'NONLOCAL',
})


@dataclass
class PeepholePattern:
    """单个 peephole 优化模式的签名与反优化策略。

    字段:
        name: 模式名（唯一标识符）
        bytecode_signature: 模式签名（字节码指令序列模板，描述性文本）
        source_ast_type: 反优化后对应的源码 AST 节点类型
        anti_reduction_strategy: 反优化策略（描述如何在归约阶段处理该模式）
        invariants: 不变量断言列表（模式匹配成立必须满足的性质）
    """
    name: str
    bytecode_signature: str
    source_ast_type: str
    anti_reduction_strategy: str
    invariants: List[str] = field(default_factory=list)


class PeepholePatternLibrary:
    """CPython peephole 优化模式库主体。

    1. 算法描述
    -----------
    CPython 3.11+ 的 peephole 优化器会折叠某些源码结构为非归约友好的字节码
    模式。本模式库作为"反向查找表"，在区域识别阶段预处理时扫描所有模式，
    将优化后的字节码模式映射回源码结构（如三元表达式、隐式 return 等）。

    匹配流程：
      (a) 遍历 CFG 所有基本块；
      (b) 对每个块尝试所有已注册的模式匹配器；
      (c) 收集所有匹配结果，供区域识别阶段预处理使用。

    匹配是纯结构性的——基于指令序列模板与不变量断言，不依赖跨区域跨层次
    的启发式规则。匹配结果用作区域识别的预处理输入（如释放被误识别的块），
    不改变区域归约算法本身。模式库不引入硬编码上限，对嵌套结构保持天然
    支持（每个 cond_block 独立匹配，嵌套三元各自独立识别）。

    2. 字节码模式
    -----------
    P1: 模块级三元表达式语句 → 双 RETURN_VALUE
        用例: `a if cond else b`（模块级/函数体内的裸表达式语句，值被丢弃）
        字节码（CPython 3.11+ 实测）:
            LOAD cond; POP_JUMP_FORWARD_IF_FALSE → false;
            true:  LOAD a; POP_TOP; LOAD_CONST None; RETURN_VALUE
            false: LOAD b; POP_TOP; LOAD_CONST None; RETURN_VALUE
        特征：true/false 值块都以 RETURN_VALUE/RETURN_CONST 终结，无 JUMP_FORWARD，
        无 merge 块，值块含 POP_TOP（表达式语句的值丢弃 + 隐式 return None 栈填充）。

    关键边界：双 RETURN_VALUE 不带 POP_TOP 的模式（`LOAD value; RETURN_VALUE`）
    不是三元，而是 if-return 模式（`if cond: return a; return b`）。两者字节码
    结构上相似（双 RETURN_VALUE 无 JUMP_FORWARD），但语义不同：
      - if-return：值为 return 消费，应识别为 IF_REGION
      - 三元表达式语句：值为 POP_TOP 丢弃，应识别为 TERNARY
    区分判据是值块是否含 POP_TOP：含 POP_TOP → 三元表达式语句；不含 POP_TOP →
    if-return。`return a if cond else b`（函数尾部 return 三元）的字节码与此
    两者都不同——它产生 JUMP_FORWARD + 单 merge RETURN_VALUE（true 块跳到 merge，
    false 块 fallthrough 到 merge），由常规三元识别路径处理，不进入 P1。

    3. 边界条件
    ----------
    - cond_block 必须以 FORWARD_CONDITIONAL_JUMP_OPS 终结
      （POP_JUMP_*_IF_FALSE/TRUE/NONE/NOT_NONE）
    - cond_block 必须有恰好 2 个 conditional_successors
    - true_block/false_block 必须以 RETURN_VALUE/RETURN_CONST 终结
    - 值块的有效值表达式必须是单 LOAD 指令（LOAD_NAME/LOAD_CONST/LOAD_FAST/
      LOAD_GLOBAL/LOAD_DEREF），后跟 POP_TOP + LOAD_CONST None（隐式 return None
      栈填充）
    - 排除 CALL+POP_TOP 模式（函数调用语句，非表达式）
    - 排除含 STORE_*/RAISE_VARARGS/YIELD_VALUE/IMPORT_* 等副作用指令的块
    - 两个值块的 POP_TOP 状态必须一致（同时含 POP_TOP）
    - 值块必须含 POP_TOP（区分三元表达式语句与 if-return 模式）

    4. 归约语义
    ----------
    P1 模式的三元值被 POP_TOP 丢弃——三元表达式作为语句出现，结果不进入显式
    merge 块。归约时创建 TernaryRegion 但 merge_block=None（虚拟 merge），
    merge_context='implicit_return'，has_pop_top=True。AST 生成阶段产出
    Expr(IfExp)（表达式语句）。

    5. AST 映射
    ----------
    P1 → ast.IfExp(test=cond, body=true_value, orelse=false_value)
    外层包裹：Expr(value=IfExp)（表达式语句）

    6. 已知失败模式
    --------------
    本模式库建立前，模块级三元（test_tn06ternarycompare_*, test_tn21ternaryor_*,
    test_tn01-tn25 系列）全部失败，根因：
      (a) MatchRegion 误识别值块为 match 语句（LOAD + POP_TOP + LOAD_CONST None
          + RETURN_VALUE 模式被误判为 match subject 块）→ match_regions 守卫
          拒绝三元识别
    本模式库通过预处理解决该根因：
      - 释放被 MatchRegion 误识别的值块（解除 match_regions 守卫）

    7. P3 模式：while-true + break（Phase 2.5.4 枚举）
    --------------------------------------------------
    用例: `while True: ... break`（无限循环 + break 退出）
    字节码（CPython 3.11+ 实测）:
        NOP                          ← 循环头占位（条件被优化掉）
        >> <body>                    ← 循环体
        <break_target>: LOAD_CONST None; RETURN_VALUE  ← break 编译为 RETURN_VALUE
        <back_edge>: JUMP_BACKWARD → <body>  ← 回边是唯一的循环标记
    特征：循环头是无条件的 NOP（无常量条件检查），循环仅由 JUMP_BACKWARD 回边
    标识。break 被编译为 LOAD_CONST None + RETURN_VALUE（模块级）或 JUMP_FORWARD
    （函数内跳到函数出口），与 return 语句字节码不可区分。
    反归约难点：
      (a) 循环头无条件分支——标准「循环头 = 被回边支配且有条件出口」启发式
          不触发，需依靠回边唯一性识别 while-true
      (b) break 与 return 字节码相同——需依靠支配关系区分（break 退出循环，
          return 退出函数）
    当前状态：LoopRegion.is_while_true=True 已正确识别（while_loop 测试 100%
    通过）。P3 模式枚举用于文档化与查询 API。

    8. P4 模式：chained compare（Phase 2.5.5 枚举）
    -----------------------------------------------
    用例: `a < b < c`（链式比较表达式）
    字节码（CPython 3.11+ 实测，测试上下文）:
        LOAD a; LOAD b; SWAP 2; COPY 2; COMPARE_OP <; POP_JUMP_IF_FALSE → cleanup;
        LOAD c; COMPARE_OP <; POP_JUMP_IF_FALSE → exit;
        JUMP_FORWARD → then;
        cleanup: POP_TOP; LOAD_CONST None; RETURN_VALUE
    字节码（值上下文，如 `z = a < b < c`）:
        LOAD a; LOAD b; SWAP 2; COPY 2; COMPARE_OP <; JUMP_IF_FALSE_OR_POP → cleanup;
        LOAD c; COMPARE_OP <; JUMP_FORWARD → merge;
        cleanup: SWAP 2; POP_TOP;  ← 清理 COPY 保留的中间操作数
        merge: STORE z
    特征：一个源码表达式被降级为多个 COMPARE_OP + SWAP/COPY 栈操作 + 短路分支。
    中间操作数 b 被 COPY(2) 复制供两个比较使用。短路 cleanup 块仅清理栈，无
    AST 对应。
    反归约难点：
      (a) 一个表达式跨多个基本块——短路分支无 AST 对应
      (b) SWAP/COPY 栈操作无 AST 对应——需通过忽略它们 + 从 LOAD_* 重建操作数
      (c) 两种上下文（测试 vs 值）有不同短路指令（POP_JUMP_IF_FALSE vs
          JUMP_IF_FALSE_OR_POP）与不同 cleanup（POP_TOP vs SWAP+POP_TOP）
      (d) not 链式比较通过跳转反转实现（无 UNARY_NOT）
      (e) 与 BoolOp 组合时（`a < b < c and d < e < f`）短路目标交错
    当前状态：_identify_chained_compare_regions 已正确识别基本链式比较
    （if18/adv01/adv05 测试通过）。与 BoolOp 组合的复合模式
    （adv02_chaincmp_and_chaincmp）待 Phase 3 批次 5 修复。P4 模式枚举用于
    文档化与查询 API（is_p4_chained_compare_header）。

    9. P5 模式：BoolOp 短路独立 exit 块（Phase 2.5.6 枚举）
    -------------------------------------------------------
    用例: `if a and b or c: pass`（混合 and/or 链）
    字节码特征：CPython 3.11 在模块级/函数尾部为每个操作数的短路目标发射
    独立的 trivial exit 块（LOAD_CONST None; RETURN_VALUE），而非共享同一
    merge 块。目标 offset 不同但语义等价。
    反归约难点：链检测因 target 不同而中断，需 _is_equivalent_exit_block
    识别语义等价的 exit 块。
    当前状态：已在 _detect_boolop_conditional_chain 修复（bool20 测试通过）。

    10. P6 模式：not X 跳转反转（Phase 2.5.6 枚举）
    -----------------------------------------------
    用例: `while not done and has_data(): pass`（not X 在 and 链中）
    字节码特征：CPython 3.11 优化掉 UNARY_NOT，通过反转跳转方向实现 not 语义。
    `not X` 在 and 链中：跳转是 IF_TRUE（X 为真时 not X 为假，短路退出）。
    反归约难点：字节码无 UNARY_NOT 指令，需从跳转方向重建 not 语义。
    当前状态：已在 _build_boolop_expression / _build_grouped_boolop_expression
    修复（bool11 测试通过）。

    11. P7 模式：while 条件 back-edge 重查（Phase 2.5.6 枚举）
    ---------------------------------------------------------
    用例: `while not done and has_data(): process()`（复合条件 while 循环）
    字节码特征：CPython 3.11 在回边处复制整个 while 条件进行重查。重查块
    含 FORWARD 条件跳转到 trivial exit（每个 and 操作数一个），与正向条件
    结构相同但位于循环体末尾。
    反归约难点：
      (a) 重查块被误识为 IfRegion（需 _should_skip_block_for_if_region
          的 back-edge 重查检测）
      (b) 反向走查误吸外层 if 条件块（需 _back_edge_recheck_count 配额）
    当前状态：已在 _identify_loop_regions + _should_skip_block_for_if_region
    修复（bool11 测试通过）。

    12. P8 模式：隐式 return None（Phase 2.5.6 枚举）
    -----------------------------------------------
    用例: 模块级/函数尾部的隐式 return None
    字节码特征：LOAD_CONST None; RETURN_VALUE（CPython 3.11 在模块级为每个
    退出路径添加隐式 return None）。RETURN_CONST（CPython 3.12+ 优化）。
    反归约难点：隐式 return None 块与显式 return None / break 语句字节码
    相同，需依靠控制流上下文区分。
    当前状态：P1 模式依赖此特征（值块的 LOAD_CONST None + RETURN_VALUE 是
    隐式 return None 栈填充）。_is_trivial_return_block 识别此模式。
    """

    def __init__(self):
        self.patterns: List[PeepholePattern] = [
            PeepholePattern(
                name='P1_DOUBLE_RETURN_TERNARY',
                bytecode_signature=(
                    'cond_block: <cond_expr>, POP_JUMP_FORWARD_IF_{FALSE|TRUE} -> false; '
                    'true:  <value_expr>, POP_TOP, LOAD_CONST None, RETURN_VALUE; '
                    'false: <value_expr>, POP_TOP, LOAD_CONST None, RETURN_VALUE'
                ),
                source_ast_type='ast.IfExp',
                anti_reduction_strategy=(
                    'Create TernaryRegion with merge_block=None (virtual merge), '
                    "merge_context='implicit_return', has_pop_top=True. "
                    'AST: Expr(IfExp) (expression statement, value discarded).'
                ),
                invariants=[
                    'cond_block ends with FORWARD_CONDITIONAL_JUMP_OPS',
                    'cond_block has exactly 2 conditional_successors',
                    'both value blocks end with RETURN_VALUE/RETURN_CONST',
                    'value blocks contain no STORE_*/RAISE_VARARGS/YIELD_VALUE/IMPORT_*',
                    'value blocks contain no CALL+POP_TOP pattern (statement, not expression)',
                    'both value blocks contain POP_TOP (expression statement, not if-return)',
                ],
            ),
            PeepholePattern(
                name='P3_WHILE_TRUE_BREAK',
                bytecode_signature=(
                    'header: NOP (condition elided by peephole); '
                    'body: <loop_body>; '
                    'break: LOAD_CONST None, RETURN_VALUE (module-level) or '
                    'JUMP_FORWARD -> func_exit (function-level); '
                    'back_edge: JUMP_BACKWARD -> header'
                ),
                source_ast_type='ast.While',
                anti_reduction_strategy=(
                    'Create LoopRegion with is_while_true=True, condition_block=None. '
                    'break blocks identified via dominance (break exits loop, '
                    'return exits function). AST: While(test=Constant(True), body=..., orelse=[]).'
                ),
                invariants=[
                    'header is NOP (no conditional branch at loop entry)',
                    'back_edge is JUMP_BACKWARD to header',
                    'break compiled to LOAD_CONST None + RETURN_VALUE (module) or '
                    'JUMP_FORWARD (function)',
                    'break and return have identical bytecode — distinguished by dominance',
                ],
            ),
            PeepholePattern(
                name='P4_CHAINED_COMPARE',
                bytecode_signature=(
                    'test context: LOAD a, LOAD b, SWAP 2, COPY 2, COMPARE_OP, '
                    'POP_JUMP_IF_FALSE -> cleanup; LOAD c, COMPARE_OP, '
                    'POP_JUMP_IF_FALSE -> exit; JUMP_FORWARD -> then; '
                    'cleanup: POP_TOP, LOAD_CONST None, RETURN_VALUE; '
                    'value context: same but JUMP_IF_FALSE_OR_POP + SWAP 2, POP_TOP cleanup'
                ),
                source_ast_type='ast.Compare',
                anti_reduction_strategy=(
                    'Create IfRegion with chained_compare_blocks/chained_compare_ops. '
                    'AST: Compare(left=a, ops=[Lt, Lt], comparators=[b, c]). '
                    'SWAP/COPY/COMPARE_OP consumed implicitly by extracting LOAD_* operands.'
                ),
                invariants=[
                    'header block contains COPY(arg=2) immediately followed by COMPARE_OP/IS_OP/CONTAINS_OP',
                    'fall-through chain has >= 1 extra chain block (>= 2 ops total)',
                    'test context: POP_JUMP_IF_FALSE short-circuit + POP_TOP cleanup',
                    'value context: JUMP_IF_FALSE_OR_POP short-circuit + SWAP+POP_TOP cleanup',
                    'not chain: final jump inverted (POP_JUMP_IF_TRUE instead of FALSE)',
                ],
            ),
            PeepholePattern(
                name='P5_BOOLOP_SEPARATE_EXIT',
                bytecode_signature=(
                    'Each operand in and/or chain has its own trivial exit block '
                    '(LOAD_CONST None, RETURN_VALUE) at module/function-tail position. '
                    'Targets differ but are semantically equivalent.'
                ),
                source_ast_type='ast.BoolOp',
                anti_reduction_strategy=(
                    'Use _is_equivalent_exit_block to treat separate trivial exit '
                    'blocks as equivalent in _detect_boolop_conditional_chain. '
                    'AST: BoolOp(op=And/Or, values=[...]).'
                ),
                invariants=[
                    'each operand short-circuit target is a trivial return block',
                    'targets have different offsets but same semantics',
                    '_is_equivalent_exit_block returns True for any pair',
                ],
            ),
            PeepholePattern(
                name='P6_NOT_X_JUMP_INVERSION',
                bytecode_signature=(
                    'not X in boolop chain: no UNARY_NOT instruction. '
                    'Jump direction inverted: not X in AND chain uses POP_JUMP_IF_TRUE '
                    '(exit when X is true, i.e. not X is false).'
                ),
                source_ast_type='ast.UnaryOp(Not)',
                anti_reduction_strategy=(
                    'In _build_boolop_expression / _build_grouped_boolop_expression, '
                    'when chain_op is "and" and jump is IF_TRUE, wrap operand in '
                    'UnaryOp(Not, ...). AST: UnaryOp(op=Not, operand=X).'
                ),
                invariants=[
                    'no UNARY_NOT instruction in bytecode',
                    'not X in AND chain: POP_JUMP_IF_TRUE (inverted)',
                    'not X in OR chain: POP_JUMP_IF_FALSE (inverted)',
                ],
            ),
            PeepholePattern(
                name='P7_WHILE_BACKEDGE_RECHECK',
                bytecode_signature=(
                    'While condition duplicated at back edge: back_edge block contains '
                    'FORWARD conditional jumps to trivial exit blocks (one per AND operand), '
                    'mirroring the forward condition structure.'
                ),
                source_ast_type='ast.While',
                anti_reduction_strategy=(
                    'Detect back-edge recheck in _should_skip_block_for_if_region '
                    '(skip IfRegion creation for recheck blocks). '
                    'Use _back_edge_recheck_count quota in backward walk to limit '
                    'absorbed equivalent-exit predecessors. AST: While(test=..., body=...).'
                ),
                invariants=[
                    'back-edge block has FORWARD conditional jumps to trivial exits',
                    'recheck count = number of AND operands in while condition',
                    'recheck blocks must be skipped by IfRegion identifier',
                ],
            ),
            PeepholePattern(
                name='P8_IMPLICIT_RETURN_NONE',
                bytecode_signature=(
                    'Module-level/function-tail: LOAD_CONST None, RETURN_VALUE '
                    '(CPython 3.11) or RETURN_CONST (CPython 3.12+). '
                    'Added to every exit path implicitly.'
                ),
                source_ast_type='ast.Constant(None) / implicit',
                anti_reduction_strategy=(
                    '_is_trivial_return_block identifies this pattern. '
                    'P1 pattern depends on it (value block LOAD_CONST None + RETURN_VALUE '
                    'is implicit return None stack fill). Distinguish from explicit '
                    'return None and break via control-flow context.'
                ),
                invariants=[
                    'block contains only LOAD_CONST None + RETURN_VALUE (or RETURN_CONST None)',
                    'no other effective instructions',
                    'semantically equivalent across different offsets',
                ],
            ),
        ]
        # P1 模式匹配的 cond_block 集合（由 match_peephole_pattern 填充）
        # 用于区域识别阶段查询某块是否为 P1 模式的条件块
        self._p1_cond_blocks: Dict[int, Dict[str, Any]] = {}
        # P3 模式匹配的 while-true 循环头集合（由 match_peephole_pattern 填充）
        self._p3_headers: Set[int] = set()
        # P4 模式匹配的链式比较头集合（由 match_peephole_pattern 填充）
        self._p4_headers: Set[int] = set()

    def match_peephole_pattern(self, blocks, cfg) -> List[Dict[str, Any]]:
        """在识别阶段预处理时扫描所有模式。

        Args:
            blocks: Iterable[BasicBlock] - CFG 中所有基本块
            cfg: ControlFlowGraph

        Returns:
            List[Dict] - 匹配结果列表，每个结果包含：
                - 'pattern_name': str  （模式名）
                - 'cond_block': BasicBlock  （条件块）
                - 'true_block': BasicBlock  （真值块）
                - 'false_block': BasicBlock  （假值块）
                - 'has_pop_top': bool  （恒为 True，标识三元表达式语句）
                - 'value_blocks_to_release': List[BasicBlock]
                  （需要从 MatchRegion 释放的值块）
        """
        # 重置内部状态
        self._p1_cond_blocks = {}
        self._p3_headers = set()
        self._p4_headers = set()
        matches: List[Dict[str, Any]] = []
        for block in blocks:
            # P1: 双 RETURN_VALUE 三元表达式语句
            match = self._match_p1_double_return_ternary(block, cfg)
            if match is not None:
                matches.append(match)
                # 索引：以 cond_block.start_offset 为键
                self._p1_cond_blocks[block.start_offset] = match
            # P3: while-true + break 循环头
            if self._match_p3_while_true_header(block, cfg):
                self._p3_headers.add(block.start_offset)
                matches.append({
                    'pattern_name': 'P3_WHILE_TRUE_BREAK',
                    'header_block': block,
                })
            # P4: 链式比较头
            if self._match_p4_chained_compare_header(block, cfg):
                self._p4_headers.add(block.start_offset)
                matches.append({
                    'pattern_name': 'P4_CHAINED_COMPARE',
                    'header_block': block,
                })
        return matches

    def is_p1_cond_block(self, block) -> bool:
        """查询某块是否为已识别的 P1 模式条件块。"""
        return block is not None and block.start_offset in self._p1_cond_blocks

    def get_p1_match(self, block) -> Optional[Dict[str, Any]]:
        """获取某块对应的 P1 模式匹配结果（若有）。"""
        if block is None:
            return None
        return self._p1_cond_blocks.get(block.start_offset)

    def is_p3_while_true_header(self, block) -> bool:
        """查询某块是否为已识别的 P3 模式 while-true 循环头。

        P3 模式：while True: ... break
        循环头是 NOP 占位（条件被 CPython peephole 优化掉），
        循环仅由 JUMP_BACKWARD 回边标识。
        """
        return block is not None and block.start_offset in self._p3_headers

    def is_p4_chained_compare_header(self, block) -> bool:
        """查询某块是否为已识别的 P4 模式链式比较头。

        P4 模式：a < b < c
        头块含 COPY(arg=2) 紧跟 COMPARE_OP/IS_OP/CONTAINS_OP。
        """
        return block is not None and block.start_offset in self._p4_headers

    def _match_p1_double_return_ternary(self, cond_block, cfg) -> Optional[Dict[str, Any]]:
        """检测 P1 模式: 双 RETURN_VALUE 三元表达式语句。

        检测步骤:
          1. cond_block 以 FORWARD_CONDITIONAL_JUMP_OPS 终结
          2. cond_block 有恰好 2 个 conditional_successors
          3. 两个后继都以 RETURN_VALUE/RETURN_CONST 终结
          4. 两个后继的有效值表达式是单 LOAD 指令
          5. 排除 CALL+POP_TOP 模式（语句，非表达式）
          6. 排除含 STORE/RAISE/YIELD/IMPORT 等副作用指令的块
          7. 两个值块的 POP_TOP 状态必须一致
          8. 值块必须含 POP_TOP（区分三元表达式语句与 if-return 模式）
        """
        last_instr = cond_block.get_last_instruction()
        if not last_instr:
            return None

        # 步骤 1: cond_block 以 FORWARD_CONDITIONAL_JUMP_OPS 终结
        if last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        if last_instr.argval is None:
            return None

        # 步骤 1b: cond_block 必须含条件表达式（至少一条非噪音指令在 POP_JUMP 之前）。
        # `async def f(): if await g(): return 1; return 0` 编译后 cond_block
        # 可能只是裸 `POP_JUMP_IF_FALSE`（条件表达式在前驱块中通过 SEND/
        # YIELD_VALUE 链计算后留在栈上）。此场景不是三元表达式（无内联条件），
        # 必须跳过 P1 匹配，否则会创建无条件的 TernaryRegion 破坏 IfRegion。
        _cond_non_noise = [i for i in cond_block.instructions
                           if i.opname not in NOISE_OPS
                           and i is not last_instr]
        if not _cond_non_noise:
            return None

        # 步骤 1c: cond_block 的前驱不能以 JUMP_BACKWARD_NO_INTERRUPT 终结。
        # `async def f(): if await g() > 0: return 1; return 0` 编译后，
        # await 表达式在 SEND/YIELD_VALUE/JUMP_BACKWARD_NO_INTERRUPT 循环中计算，
        # 结果留在栈上。cond_block 只含 `LOAD_CONST 0; COMPARE_OP >; POP_JUMP`
        # （条件的一部分），P1 会创建条件不完整的三元（如 `1 if 0 else 0`）。
        # JUMP_BACKWARD_NO_INTERRUPT 是 await 循环专属指令，不会出现在普通循环中。
        for _pred in cond_block.predecessors:
            _pred_last = _pred.get_last_instruction()
            if (_pred_last is not None
                    and _pred_last.opname == 'JUMP_BACKWARD_NO_INTERRUPT'):
                return None

        # 步骤 2: 恰好 2 个 conditional_successors
        succs = list(cond_block.conditional_successors)
        if len(succs) != 2:
            return None

        # 区分 true_block (fallthrough) 和 false_block (jump target)
        true_block = next((s for s in succs
                           if s.start_offset != last_instr.argval), None)
        false_block = next((s for s in succs
                            if s.start_offset == last_instr.argval), None)
        if true_block is None or false_block is None:
            return None
        if true_block is false_block:
            return None

        # 步骤 3: 两个后继都以 RETURN_VALUE/RETURN_CONST 终结
        if not _ends_with_return(true_block) or not _ends_with_return(false_block):
            return None

        # 步骤 4: 两个后继的有效值表达式是单 LOAD 指令
        if not _is_single_load_value_block(true_block):
            return None
        if not _is_single_load_value_block(false_block):
            return None

        # 步骤 5: 排除 CALL+POP_TOP 模式
        if _has_call_pop_top(true_block) or _has_call_pop_top(false_block):
            return None

        # 步骤 6: 排除含副作用指令的块
        # 同时检查 cond_block（排除 walrus 赋值 `if (n := expr):` 等场景，
        # 其条件含 STORE_* 副作用，不应识别为三元——条件重建会丢失 walrus
        # 语义，生成破碎的 `1 if 0 else 0`）和值块。
        for blk in (cond_block, true_block, false_block):
            for i in blk.instructions:
                if i.opname in SIDE_EFFECT_OPS:
                    return None

        # 步骤 7: 两个值块的 POP_TOP 状态必须一致
        has_pop_top_true = _has_pop_top(true_block)
        has_pop_top_false = _has_pop_top(false_block)
        if has_pop_top_true != has_pop_top_false:
            return None
        has_pop_top = has_pop_top_true

        # 步骤 8: 值块必须含 POP_TOP。
        # 双 RETURN_VALUE 模式下，含 POP_TOP 的值块对应三元表达式语句
        # （`a if cond else b` 的值被丢弃，编译为 LOAD value; POP_TOP;
        # LOAD_CONST None; RETURN_VALUE）。不含 POP_TOP 的值块对应 if-return
        # 模式（`if cond: return a; return b` 编译为 LOAD value; RETURN_VALUE），
        # 应识别为 IF_REGION 而非 TERNARY。`return a if cond else b` 不进入
        # 此分支——它产生 JUMP_FORWARD + 单 merge RETURN_VALUE（true 块以
        # JUMP_FORWARD 终结而非 RETURN_VALUE），由常规三元识别路径处理。
        # 不含 POP_TOP 时返回 None，让 _block_is_return_body 守卫拒绝三元，
        # 由 IfRegion 识别处理。
        if not has_pop_top:
            return None

        return {
            'pattern_name': 'P1_DOUBLE_RETURN_TERNARY',
            'cond_block': cond_block,
            'true_block': true_block,
            'false_block': false_block,
            'has_pop_top': has_pop_top,
            'value_blocks_to_release': [true_block, false_block],
        }

    def _match_p3_while_true_header(self, block, cfg) -> bool:
        """检测 P3 模式: while-true + break 循环头。

        CPython 3.11+ peephole 优化器将 `while True:` 的条件检查完全消除，
        循环头变为 NOP 占位。循环仅由 JUMP_BACKWARD 回边标识。

        检测步骤:
          1. 块的全部有效指令仅为 NOP（或空块）
          2. 块有至少一个后继是 JUMP_BACKWARD 回边目标（即存在回边指向此块）
          3. 块不是函数入口（RESUME 块）

        本匹配器仅用于标记 while-true 循环头供查询 API 使用。实际循环识别
        由 _identify_loop_regions 通过回边分析完成，不依赖此标记。
        """
        # 步骤 3: 排除函数入口（RESUME 块）
        first_instr = block.instructions[0] if block.instructions else None
        if first_instr is not None and first_instr.opname == 'RESUME':
            # RESUME 块可能同时是循环头（while True 在函数体首行），
            # 检查是否有回边指向此块
            pass  # 不排除，继续检查

        # 步骤 1: 块的有效指令仅为 NOP（while-true 头是无条件占位）
        effective = [i for i in block.instructions
                     if i.opname not in NOISE_OPS]
        if effective:
            # while-true 头不应有有效指令（NOP 占位）
            # 但如果块同时是循环体入口（while True: body_first_stmt），
            # 则有效指令属于循环体，不是循环头
            return False

        # 步骤 2: 存在回边指向此块（JUMP_BACKWARD 的目标）
        for pred in block.predecessors:
            pred_last = pred.get_last_instruction()
            if (pred_last is not None
                    and pred_last.opname in BACKWARD_JUMP_OPS
                    and pred_last.argval == block.start_offset):
                return True

        return False

    def _match_p4_chained_compare_header(self, block, cfg) -> bool:
        """检测 P4 模式: 链式比较头块。

        CPython 3.11+ 将 `a < b < c` 降级为 SWAP/COPY/COMPARE_OP 序列。
        头块含 COPY(arg=2) 紧跟 COMPARE_OP/IS_OP/CONTAINS_OP。

        检测步骤:
          1. 块含 COPY(arg=2) 指令
          2. COPY 之后紧跟 COMPARE_OP/IS_OP/CONTAINS_OP
          3. 块以条件跳转终结（POP_JUMP_IF_FALSE/JUMP_IF_FALSE_OR_POP）

        本匹配器仅用于标记链式比较头供查询 API 使用。实际链式比较识别
        由 _identify_chained_compare_regions 完成，不依赖此标记。
        """
        instrs = block.instructions
        for idx, instr in enumerate(instrs):
            if instr.opname == 'COPY' and instr.arg == 2:
                # 步骤 2: COPY 之后紧跟 COMPARE_OP/IS_OP/CONTAINS_OP
                if idx + 1 < len(instrs):
                    next_instr = instrs[idx + 1]
                    if next_instr.opname in COMPARE_OPS:
                        # 步骤 3: 块以条件跳转终结
                        last = block.get_last_instruction()
                        if (last is not None
                                and (last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                                     or last.opname.startswith('JUMP_IF_'))):
                            return True
        return False


def _ends_with_return(block) -> bool:
    """检查块是否以 RETURN_VALUE/RETURN_CONST 终结。"""
    last = block.get_last_instruction()
    return last is not None and last.opname in RETURN_OPS


def _has_pop_top(block) -> bool:
    """检查块是否含 POP_TOP 指令（非噪音）。"""
    return any(i.opname == 'POP_TOP' for i in block.instructions
               if i.opname not in NOISE_OPS)


def _is_single_load_value_block(block) -> bool:
    """检查块是否是"单 LOAD 表达式 + 可选 POP_TOP + 可选 LOAD_CONST None + RETURN"模式。

    有效模式（按从前往后）:
      - LOAD value; RETURN                              （函数尾部）
      - LOAD value; POP_TOP; LOAD_CONST None; RETURN_VALUE  （模块级）
      - LOAD_CONST value; RETURN_CONST                  （函数尾部，常量）
      - LOAD_CONST value; POP_TOP; LOAD_CONST None; RETURN_VALUE  （模块级，常量）

    排除:
      - 多个 LOAD 指令（如 LOAD a; LOAD b; BINARY_OP）
      - CALL 指令（函数调用，由 _has_call_pop_top 单独检查）
      - 含 STORE/RAISE/YIELD 等副作用指令的块（由调用方检查）
    """
    effective = [i for i in block.instructions
                 if i.opname not in NOISE_OPS]
    if not effective:
        return False

    # 必须以 RETURN 终结
    if effective[-1].opname not in RETURN_OPS:
        return False

    # 值表达式部分（RETURN 之前）
    value_part = effective[:-1]

    # 从尾部向前去除：LOAD_CONST None（隐式 return None 栈填充）→ POP_TOP（值丢弃）
    # 顺序很重要：模块级三元值块是 LOAD value; POP_TOP; LOAD_CONST None; RETURN_VALUE
    # 需要先去除 LOAD_CONST None，再去除 POP_TOP
    if value_part and value_part[-1].opname == 'LOAD_CONST' and value_part[-1].argval is None:
        value_part = value_part[:-1]
    if value_part and value_part[-1].opname == 'POP_TOP':
        value_part = value_part[:-1]

    # 剩余必须是恰好一条 LOAD 指令
    if len(value_part) != 1:
        return False
    return value_part[0].opname in LOAD_VALUE_OPS


def _has_call_pop_top(block) -> bool:
    """检查块是否含 CALL+POP_TOP 模式（函数调用语句，非表达式）。

    CALL 指令后跟 POP_TOP 表示函数调用结果被丢弃（语句），不是三元值表达式。
    """
    effective = [i for i in block.instructions
                 if i.opname not in NOISE_OPS]
    has_call = any(i.opname == 'CALL' for i in effective)
    has_pop_top = any(i.opname == 'POP_TOP' for i in effective)
    # 如果同时有 CALL 和 POP_TOP，且 CALL 之后紧跟 POP_TOP（中间可有 PRECALL）
    if has_call and has_pop_top:
        for idx, i in enumerate(effective):
            if i.opname == 'CALL':
                # 检查 CALL 之后是否紧跟 POP_TOP（允许中间有 PRECALL）
                for j in effective[idx + 1:]:
                    if j.opname == 'POP_TOP':
                        return True
                    if j.opname not in ('PRECALL',):
                        break
    return False
