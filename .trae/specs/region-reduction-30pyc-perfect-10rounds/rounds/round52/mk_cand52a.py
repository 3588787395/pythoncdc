# -*- coding: utf-8 -*-
"""Round 52 candidate R52-A: per-arm same-layer ownership test in R51-A's entry conjunct.

Writes spec_r52a.json (the landing artefact). The mirror arm is built by replaying that
spec with r52a.py build, so what is measured is byte-for-byte what would be landed.
"""
import io
import json

P = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
raw = io.open(P, 'rb').read()
src = raw.decode('utf-8-sig')
NL = '\r\n' if src.count('\r') else '\n'
u = src.replace(NL, '\n')

CRLF = chr(13) + chr(10)


def j(lines):
    """Join source lines with an explicit CRLF marker (normalised to LF for the spec)."""
    return CRLF.join(lines) + CRLF


ANCHOR = j([
    '        if _r51_ok:',
    '            for _r51_r in self.regions:',
    '                if _r51_r.entry in _r51_arm:',
    '                    _r51_ok = False',
    '                    break',
])

GUARD = j([
    '                if _r51_r.entry in _r51_arm:',
    '                    # [R52-A 同层归属精化] 区域归约算法原则 2（每块唯一归属且归属者必须发射）＋原则 3',
    '                    # （嵌套即抽象节点）：`该块是某区域的 entry` 只有在该区域**真的拥有这块**时',
    '                    # 才构成竞争归属。分析器为尚未归约的块留下的退化容器区域（类型恰为 Region、',
    '                    # region_type=BASIC、blocks 只含 entry 自己一块）不是抽象节点，而是占位记录；',
    '                    # 当这块的 `block_to_region` 归属正是本链时，把它当竞争者会永远否决 R51-A',
    '                    # （复现体 r51a_04 / r51b_06 的垫块即此形状：单块、终结子是一条 JUMP_FORWARD、',
    '                    # 且被链自己收在 `elif_final_else` 里）。真竞争者——任何结构区域（IfRegion /',
    '                    # LoopRegion / TryExceptRegion / …）或以该块为入口、块集更大的区域——仍然否决，',
    '                    # 因此本精化不放宽任何跨区域/跨层次的约束，只排除「自己占的坑」这一种假阳性。',
    '                    # 判据全是块同一性与区域同一性，不读名字、常量、绝对偏移与指令数。',
    '                    if (type(_r51_r) is Region',
    '                            and _r51_r.region_type is RegionType.BASIC',
    '                            and all(_r52_x is _r51_r.entry for _r52_x in _r51_r.blocks)',
    '                            and self.region_analyzer.block_to_region.get(_r51_r.entry)',
    '                            is region):',
    '                        continue',
    '                    _r51_ok = False',
    '                    break',
])

REPL = j([
    '        if _r51_ok:',
    '            for _r51_r in self.regions:',
]) + GUARD

anchor_u = ANCHOR.replace(CRLF, chr(10))
repl_u = REPL.replace(CRLF, chr(10))
n = u.count(anchor_u)
assert n == 1, 'anchor occurrences=%d' % n
patched = u.replace(anchor_u, repl_u)
assert patched != u
inserted = repl_u.count(chr(10)) - anchor_u.count(chr(10))

spec = {'file': 'core/cfg/region_ast_generator.py',
        'anchor': anchor_u,
        'repl': repl_u,
        'inserted_lines': inserted}
io.open('D:/Temp/r52gate/spec_r52a.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('spec written; inserted_lines=%d; anchor ok' % inserted)
