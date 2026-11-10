# fix158.py: rr-v5r158 [v158-RETFIN] try+finally 内联 return 值重组——if 臂穿
# finally 正常路径副本族（只增不破，单文件一处）。
#
# F1: `try: if c: return meth(url, fp, 500, msg, headers)  finally: self.tries = 0`
#     （urllib.request.FancyURLopener.http_error_302 实形，源 line 2161-2168）
#     v157 渲染 `meth(...)`（Expr）+ `return 0`——3.11 零成本 finally 对
#     return-in-try 发射 <CALL 求值> + [finally 正常副本内联：LOAD_CONST 0;
#     STORE_ATTR tries] + RETURN_VALUE，返回值（CALL 结果）驻留栈底穿越块界；
#     渲染把 CALL 当 Expr 语句、RETURN 抓副本尾 LOAD_CONST 0 = 真实 R1
#     （调用结果被丢弃、恒返回 0，判官 Different bytecode）。
#
# 根因: if 臂走查 _process_if_blocks（then 臂块循环）中——①值尾块（纯值生产
#     运行、无语句终结符）经 _generate_block_statements 尾 flush 渲染为 Expr；
#     既有 Expr→Return 转换被 `self._try_depth <= 0` 门挡住（try 上下文）；
#     ②后继 RETURN 块拉入路径把 finally 正常副本块当普通 return 块渲染
#     `return 0`。B207 return-in-finally 归约不适用：其直落判定
#     `_fall_through` 用「末有效指令偏移+2」——CALL 带 CACHE 尾垫使 +2 ≠ 副本
#     块起始（164 ≠ 172）且 B207 只在 _generate_try_body 块循环触发（该处
#     if 臂块已被 if 生成提前消费）。STORE_FAST result 名字形（B188→B234）
#     由 B75 前置归约正确重组，仅内联 CALL 值形缺。
#
# 修复: _process_if_blocks 后继 RETURN 拉入站点前加 [v158-RETFIN] 精确形
#     （B207 同式词汇，仅直落判定改用「非异常入口后继」——副本块起始偏移可
#     跨 CALL CACHE 尾垫，+2 判据不适用）：本臂末语句为 Expr ∧ 本块有效运行
#     无语句终结符（纯值生产运行）∧ 直落后继（后继中唯一非 PUSH_EXC_INFO
#     块）为任一区域 finally_copy_blocks 台账成员或 finally 异常副本体切片
#     同构 ∧ 链尾（≤8 跳）有效运行以 RETURN_VALUE/RETURN_CONST 终结 ∧
#     RETURN 前运行（POP_TOP 剥尾）可重建（副本体保守验证）⇒ 臂末 Expr 原位
#     升格 Return(值)（stmts[-1] is bs[-1] 同一对象），后继副本链登记
#     generated（体语句由 finalbody 机制唯一归属发射，fc_keep=0 抑制不重复）。
#     任一条件不成立逐位落回既有拉入路径（C3）。语言级依据：del/return 不可
#     作子表达式，值尾块运行恒为待返回值；finally 正常副本块属台账/异常副本
#     体同构（CPython 复制语义结构事实）。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
MARKER = 'v158-RETFIN'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s

# ---------- Site: _process_if_blocks RETURN-successor pull ----------
old = """                    if _succ_last and _succ_last.opname == 'RETURN_VALUE':
                        # [R60 Fix1] 识别条件：当前为 then 臂（branch=='then'）、"""
assert s.count(old) == 1, 'succ-pull anchor %d' % s.count(old)

new = """                    if _succ_last and _succ_last.opname == 'RETURN_VALUE':
                        # [v158-RETFIN] try+finally 内联 return 值重组（if 臂
                        # 穿 finally 正常路径副本，B207 同式词汇）：CPython
                        # 3.11 零成本 finally 对 return-in-try 发射 <值求值> +
                        # [finally 正常副本内联] + RETURN_VALUE，返回值驻留栈
                        # 底穿越块界。臂尾值块此前渲染 Expr（既有 Expr→Return
                        # 转换被 _try_depth<=0 门挡住）、副本块被拉入渲染
                        # `return 0`（RETURN 抓副本尾常量，http_error_302 实
                        # 形=真实 R1）。精确形：臂末语句为 Expr ∧ 本块有效运
                        # 行无语句终结符 ∧ 直落后继（唯一非 PUSH_EXC_INFO 块
                        # ——副本起始可跨 CALL CACHE 尾垫，B207 的 +2 判据不
                        # 适用）为 finally_copy_blocks 台账成员或 finally 异常
                        # 副本体切片同构 ∧ 链尾（≤8 跳）RETURN 终结 ∧ RETURN
                        # 前运行可重建 ⇒ 臂末 Expr 原位升格 Return(值)，副本
                        # 链登记 generated（体由 finalbody 机制发射）。任一
                        # 条件不成立逐位落回既有拉入路径。
                        _v158_hit = False
                        if (bs and isinstance(bs[-1], dict)
                                and bs[-1].get('type') == 'Expr'
                                and bs[-1].get('value') is not None):
                            _v158_hit = self._v158_try_arm_return_in_finally(
                                block, _succ)
                        if _v158_hit:
                            _v158_ret = {'type': 'Return',
                                         'value': bs[-1]['value']}
                            if stmts and stmts[-1] is bs[-1]:
                                stmts[-1] = _v158_ret
                            else:
                                stmts.append(_v158_ret)
                            self.generated_blocks.add(_succ)
                            self.generated_offsets.add(_succ.start_offset)
                            break
                        # [R60 Fix1] 识别条件：当前为 then 臂（branch=='then'）、"""
