"""R35 candidate builder (R21-27d): a JoinedStr prefix part is a literal or a consumed value, nothing else.

Last of the four co-requisite hunks for etf_purchase_redemption (after build_cand_r35_R21-27.py,
build_cand_r35b_R21-27_chain.py, build_cand_r35c_R21-27_callee_skip.py). Measured state before this one:
the unit is `delta=0 / 1 hunk`, the only difference being the literal `' 数量：'` rendered as
`' 数量：order'` — the per-`LOAD_*` fallback pushed the ternary condition's own operand name (`LOAD_FAST
order`, not consumed by any FORMAT_VALUE) into JoinedStr.values, and the renderer folds such a non-dict/
Name part into the literal text.

Rule: after the prefix is assembled (before the chain's own FormattedValue is appended), keep only parts
that are `Constant` (literal) or `FormattedValue` (consumed by a FORMAT_VALUE). A bare Name/str/Call part
has no FORMAT_VALUE consuming it inside this JoinedStr, so by「每块唯一归属」it belongs to the following
condition expression, not to this string.

usage: python -X utf8 build_cand_r35d_R21-27_part_kind_filter.py <generator-file>
"""
import hashlib
import py_compile
import sys

ANCHOR = [
    "                # ternary是最后一个FormattedValue（merge_block的FORMAT_VALUE格式化它）",
    "                _r65_chain_part = {",
]

NEW = [
    "                # [R21-27d] 前缀片段只保留两类：字面 Constant、或已被某条 FORMAT_VALUE 消费的",
    "                # FormattedValue。逐条 LOAD_* 回退会把三元条件自身的操作数名（实测 ' 数量：'",
    "                # 之后多出的 'order'，即未被消费的 LOAD_FAST order）压进 values，渲染端把它折",
    "                # 进字面量。依「每块唯一归属」，没有被本串 FORMAT_VALUE 消费的裸 Name/str/Call",
    "                # 片段属于后续条件表达式，不属于这个 JoinedStr。",
    "                fstring_parts = [_r27d_p for _r27d_p in fstring_parts",
    "                                 if isinstance(_r27d_p, dict)",
    "                                 and _r27d_p.get('type') in ('Constant',",
    "                                                              'FormattedValue')]",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')
    ab = [x.encode('utf-8') for x in ANCHOR]
    hits = [n for n in range(len(lines) - len(ab) + 1) if lines[n:n + len(ab)] == ab]
    assert len(hits) == 1, 'anchor hits %d' % len(hits)
    n = hits[0]
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n:]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('inserted %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
