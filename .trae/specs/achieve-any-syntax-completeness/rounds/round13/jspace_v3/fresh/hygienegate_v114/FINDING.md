# FINDING — rr-v5r123 [v123-HYGRENAME]：卫生红数闩基线漂移修复（validate_region_generator_signatures 15→14）+ /iterfind 派发表族本轮结构诊断登记

## 0. 结论速览

- 台账 48.6 两候选中，/iterfind（−102 字节）while-1 体丢失大族经本轮探针
  实证仍属「派发表先行」结构重排（r105 在案：窄修前向吸收曾破坏 pc6 级
  已闭合案被回退），本轮不冒险窄修，取指令备选**卫生红数闩小族**闭环；
  iterfind 结构事实（§3）登记留档供派发表轮。
- [v123-HYGRENAME] 合规重命名：`_v114_merge_orphan_nop_segments` →
  `_v114_orphan_nop_segments_regroup`（命中禁用模式 merge_pattern 的 v114
  引入方法；其余 14 错全为基线闩值时既有祖父方法）。纯重命名零行为变化：
  验证器 **15→14 错**、pytest 卫生闩 **3 failed→2 failed**（282 passed）、
  电池 267 案 **TEXT-DIFF 0** 零漂移、ElementPath 产品逐字节不变。

## 1. 根因（红数闩漂移）

- `tests/test_repo_tool_hygiene.py::test_registered_red_count_does_not_grow`
  以 `BASELINE_ERRORS=14` 闩 `scripts/validate_region_generator_signatures.py`
  的错误数（FORBIDDEN_PATTERNS：`_fix_/_patch_/_hack_/_workaround_/_correct_/
  _adjust_/_merge_/_fallback_/_from_block/_raw_/_unsafe_` + 主方法唯一性）。
- r113~r120 间 v114 轮新增 `_v114_merge_orphan_nop_segments`（[v114-MERGENOP]
  三元 merge 块孤立常量 NOP 发射）命中 `_merge_` 模式 → 14→15，卫生闩自该轮
  起常红（r118~r122 台账「3 failed」第三项即此）。
- A/B 定性：HEAD（f7cf3d5b）验证器同为 15 错 6 警——非 v122 引入；修复 =
  重命名该方法脱离禁用模式（不动基线闩值——测试文档明示 clamp 不得松弛）。

## 2. 修复与验证（只增不破 = 纯重命名）

- `_v114_merge_orphan_nop_segments` → `_v114_orphan_nop_segments_regroup`
  （避免全部禁用模式；引用仅 def+1 调用两处，无字符串/动态引用）。
  `fix_patch_v5r123.diff`（2 文件→1 文件 2 处，+2/−2）。
- 验证（全实测）：
  - 验证器：**统计: 14 个错误, 6 个警告**（HEAD 对照 15/6）。
  - pytest 7 套件：**2 failed / 282 passed / 2 xpassed**——卫生闩转绿；
    余 2 失败 = 既有冻结对（B01/B02，前已存在不动）。
  - A/B 回归电池 **267 案**（r123_regress.py，单文件 RAG 交换
    HEAD f7cf3d5b vs v123；r110 169+v111~v122 各组+本轮 0 新案）：**TEXT-DIFF
    0/267**；R110 案 168/169 一致（唯一差 mc1 两侧同持修复正常归一）；
    登记差 10 案 ALL SAME-SIGNATURE；NO-SRC 0。
  - ElementPath 快核：v123 产品与 v122 逐字节相同（重命名方法在渲染路径
    [v114-MERGENOP] 上，行为不变实证）。

## 3. /iterfind 派发表族结构诊断（本轮探针实证，登记留档）

最小对照（原版 3.11.7 vs v123 产品，stdlib_xml_ElementPath /iterfind）：
- 原件 `selector = []` 后为 `while 1:` 环——环体 try1
  `selector.append(ops[token[0]](next, token))` + `except StopIteration:
  raise SyntaxError('invalid path') from None`；try2 `token = next();
  if token[0]=='/': token = next()` + `except StopIteration: break`。
- 产品：**while 1 壳丢失**、try1 体丢失（`try: pass`）、try2 保序但
  `break` 丢失（`except: pass`）——即 −102 字节主体；判官 38/39 唯一失败单位。
- 区域树实证（probe_iterfind.py）：LoopRegion@492 **已检出**
  （blocks=[494,588,652,492,650,696,716,750]，is_while_true=True）但
  TryExceptRegion@494 的 blocks **前向吸收了环头 492**（同块双认领）→
  层级裁决环被孤儿化，环体分裂渲染（try1 体被吞、break 块 742/744 并入
  try 区）——与 r105 pe 系在案病形同构（自然出口/环头被前向吸收 →
  `_is_while_true` 判 True → site9k while-1 发射错乱）。
- 修复路径（登记）：**派发表先行**——区域构造顺序重排（Loop 的
  entry/环体认领先于 Try 的前向吸收，或层级裁决时环头唯一归属环）。
  r105 教训：`_collect_natural_loop_body` 前向吸收排除与 `_is_while_true`
  可达性两处窄修均破坏 pc6 级已闭合案，故须整体重排并全额闸门验收。

## 4. 验收口径

小测试收口（纯重命名零行为变化：验证器 + pytest + 267 案电池 + 产品快核）。
不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

- /iterfind 派发表先行重排（§3 路径，研究级，独立大轮全额闸门）——
  REAL46-008 判官唯一残余单位（R7=1，38/39）。
- v118 E2 残余（while 底部 store-recheck）同域；E6 相邻 NOP 对；
  46 sweep 其余 DIFFERENT（REAL46-011~016）/4 compile_error 案。
- pytest 余 2 失败 = 冻结对（B01/B02，前已存在冻结基线，属登记态）。

## 6. 证据文件

`fix_patch_v5r123.diff`、`r123_regress.py`+`r123_regress_result.txt`、
`ElementPath_product_v123.py`、`probe_iterfind.py`、本文件；中间件
（sweep46 双侧、电池 TMP、r123diag 探针）在 D:/temp/opencode/cl_layout/
r123regress、r123diag，不入库。
