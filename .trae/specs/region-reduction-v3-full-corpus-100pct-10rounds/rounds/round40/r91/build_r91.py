"""R91 byte-level patcher: UTF-8 BOM + all-CRLF files, split(b'\\r\\n'), unique anchors.

usage: python -X utf8 build_r91.py <patchname>
Every write is verified: b'\\r\\r\\n' count == 0, py_compile passes, sha16 recorded.
"""
import hashlib
import py_compile
import shutil
import sys

ROOT = 'D:/Temp/r91'
AN = 'core/cfg/region_analyzer.py'
GEN = 'core/cfg/region_ast_generator.py'

BASE = {}   # pristine copies, taken from the mirror at first run


def load(path):
    key = path
    if key not in BASE:
        BASE[key] = open(ROOT + '/' + path, 'rb').read()
    return BASE[key]


def lines_of(raw):
    assert not raw.startswith(b'\r')
    return raw.split(b'\r\n')


def apply(path, edits):
    """edits: list of (anchor_lines, new_lines, mode) mode in {'after','before','replace'}"""
    raw = load(path)
    bom = raw.startswith(b'\xef\xbb\xbf')
    body = raw[3:] if bom else raw
    ls = lines_of(body)
    for anchor, new, mode in edits:
        a = [l.encode('utf-8') for l in anchor]
        hits = []
        for i in range(len(ls) - len(a) + 1):
            if ls[i:i + len(a)] == a:
                hits.append(i)
        if len(hits) != 1:
            raise SystemExit('ANCHOR NOT UNIQUE (%d hits) in %s:\n%s' %
                             (len(hits), path, '\n'.join(anchor)))
        i = hits[0]
        nl = [l.encode('utf-8') for l in new]
        if mode == 'replace':
            ls[i:i + len(a)] = nl
        elif mode == 'after':
            ls[i + len(a):i + len(a)] = nl
        else:
            ls[i:i] = nl
    out = b'\xef\xbb\xbf' + b'\r\n'.join(ls) if bom else b'\r\n'.join(ls)
    assert out.count(b'\r\r\n') == 0, 'CR-CR-LF introduced'
    assert (out.count(b'\n') - out.count(b'\r\n')) == 0, 'bare LF introduced'
    open(ROOT + '/' + path, 'wb').write(out)
    tmp = ROOT + '/out/_pc_%s.py' % hashlib.md5(path.encode()).hexdigest()[:8]
    shutil.copyfile(ROOT + '/' + path, tmp)
    py_compile.compile(tmp, doraise=True)
    print('patched %s sha16=%s bytes=%d' % (path, hashlib.sha256(out).hexdigest()[:16], len(out)))


def restore():
    for p in (AN, GEN):
        if p in BASE:
            open(ROOT + '/' + p, 'wb').write(BASE[p])


