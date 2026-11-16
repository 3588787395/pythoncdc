# -*- coding: utf-8 -*-
"""rr-v5r184 补丁：tarfile `_FileInFile.read` 闭合（M1 + M2 同改）。

三个编辑（全部为「窄谓词 + 封闭守卫」，不命中时逐位保持既有行为）：

  E1 [v184-NOPCOAL]  core/cfg/region_analyzer.py
     `_coalesce_nop_prefix_loop_headers`：NOP-only 循环头 B_h 的唯一后继 B_r
     本身已是循环头且有**自己的回边**时，不把 B_h 的回边重定向到 B_r。
     原行为使外层 while 的回边被并到内层 while True 的 header（两个循环共
     header），`_collect_natural_loop_body` 取并集 ⇒ 外层 while 降为 if。
     判据只用回边表与块身份（`any(tgt is succ)`）。

  E2 [v184-WTCHAIN-HDR]  core/cfg/region_analyzer.py
     `_should_skip_block_for_if_region`：while 循环 header 且
     `condition_block is None`（`while True`）且该块自身是比较链首块
     （COPY(2)+COMPARE_OP 且 compare_ops ≥ 2）时，不再按 W43 循环结构跳过，
     交回 `_build_basic_if_region`（`while cond: if a<b<c:` 已在用的既有链
     式比较归约路径，含 then/else 收集与清理块剥离）。

  E3 [v184-WTCHAIN-EMIT]  core/cfg/region_ast_generator.py
     `_loop_handle_header`：`while True` 的 header 块恰是上述链式比较
     IfRegion 的 entry 时，先在循环体首部把该 IfRegion 整树生成（嵌套即
     抽象节点），再按既有路径继续。原实现只有 `condition_block is not None`
     的 header 才派发嵌套 IfRegion，`while True` 体首的链式比较条件因此
     退化为 `if <第二比较操作数>:`。

用法：
  python -I -X utf8 fix184.py            # 打补丁（幂等：已打则跳过）
  python -I -X utf8 fix184.py --revert   # 反向撤销（与打补丁往返 sha 一致）
  python -I -X utf8 fix184.py --check    # 只报告每个编辑的命中次数
"""
from __future__ import annotations

import hashlib
import io
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'

E1_OLD = """                if _succ in self.loop_analyzer.loop_headers and _succ != h:
                    _nop_headers.append((h, _succ))
"""
E1_NEW = """                if _succ in self.loop_analyzer.loop_headers and _succ != h:
                    # [v184-NOPCOAL] 区域归约算法原则 2（每块唯一归属）：
                    # NOP 头 B_h 的唯一后继 B_r 若是**自己的**循环头（回边表里
                    # 已有目标 == B_r 的回边），则 B_h 是外层循环的回边落点、
                    # 不是 B_r 的纯前缀占位。此时把 B_h 的回边改指 B_r 会让
                    # 内外两层循环共用 header，`_collect_natural_loop_body`
                    # 只取并集 ⇒ 外层 while 整体降为 if（tarfile
                    # `_FileInFile.read` 的外层 `while size > 0:` 实测）。
                    # 判据只读回边表（src,tgt 块身份）与 header 的后继身份；
                    # 未命中（B_r 无自身回边）时逐位维持既有合并行为（C3）。
                    if any(tgt is _succ for _src, tgt in self.loop_analyzer.back_edges):
                        continue
                    _nop_headers.append((h, _succ))
"""

E2_OLD = """        if isinstance(block_region, LoopRegion):
            if block == block_region.condition_block:
                return True
"""
E2_NEW = """        if isinstance(block_region, LoopRegion):
            # [v184-WTCHAIN-HDR] 区域归约算法原则 2（每块唯一归属）+ 原则 3
            # （嵌套即抽象节点）：`while True:` 的体首块同时是本循环 header 与
            # 比较链首块时，该块承载的是**体内** `if a < b < c:` 条件（回边在
            # 链后独立块上），不是回边条件重检副本。W43 的 header 守卫按
            # 「无 condition_block 的 header」一律跳过，使链式比较区域建不出、
            # 下游只按第二比较块重建 `if <第二操作数>:`（tarfile
            # `_FileInFile.read` 的 `if start <= self.position < stop:` 实测）。
            # 判据只用本块结构事实：header 身份 + condition_block 缺席 +
            # `_is_chained_compare_header` 的 COPY(2)+COMPARE_OP 指令对 +
            # `_detect_chained_compare_pattern` 的 compare_ops ≥ 2。放行后
            # 交既有 `_build_basic_if_region`（`while cond: if a<b<c:` 同一条
            # 归约路径，含清理块剥离与 then/else 收集）；未命中时逐位保持
            # 既有跳过（守卫封闭，C3）。
            if (block == block_region.header_block
                    and block_region.condition_block is None
                    and self._is_chained_compare_header(block)):
                _v184_cc_info = self._detect_chained_compare_pattern(block)
                if (_v184_cc_info
                        and len(_v184_cc_info.get('compare_ops') or []) >= 2):
                    return False
            if block == block_region.condition_block:
                return True
"""

