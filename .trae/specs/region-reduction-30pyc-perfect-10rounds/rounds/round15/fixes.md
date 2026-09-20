# Round 15 修复记录（fixes）—— 前置语句发射权登记（SubTask 13.1 / 13.2 正解）

改动全部在 `core/cfg/region_ast_generator.py`（UTF-8 BOM + 纯 CRLF，一律字节级补丁）。
sha 链（前 → 后）：

```
dc4bf5857f3a42a5  (Round 14 产物 + A1b，本轮起点)
 → d5a827199240447b  A2   指令粒度登记表 + 漏斗登记
 → 4081092974cdecb4  A2b  _generate_boolop 重入保护 + 祖先认领交接
 → 9407806fb72c2103  A2c  A1b 让位判据纳入「正在生成中」的区域
 → 30ed9522ca00c94d  A2d  祖先发射情形同样把 owner 登记为已生成
 → 7c5ffe968232806d  A2e  同量纲切片从漏斗移到链首消费者
 → f8debe9af6b60b20  A2f  提取后丢弃路径的认领快照回滚（本轮终态）
```

## 1. A2：登记表与量纲（`region_ast_generator.py:240` / `:46165`）

新增 `self.prefix_emitted_upto: Dict[BasicBlock, int]`（`:240`，紧接
`_entry_prefix_emitted_blocks`）：语义 = 「该块内**已经作为语句进入输出**的前缀，其覆盖到的
最后一条指令偏移」。只增不减，单向数据流。

唯一登记点 `_register_prefix_emitted(block, instrs)`（`:46165`），值取本次实际消费的
前缀末指令偏移（`max(i.offset)`），不是 `block.start_offset`。Round 13 失败尝试 (a) 的病根
正是「登记量纲 ≠ 判定量纲」。调用点在真正产出语句的两条出口（`:46242` 委托出口、
`:46275` 归约出口）；调用点在 `_build_prefix_stmt_list` 内部，而该漏斗全仓库只有 2 个
调用方，因此不会再出现 Round 13 失败尝试 (b) 的「第一份语句不走台账」。

## 2. A2b/A2c/A2d：双角色块的重入保护与交接（`:30987` / `:16337` / `:16418` / `:11090`）

`BoolOpRegion ↔ IfRegion` 是双向认领：`_generate_boolop_impl` 派发「entry 恰好是本区域
merge_block」的下游 IfRegion，而 `_if_generate_normal` 又经 `_boolop_merge_owner_for`
回头取本 BoolOp 区域。原则 2 在生成层的表达 = 「正在生成中的区域不得被自己的子节点再生成
一次」，故：

- `_generate_boolop` 改为包装（`:30987`），生成期把 `id(region)` 压入 `_generating_regions`；
- `_boolop_merge_owner_for(..., include_generating=False)`（`:16337`）默认跳过正在生成中的
  候选，`_if_generate_normal`（`:16418`）显式传 `include_generating=True` 取得祖先 owner，
  并据此置 `_boolop_owner_emitted_by_ancestor`；
- 两种情形都必须 `self._generated_regions.add(id(_boolop_merge_owner))`（A2d），否则
  `_if_extract_condition_from_instructions` 不再抑制 BoolOp 重建，输出 `if a and 2:` 而非
  `if b:`（A2c 实测）；
- `_if_extract_cond_instructions` 出口登记（`:13835`）：条件提取实际吃到的语句段同样按指令
  粒度登记，供链首消费者切片；
- A1b 的让位判据（`:11090`）改用 `include_generating=True`，否则「owner 正在生成中」会被
  误判成「无 owner」，整段 if 消失（A2b 实测 r14j_11/12 由 29→9 / 29→11）。

## 3. A2e：切片只能放在链首消费者（`:31328-31342`）

