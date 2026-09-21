# Round 18-A 分析：`elif` 条件块被尾随 `if` 的 and 链发现跨层次吸收

## 一、病灶（真实 pyc 的块级事实）

`site-packages/fly/data/quotation.pyc` → `<module>.change_future_real_date`，源码形状：

```python
        elif delivery_date:                       # B0 @358
            delivery_date = delivery_date.strftime('%Y%m%d')   # ┐ 同一基本块 B1 @362
            if delivery_date < end[:8]:           #              ┘ 块尾 POP_JUMP_IF_FALSE → 436
                end = delivery_date
```

`build_cfg` + `RegionAnalyzer.analyze()` 实测（脚本 `D:/Temp/r18/r18_diag.py`）：

| 块/区域 | 数值 |
|---|---|
| B0 @358 | `LOAD_FAST delivery_date` + `POP_JUMP_FORWARD_IF_FALSE → 436`；preds=[278]，succs=[436, 362]；`get_entry_region_for_block` → **None** |
| B1 @362 | 臂体赋值 + `... COMPARE <` + `POP_JUMP_FORWARD_IF_FALSE → 436`；preds=[358] |
| IfRegion entry=278 | `elif_conditions=[358]`，then=[282,352,356]，else=[358,362,432]，merge=436 |
| IfRegion entry=362 | `condition_block=362`，then=[432]，merge=436 |

生成端 `_if_generate_normal` 走 `_main_ibc is None` 分支 → `_discover_predicate_and_chain(region, 362)`
反向收集：B0 末指令跳转目标 436 == B1 的汇合目标，且 B0 的 fallthrough 后继正是 B1 ⇒
B0 被当成首合取支，实测返回 `blocks=[358, 362]`，条件重建为
`BoolOp(and, [delivery_date, delivery_date < end[:8]])`。

TRACE 行（`D:/Temp/r18/r18_fn.py --trace`）：
`[TRACE _discover_predicate_and_chain] cond=362 -> blocks=[358, 362]`

后果：`if delivery_date < end[:8]:` → `if delivery_date and delivery_date < end[:8]:`，
严格尺子 `seq_len orig=91 decomp=93`（多发射一条 LOAD_FAST 与其跳转）。

## 二、为什么既有守卫抓不到

同一方法里已有的守卫是「前驱候选是某区域的 **entry** 且该区域的 `condition_block` 就是它」
（嵌套 if 头）。B0 不是任何区域的 entry —— 它只是**父** elif 链区域的 `elif_conditions` 成员，
该链区域的 entry 是主 `if` 的测试块 278。于是 B0 成了守卫的盲区。

对照形状 `if X: … ; 臂内 if X < e:`（本电池 25 号）：那里 X 的测试块**就是**该 IfRegion 的
entry + condition_block，既有守卫命中 ⇒ 两个世界都 MATCH。差别正说明本轮补的是 elif 一侧的洞。

## 三、修法（只加一条唯一归属判据，不新增规则）

`core/cfg/region_ast_generator.py` `_discover_predicate_and_chain`，在既有 entry 守卫之后：

```python
for _oth in self.region_analyzer.regions:
    if _oth is not region and any(_ec is p for _ec in (getattr(_oth, 'elif_conditions', None) or [])):
        return None
```

原则 2（每个块在任何场合只属于一个区域）：B0 已被外层 elif 链区域认领为结构块，
不可能同时是内层 `if` 的合取支；跨层次吸收即本轮禁止的形状。放弃整条链后回退到既有的
单条件生成路径（不新增任何生成规则），与前驱候选是嵌套 if 头时的处理完全同构。

`git diff --numstat`：`core/cfg/region_ast_generator.py` +15/−1（−1 行是注释改写，代码只增守卫；
区域文件 LF 归一 sha256 前 16 位 `a5e2f7e75fa69cca` → `a107457c5215daaf`）；
`core/cfg/region_analyzer.py` 本轮零改动（工作区 sha `255d53d3c8707a07`，与 Round 17 相同）。
补丁脚本 `D:/Temp/r18/r18_fix_chain_owner.py`（字节级 CRLF，2965757 → 2966969 字节）。

