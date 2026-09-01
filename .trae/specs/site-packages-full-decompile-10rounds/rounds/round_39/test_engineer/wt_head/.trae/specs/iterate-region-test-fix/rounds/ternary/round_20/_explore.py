"""R20 探索脚本：批量验证候选 ternary 模式是否反编译失败。

不依赖 pytest，直接调用 CFGBuilder → RegionAnalyzer → RegionASTGenerator
→ CodeGenerator 管道，比较原始/重编字节码（过滤跳转指令后）。
"""
import sys
import os
import dis
import types
import traceback

sys.path.insert(0, '/workspace')

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator


SKIP_OPNAMES = {
    'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'FOR_ITER', 'SEND',
    'NOP', 'CACHE',
}


def filter_instrs(instrs):
    return [i for i in instrs if i.opname not in SKIP_OPNAMES]


def compare(orig, recomp, depth=0):
    """返回 (ok, msg)。ok=True 表示字节码匹配。"""
    if depth > 5:
        return True, ""
    oi = filter_instrs(list(dis.get_instructions(orig)))
    ri = filter_instrs(list(dis.get_instructions(recomp)))
    if len(oi) != len(ri):
        return False, f"指令数不匹配: {len(oi)} vs {len(ri)}\n  原始: {[i.opname for i in oi[:25]]}\n  重编: {[i.opname for i in ri[:25]]}"
    for i, (a, b) in enumerate(zip(oi, ri)):
        if a.opname != b.opname:
            return False, f"指令{i}操作码不匹配: {a.opname} vs {b.opname}\n  原始: {[x.opname for x in oi[max(0,i-3):i+4]]}\n  重编: {[x.opname for x in ri[max(0,i-3):i+4]]}"
        if a.argval != b.argval and a.opname not in (
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        ):
            if isinstance(a.argval, types.CodeType) and isinstance(b.argval, types.CodeType):
                ok, msg = compare(a.argval, b.argval, depth + 1)
                if not ok:
                    return False, f"嵌套code object不匹配 (指令{i}): {msg}"
            else:
                try:
                    if abs(a.argval or 0) != abs(b.argval or 0):
                        return False, f"指令{i}参数不匹配: {a.argval} vs {b.argval} (op={a.opname})"
                except TypeError:
                    if a.argval != b.argval:
                        return False, f"指令{i}参数不匹配: {a.argval} vs {b.argval} (op={a.opname})"
    return True, ""


