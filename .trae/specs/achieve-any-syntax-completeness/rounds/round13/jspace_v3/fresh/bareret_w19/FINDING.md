# FINDING — rr-v5r115 [v115-BARERET]：W19 元组解包尾部准入把非尾声块显式裸 return 当隐式丢弃（真实 R1 语义缺陷族）

## 0. 结论速览

- 修复 REAL46-031（packaging/version.py）`/Version/__setstate__` 判官盲区差异
  （co_code 818 vs 816，rr-v5r114 登记未修）：整案权威判官维持 **EQUAL
  （diffs=[])**，盲区递归字段比对 **68 code objects 全部字节相等**（v114 为
  1 差异）。
- 该族是**真实 R1 语义缺陷**而非纯字节差（repro4 运行时实测）：if 臂尾的
  显式裸 `return` 被剥离后，返回路径落入本块之后的语句——
  ORIG `m(6元组) → None`（尾部语句不执行）vs PROD `→ ('tail', None)`
  （尾部语句被执行）。

## 1. 根因（settrace 行级追踪定位，`probe_w19_trace.py`）

- 疾病位点：`region_ast_generator._build_attr_target_unpack`（[W19] 属性/下标
  目标元组解包解析器）尾部准入——`_w19_tail` 恰为
  `[LOAD_CONST None, RETURN_VALUE]` 时一律判 `_w19_is_implicit_ret=True`
  并**剥离不发射**（注释口径「尾部隐式 return None 按 RETURN_NONE 语义剥离」）。
- 判据缺口：该 2 指令尾对有两种来源——①函数尾声块的隐式 return（丢弃安全，
  反编译源码的函数尾隐式 return 重编译再生，字节等价）；②**源码显式裸
  `return`**（早返回；CPython 内联编译为同一 2 指令对）。二者局部不可分，
  但结构可分：①只发生在 cfg **最高偏移块**（函数尾声块，控制流终点）；
  ②发生在臂内/中间块。W19 旧判据不分 → ②被误剥离。
- 机制链（repro4）：`if len(state)==6: self._p, self._q = state[:2]; return` 的
  then 臂块 96 = [UNPACK 前缀..., LOAD_CONST None, RETURN_VALUE] → W19 认领
  发射仅 Assign、剥 return → IfRegion then 臂丢 Return → 渲染 `if/elif` 无
  return → 重编译臂尾变 JUMP_FORWARD 落到 if 链后（−2 字节 + 控制流改变）。
- 同域排除：[B107] `_build_chained_complex_target_assign` 无尾部剥离逻辑；
  `_is_implicit_return_block` 各用点（4804–5028）为 R8-B121/R44A return-sink
  分类（纯尾声块判定，带独立守卫，语料 fire census 在案）——非同病。

## 2. 修复（`core/cfg/region_ast_generator.py` [v115-BARERET] +25/−0，只增不破）

- W19 尾部准入处新增尾声块判据：`_w19_is_implicit_ret` 为真时，取
  `self.cfg.blocks` 全块最大 `start_offset`；本块偏移 ≠ 最大偏移（非尾声块）
  → **放弃认领**（return None），整块交回通用路径——其 RETURN_VALUE 语句
  边界归约（[Phase 7 根因1] 位点）已实证按 `Return(None)` 正确发射
  （repro1/4 修复后产品文本 `return None` + 字节相等直证）。
- 尾声块（偏移 == 最大偏移）维持既有剥离逐位不变（C3）——丢弃后由函数尾
  隐式 return 再生，字节等价（C1/C1b 控制案实测）。
- 判据全同层结构事实（块偏移 vs 全块最大偏移），无名字/偏移白名单/计数特例。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r115.py` 9 案，A/B 文件交换 HEAD `5e16ae25` vs v115）

| 案 | 形 | HEAD | v115 | 判定 |
|---|---|---|---|---|
| E1_bare_ret_tail | 内层 if 臂尾裸 return + 非互斥后随语句 | TEXT-DIFF（return 丢、字节错） | 重编译 BYTE-EQUAL + 运行时 ORIG==PROD | PASS |
| E2_bare_ret_nested | __setstate__ 形双裸 return 嵌套（REAL46-031 精确形） | TEXT-DIFF | BYTE-EQUAL | PASS |
| C2_bare_ret_last | `if x:` 臂内裸 return（非尾声块；初判控制、实测同为功效） | TEXT-DIFF | BYTE-EQUAL | PASS（功效） |
| C1/C1b | 尾声块解包（`a, b = g()` 函数末/仅此一句） | — | 逐字节同 + BYTE-EQUAL（尾声剥离保留） | PASS（C3） |
| C3_valret_arm | 臂尾带值 return | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C4_attr_unpack | `a, self.b = f()` 属性目标解包（W19 核心形）无 return | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C5_quot_shape | `x, y = f(); return x, y`（quotation 形，尾非隐式） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C6_unpack_mid | 函数中部解包（尾为空） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |

### 3.2 运行时对照（`repro4_sem.py`）

- 修复前：ORIG `m(6元组) → None, _tail=None` vs PROD `→ ('tail', None),
  _tail=1`（真实分歧）。
- 修复后：ORIG==PROD（`None, _tail=None` / 2 元组路径逐项一致）。

### 3.3 REAL46-031 全闭合

- 权威判官（`sd_031_v115.py` → `semantic_REAL46-031_v115.json`）：
  **EQUAL（diffs=[]）**。
- 盲区递归字段比对（68 code objects：co_code/exceptiontable/names/varnames/
  argcount/flags/consts 按名归一）：**0 差异**（v114 为 1：__setstate__）——
  packaging/version.py 产品与原件全嵌套逐字节相等。

## 4. 验收（小测试口径：全量闸门按用户政策只留给大改动）

- A/B 回归电池（r115_regress.py：r110 169 + v111 15 + v112 15 + v113 15 + v114 12
  + 本轮 9 案源）：**TEXT-DIFF 3 / 223 可执行案**，恰为本轮 3 功效案
  （E1/E2/C2）且重编译签名全部 BYTE-EQUAL；其余 220 案 TEXT-SAME；既有登记差
  10 案 **ALL SAME-SIGNATURE**；R110 案 168/169 一致（唯一差 mc1 = r110 轮功效
  案两侧同持修复正常归一）；NO-SRC 0。
  （过程登记：电池脚本标记串替换链曾产生奇美拉标记 `v115-ARGOR` 致自愈误触发、
  EV 矩阵副本未加 `__main__` 守卫在 import 时执行 A/B 交换——两处均已修正后
  重跑，上列读数为修正后实测。）
- pytest 7 套件冻结对一致（2F+product_freshness 预存在陈旧）。
- 比较器冻结：pyc_verify.py FE1902A9、semantic_diff.py DBCB1E24、tests/ 零改动。
- 不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 证据文件

`fix_patch_v5r115.diff`、`matrix_v5r115.py`、`r115_regress.py+result`、
`repro1/3/4+运行时对照`、`sd_031_v115.py+semantic json`、
`REAL46-031_product_v115.py`、`probe_w19_trace.py`（settrace 定位）、
本文件。
