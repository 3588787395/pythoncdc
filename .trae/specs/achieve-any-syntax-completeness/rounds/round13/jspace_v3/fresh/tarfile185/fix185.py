# -*- coding: utf-8 -*-
"""r185 patch: shared post-try break for TarFile.next.

Edits only core/cfg/region_ast_generator.py:
  E1  loop break-target repair + nested else-entry repair (after analyze)
  E2  expand marked Try to [Try, Break] in LoopRegion body
  E3  helper methods (_v185_try_shared_loop_break / _v185_split_shared_break)
  E4  compute shared break target before handlers are consumed
  E5  strip duplicated arm-tail Break and mark the Try

Usage: python -I -X utf8 fix185.py [--check|--revert]
"""
import hashlib
import io
import os
import py_compile
import sys

REL = 'core/cfg/region_ast_generator.py'
ROOT = os.environ.get('R185_ROOT') or r'F:\Downloads\pythoncdc-main'
PATH = ROOT + '\\' + REL.replace('/', '\\')
MARKERS = ('[v185-SHARED-EXIT]', '[v185-NESTED-ELSE-ENTRY]',
           '[v185-SHARED-BREAK]')


EDITS = [
    ('v185-SHARED-EXIT+L2', '        self.regions = self.region_analyzer.analyze()\n\n        entry_block = self.cfg.entry_block\n', "        self.regions = self.region_analyzer.analyze()\n\n        # [v185-SHARED-EXIT] 循环 break 落点若被**循环之后的 IfRegion**认领\n        # （其 entry 不在 LoopRegion.blocks 中），该块是 break 之后的续行\n        # if 体，不是 break 落点本身。R102 子区域有界 DFS 从 try/handler\n        # 清理蹦床深入循环外代码时会把 post-loop if 的 then 块误注册为\n        # 第二个 break 落点（tarfile TarFile.next：548→1250→1256），使\n        # LoopRegion 认领循环外语句、break 发射位置错位。归约方式：仅把\n        # 该块从循环 break/块集合摘除（块归属仍是其 IfRegion，不改\n        # block_to_region），并同步 generator 元数据；判据只读 break 块\n        # 的宿主区域与 entry 成员关系，不命中时逐位不变。\n        for _lr in self.regions:\n            if not isinstance(_lr, LoopRegion):\n                continue\n            _lr_body = set(_lr.body_blocks or [])\n            if _lr.header_block is not None:\n                _lr_body.add(_lr.header_block)\n            if _lr.condition_block is not None:\n                _lr_body.add(_lr.condition_block)\n            for _b in list(_lr.break_blocks or []):\n                if _b in _lr_body or _b is _lr.back_edge_block:\n                    continue\n                _br = next((ir for ir in self.regions\n                            if isinstance(ir, IfRegion)\n                            and (_b in (ir.then_blocks or [])\n                                 or _b in (ir.else_blocks or []))), None)\n                if _br is None or _br.entry is None:\n                    continue\n                if _br.entry in (_lr.blocks or set()):\n                    continue\n                # 仅命中「post-loop if 的 then 体」这一形态：then 块唯一\n                # 前驱就是该 if 的条件块，且块内含用户语句（调用/属性/\n                # 存储等），不是纯跳转/清理型真 break 落点。\n                _preds = set(getattr(_b, 'predecessors', None) or ())\n                if (len(_preds) != 1\n                        or _br.condition_block not in _preds):\n                    continue\n                _b_user = [i for i in _b.instructions\n                           if i.opname not in NOISE_OPS\n                           and i.opname not in PURE_JUMP_OPS\n                           and i.opname not in CONDITIONAL_JUMP_OPS\n                           and i.opname not in ('POP_TOP', 'EXTENDED_ARG',\n                                                'POP_EXCEPT', 'LOAD_CONST',\n                                                'STORE_FAST', 'DELETE_FAST',\n                                                'STORE_NAME', 'DELETE_NAME',\n                                                'STORE_ATTR', 'RETURN_VALUE',\n                                                'RETURN_CONST', 'RERAISE')]\n                if not _b_user:\n                    continue\n                _lr.break_blocks = [x for x in _lr.break_blocks if x is not _b]\n                _lr.blocks = set(_lr.blocks or set()) - {_b}\n                # 块归属交还其真实宿主 IfRegion（每块唯一归属）；否则\n                # block_to_region 仍指向 LoopRegion，生成端会在 IfRegion\n                # 之前抢先发射 then 体（TarFile.next 的 append 提前）。\n                self.region_analyzer.block_to_region[_b] = _br\n                _bbp = [x for x in (_lr.metadata.get('break_blocks_precise') or [])\n                        if x is not _b]\n                _lr.metadata['break_blocks_precise'] = _bbp\n                if self.region_analyzer.block_roles.get(_b.start_offset) in (\n                        BlockRole.BREAK, BlockRole.PURE_BREAK):\n                    self.region_analyzer.block_roles[_b.start_offset] = BlockRole.IF_THEN\n\n\n        # [v185-NESTED-ELSE-ENTRY] 区域归约算法原则 2/3/4：当某 IfRegion 的\n        # 条件假出口块本身就是另一个既有 IfRegion 的条件入口（嵌套 if 条件，\n        # 如 except 体内的 `elif offset == 0: raise`），该入口必须作为父\n        # IfRegion 的 else 臂引用节点保留。构建期 in-loop 过滤会把它当作\n        # 「不在循环体/不离开循环」的块剔除，只留下子 if 的 then 体与清理\n        # 块——父 else 臂于是吞掉子 if 的体，生成端把 raise 提升为无条件\n        # 语句、子条件退化为死 `pass`（tarfile TarFile.next：586 else 丢\n        # 716）。本修复在 analyze 全部落定后仅补回该入口引用（不改\n        # block_to_region：子 IfRegion 仍是其 body 的唯一 owner），判据只读\n        # 条件块末跳转目标、既有 IfRegion 入口映射、merge 未定与成员关系，\n        # 不命中时逐位不变。\n        for _ir in self.regions:\n            if not isinstance(_ir, IfRegion) or _ir.condition_block is None:\n                continue\n            if getattr(_ir, 'merge_block', None) is not None:\n                continue\n            # 只修 except 臂内的嵌套 if 条件（父条件块归属 TryExceptRegion\n            # 的 handler 域）；try 体/其它作用域的 else 臂维持既有归约。\n            _owner_try = self.region_analyzer.block_to_region.get(\n                _ir.condition_block)\n            if not isinstance(_owner_try, TryExceptRegion):\n                continue\n            if not any(_ir.condition_block in _hbs\n                       for _exc, _name, _hbs in (_owner_try.except_handlers or [])):\n                continue\n            _ir_last = _ir.condition_block.get_last_instruction()\n            if (_ir_last is None or _ir_last.opname not in CONDITIONAL_JUMP_OPS\n                    or _ir_last.argval is None):\n                continue\n            _es = self.cfg.get_block_by_offset(_ir_last.argval)\n            if _es is None:\n                continue\n            _child = self.region_analyzer._ifregion_by_entry.get(_es)\n            if (_child is None or _child is _ir\n                    or _es in (_ir.else_blocks or [])\n                    or _es in (_ir.blocks or set())\n                    or _es in (_ir.then_blocks or [])):\n                continue\n            _ir.else_blocks = [_es] + list(_ir.else_blocks or [])\n            _ir.blocks = set(_ir.blocks or set()) | {_es}\n\n        entry_block = self.cfg.entry_block\n"),
    ('v185-SHARED-BREAK-SPLIT', "            if _child_has_break_to_outer:\n                body_stmts.append({'type': 'Break'})\n\n        return body_stmts\n\n    def _loop_collect_child_regions", "            if _child_has_break_to_outer:\n                body_stmts.append({'type': 'Break'})\n\n        # [v185-SHARED-BREAK] 把带标记的 Try 展开为 Try 后随共享 Break。\n        return self._v185_split_shared_break(body_stmts)\n\n    def _loop_collect_child_regions"),
    ('v185-HELPERS', '    def _generate_try(self, region: TryExceptRegion) -> Dict[str, Any]:\n', '    def _v185_try_shared_loop_break(self, region):\n        """[v185-SHARED-BREAK] try/handler 共享的 post-try break 落点判定。\n\n        识别条件：try 在 LoopRegion 内、无 finally；所有 handler 的正常\n        出口（块末无条件前向跳转且落点不在本 region.blocks 内）以及\n        try-else 蹦床指向**同一个**循环外落点，且该落点不在循环块集中。\n        命中返回该落点块，否则 None。只读区域成员/块末跳转/落点归属。\n        """\n        loop = region.find_enclosing_parent((LoopRegion,))\n        if (loop is None or getattr(region, \'has_finally\', False)\n                or not region.except_handlers):\n            return None\n        targets = set()\n        n_exit = 0\n        for _exc, _name, hblocks in region.except_handlers:\n            for hb in hblocks:\n                last = hb.get_last_instruction()\n                if (last is not None\n                        and last.opname in (\'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')\n                        and last.argval is not None):\n                    tgt = self.cfg.get_block_by_offset(last.argval)\n                    if tgt is not None and tgt not in region.blocks:\n                        targets.add(tgt)\n                        n_exit += 1\n        for eb in (region.else_blocks or []):\n            last = eb.get_last_instruction()\n            if (last is not None\n                    and last.opname in (\'JUMP_FORWARD\', \'JUMP_ABSOLUTE\')\n                    and last.argval is not None):\n                tgt = self.cfg.get_block_by_offset(last.argval)\n                if tgt is not None and tgt not in region.blocks:\n                    targets.add(tgt)\n        if len(targets) != 1 or n_exit < 2:\n            return None\n        tgt = next(iter(targets))\n        if tgt in (loop.blocks or set()):\n            return None\n        return tgt\n\n    def _v185_split_shared_break(self, node):\n        """把带 `_v185_shared_break` 标记的 Try 展开为 [Try, Break]。\n\n        仅在 LoopRegion 体语句列表上调用；递归进入普通语句的 body/\n        orelse/finalbody/handlers，标记节点处就地追加共享 Break。\n        """\n        if isinstance(node, list):\n            out = []\n            for x in node:\n                r = self._v185_split_shared_break(x)\n                if isinstance(r, list):\n                    out.extend(r)\n                else:\n                    out.append(r)\n            return out\n        if not isinstance(node, dict):\n            return node\n        for k in (\'body\', \'orelse\', \'finalbody\'):\n            if isinstance(node.get(k), list):\n                node = dict(node, **{k: self._v185_split_shared_break(node[k])})\n        if node.get(\'type\') == \'Try\' and node.get(\'_v185_shared_break\'):\n            node = dict(node)\n            node.pop(\'_v185_shared_break\', None)\n            return [node, {\'type\': \'Break\'}]\n        if isinstance(node.get(\'handlers\'), list):\n            node = dict(node, handlers=[self._v185_split_shared_break(h)\n                                        for h in node[\'handlers\']])\n        return node\n\n    def _generate_try(self, region: TryExceptRegion) -> Dict[str, Any]:\n'),
    ('v185-TARGET', '        region_id = id(region)\n        self._generating_regions.add(region_id)\n        self._try_depth += 1\n\n        try:\n', '        region_id = id(region)\n        self._generating_regions.add(region_id)\n        self._try_depth += 1\n        # [v185-SHARED-BREAK] 在生成消耗 handler 列表之前先算出共享\n        # post-try break 落点（_generate_try 内部会改写 except_handlers）。\n        _v185_shared_break_target = self._v185_try_shared_loop_break(region)\n\n        try:\n'),
    ('v185-MARK', '            if _post_try_stmts_r19n2:\n                if isinstance(try_ast, list):\n                    try_ast = try_ast + _post_try_stmts_r19n2\n                else:\n                    try_ast = [try_ast] + _post_try_stmts_r19n2\n\n            return try_ast\n', "            if _post_try_stmts_r19n2:\n                if isinstance(try_ast, list):\n                    try_ast = try_ast + _post_try_stmts_r19n2\n                else:\n                    try_ast = [try_ast] + _post_try_stmts_r19n2\n\n            # [v185-SHARED-BREAK] 共享 post-try break 被重复发射在 try 体与\n            # 最后一个 handler 尾部（try 体 norm 出口与各 handler 清理蹦床\n            # 都落在同一循环外 break 落点）。源码里它是 try/except 之后的\n            # 单条 `break`：此处剥掉两处臂尾 Break 并打标，由循环体装配层\n            # 展开为 Try 后随 Break（每块唯一归属 + AST 一一映射）。\n            if (_v185_shared_break_target is not None\n                    and isinstance(try_ast, dict)\n                    and try_ast.get('type') == 'Try'):\n                _v185_body = list(try_ast.get('body') or [])\n                _v185_hs = list(try_ast.get('handlers') or [])\n                _v185_nbr = 0\n                _v185_nhs = []\n                for _h in _v185_hs:\n                    _hb = list(_h.get('body') or [])\n                    if (_hb and isinstance(_hb[-1], dict)\n                            and _hb[-1].get('type') == 'Break'):\n                        _hb = _hb[:-1]\n                        _v185_nbr += 1\n                    _v185_nhs.append(dict(_h, body=_hb))\n                if (_v185_body and isinstance(_v185_body[-1], dict)\n                        and _v185_body[-1].get('type') == 'Break'\n                        and _v185_nbr >= 1):\n                    try_ast = dict(try_ast, body=_v185_body[:-1],\n                                   handlers=_v185_nhs)\n                    try_ast['_v185_shared_break'] = True\n\n            return try_ast\n"),
]


