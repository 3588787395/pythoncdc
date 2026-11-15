# -*- coding: utf-8 -*-
"""rr-v5r178 patch — subprocess SP4 FINALLY-ARM: `Popen.__exit__` (74→75/78).

单文件单 anchor（core/cfg/region_ast_generator.py），只增不破。

复查更正（逐指令差分，`r178/work/diff_ex.txt`）：recon170 SP4 卡把差异描述为
「finally 臂尾两条语句丢失」，实测 **AST 里两条语句都在**（`self._sigint_wait_secs
= 0` / `return` 均存在，finally 主臂结构正确）。真实差异是**多出一条幻影语句**：
函数末尾多出

        if TimeoutExpired:
            pass

（产物 107→112 条指令；首个差异 idx=61 原 `LOAD_CONST None; RETURN_VALUE` →
产物 `JUMP_FORWARD to 212`，尾部插入 6 条 `LOAD_GLOBAL/POP_JUMP_FORWARD_IF_FALSE/
LOAD_CONST/RETURN_VALUE`）。它来自 try/finally 的**异常路径副本**：副本内层
try/except 的 IfRegion/TryExceptRegion 因 entry 落在外层 try 的 blocks 里被
top_level 过滤，其 handler 匹配头（`PUSH_EXC_INFO; LOAD_GLOBAL TimeoutExpired;
CHECK_EXC_MATCH; POP_JUMP_FORWARD_IF_FALSE`）既无发射 owner、也不在
generated_blocks，收尾孤儿块 BASIC 区域把它当普通块重建为 `if <Exc>: pass`。

修复谓词：`_generate_block_statements`（块语句重建单一漏斗）在 B86 纯异常协议
块守卫后新增「未发射 TryExceptRegion 的 handler 入口块」守卫——块未生成、首条
非噪声指令为 `PUSH_EXC_INFO`、且块是某个既未生成又不在生成中的 TryExceptRegion
的 `handler_entry_blocks` 成员 ⇒ 整块登记 generated、发射空语句（handler 头的
语义由 try 语句重编译自然再生）。正在生成的区域显式豁免，其 handler 臂仍走
`_generate_handler_body_statements`；已生成区域入口在 `_generate_try` 开头即登记
generated。不命中时逐位保持（C3）。

不触碰 r172 三处 try/finally 判据（region_analyzer 的「try 体块集真子集 /
同入口跨度包含 / 生成侧 span 包含」）——本补丁只在生成端块漏斗加一条未发射
handler 入口的抑制，不改区域识别、不改 finally 归属、不改 _generate_try_body。

Applies with count==1 anchor, utf-8-sig (BOM aware) + newline preserving
(LF-space edit, CRLF restore), py_compile validation and full idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix178.py [--root <repo-root>] [--check]
"""
import argparse
import py_compile

REPO = 'F:/Downloads/pythoncdc-main'

# ---- anchor 1: helper method, inserted before _downstream_region_entry ----
OLD1 = '''            return False
        return _seen_protocol

    def _downstream_region_entry(self, block: BasicBlock, exclude: Any) -> Optional[Any]:
'''

