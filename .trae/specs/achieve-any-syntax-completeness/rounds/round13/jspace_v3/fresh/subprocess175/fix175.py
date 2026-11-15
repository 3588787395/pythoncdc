# -*- coding: utf-8 -*-
"""rr-v5r175 patch — subprocess SP1 CALLEX: with-item CALL_FUNCTION_EX.

`with Popen(*popenargs, **kwargs) as p:` 的上下文表达式在
region_analyzer._extract_with_items 里按 ctx 白名单收集指令；白名单缺
DICT_MERGE + CALL_FUNCTION_EX，父表达式因此少了终结调用，下游
ExpressionReconstructor 只见到「被调对象 + 实参装载 + 空 BUILD_MAP +
kwargs」，按栈顶残留值归约为 `with kwargs as p:`（重编后少 5 条指令）。
本补丁把这两条扩展调用/合并指令并入同一值生产链白名单。

Applies the r175 edit with count==1 anchors, utf-8-sig (BOM aware) +
newline preserving (LF-space edit, CRLF restore), py_compile validation
and full idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix175.py [--root <repo-root>] [--check]
"""
import argparse
import py_compile

REPO = 'F:/Downloads/pythoncdc-main'

_COMMENT = (
    "                # [r175 SP1 CALLEX] DICT_MERGE + CALL_FUNCTION_EX 同属上下文\n"
    "                # 表达式的值生产链：`with Popen(*popenargs, **kwargs) as p:`\n"
    "                # 的字节码为 LOAD_GLOBAL(Popen); LOAD_FAST(popenargs);\n"
    "                # BUILD_MAP 0; LOAD_FAST(kwargs); DICT_MERGE 1;\n"
    "                # CALL_FUNCTION_EX 1; BEFORE_WITH。旧白名单只收前四条，\n"
    "                # 父表达式因此缺少终结调用，ExpressionReconstructor 按栈顶\n"
    "                # 残留值归约为 `with kwargs as p:`（调用整体蒸发，重编后少\n"
    "                # LOAD_GLOBAL/BUILD_MAP/DICT_MERGE/CALL_FUNCTION_EX 共 5 条）。\n"
    "                # 依「表达式完整性」：合并与扩展调用是同一调用表达式的组成\n"
    "                # 部分，必须随值生产链一并收集，否则上下文表达式不可辨识。\n"
)

PATCHES = [
    ('core/cfg/region_analyzer.py', [
        # (1) 注释：说明 DICT_MERGE/CALL_FUNCTION_EX 为何属于 ctx 白名单
        ("                # 表达式的组成部分，必须随 CALL 一起收集。\n"
         "                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_FAST',\n",
         "                # 表达式的组成部分，必须随 CALL 一起收集。\n"
         + _COMMENT +
         "                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_FAST',\n"),
        # (2) 白名单：追加 DICT_MERGE + CALL_FUNCTION_EX
        ("                                   'KW_NAMES'):\n"
         "                    ctx_expr.append(instr)\n",
         "                                   'KW_NAMES',\n"
         "                                   'DICT_MERGE', 'CALL_FUNCTION_EX'):\n"
         "                    ctx_expr.append(instr)\n"),
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
