# -*- coding: utf-8 -*-
"""rr-v5r176 patch — cookiejar CJ4: `_normalized_cookie_tuples` (101/105).

单文件 4 anchor（region_analyzer.py），只增不破：

A. `_v171_iter_exit_merge` 的 continue 臂判据补「NCPD 塌陷到循环出口」形态：
   `if c: continue` 之后仍有同层兄弟语句时 merge 落在循环块集之外，而对侧
   else_succ 仍在循环块集内——后者才是 if 之后的同层顺序语句入口。旧判据只认
   `merge is header`，于是 merge 停在循环出口，else 臂把余下兄弟语句全部吞入
   （cookie `if k in standard: continue` / `if max_age_set: continue` 链根因）。
B. `_check_elif_chain` 候选 elif 臂以 continue 离开本轮迭代时，inner_merge 归位
   到 inner_else_succ（与 A 同源），使 final_else 不再越过同层兄弟语句继续收集。
C. `_v171_iter_exit_merge` 的 break 臂「裸臂门」补一个结构豁免：break 落点恰为
   NCPD 的 merge（循环出口，落在循环块集外）且对侧 else_succ 仍在循环块集内时，
   带语句的 break 臂同样是 if 的迭代出口（`if v is None: ...; break` 吞掉后续）。

Applies the r176 edit with count==1 anchors, utf-8-sig (BOM aware) +
newline preserving (LF-space edit, CRLF restore), py_compile validation
and full idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix176.py [--root <repo-root>] [--check]
"""
import argparse
import py_compile

REPO = 'F:/Downloads/pythoncdc-main'

