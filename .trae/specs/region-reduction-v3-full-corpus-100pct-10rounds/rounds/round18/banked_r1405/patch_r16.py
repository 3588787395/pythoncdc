"""Apply the R14-05 candidate patch to the MIRROR analyzer (line-anchored, CRLF-safe).

Each op is (name, [anchor lines], [replacement lines]) matched on CR-normalised
content; every anchor must match exactly once or nothing is written.
"""
import hashlib
import os
import shutil
import subprocess
import sys

MIRROR = r"D:/Temp/r160/mirror"
TARGET = os.path.join(MIRROR, "core", "cfg", "region_analyzer.py")
PRISTINE_DIR = r"D:/Temp/r160/work/pristine"
BASE = "640d33a77dcb71c2"
NL = "\n"

HELPER = '''    def _r16_cc_cleanup_hop(self, blk: BasicBlock) -> Optional[BasicBlock]:
        """[R14-05] 链式比较「早退清理块」之后的真实汇合块。

        算法依据：CPython 3.11 把 `a < b < c` 前段短路为假的路径编成
        `POP_TOP; JUMP_FORWARD -> exit` —— 该块既不承载值也不承载语句，只是把
        控制流引到本 run 的汇合点。既有 _is_chained_compare_cleanup_block 只认
        `SWAP; POP_TOP` 的旧形状，故链式比较作为布尔 run 成员时，_boolop_resolve_merge
        会把清理块 itself 当成汇合块。
        归约顺序：在布尔 run 归约（_boolop_resolve_merge）时同层调用，不回看任何
        已渲染区域。唯一归属：本判定不认领块，只把汇合块指针从清理块移到其目标。
        入口引用语义：命中后 BoolOpRegion.merge_block 即该 run 的假出口块，父
        IfRegion 据此把真值边落点认成臂入口。
        反编译流程：[C1] 判据只用块内非噪声指令序列（恰为 POP_TOP 紧跟
        JUMP_FORWARD）与该跳边目标，无函数名、无字符串常量、无字节偏移、无
        指令计数阈值；[C2] 纯查询，不写任何区域字段；[C3] 形状不符返回 None，
        调用方维持原汇合块。
        """
        _eff = [i for i in blk.instructions if i.opname not in NOISE_OPS]
        if (len(_eff) == 2 and _eff[0].opname == 'POP_TOP'
                and _eff[1].opname == 'JUMP_FORWARD'
                and getattr(_eff[1], 'argval', None) is not None):
            return self.cfg.get_block_by_offset(_eff[1].argval)
        return None

    def _r16_boolop_cc_run_operand(self, cand: BasicBlock, prefix_blocks) -> bool:
        """[R14-05] cand 是否为正在装配的布尔算子 run 的「链式比较操作数」。

        算法依据（原则 1 自底向上 + 原则 3 嵌套即抽象节点）：跳转语境里的
        `A or B or a<b<c` 降级为「每名成员块尾一条条件跳边 + 落空边接下一成员」，
        其中链式比较成员把整段 COPY(2)+COMPARE_OP 结构作为**单个**操作数被父 run
        引用；其内部段块唯一归属链式比较本身（原则 2），不进 op_chain。
        与既有 hop 机制的差别：hop 以「该链式比较区域已在 self.regions」为前提，
        而区域登记与本 run 的识别没有先后保证（链式比较区域可能晚于布尔识别才出现，
        实测 a03/strategy 形在布尔识别时 cc 区域表为空），故本判据只用块内结构识别
        链式比较，不查区域表。

        识别条件（[C1] 全为同层块结构事实：块内指令集、块末指令 opcode 与跳边
        目标、前驱/后继身份；无函数名、无常量、无字节偏移、无成员数阈值）：
          (1) cand 是链式比较头块（COPY(arg=2) 紧跟 COMPARE_OP/IS_OP/CONTAINS_OP，
              且检测器给出 >=2 个比较算子，即确有末段）；
          (2) run 前缀 prefix_blocks 的每名成员都以短路/条件正向跳边落到**同一块**
              T —— 该 run 的短路出口已定；
          (3) cand 的链式比较**末段**有一条成功沿直达 T，或经一个仅含
              JUMP_FORWARD 的纯控制块落到 T —— 即 cand 的「比较成立」路径正是本
              run 的出口，它不是下一条语句的条件块。
        归约方式：命中即允许链 walk 越过「块已被认领」类守卫把 cand 收为下一名
        成员（内部块仍由既有 hop 机制跳过），不改写任何已成立区域的归属。
        唯一归属判定：命中只让 cand 进入 op_chain，其内部段块不进入；不命中维持
        原守卫，cand 仍是它自己那条语句的入口。
        入口引用语义：T 保持为该 run 的引用出口，父 IfRegion 依 T 与汇合块确定
        臂入口，本判定不预先指定臂。
        反编译流程：[C2] 纯查询谓词；[C3] cand 缺末段/前缀不汇聚同一块/cand 两条
        沿都不达 T 时一律 False，产物与入轮逐字节一致。
        """
        if cand is None or not prefix_blocks:
            return False
        if not self._is_chained_compare_header(cand):
            return False
        _pat = self._detect_chained_compare_pattern(cand)
        if not _pat or len(_pat.get('compare_ops', []) or []) < 2:
            return False
        _BOOLOP_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        _T = None
        for _b in prefix_blocks:
            _bl = _b.get_last_instruction()
            if (_bl is None or getattr(_bl, 'argval', None) is None
                    or _bl.opname not in _BOOLOP_JUMPS):
                return False
            _t = self.cfg.get_block_by_offset(_bl.argval)
            if _t is None:
                return False
            if _T is None:
                _T = _t
            elif _T is not _t:
                return False
        if _T is None:
            return False
        _segs = [cand] + list(_pat.get('extra_chain_blocks', []) or [])
        _last_seg = _segs[-1]
        _li = _last_seg.get_last_instruction()
        if _li is None or getattr(_li, 'argval', None) is None:
            return False
        for _s in list(_last_seg.conditional_successors):
            if _s is _T:
                return True
        return self._r16_cc_operand_success_edge(cand) is _T

    def _r16_cc_operand_success_edge(self, cand: BasicBlock) -> Optional[BasicBlock]:
        """[R14-05] 链式比较成员「比较成立」一侧的落点。

        算法依据：链式比较 `a<b<c` 作布尔 run 的单名成员时，其「成功沿」不在
        cand 块本身，而在**末段**块的落空边上；该落空边若只是一个
        POP_TOP/JUMP_FORWARD 型纯控制块（CPython 在 cc 段与 run 体之间的接线块），
        则再前进一步。与 _r16_boolop_cc_run_operand 共用同一结构识别
        （COPY(arg=2)+比较指令对、>=2 个比较算子），不查区域表。
        归约顺序：链 walk / run 一致性校验时同层调用。唯一归属：不认领块。
        入口引用语义：返回值即该成员被当成单个抽象操作数时的「比较成立」出口，
        父 run 的成员段块（extra_chain_blocks、纯控制块）不出现在调用方的
        成员集合里。
        反编译流程：[C1] 只用块内指令集、末指令 opcode 与跳边/落空边身份；
        [C2] 纯查询；[C3] cand 不是链式比较头块或末段无落空边时返回 None。
        """
        if cand is None or not self._is_chained_compare_header(cand):
            return None
        _pat = self._detect_chained_compare_pattern(cand)
        if not _pat or len(_pat.get('compare_ops', []) or []) < 2:
            return None
        _segs = [cand] + list(_pat.get('extra_chain_blocks', []) or [])
        _last_seg = _segs[-1]
        _li = _last_seg.get_last_instruction()
        if _li is None or getattr(_li, 'argval', None) is None:
            return None
        _ft = None
        for _s in list(_last_seg.conditional_successors):
            if _s.start_offset != _li.argval:
                _ft = _s
                break
        if _ft is None:
            return None
        _fl = _ft.get_last_instruction()
        if (_fl is not None and _fl.opname == 'JUMP_FORWARD'
                and getattr(_fl, 'argval', None) is not None
                and len([i for i in _ft.instructions if i.opname not in NOISE_OPS]) == 1):
            return self.cfg.get_block_by_offset(_fl.argval)
        return _ft

'''

