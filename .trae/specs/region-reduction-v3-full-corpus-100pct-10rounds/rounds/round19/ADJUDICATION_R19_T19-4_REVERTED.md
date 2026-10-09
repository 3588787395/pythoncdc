# R19-T19-4 门链判决 —— order_api 两单元翻正、但净文件数下降 ⇒ 不落地，已逐字节回退

判据与实现在 `banked_r19t1/`（两文件 + `FIX_T19-4.md` + 回退后写的收窄规格）。
本文件只记主代理自己复测与门链的事实。

## 1. 这一票买到了什么（真缺陷、真根因、真翻正）

`IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` 35/37 的两个失败单元
（`<module>.future_order` −27、`<module>.option_order` −39）根因确证：
三元的条件测试与**未闭合的宿主调用前缀**融在同一个基本块，识别端照建顶层
`TernaryRegion(entry=condition_block)`，发射端只发裸三元、宿主整条语句消失。
判据是既有「栈效应判据」族的自然补全（`_ternary_nested_in_container_construction`
docstring 第 3 条逃逸的另一半）：跳转时残留栈 L≥1，且沿 merge 链**第一个把栈深降到 L 以下
的指令属调用消费族** ⇒ 栈底是未闭合调用而非独立求值；跨度扩到栈深回 0，整体归约为一条语句。

读数（我在自己的 scratch 镜像与实时树上各测一遍）：

```
repro_orderapi  基线 GREEN=2 RED=3  ->  GREEN=5 RED=0   （o1/o4/o5 翻正，o2/o3 保持绿）
order_api.pyc   35/37 -> 37/37 status=success           （整文件翻绿）
repro_tail 13G/0R、repro_arm 0G/3R、repro_ccneg 3G/1R   （护栏不动）
```

## 2. 我自己的一个假否（登记以免重犯）

先只把 `region_ast_generator.py` 装进镜像测，读数 `GREEN=2 RED=3`＝与基线同分 ⇒ 我一度判该判据零翻正。
实际是**安装不完整**：这条路线还必须改 `core/cfg/ast_generator_v2.py`
（融合三元的折叠 `_open_ternary_region` 历史上只接了 `POP_JUMP_*_IF_NONE` 极性，
`IF_FALSE` 极性两条臂的栈压回从未折叠，`reconstruct` 返回垃圾；补丁把新极性接入**同一**
open/track/close 机制，开关 `fold_cond_jump_ternary` 默认关、`reset()` 清旗）。
补装第二文件后同一镜像立刻 5/0 与 37/37。
⇒ 教训：**多文件判据必须整组装再测**，单文件安装的「零翻正」不是判决（先 `diff -rq` 数改动文件）。

## 3. 门链 label 19 vs 18（全四阶段跑完，非面板）

```
[regen] ok=402 bad=0        [verify] 8 shards      [report]  [checks] rc=0
[units] 6584/6617 -> 6584/6617 (99.5013%)      [files] 390 -> 389
[gates] 文件级回退=2  UNIT_REGRESSIONS=2  新增失败单元=2  翻正单元=2
  FIXED    order_api.pyc <module>.future_order / <module>.option_order   （35 -> 37）
  NEW-FAIL plugin_system_log/__init__.pyc <module>.DefaultLogger.setup    （10 -> 9）
  NEW-FAIL plugin_system_trade/function.pyc <module>.get_entrust_item_info（71 -> 70）
checks: quotation 153/153、small34 units_success=1536（基线 1535）、自证 153/153 Equal（两变异各抓 1）、
        pytest 3 failed / 279 passed / 2 xpassed（封盘基线 2 failed / 280 passed ⇒ 新增 1 例击红）
```

⇒ 2 单元翻正、1 整文件翻绿，**但两个原本全绿文件被击红、净文件数 390→389、并新击红一个 pytest 用例**。
按「文件数不得下降 + 零回退」⇒ **不落地**。
17 文件面板对此**完全失明**（两处回退文件都不在面板里，pytest 也只有 checks 阶段才看得见）
⇒ 收窄规格与必测清单写在 `banked_r19t1/README.md`（跨度须在闭合宿主调用的那条指令后即刻停止；
前缀语句与臂块语句归属互斥；复测三单元 + pytest 必含）。

## 4. 回退凭据

```
install_deliver.py restore core/cfg/region_ast_generator.py  byte_exact=True sha=5066b1367b6de3c7
install_deliver.py restore core/cfg/ast_generator_v2.py      byte_exact=True sha=e1e0dcda2e745298
core/cfg/region_analyzer.py 640d33a77dcb71c2（本轮从未改动）
git status --porcelain core/ = 空
```

回退后正在以 pristine 代码重跑门链（label 19 覆盖 `after/`），使 site-packages 产物、
`after/*.json` 名册与 pristine 代码三者一致 —— 门链中途不落的产物是陈旧态，必须扫清。
