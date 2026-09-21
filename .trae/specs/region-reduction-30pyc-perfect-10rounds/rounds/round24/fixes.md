# Round 24 — 落地修复 R24-A

## 1. 根因（同层判据缺失）

`core/cfg/region_analyzer.py` 里 `IfRegion.can_be_ternary_header` 的原实现是

```python
return not bool(self.chained_compare_blocks)
```

即：**只要该 IfRegion 带有链式比较块，就一律拒绝把它的块当作三元表达式的条件头**。
但 `region_ast_generator._detect_ternary_pattern` 的 Phase-7-D 分支恰恰是支持这种形状的，
它以 `region.entry is block` 为键沿 `chained_compare_blocks` 走到末段比较块，取 fallthrough
（可经 `JUMP_FORWARD` 连接块）为 true 值块、跳转目标为 false 值块 —— 两边判据不同层：
生成端要求「区域入口块」，分析端无条件禁止。

被拒之后的降级路径是致命的一环：三元赋值不再作为**表达式**发射，而是被拆成 if/else
**语句**，两条臂的纯值块（`int(data_count)` / `200`）被当作语句体发射后其栈顶值被丢弃，
**赋值本身整体消失**。语料见证是 `IQData/plugins/plugin_system_realquote/real_quote.pyc`
的 `get_real_L2_data`（orig=decomp=359、`true_diffs=337`）与孪生
`fly/data/quote.pyc` 的 `get_individual_data`：产物里 `data_count` 从未被重绑 = 语义缺陷，
不只是指令错位。

## 2. 判据（落地原文）

```python
def can_be_ternary_header(self, block, analyzer) -> bool:
    # if区域占用ternary header块时，若存在链式比较块则禁止创建ternary
    if not self.chained_compare_blocks:
        return True
    # [R24-A] 链式比较 IfRegion 的入口块可以是三元表达式的条件头
    # （`v = A if a < b <= c else B`），但该入口块不能同时是整个 CFG 的入口块：
    # _detect_ternary_pattern 的 Phase-7-D 分支正是以 `region.entry is block` 为键沿
    # chained_compare_blocks 走到末段比较块，取其 fallthrough（可经
    # JUMP_FORWARD 连接块）为 true 值块、跳转目标为 false 值块。
    # 中间比较块仍禁止。真正的钻石/值块/merge 消费判据仍由下游
    # _detect_ternary_pattern + R39 值块纯度守卫裁决。
    if (block is self.entry
            and self.entry is not analyzer.cfg.entry_block):
        return True
    return False
```

同层性：两条判据都只引用**本区域自身**的结构身份（`self.entry`、`block`）与 CFG 的入口块，
不引用跨层块序、不引用偏移区间、不新增任何跨递归调用的 `self._*` 标量
（Round 23 R23-A 的缺陷类别）。钻石/值块/merge 的合法性仍由生成端既有守卫裁决，
分析端只放开「这一层允许被询问」。

## 3. 选型过程（为什么是这一条而不是更宽的那条）

| 变体 | 判据 | 实测 |
|---|---|---|
| patchA | `block is self.entry or block is self.chained_compare_blocks[-1]` | 58 文件触发面上产生**过量发射**（HEAD 已有的形状被改写、产物尾部丢语句），否决 |
| patchA2 | 收窄到 entry | 仍带一处不必要的 head 形状改写 |
| patchA3 | `block is self.entry and self.entry is not analyzer.cfg.entry_block` | 与 patchA4 在 58 文件触发面上**逐字节相同** |
| **patchA4 = R24-A** | 同上（最终落地文本） | 取**最小判据**：保留 patchA 的全部收益（`get_real_L2_data` 359/359 由不匹配转为完全匹配），消除其过量发射 |

触发面读数（58 个含链式比较的语料文件，官方尺）：**2 个文件产物变化、0 个当时已 ok 文件变化**，
`Σmatched 1905 → 1906`。

## 4. 落地字节

* `core/cfg/region_analyzer.py`：`59b70fa360d19ad0` → `6df13cdaf815920c`
  （13 增 1 删；纯 CRLF 26793 行、无裸 LF、无 BOM 保持不变；`ast.parse` 自检通过）
* `core/cfg/region_ast_generator.py`：`a365c378e6a40fed` **未改动** —— 本轮是分析端单文件修复
* 落地方式：`probes/mk_spec24.py` 由 base 镜核（与工作树 sha 相同）→ 实测候选镜核派生 1 个
  hunk，spec 内置自证 `spec(base)==候选字节`；`probes/apply_spec.py --write` 只允许两文件白名单、
  锚点 `count(old)==1`、按文件 EOL 约定还原 CRLF。
  落地后由**工作树**重建 `mirr/landed24` 并逐文件哈希核对 ⇒ 后续门禁都在落地字节上跑。
  注：落地后又做过一次**纯注释**改写（把注释里残留的 patchA「最后一个比较块」臂的说法
  改成实际落地的 entry 判据；代码行逐字未变），因此最终字节 `6df13cdaf815920c` 才是
  所有 landed 门禁的读数对象。

## 5. 收益与残余

收益（官方尺，真尺 `single` 复验）：
`real_quote.pyc 37/44 → 38/44`，`get_real_L2_data` 从 `orig=359 decomp=359 / true_diffs=337`
变为完全匹配；`fly/data/quote.pyc` 仍 `67/81`，但其 `get_individual_data` 由
`orig=312 decomp=304` 收窄到 `decomp=306`（长度差 8→6，无币值）。

残余（R24-A 有意不覆盖，均已入电池/记录）：
1. `get_cache_l2_data` / `get_cache_l2_data_by_one`（`orig 337/321`、`decomp 335/319`、
   `first_diff index 18 JUMP_FORWARD vs POP_TOP`）—— 三元头位于**函数首块**
   （`self.entry is analyzer.cfg.entry_block`），是判据显式排除的那一半；
   电池见证 `b03_cc_ternary_at_head`（两核产物逐字节相同、都 FAIL）。
2. `for` 体内的嵌套三元（电池见证 `c04_cc_ternary_nested_in_loop`，同样两核相同）。
3. `d07_ternary_cc_mix`：产物被改写、长度转对（`ternary_with_cc_arms 23/21 → 23/23`），
   但官方仍不匹配 ⇒ 无币值。这是全量 402 里第 2 个「改写但无增益」的产物。
