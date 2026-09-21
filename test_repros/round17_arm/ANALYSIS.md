# Round 17-A —— D2 守卫判据④（循环豁免）删除的最小复现电池

目录：`test_repros/round17_arm/`（26 个复现源文件 + `run_all.py` + 本文）
被测核：`core/cfg/region_analyzer.py`（sha256 前 16 位 `255d53d3c8707a07`）、
`core/cfg/region_ast_generator.py`（`0fc591a8433e7032`）
尺子：`_r10_strict_check.strict_compare`（只 import，不改）

## 1. 守卫是什么

`RegionAnalyzer._build_elif_region`（`core/cfg/region_analyzer.py:17831`）在把「回收出来的
else 臂」识别成 **if/elif 链**之前有一道否决（下称 D2 守卫，现行位置
`core/cfg/region_analyzer.py:18755-18763`）：

```python
if (inner_merge is not None and merge_ is not None
        and inner_merge is not merge_):
    _d2_last = inner_merge.get_last_instruction()
    _d2_terminal = (_d2_last is not None
                        and _d2_last.opname in (
                            'RETURN_VALUE', 'RETURN_CONST',
                            'RAISE_VARARGS', 'RERAISE'))
    if not _d2_terminal:
        return None          # 不建 elif 链，改建 IF_THEN_ELSE（else 臂 = 嵌套 if + 尾随语句）
```

判据（全部满足才否决）：① `inner_merge is not None`；② `merge_ is not None`；
③ `inner_merge is not merge_`；④ **旧**：「外层 else 不在循环内」
（`and self._find_enclosing_loop(first_else) is None`）；⑤ `inner_merge` 非终态块。

`inner_merge` 是 else 臂里那个嵌套 if 两路分支的汇聚点，`merge_` 是整条外层链的汇聚点。
`inner_merge != merge_`（③）等价于「嵌套 if 之后还有尾随语句属于外层 else 臂」。

## 2. 为什么④是错的

* **循环归属不是结构差异。** 真 elif 链（`else:` 里只剩一个嵌套 if、其后无语句）的两路
  分支必然汇聚到外层 merge，于是 `inner_merge is merge_`，判据③已经把合法链全部放行。
  ④对合法链是**冗余**判据。
* **④对「loop 内嵌套 if + 尾随」是漏检开关。** 一旦 else 臂在循环里，④使守卫失效，
  else 臂被建成 `IF_ELIF_CHAIN`；链构建末尾的 `_elif_struct_blocks` 过滤会把尾随语句剔出
  else 臂并外提成链的兄弟语句。此时 then/elif 臂末尾那条 `JUMP_FORWARD` 的落点从
  **外层 merge** 变成 **被外提的尾随语句入口** —— 即 `target_diff`（跳转终点漂移），
  并且尾随语句在 then 臂路径上也被执行了一遍（语义改写，真实代码里表现为
  变量未定义 / 重复副作用）。
* **真实代价**：`site-packages/IQData/manager/plugin_manager.pyc`
  与 `site-packages/IQEngine/core/plugin_manager.pyc` 的 `PluginManager.set_engine`
  分别 9/10 → **10/10**、8/9 → **9/9**；406 pyc 语料 FIXED=7 文件/9 函数、BROKEN=0、CHANGED=0。

删除④后，守卫只看 ①②③⑤ —— 纯结构判据，循环内/外一视同仁。

## 3. 测量方法（关键：只能原地换方法）

* post-patch = 仓库当前核：
  `PYTHONIOENCODING=utf-8 D:/Python/python.exe test_repros/round17_arm/run_all.py --strict`
* pre-patch = 把④塞回去，**不碰仓库**：取 `inspect.getsource(RegionAnalyzer._build_elif_region)`
  → dedent → 在守卫收尾行 `and inner_merge is not merge_):` 前插回
  `and self._find_enclosing_loop(first_else) is None` → `exec(compile(src,'<r17a_prepatch>','exec'), …)`
  → `setattr` 回类。**不能整模块替换** `core.cfg.region_analyzer`：那会让 `isinstance`
  身份断裂、函数被静默降级为 `pass`。实现见 `D:/Temp/r17arm/measure.py`（与
  `D:/Temp/r17arm/h.py` 同一技术），区域层数值探针见 `D:/Temp/r17arm/trace.py`
  （在守卫前插一行 print，报 `block / first_else / inner_merge / merge_ / inloop / term`）。
* 编译产物全部落在 `D:/Temp/r17arm/build/`，仓库内不留 `.pyc` / 生成 `.py`。

## 4. 逐复现表

「守卫数值」列格式 `block / first_else / inner_merge / merge_ / inloop / term`（字节偏移，
base 世界实测）。`—` 表示该形状从未走到守卫。

