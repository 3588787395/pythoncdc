"""R14-01 四臂补丁文本（只读参考，不参与电池判决）：OLD_*/NEW_* 成对，作用于 core/cfg/region_analyzer.py 基线 640d33a77dcb71c2。 HELPER 是新增的三个识别端谓词 _r14_cc_segments/_r14_cc_operand_reaches/_r14_cc_operand_exit/_r14_cc_run_member/_r14_cc_cleanup_hop。"""
HELPER = """    def _r14_cc_segments(self, current):
        # [R14-01] 链式比较操作数段表：头块 + 既有链式比较检测器给出的续块。
        _info = self._detect_chained_compare_pattern(current)
        if not _info or len(_info.get('compare_ops', [])) < 2:
            return None
        return [current] + list(_info.get('extra_chain_blocks', []) or [])

    def _r14_cc_operand_reaches(self, current, T):
        # [R14-01] 识别端·链式比较作为布尔算子 run 的操作数：current 是
        # COPY(2)+COMPARE_OP 结构的链式比较头块，且其末段的某条后继边（直接，
        # 或经一个仅含 JUMP_FORWARD 的控制块）落到本 run 前缀共享的短路目标 T
        # 时，current 是该 run 的操作数，而不是下一条语句的条件块。
        # 原则 3（嵌套即抽象节点）：链式比较整段作为单个操作数被父 run 引用，
        # 内部块不逐段进入 op_chain（原则 2 每块唯一归属由既有 cc 区域消费端
        # 与生成端 _build_boolop_operand 的链式比较回退分支承担）。
        if not self._is_chained_compare_header(current):
            return False
        _segs = self._r14_cc_segments(current)
        if not _segs:
            return False
        for _s in list(_segs[-1].conditional_successors):
            if _s is T:
                return True
            _sl = _s.get_last_instruction()
            if (_sl is not None and _sl.opname == 'JUMP_FORWARD'
                    and getattr(_sl, 'argval', None) is not None
                    and len([i for i in _s.instructions
                             if i.opname not in ('NOP', 'CACHE')]) == 1
                    and self.cfg.get_block_by_offset(_sl.argval) is T):
                return True
        return False

    def _r14_cc_operand_exit(self, current):
        # [R14-01] 链式比较操作数的失败腿目标：末段条件跳转的落点块。
        _segs = self._r14_cc_segments(current)
        if not _segs:
            return None
        _li = _segs[-1].get_last_instruction()
        if _li is None or getattr(_li, 'argval', None) is None:
            return None
        return self.cfg.get_block_by_offset(_li.argval)

"""

OLD_IF = ("                    if (_r64_closed and _r64_cj is not _r64_T\n"
          "                            and ft_succ is not _r64_T\n"
          "                            and not _r64_rejoin):\n"
          "                        chain.pop()\n"
          "                        break\n")
NEW_EXEMPT = ("                    if (_r64_closed and _r64_cj is not _r64_T\n"
              "                            and ft_succ is not _r64_T\n"
              "                            and not _r64_rejoin):\n"
              "                        if self._r14_cc_operand_reaches(current, _r64_T):\n"
              "                            break\n"
              "                        chain.pop()\n"
              "                        break\n")
OLD_CLAMP = ("            if (_w14_t0 is not None and _w14_last_ft is not None\n"
             "                    and _w14_t0 is not _w14_last_ft):\n")
NEW_CLAMP = ("            if (_w14_t0 is not None and _w14_last_ft is not None\n"
             "                    and _w14_t0 is not _w14_last_ft\n"
             "                    and not self._r14_cc_operand_reaches(_w14_last_blk, _w14_t0)):\n")

OLD_MERGE = ("                    break\n"
             "        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the\n")
NEW_MERGE = ("                    break\n"
             "            # [R14-01] 条件跳转收尾的末成员同样适用清理块解析：or run 的末\n"
             "            # 操作数为链式比较时，其短路腿落到 POP_TOP 清理块，真正的汇合点\n"
             "            # 在清理块之后（else / next elif 入口）。\n"
             "            if merge is not None and self._is_chained_compare_cleanup_block(merge):\n"
             "                _r14_eff = self._get_effective_merge_through_cleanup(merge)\n"
             "                if _r14_eff is not None:\n"
             "                    merge = _r14_eff\n"
             "        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the\n")
NEW_HOPM = ("                    break\n"
            "            # [R14-01] or run 的末操作数为链式比较时，其短路腿落到链式\n"
            "            # 比较的早退清理块（POP_TOP + JUMP_FORWARD），真正的汇合点在\n"
            "            # 清理块之后（else / next elif 入口），与普通三操作数 or 链\n"
            "            # （末成员 IF_FALSE 直接落 else 入口）保持一致。\n"
            "            if merge is not None and self._is_chained_compare_header(last_block):\n"
            "                _r14_eff = self._r14_cc_cleanup_hop(merge)\n"
            "                if _r14_eff is not None:\n"
            "                    merge = _r14_eff\n"
            "        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the\n")