# ─── patch A: analyzer mixed or-prefix / and-group chain detector ───────────
A_METHOD = [
    "    def _detect_while_condition_or_prefix_and_group_chain(self, cond_block: BasicBlock,",
    "                                                            loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:",
    "        \"\"\"[R21-62] 检测「or 头 run + and 尾组」混合 while 条件链（闩锁复制形态）。",
    "",
    "        [识别条件] CPython 3.11 把 ``while A or B or (C and not D):`` 编译为单向",
    "        fall-through 短路边：or run 非末成员 POP_JUMP_FORWARD_IF_TRUE → 循环体入口 T；",
    "        and 组假边 POP_JUMP_FORWARD_IF_FALSE 越过余下全部成员直达循环出口 F；末成员",
    "        fall-through 进体。链成员的条件跳转目标因此必然收敛到【两个】目标类",
    "        （真出口 T / 假出口 F），与均匀链的 R07 all_same_target（单目标）结构性",
    "        互斥——既有前向 walk 在第二个目标类出现处拒绝整链，后向 walk 只拿到链首",
    "        一元，故 ``while`` 测试被截断为第一操作数。与 [R7-B45] 的「and 头前缀 +",
    "        括号化 or 尾 run」互为镜像：该形态假边由 and 头发出、真边由 or 尾发出。",
    "        [R21-62] 的第二判据是本形态独有的【闩锁复制签名】：CPython 在回边处整体",
    "        重发同一条件链，体首块（= T）尾部逐位复制链首操作数的求值序列，且闩锁",
    "        侧存在 ≥2 条以条件回跳落到同一 T 的独立后向边（实测 _sync_worker：",
    "        @704/@876/@1056 三条 POP_JUMP_BACKWARD_IF_* → @704，而 region 只声明",
    "        back_edge_block=@704 一条）。两个判据同时成立才接管，单条后向边形态",
    "        （普通 continue 闩锁）不命中。",
    "        [归约方式] 自 condition_block 沿 fall-through 单向行走：逐成员校验其条件",
    "        跳转目标经连接块（单条无条件跳转 / 纯噪声块）归一后 ∈ {T, F}，F 唯一且",
    "        在体语义集合之外；成员块不得含 STORE（海象 COPY(1)+STORE 除外），不得含",
    "        异常帧指令；末成员 fall-through 归一后必须命中 T。链 = [(成员,op)…]，",
    "        op 与既有前向 walk 逐字同规则（'FALSE'→'and'，否则 'or'）。",
    "        [AST 映射] 交 Step 5 调用方经 _create_boolop_region_from_chain 归约为",
    "        LoopRegion 条件子区域；闩锁复制块由生成侧抑制（每块唯一归属）。",
    "        [C1] 只读块末 opcode 族、后继身份、支配式目标归一与循环自身块集；",
    "        [C2] 不认领/不登记任何块，任一校验失败即返回 None，调用方回退既有 walk，",
    "        行为与未命中逐位一致；[C3] 无状态、无副作用、单出口、无名字/常量/偏移。",
    "        \"\"\"",
    "        _CONNECTION_OPS = ('JUMP_FORWARD', 'JUMP_ABSOLUTE')",
    "        _STATEMENT_END_OPS = ('POP_TOP', 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',",
    "                              'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',",
    "                              'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',",
    "                              'YIELD_VALUE', 'BREAK_LOOP')",
    "        _EXC_FRAME_OPS = ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',",
    "                          'PREP_RERAISE_STAR', 'WITH_EXCEPT_START', 'RERAISE')",
    "        last = cond_block.get_last_instruction()",
    "        if (last is None or last.argval is None",
    "                or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS",
    "                or 'TRUE' not in last.opname):",
    "            return None",
    "        _body_sem = set(loop.body_blocks or [])",
    "        for _attr in ('header_block', 'entry', 'condition_block', 'back_edge_block'):",
    "            _bv = getattr(loop, _attr, None)",
    "            if _bv is not None:",
    "                _body_sem.add(_bv)",
    "",
    "        def _norm(b):",
    "            for _ in range(8):",
    "                if b is None:",
    "                    return None",
    "                eff = [i for i in b.instructions if i.opname not in NOISE_OPS]",
    "                if (len(eff) == 1 and eff[0].opname in _CONNECTION_OPS",
    "                        and eff[0].argval is not None):",
    "                    b = self.cfg.get_block_by_offset(eff[0].argval)",
    "                    continue",
    "                if not eff:",
    "                    succs = [s for s in b.successors]",
    "                    if len(succs) == 1:",
    "                        b = succs[0]",
    "                        continue",
    "                return b",
    "            return b",
    "",
    "        def _fallthrough(b, jt_off):",
    "            for s in b.conditional_successors:",
    "                if s.start_offset != jt_off:",
    "                    return s",
    "            return None",
    "",
    "        true_tgt = _norm(self.cfg.get_block_by_offset(last.argval))",
    "        if true_tgt is None or (true_tgt is not loop.header_block",
    "                                and true_tgt not in _body_sem):",
    "            return None",
    "        false_tgt = None",
    "        chain: List[Tuple[BasicBlock, str]] = []",
    "        cur = cond_block",
    "        seen = set()",
    "        while cur is not None and cur not in seen:",
    "            seen.add(cur)",
    "            cl = cur.get_last_instruction()",
    "            if (cl is None or cl.argval is None",
    "                    or cl.opname not in FORWARD_CONDITIONAL_JUMP_OPS):",
    "                return None",
    "            if any(i.opname in _EXC_FRAME_OPS for i in cur.instructions):",
    "                return None",
    "            _eff = [i for i in cur.instructions if i.opname not in NOISE_OPS]",
    "            _nonjmp = _eff[:-1] if _eff and _eff[-1] is cl else _eff",
    "            _si = -1",
    "            for _k, _i in enumerate(_nonjmp):",
    "                if _i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',",
    "                                  'STORE_ATTR', 'STORE_SUBSCR'):",
    "                    _prev = _nonjmp[_k - 1] if _k > 0 else None",
    "                    if not (_prev is not None and _prev.opname == 'COPY' and _prev.arg == 1):",
    "                        return None",
    "                    _si = _k",
    "            jt = _norm(self.cfg.get_block_by_offset(cl.argval))",
    "            ft = _norm(_fallthrough(cur, cl.argval))",
    "            if jt is None or ft is None:",
    "                return None",
    "            if jt is true_tgt or jt in _body_sem:",
    "                _op = 'or' if 'TRUE' in cl.opname else 'and'",
    "                if 'FALSE' in cl.opname:",
    "                    return None",
    "                chain.append((cur, _op))",
    "                if ft is true_tgt or ft in _body_sem:",
    "                    break",
    "                cur = _fallthrough(cur, cl.argval)",
    "                continue",
    "            if false_tgt is None:",
    "                false_tgt = jt",
    "            elif jt is not false_tgt:",
    "                return None",
    "            if 'FALSE' in cl.opname:",
    "                chain.append((cur, 'and'))",
    "                cur = _fallthrough(cur, cl.argval)",
    "                continue",
    "            chain.append((cur, 'or'))",
    "            if ft is true_tgt or ft in _body_sem:",
    "                break",
    "            return None",
    "        else:",
    "            return None",
    "        if len(chain) < 3 or false_tgt is None or false_tgt in _body_sem:",
    "            return None",
    "        if sum(1 for _, _o in chain if _o == 'and') < 1:",
    "            return None",
    "        _chain_blks = [b for b, _ in chain]",
    "        for _cb in _chain_blks:",
    "            _own = self.block_to_region.get(_cb)",
    "            if _own is None or _own is loop:",
    "                continue",
    "            if isinstance(_own, LoopRegion) and loop.header_block in getattr(_own, 'blocks', ()):",
    "                continue",
    "            if isinstance(_own, IfRegion) and _own.entry is _cb:",
    "                continue",
    "            return None",
    "        # [R21-62 第二判据] 闩锁复制签名：体首块尾部逐位复制链首操作数求值序列 +",
    "        # 至少两条独立后向条件边归一到同一真出口。",
    "        _tail_prefix = self._r2162_split_duplicated_tail(true_tgt, _chain_blks[0])",
    "        if _tail_prefix is None:",
    "            return None",
    "        _bwd_srcs = set()",
    "        for _bb in loop.body_blocks or []:",
    "            _bl = _bb.get_last_instruction()",
    "            if (_bl is None or _bl.opname not in BACKWARD_CONDITIONAL_JUMP_OPS",
    "                    or _bl.argval is None):",
    "                continue",
    "            if _norm(self.cfg.get_block_by_offset(_bl.argval)) is true_tgt:",
    "                _bwd_srcs.add(_bb)",
    "        if len(_bwd_srcs) < 2:",
    "            return None",
    "        return chain",
    "",
    "    def _r2162_split_duplicated_tail(self, body_entry: BasicBlock,",
    "                                       chain_head: BasicBlock):",
    "        \"\"\"[R21-62 判据] 体首块尾部是否整体复制链首操作数的求值序列。",
    "",
    "        只读两个块自身的指令 opcode 序列（噪声与块末条件跳转除外）：若体首块以",
    "        链首操作数的完整 opcode 序列结尾，且其前缀含至少一条完整语句终结指令",
    "        （POP_TOP / STORE_* / RETURN*），返回前缀指令列表；否则 None。",
    "        CPython 3.11 在 while 回边重发短路条件时正是这一形态。零名字/常量/偏移。",
    "        \"\"\"",
    "        if body_entry is None or chain_head is None:",
    "            return None",
    "        _b = [i for i in body_entry.instructions if i.opname not in NOISE_OPS",
    "              and i.opname != 'EXTENDED_ARG']",
    "        _c = [i for i in chain_head.instructions if i.opname not in NOISE_OPS",
    "              and i.opname != 'EXTENDED_ARG']",
    "        if _b and _b[-1].opname in CONDITIONAL_JUMP_OPS:",
    "            _b = _b[:-1]",
    "        if _c and _c[-1].opname in CONDITIONAL_JUMP_OPS:",
    "            _c = _c[:-1]",
    "        if not _c or len(_b) <= len(_c):",
    "            return None",
    "        if [i.opname for i in _b[-len(_c):]] != [i.opname for i in _c]:",
    "            return None",
    "        _prefix = _b[:-len(_c)]",
    "        if not any(i.opname in ('POP_TOP', 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',",
    "                               'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',",
    "                               'RETURN_VALUE', 'RETURN_CONST') for i in _prefix):",
    "            return None",
    "        return _prefix",
    "",
]

