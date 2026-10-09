# FIX T12-21 — elif 臂候选必须只由「本链头所属区域」进入：语句回来了（net 0、hunks 25→4），零连带

票号 **T12-21**（承接 `DIAG_T1212_MATCHER_MERGE_AS_ENTRY.md` §8/§9；T12-18 的收集侧替身）。
靶文件 `IQEngine/plugins/plugin_system_matcher/matcher.pyc`（16/17，唯一失败单元
`<module>.DefaultMatcher.match` ⇒ 整文件翻转候选）。

## 1. 改动（一行判据 + 六节注释）

施工点：`core/cfg/region_analyzer.py` `_check_elif_chain` 接受首个臂候选处
（HEAD 行 `:21852`，即 `conditions = [first_else]` **之前**）：

```python
            _r1221_howner = self.block_to_region.get(header_)
            if _r1221_howner is not None:
                for _r1221_p in (first_else.predecessors or []):
                    if self.block_to_region.get(_r1221_p) is not _r1221_howner:
                        return None
```

语义：臂条件块在字节上只被**上一条臂的假边**进入；若候选存在归**别的区域**（外层 LoopRegion
或兄弟语句的 BoolOpRegion）的前驱，它就是**下一条语句**的测试块，不是一条 elif 臂。
只读 `block_to_region` 归属与 `predecessors`（都是识别期已填实的表），
不含偏移、指令数、名字（rules.md §1.4 G4）。`return None` 走的是该函数既有的拒绝路径
（`:21850`、`:22385` 同形），调用方按「无更深 elif」处理，不新增第二套口径（C3 守卫封闭）。

字节：`e926a54f17753b33` → **`48b812e60ef52d27`**（备份 `D:/Temp/r142/pre_t1221_analyzer.py`；
构建器 `D:/Temp/r142/patch_t1221_land.py`：锚行唯一性、CRLF 纯净、行数增量、标记命中、
`compile()` 全部在写盘前断言）。

## 2. 判据的分离度是**实测**出来的，不是设计时猜想

惰性探针 `D:/Temp/r142/t1220_scope.py`（CLI-vs-CLI 自证：产物 13255 = 13255）在 `:21852` 打印每个
被接受候选的前驱及其归属：

| 候选 `first_else` | `header_` | 前驱 | 前驱归属 | 判据 |
|---|---|---|---|---|
| 1570 | 1444 | 1444, 1486 | BoolOpRegion@1444 ×2 | 通过（真 elif） |
| 2038 | 1912 | 1912, 1954 | BoolOpRegion@1912 ×2 | 通过 |
| 2338 | 2212 | 2212, 2254 | BoolOpRegion@2212 ×2 | 通过 |
| 2846 | 2484 | 2484, 2526 | BoolOpRegion@2484 ×2 | 通过 |
| **2164** | 2038 | 1834,1884,1896,1908,**2038,2080** | **LoopRegion@6 ×2、BoolOpRegion@1884 ×2**、BoolOpRegion@2038 ×2 | **拒绝** |

⇒ 四个真 elif 全部满足判据，被误收的语句测试块 @2164 被拒 —— 这是本判据唯一的实测依据，
也是 T12-18（删侧钳制）失败的对照：@2164 的 `block_to_region` 本来就归链，
必须让它在**进入成员表之前**被拒，否则区域活着也不分派（见 DIAG_T1212 §9）。

## 3. 七文件 A/B（`D:/Temp/r142/t1221_candidate.py`，镜像内跑，仓库当时未动）

```
BASE m 16/17   CAND m 16/17   DIFF 13255->13345
BASE q 153/153 CAND q 153/153 SAME_as_BASE
BASE h 29/30   CAND h 29/30   SAME_as_BASE
BASE w 55/58   CAND w 55/58   SAME_as_BASE
BASE e 12/13   CAND e 12/13   SAME_as_BASE
BASE b 84/85   CAND b 84/85   SAME_as_BASE
BASE d 27/27   CAND d 27/27   SAME_as_BASE
```

（`load_daily` 在 HEAD 代码下读 27/27，即它已不是残余项；残差表里那条 26/27 是
label 12 那轮**候选构建**产物留下的，撤回后不再成立。）

hunk 剖面（同一次运行内对比，`D:/Temp/r138/hunk138.py`）：

```
BASE  len 776/766  net=+10  hunks=25  real=1  reloc=24  deleted=34  inserted=24
CAND  len 776/776  net=+ 0  hunks= 4  real=0  reloc= 4  deleted= 4  inserted= 4
```

