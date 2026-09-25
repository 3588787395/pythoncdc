# -*- coding: utf-8 -*-
"""build the R67-diag3 specs: C2 = BUILD_CONST_KEY_MAP stack effect (arg+1 pops)."""
import io
import json

GEN = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
C1 = json.load(io.open('specs/cand_r67_bare_return_sink.json', encoding='utf-8'))

ANCHOR2 = (
    "        if op == 'BUILD_SLICE':\n"
    "            return 1, 2 + (instr.arg or 0)\n"
    "        if op.startswith('BUILD_'):\n"
    "            return 1, instr.arg or 0\n"
)

NEW2 = (
    "        # [R67-diag3 C2 BUILD_CONST_KEY_MAP 栈效应 = 1 push / (arg+1) pop]\n"
    "        # 识别条件：opname 恰为 'BUILD_CONST_KEY_MAP'（操作码身份，不看 key/value 内容、\n"
    "        #   不依赖偏移与函数名）。它排在通用 `BUILD_*` 分支之前，其余 BUILD_* 行为不变。\n"
    "        # 归约方式：按 CPython 3.11 该操作码的定义，`BUILD_CONST_KEY_MAP i` 弹出 i 个\n"
    "        #   value **再加 1 个打包好的 const key tuple**（紧邻其前的那条 LOAD_CONST），\n"
    "        #   净压 1 个 dict —— 即 pop = i + 1，而非通用 BUILD_* 的 pop = i。本方法的调用方\n"
    "        #   _extract_dict_prefix_values / _generate_ternary 的 cond_val_start 检测都按\n"
    "        #   `needed` 反向累加此二元组来切分「条件测试之前的值表达式段」：旧的 pop = i 少算\n"
    "        #   了一次弹栈，使 key-tuple 那条 LOAD_CONST 被当作**独立**的一段值，整张 dict 因此\n"
    "        #   被拆散，重建时只剩 keys[0] 与最后一个 value（`{'error_no': -1, 'error_info': m}`\n"
    "        #   → `{'error_no': m}`）。修正后整条 const-key dict 构建落进同一段，父容器按压栈\n"
    "        #   顺序拿到一个完整的 Dict 子节点。\n"
    "        # AST 映射：dict 字面量（所有 key 均为常量串）在 condition_block 前缀里的字节码段\n"
    "        #   (v1..vi, LOAD_CONST (k1..ki), BUILD_CONST_KEY_MAP i) ⇒ 单个 ast.Dict(keys=[k1..ki],\n"
    "        #   values=[v1..vi]) 节点，作为父容器（Tuple/Dict）的一个同层子表达式。\n"
    "        if op == 'BUILD_CONST_KEY_MAP':\n"
    "            return 1, (instr.arg or 0) + 1\n"
)

spec2 = {
    "name": "cand_r67_bckm_stack_effect",
    "file": "core/cfg/region_ast_generator.py",
    "edits": [{"anchor": ANCHOR2, "repl": ANCHOR2 + NEW2}],
    "note": "R67 diag3 C2",
}
spec3 = {
    "name": "cand_r67_bckm_stack_effect_plus_bare_return_sink",
    "file": "core/cfg/region_ast_generator.py",
    "edits": [],
    "note": "R67 diag3 C1+C2 pair",
}
u = io.open(GEN, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
print('anchor2 count =', u.count(ANCHOR2))
spec3['edits'] = C1['edits'] + spec2['edits']
for nm, sp in (('cand_r67_bckm_stack_effect', spec2),
               ('cand_r67_pair', spec3)):
    io.open('specs/%s.json' % nm, 'w', encoding='utf-8').write(
        json.dumps(sp, ensure_ascii=False, indent=1))
    print('wrote', nm)
