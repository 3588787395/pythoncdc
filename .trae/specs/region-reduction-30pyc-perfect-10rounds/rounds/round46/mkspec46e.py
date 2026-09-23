"""Build spec_r46e.json (candidate R46-E): _loop_postprocess must not fold the loop's
back-edge statements into an If arm whose tail only reaches the back edge by the
else-skipping unconditional forward jump.

usage: python -X utf8 mkspec46e.py
"""
import io
import json

P = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
OUT = r'D:/Temp/r46orch/spec_r46e.json'

src = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if '\r' in src else '\n'
u = src.replace(nl, '\n')
lines = u.split('\n')
GUARD = '                if _be_all_in_then and _be_then_region:'
idx = [i for i, l in enumerate(lines) if l == GUARD]
assert len(idx) == 1, idx
anchor = '\n'.join(lines[idx[0]:idx[0] + 2])
assert u.count(anchor) == 1, u.count(anchor)

ins = '''                # 区域归约算法原则 1（每块＝前导语句 + 唯一终止指令）+ 原则 4（父序列引用
                # 子区域入口后继续归约）：
                # 【识别条件】认领了回边块全部前驱的那个 then 臂，其臂内块是以「无条件前向
                # 跳转（JUMP_FORWARD/JUMP_ABSOLUTE）落到回边块」结束，且回边块本身不在该臂内。
                # 【危害形态】CPython 只在臂的源码文本已经结束时才发射这条跨越 else 的跳转，
                # 所以回边块是父序列（本 if 语句之后）的代码：把回边语句并进这个 If 节点的
                # body，等于把 if 之后的语句写进 if 体里，臂尾的 else-跳过跳转随之消失
                # （site-packages/fly/simtradding/flyAccount.pyc::<module>.TradeAccount.
                # init_connection 42/41 形）。
                # 【归约方式】命中时回边语句退回循环体序列尾部（现有 else 分支的
                # body_stmts.extend），不改区域归属、不新增语句。
                # 【只删不增】判据只读臂成员关系、回边块身份、终止指令操作码类别与前驱/后继
                # 关系，不读名字、常量、绝对偏移、指令条数、函数名。
                _r46_be_esc = False
                if _be_then_region is not None and _be_block is not None:
                    _r46_arm = set(getattr(_be_then_region, 'then_blocks', None) or [])
                    for _r46_p in (_be_block.predecessors or []):
                        _r46_last = _r46_p.get_last_instruction()
                        if (_r46_p in _r46_arm and _be_block not in _r46_arm
                                and _r46_last is not None
                                and _r46_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                and _r46_last.argval == _be_block.start_offset):
                            _r46_be_esc = True
                            break
                if _be_all_in_then and _be_then_region and not _r46_be_esc:
                    _be_placed = False'''
repl = ins
assert u.count(repl) == 0, 'patch already applied'
json.dump({'file': 'core/cfg/region_ast_generator.py', 'anchor': anchor, 'repl': repl,
           'count': 1}, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('anchor=%r(%d lines) insert=%d lines' % (anchor.split(chr(10))[0][:40], len(anchor.split('\n')),
                                               len(repl.split('\n'))))