⇒ **被吞的 10 指令语句头回来了**（`real=1 → 0`，指令数完全对齐），
残余 4 处恰好是 B138 §Task1bis 预先点名的四个「真目标差」，逐条对得上：

| hunk | orig | prod |
|---|---|---|
| @1322 | `JUMP_FORWARD ->@2464` | `->@3210` |
| @1382 | `POP_JUMP_FORWARD_IF_TRUE ->@1444` | `->@1696` |
| @1910 | `POP_JUMP_FORWARD_IF_TRUE ->@2164` | `->@2034` |
| @2210 | `POP_JUMP_FORWARD_IF_TRUE ->@2464` | `->@2334` |

单元读数仍 16/17：判据解决的是**省略**，四条**落点**属于生成端的链/操作数分组
（`pythoncdc-falsified-residual-axes` 项 13 的结论），尚未攻。

## 4. 为什么值得跑满 402 门

本轮（round 12）此前 0 翻转，役规要求每轮至少解决一个 pyc。本改动是本轮第一个
**改变产物且七文件零连带**的候选；落不落地按门判据说话，不按判据命中说话
（`fires without flips` 规则）。门（label 13 vs 12，链日志 `D:/Temp/r142/install_and_gate13_*.log`，
gate_chain13.sh 严格串行 regen→verify→report→checks→residual）读数待填：

- regen `ok= / bad=`
- `[units] … -> …` / `[files] … -> …` / `[gates] 翻正单元= 新增失败单元=`
- checks：quotation / small34 / selfcheck / 七套件（须仍 `2 failed / 280 passed / 2 xpassed` 同名两红）
- residual 表：残余文件/单元数与 `UNREGISTERED`

## 5. 四条落点的**同一宿主**（与 17/17 oracle 文本逐字对照，只读比对 `diff --strip-trailing-cr`）

`diff D:/Temp/r138/m_or_full.py D:/Temp/r142/wt/cand_m.py` 只剩三处（155–179 行窗口），
每条都能对上 §3 的 hunk：

| 残余形状（产物） | oracle（字节正确） | hunk |
|---|---|---|
| `if not (A∧B):` 套 `if (A∧C):` | `if (A∧B) or (A∧C):` | @1382 |
| 头 `… and C:` ＋ 体内 `if X or BUY…` | 头 `… and C and not X:` ＋ 体内 `if BUY…` | @1910 |
| `if symbol[:3] in ('688','689'):` 体内 `if X or BUY…` | 同头 ＋ 体内 `if not X: if BUY…` | @2210 |
| 臂尾 `JUMP_FORWARD ->@3210` | 应落 `->@2464`（if/else 汇合） | @1322 |

⇒ 三处**同一机制**：一条语句头里的 `and`/`or` 链没有被整条重建为**一个**条件表达式，
末腿被下放成了体内臂的条件（@1322 只是它顺带造成的落点差）。区域侧证据与此一致：
同一个头测试被拆成 `IfRegion@1834/1884/1908/1912`（`cond` 同为 1896/1908/1954，
`merge` 同为 2164）加 `BoolOpRegion@1884(merge=2208)/@1912(merge=2038)/@2038(merge=2164)`，
即腿的分段发生在识别/分组层，而 oracle 要的是「一头一区域 + 一条完整布尔表达式」。
这正是 `pythoncdc-falsified-residual-axes` 项 13 记的那道未攻的两层生成端改动
（扁平 `{'blocks':[…],'op':'or'}` 表达不了 `(A∧B)∨(A∧C)`，还需要极性-aware 的尾承接）。

下一票 **T12-22** 的边界：先只处理**@1910/@2210 这一形**（头的末腿 `and not X` 被下放成体内
`X or …`），因为它在 oracle 里允许两种等价写法（`if not X:` 嵌套 与 头内 `and not X` 扁平，
B138 实测两者字节相同），改动面比 `(A∧B)∨(A∧C)` 的操作数树小；@1382/@1322 留作第二刀。


## 6. 判决（门出数后填写；不得预先写「已解决」）

- 若 `翻正单元 ≥ 1` 且 `新增失败单元 = 0` ⇒ 保留 `48b812e60ef52d27`，
  本轮以实测翻转收尾，残余重算并入 `RESIDUAL_R13.md`；
- 若 `翻正单元 = 0` ⇒ **逐字节撤回**到 `e926a54f17753b33`（`cp D:/Temp/r142/pre_t1221_analyzer.py`），
  并连同四条落点残差登记为共要件（补丁留在 `D:/Temp/r142/analyzer_t1221_land.py`），
  按项 13 换到生成端链/操作数分组轴；
- 无论哪种，残余表由 `residual_report.py` 重发，不手改数字。
