# -*- coding: utf-8 -*-
"""Build the Round 51 candidate arm B: worktree core + R51-A + R51-B.

Byte-level, CRLF-preserving, anchor-uniqueness asserted.
usage: python -X utf8 mk_cand51b.py <dst-mirror>
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
DST = sys.argv[1]
SRC = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

ANCHOR = ("        elif_orelse = nested_elif_stmts if nested_elif_stmts else "
          "(final_else_stmts if final_else_stmts else [])\n")

BODY_A = '''        # [R51-A 同层判据] 区域归约算法原则 1（块 = 前导语句 + 恰好一个终结子）＋
        # 原则 2（每块唯一归属且归属者必须发射）：链尾 else 臂的全部块都不含语句
        # （只剩噪声指令，或噪声 + 一条无条件跳转）时，这块的存在本身即源码里有
        # 一个空 else 子句的证据——没有 else 子句时 CPython 把最后一个 elif 测试的
        # 落空目标直接指向汇合点，不会留下需要跳过去的中间块。臂体发射为空 ⇒
        # orelse 被丢弃 ⇒ 前一臂末的出口跳转随之折叠，re-compile 恰少一条
        # JUMP_FORWARD。补 `else: pass`（重编译即该臂块本身）并由本链认领这些块，
        # 免得它们再被当作孤立边界 NOP 摊平成兄弟语句。判据全为结构事实（块同一性、
        # 终结子类别、前驱/后继关系），不读名字、常量、绝对偏移与指令数。
        _r51_arm = region.elif_final_else
        _r51_merge = region.merge_block
        _r51_test = (region.elif_conditions[-1] if region.elif_conditions
                     else region.condition_block)
        if (_r51_arm and not final_else_stmts
                and not (len(nested_elif_stmts or []) == 1
                         and (nested_elif_stmts[0].get('orelse') or []))
                and _r51_merge is not None and _r51_test is not None
                and _r51_arm[0] in (_r51_test.successors or [])):
            _r51_ok = all(
                not [i for i in _r51_b.instructions
                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG',
                                         'PUSH_NULL', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')]
                and _r51_b is not _r51_merge
                for _r51_b in _r51_arm)
        else:
            _r51_ok = False
        if _r51_ok:
            _r51_last = _r51_arm[-1]
            _r51_exit = _r51_last.get_last_instruction()
            _r51_reaches = (_r51_exit is not None
                            and _r51_exit.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                            and _r51_exit.argval == _r51_merge.start_offset)
            if not _r51_reaches:
                _r51_reaches = _r51_merge in (_r51_last.successors or [])
            _r51_ok = _r51_reaches
        if _r51_ok:
            for _r51_r in self.regions:
                if _r51_r.entry in _r51_arm:
                    _r51_ok = False
                    break
        if _r51_ok:
            if len(nested_elif_stmts or []) == 1 and not (nested_elif_stmts[0].get('orelse') or []):
                nested_elif_stmts[0]['orelse'] = [{'type': 'Pass'}]
            else:
                final_else_stmts = [{'type': 'Pass'}]
            for _r51_b in _r51_arm:
                self.generated_blocks.add(_r51_b)
'''

BODY_B = '''        # [R51-B 同层判据] 区域归约算法原则 2（每块唯一归属且归属者必须发射）＋
        # 原则 4（父区域以子区域入口引用子区域，而非其全部块）：链的最后一个测试
        # 若把落空边指向一个「只有噪声指令、唯一后继是链汇合点」的块，源码里就
        # 存在一个空的 else 子句（无 else 时 CPython 让落空边直接落到汇合点，不留
        # 中间块）。分析侧在 _build_elif_region 把这种平凡臂擦除（inner_else_blocks
        # 全为 _is_trivial_block ⇒ 擦成 IF_THEN），该块因此既不属于本链也不属于
        # 任何子区域，只被父区域按孤立边界 NOP 摊平成兄弟语句 `while False: pass`；
        # 兄弟语句紧跟前一臂体，编译时不再需要越过空臂的跳转 ⇒ 整函数恰少一条
        # JUMP_FORWARD（repro: trade_live_broker 的 get_crdt_stock_info/
        # get_crdt_target_stockinfo/get_crdt_enslosecu_stock_info 各差 1 条）。
        # 修法＝把该块按区域归属收回本链，发射 `else: pass` 并标记已生成。
        # 判据：①本链此刻没有任何 orelse 内容 ②链有汇合块 ③候选块非汇合块、
        # 有前驱、全部指令皆噪声（NOP/CACHE/RESUME/EXTENDED_ARG/PUSH_NULL，连跳转
        # 都没有 ⇒ 与 R51-A 的「臂体自身带出口跳转」互斥）、后继集恰为 {merge}
        # ④每个前驱要么是本链的块、要么其终结子是指向该块的条件跳转，且至少一个
        # 前驱属后者（这条边就是源码 if/elif 的落空边）⑤该块不是任何区域的入口、
        # 尚未被发射 ⑥满足①..⑤者唯一。全部是块同一性／终结子类别／前驱后继关系，
        # 不读名字、常量、绝对偏移与指令数。
        _r51b_merge = region.merge_block
        _r51b_container = None
        if nested_elif_stmts and len(nested_elif_stmts) == 1:
            if not (nested_elif_stmts[0].get('orelse') or []):
                _r51b_container = nested_elif_stmts[0]
        elif not nested_elif_stmts and not final_else_stmts:
            _r51b_container = 'flat'
        _r51b_pad = None
        if _r51b_container is not None and _r51b_merge is not None:
            _r51b_rbs = set(id(_r51b_x) for _r51b_x in region.blocks)
            _r51b_cands = []
            for _r51b_b in self.cfg.blocks.values():
                if _r51b_b is _r51b_merge or not _r51b_b.predecessors:
                    continue
                if [i for i in _r51b_b.instructions
                        if i.opname not in ('RESUME', 'NOP', 'CACHE',
                                            'EXTENDED_ARG', 'PUSH_NULL')]:
                    continue
                if set(_r51b_b.successors or set()) != {_r51b_merge}:
                    continue
                if _r51b_b in self.generated_blocks:
                    continue
                if any(_r51b_r.entry is _r51b_b for _r51b_r in self.regions):
                    continue
                _r51b_false_edge = False
                _r51b_preds_ok = True
                for _r51b_p in _r51b_b.predecessors:
                    _r51b_pt = _r51b_p.get_last_instruction()
                    if (_r51b_pt is not None and 'JUMP' in _r51b_pt.opname
                            and _r51b_pt.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                        'JUMP_BACKWARD',
                                                        'JUMP_BACKWARD_NO_INTERRUPT')
                            and _r51b_pt.argval == _r51b_b.start_offset):
                        _r51b_false_edge = True
                    elif id(_r51b_p) not in _r51b_rbs:
                        _r51b_preds_ok = False
                        break
                if _r51b_preds_ok and _r51b_false_edge:
                    _r51b_cands.append(_r51b_b)
            if len(_r51b_cands) == 1:
                _r51b_pad = _r51b_cands[0]
        if _r51b_pad is not None:
            if _r51b_container == 'flat':
                final_else_stmts = [{'type': 'Pass'}]
            else:
                _r51b_container['orelse'] = [{'type': 'Pass'}]
            self.generated_blocks.add(_r51b_pad)
'''

NEW = (BODY_A + BODY_B + ANCHOR).replace('\n', '\r\n')
ANCHOR_B = ANCHOR.replace('\n', '\r\n').encode('utf-8')
NEW_B = NEW.encode('utf-8')

if os.path.exists(DST):
    shutil.rmtree(DST)
os.makedirs(DST)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(DST, 'core'),
                ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(os.path.join(REPO, 'pycdc.py'), os.path.join(DST, 'pycdc.py'))
for _root, _dirs, _files in os.walk(DST):
    assert '__pycache__' not in _dirs, _root
dst_f = os.path.join(DST, 'core', 'cfg', 'region_ast_generator.py')
data = open(dst_f, 'rb').read()
assert data == open(SRC, 'rb').read(), 'mirror bytes differ from worktree'
assert data.count(ANCHOR_B) == 1, 'anchor count = %d' % data.count(ANCHOR_B)
assert data.count(b'\n') == data.count(b'\r\n'), 'mixed line endings'
assert data.startswith(b'\xef\xbb\xbf'), 'BOM lost'
patched = data.replace(ANCHOR_B, NEW_B)
assert patched.count(b'\n') == patched.count(b'\r\n'), 'patch introduced a bare LF'
assert patched.startswith(b'\xef\xbb\xbf'), 'BOM lost after patch'
compile(patched, dst_f, 'exec')
open(dst_f, 'wb').write(patched)
print('candidate C built: %s (+%d lines, %d -> %d bytes)' % (
    DST, NEW_B.count(b'\n') - ANCHOR_B.count(b'\n'), len(data), len(patched)))
