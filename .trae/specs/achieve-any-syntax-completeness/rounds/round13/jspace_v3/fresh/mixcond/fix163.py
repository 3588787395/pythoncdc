# -*- coding: utf-8 -*-
"""rr-v5r163 fix: for-iter BoolOp 归属门控（v163-FORITERBOUND）。

只改 core/cfg/region_ast_generator.py：
  1) 新增私有谓词 _v163_boolop_iter_source_ok(merge_block)
  2) _loop_generate_for 的 BoolOp-for-iter 候选筛选 + 同一 fallback 归属处调用该谓词
  3) _generate_boolop 的镜像 iter-context 分支调用同一谓词

不命中时逐字节保持现状（C3）；可重复执行（已打补丁则跳过）；写回 utf-8-sig（保留 BOM）。
"""
import os
import py_compile
import sys

TARGET = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'

HELPER_ANCHOR = """    def _loop_generate_for(self, region: LoopRegion) -> Dict[str, Any]:
        pre_stmts = []
"""

HELPER_PATCH = '''    def _v163_boolop_iter_source_ok(self, merge_block) -> bool:
        """[v163-FORITERBOUND] BoolOpRegion 的 merge 块是否真能整块充当 for 的 iterable。

        区域归约算法原则 4（父引用子入口）把 ``for x in (a or b):`` 的
        BoolOpRegion 当 iter 表达式，前提是 merge 块就是 GET_ITER 块。但基本块
        是语句边界之上的粒度：上一条赋值语句的写回 ``STORE_*`` 与下一条 ``for``
        的 ``LOAD iterable; GET_ITER`` 可以落在同一块（urllib.request.FTPHandler.
        ftp_open 的 B=696-700：``STORE_FAST type`` / ``LOAD_FAST attrs`` /
        ``GET_ITER``）。此时 merge 身份相同，但该 BoolOp 并非 iterable 来源，
        整条链被误当 iter_expr，真正的 iterable 装载被越过（for-iterable 提取
        在基本块粒度越界）。

        判据（I.4 白名单：只读本块指令 opcode 序列，不涉及名字/偏移/区域类型）：
          ① 取块内最后一个 GET_ITER/GET_AITER 作迭代器设置点；
          ② 该点之前的迭代对象装载段内不得出现语句消费指令 ``STORE_*`` /
             ``POP_TOP`` —— 它们表示上一条语句在本块写回/丢弃，块首因此不属于
             本 for 的 iterable。两个例外都维持既有归属（不改变文本）：
             ``COPY`` 紧邻的单个 ``STORE_*`` 是 walrus（``for x in (n := a or b)``）
             的值保留写回；相邻两次及以上 ``STORE_*`` 是链式同值多目标
             （``first = last = flag or next(it)``），写回值即 BoolOp 结果。
             其余 ``STORE_*`` / ``POP_TOP`` 一律拒绝。
        块内无 GET_ITER（无法证明语句边界）时返回 True，保持既有行为（C3）。
        不命中返回 False，调用方落回既有 _loop_extract_for_iter_pre_stmts 的
        指令级拆分路径（前缀语句留循环前，GET_ITER 前段作 iterable）。
        """
        if merge_block is None:
            return True
        _noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
        _v163_instrs = [i for i in merge_block.instructions
                        if i.opname not in _noise]
        _v163_last_iter_idx = -1
        for _v163_i, _v163_ins in enumerate(_v163_instrs):
            if _v163_ins.opname in ('GET_ITER', 'GET_AITER'):
                _v163_last_iter_idx = _v163_i
        if _v163_last_iter_idx < 0:
            return True
        _v163_pre = _v163_instrs[:_v163_last_iter_idx]
        # 链式同值多目标（`first = last = flag or next(it)`）：块内相邻两次
        # STORE_* 写回同一值，该值就是 BoolOp 结果，整块归属保持既有行为。
        for _v163_ci in range(len(_v163_pre) - 1):
            if (_v163_pre[_v163_ci].opname.startswith('STORE_')
                    and _v163_pre[_v163_ci + 1].opname.startswith('STORE_')):
                return True
        _v163_prev = None
        for _v163_ins in _v163_pre:
            if _v163_ins.opname == 'POP_TOP':
                return False
            if _v163_ins.opname.startswith('STORE_'):
                # COPY 紧邻的 STORE_* 是 walrus（`for x in (n := a or b)`）的
                # 值保留写回：值仍留在栈顶供 GET_ITER 消费，不是语句边界。
                # 其余 STORE_* 一律视为上一条语句的写回。
                if not (_v163_prev is not None and _v163_prev.opname == 'COPY'):
                    return False
            _v163_prev = _v163_ins
        return True

    def _loop_generate_for(self, region: LoopRegion) -> Dict[str, Any]:
        pre_stmts = []
'''