s = s.replace(old, new, 1)

# ---------- New helper method before _process_if_blocks's host or after _b207_return_in_finally_stmts ----------
anchor_helper = """    def _b75_consume_arm_return_copies(self, region: TryExceptRegion) -> None:"""
assert s.count(anchor_helper) == 1, 'helper anchor %d' % s.count(anchor_helper)

helper = """    def _v158_try_arm_return_in_finally(self, value_block: BasicBlock,
                                        first_succ: BasicBlock) -> bool:
        \"\"\"[v158-RETFIN] if 臂值尾块穿 finally 正常路径副本链精确形判定。

        判据（全部块内/台账结构事实，I.4 白名单；B207 同式词汇）：
          ① 值尾块有效运行（剥 RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG）
             非空且无语句终结符（STORE 族/POP_TOP/RETURN/跳转/RAISE/
             IMPORT）——纯值生产运行；
          ② 直落后继链：本块后继中唯一非 PUSH_EXC_INFO 块（异常入口排除；
             副本起始偏移可跨 CALL CACHE 尾垫，不能用 +2 判定）；
          ③ 链逐块（≤8 跳）是任一区域 finally_copy_blocks 台账成员，或
             finally 异常副本体（剥噪/剥 PUSH_EXC_INFO/剥框架尾）的连续
             opcode 切片同构（B207 _is_copy_slice 同一词汇）；
          ④ 链尾块有效运行以 RETURN_VALUE/RETURN_CONST 终结，RETURN 前运
             行（POP_TOP 剥尾）可重建（副本体保守验证）；
          ⑤ 任一条件不成立 → False（调用方逐位落回既有拉入路径，C3）。
        副本体语句由 finalbody/fc_keep 机制唯一归属发射，本方法只读不改块图。
        \"\"\"
        _noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
        _STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
        _terminators = set(_STORE_OPS) | {
            'POP_TOP', 'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',
            'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        } | set(FORWARD_CONDITIONAL_JUMP_OPS) | set(BACKWARD_CONDITIONAL_JUMP_OPS)
        _run = [i for i in value_block.instructions if i.opname not in _noise]
        if not _run:
            return False
        if any(i.opname in _terminators for i in _run):
            return False
        # ② 直落后继：本块后继中唯一非异常入口块
        _norm_succs = []
        for _s in (value_block.successors or []):
            if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
                   for i in _s.instructions):
                continue
            _norm_succs.append(_s)
        if len(_norm_succs) != 1:
            return False
        _regions = getattr(self.region_analyzer, 'regions', None) or ()
        _frame_tail_ops = ('RERAISE', 'COPY', 'POP_EXCEPT', 'SWAP', 'POP_TOP')
        _fc_offsets = set()
        _exc_seqs = []
        for _rg in _regions:
            _fc = getattr(_rg, 'finally_copy_blocks', None) or {}
            _fc_offsets.update(_fc.keys())
            if not getattr(_rg, 'has_finally', False):
                continue
            _fb = getattr(_rg, 'finally_blocks', None) or []
            _seq = []
            for _fb_b in _fb:
                for _i in _fb_b.instructions:
                    if _i.opname in _noise or _i.opname == 'PUSH_EXC_INFO':
                        continue
                    _seq.append(_i.opname)
            while _seq and _seq[-1] in _frame_tail_ops:
                _seq.pop()
            if _seq:
                _exc_seqs.append(_seq)

        def _is_copy_slice(_blk):
            _ops = [i.opname for i in _blk.instructions if i.opname not in _noise]
            while _ops and _ops[-1] in _frame_tail_ops:
                _ops.pop()
            if not _ops:
                return False
            return any(any(_seq[j:j + len(_ops)] == _ops
                           for j in range(len(_seq) - len(_ops) + 1))
                       for _seq in _exc_seqs)

        _cur = _norm_succs[0]
        for _hop in range(8):
            _cur_run = [i for i in _cur.instructions if i.opname not in _noise]
            if not _cur_run:
                return False
            _last = _cur_run[-1]
            if _last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                # ④ RETURN 前运行保守验证（副本体可重建）
                _tail_run = _cur_run[:-1]
                while _tail_run and _tail_run[-1].opname == 'POP_TOP':
                    _tail_run.pop()
                if _tail_run:
                    _tail_re = self.expr_reconstructor.reconstruct(list(_tail_run))
                    if _tail_re is None:
                        return False
                return True
            if _cur.start_offset not in _fc_offsets and not _is_copy_slice(_cur):
                return False
            # 下一跳：本块后继中唯一非异常入口块
            _nxt = []
            for _s2 in (_cur.successors or []):
                if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
                       for i in _s2.instructions):
                    continue
                _nxt.append(_s2)
            if len(_nxt) != 1:
                return False
            _cur = _nxt[0]
        return False

"""
s = s.replace(anchor_helper, helper + anchor_helper, 1)

assert s != orig
assert s.count(MARKER) == 2
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix158 applied: %d markers' % s.count(MARKER))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
