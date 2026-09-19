# Round 5–7 回归审计与修复报告

> 初版为 Round 5；Round 6 补入 `resource_utils / trade_schedule` 两项修复及其定位方法；
> Round 7 补入 `strategy` 修复（6.3 节）与 Round 6 收尾的全量复验真实索引（第七节）。
>
> 本报告只描述**被迭代窗口改坏**的文件（`3cf6dce2..` 期间的回归），
> 不含基线即非 100% 的历史遗留项。

## 一、结论

用户"越修越差"的判断**成立**。用提交历史做基线、逐个提交真实重跑后确认：
迭代窗口 `3cf6dce2..c33af45b` 内，**19 个原本真 100% 的文件被打成 partial**。

处置进展：

| 轮次 | 提交 | 成果 | 索引 |
|---|---|---|---|
| Round 5 | `dc28516d` + `e981df4c` | 修 6 个文件回 100% | 334 ok/68 partial → **340 ok/62 partial** |
| Round 6 | `26b643c7` (+`2eb85006`) | `resource_utils.pyc` 0.5000 → **1.0000** | 340 → **341 ok** |
| Round 6 | `ce254791` | `trade_schedule.pyc` 0.7778 → **1.0000** |  |
| Round 6 收尾 | `0ebfe9c4` | 全量复验回填真实索引 | **342 ok/60 partial（97.37%）** |
| Round 7 | `bf49f0f8` | `strategy(IQEngine/core)` 0.6316 → **1.0000**<br>+ `strategy(fly_data)` 0.8333 → **0.9583** |  |
| Round 7 收尾 | `ad945ba6` + 本轮索引 | 全量复验（402/402） | **343 ok/59 partial（97.55%）** |

三轮均已提交并 push 到远程（`origin/main` = `ad945ba6`）。

Round 7 收尾全量复验**逐项核对 402 个文件**，只有 **6 个**数值发生变化，
且**"旧 ok → 新 partial" 为 0 个**（即**零回归**）：

| 文件 | 复验前 | 复验后 | 性质 |
|---|---|---|---|
| `IQEngine/core/strategy/strategy.pyc` | 0.6316 (12/19) | **1.0000 ok (19/19)** | Round 7 修复 |
| `.../plugin_fly_data/strategy/strategy.pyc` | 0.8333 (20/24) | **0.9583 (23/24)** | Round 7 连带（回到历史基线）|
| `IQEngine/utils/trade_schedule.pyc` | 0.7778 (7/9) | **1.0000 ok (9/9)** | Round 6 修复回填 |
| `IQCommon/common/main.pyc` | 0.8485 (28/33) | 0.8788 (29/33) | Round 5 修复回填 |
| `.../plugin_system_realquote/real_quote.pyc` | 0.8182 (36/44) | 0.8409 (37/44) | Round 5 修复回填 |
| `fly/data/quotation.pyc` | 0.993000 | 0.993007 | 浮点精度（142/143 未变）|

累计字节码匹配 **97.37% → 97.55%**（匹配函数 5595 → **5605**，共 5746）。

> 索引口径：`batch --all` 每轮收尾全量复验。Round 6 收尾实测
> **虚标 0 个、低估 1 个**（`trade_schedule.pyc` 已补正），说明前几轮修正后的索引是诚实的。

## 二、"看起来越修越差"的两个机制性原因

### 1. 索引虚高（`faf88269` 已修）
`scripts/pyc_batch_verify.py` 的 `batch` 只跑非 ok 条目：

```python
pending = [e for e in entries if e.get('decompile_status') != 'ok']
```

文件一旦标记 `ok` 就**永不复验**，过期标记长期累积。于是
`pyc_index.json` 曾标 **370 ok**，而 Round 4 用同一工具做的全量复验实测只有 **334 ok**，
**36 个虚标**；提交时入库的又偏偏是那份过期索引。
→ 已改为 334/68，并给驱动增加 `--all` 全量复验开关，供**每轮收尾**核对。