A_CALL = [
    "        _r2162_chain = self._detect_while_condition_or_prefix_and_group_chain(cond_block, loop)",
    "        if _r2162_chain and len(_r2162_chain) >= 3:",
    "            return _r2162_chain",
]

A_ANCHOR_CALL = [
    "        _nested_chain = self._detect_while_condition_nested_and_or_chain(cond_block, loop)",
    "        if _nested_chain and len(_nested_chain) >= 2:",
    "            return _nested_chain",
]

RELAX = [
    "                        # [R21-62] back_edge_block is header_block ⇒ 闩锁复制形态：不得在 header 处停止",
    "                        # 收集体可达变量集（后向重入边即锁存边本身）；回访防护由 _rvis2 承担。",
    "                        if _rc2 != region.back_edge_block or _rc2 is region.header_block:",
]
RELAX_OLD = ["                        if _rc2 != region.back_edge_block:"]

PATCHES = {
    'CLEAN': [],
    'AR': [
        (AN, [
            "    def _detect_while_condition_boolop_chain(self, cond_block: BasicBlock, loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:",
        ], A_METHOD, 'before'),
        (AN, A_ANCHOR_CALL, A_CALL, 'after'),
        (AN, RELAX_OLD, RELAX, 'replace'),
    ],
    'A': [
        (AN, [
            "    def _detect_while_condition_boolop_chain(self, cond_block: BasicBlock, loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:",
        ], A_METHOD, 'before'),
        (AN, A_ANCHOR_CALL, A_CALL, 'after'),
    ],
}


def main():
    name = sys.argv[1]
    grouped = {}
    order = []
    for path, anchor, new, mode in PATCHES[name]:
        if path not in grouped:
            grouped[path] = []
            order.append(path)
        grouped[path].append((anchor, new, mode))
    for path in order:
        apply(path, grouped[path])


if __name__ == '__main__':
    main()
