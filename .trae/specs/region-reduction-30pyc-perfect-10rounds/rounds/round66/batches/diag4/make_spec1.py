# -*- coding: utf-8 -*-
"""Build specs/cand_r66_d1_augsub_continue.json from the CURRENT landed bytes.
Single file / single anchor; anchor uniqueness asserted on the LF-normalised text."""
import io, json, sys
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
u = io.open(SRC, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if u.count('\r') else '\n'
u = u.replace(nl, '\n')
lines = u.split('\n')
anchor = '\n'.join(lines[44368:44371])
assert u.count(anchor) == 1, u.count(anchor)

I24 = ' ' * 24
I28 = ' ' * 28
repl = anchor.split('\n')[0] + '\n' + '\n'.join([
    I28 + '# [R66-diag4 D1 augsub-continue-role] CONTINUE 角色块的增强下标赋值重建。',
    I28 + '# 识别条件：栈上表达式串含 in-place BINARY_OP(arg>=13) 且其后至少一条 SWAP，',
    I28 + '#   且含 COPY(arg>=2) 目标复制 —— 即 CPython 3.11 `c[k] op= v` 的读回协议',
    I28 + '#   `LOAD c, LOAD k, COPY, COPY, BINARY_SUBSCR, <v>, BINARY_OP(自增), SWAP, SWAP,',
    I28 + '#   STORE_SUBSCR`；与 _build_effective_stmts 里 [R102 fix] 的判据同一层次',
    I28 + '#   （块内语句切分器）、同一结构身份（栈协议特征，不含名字/偏移/阈值）。',
    I28 + '# 归约方式：把整串连同本条 STORE_SUBSCR 委托给同层次语句构造器',
    I28 + '#   _build_subscript_assign 做栈模拟重建；返回 None 时原样落回下方既有的',
    I28 + '#   _split_subscr_operands 切分路径（零退化）。',
    I28 + '# AST 映射：AugAssign(target=Subscript(value=容器, slice=键), op=自增运算符,',
    I28 + '#   value=右值)；未命中/委托失败仍是 Assign(targets=[Subscript], value=…)。',
    I28 + "_r66d4_aug = any(",
    I28 + "    _r66d4_i.opname == 'BINARY_OP' and _r66d4_i.arg is not None and _r66d4_i.arg >= 13",
    I28 + "    and any(_r66d4_s.opname == 'SWAP'",
    I28 + "                for _r66d4_s in _eff_expr_instrs[_r66d4_e + 1:])",
    I28 + "    for _r66d4_e, _r66d4_i in enumerate(_eff_expr_instrs))",
    I28 + "if _r66d4_aug and any(_r66d4_c.opname == 'COPY' and _r66d4_c.arg is not None",
    I28 + "                     and _r66d4_c.arg >= 2 for _r66d4_c in _eff_expr_instrs):",
    I28 + "    _r66d4_stmt = self._build_subscript_assign(_eff_expr_instrs + [_instr])",
    I28 + "    if _r66d4_stmt is not None:",
    I28 + "        _eff_stmts.append(_r66d4_stmt)",
    I28 + "        _eff_expr_instrs = []",
    I28 + "        continue",
    I28 + '# 栈效应切分支持多指令容器（data.loc = LOAD+LOAD_ATTR）。',
    I28 + '_split = self._split_subscr_operands(_eff_expr_instrs)',
])
assert repl.startswith(anchor.split('\n')[0]) and repl.endswith('_split = self._split_subscr_operands(_eff_expr_instrs)')
io.open('specs/cand_r66_d1_augsub_continue.json', 'w', encoding='utf-8').write(json.dumps(
    {'file': 'core/cfg/region_ast_generator.py', 'anchor': anchor, 'repl': repl},
    ensure_ascii=False, indent=1))
print('spec written; inserted lines =', repl.count('\n') - anchor.count('\n'))
