# fix155b.py: [v155-CONDLEAK] elif-chain builder merge-owner A2b/H2 mirror
import io

p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
s = io.open(p, encoding='utf-8-sig').read()

a = """        _elif_boolop_merge_owner = None
        for _r in self.regions:
            if (not isinstance(_r, BoolOpRegion)
                    or getattr(_r, 'merge_block', None) is not cond_block
                    or _r is region
                    or id(_r) in self._generated_regions
                    or id(_r) in self._generating_regions
                    or _r.entry is None
                    or _r.entry is cond_block):
                continue
            _bo_enc = _r.find_enclosing_parent((IfRegion,))
            if _bo_enc is region:
                continue
            if not _r.value_target:
                continue
            _has_store_in_merge = any(
                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                for i in cond_block.instructions
            )
            if not _has_store_in_merge:
                continue
            _elif_boolop_merge_owner = _r
            break"""
assert a in s, 'ebm lookup'
r = """        _elif_boolop_merge_owner = None
        # [v155-CONDLEAK] A2b/H2 变体镜像（与 _if_generate_normal 的
        # _boolop_merge_owner_for 同层）：owner 可能正在祖先帧里生成
        # （'generating'——BoolOp 生成中派发了本链）或已由兄弟单元发射完毕
        # （'generated'）。两种情形赋值都已/将由 owner 发射，本链不得再次
        # _generate_boolop 取回（原则 2），但仍须以 owner 为 boolop_merge_
        # target 提取块尾条件——否则条件扫描从块首 STORE 起算，双角色块的
        # 条件段被错读成赋值段（copyfileobj 实形：`if length == 0:` 渲染成
        # `if bufsize or 16384:`，函数每次调用提前返回=真实 R1）。
        _elif_bo_skip_generate = False
        for _r in self.regions:
            if (not isinstance(_r, BoolOpRegion)
                    or getattr(_r, 'merge_block', None) is not cond_block
                    or _r is region
                    or id(_r) in self._generated_regions
                    or id(_r) in self._generating_regions
                    or _r.entry is None
                    or _r.entry is cond_block):
                continue
            _bo_enc = _r.find_enclosing_parent((IfRegion,))
            if _bo_enc is region:
                continue
            if not _r.value_target:
                continue
            _has_store_in_merge = any(
                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                for i in cond_block.instructions
            )
            if not _has_store_in_merge:
                continue
            _elif_boolop_merge_owner = _r
            break
        if _elif_boolop_merge_owner is None:
            # A2b/H2 变体：生成中/已生成的 owner 不进上面的主查找（其 id 在
            # generated/generating 台账中），这里补扫。
            for _r in self.regions:
                if (not isinstance(_r, BoolOpRegion)
                        or getattr(_r, 'merge_block', None) is not cond_block
                        or _r is region
                        or _r.entry is None
                        or _r.entry is cond_block):
                    continue
                if (id(_r) not in self._generated_regions
                        and id(_r) not in self._generating_regions):
                    continue
                if not _r.value_target:
                    continue
                if not any(
                        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                        for i in cond_block.instructions):
                    continue
                _elif_boolop_merge_owner = _r
                _elif_bo_skip_generate = True
                break"""
s = s.replace(a, r, 1)

a2 = """        if _elif_boolop_merge_owner is not None:
            _bo_result = self._generate_boolop(_elif_boolop_merge_owner)
            if _bo_result:
                if isinstance(_bo_result, list):
                    pre_stmts.extend(_bo_result)
                else:
                    pre_stmts.append(_bo_result)
            self._generated_regions.add(id(_elif_boolop_merge_owner))"""
assert a2 in s, 'ebm consume'
r2 = """        if _elif_boolop_merge_owner is not None:
            # [v155-CONDLEAK] owner 生成中/已发射时跳过再次 _generate_boolop
            # （A2b：`b = a and 2` 发两份；H2：兄弟单元已发过）——赋值发射权
            # 归 owner 帧，本链仅以 value_target 提取块尾条件。
            if not _elif_bo_skip_generate:
                _bo_result = self._generate_boolop(_elif_boolop_merge_owner)
                if _bo_result:
                    if isinstance(_bo_result, list):
                        pre_stmts.extend(_bo_result)
                    else:
                        pre_stmts.append(_bo_result)
            self._generated_regions.add(id(_elif_boolop_merge_owner))"""
s = s.replace(a2, r2, 1)

io.open(p, 'w', encoding='utf-8-sig').write(s)
print('fix155b inserted')

import py_compile
py_compile.compile(p, doraise=True)
print('syntax OK')