## 四、双世界实测（`D:/Temp/r18arm/measure.py --core <核目录>`）

pre = 镜像核 `8145f6ff`（无守卫），post = 仓库工作区核（有守卫）。逐文件仅比较
`_r10_strict_check.strict_compare` 的 MATCH/MISMATCH：

| # | 形状 | pre | post |
|---|---|---|---|
| 01 | elif 臂：赋值 + 尾随 `if d < e` | MISMATCH | MATCH |
| 02 | elif 臂：`+=` + 尾随 `if d == e` | MISMATCH | MATCH |
| 03 | elif 臂：调用前缀 + 尾随 `if d < e` | MISMATCH | MATCH |
| 04 | 第三个 elif 臂 + 前缀 + 尾随 cmp | MISMATCH | MATCH |
| 05 | for 循环内 elif 臂 + 前缀 + 尾随 cmp | MATCH | MATCH（UNCONFIRMED） |
| 06 | 类方法内 elif 臂 + 前缀 + 尾随 `>` | MISMATCH | MATCH |
| 07 | elif 臂 + 前缀 + 尾随 `if d in s` | MISMATCH | MATCH |
| 08 | 两个 elif 臂各带前缀 + 尾随 cmp | MISMATCH | MATCH |
| 09 | elif 臂：`d = g(d)` + 尾随 cmp | MISMATCH | MATCH |
| 10 | 模块级 if/elif + 前缀 + 尾随 cmp | MISMATCH | MATCH |
| 11 | while 循环内 elif 臂 + 前缀 + 尾随 cmp | MISMATCH | MATCH |
| 12 | elif 臂内再嵌一层 elif 臂 + 前缀 + 尾随 cmp | MISMATCH | MATCH |
| 20 | 真链 `if d and d < e` | MATCH | MATCH |
| 21 | 真链 `if d and d in s` | MATCH | MATCH |
| 22 | `elif d and d < e`（前向发现路径） | MATCH | MATCH |
| 23 | 纯 if/elif/else 链 | MATCH | MATCH |
| 24 | 链首前缀赋值 `t = x > 1; if t and y > 2` | MATCH | MATCH |
| 25 | `if a:` 臂内尾随 `if a < e`（既有 entry 守卫已覆盖） | MATCH | MATCH |
| 26 | then 臂内两层嵌套 if | MATCH | MATCH |
| 27 | elif 臂 + 前缀 + 尾随**真** and 链 `if d and d < e` | MATCH | MATCH |

⇒ 11 个锚点全部翻正，27 号证明守卫不误伤「臂内本身就是真 and 链」的形状，
8 个负对照两世界皆 MATCH（零误伤）。

## 五、真实语料侧的影响

| 文件 | 补丁前 | 补丁后 | 消失的缺陷函数 |
|---|---|---|---|
| `site-packages/fly/data/quotation.pyc` | 147/150 | 148/150 | `<module>.change_future_real_date` |
| `site-packages/fly/data/quote.pyc` | 68/89 | 69/89 | `<module>.change_future_real_date` |

第三个孪生 `fly/data/quote_handler.pyc` 的缺陷清单里**没有** `change_future_real_date`
（它的 11 项缺陷是 `get_kline_local`/`get_index` 一族，补丁前后逐名相同）⇒ 本轮只翻正两处同名函数。

另 6 个 WORSENED(rolled back) 文件（`real_quote` 35/45、`flytools` 63/66、`klinedata` 50/63、
`plugin_fly_data/__init__` 19/21、`quote_handler` 61/72、`util/common_func` 17/22）
补丁前后逐名相同 ⇒ 属 Round 13 以来既有的产物/核漂移族，与 R18-A 无关
（A/B 数据 `D:/Temp/r18/ab_pre{1,2}.json` / `ab_post{1,2}.json`）。
