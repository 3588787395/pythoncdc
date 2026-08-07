with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """    def _try_build_chained_compare_in_boolop(self, chain_block, region):
        \"\"\"[CPython peephole P4 + P5 interaction] Reconstruct a chained
        compare (e.g. ``a < b < c``) when its entry block appears as a
        BoolOp operand.

        算法角色：链式比较操作数重建器（Chained Compare Operand Reconstructor）
        输入：chain_block (BoolOp op_chain 的一个块) + BoolOpRegion
        输出：完整链式比较 AST（{'type': 'Compare', ...}）或 None

        【背景】
        当 ``if a < b < c and d < e < f:`` 被编译时，每个链式比较
        (a<b<c, d<e<f) 由 ``_identify_chained_compare_regions`` 识别为一个
        IfRegion（带 ``chained_compare_ops`` / ``chained_compare_blocks``）。
        该识别在 BoolOp 识别之前发生（自底向上归约：链式比较是更小的归约单元）。"""

new = """    def _try_build_chained_compare_in_boolop(self, chain_block, region):
        \"\"\"[CPython peephole P4 + P5 interaction] Reconstruct a chained
        compare (e.g. ``a < b < c``) when its entry block appears as a
        BoolOp operand.

        算法角色：链式比较操作数重建器（Chained Compare Operand Reconstructor）
        输入：chain_block (BoolOp op_chain 的一个块) + BoolOpRegion
        输出：完整链式比较 AST（{'type': 'Compare', ...}）或 None

        【背景】
        当 ``if a < b < c and d < e < f:`` 被编译时，每个链式比较
        (a<b<c, d<e<f) 由 ``_identify_chained_compare_regions`` 识别为一个
        IfRegion（带 ``chained_compare_ops`` / ``chained_compare_blocks``）。
        该识别在 BoolOp 识别之前发生（自底向上归约：链式比较是更小的归约单元）。
        [R36] Also handles the case where chain_block is the merge_block of a
        preceding chained compare (value-context, cached by _generate_if)."""

# Also add cache check at the beginning of the method body
old2 = """        该识别在 BoolOp 识别之前发生（自底向上归约：链式比较是更小的归约单元）。
        随后 BoolOp 链检测把每个链式比较的 entry 作为单个操作数加入 op_chain
        （通过 hop 逻辑跳过链式比较内部块），因此 op_chain 中每个 chain_block
        可能是某个链式比较 IfRegion 的 entry。

        【问题】
        若直接对 chain_block 调用 ``expr_reconstructor.reconstruct()``，只会
        取到 entry 块内的第一个 COMPARE_OP（如 ``a < b``），丢失后续链节
        （``< c``），导致 ``a < b < c`` 退化为 ``a < b``。

        【修复】
        遍历 ``self.regions`` 查找 entry == chain_block 且带 chained_compare_ops
        (长度 ≥ 2) 的 IfRegion，调用 ``_build_chained_compare_from_region_data``
        重建完整链式比较表达式。同时把链式比较的内部块标记为已生成，避免父
        IfRegion 重复处理。

        【4 原则合规】
        - 自底向上归约：链式比较 IfRegion 先于 BoolOp 识别，本方法仅在表达式
          重建阶段把已识别的子区域作为抽象节点展开为表达式，不改变归约顺序。
        - 每块唯一归属：链式比较的内部块（chained_compare_blocks）属于链式比较
          IfRegion，不属于 BoolOpRegion；本方法把这些块标记为 generated，
          防止父 IfRegion 重复处理。
        - 嵌套即抽象节点：链式比较 IfRegion 作为 BoolOp 的抽象操作数节点。
        - 父引用子入口：BoolOp 的 op_chain 引用链式比较 IfRegion 的 entry。
        \"\"\"
        for r in self.regions:"""

new2 = """        该识别在 BoolOp 识别之前发生（自底向上归约：链式比较是更小的归约单元）。
        随后 BoolOp 链检测把每个链式比较的 entry 作为单个操作数加入 op_chain
        （通过 hop 逻辑跳过链式比较内部块），因此 op_chain 中每个 chain_block
        可能是某个链式比较 IfRegion 的 entry。

        【问题】
        若直接对 chain_block 调用 ``expr_reconstructor.reconstruct()``，只会
        取到 entry 块内的第一个 COMPARE_OP（如 ``a < b``），丢失后续链节
        （``< c``），导致 ``a < b < c`` 退化为 ``a < b``。

        【修复】
        遍历 ``self.regions`` 查找 entry == chain_block 且带 chained_compare_ops
        (长度 ≥ 2) 的 IfRegion，调用 ``_build_chained_compare_from_region_data``
        重建完整链式比较表达式。同时把链式比较的内部块标记为已生成，避免父
        IfRegion 重复处理。

        【4 原则合规】
        - 自底向上归约：链式比较 IfRegion 先于 BoolOp 识别，本方法仅在表达式
          重建阶段把已识别的子区域作为抽象节点展开为表达式，不改变归约顺序。
        - 每块唯一归属：链式比较的内部块（chained_compare_blocks）属于链式比较
          IfRegion，不属于 BoolOpRegion；本方法把这些块标记为 generated，
          防止父 IfRegion 重复处理。
        - 嵌套即抽象节点：链式比较 IfRegion 作为 BoolOp 的抽象操作数节点。
        - 父引用子入口：BoolOp 的 op_chain 引用链式比较 IfRegion 的 entry。
        \"\"\"
        # [R36] Check cache first — _generate_if may have cached the chained
        # compare expression when it detected the IfRegion is a BoolOp operand.
        if hasattr(self, '_chain_compare_expr_cache'):
            _cached = self._chain_compare_expr_cache.get(id(chain_block))
            if _cached is not None:
                return _cached
        for r in self.regions:"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fix3a: docstring updated")
else:
    print("FAIL: old not found for docstring")

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix3b: cache check added")
else:
    print("FAIL: old2 not found for cache check")

with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
