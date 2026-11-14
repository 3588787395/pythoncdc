# fix161c.py: rr-v5r161 [v161-NOTMIX] 最终形态——回退五处走查改动，
# 改为「标准走查失败后的极性融合 not 头专用探测」。
#
# 前情：v161 的门内登记+走查尾重分类（fix161.py）修好融合 not 头，但门改动
# 使走查越过 HEAD 断链点，把 NOTTAIL `A and not (B and C)` 一并吞入，产生
# 德摩根语义反转（difflib 61/62）；fix161b（走查尾 >=3 收窄）又被实证推翻
# （`not a or b` 反成 `if a and b:` 真值表反转）。两树探针（probe3.py）证实：
# 融合形与 NOTTAIL 在首续接点完全镜像，门内无判别力；判别力在完整结构
# （and 子链 >=2 成员、每成员同跳 E、末成员 fall-through == 链首目标）。
#
# 本补丁：① 走查回到 HEAD 逐字节（由 head_region_analyzer.py 覆盖完成，
# 已核验 git numstat 为空）；② 注入 _detect_fused_not_head_chain 专用探测，
# 仅在 `len(chain) < 2` 时尝试；命中则沿用既有下游，不命中 return None
# （HEAD 同路径，C3）。
import io
import py_compile

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s


def rep(old, new, expect=1):
    global s
    c = s.count(old)
    assert c == expect, 'anchor count %d (expect %d): %r' % (c, expect, old[:90])
    s = s.replace(old, new, expect)


DETECTOR = '''    def _detect_fused_not_head_chain(self, start_block: BasicBlock) -> Optional[List[Tuple[BasicBlock, str]]]:
        """[v161-NOTMIX] 极性融合 not 头的 or→and 混合链专用探测（走查失败后）。

        形如 ``not A or (B and C)``：CPython 把 ``not A`` 的假边直接融合到条件
        真值汇聚块（不生成 UNARY_NOT），opcode-only 分类按末成员极性把链首误
        标为 'and'，标准走查在首续接门（「链首与候选出口不等」）即断链。该断
        链点与 NOTTAIL（``A and not (B and C)``）在门内完全镜像——两形只有
        {链首目标, 候选目标} = {体入口, 子链出口} 的对调，门时点无法区分（见
        fresh/notmix/DESIGN_r161c.md 两树探针实证），故改由本探测按完整结构
        重建：

        ① 链首 head：FALSE 极性条件跳转，目标 B = and 子链末成员的
           fall-through（条件真值汇聚块 / 体入口）；
        ② head 的 fall-through 后继 Y：条件跳转，目标 E = and 子链共享假出口；
           要求 E ≠ B（且二者非同价平凡出口，避免双 None 归并形歧义）；
        ③ 自 Y 沿 fall-through 走子链：每个成员末指令为条件跳转且目标 == E
           （或等价于 E，含 CPython jump-threading 的等价出口变体）；遇到
           fall-through == B 的成员即为子链末成员，子链闭合；
        ④ 子链成员数 >= 2 才成立。

        判别力（实证）：``not A or (B and C)`` 命中（成员 2、末成员 ft == B，
        返回 [(head,'or'), (B,'and'), (C,'and')]，与 fix161 走查产出的链逐元素
        相同）；``not A or B`` 双成员形成员数 1 不命中（维持 HEAD 的「无 else」
        装配路径，零触碰）；NOTTAIL 的第二成员为 TRUE 极性且目标 18 ≠ E，子链
        成员数恒为 1，不命中（维持 HEAD 的 ``A and not (B and C)`` 渲染）。

        不命中返回 None，调用方维持 HEAD 的 ``return None`` 路径（逐字节不变，
        C3）。只读 CFG（块末指令 opname/argval、conditional_successors、
        get_block_by_offset、_is_equivalent_exit_block），不新增 self 跨方法
        状态（C1/C2）；不使用文件名/名字白名单/偏移阈值（I.4 白名单）。
        """
        if start_block is None:
            return None
        boolop_jumps = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        head_li = start_block.get_last_instruction()
        if (head_li is None or head_li.opname not in boolop_jumps
                or 'FALSE' not in head_li.opname
                or getattr(head_li, 'argval', None) is None):
            return None
        head_tgt = self.cfg.get_block_by_offset(head_li.argval)
        if head_tgt is None:
            return None
        head_ft = None
        for succ in start_block.conditional_successors:
            if succ.start_offset != head_li.argval:
                head_ft = succ
                break
        if head_ft is None or head_ft is head_tgt:
            return None
        y_li = head_ft.get_last_instruction()
        if (y_li is None or y_li.opname not in boolop_jumps
                or getattr(y_li, 'argval', None) is None):
            return None
        sub_exit = self.cfg.get_block_by_offset(y_li.argval)
        if sub_exit is None or sub_exit is head_tgt:
            return None
        if self._is_equivalent_exit_block(head_tgt, sub_exit):
            return None
        members = []
        seen = set()
        cur = head_ft
        closed = False
        while cur is not None and cur.start_offset not in seen and len(members) <= 64:
            seen.add(cur.start_offset)
            cur_li = cur.get_last_instruction()
            if (cur_li is None or cur_li.opname not in boolop_jumps
                    or getattr(cur_li, 'argval', None) is None):
                return None
            cur_jt = self.cfg.get_block_by_offset(cur_li.argval)
            if cur_jt is None or not (cur_jt is sub_exit
                                      or self._is_equivalent_exit_block(cur_jt, sub_exit)):
                return None
            cur_ft = None
            for succ in cur.conditional_successors:
                if succ.start_offset != cur_li.argval:
                    cur_ft = succ
                    break
            if cur_ft is None:
                return None
            members.append(cur)
            if cur_ft is head_tgt:
                closed = True
                break
            cur = cur_ft
        if not closed or len(members) < 2:
            return None
        chain = [(start_block, 'or')]
        chain.extend((m, 'and') for m in members)
        return chain

'''