`pre_instrs` 取回后按 `i.offset > prefix_emitted_upto[first_chain_block]` 过滤，剩余段为空
时下面的归约入口扫描自然找不到切点 ⇒ 本区域一条前缀都不发。
下沉到 `_build_prefix_stmt_list` 内部切片被实测否决：该漏斗同时服务 `prefix_block` 与
post-store 请求方，一起切掉会造成 `IQCommon/profiler_func` 模块级 import 丢失。

## 4. A2f：提取后丢弃 ⇒ 认领必须撤销（`:31001-31014`）

`_generate_boolop_impl` 存在 `_guard_clause_skip` 路径：`results = list(pre_stmts)` 之后
置 `prefix_stmts_pending = True` 并 `return None`，即**提取了前缀却一条都没发**。登记语义是
「已进入输出」，故包装层在调用前拍快照、调用返回空时整体回滚。与 `_generating_regions`
进出栈同属一次调用的作用域记账，方向仍自底向上、不回改数据流。
不做的代价（实测）：`IQCommon/profiler_func` 模块级 `PY3 = sys.version_info[0] == 3` 整体
丢失，16/16 → 15/16。

## 5. 实测效果

| 尺子 | A2 前（`dc4bf5857f3a42a5`，A1b） | A2f（本轮终态） |
| --- | --- | --- |
| `test_repros/round14_join`（16 复现） | MISMATCH=11 MATCH=5 | **MISMATCH=1 MATCH=15**，10 个翻正项已改标 SENTINEL，UNEXPECTED=0 |
| 14 文件严格 A/B（`D:/Temp/r14_ab2.py`） | 534/589 | **534/589，缺陷集合与 A1b 逐函数完全相同（diff 为空）⇒ 零回归** |
| 31 个「只差 1 个函数」文件产物门 | — | UNCHANGED=29，2 项 REGRESSION 经换件 A/B 证明在 **HEAD 提交态同样发生**（`json_persistance` 6/7、`base_validator` 5/6），属 SubTask 13.3 的 Round 13 遗留债，非本轮引入 |

`r14j_09_try_in_else_arm` 仍是唯一 MISMATCH，且根因不同族：analyzer 让 IfRegion 的 else 臂
与兄弟 `TryExceptRegion` 争夺同一批块（`IfRegion entry=84 blocks=[84,90] then_blocks=[90]
merge_block=98`，`TryExceptRegion entry=100 blocks=[98,100,…]` 且无 parent），属**结构区域
在 else 臂的吸收**问题，与 `PluginManager.set_engine` ×2（SubTask 13.4 / A-2）同源，
本轮作为第二交付项继续处理。
---

# Round 15-B：else 臂「双角色块」认领（H1 + H2）

基线 sha `f8debe9af6b60b20` → 落地位 `d07996aaa20d4665`
（`core/cfg/region_ast_generator.py`，UTF-8 BOM + 纯 CRLF，行数 48070 → 48122）。
补丁脚本 `D:/Temp/r15_h1_patch.py`（6 个 hunk，断言 base sha、锚点唯一、
BOM/CRLF 不变、compile 通过、拒绝重复应用）；反向重建 `D:/Temp/r15_make_base_copy.py`。
落地前的全部验证走「副本播种」（`D:/Temp/r15_h1_dryrun.py` / `D:/Temp/r15_seed_any.py`
把 `D:/Temp/r15_h1_copy.py` 装进 `sys.modules['core.cfg.region_ast_generator']`），
因此与只读诊断子代理并行时仓库零写入。

## 1. H1：`_try_collect_c3` 的否决漏掉「值 merge 块 ≠ 入口占用」

