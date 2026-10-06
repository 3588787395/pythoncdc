# 临时校验：证明本轮整改为纯注释/文档级（剥离 docstring 后 AST 恒等）
import ast
import sys

P = r'f:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py'
cur = open(P, encoding='utf-8-sig').read()

b_new = ("                # 依原则 2（每块唯一归属）：链步块归属 BoolOpRegion，不得再被\n"
         "                # ternary 认领（判据只读块末 opcode 族，I.4 白名单）。\n"
         "                # C1：只读本块末指令 opcode 族（SHORT_CIRCUIT_JUMP_OPS），同层结构事实；\n"
         "                # C2：真 ternary 条件恒以条件跳转收尾，不被本守卫命中；守卫未命中\n"
         "                #     时逐位维持既有 ternary 认领行为，BoolOp 与 ternary 各自独立保真；\n"
         "                # C3：守卫封闭 ternary 认领域，令值位 BoolOp 链步块唯一归 BoolOpRegion。\n")
b_old = ("                # 依原则 2（每块唯一归属）：链步块归属 BoolOpRegion，不得再被\n"
         "                # ternary 认领（判据只读块末 opcode 族，I.4 白名单）。\n")

a2_new = ("        满足 C1（只读本块指令序列与 opcode，同层结构事实）/ C2（真实链式比较\n"
          "        判定不变：形态相同则判定逐位不变）/ C3（本方法只判形态；对循环返回\n"
          "        拆除段的显式排除由调用点 `_has_compare_chain_step_predecessor` 施加，\n"
          "        守卫封闭在调用侧）。\n")
a2_old = ("        满足 C1（同层结构事实）/ C2（真实链式比较判定不变）/ C3（对循环\n"
          "        返回拆除段显式排除，守卫封闭）。\n")

a1_new = ("        【算法依据】\n"
          "        链式比较（`a < b < c` 等）在值上下文由 [R113 fix] 引入的清理块\n"
          "        （SWAP 2 + POP_TOP）承载中间值抹除。**本方法只按 `SWAP 2 + POP_TOP`\n"
          "        指令序列（NOISE_OPS 过滤后恰两条有效指令）判定「清理块形态」，不做\n"
          "        任何前驱判定**；因该指令序列与 `for` 循环体内 `return <表达式>` 的隐藏\n"
          "        迭代器拆除段（SWAP 2; POP_TOP; RETURN_VALUE）完全同形，单凭本方法会把\n"
          "        循环返回拆除段一并判为清理块。B99 的「比较链步前驱」追加条件由**调用点**\n"
          "        （`_detect_boolop_short_circuit_chain` 的 R113 分支）以\n"
          "        `_has_compare_chain_step_predecessor` 施加，不在本方法内。判据只读本块\n"
          "        指令序列与 opcode，符合 I.4 白名单。\n")
a1_old = ("        【算法依据】\n"
          "        链式比较（`a < b < c` 等）在值上下文由 [R113 fix] 引入的清理块\n"
          "        （SWAP 2 + POP_TOP）承载中间值抹除；清理块的指令序列与 `for` 循环体\n"
          "        内 `return <表达式>` 的隐藏迭代器拆除段（SWAP 2; POP_TOP; RETURN_VALUE）\n"
          "        完全同形。原实现仅凭两条有效指令（SWAP + POP_TOP）判定，会把循环\n"
          "        返回拆除段误判为比较链清理块，使 `for` 体宿主下的值位 BoolOp 消费链\n"
          "        在短路跳转处被 R113 分支截断（B99 表达式蒸发）。[B99 fix] 追加\n"
          "        `_has_compare_chain_step_predecessor` 守卫：只有存在「短路跳转收尾且\n"
          "        跳转前紧跟比较族操作码」的前驱块时才认定为清理块。\n"
          "        判据只读同层块结构事实（块末 opcode 族 + 前驱集合 + 前驱块指令\n"
          "        opcode），符合 I.4 白名单。\n")

pre = cur
for new, old in ((b_new, b_old), (a2_new, a2_old), (a1_new, a1_old)):
    if new not in pre:
        sys.exit('REVERSE_ANCHOR_NOT_FOUND')
    pre = pre.replace(new, old)

def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return tree

a = ast.dump(strip_docstrings(ast.parse(cur)))
b = ast.dump(strip_docstrings(ast.parse(pre)))
print('LOGIC_AST_EQUAL =', a == b)
print('cur_len=%d pre_len=%d delta=%d' % (len(cur), len(pre), len(cur) - len(pre)))