SITE1_ANCHOR = """            for _r in self.region_analyzer.regions:
                if (isinstance(_r, BoolOpRegion) and _r.merge_block is not None
                        and _r.merge_block is for_iter_setup):
                    _boolop_for_iter = _r
                    break
"""

SITE1_PATCH = """            for _r in self.region_analyzer.regions:
                if (isinstance(_r, BoolOpRegion) and _r.merge_block is not None
                        and _r.merge_block is for_iter_setup
                        and self._v163_boolop_iter_source_ok(_r.merge_block)):
                    _boolop_for_iter = _r
                    break
"""

SITE2_ANCHOR = """            if _boolop_for_iter is None:
                _fis_owner_b = self.region_analyzer.get_region_for_block(for_iter_setup)
                if isinstance(_fis_owner_b, BoolOpRegion):
                    _boolop_for_iter = _fis_owner_b
"""

SITE2_PATCH = """            if _boolop_for_iter is None:
                _fis_owner_b = self.region_analyzer.get_region_for_block(for_iter_setup)
                if (isinstance(_fis_owner_b, BoolOpRegion)
                        and (getattr(_fis_owner_b, 'merge_block', None) is not for_iter_setup
                             or self._v163_boolop_iter_source_ok(for_iter_setup))):
                    _boolop_for_iter = _fis_owner_b
"""

SITE3_ANCHOR = """            for _lr in self.region_analyzer.regions:
                if (isinstance(_lr, LoopRegion)
                        and _lr.region_type == RegionType.FOR_LOOP
                        and _lr.metadata.get('for_iter_setup') is region.merge_block):
"""

SITE3_PATCH = """            for _lr in self.region_analyzer.regions:
                if (isinstance(_lr, LoopRegion)
                        and _lr.region_type == RegionType.FOR_LOOP
                        and _lr.metadata.get('for_iter_setup') is region.merge_block
                        and self._v163_boolop_iter_source_ok(region.merge_block)):
"""

MARKER = '_v163_boolop_iter_source_ok'

SITE4_ANCHOR = """                            if _before_with_idx is not None:
                                _post_store_clean = []
"""

SITE4_PATCH = """                            if _before_with_idx is not None:
                                _post_store_clean = []
                            # [v163-FORITERBOUND] 每块唯一归属：merge 块同时是
                            # 某 LoopRegion 的 for_iter_setup（块尾 GET_ITER 或
                            # GET_AITER）时，STORE_* 之后的 `LOAD iterable;
                            # GET_ITER` 归属该循环的迭代器提取
                            # （_loop_generate_for → _loop_extract_for_iter_pre_stmts），
                            # 本 BoolOp 区域不得再发射为裸表达式（否则 for 前多
                            # 一条 `attrs`/`b` Expr，判官 Different bytecode）。
                            # 判据只读块尾 opcode + 区域归属事实，不依赖名字/偏移。
                            _v163_mb_last = (region.merge_block.get_last_instruction()
                                             if region.merge_block is not None else None)
                            if (_v163_mb_last is not None
                                    and _v163_mb_last.opname in ('GET_ITER', 'GET_AITER')):
                                for _v163_lr in self.region_analyzer.regions:
                                    if (isinstance(_v163_lr, LoopRegion)
                                            and _v163_lr.metadata.get('for_iter_setup') is region.merge_block):
                                        _post_store_clean = []
                                        break
"""


def main():
    with open(TARGET, 'r', encoding='utf-8-sig', newline='') as _f:
        _raw = _f.read()
    # git core.autocrlf=true 下 checkout 可能把工作树改成 CRLF；统一按任务初始
    # 工作树（LF + BOM）回写，锚点与替换一律在 LF 文本上进行，保证可重复执行。
    src = _raw.replace('\r\n', '\n').replace('\r', '\n')

    if MARKER in src:
        print('[fix163] already applied; nothing to do')
        py_compile.compile(TARGET, doraise=True)
        print('[fix163] py_compile OK')
        return 0

    edits = [
        ('helper', HELPER_ANCHOR, HELPER_PATCH),
        ('site1-loopy-for-iter', SITE1_ANCHOR, SITE1_PATCH),
        ('site1b-loop-fallback', SITE2_ANCHOR, SITE2_PATCH),
        ('site3-boolop-mirror', SITE3_ANCHOR, SITE3_PATCH),
        ('site4-boolop-post-store', SITE4_ANCHOR, SITE4_PATCH),
    ]
    for _name, _anchor, _patch in edits:
        _n = src.count(_anchor)
        if _n != 1:
            print('[fix163] FATAL anchor %s count=%d (expected 1)' % (_name, _n))
            return 2
        src = src.replace(_anchor, _patch, 1)
        print('[fix163] patched %s (anchor count=1)' % _name)

    with open(TARGET, 'w', encoding='utf-8-sig', newline='') as _f:
        _f.write(src)

    py_compile.compile(TARGET, doraise=True)
    print('[fix163] py_compile OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