NEW1 = '''            return False
        return _seen_protocol

    def _rag_is_unemitted_try_handler_entry(self, block: BasicBlock) -> bool:
        """[v178-ORPHAN-HDR] 未发射 TryExceptRegion 的 handler 入口块判定。

        ①算法依据：CPython 3.11 的 except 匹配头
        ``PUSH_EXC_INFO; LOAD_GLOBAL <Exc>; CHECK_EXC_MATCH; POP_JUMP_IF_FALSE``
        是异常表机制的组成块，不是用户语句。try 区域生成时由
        ``_generate_try`` 在 handler 块快照处整组登记 generated（每块唯一
        归属）；但 try/finally 的异常路径副本与正常副本结构镜像，区域归约
        把副本的 IfRegion/TryExceptRegion 按「entry 在外层 try 的 blocks 中」
        滤出 top_level，副本内层 try 的 handler 入口块因此既无发射 owner、
        也不在 ``generated_blocks`` 中，收尾的孤儿块 BASIC 区域会把它当普通
        块重建为幻影 ``if <Exc>: pass``（subprocess ``Popen.__exit__`` 实测：
        多 6 条指令，107→112，判官 Different control flow）。
        ②归约顺序：位于 ``_generate_block_statements`` 单一漏斗的 B86 纯
        协议块守卫之后、通用块语句重建之前；命中即整块登记 generated 并
        发射空语句。
        ③唯一归属判定（I.4 白名单：块内 opcode 形态 + 区域成员关系）：
        块未生成、首条非噪声指令为 ``PUSH_EXC_INFO``（3.11 handler 入口
        特征码），且块是某个**未生成/未在生成中** TryExceptRegion 的
        ``handler_entry_blocks`` 成员。已生成区域的入口在 ``_generate_try``
        开头即登记 generated，首条件直接排除；正在生成的区域显式豁免，
        其 handler 臂仍走 ``_generate_handler_body_statements``。
        ④嵌套处理：块级判据，任意宿主/嵌套深度同语义；只作用于漏斗，
        不拆散任何区域。
        ⑤入口引用语义：返回布尔值；True 时调用方登记 generated 并返回
        空语句列表——handler 头的语义由所属 try 语句重编译自然再生。
        ⑥反编译流程：块语句重建漏斗的前置守卫（与 B86 同层）。
        C1 只读块指令 opcode 与区域 handler_entry_blocks 成员关系。
        C2 不新增跨方法状态；``_generated_regions`` / ``_generating_regions``
        为既有生成期集合。
        C3 未命中（已生成 / 正在生成 / 非 handler 入口）时返回 False，行为
        逐位保持。
        """
        if block in self.generated_blocks:
            return False
        _first = None
        for _instr in block.instructions:
            if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG'):
                continue
            _first = _instr
            break
        if _first is None or _first.opname != 'PUSH_EXC_INFO':
            return False
        for _r in self.region_analyzer.regions:
            if not isinstance(_r, TryExceptRegion):
                continue
            if id(_r) in self._generated_regions or id(_r) in self._generating_regions:
                continue
            if any(_hb is block
                   for _hb in (getattr(_r, 'handler_entry_blocks', None) or ())):
                return True
        return False

    def _downstream_region_entry(self, block: BasicBlock, exclude: Any) -> Optional[Any]:
'''

# ---- anchor 2: consume the guard in the single funnel ----
OLD2 = '''        if self._rag_is_pure_exception_protocol_block(block):
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return []
        # [R5-B119 loopsink] 循环/for-iter 尾出口的相邻双隐式 return None sink 对
'''

NEW2 = '''        if self._rag_is_pure_exception_protocol_block(block):
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return []
        # [v178-ORPHAN-HDR] 未发射 try 区域的 handler 入口块不是语句（单一
        # 漏斗）：try/finally 异常路径副本的内层 try 被区域归约滤出 top_level
        # 后，其 handler 匹配头（PUSH_EXC_INFO / LOAD_GLOBAL <Exc> /
        # CHECK_EXC_MATCH / 条件跳转）成为无 owner 的孤儿块，经通用块重建变成
        # 幻影 `if <Exc>: pass`（subprocess Popen.__exit__ 实测多 6 条指令，
        # 107→112）。判据与豁免面全在 _rag_is_unemitted_try_handler_entry 的
        # docstring 里；本漏斗是唯一消费端。C3：未命中逐位保持。
        if self._rag_is_unemitted_try_handler_entry(block):
            self.generated_blocks.add(block)
            self.generated_offsets.add(block.start_offset)
            return []
        # [R5-B119 loopsink] 循环/for-iter 尾出口的相邻双隐式 return None sink 对
'''

PATCHES = [
    ('core/cfg/region_ast_generator.py', [(OLD1, NEW1), (OLD2, NEW2)]),
]


def _apply(path, pairs, check=False):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    crlf = '\r\n' in text
    norm = text.replace('\r\n', '\n')
    done = 0
    for old, new in pairs:
        c_old, c_new = norm.count(old), norm.count(new)
        if c_old == 1:
            norm = norm.replace(old, new, 1)
            done += 1
        elif c_old == 0 and c_new >= 1:
            continue
        else:
            raise SystemExit('ANCHOR-FAIL %s old=%d new=%d\n%r'
                             % (path, c_old, c_new, old[:200]))
    out = norm.replace('\n', '\r\n') if crlf else norm
    data = out.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    if not check:
        open(path, 'wb').write(data)
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=REPO)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    total = 0
    for rel, pairs in PATCHES:
        p = args.root.rstrip('/') + '/' + rel
        n = _apply(p, pairs, check=args.check)
        total += n
        print('%s: %d hunk(s) %s' % (rel, n, 'already-applied'
                                     if n == 0 else 'patched'))
    for rel, _ in PATCHES:
        p = args.root.rstrip('/') + '/' + rel
        py_compile.compile(p, doraise=True)
    print('py_compile OK; total patched hunks = %d' % total)


if __name__ == '__main__':
    main()