识别条件：else 臂两阶段收集中，第二阶段的 `BoolOpRegion/TernaryRegion` 把自己的
`merge_block` 登记进 `_value_merge_blocks_c3`；第三阶段的 `IfRegion` 若
`entry ∈ _claimed_blocks_c3` 但同时 `entry ∈ _value_merge_blocks_c3` 且
`condition_block is entry`，则**不否决**。
归约方式：块的所有权按「指令段」而非「整块」判定 —— 值区域的 merge_block 只认领
store 前缀，块尾条件段仍归后继 if（原则 2 的显式例外，与分析层例外 3 同一条判据）。
AST 映射：臂内 emit 单元由 `[BoolOp@12]` 变为 `[BoolOp@12, If@76]`，
中间 `if` 语句复原。
不做的代价（实测）：`IQData/utils/arg_checker`、`IQEngine/utils/arg_checker` 各丢
`LOAD_FAST valid; POP_JUMP_FORWARD_IF_FALSE` 两条 ⇒ 38/39、42/43。

## 2. H2：owner 的「识别」与「发射权」必须解耦

设计稿原判据（`:16418` 一处）不足以复原：H1 单独落地时 IfRegion 虽被收集，
`_generate_if` 仍在 `:11090` 把它扔掉 ——
`_boolop_merge_owner_for(region, include_generating=True)` 遇到**已发射完毕**的
owner（兄弟单元）返回 None ⇒ `return []` ⇒ 整条 if 连同其嵌套区域消失
（r15a_01 实测 seq_len 61→25）。
最终三处：
- `_boolop_merge_owner_for` 增 `include_generated` 形参，把
  `id(_r) in self._generated_regions` 从识别判据里摘出来（识别只看
  `owner.merge_block is cond_block`）；
- `:11090` carve-out 传 `include_generated=True`；
- `_if_generate_normal` 祖先兜底后加 `else` 分支：`_bo_sib` 命中且
  `id ∈ _generated_regions` ⇒ 置 `_boolop_owner_emitted_by_ancestor`，
  赋值**不再**二次 `_generate_boolop`（原则 2：一条语句一个发射者），
  但仍把 `boolop_merge_target=owner.value_target` 交给
  `_if_extract_cond_instructions`，条件从块尾 store 之后起算。

## 3. 实测

| 尺子 | 修复前 | 修复后 |
| --- | --- | --- |
| `test_repros/round15_arm`（12 复现，本轮新建） | MISMATCH=9 | MISMATCH=4，**5 项翻正并改标 SENTINEL**，UNEXPECTED=0 |
| `test_repros/round14_join`（16） | MISMATCH=1 | MISMATCH=1（无变化、无 REGRESSED） |
| `test_repros/round14`（17）/ `round13`（25） | 0 UNEXPECTED | 0 UNEXPECTED（逐项同 EXPECT） |
| 31 文件内存严格 A/B（`r15_ab3` 换件法，产物不动仓库） | 445 identical | **447**，逐文件其余 28 项不变 |
| `quotation.pyc` 单验 | 147/150 | 147/150，缺陷集合逐函数相同 ⇒ 与本轮无关 |
| 全量产物门 406 targets | CLEAN=327 UNCHANGED=67 | **CLEAN=329 UNCHANGED=65** WORSENED=9 REGRESSION=2 NO-OKPY=1 |
| 官方（loose）口径 | IQData 38/39、IQEngine 42/43 | **39/39 rate=1.0、43/43 rate=1.0**（`scripts.pyc_batch_verify.bytecode_diff` 复算） |

产物门两轮：`D:/Temp/r15_gate_c1.json`（326 项，CLEAN=270 UNCHANGED=49 WORSENED=5
REGRESSION=2）+ `D:/Temp/r15_gate_c1b.json`（80 项，CLEAN=59 UNCHANGED=16
WORSENED=4 NO-OKPY=1）。
**9 WORSENED + 2 REGRESSION 与 Round 14 的 `D:/Temp/r14_gate_c1.json` 文件集合逐个相同**
（klinedata、common_func、real_quote、plugin_fly_data/__init__、history_api、
flytools、market_time、quotation、quote_handler + json_persistance、base_validator），
且其中 5 项再用「pre-patch 副本」内存复算逐一对齐（50/63、17/22、35/45、19/21、16/18
与门内 after 值完全相同）⇒ 全部为 Round 13 遗留的产物/代码漂移（SubTask 13.3），
本轮零新增回退。
