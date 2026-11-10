# fix152c.py: [v152-LATCH] _r2164_purge_latch_legs leg-target refinement
#   The latch-leg criterion (no STORE + conditional jump + loads ⊆ condition vars)
#   also matches an ordinary body `if <same-var>:` statement (difflib.HtmlDiff.
#   _line_wrapper: `while fromlist or tolist:` body `if tolist: ... else: ...`
#   test block absorbed into the condition BoolOpRegion -> if/else collapses,
#   pop + else-assign emitted flat = real R1). Refinement: a latch leg's
#   conditional jump target must reach the loop re-entry (header) or the loop
#   exit (condition merge) — directly, or through leg-shaped continuation
#   blocks (no STORE, conditional jump) within a small bound (mixed-chain latch
#   legs jump forward to the next latch leg). Body if-arms carry STOREs and
#   fail the walk.
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
s = io.open(p, encoding='utf-8-sig').read()

anchor = """        LOAD_OPS = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
        STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                     'STORE_ATTR', 'STORE_SUBSCR')
        JUMP_OPS = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'NOP')
        to_purge = []"""
assert anchor in s, 'latch anchor missing'
repl = """        LOAD_OPS = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
        STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                     'STORE_ATTR', 'STORE_SUBSCR')
        JUMP_OPS = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'NOP')
        # [v152-LATCH] 闩锁腿目标精化（只增不破）：真闩锁腿的条件跳转目标必
        # 须到达循环再入点（header）或循环出口（条件链 merge）——直接命中，
        # 或经腿形续块（无 STORE、条件跳转，混合链闩锁成员前向跳下一闩锁
        # 腿）有界走查到达。体内普通 `if <同变量>:` 语句（difflib.HtmlDiff.
        # _line_wrapper 实形：`while fromlist or tolist:` 体内 `if tolist:`
        # 测试块 loads={tolist} ⊆ 条件变量集、无 STORE、条件跳转——既有判据
        # 无法区分再测试腿）其假边目标是体内 if 臂块（带 STORE），走查失败
        # ⇒ 不再被吸进条件 BoolOpRegion，交还 IfRegion 语句级归约（if/else
        # 不再坍塌）。
        _merge_latch = getattr(boolop_region, 'merge_block', None)

        def _v152_latch_leg_target_ok(_li):
            _tgt = self.cfg.get_block_by_offset(_li.argval) if _li.argval is not None else None
            _seen = set()
            _cur = _tgt
            for _ in range(6):
                if _cur is None or _cur.start_offset in _seen:
                    return False
                _seen.add(_cur.start_offset)
                if _cur is hdr or (_merge_latch is not None and _cur is _merge_latch):
                    return True
                _cur_eff = [i for i in _cur.instructions if i.opname not in NOISE_OPS]
                if any(i.opname in STORE_OPS for i in _cur_eff):
                    return False
                _cur_li = _cur.get_last_instruction()
                if (_cur_li is None or _cur_li.argval is None
                        or _cur_li.opname not in (FORWARD_CONDITIONAL_JUMP_OPS
                                                  | BACKWARD_CONDITIONAL_JUMP_OPS)):
                    return False
                _cur = self.cfg.get_block_by_offset(_cur_li.argval)
            return False

        to_purge = []"""
s = s.replace(anchor, repl, 1)

anchor2 = """            is_leg = (li is not None
                      and li.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                      and bool(loads) and loads <= cond_vars)"""
assert anchor2 in s, 'is_leg anchor missing'
repl2 = """            is_leg = (li is not None
                      and li.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                      and bool(loads) and loads <= cond_vars
                      and _v152_latch_leg_target_ok(li))"""
s = s.replace(anchor2, repl2, 1)

io.open(p, 'w', encoding='utf-8-sig').write(s)
print('fix C inserted')

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
