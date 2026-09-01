"""
Defect 05 — ASSERT/COMPARE: 链式比较中的 CALL 参数丢失 (`len(s)` → `len`)
================================================================
触发区域类型：ASSERT + COMPARE_OP (链式比较 11 >= len(s) >= 9)
根因初判：
    core/cfg/region_ast_generator.py 的链式比较重建
    (`_generate_compare` / `Compare` AST 重建) 在处理
    `11 >= len(s) >= 9` 三元链式比较时，把中段 `len(s)` 的
    CALL 节点拆解为单独的 LOAD_GLOBAL len，丢失了 LOAD_FAST s
    + PRECALL + CALL 指令，导致只剩裸 `len`。
    区域归约时把 `len(s)` 的 CALL 错误归并到比较链的左/右操作数，
    违反「嵌套即抽象节点」：len(s) 应作为一个 Call 子节点整体
    参与比较，不可拆分。

最小字节码模式（Python 3.11，链式比较 + CALL）：
    LOAD_CONST 11
    LOAD_GLOBAL len
    LOAD_FAST s
    PRECALL 1
    CALL 1
    LOAD_CONST 9
    COMPARE_OP <=                # 11 >= len(s)
    SWAP / COPY                  # 链式中段
    COMPARE_OP <=                # len(s) >= 9
    COMPARE_OP                   # 链式比较合并
    POP_JUMP_IF_FALSE
    <assert msg>

反编译产物（错误）：
    assert 11 >= len >= 9, 'msg2'
期望产物：
    assert 11 >= len(s) >= 9, 'msg2'

验证：python pycdc.py <this>.pyc  # 观察 len 丢失参数
"""
def check_stock(s):
    assert isinstance(s, str), "msg"
    assert 11 >= len(s) >= 9, 'msg2'
    assert s.split('.')[1] in ('SS', 'SZ'), "msg3"