def _decode(raw):
    bom = raw.startswith(b'\xef\xbb\xbf')
    return raw.decode('utf-8-sig'), bom


def _encode(text, bom):
    data = text.encode('utf-8')
    return (b'\xef\xbb\xbf' + data) if bom else data


def _eol(text):
    return '\r\n' if '\r\n' in text else '\n'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main(argv):
    raw = open(PATH, 'rb').read()
    text, bom = _decode(raw)
    eol = _eol(text)
    check = '--check' in argv
    revert = '--revert' in argv
    rows = []
    ok = True
    if revert:
        work = text
        for key, old, new in reversed(EDITS):
            n = new.replace('\n', eol)
            o = old.replace('\n', eol)
            if work.count(n) != 1:
                rows.append('%-28s REVERT-ANCHOR-FAIL new=%d'
                            % (key, work.count(n)))
                ok = False
                break
            work = work.replace(n, o, 1)
            rows.append('%-28s reverted' % key)
        if ok:
            back = _encode(work, bom)
            open(PATH, 'wb').write(back)
            try:
                py_compile.compile(PATH, doraise=True)
                rows.append('py_compile OK')
            except Exception as e:
                rows.append('py_compile FAIL %s' % e)
                ok = False
            rows.append('bytes %d -> %d sha %s' % (len(raw), len(back), _sha(back)))
    elif check:
        for key, old, new in EDITS:
            o = old.replace('\n', eol)
            n = new.replace('\n', eol)
            rows.append('%-28s old=%d new=%d %s'
                        % (key, text.count(o), text.count(n),
                           'APPLY' if text.count(o) == 1 and text.count(n) == 0
                           else ('ALREADY' if text.count(n) == 1 else 'FAIL')))
            ok &= (text.count(o) == 1 and text.count(n) == 0) or text.count(n) == 1
    else:
        work = text
        changed = 0
        for key, old, new in EDITS:
            o = old.replace('\n', eol)
            n = new.replace('\n', eol)
            if work.count(n) == 1:
                rows.append('%-28s already-applied' % key)
                continue
            if work.count(o) != 1:
                rows.append('%-28s ANCHOR-FAIL old=%d' % (key, work.count(o)))
                ok = False
                break
            work = work.replace(o, n, 1)
            changed += 1
            rows.append('%-28s applied' % key)
        if ok and changed:
            out = _encode(work, bom)
            open(PATH, 'wb').write(out)
            try:
                py_compile.compile(PATH, doraise=True)
                rows.append('py_compile OK')
            except Exception as e:
                rows.append('py_compile FAIL %s' % e)
                ok = False
            rows.append('bytes %d -> %d sha %s' % (len(raw), len(out), _sha(out)))
        elif ok:
            rows.append('no change (idempotent)')
    print('\n'.join(rows))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