E3_OLD = """        _header_region = self.region_analyzer.get_region_for_block(block)
        if _header_if_region is None:
"""
E3_NEW = """        # [v184-WTCHAIN-EMIT] 区域归约算法原则 3（嵌套即抽象节点）+ 原则 4
        # （父引用子入口）：`while True:` 的 header 块恰是比较链 IfRegion 的
        # entry 时，该 IfRegion 是循环体的**首条语句**。下方 header 派发只对
        # `condition_block is not None` 的循环派发嵌套 IfRegion（回边重检
        # 形态），`while True` 因 condition_block 缺席落到逐指令兜底，链式
        # 比较条件被截成 `if <第二比较操作数>:`。此处按同一「父引用子入口」
        # 语义先整树生成该 IfRegion（含其条件块的块内前缀语句），再按既有
        # 路径继续；判据只用本层结构事实：WHILE_LOOP + condition_block 缺席
        # + header 身份 + 子区域 entry 同一性 + chained_compare_ops 长度 ≥ 2。
        # 未命中（其它任何 header 形态）时逐位维持既有派发（C3）。
        _v184_chain_if = None
        for _v184_child in region.iter_descendants((IfRegion,)):
            if (_v184_child.entry is block
                    and getattr(_v184_child, 'chained_compare_ops', None)
                    and len(_v184_child.chained_compare_ops) >= 2):
                _v184_chain_if = _v184_child
                break
        if (_v184_chain_if is not None
                and region.region_type == RegionType.WHILE_LOOP
                and region.condition_block is None
                and block is region.header_block):
            _v184_if_id = id(_v184_chain_if)
            if (_v184_if_id not in self._generated_regions
                    and _v184_if_id not in self._generating_regions):
                _v184_if_ast = self._generate_if(_v184_chain_if)
                if _v184_if_ast:
                    if isinstance(_v184_if_ast, list):
                        body_stmts.extend(_v184_if_ast)
                    else:
                        body_stmts.append(_v184_if_ast)
                for _v184_cb in _v184_chain_if.blocks:
                    self.generated_blocks.add(_v184_cb)
                self._generated_regions.add(_v184_if_id)
            self.generated_blocks.add(block)
            return
        _header_region = self.region_analyzer.get_region_for_block(block)
        if _header_if_region is None:
"""

EDITS = [
    ('core/cfg/region_analyzer.py', 'v184-NOPCOAL', E1_OLD, E1_NEW),
    ('core/cfg/region_analyzer.py', 'v184-WTCHAIN-HDR', E2_OLD, E2_NEW),
    ('core/cfg/region_ast_generator.py', 'v184-WTCHAIN-EMIT', E3_OLD, E3_NEW),
]


def read_text(path):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    return text, bom


def write_text(path, text, bom):
    data = text.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    with open(path, 'wb') as f:
        f.write(data)


def eol_of(text):
    return '\r\n' if '\r\n' in text else '\n'


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    mode = 'apply'
    if '--revert' in sys.argv:
        mode = 'revert'
    elif '--check' in sys.argv:
        mode = 'check'
    os.chdir(REPO)
    texts, boms = {}, {}
    for rel in {e[0] for e in EDITS}:
        texts[rel], boms[rel] = read_text(rel)
    before = {rel: sha(rel) for rel in texts}

    order = EDITS if mode != 'revert' else list(reversed(EDITS))
    errors = 0
    touched = set()
    for rel, key, old, new in order:
        text = texts[rel]
        eol = eol_of(text)
        o = old.replace('\n', eol)
        n = new.replace('\n', eol)
        if mode == 'revert':
            o, n = n, o
        c_old, c_marker = text.count(o), text.count(key)
        print('%-32s %-20s marker=%d old_count=%d' % (rel, key, c_marker, c_old))
        if mode == 'check':
            continue
        if mode == 'apply' and c_marker:
            print('SKIP   %s %s（已打补丁）' % (rel, key))
            continue
        if mode == 'revert' and not c_marker:
            print('SKIP   %s %s（未打补丁）' % (rel, key))
            continue
        if c_old != 1:
            print('ERROR  %s %s 锚点命中 %d 次（要求恰 1 次）' % (rel, key, c_old))
            errors += 1
            continue
        texts[rel] = text.replace(o, n, 1)
        touched.add(rel)
    if mode == 'check':
        return 0
    if errors:
        print('ABORT  未写入任何文件')
        return 2

    # 内存态语法预检
    for rel in touched:
        try:
            compile(texts[rel], rel, 'exec')
        except SyntaxError as exc:
            print('SYNTAX-ERROR %s: %s line %s' % (rel, exc.msg, exc.lineno))
            return 3

    _tmpdir = tempfile.mkdtemp(prefix='fix184_')
    for rel in sorted(touched):
        write_text(rel, texts[rel], boms[rel])
        py_compile.compile(rel, cfile=os.path.join(_tmpdir, 'check.pyc'),
                          doraise=True)
        print('WRITE  %-32s sha %s -> %s' % (rel, before[rel][:16], sha(rel)[:16]))
    for rel in sorted(set(before) - touched):
        print('KEEP   %-32s sha %s' % (rel, before[rel][:16]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