OPS = [
    ("helper_insert",
     "    def _detect_boolop_chain_start(self, block: BasicBlock, claimed: Set[BasicBlock]) -> Optional[List[Tuple[BasicBlock, str]]]:",
     HELPER + "    def _detect_boolop_chain_start(self, block: BasicBlock, claimed: Set[BasicBlock]) -> Optional[List[Tuple[BasicBlock, str]]]:"),
    ("S1_claim_guard",
     NL.join([
         "            if not skip_claimed_check:",
         "                if ft_succ in claimed:",
         "                    break",
         "                if ft_succ in self.block_to_region:",
         ""]),
     NL.join([
         "            if not skip_claimed_check:",
         "                # [R14-05] 链式比较成员不因「被其它区域领有」断链：",
         "                _r16_cc_operand = self._r16_boolop_cc_run_operand(",
         "                    ft_succ, [b for b, _ in chain])",
         "                if ft_succ in claimed and not _r16_cc_operand:",
         "                    break",
         "                if (ft_succ in self.block_to_region",
         "                        and not _r16_cc_operand):",
         ""])),
    ("S2_loop_guard",
     NL.join([
         "                if ft_succ in self.block_to_region:",
         "                    _ft_reg = self.block_to_region.get(ft_succ)",
         "                    if isinstance(_ft_reg, LoopRegion):",
         ""]),
     ("                if ft_succ in self.block_to_region:\n"
      "                    _ft_reg = self.block_to_region.get(ft_succ)\n"
      "                    if (isinstance(_ft_reg, LoopRegion)\n"
      "                            and not self._r16_boolop_cc_run_operand(\n"
      "                                ft_succ, [b for b, _ in chain])):\n")),
    ("S3_cc_hop_guard",
     NL.join([
         "                    if (_first_jt is not None and _cur_jt is not None",
         "                            and _first_jt is not _cur_jt",
         "                            and not self._is_equivalent_exit_block(_first_jt, _cur_jt)):",
         "                        chain.pop()",
         "                        break",
         ""]),
     ("                    if (_first_jt is not None and _cur_jt is not None\n"
      "                            and _first_jt is not _cur_jt\n"
      "                            and not self._is_equivalent_exit_block(_first_jt, _cur_jt)\n"
      "                            and not self._r16_boolop_cc_run_operand(\n"
      "                                current, [b for b, _ in chain[:-1]])):\n"
      "                        chain.pop()\n"
      "                        break\n")),
    ("S4_r64_pop",
     NL.join([
         "                    if (_r64_closed and _r64_cj is not _r64_T",
         "                            and ft_succ is not _r64_T",
         "                            and not _r64_rejoin):",
         "                        chain.pop()",
         "                        break",
         ""]),
     ("                    if (_r64_closed and _r64_cj is not _r64_T\n"
      "                            and ft_succ is not _r64_T\n"
      "                            and not _r64_rejoin\n"
      "                            and not self._r16_boolop_cc_run_operand(\n"
      "                                current, [b for b, _ in chain[:-1]])):\n"
      "                        chain.pop()\n"
      "                        break\n")),
    ("S5_merge_hop",
     NL.join([
         "                    break",
         "        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the",
         ""]),
     ("                    break\n"
      "            # [R14-05] 末成员是链式比较头块时，其短路边落到该链式比较的\n"
      "            # 早退清理块（POP_TOP + JUMP_FORWARD），真正的汇合块在清理块\n"
      "            # 之后（else / 下一兄弟语句入口），与普通三操作数 or 链的末成员\n"
      "            # 短路边直接落 else 入口保持一致。\n"
      "            if (merge is not None\n"
      "                    and self._is_chained_compare_header(last_block)):\n"
      "                _r16_eff = self._r16_cc_cleanup_hop(merge)\n"
      "                if _r16_eff is not None:\n"
      "                    merge = _r16_eff\n"
      "        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the\n"),
     ),
    ("S6_r59_cc_member",
     NL.join([
         "                _first_jt = self.cfg.get_block_by_offset(_first_last.argval) if _first_last.argval is not None else None",
         "                _second_blk = chain[1][0]",
         "                _second_last = _second_blk.get_last_instruction()",
         "                _second_ft = None",
         "                if _second_last and _second_last.argval is not None:",
         "                    _second_ft = next((s for s in _second_blk.conditional_successors",
         "                                      if s.start_offset != _second_last.argval), None)",
         "                if _first_jt is not None and _second_ft is not None and _first_jt is _second_ft:",
     ]),
     NL.join([
         "                _first_jt = self.cfg.get_block_by_offset(_first_last.argval) if _first_last.argval is not None else None",
         "                _second_blk = chain[1][0]",
         "                _second_last = _second_blk.get_last_instruction()",
         "                _second_ft = None",
         "                if _second_last and _second_last.argval is not None:",
         "                    _second_ft = next((s for s in _second_blk.conditional_successors",
         "                                      if s.start_offset != _second_last.argval), None)",
         "                # [R14-05] 次成员是链式比较操作数时，它的「比较成立」落点不在",
         "                # 自身块的落空边（那是它的内部续段），而在链式比较末段之后；",
         "                # R59 的「首成员真边 == 次成员落空边」必须以该落点为准，否则",
         "                # 整条 or-run 被误判成 if/elif 而交还 IfRegion 层级拆成嵌套 if。",
         "                if self._r16_boolop_cc_run_operand(_second_blk, [chain[0][0]]):",
         "                    _second_ft = self._r16_cc_operand_success_edge(_second_blk)",
         "                if _first_jt is not None and _second_ft is not None and _first_jt is _second_ft:",
     ])),
    ("S7_arm_entry_cc_member",
     NL.join([
         "                for s in last_succs:",
         "                    if s != else_succ and s not in chain_blocks:",
         "                        then_succ = s",
         "                        break",
     ]),
     NL.join([
         "                for s in last_succs:",
         "                    if s != else_succ and s not in chain_blocks:",
         "                        then_succ = s",
         "                        break",
         "                # [R14-05] 该链式比较同时是布尔算子 run 的成员时",
         "                # （condition_block 落在 BoolOpRegion.op_chain 内），它的",
         "                # 「比较成立」落点在链式比较末段之后，且要越过 CPython 为",
         "                # run 多条成员接线用的纯 JUMP_FORWARD 控制块；上面按偏移",
         "                # 排序取后继会把那个接线块当成臂入口，于是臂体被登记成",
         "                # merge、真臂体落在臂外。判据与 run walk 端同一处复用。",
         "                if (isinstance(block_region, BoolOpRegion)",
         "                        and block_region.entry == block",
         "                        and condition_block in {b for b, _ in block_region.op_chain}",
         "                        and self._r16_boolop_cc_run_operand(",
         "                            condition_block,",
         "                            [b for b, _ in block_region.op_chain][:-1])):",
         "                    _r16_then = self._r16_cc_operand_success_edge(condition_block)",
         "                    if _r16_then is not None:",
         "                        then_succ = _r16_then",
     ])),
    ("S8_run_exits_decided_together",
     NL.join([
         "                    ) and len(else_succ.successors) == 1",
         "                    if _else_is_cleanup:",
         "                        else_succ = list(else_succ.successors)[0]",
         "",
         "            # Fix: 当条件块在 TryExceptRegion 的 try_blocks 中时，",
     ]),
     NL.join([
         "                    ) and len(else_succ.successors) == 1",
         "                    if _else_is_cleanup:",
         "                        else_succ = list(else_succ.successors)[0]",
         "            # [R14-05] 臂入口与汇合身份一起决定（原则 2 每块唯一归属 +",
         "            # 原则 4 父引用子入口，不做事后修补）：主条件是 BoolOpRegion",
         "            # （本区 entry 即该 run 的首名成员）且其末名成员是链式比较时，",
         "            # 该 run 的两条出口已由 run 自身给出 —— 真出口是链式比较成员",
         "            # 的「比较成立」落点（末段之后，必要时越过 run 接线用的纯",
         "            # JUMP_FORWARD 控制块），假出口就是 _boolop_resolve_merge 已解析",
         "            # 出的 BoolOpRegion.merge_block。此时不能再让 post-dominator 在",
         "            # 「run 内部成员块」之间另找汇合点：实测它会把臂体登记成 merge，",
         "            # 把真正的 run 汇合块留在区外（api_base/strategy 两处 IF_TRUE 落点差）。",
         "            _r16_run_merge = None",
         "            if (isinstance(block_region, BoolOpRegion)",
         "                    and block_region.entry == block",
         "                    and block_region.merge_block is not None",
         "                    and len(getattr(block_region, 'op_chain', []) or []) >= 2",
         "                    and condition_block is not block",
         "                    and self._r16_boolop_cc_run_operand(",
         "                        condition_block,",
         "                        [b for b, _ in block_region.op_chain][:-1])):",
         "                _r16_then = self._r16_cc_operand_success_edge(condition_block)",
         "                if (_r16_then is not None",
         "                        and _r16_then is not block_region.merge_block",
         "                        and _r16_then is not condition_block):",
         "                    then_succ = _r16_then",
         "                    else_succ = block_region.merge_block",
         "                    _r16_run_merge = block_region.merge_block",
         "",
         "            # Fix: 当条件块在 TryExceptRegion 的 try_blocks 中时，",
     ])),
    ("S9_merge_identity",
     "\n            merge = self._find_nearest_common_post_dominator(then_succ, else_succ)\n",
     "\n            merge = self._find_nearest_common_post_dominator(then_succ, else_succ)\n"
     "            if _r16_run_merge is not None:\n"
     "                merge = _r16_run_merge\n"),
    ("S10_run_member_cc_carries_no_arm",
     NL.join([
         "            # 如果检测到链式比较，设置链式比较信息到区域上",
         "            if region is not None and chained_compare_info:",
     ]),
     NL.join([
         "            # [R14-05] 作为布尔 run 成员的链式比较区域不承载臂（原则 3",
         "            # 嵌套即抽象节点 + 原则 2 每块唯一归属）：它的 entry 已被某条",
         "            # BoolOpRegion 的 op_chain 引为单名操作数，其「比较成立」落点块",
         "            # 属于父 IfRegion 的臂体；若继续把它收成本区 then/else，父臂与",
         "            # 本级争同一块，实测父臂渲染成 pass 且臂体语句整体丢失。命中时",
         "            # 只从已收集的臂集中取消「不属于本链式比较段」的块认领，不新增",
         "            # 语句、区域或跳边。本处是 _build_elif_region 与 _build_basic_if_region",
         "            # 两个构造器的唯一汇聚点，判据与 run walk 端同一处复用。",
         "            if region is not None:",
         "                _r16_br = self.block_to_region.get(block)",
         "                _r16_oc = ([b for b, _ in (getattr(_r16_br, 'op_chain', None) or [])]",
         "                             if isinstance(_r16_br, BoolOpRegion) else [])",
         "                if (len(_r16_oc) >= 2 and block in _r16_oc and block is not _r16_oc[0]",
         "                        and self._r16_boolop_cc_run_operand(block, _r16_oc[:-1])):",
         "                    _r16_own = {block}",
         "                    _r16_own |= set((self._detect_chained_compare_pattern(block)",
         "                                    or {}).get('extra_chain_blocks', []) or [])",
         "                    region.then_blocks = [b for b in region.then_blocks",
         "                                          if b in _r16_own or b == merge]",
         "                    region.else_blocks = [b for b in region.else_blocks",
         "                                          if b in _r16_own or b == merge]",
         "                    region.blocks = {b for b in region.blocks",
         "                                     if b in _r16_own or b in (block, merge)}",
         "            # 如果检测到链式比较，设置链式比较信息到区域上",
         "            if region is not None and chained_compare_info:",
     ])),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    raw = open(TARGET, "rb").read()
    h = sha(raw)
    keep = os.path.join(PRISTINE_DIR, BASE + ".py")
    if h != BASE and not os.path.exists(keep):
        print("ABORT: unexpected pre-state %s" % h[:16])
        return 2
    if not os.path.exists(keep):
        with open(keep, "wb") as fh:
            fh.write(raw)
    base = open(keep, "rb").read()
    lines = base.splitlines(keepends=True)
    norm = [l.replace(b"\r\n", b"\n").decode("utf-8") for l in lines]
    endings = [b"\r\n" if l.endswith(b"\r\n") else b"\n" for l in lines]
    text = "".join(norm)
    for name, anchor, repl in OPS:
        n = text.count(anchor)
        if n != 1:
            print("ANCHOR_FAIL %s matches=%d" % (name, n))
            return 1
        text = text.replace(anchor, repl, 1)
        print("APPLIED %s" % name)
    new_lines = text.split("\n")
    if new_lines and new_lines[-1] == "":
        new_lines.pop()
    eol = b"\r\n"
    out = b"".join(l.encode("utf-8") + eol for l in new_lines)
    open(TARGET, "wb").write(out)
    r = subprocess.run([sys.executable, "-X", "utf8", "-c",
                        "import py_compile;py_compile.compile(r'%s',doraise=True)" % TARGET],
                       capture_output=True, text=True)
    print("py_compile rc=%d %s" % (r.returncode, (r.stderr or "")[-700:]))
    cur = sha(open(TARGET, "rb").read())
    print("patched_sha=%s" % cur[:16])
    ls = out.splitlines(keepends=True)
    print("lines=%d crlf=%d lf=%d" % (len(ls), sum(1 for l in ls if l.endswith(b"\r\n")),
                                      sum(1 for l in ls if l.endswith(b"\n") and not l.endswith(b"\r\n"))))
    return r.returncode


def unpatch():
    keep = os.path.join(PRISTINE_DIR, BASE + ".py")
    want = sha(open(keep, "rb").read())
    shutil.copyfile(keep, TARGET)
    cur = sha(open(TARGET, "rb").read())
    print("restored=%s byte_exact=%s" % (cur[:16], cur == want))
    return 0 if cur == want else 1


if __name__ == "__main__":
    if "off" in sys.argv:
        sys.exit(unpatch())
    sys.exit(main())
