# Round 31 测试报告：future_position.pyc::make_trade 不匹配分析

日期：2026-08-30　测试人：测试工程师　约束：未修改 core/、scripts/、*OK.py

## 1. 目标与结果

- 文件：`site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc`
- 结果：71/72 匹配，唯一不匹配函数 **`make_trade`**（orig=297 / decomp=292 指令，true_diffs=32）

## 2. 首个差异（ORIG vs RECOMP）

原版 else 分支前导两条赋值在产物中消失，且真分支尾部的 `JUMP_FORWARD` 被
重编译器优化为内联 `LOAD_CONST None; RETURN_VALUE`：

```
ORIG  1412 JUMP_FORWARD  1442            RECOMP 1412 LOAD_CONST None
ORIG  1414 LOAD_FAST     current_date    RECOMP 1414 RETURN_VALUE
ORIG  1418 STORE_ATTR    _long_clean_time     （RECOMP 无对应指令）
ORIG  1428 LOAD_CONST    0.0
ORIG  1432 STORE_ATTR    _buy_avg_open_price  （RECOMP 无对应指令）
ORIG  1442 old_margin = self.margin ...  RECOMP 1416 old_margin = self.margin ...
```

净差：orig 多 7 条（JUMP_FORWARD + else 前导 6 条），recomp 多 2 条（隐式
return None 被优化器内联）。`_long_clean_time` 从 co_names 消失，co_consts 多出 1 个 None。

## 3. 原始字节码关键片段

`make_trade` 末段（`dis` 全量见 make_trade_orig_dis.txt）：

```
1292 COMPARE_OP !=                     # if self.buy_amount - trade_amount != 0:
1298 POP_JUMP_FORWARD_IF_FALSE  1414
1300..1402 self._buy_avg_open_price = ...   # 真分支
1412 JUMP_FORWARD 1442                      # 跳过 else
1414 LOAD_FAST current_date                 # else:
1418 STORE_ATTR _long_clean_time            #   self._long_clean_time = current_date
1428 LOAD_CONST 0.0
1432 STORE_ATTR _buy_avg_open_price         #   self._buy_avg_open_price = 0.0
1442 old_margin = self.margin ...           # merge：...return old-...+delta
1596 RETURN_VALUE
```

即源码为：if/elif 链的 **final else 内是嵌套 if/else（嵌套 else 有两条真实赋值），
嵌套 if/else 之后还有 merge 尾随语句（以 return 结尾）**。

## 4. 区域结构实测（PYTHONHASHSEED=0，probe_region_attrs.py）

- 外层 `IF_ELIF_CHAIN`（entry@0）：`elif_conditions=[850]`，
  **`elif_final_else=[1272, 1300, 1414, 1442]`**（merge 块 1442 被折入 final else，
  链自身的 merge_block 被误识别为 144——then 分支内部的块）。
- 内层 `IF_THEN_ELSE`（entry@1272）：`then_blocks=[1300]`、`else_blocks=[1414]`、merge@1442。
- `probe_pib.py` 实测：`_process_if_blocks(elif_final_else, branch='else')` 返回的 AST
  **是正确的**：`[If(test=..., body=[1 赋值], orelse=[_long_clean_time, _buy_avg_open_price=0.0]),
  old_margin 赋值, AugAssign, ..., Return]` —— 内层 If 的 orelse 完好，merge 是其后兄弟节点。

## 5. 根因判断

**语句丢失发生在渲染层，不在区域分析层。**

- 上游（region_analyzer.py 的链 merge 识别 / region_ast_generator.py 的
  `_process_if_blocks`）输出均正确；把 merge 块折进 `elif_final_else` 只是诱因
  （使内层 If 与 merge 语句成为同一 orelse 列表中的相邻节点）。
- 直接缺陷：`core/cfg/code_generator.py` `_generate_elif_or_else`（def 在 1712 行，
  缺陷逻辑在 ~1783-1799 行）。当 `orelse.nodes = [If(_is_elif=True), 兄弟语句...]`
  时：
  - `len(orelse.nodes) > 1` 分支把**兄弟语句**（merge 内容）渲染成该 elif 的
    `else:` 体；
  - 仅 `len(orelse.nodes) == 1` 时才递归 `elif_node.orelse`（1796-1799 行）；
  - 两者并存时 **elif 节点自身的 orelse（两条赋值）被静默丢弃**。
- 正确行为应为：`elif_node.orelse` 非空时以它为 else 体，兄弟语句作为链后
  尾随语句发射（或二者结构校验后合并），保序不丢失。

## 6. 最小复现与验证

| 文件（round_31/test_engineer/） | 结果 |
|---|---|
| `repro_r31_elif_else_merge.py`（v1，扁平 if/elif/else+merge，对照） | 5/5 匹配，**不触发** |
| `repro_r31_make_trade_mirror.py`（v2，镜像 make_trade 嵌套结构） | **DIFF**：`make` orig=253 / decomp=248，true_diffs=33 |

v2 产物症状与目标逐点一致：final else 的嵌套 if 被拍平为
`elif obj.c - amt != 0:`，嵌套 else 体 `obj.q = 'q'` / `obj.p = 0.0` 两条赋值
丢失，merge 语句顶替成 else 体。

验证命令（3.11.7 magic a70d0d0a，PYTHONHASHSEED=0）：
```
D:/Python/python.exe -c "from scripts import pyc_batch_verify as pbv; print(pbv.decompile_single('repro_r31_make_trade_mirror.pyc'))"
# 再对产物跑 pbv.bytecode_diff → matched 6/7, make DIFF
```

## 7. 附件

- `probe_mismatch.py` / `probe_region_attrs.py` / `probe_else_path.py` / `probe_pib.py`：分析脚本
- `make_trade_orig_dis.txt`：原始函数全量反汇编
- 修复建议落点：`core/cfg/code_generator.py::_generate_elif_or_else`（渲染层）；
  可选加固：region_analyzer 链 merge 识别（避免把真实 merge 误判进 then 分支内部块）。