### 2. 不能用"历史提交里的旧 OK.py"当基线（本轮方法论的转折点）
`OK.py` 是**当时**反编译器的输出并随提交入库。但文件若未被重新生成，
它就是**更早某次运行的好输出**，拿它重做比对必然 100% —— 会把所有回归漏掉。
第一版审计正是这样误判的（结论一度是"这 36 个不是回归"）。
→ 必须**真跑反编译器**，且各提交用**同一份驱动脚本**。

## 三、审计方法

| 工具 | 作用 |
|---|---|
| `scripts/regress_bisect.py` | 每个提交一个独立 git worktree，真实重跑；pyc 走镜像目录，OK.py 只写镜像 |
| `scripts/core_bisect.py` | 只 `git checkout <commit> -- core/`（秒级切换），适合 10+ 提交的粗筛；含还原后自检 |
| `scripts/audit_ok_history.py` | 用历史提交里的 OK.py 反查"当时是否真 100%"（仅作旁证，不能当基线） |

基线 `3cf6dce2`（Pre-round1）实跑：回归清单中的文件确为 1.0000。

## 四、责任提交定位（三探针，逐提交真实重跑）

| 提交 | config.pyc | resource_utils.pyc | trade_schedule.pyc |
|---|---|---|---|
| `3cf6dce2` 基线 | 1.0000 | 1.0000 | 1.0000 |
| **`50548e37` R53** | 1.0000 | **0.5000** ↓ | 1.0000 |
| `bf36e0f8` R56 | 1.0000 | 0.5000 | 1.0000 |
| **`a965032f` R57** | **0.5000** ↓ | 0.5000 | 1.0000 |
| `9ceff7f7` R60 | 0.5000 | 0.5000 | 1.0000 |
| **`daae1556` R61** | 0.5000 | 0.5000 | **0.7778** ↓ |
| `0ed7892e` R64 | 0.5000 | 0.5000 | 0.7778 |
| `51dde1da` Round 1 | 0.5000 | 0.5000 | 0.7778 |

即 **R53 / R57 / R61 三个"改进"提交在修好目标文件的同时打坏了这些文件**，
Round 1–4 未对它们造成进一步破坏。

## 五、Round 5 已修复（commit `dc28516d`）

**根因**：R57 引入

```python
_handler_reach_sources = handler_normal_exit_blocks if handler_normal_exit_blocks else handler_end_blocks
```

用 handler 的"正常出口可达块"整体覆盖 `handler_end_blocks`。当 `try` 位于
`if/else` 分支体内时，外层 `if` 的 `else` 体也被判为 handler 可达 → 被当成 try 的
alternative merge → 生成 `try/except/else`，而真实结构是 `if/else`，
多出一条 `JUMP_FORWARD` 跳过 else 体。

**修复**：改为 `handler_end_blocks` 优先，仅在其为空时回退：

```python
_handler_reach_sources = handler_end_blocks if handler_end_blocks else handler_normal_exit_blocks
```

**受控 A/B 实测**（`core_bisect.py`，仅切换 `faf88269` 与 `dc28516d`，同一驱动脚本）：

| 文件 | 修复前 | 修复后 |
|---|---|---|
| `IQCommon/common/config.pyc` | 0.5000 | **1.0000** |
| `fly/common/common.pyc` | 0.8333 | **1.0000** |
| `IQCommon/data/api_data.pyc` | 0.9286 | **1.0000** |
| `IQData/utils/arg_checker.pyc` | 0.9744 | **1.0000** |
| `IQEngine/utils/arg_checker.pyc` | 0.9767 | **1.0000** |
| `IQCommon/arg_checker.pyc` | 0.9787 | **1.0000** |
| `IQCommon/common/main.pyc` | 0.8485 | 0.8788（部分） |
| `trade_schedule / position_validator / graph / instance` | — | 两版一致，**0 回归** |

