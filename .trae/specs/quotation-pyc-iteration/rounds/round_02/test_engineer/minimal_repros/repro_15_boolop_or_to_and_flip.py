"""
Defect 15 (R2 新增) — BOOLOP：`not (A == x or B == y or ...)` 链中 `or` 被误重建为 `and`
================================================================
R1 关联：无（R2 新出现；与 repro_06 BOOLOP and/or 归约同源但反向）。

R2 复现状态：**新出现**。
  quotation.pyc::check_frequency line 1921（R2 产物）：
        if not (frequency[-1:] == 'm' and frequency[-1:] == 'd' and frequency == '1w' and frequency == 'mo' and frequency == '1q' and frequency == '1y'):
            assert frequency == '1y', "您输入的频率有误..."
  —— 原始 `if not (frequency[-1:] == 'm' or ... or frequency == '1y'):`
     中 6 路 `or` 短路全部被误重建为 `and`。原字节码每路 `==` 后跟
     `POP_JUMP_FORWARD_IF_TRUE to 196`（or 短路：任一为真即跳过 assert），
     归约器把 `POP_JUMP_IF_TRUE`（or）误读为 `POP_JUMP_IF_FALSE`（and）。

触发区域类型：BOOLOP (or → and) + COMPARE_OP (== 链) + UnaryOp (not)
根因初判：
    `core/cfg/region_ast_generator.py` 的 BoolOp 重建把
    `POP_JUMP_FORWARD_IF_TRUE`（or 的短路跳转）与 `POP_JUMP_FORWARD_IF_FALSE`
    （and 的短路跳转）混淆，统一重建为 `and`。
    违反「入口引用语义」：or/and 的短路方向决定 BoolOp.op，不可互换。

最小字节码模式（Python 3.11，not(== or == or ==)）：
    LOAD_FAST frequency / LOAD_CONST -1 / BUILD_SLICE / BINARY_SUBSCR
    LOAD_CONST 'm'
    COMPARE_OP ==
    POP_JUMP_FORWARD_IF_TRUE to <skip>       # or 短路（任一真→跳过 assert）
    LOAD_FAST frequency / ... / COMPARE_OP == 'd'
    POP_JUMP_FORWARD_IF_TRUE to <skip>       # or
    ...
  <skip>:
    <next stmt>

R2 反编译产物（错误，or → and）：
    if not (frequency[-1:] == 'm' and frequency[-1:] == 'd' and frequency == '1w' and frequency == 'mo' and frequency == '1q' and frequency == '1y'):
        assert frequency == '1y', 'msg'
期望产物：
    if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == 'mo' or frequency == '1q' or frequency == '1y'):
        assert frequency == '1y', 'msg'

验证：python pycdc.py <this>.pyc  # 观察 not(... or ...) 被重建为 not(... and ...)
"""
def check_frequency(frequency):
    if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == '1w' or frequency == '1y'):
        assert frequency == '1y', 'frequency error'
    return frequency
