# DIAG B153–B158 — clock_worker 的 110 指令语句体：四条「重派发已登记入口块」判据全部不成

票号 **B153/B154/B155/B156/B158**（同一判据族四次成形）。镜像 `D:/Temp/r141/wt`
（基线 generator 字节 `e9a8f65f6451bcc8`、analyzer `e926a54f17753b33`；每次安装脚本内都
`assert` 基线哈希，仓库 `core/` 全程未动，收尾 `git status --porcelain -- core/ site-packages/` = 0）。
判据尺 `scripts/pyc_verify.py single`。目标文件
`IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
（12/13，唯一失败单元 `<module>.RealtimeEventSource.clock_worker` ⇒ **整文件翻转候选**）。

## 1. 宿主事实（全部由**自证惰性**的追踪给出）

| 追踪 | 惰性自证 | 读数 |
|---|---|---|
| `[R147]` 派发追踪（只读 `type/entry.offset/id/len`） | 产物 `20555` 字节 = HEAD 逐字节相同 | `_process_if_blocks branch=then reg_entry@7582 blocks=[…, 7706, 7708, 7972, 7710, 7980, 8170, …]` —— **@7972 在父臂块表里** |
| `[R151]` 循环内状态打印 | 产物 `20555` 字节 = HEAD 相同 | 迭代到 `@7972` 时 `in_gen=True in_gen_off=True`；owners 含 `IfRegion@7972(then=True)` ⇒ 它是某区域 **ENTRY**，却被当作已生成跳过 |
| `[R147]` 的 `_generate_if` 行 | 同上 | **`entry@7972` 全 run 从未出现** ⇒ 这条 110 指令语句体（`if persist_flag is not False:`）整块不发 |

与 handlers 的差别很关键：handlers 丢的是 pure-none 终块（`_generate_block_statements` 内部
隐式尾声拒绝，见 `LEDGER_R11_DAY2.md` §B146），而这里丢的是**普通语句区域入口**——漏斗若被
请求就能发（此前 `_history_bars`/`clock_worker` 的 gbs 计数 84 中确无 7972，即从未请求）。
所以「重派发该入口区域」看起来正是对症的修法。四次成形都被实测否掉：

## 2. 四次成形与读数（施工点同一处：`_process_if_blocks` 的 `if block in self.generated_blocks: continue`）

| 形 | 字节 | 放行条件 | quotation | realtime_event_source |
|---|---|---|---|---|
| B153 无约束 | `3c3778f145ba64a3` | 块是某区域 entry ∧ id 未生成 | **137/153**（16 回归） | 12/13，产物 20555→20812（结构改变但单元仍红） |
| B154 parent | `3691de831e42dafd` | ＋ `child.parent is region` | 153/153，产物 **SAME_as_HEAD** | 12/13，产物 **SAME_as_HEAD**（@7972 的 parent 不是该臂 ⇒ 条件不成立，惰性） |
| B156 containment | `e79a458c31561c38` | ＋ `set(child.blocks) ⊆ set(region.blocks)` | **138/153** | **10/13**，产物 20555→**5423 字节**（递归重派发把函数体吃掉） |
| B158 entry-offset 守卫 | `6c0ac1b80ea5e9e0` | 把 id 换成「入口偏移未出现在任何已生成区域」 | **137/153** | 12/13，产物 20812（仍红） |

回归单元名（B153/B158 同一批 15–16 个）：`one_prod_to_dataframe`、`fill_minute_or_day_blank`、
`build_future_fill_time`、`change_future_real_date`、`get_price`、`get_date_and_count`、
`get_balance_statement`、`get_income_statement`、`get_cashflow_statement`、`get_growth_ability`、
`get_profit_ability`、`get_eps`、`get_cash_collection_ability`、`get_operating_ability`、
`get_debt_paying_ability`、`check_frequency` —— 全部是 quotation 里**本来绿**的单元。

## 3. 为什么「未生成」信号不可用（`[R157]` 父链读数）

对每条命中分支打印 `arm 父链 / child.parent 父链`：

```
evt  : fire block@6374  arm=IfRegion@6280/LoopRegion@5598/LoopRegion@5598   child_parent=LoopRegion@5598/…
quo  : fire block@634   arm=IfRegion@476/LoopRegion@472/LoopRegion@458      child_parent=LoopRegion@472/…
quo  : fire block@800   arm=IfRegion@476/LoopRegion@472/LoopRegion@458      child_parent=IfRegion@800/LoopRegion@472/…
```

⇒ quotation 的命中情形是**兄弟臂**：该子区域由所在循环体发射路径正常发出，而那条路径
**不把区域登记进 `self._generated_regions`**（只登记块）。于是无论按 id 还是按入口偏移判
「未生成」都成立，重派发 ⇒ 双发 ⇒ 16 单元回归；containment 形更进一步把祖先区域的子区域
也重派发，产生递归吞体（5423 字节）。
而 evt 的 @7972 需要的是「它**从未**被任何路径发过」这个事实，现有容器（`_generated_regions`
/ `generated_blocks` / `generated_offsets`）都无法区分「已发但不登记区域」与「从未发」。

**裁决**：本票族不落地（四条判据：一条惰性、一条回归 16 单元、一条吞掉函数体、一条仍回归 16 单元）。
`realtime_event_source` 仍 12/13。下一票若再碰这条 110 指令语句体，**必须先去读**
循环体发射路径里「发过语句但只登记块、不登记区域」的那一处（候选：`_loop_generate_while`
体内对 `region.body_blocks` 的逐块消费：`region_ast_generator.py:8291`、`:7538`、`:7766`），
把「已发射区域入口」记进一个可判别的集合，再谈重派发；在那之前禁止再用
`_generated_regions` / 入口偏移作为「未生成」的代理判据（本票已实测两者皆不可用）。
补丁留在 `D:/Temp/r141/patch_b158.py`（最完整的一版，含 6 节注释）。

## 4. 顺带钉住的另一个事实（供 handlers 票参考，非本票主张）

`[R151]` 显示 `LoopRegion@5598` 在 `self.regions` 里出现**两次**（owners 列表里同名同入口重复），
与 handlers 里 `LoopRegion@2` 重复同形 ⇒ 「同入口重复区域对象」不是孤例，
凡按 `id(region)` 做状态判据的修法都会在这两处失真。