def decompile(source):
    code = compile(source, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    decompiled = code_gen.generate(result)
    return code, decompiled


CANDIDATES = [
    # ===== 1. 嵌套 ternary 在 ternary body（非 orelse 链） =====
    ("r20_nested_ternary_in_body",
     "x = (a if (b if c1 else c2) else d)\n"),
    ("r20_nested_ternary_in_cond",
     "x = ((a if c1 else b) if c2 else d)\n"),
    ("r20_triple_nested_both",
     "x = ((a if c1 else b) if c2 else (d if c3 else e))\n"),
    ("r20_nested_ternary_as_call_arg",
     "f(a if (b if c1 else c2) else d)\n"),
    ("r20_nested_ternary_subscript",
     "x[a if (b if c1 else c2) else d]\n"),

    # ===== 2. ternary + walrus 复合 =====
    ("r20_walrus_ternary_in_ternary_cond",
     "x = (n := a) if (m := b if c else d) else e\n"),
    ("r20_walrus_subscr_assign",
     "x[(n := a if c else b)] = y\n"),
    ("r20_walrus_ternary_attr_assign",
     "obj.attr = (n := a if c else b)\n"),
    ("r20_walrus_ternary_dict_key",
     "d = {(n := a if c else b): 1}\n"),

    # ===== 3. f-string 复杂格式 =====
    ("r20_fstring_two_ternary",
     "x = f\"{a if c else b}{d if e else f}\"\n"),
    ("r20_fstring_ternary_conversion",
     "x = f\"{(a if c else b)!r}\"\n"),
    ("r20_fstring_ternary_format_spec",
     "x = f\"{a if c else b:>10}\"\n"),
    ("r20_fstring_ternary_in_format_spec",
     "x = f\"{x:{a if c else b}}\"\n"),
    ("r20_fstring_ternary_nested",
     "x = f\"{a if (b if c1 else c2) else d}\"\n"),

    # ===== 4. set/frozenset literal =====
    ("r20_set_two_ternary",
     "x = {a if c else b, d if e else f}\n"),
    ("r20_set_ternary_mixed",
     "x = {1, a if c else b, 2}\n"),
    ("r20_frozenset_ternary",
     "x = frozenset({a if c else b})\n"),

    # ===== 5. starred 表达式 =====
    ("r20_starred_list_ternary",
     "x = [*[a if c else b]]\n"),
    ("r20_starred_tuple_ternary",
     "x = (*[a if c else b],)\n"),
    ("r20_dict_double_star_ternary",
     "x = {**{a if c else b: 1}}\n"),
    ("r20_starred_call_ternary",
     "f(*[a if c else b])\n"),
    ("r20_starred_call_mixed",
     "f(1, *[a if c else b], 2)\n"),

    # ===== 6. ternary 条件表达式链 =====
    ("r20_ternary_elif_chain",
     "x = a if c1 else b if c2 else d if c3 else e\n"),

    # ===== 7. lambda body 复合 =====
    ("r20_lambda_nested_ternary",
     "f = lambda: a if c else (b if x else d)\n"),
    ("r20_lambda_starargs_ternary",
     "f = lambda *args: a if c else b\n"),
    ("r20_lambda_kwargs_ternary",
     "f = lambda **kw: a if c else b\n"),
    ("r20_lambda_kwonly_ternary",
     "f = lambda *, x: a if c else b\n"),

    # ===== 8. global/nonlocal 上下文 =====
    ("r20_global_then_ternary_assign",
     "def f():\n    global x\n    x = a if c else b\n"),
    ("r20_nonlocal_then_ternary_assign",
     "def f():\n    nonlocal x\n    x = a if c else b\n"),

    # ===== 9. except handler 表达式 =====
    ("r20_except_handler_ternary_as",
     "def f():\n    try:\n        x = 1\n    except (A if c else B) as e:\n        pass\n"),
    ("r20_except_handler_ternary",
     "def f():\n    try:\n        x = 1\n    except (A if c else B):\n        pass\n"),

    # ===== 10. for-else / while-else else body =====
    ("r20_for_else_ternary",
     "def f():\n    for i in r:\n        pass\n    else:\n        x = a if c else b\n"),
    ("r20_while_else_ternary",
     "def f():\n    while c1:\n        pass\n    else:\n        x = a if c else b\n"),

    # ===== 11. class body 复杂赋值 =====
    ("r20_class_body_ternary_method",
     "class C:\n    x = a if c else b\n    def m(self):\n        return self.x\n"),

    # ===== 12. ternary + boolean op 复合 =====
    ("r20_boolop_two_ternary_and",
     "x = (a if c else b) and (d if e else f)\n"),
    ("r20_boolop_two_ternary_or",
     "x = (a if c else b) or (d if e else f)\n"),
    ("r20_unary_not_ternary",
     "x = not (a if c else b)\n"),

    # ===== 13. comprehension if 子句 =====
    ("r20_listcomp_if_ternary",
     "x = [i for i in r if (a if c else b)]\n"),
    ("r20_setcomp_if_ternary",
     "x = {i for i in r if (a if c else b)}\n"),
    ("r20_dictcomp_if_ternary",
     "x = {i: j for i in r if (a if c else b)}\n"),
    ("r20_genexp_if_ternary",
     "x = sum(i for i in r if (a if c else b))\n"),

    # ===== 14. yield from + 复合 =====
    ("r20_yield_from_ternary_binop",
     "def f():\n    yield from (a if c else b) + (d if e else f)\n"),
    ("r20_yield_from_ternary_attr",
     "def f():\n    yield from (a if c else b).m()\n"),

    # ===== 15. assert 复合 message =====
    ("r20_assert_msg_two_ternary_binop",
     "assert x, (a if c else b) + (d if e else f)\n"),
    ("r20_assert_msg_ternary_format",
     "assert x, f\"{(a if c else b)}\"\n"),

    # ===== 额外探索 =====
    ("r20_ternary_in_dict_value_global",
     "def f():\n    global x\n    d = {k: a if c else b}\n"),
    ("r20_ternary_in_aug_assign",
     "x += a if c else b\n"),
    ("r20_ternary_compare_chain_with_ternary_mid",
     "x = a < (b if c else d) < e\n"),
    ("r20_ternary_as_subscript_target_complex",
     "d[a if c else b] += 1\n"),
    ("r20_ternary_in_del_subscript",
     "del d[a if c else b]\n"),
    ("r20_ternary_return_tuple_two",
     "def f():\n    return a if c else b, d if e else f\n"),
    ("r20_ternary_in_match_subject",
     "def f():\n    match a if c else b:\n        case 1:\n            pass\n"),
    ("r20_ternary_in_match_guard",
     "def f():\n    match x:\n        case 1 if (a if c else b):\n            pass\n"),
    ("r20_ternary_dict_key_value_ternary_tuple",
     "x = {(a if c else b): (d if e else f)}\n"),
    ("r20_ternary_compare_with_method_call",
     "x = (a if c else b).m() == d\n"),
    ("r20_ternary_call_then_subscript",
     "x = f(a if c else b)[0]\n"),
    ("r20_ternary_subscript_then_call",
     "x = d[a if c else b]()\n"),
    ("r20_ternary_in_for_iter",
     "def f():\n    for i in (a if c else b):\n        pass\n"),
    ("r20_ternary_starred_in_call_kw",
     "f(x=1, *[a if c else b])\n"),
    ("r20_ternary_in_with_item",
     "def f():\n    with (a if c else b) as x:\n        pass\n"),
    ("r20_ternary_in_async_with_item",
     "async def f():\n    async with (a if c else b) as x:\n        pass\n"),
    ("r20_ternary_tuple_unpack_starred",
     "a, *b = (1, (a if c else b))\n"),
    ("r20_ternary_in_ann_assign_value",
     "x: int = a if c else b\n"),
    ("r20_ternary_dictcomp_value_ternary",
     "x = {k: (a if c else b) for k in r}\n"),
    ("r20_ternary_listcomp_iter_ternary",
     "x = [i for i in (a if c else b)]\n"),
]


def main():
    results = []
    for name, src in CANDIDATES:
        try:
            code, decompiled = decompile(src)
        except Exception as e:
            results.append((name, src, "DECOMPILE_ERROR", str(e), ""))
            continue
        try:
            recompiled = compile(decompiled, '<decompiled>', 'exec')
        except SyntaxError as e:
            results.append((name, src, "RECOMPILE_SYNTAX_ERROR", str(e), decompiled))
            continue
        ok, msg = compare(code, recompiled)
        if ok:
            results.append((name, src, "OK", "", decompiled))
        else:
            results.append((name, src, "FAIL", msg, decompiled))

    print("=" * 80)
    print("R20 探索结果汇总")
    print("=" * 80)
    fails = [r for r in results if r[2] == "FAIL"]
    errors = [r for r in results if r[2] in ("DECOMPILE_ERROR", "RECOMPILE_SYNTAX_ERROR")]
    oks = [r for r in results if r[2] == "OK"]
    print(f"总数: {len(results)}  OK: {len(oks)}  FAIL: {len(fails)}  ERROR: {len(errors)}")
    print()
    print("===== FAIL 列表 =====")
    for name, src, status, msg, decompiled in fails:
        print(f"\n--- {name} ---")
        print(f"源码: {src!r}")
        print(f"反编译:\n{decompiled}")
        print(f"失败: {msg}")
    print()
    print("===== ERROR 列表 =====")
    for name, src, status, msg, decompiled in errors:
        print(f"\n--- {name} ({status}) ---")
        print(f"源码: {src!r}")
        print(f"错误: {msg}")
        if decompiled:
            print(f"反编译:\n{decompiled}")
    print()
    print("===== OK 列表（前10个）=====")
    for name, src, status, msg, decompiled in oks[:10]:
        print(f"  {name}: OK")


if __name__ == '__main__':
    main()
