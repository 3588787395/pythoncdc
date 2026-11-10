# fix156.py: rr-v5r156 [v156-BINPAREN] BinOp 同优先级右子括号族（只增不破）
# 文件: core/cfg/code_generator.py 两处（AST 路径 _generate_binary + dict 路径
# _generate_binop_from_dict）——same-prec 右子括号集 ('-', '/', '//', '%') 扩为
# 全部左结合算子；'**'（右结合）除外。既有 '-','/','//','%' 行为逐位不变。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/code_generator.py'
MARKER = 'v156-BINPAREN'

s = io.open(PATH, encoding='utf-8').read()
orig = s

NEW_TUPLE = "('+', '-', '*', '@', '/', '//', '%', '<<', '>>', '&', '^', '|')"

COMMENT = (
    "        # [v156-BINPAREN] 同优先级右子 BinOp 为左结合算子时必须括号：\n"
    "        # 右嵌套形（NUL * (BLOCKSIZE * 2)，tarfile.close 实形）不加括号\n"
    "        # 会重结合为左结合形（NUL * BLOCKSIZE * 2），重编译指令序不同\n"
    "        # （LOAD a; LOAD b; LOAD c; OP; OP vs LOAD a; LOAD b; OP; LOAD c; OP）。\n"
    "        # 括号集扩为全部左结合算子；'**' 右结合除外（a ** (b ** c) 不带\n"
    "        # 括号重解析即右嵌套形，字节等价）。'-','/','//','%' 既有行为逐位不变。\n"
)

# ---------- Site 1: _generate_binary (AST 路径) ----------
old1 = (
    "        # 对于右子表达式：\n"
    "        # - 如果优先级低于当前优先级，需要括号\n"
    "        # - 如果优先级相同且是右结合操作符（**），不需要括号\n"
    "        # - 如果优先级相同且是左结合操作符，不需要括号\n"
    "        if right_precedence < current_precedence:\n"
    "            right_code = self._generate_expression(node.right, current_precedence)\n"
    "        elif right_precedence == current_precedence and op_str in ('-', '/', '//', '%'):\n"
)
assert s.count(old1) == 1, 'site1 anchor count %d' % s.count(old1)
new1 = (
    "        # 对于右子表达式：\n"
    "        # - 如果优先级低于当前优先级，需要括号\n"
    "        # - 如果优先级相同且是右结合操作符（**），不需要括号\n"
    "        # - 如果优先级相同且是左结合操作符，需要括号 [v156-BINPAREN]\n"
    "        if right_precedence < current_precedence:\n"
    "            right_code = self._generate_expression(node.right, current_precedence)\n"
    + COMMENT
    + "        elif right_precedence == current_precedence and op_str in " + NEW_TUPLE + ":\n"
)
s = s.replace(old1, new1, 1)

# ---------- Site 2: _generate_binop_from_dict (dict 路径) ----------
old2 = (
    "        # 右子表达式：优先级低于当前时加括号\n"
    "        if right_prec < current_precedence:\n"
    "            right_code = self._generate_expression(right, current_precedence)\n"
    "        elif right_prec == current_precedence and op_str in ('-', '/', '//', '%'):\n"
)
assert s.count(old2) == 1, 'site2 anchor count %d' % s.count(old2)
new2 = (
    "        # 右子表达式：优先级低于当前时加括号\n"
    "        if right_prec < current_precedence:\n"
    "            right_code = self._generate_expression(right, current_precedence)\n"
    + COMMENT
    + "        elif right_prec == current_precedence and op_str in " + NEW_TUPLE + ":\n"
)
s = s.replace(old2, new2, 1)

assert s != orig
assert s.count(MARKER) >= 2
io.open(PATH, 'w', encoding='utf-8', newline='').write(s)
print('fix156 applied: %d marker sites' % s.count(MARKER))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
