# -*- coding: utf-8 -*-
"""Emit the R49-A spec (shared sink-tail merge) for build2.py."""
import io
import json

HELPER = '''    def _r49a_shared_sink_tail_merge(self, header: BasicBlock,
                                     then_succ: BasicBlock,
                                     else_succ: BasicBlock,
                                     struct_blocks) -> Optional[BasicBlock]:
        """ 区域归约算法原则 1（块 = 前导语句 + 唯一终止符）+ 原则 2（每块唯一归属，
        且归属者必须发射该块）：merge 兜底退化为 else_succ 之前，先找两臂真正汇合的
        「公共 sink 尾块」。

        失败模式（klinedata.get_history_new 偏移 298 的 if）：and 短路链的 then 臂以嵌套
        if/else 结束，两条内层臂的出口块都 JUMP_FORWARD 到函数尾部 `return <var>` 块；
        else_succ 是 else 体首块而非汇合点。NCPD 因臂内有 return 而为 None，
        _compute_merge_from_jump_targets 只读 then_succ 自身的 JUMP_FORWARD 也为 None，
        于是兜底把 merge 绑到 else_succ；_collect_branch_blocks 遂沿 then 臂越过真实
        汇合点，把函数尾部 return 块吸入臂内 ⇒ 尾部 return 被重复发射（臂内一次、函数
        末尾隐式 return None 一次），strict seq_len +1 且末尾 LOAD_CONST None。

        判据全为结构事实：① else_succ 不在 then 臂前向闭包内（闭包不越过条件结构块）；
        ② 候选块 t ∈ 闭包、不属于条件结构块，其终结符为 return/raise 族且无正常流后继
        （纯 sink 尾）；③ t 有前驱 p 既不在闭包内也不属于条件结构块，且 p 不经闭包即可
        由 else_succ 前向到达 ⇒ p 是另一臂汇入 t 的路径；④ 满足 ①..③ 的 t 唯一。
        四条一起才证明 else_succ 不是汇合点而 t 是。命中返回 t（调用方以 t 作 merge），
        未命中返回 None ⇒ 逐字保留原兜底世界。
        """
        _r49a_struct = set(struct_blocks or ())
        for _r49a_b in (header, then_succ, else_succ):
            if _r49a_b is not None:
                _r49a_struct.add(_r49a_b)
        _r49a_closure = set()
        _r49a_work = [then_succ]
        while _r49a_work:
            _r49a_b = _r49a_work.pop()
            if _r49a_b in _r49a_closure:
                continue
            _r49a_closure.add(_r49a_b)
            for _r49a_s in (_r49a_b.successors or []):
                if _r49a_s in _r49a_struct or _r49a_s in _r49a_closure:
                    continue
                _r49a_work.append(_r49a_s)
        if else_succ in _r49a_closure:
            return None
        _r49a_outside = set()
        _r49a_work = [else_succ]
        while _r49a_work:
            _r49a_b = _r49a_work.pop()
            if _r49a_b in _r49a_outside or _r49a_b in _r49a_closure:
                continue
            _r49a_outside.add(_r49a_b)
            for _r49a_s in (_r49a_b.successors or []):
                if _r49a_s in _r49a_closure or _r49a_s in _r49a_outside:
                    continue
                _r49a_work.append(_r49a_s)
        _r49a_cands = []
        for _r49a_b in _r49a_closure:
            if _r49a_b in _r49a_struct:
                continue
            _r49a_last = _r49a_b.get_last_instruction()
            if (_r49a_last is None
                    or _r49a_last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                 'RAISE_VARARGS', 'RERAISE')):
                continue
            _r49a_e = getattr(_r49a_b, 'exception_successors', set()) or set()
            if [s for s in (_r49a_b.successors or []) if s not in _r49a_e]:
                continue
            if any(_r49a_p in _r49a_outside and _r49a_p not in _r49a_struct
                   for _r49a_p in (_r49a_b.predecessors or [])):
                _r49a_cands.append(_r49a_b)
        if len(_r49a_cands) != 1:
            return None
        return _r49a_cands[0]

'''

A1 = "    def _compute_merge_from_jump_targets(self, header: BasicBlock,"
E1 = {'anchor': A1, 'repl': HELPER + A1}

A2 = ("                            if _else_has_external_pred:\n"
      "                                merge = else_succ\n")
R2 = ("                            if _else_has_external_pred:\n"
      "                                _r49a_tail = self._r49a_shared_sink_tail_merge(\n"
      "                                    block, then_succ, else_succ, _if_struct_blocks)\n"
      "                                merge = (_r49a_tail if _r49a_tail is not None\n"
      "                                         else else_succ)\n")
E2 = {'anchor': A2, 'repl': R2}

A3 = ("# 原逻辑设 merge=408，else_blocks=[]，IF_ELIF_CHAIN 无法创建。\n"
      "                merge = else_succ\n")
R3 = ("# 原逻辑设 merge=408，else_blocks=[]，IF_ELIF_CHAIN 无法创建。\n"
      "                _r49a_tail = self._r49a_shared_sink_tail_merge(\n"
      "                    block, then_succ, else_succ,\n"
      "                    {block, then_succ, else_succ} | chain_blocks)\n"
      "                merge = (_r49a_tail if _r49a_tail is not None\n"
      "                         else else_succ)\n")
E3 = {'anchor': A3, 'repl': R3}

spec = {'file': 'core/cfg/region_analyzer.py', 'edits': [E1, E2, E3]}
io.open(r'D:/Temp/r49mine/spec_r49a.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('spec written, 3 edits')