HELPER += """    def _r14_cc_cleanup_hop(self, blk):
        # [R14-01] 链式比较早退清理块（POP_TOP + JUMP_FORWARD）的汇合落点。
        _eff = [i for i in blk.instructions if i.opname not in ('NOP', 'CACHE')]
        if (len(_eff) == 2 and _eff[0].opname == 'POP_TOP'
                and _eff[1].opname == 'JUMP_FORWARD' and _eff[1].argval is not None):
            return self.cfg.get_block_by_offset(_eff[1].argval)
        return None

"""

OLD_GUARD = '                    if (_first_jt is not None and _cur_jt is not None\n                            and _first_jt is not _cur_jt\n                            and not self._is_equivalent_exit_block(_first_jt, _cur_jt)):\n                        chain.pop()\n'
NEW_GUARD = '                    if (_first_jt is not None and _cur_jt is not None\n                            and _first_jt is not _cur_jt\n                            and not self._is_equivalent_exit_block(_first_jt, _cur_jt)\n                            and not self._r14_cc_operand_reaches(current, _first_jt)):\n                        chain.pop()\n'

HELPER += """    def _r14_cc_run_member(self, blk, chain):
        # [R14-02] 链式比较区域入口作为布尔算子 run 的末操作数（原则 3：嵌套
        # 区域即抽象节点，被父 run 引用而非被吸收）：blk 是带
        # chained_compare_ops(>=2) 的 IfRegion 入口，且该链式比较的成功腿落到
        # 本 run 前缀共享的短路目标 T（前缀全员跳转目标同为一块，[C1] 同层块
        # 末指令与区域表事实）时，blk 属于该 run；其内部块仍唯一归属该链式
        # 比较区域（原则 2），由既有 hop 机制跳过。
        if not chain or len(chain) < 2:
            return False
        _l0 = chain[0][0].get_last_instruction()
        if _l0 is None or getattr(_l0, 'argval', None) is None:
            return False
        _T = self.cfg.get_block_by_offset(_l0.argval)
        if _T is None:
            return False
        for _b, _o in chain:
            _bl = _b.get_last_instruction()
            if (_bl is None or getattr(_bl, 'argval', None) is None
                    or self.cfg.get_block_by_offset(_bl.argval) is not _T):
                return False
        for _r in self.regions:
            if (type(_r) is IfRegion and getattr(_r, 'chained_compare_ops', None)
                    and len(_r.chained_compare_ops) >= 2 and _r.entry is blk):
                return self._r14_cc_operand_reaches(blk, _T)
        return False

"""

OLD_C1 = """            if not skip_claimed_check:
                if ft_succ in claimed:
                    break
"""
NEW_C1 = """            if not skip_claimed_check:
                if ft_succ in claimed and not self._r14_cc_run_member(ft_succ, chain):
                    break
"""
OLD_C2 = """                if ft_succ in self.block_to_region:
"""
NEW_C2 = """                if ft_succ in self.block_to_region and not self._r14_cc_run_member(ft_succ, chain):
"""

OLD_C12 = """            if not skip_claimed_check:
                if ft_succ in claimed:
                    break
                if ft_succ in self.block_to_region:
                    # [R2-B9 fix] TryRegion 范围认领豁免（try_scope_exempt=
"""
NEW_C12 = """            if not skip_claimed_check:
                # [R14-02] 链式比较区域入口可作为本 run 的末操作数被引用（原则 3），
                # 不视为「已被其它区域领有」而断链；其内部块仍由下方 hop 机制排除。
                if ft_succ in claimed and not self._r14_cc_run_member(ft_succ, chain):
                    break
                if (ft_succ in self.block_to_region
                        and not self._r14_cc_run_member(ft_succ, chain)):
                    # [R2-B9 fix] TryRegion 范围认领豁免（try_scope_exempt=
"""

OLD_RB = "        region_blocks = chain_blocks | ({merge} if merge else set())" + chr(10)
NEW_RB = OLD_RB + """        # [R14-03] 链式比较操作数头块不进 BoolOpRegion.blocks：该块唯一归属
        # 其自身的链式比较 IfRegion（原则 2），BoolOpRegion 只在 op_chain 中
        # 引用它作为单个操作数（原则 3 抽象节点）。缺此处置时头块被两处认领，
        # 父 IfRegion 的块集与 elif 收集随之失真。
        for _r14_b in list(region_blocks):
            for _r14_r in self.regions:
                if (type(_r14_r) is IfRegion
                        and getattr(_r14_r, 'chained_compare_ops', None)
                        and len(_r14_r.chained_compare_ops) >= 2
                        and _r14_r.entry is _r14_b):
                    region_blocks.discard(_r14_b)
                    break
"""