DEF_ANCHOR = ('    def _detect_boolop_conditional_chain(self, start_block: BasicBlock, '
              'claimed: Set[BasicBlock], skip_claimed_check: bool = False, '
              'try_scope_exempt: bool = False) -> Optional[List[Tuple[BasicBlock, str]]]:\n')

HOOK_OLD = '''        if len(chain) < 2:
            return None
        # [W14-A 修复·or 首链真出口一致性裁剪] 首成员为 IF_TRUE 跳转且
'''

HOOK_NEW = '''        if len(chain) < 2:
            # [v161-NOTMIX] 标准走查在首续接门断链后才尝试：极性融合 not 头
            # 的 or→and 混合链（`not A or (B and C)`）在 opcode-only 分类下与
            # NOTTAIL（`A and not (B and C)`）首续接点完全镜像，门内无判别力
            # （DESIGN_r161c.md 两树探针实证）。改由专用结构探测重建：and 子链
            # >=2 成员 ∧ 每成员同跳子链出口 E ∧ 末成员 fall-through == 链首
            # 目标 B。命中则用其链继续走下方既有下游（mixed-chain unify），
            # 与 fix161 走查产出的链逐元素相同；不命中仍 return None，与 HEAD
            # 逐字节同路径——`not A or B`（成员 1）与 NOTTAIL（第二成员 TRUE
            # 极性、目标 != E）均不命中，零触碰。
            _v161_fused = self._detect_fused_not_head_chain(start_block)
            if _v161_fused is None:
                return None
            chain = _v161_fused
        # [W14-A 修复·or 首链真出口一致性裁剪] 首成员为 IF_TRUE 跳转且
'''

rep(HOOK_OLD, HOOK_NEW)
rep(DEF_ANCHOR, DETECTOR + DEF_ANCHOR)

assert s != orig
assert s.count('v161-NOTMIX') == 2, 'marker count %d' % s.count('v161-NOTMIX')
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix161c applied: markers=%d, lines=%d' % (s.count('v161-NOTMIX'), len(s.splitlines())))

py_compile.compile(PATH, doraise=True)
print('syntax OK')