### 更正
`dc28516d` 的提交信息里"trade_schedule.pyc 0.7778 → 1.00"是**错误读数**：
当时工作区 `core/` 正被另一进程 `git checkout` 覆盖，测到的不是该修复的效果。
A/B 复测为 0.7778/0.7778，即该修复对它无影响。已在 `e981df4c` 原样更正。

## 六、Round 6–7 回归修复明细

### 6.1 `resource_utils.pyc` 0.5000 → 1.0000（commit `26b643c7`）

**症状**：`IQCommon/util/resource_utils.pyc` 的 `release_memory_with_measurement`
比原程序**多一条 `return None`**（orig 112 / decomp 113 条指令），
使 then 臂由「fall-through 内联隐式返回」被迫改成 `JUMP_FORWARD` 跳到句尾。

**定位链**（可复用）：
1. `_r6_dump_regions.py` 打印区域树 → `TryExceptRegion.try_blocks` 含 404；
   同时 `IfRegion.entry=166 merge_block=404`，但 **404 不在该 `IfRegion.blocks` 里**。
   → 生成嵌套 `IfRegion` 后只标记了 `nr.blocks`，404 仍算"未生成"，
   被 try 体的线性遍历当普通语句捡起。
2. `_r6_fdiff.py <函数名> <commitA> <commitB> <file>` 抽取同名函数做 diff
   → 发现 **R53** 在 `_generate_try_body` 的「隐式 return」分支处新增
   `else: body_stmts.append(Return(Constant(None)))`，判据**过宽**。
3. 排除法：给该分支加环境开关实测 —— **禁用 R53 同批的 `[F-TRY-BODY-RETURN fix]` pass
   后产物逐字节不变**（该块早已被 IfRegion 生成路径标记 generated）→ 排除该 pass。

**修复**（依「原则 2 每块唯一归属 + 原则 4 父引用子入口」）：
隐式 `return None` 块若同时是**其它区域**的 `merge_block`，则不再合成 Return。

```python
# [R6 fix] 若该隐式 return None 块同时是某个嵌套区域的 merge_block…
_is_other_region_merge = any(
    getattr(_r, 'merge_block', None) is block and _r is not region
    for _r in self.region_analyzer.regions)
if _is_cond_jump_target:
    body_stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}, '_explicit_return': True})
elif self._loop_depth > 0:
    body_stmts.append({'type': 'Break'})
elif not _is_other_region_merge:
    body_stmts.append({'type': 'Return', 'value': {'type': 'Constant', 'value': None}, '_explicit_return': True})
```

**实测**：`resource_utils` 0.5000 → **1.0000**；33 文件清单其余 32 项**逐项不变**，零回归。
索引 `2eb85006`：340 → **341 ok**。

### 6.2 `trade_schedule.pyc` 0.7778 → 1.0000（commit `ce254791`）

**症状**：真正失配只有两个函数 `is_stock_trade_trigger` / `is_future_trade_trigger`
**丢失尾部** `else: return am_open <= now < am_close or pm_open <= now < pm_close`。
（`get_trading_schedule` 的 `else:` → `continue` 只是文本差异，**字节码等价**，
下游 `return None` 被中止式跳过 —— 该原假设已被推翻，不是失配原因。）

**定位链**：
- `_r6_split_r61.py`：在 `9ceff7f7`(R60) 的 core 上**单独换入 R61 的两个文件**
  → **`core/cfg/region_analyzer.py` 是唯一原因**（generator 无罪），R61 后 1.0 → 0.7778。
- **重要反例**：在 HEAD 上逐条回退 R61 的 4 个 hunk（analyzer 3 + generator 1）
  产物**逐字节不变** → 说明 HEAD 上存在**第二套机制**，单独回退 R61 hunk 无效。
  （这正是"按文件二分 → 再问谁在 HEAD 上生效"两级定位的必要性。）