| # | 文件 | 形状要点 | 角色 | 守卫数值 | pre-patch | post-patch | EXPECT |
|---|---|---|---|---|---|---|---|
| 01 | r17a_01_anchor_for_assign_tail | for；else=嵌套 if/else(`and`)+两条尾随赋值 | 锚点 | 44/62/170/222/T/F | MISMATCH `target_diff #13 (('text',LOAD_FAST)→('len',LOAD_GLOBAL))` | MATCH | SENTINEL |
| 02 | r17a_02_anchor_for_call_tail | 尾随=日志调用+构造 dict | 锚点 | 44/100/194/276/T/F | MISMATCH `target_diff #16 payload→log` | MATCH | SENTINEL |
| 03 | r17a_03_anchor_for_for_tail | 尾随=**for 循环**+赋值 | 锚点 | 48/66/164/292/T/F | MISMATCH `target_diff #15 head→enumerate` | MATCH | SENTINEL |
| 04 | r17a_04_anchor_for_while_tail | 尾随=**while 循环**+append | 锚点 | 44/62/166/242/T/F | MISMATCH `target_diff #13 report→n` | MATCH | SENTINEL |
| 05 | r17a_05_anchor_for_try_tail | 尾随=**try/except**+append | 锚点 | 44/62/140/258/T/F | MISMATCH `target_diff #13 report→n` | MATCH | SENTINEL |
| 06 | r17a_06_anchor_for_with_tail | 尾随=**with 块**+赋值 | 锚点 | 44/62/140/282/T/F | MISMATCH `target_diff #13 n→store` | MATCH | SENTINEL |
| 07 | r17a_07_anchor_for_return_tail | 外层三臂；尾随=**提前 return 守卫** | 锚点 | 62/80/158/176/T/F | MISMATCH `target_diff #13 report→n` | MATCH | SENTINEL |
| 08 | r17a_08_anchor_for_break_tail | 尾随含 **break** | 锚点 | 48/74/132/194/T/F | MISMATCH `target_diff #17 report→score` | MATCH | SENTINEL |
| 09 | r17a_09_anchor_for_continue_tail | 外层 else=嵌套 if/elif/else；尾随含 **continue** | 锚点 | 44/62/96/146/T/F | MISMATCH `target_diff #13 report→n` | MATCH | SENTINEL |
| 10 | r17a_10_anchor_while_boolop | **while** 包裹；外/内条件皆 BoolOp | 锚点 | 96/152/222/310/T/F | MISMATCH `target_diff #24 len→seen` | MATCH | SENTINEL |
| 11 | r17a_11_anchor_inner_elif_chain | else 臂=完整嵌套 **if/elif/else** + 两条尾随 | 锚点 | 44/62/116/156/T/F | MISMATCH `target_diff #13 out→len` | MATCH | SENTINEL |
| 12 | r17a_12_anchor_two_level_deep | **两层**嵌套（else 臂里再套 if/else）+ 尾随 | 锚点 | 44/62/104/140/T/F | MISMATCH `target_diff #13 report→acc` | MATCH | SENTINEL |
| 13 | r17a_13_anchor_module_scope | **模块级** for（无函数包裹） | 锚点 | 18/36/136/188/T/F | MISMATCH `target_diff #18 ('text',LOAD_NAME)→(4,LOAD_CONST)` | MATCH | SENTINEL |
| 14 | r17a_14_anchor_class_method_plugin | module→class→method→for→三臂链，else 臂嵌套链+尾随 | 锚点（真实缺陷源） | 170/220/358/460/T/F | MISMATCH `target_diff #25 dict→log` | MATCH | SENTINEL |
| 15 | r17a_15_anchor_nested_if_then_only | else 臂的嵌套 if **无 else**（then 臂以 JUMP_FORWARD 收尾） | 锚点 | 48/74/88/124/T/F | MISMATCH `seq_len 39→40` | MATCH | SENTINEL |
| 16 | r17a_16_anchor_outer_or_boolop | 外层 **or** 短路条件；尾随=增量赋值 | 锚点 | 44/74/152/188/T/F | MISMATCH `target_diff #17 report→out` | MATCH | SENTINEL |
| 17 | r17a_17_anchor_while_plain_cond | **while** + 全部条件为普通比较（无 BoolOp） | 锚点 | 44/162/190/232/T/F | MISMATCH `target_diff #29 name→seen` | MATCH | SENTINEL |
| 18 | r17a_18_anchor_nested_for_inner | **双层 for**，形状在内层；`and` 条件 | 锚点 | 74/92/174/184/T/F | MISMATCH `target_diff #21 report→n` | MATCH | SENTINEL |
| 20 | r17a_20_neg_clean_chain_in_loop | 循环内**干净 if/elif/elif/else** 链 | 负对照③ | 48/66/**90/90**/T/F | MATCH | MATCH | MATCH |
| 21 | r17a_21_neg_nested_if_no_tail | else 臂=嵌套 if/elif/else，**无尾随** | 负对照③ | 48/66/**90/90**/T/F | MATCH | MATCH | MATCH |
| 22 | r17a_22_neg_nested_if_in_then_arm | 「嵌套 if + 尾随」在 **then 臂** | 负对照（触发面） | — | MATCH | MATCH | MATCH |
| 23 | r17a_23_neg_tail_after_chain | 尾随挪到**整条链之外**（=缺陷输出声称的源码） | 负对照③ | 44/62/**170/170**/T/F | MATCH | MATCH | MATCH |
| 24 | r17a_24_neg_no_enclosing_loop | 01 的形状但**无任何循环** | 负对照④（唯一因④而异的场景） | 0/58/166/218/**F**/F | MATCH | MATCH | MATCH |
| 25 | r17a_25_probe_terminal_inner_merge | 尾随=`return acc`，`inner_merge` 是**终态块** | 探针⑤ | 48/72/98/106/T/**T** | MISMATCH `seq_len 40→39` | MISMATCH `seq_len 40→39` | MISMATCH |
| 26 | r17a_26_neg_shared_exit_no_outer_merge | else 臂含 `return`，外层**无独立 merge** | 负对照② | 48/80/106/**None**/T/F | MATCH | MATCH | MATCH |
| 27 | r17a_27_unconf_merge_signature_equal | 与 04 同形状，但外层 merge 首指令 == 尾随首指令 | 尺子盲区 | 44/62/166/242/T/F | MATCH（展平确实发生） | MATCH | UNCONFIRMED |

