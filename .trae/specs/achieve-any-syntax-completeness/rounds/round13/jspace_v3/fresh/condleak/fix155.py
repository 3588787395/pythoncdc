# fix155.py: [v155-CONDLEAK] value-context BoolOp merge block hosting the next
#   statement's if test — the guard_clause_prefix_end marker gate lacked the
#   _is_merge_if_condition + _value_merge_hosts_next_if conjunction.
#   `bufsize = bufsize or 16*1024` followed by `if length == 0:` compiles the
#   STORE + the next statement's COMPARE test into ONE basic block (B8): it is
#   both the value-BoolOpRegion's merge block and the IfRegion's entry/
#   condition_block. _is_merge_if_condition (value-context + COMPARE_OP +
#   forward jump) fires and suppresses exception-3 (next-stmt-if) and the
#   guard marker -> the generator renders the if with the BoolOp expression as
#   the test (`if bufsize or 16384: return None`, copyfileobj real shape =
#   real R1: the function bails out on every call). Fix: when the precise
#   language-level predicate _value_merge_hosts_next_if ALSO holds, set the
#   marker (R36 dual-role path: "<BoolOp assignment> + If(tail test, ...)")
#   — the exception-2/3 path behavior is bit-for-bit unchanged (C3).
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
s = io.open(p, encoding='utf-8-sig').read()

a = """            _merge_boolop_guard_prefix_end = None
            if (_owning_boolop is not None
                    and (_is_merge_with_guard_clause or _is_merge_next_stmt_if)):"""
assert a in s, 'gate anchor'
r = """            _merge_boolop_guard_prefix_end = None
            # [v155-CONDLEAK] 例外2/3 之外的双角色补口（只增不破）：值上下文
            # BoolOp 的 merge_block 同时承载后继语句的 if 测试
            # （`bufsize = bufsize or 16*1024` + `if length == 0:` 编译进同一
            # 块——STORE 之后是下一条语句的 COMPARE 测试，copyfileobj 实形）。
            # _is_merge_if_condition（值上下文+COMPARE_OP+前向跳转）为真时压过
            # 例外3，guard_clause_prefix_end 不写下 → 生成器把 BoolOp 表达式
            # 当作 if 测试（`if bufsize or 16384: return None`——函数每次调用
            # 提前返回）。补口：例外3 的语言级精确判据
            # _value_merge_hosts_next_if 同时成立时同样写下标记（R36 双角色
            # 路径："<BoolOp 赋值语句> + If(块尾测试, ...)"）——例外2/3 既有
            # 路径逐位不变（C3）。
            if (_owning_boolop is not None
                    and (_is_merge_with_guard_clause or _is_merge_next_stmt_if
                         or (_is_merge_if_condition
                             and self._value_merge_hosts_next_if(block, _owning_boolop)))):"""
s = s.replace(a, r, 1)
io.open(p, 'w', encoding='utf-8-sig').write(s)
print('fix155 inserted')

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