PATCHES = [
    ('core/cfg/region_analyzer.py', [
        # (1)
        ('          (a) merge 落在循环边界——continue 臂要求 merge 就是本 if 所在\n              **最内层循环**的 header_block；break 臂要求 merge 不在该循环\n              的块集内（= 循环出口）。merge 落在循环体内（真实 else 臂的\n              常规 if/else、`if a: continue / else: X` 之类）一律不认领。\n',
         '          (a) merge 落在循环边界——continue 臂要求 merge 是循环头，或 merge\n              在循环块集之外且对侧入口 else_succ 仍在循环块集内（循环体尾部\n              的 `if c: continue` 之后仍有同层兄弟语句时，NCPD 塌陷到循环\n              出口块，对侧入口才是 if 之后的同层顺序语句）；break 臂要求\n              merge 不在该循环的块集内（= 循环出口）且对侧入口仍在循环块\n              集内。merge 落在循环体内（真实 else 臂的\n              常规 if/else、`if a: continue / else: X` 之类）一律不认领。\n'),
        # (2)
        ("        _is_continue = (_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')\n                        and _last.argval == getattr(_hdr, 'start_offset', None)\n                        and merge is _hdr)\n",
         "        # [r176-ITER-EXIT-2] continue 臂的 merge 除「就是循环头」外还有\n        # 「NCPD 塌陷到循环出口」形态：循环体尾部/嵌套循环里的 `if c: continue`\n        # 之后仍有同层兄弟语句时，NCPD(then_succ, else_succ) 给出的是循环出口\n        # 块（落在循环块集之外），而对侧 else_succ 仍在循环块集内——后者才是\n        # if 之后的同层顺序语句入口。判据只读块集身份（原则 2/4），与既有\n        # merge is header 判据取并集；不命中返回 None（C3），调用方行为不变。\n        _is_continue = (_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')\n                        and _last.argval == getattr(_hdr, 'start_offset', None)\n                        and (merge is _hdr\n                             or (merge not in _loop.blocks\n                                 and else_succ in _loop.blocks)))\n"),
        # (3)
        ('                if any(_i.opname in _v171_arm_stmt\n                       for _i in then_succ.instructions):\n                    _is_break = False\n',
         "                if any(_i.opname in _v171_arm_stmt\n                       for _i in then_succ.instructions):\n                    # [r176-BREAK-EXIT] 带语句的 break 臂在「嵌套循环尾部 +\n                    # if 之后仍有同层兄弟语句」形态下同样是 if 的迭代出口：\n                    # break 落点恰为 NCPD 求得的 merge（循环出口块，落在循环块\n                    # 集之外），而对侧 else_succ 仍在循环块集内。两臂不在本作用\n                    # 域向前汇合，merge 必须归位到 else_succ，否则 if 之后的同层\n                    # 兄弟语句被吸进臂内（cookiejar _normalized_cookie_tuples 的\n                    # `if v is None: _debug(...); bad_cookie = True; break` 吞掉\n                    # `v = v.lower()` 之后的整段 if 链）。\n                    # 判据只读块末跳转落点与块集身份，与 continue 侧 (a) 同源；\n                    # tarfile TarFile.next 的 `if tarinfo is not None: ... else:\n                    # ...` 形态（对侧入口不在同一嵌套循环块集内）不命中，保持\n                    # 既有行为（458 电池实测零变化）。\n                    _v176_break_exit = (\n                        _last is not None\n                        and getattr(_last, 'argval', None) == getattr(merge, 'start_offset', None)\n                        and merge not in _loop.blocks\n                        and else_succ in _loop.blocks)\n                    if not _v176_break_exit:\n                        _is_break = False\n"),
        # (4)
        ('            # 区域归约算法原则 2（每块唯一归属）+ 原则 4（归约顺序）：\n            # 当内层 elif 的 else 分支入口等于外层 merge 时，inner_merge 应设为\n',
         '            # [r176-ITER-ELIF] 候选 elif 臂无条件离开本轮迭代（continue）时，两臂\n            # 不在本作用域向前汇合：NCPD 只能给出更晚的循环边界（循环头或循环\n            # 出口），内层 inner_merge 与外层链 merge_ 可能同时塌陷到同一个循环\n            # 边界块。此时 inner_else_succ 才是 if 之后的同层顺序语句入口；若仍按\n            # NCPD 收集，inner_else_blocks 会越过它把循环体余下的同层兄弟语句全部\n            # 吞进 final_else（cookiejar CookieJar._normalized_cookie_tuples 的\n            # `if k == "expires": if max_age_set: continue; if v is None: ...` 之后\n            # 整段 if 链被并成 else 体）。\n            # 判据（I.4 结构事实，与 _v171_iter_exit_merge 的 continue 侧同源）：\n            #   ① inner_merge 落在候选臂所在循环的块集之外（循环边界）；\n            #   ② inner_else_succ 仍在该循环块集内（同层顺序语句）；\n            #   ③ 候选臂末指令无条件回到循环头（JUMP_BACKWARD→header，continue）。\n            # 命中 → inner_merge = inner_else_succ，使 inner_else_blocks 为空\n            # （entry==merge，无 final_else）；随后 d2 判据（inner_merge≠merge_）\n            # 对该形态弃权，交由 _v171_iter_exit_merge 把 merge 归位到 else_succ。\n            # break 臂不在此列：链尾 `elif b: break` 的芯形由既有 break 判据与\n            # elif 守卫处置（r110 pc1/pc2 等电池案）。\n            if (inner_merge is not None and inner_else_succ is not None\n                    and inner_then_succ is not None):\n                _ie_loop = self._find_enclosing_loop(first_else)\n                if (_ie_loop is not None\n                        and inner_merge not in _ie_loop.blocks\n                        and inner_else_succ in _ie_loop.blocks):\n                    _ie_hdr = getattr(_ie_loop, \'header_block\', None)\n                    _ie_last = inner_then_succ.get_last_instruction()\n                    _ie_continue = (_ie_hdr is not None\n                                    and _ie_last is not None\n                                    and _ie_last.opname in (\'JUMP_BACKWARD\',\n                                                            \'JUMP_BACKWARD_NO_INTERRUPT\')\n                                    and _ie_last.argval == _ie_hdr.start_offset)\n                    if _ie_continue:\n                        inner_merge = inner_else_succ\n            # 区域归约算法原则 2（每块唯一归属）+ 原则 4（归约顺序）：\n            # 当内层 elif 的 else 分支入口等于外层 merge 时，inner_merge 应设为\n'),
    ]),
]



def _apply(path, pairs, check=False):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    crlf = '\r\n' in text
    norm = text.replace('\r\n', '\n')
    done = 0
    for old, new in pairs:
        c_old, c_new = norm.count(old), norm.count(new)
        if c_old == 1 and c_new >= 1 and old in new:
            # 插入型锚点：old 文本保留在 new 内部 ⇒ 已应用（幂等）
            continue
        if c_old == 1:
            norm = norm.replace(old, new, 1)
            done += 1
        elif c_old == 0 and c_new >= 1:
            continue
        else:
            raise SystemExit('ANCHOR-FAIL %s old=%d new=%d\n%r'
                             % (path, c_old, c_new, old[:200]))
    out = norm.replace('\n', '\r\n') if crlf else norm
    data = out.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    if not check:
        open(path, 'wb').write(data)
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=REPO)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    total = 0
    for rel, pairs in PATCHES:
        p = args.root.rstrip('/') + '/' + rel
        n = _apply(p, pairs, check=args.check)
        total += n
        print('%s: %d hunk(s) %s' % (rel, n, 'already-applied'
                                     if n == 0 else 'patched'))
    for rel, _ in PATCHES:
        p = args.root.rstrip('/') + '/' + rel
        py_compile.compile(p, doraise=True)
    print('py_compile OK; total patched hunks = %d' % total)


if __name__ == '__main__':
    main()