## 5. 实测汇总行

post-patch（`run_all.py --strict`，退出码 **0**）：

```
repros=26  MISMATCH=1  MATCH=25  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
```

pre-patch（把④原地塞回，同一批源文件，`D:/Temp/r17arm/measure.py prepatch`）：

```
[prepatch] n=26 MISMATCH=19
[base]     n=26 MISMATCH=1
```

即 **18 个锚点全部 pre-patch MISMATCH → post-patch MATCH**（远超「至少 6 个」的要求），
6 个负对照与 1 个盲区探针在两世界均 MATCH，无一被误伤。

## 6. 未达预期 / 需要如实记录的形状

1. **25（判据⑤形状）在两世界以同一签名失败**：`summarize` 里 else 臂尾随的
   `return acc` 被生成器并入臂内（seq_len 40→39）。这是**另一族既有缺陷**，
   与④无关（守卫数值 `term=True` ⇒ ⑤在两世界都驳回否决，走同一条路径）。
   按标注规则仍记 MISMATCH（post-patch 仍缺陷）。
2. **15 的缺陷签名是 `seq_len` 而不是 `target_diff`**：else 臂的嵌套 `if` 没有 else 时
   展平会多发射一条指令，尺子从长度维度抓到，而非终点漂移。
3. **27 是度量盲区**：pre-patch 的展平在源码层真实发生（`while`/`append` 被外提，
   `raw is None` 分支因此也会执行它们），但 CPython 为 `values[name] = n` 先发射
   `LOAD_FAST n`，与 while 头块首指令逐字相同 ⇒ `strict_compare` 的单指令终点签名无法区分。
   同族缺陷的真实覆盖面比 `target_diff` 计数更大。
4. **写锚点时的两处「噪声陷阱」**（首轮曾因此把可判别形状污染成两世界同缺陷，已剔除）：
   * BoolOp 里带 `not`（`strict and not isinstance(val, str)`）会另生一族
     `and`-短路嵌套 if 缺陷（01 的首版在两个世界都 MISMATCH），故 01/22/23/24 的条件统一
     改为不含 `not` 的形式；
   * 同一表达式里混用 `*` 与 `%`（`' ' * (len(text) % 4)`）会被生成器去括号成
     `' ' * len(text) % 4`，产生与本缺陷无关的 `seq_diff`（13 的首版）。
5. **break 尾随的姊妹形状**（`report.append` 不在 break 之前）在两世界同为
   `seq_len 48/49`：break 之后重复发射了循环退出代码。08 采用 append 在 break 之前的
   变体后成为干净锚点。

## 7. 复现命令

```sh
cd F:/Downloads/pythoncdc-main
PYTHONIOENCODING=utf-8 D:/Python/python.exe test_repros/round17_arm/run_all.py --strict
PYTHONIOENCODING=utf-8 D:/Python/python.exe test_repros/round17_arm/run_all.py 04 13 --show-diff
PYTHONIOENCODING=utf-8 D:/Python/python.exe D:/Temp/r17arm/measure.py prepatch   # 交叉验证
PYTHONIOENCODING=utf-8 D:/Python/python.exe D:/Temp/r17arm/trace.py  base        # 区域层数值
```
