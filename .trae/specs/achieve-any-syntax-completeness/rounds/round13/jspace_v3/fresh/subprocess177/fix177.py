# -*- coding: utf-8 -*-
"""rr-v5r177 patch — subprocess SP3 STMT-DROP: `Popen.__del__` (73→74/78).

单文件单 anchor（core/cfg/code_generator.py），只增不破。

病灶（实测复现 `r170recon/repro/real/sp_Popen___del___real.py`）：
`__del__` 尾部
    if self.returncode is None and _active is not None:
        _active.append(self)
整条语句在产物中蒸发（41→27 条指令，CFG 11→7 节点）。AST 端并无丢失：
`_boolop_chain_exits_are_distinct_sinks` 按「两个互不相同的隐式 return None
出口」正确拒绝折叠为 BoolOp，链成员由 IfRegion 逐层认领，转换后 AST 里尾部
`If(returncode is None) -> If(_active is not None)` 完整存在；丢失发生在
CodeGenerator._generate_if 的 orelse 尾段处理：`_filter_duplicate_if_in_else`
只按**条件文本**判重，而该尾部 if 的条件文本与同一 orelse 里的前一条
`if self.returncode is None: _warn(...)` 相同（并列两条独立语句，条件撞车），
于是被当成结构化分析重影删除，并就地改写 `node.orelse._nodes` 使其永久消失。

修复谓词：把「重复 elif 重影」判据从「条件文本相同」升级为「整臂签名相同」
（条件文本 + then 体渲染文本 + else 体渲染文本）。结构化分析产生的重影由同一
组块二次发射，整臂一致；仅是条件撞车的独立语句 body 不同，必须保留。
签名渲染失败时回退旧行为（按条件去重），保证既有重影清理路径逐位不变（C3）。

Applies the r177 edit with count==1 anchor, utf-8-sig (BOM aware) +
newline preserving (LF-space edit, CRLF restore), py_compile validation
and full idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix177.py [--root <repo-root>] [--check]
"""
import argparse
import py_compile

REPO = 'F:/Downloads/pythoncdc-main'

OLD = '''        else_node_ids = set(id(n) for n in else_nodes)
        elif_conditions = set()
        for node in all_nodes:
            if id(node) in else_node_ids:
                continue
            if isinstance(node, ASTIf) and node.test:
                # 提取条件表达式
                test_str = self._get_condition_str(node.test)
                if test_str:
                    elif_conditions.add(test_str)

        # 过滤掉与elif条件重复的嵌套if
        filtered = []
        for node in else_nodes:
            if isinstance(node, ASTIf) and node.test:
                test_str = self._get_condition_str(node.test)
                if test_str in elif_conditions:
                    # 这是重复的if，跳过
                    continue
            filtered.append(node)

        return filtered
'''

NEW = '''        else_node_ids = set(id(n) for n in else_nodes)
        # [r177-STMTDROP] 「elif 重影」判据由「条件文本相同」升级为「整臂签名
        # 相同」（条件 + then 体 + else 体渲染文本）。旧判据只比条件文本，于是
        # else 体内**合法独立**的 if（条件恰好与 elif 相同、但 body 不同）被当作
        # 重影删除——整条语句蒸发（subprocess Popen.__del__ 尾部
        # `if self.returncode is None and _active is not None: _active.append(self)`
        # 与前面的 `if self.returncode is None: _warn(...)` 条件撞车，41→27
        # 指令、CFG 11→7）。结构化分析重影是同一组块二次发射，整臂一致；条件
        # 撞车但 body 不同的是两条独立语句，必须保留（C3：签名不可得时回退旧
        # 行为，既有重影清理路径逐位不变）。
        elif_arms = []
        for node in all_nodes:
            if id(node) in else_node_ids:
                continue
            if isinstance(node, ASTIf) and node.test:
                # 提取条件表达式
                test_str = self._get_condition_str(node.test)
                if test_str:
                    elif_arms.append((test_str, self._if_arm_signature(node)))

        # 过滤掉与elif条件重复的嵌套if
        filtered = []
        for node in else_nodes:
            if isinstance(node, ASTIf) and node.test:
                test_str = self._get_condition_str(node.test)
                _arm_sig = self._if_arm_signature(node)
                _is_dup = False
                for _ets, _esig in elif_arms:
                    if _ets != test_str:
                        continue
                    # 条件撞车只是必要条件；整臂签名一致（或任一侧不可得，
                    # 保持旧行为）才认定为重影。
                    if _esig is None or _arm_sig is None or _esig == _arm_sig:
                        _is_dup = True
                        break
                if _is_dup:
                    # 这是重复的if，跳过
                    continue
            filtered.append(node)

        return filtered

    def _if_arm_signature(self, node: ASTIf) -> Optional[str]:
        """[r177-STMTDROP] `if` 整臂签名：条件文本 + then/else 体渲染文本。

        ①算法依据：结构化分析把 elif 臂二次发射成 else 体内的嵌套 if 时，重影
        与源臂由同一组块生成——条件、then 体、else 体渲染文本逐字相同；而
        else 体内与 elif 条件恰好相同的独立语句（`if X:` 后跟其他语句，再出现
        一条 `if X:` 做别的事）body 必然不同。仅比较条件文本无法区分二者，
        会把独立语句整条删除（语句蒸发）。
        ②归约顺序：只被 `_filter_duplicate_if_in_else` 消费，用于「是否删除
        else 体内嵌套 if」；不认领块、不建区域、不改异常表/循环表。
        ③唯一归属：签名是只读结构事实（AST 节点渲染文本），不改变任何节点的
        归属；返回 None 时调用方回退旧判据。
        ④嵌套处理：渲染走节点自身 `to_code`（局部 _visited 环检测），不递归
        调用本生成器，避免生成期状态污染。
        ⑤入口引用语义：无。
        ⑥反编译流程：_generate_if 的 orelse 尾段 → _filter_duplicate_if_in_else
        → 本方法；命中整臂一致才删除重影，否则保留语句。
        C1 局部消费：只读传入的 If 节点（test/body/orelse）。
        C2 黑箱组合：对外只交付字符串或 None，不暴露内部结构。
        C3 守卫封闭：异常一律返回 None，消费端按旧行为处理。
        """
        try:
            parts = [self._get_condition_str(node.test)]
            _body = getattr(node, 'body', None)
            parts.append(_body.to_code(0) if _body is not None else '')
            _orelse = getattr(node, 'orelse', None)
            parts.append(_orelse.to_code(0) if _orelse is not None else '')
            return '\\x00'.join(parts)
        except Exception:
            return None
'''

PATCHES = [
    ('core/cfg/code_generator.py', [(OLD, NEW)]),
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
