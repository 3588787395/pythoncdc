# FIX R14-04（本轮落地票）— 布尔 run 的「同目标真值边」判据

## 落地内容

`core/cfg/region_ast_generator.py`（提交 1577a2b0，文件 sha256[:16] 由
`851b0723732a2402` → `5066b1367b6de3c7`）：

1. `_if_generate_normal` 的 or 扩展臂装配处（orig 行 21283-21319 区段的
   `if _rhs_expr:` 分支）新增同目标真值边判据 `_r14_same_true`：
   头块（链式比较头时取其末段）与 rhs 操作数块（同样取末段）的条件跳转
   **同为 IF_TRUE 且 argval 落在同一个块** ⇒ 源码形状是 `not A and not B`：
   逐员取反装配 `BoolOp(and, [not A, not B])`，臂体取 rhs 的**落空边**，
   且不登记 `_or_else_block`（该形状没有 else 臂）；
   不满足时逐字节维持原 `BoolOp(or, [A, B])` 拼接与 `last = _or_rhs_block` 尾指令。
2. 新增状态位 `self._r14_and_ext`（声明、复位、以及
   `_has_or_ext = (... and ...) or self._r14_and_ext`）让该形状复用 or 扩展的
   臂装配路径而无需伪造 else 臂。

判据只读结构事实（尾指令操作码类别、跳转目标块身份、链式比较头/末段识别），
不读名字、常量、绝对偏移、指令条数（rules.md §1.5 G4）；决策发生在识别/装配
当下，不做回看修补（原则 5/6）。

## 实测（唯一裁判 scripts/pyc_verify.py single，只喂 pycdc.py --region 产物）

| 文件 | 控制读数 | 施加 R14-04 |
|---|---|---|
| `IQCommon/api/klinedata.pyc` | 62/64 | **63/64**（`kline_datetime_list` 翻正：len 410/410、内容差 0、落点差 0） |
| `IQData/api/api_base.pyc` | 27/28 | 27/28（`get_history_df` 内容差 4 → **0**、落点差 21 → **2**） |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 26/27 | 26/27（不变） |
| `IQCommon/logger/handlers.pyc` | 29/30 | 29/30（不变） |

全量门链：label **18 vs 16**（`.trae/specs/.../rounds/round18/after` 8 份分片报告）。

## 本轮同时纠正的测量口径缺陷（影响既往残差判读）

`dis.hasjrel` / `dis.hasjabs` 是**操作码编号列表**而不是名字列表，旧 hunk 工具写
`JR = set(dis.hasjrel) | set(dis.hasjabs)` 后判 `opname in JR` 恒为假 ⇒ 跳转目标差
被当成内容差，把「只差落点」的单元误标为内容/重定位家族。修正为
`{dis.opname[o] for o in ... if isinstance(o, int)}` 后重测 34 个残差单元：

- 纯落点残差（内容差 0 且长度相等）单元 **6 个**：
  `wizard_quant_api.calculate_di`（该读数取的是同名最大 code object，genexpr 单元需按全限定名配对后重测）、
  `trade_info_utils.kill_trade_process`(659, 2 处落点)、
  `strategy.tick_worker_thread`(288, 4)、
  `trade_live_broker._process_tick_order`(182, 1)、`rzrq_credit_order`(780, 1)、`get_ipo_stocks`(481, 1)
- 内容缺失型（delta ≤ −20）：**5 个** ——
  `trade_live_broker._process_order` −465/507、`_process_cancel_order` −293/333、
  `quote.run_individual_transform` −52/407、`order_api.option_order` −39/94、`future_order` −27/115
- 其余为「小内容差 + 落点差」混合。

⇒ 下一票的优先级由此重排：先取 **sole-unit 文件**（api_base、strategy）的纯落点残差，
其机制即 R14-05（or-run 未建立 BoolOpRegion）；大缺失家族（_process_order 类）单独立票。

## clock_worker 共要件（未落地，留档）

发射端批量认领抑制（`_if_generate_normal:21290` + `_process_if_blocks:25339`
的 `_arm_block_pending` 成员判据）在本轮全量门链 label 17 下：
units 6583/6617 → 6583/6617、文件 390 → 390、回退 0、**翻正 0**，
虽把 `realtime_event_source.clock_worker` 从 −113 条指令收到 −6 条并找回三条被吞语句，
依「fires without flips」逐字节回退，脚本与 pristine 副本见
`D:/Temp/r150/evt_patch.py`、`D:/Temp/r150/pristine_851b0723732a2402_region_ast_generator.py`，
细节在 `DIAG_R1507_ARM_CLAIM_YIELD.md`。