- `_r6_trace_if.py` 追踪 HEAD 机制：`IfRegion@102` 处理 else 分支（8 块）时，
  块 460/476/486/490 **已被标记 generated**（属链式比较 `IfRegion@460` 与 `BoolOpRegion@490`），
  只剩 492/508/518/522，而 `_generate_if(492)` 产出 0 语句 → else 体坍缩为空。
  → 这就是 `_if_generate_then_branch` @14223 的**链式比较子区域预标记**逻辑：
  它把 `is_empty_then_chained_compare` 的子区域**全部块**标记为已生成，
  但没考虑该子区域**实际落在 else 分支内**的情形。

**修复**（`core/cfg/region_ast_generator.py`）：

```python
if isinstance(child, IfRegion) and getattr(child, 'is_empty_then_chained_compare', False):
    # [R6 fix] 若该链式比较子区域位于本 if 的 else 分支内，归 else 分支所有
    if region.else_blocks and child.entry in set(region.else_blocks):
        continue
    for b in child.blocks:
        self.generated_blocks.add(b)
    continue
```

**实测**（同一驱动脚本，37 文件清单 `_r6_b.txt`）：
`IQEngine/utils/trade_schedule.pyc` 0.7778 → **1.0000 OK**，产物与 `3cf6dce2` 基线一致；
其余 36 项**逐项一致，零回归**。同时核对链式比较相关文件原状态
（`wizard_quant_api 0.9245`、`api_base(IQData) 0.92`、`itn 1.0`、`tradingday_calendar 1.0`）无退化。

### 6.3 `strategy.pyc` 0.6316 → 1.0000（commit `bf49f0f8`，Round 7）

**症状**：`IQEngine/core/strategy/strategy.pyc` 19 个函数里坏 7 个（12/19 = **0.6316**，
与读数**精确 1:1**）。与 `3cf6dce2` 基线做文本 diff 即见，这 7 个函数各在 try 体末尾
凭空多一条 `return None`：

`on_handle_auction` / `on_handle_data` / `on_handle_tick` / `on_order_response` /
`on_trade_response` / `on_strategy_signal_response` / `on_finalized`

（同文件 `reload_strategy` 的 `else:` 被拉平成 `continue` + 同级 `if`，
经核实**字节码等价**，不是失配原因 —— 又一次"文本差异 ≠ 字节码差异"。）

**根因**：R53 在 `_generate_try_body` 的「隐式 return」分支新增
`else: body_stmts.append(Return(Constant(None)))`，判据只有 `_is_trivial_return`
（2 条指令 `LOAD_CONST None` + `RETURN_VALUE`），**条件过宽** —— 它同样命中
"并非 try 体语句、只是外层收尾"的块。

**为何 R6 的守卫无效、为何不能用归属做判据**（本轮关键推理）：
- block 482（`on_handle_auction` 的隐式收尾）**确实在** `region.try_blocks`（共 20 个）里，
  所以 R6 的"是其它区域 `merge_block`"守卫对它不成立（实测 `merge_of=[]`）；
- 它同时被外层 `IfRegion@0` 声明，但 **`on_finalized` 没有外层 if**（owners 只有
  TryExceptRegion），所以"被别的区域声明"**也不能**当判据；
- 7 个函数的平凡 return 块结构完全一致：**唯一前驱、前驱末指令是 `POP_TOP`**
  （最外层 `with` 的 `__exit__` 调用）、无后继。即 fall-through 落进 try 保护跨度的外层收尾块
  （span `[76,508)` 亦覆盖它 → 跨度判据同样无效）。

**修复**：发射集合改为 `{条件跳转目标} ∪ {上方 [F-TRY-BODY-RETURN] pass 收纳的块}`。
新增 `_inlined_ret_offsets` 记录该 pass 的判定结果（要求平凡 return 是 try 块的**后继**、
不在 handler、属于 `region.blocks` 且**无后继**，即确为 try 体正常流出的收尾），
分支改为 `elif _is_inlined_ret and not _is_other_region_merge`。

> 为什么这样一定安全：基线（R53 之前）对该分支**本来就不发射**，
> 故新行为 = 基线 ∪ pass 收纳块 —— 只会比基线多修，不会比基线少修。

**实测**（隔离 worktree `F:/Downloads/pcdc_r7wt` + 镜像目录，同一驱动脚本，同一 37 文件清单，完整 A/B）：

| tag | ok | 变化 |
|---|---|---|
| `base`（worktree 还原到 HEAD） | 13/37 | — |
| `patched` | **14/37** | `strategy(IQEngine/core)` 0.6316 → **1.0000**<br>`strategy(fly_data)` 0.8333 → **0.9583** |

`changed = 2 / 37`，**其余 35 个文件逐项完全一致，零回归**。
`strategy.pyc` 产物与 `3cf6dce2` 基线**文本一致**（仅剩 `reload_strategy` 那处等价差异）。

`strategy(fly_data)` 的 0.9583 正好是它的历史基线值 —— 同一根因的连带收益。

> 注：本轮首次采用"**隔离 worktree + 外部镜像**"跑 A/B，
> 完全不触碰主仓库的 `core/` 与 `site-packages/`，
> 因此可以在**全量复验运行期间**并行测量，不必等复验结束。
> 实测确认 `pyc_batch_verify.py` 的 `batch` 用 `_import_decompiler()` 做**进程内导入**，
> 启动后再改 `core/` 不会影响该进程（但会影响其后新启的进程）。

## 七、剩余回归（Round 7 收尾口径：343 ok / 59 partial）

Round 6 收尾全量复验给出的 60 个 partial 中，**与本迭代窗口回归相关**的是：

| 文件 | 基线 | Round 6 收尾 | 责任提交 |
|---|---|---|---|
| `IQEngine/core/strategy/strategy.pyc` | 1.0000 | 0.6316 | **R53 → Round 7 `bf49f0f8` 已修回 1.0000** |
| `.../plugin_fly_data/strategy/strategy.pyc` | 0.9583 | 0.8333 | **R53 → Round 7 已修回 0.9583** |
| `.../plugin_system_risk_control/position_validator.pyc` | 1.0000 | 0.8000 | 待定 |
| `fly/common/user_error.pyc` | ? | 0.5000 | 待定（**新发现，跌幅最大**）|
| `IQEngine/plugins/plugin_system_log/__init__.pyc` | ? | 0.8000 | 待定 |
| `IQCommon/util/common_func.pyc` | 0.9524 | 0.8095 | 待定 |
| `IQCommon/common/main.pyc` | 0.8485 | 0.8788（已被 Round 5 部分修复）| R57/dc28516d |
| `fly/data/quote.pyc` | 0.8272 | 0.8148 | 待定 |
| `.../plugin_system_realquote/real_quote.pyc` | 0.8864 | 0.8409（已部分修复）| 待定 |
| `IQCommon/util/user_info_utils.pyc` | 1.0000 | 0.8889 | 待定 |
| `.../ptrade_hks_broker.pyc` | 1.0000 | 0.8889 | 待定 |
| `IQCommon/api/klinedata.pyc` | 0.9111 | 0.8889 | 待定 |
| `.../ptrade_future_broker.pyc` / `.../ptrade_option_broker.pyc` | 1.0000 | 0.9000 / 0.9000 | 待定 |
| `IQCommon/manager/instance.pyc` | 0.9688 | 0.9062 | 待定 |
| `IQEngine/config/config.pyc` / `.../ptrade_broker.pyc` | 1.0000 | 0.9091 | 待定 |
| `IQCommon/graph.pyc` | 1.0000 | 0.9355 | 待定 |
| `.../plugin_fly_data/__init__.pyc` | 1.0000 | 0.9500 | 待定 |

其余约 40 个 partial 为**历史遗留**（基线即不是 100%，不属"被修坏"），
完整清单见 `pyc_index.json` 与 Round 7 复验日志。

### Round 8 已完成的定位（下一个目标）
`position_validator.pyc` 0.80（4/5）—— `can_submit_order`：产物在内层 `if/elif/elif` 后
**多出一个 `else: return True`**，并**吞掉了函数尾部共享的 `return True`**。
区域分析**看起来是对的**（所有 `IfRegion` 的 `merge=1664`，`IfRegion@1280` 的 `else=[1660]` 正确），
故缺陷在**生成器侧**。块结构：
`1528`(JUMP→1664) / `1530`(cond→[1566,1658]) / `1566`(RETURN) /
`1658`(JUMP→1664) / `1660`(RETURN，真正的 else) / `1664`(RETURN，**8 个前驱**的函数尾)。

## 八、环境陷阱（本机务必注意）

1. **存在并行写入者**会 `git checkout` / `git commit` 本仓库，
   未提交的 `core/` 改动会被**静默抹掉**（实测两次，直接导致两次错误读数）。
   → 修复必须**立刻提交固化**，测量前后都要 `git status --short core/` 自检。
2. 早期提交（如 `3cf6dce2`）**没有 `scripts/pyc_batch_verify.py`**，
   直接跑会静默全失败（rate=None，看着像"全变 0"）→ 必须统一复制当前驱动脚本
   （`regress_bisect.py` 的 `sync_driver()` 已做）。
3. 反编译器本身**是确定性的**（同代码 3 次重跑结果完全一致），
   数值跳变一律是代码状态被改动，不要怀疑随机性。
4. 每轮收尾必须**全量复验**（`batch --all`），只跑非 ok 条目的做法会持续产生虚标。
5. `D:\temp` 下的 `__pycache__` 读取会被**沙箱拦截**，导致 batch 假报 `failed`（rate=0）
   → 镜像目录放**仓库内**（如 `_r6_mirror`）。
6. 清单文件**末尾必须带换行**，否则路径拼接会失败（`_r6_pass.txt` 首次生成即因此失败）
   → 用 Python 生成并显式加 `\n`。
7. 全量 `--all` 复验 402 文件约 30–90 分钟（与并行任务争 CPU 时更慢）；
   期间**不要**跑 `core_bisect.py` / 任何 `core/` 级实验（会互相污染）。

## 九、诊断工具清单（仓库根目录，均不参与反编译）

| 工具 | 作用 |
|---|---|
| `_r6_dump_regions.py` / `_r6_dump2.py` | 打印指定函数的区域树 / merge_block / 块前后继（dump2 钩 `RegionASTGenerator.__init__`，对无 try 的函数也适用） |
| `_r6_fdiff.py` | 抽取两个提交中同名函数体做 diff（快速看某提交改了什么） |
| `_r6_paircmp.py` | 在两个/多个提交的 core 上反编译同一 pyc 并对比产物文本 |
| `_r6_split_r61.py` | 按文件二分某提交的改动，定位是 analyzer 还是 generator |
| `_r6_trace_if.py` | 追踪某 `IfRegion` 处理 then/else 时各块的 generated 状态 |
| `_r6_who.py` | 在 HEAD 上找出真正生效的机制（回退 hunk 无效时用） |
| `_r7_ab.py` | **隔离 A/B 测试器**：worktree（`F:/Downloads/pcdc_r7wt`）+ 仓库外镜像 `_r7_mirror`，跑任意清单并落 `_r7_ab_<tag>.json` 供逐项对比。不触碰主仓库，故**可与全量复验并行** |
| `_r7_dump_try.py` | 打印 `TryExceptRegion` 跨度 / `try_blocks` 归属 / 平凡 return 块的前驱与后继特征 |
| `_r7_fdiff.py` | `_r6_fdiff.py` 的安全版（后者会覆盖 `_r6_b.txt` 清单） |
| `scripts/pyc_batch_verify.py` | `single` / `batch` / `stats`，`--all` 全量复验 |
| `scripts/core_bisect.py` | 只切 `core/` 的低成本逐提交 bisect |
| `scripts/regress_bisect.py` | 独立 worktree 的逐提交真实重跑 |
