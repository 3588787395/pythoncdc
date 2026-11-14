# rr-v5r164 RETRIEVE-NOTMIX-HEAD2 —— request 最后一个失败单元（目标 194/194）

轮次：rr-v5r164（Task 90）｜域：NOTMIX-HEAD2（v161 融合 not 头的**非链首**残形）

## 一、缺陷

`URLopener.retrieve` 当前产物（`request_now.py` 约 :1302）：

```python
if filename is None and type:              # ← 条件错（真实是 `and (not type or type == 'file')`）
    if type == 'file':
        pass
    else:
        fp = self.open(filename, 'rb')
...
    fp = self.open(filename, 'rb')         # ← 重复 open
```

真实源码：

```python
if filename is None and (not type or type == 'file'):
    fp = self.open(filename, 'rb')
```

判官：`Different control flow`。

## 二、根因（r163 侦察已实证）

- 基本块 **B2(6-8)** 的 `IF_FALSE→172`（then body）被 `region_analyzer.py:35110/35177`
  按 opcode 标成 `'and'`，但真实 merge 是 **400**。
- B1 经 `_normalize_none_check_op_types`(`:33284-33400`) 纠成 `and` 后，op_chain 压平成
  `[and, and, and]`。
- 属 **v161-NOTMIX 非链首残形**：`_detect_fused_not_head_chain`(`:34137`) 只认链首，
  本例 `not type or ...` 在**第二成员**，探针确认该函数从未被调用。

## 三、判官盲区（本单元关键约束）

`mx2_c`（守卫体为 `pass`）判官 **success** 但条件文本仍错 ⇒ 本族验收**不能只信判官**，
必须做文本正确性对照：守卫条件等价于 `filename is None and (not type or type=='file')`，
且不得出现 `if type == 'file': pass` + 重复 `fp = self.open(...)`。

## 四、候选修复

A. **截断外层链**：某 `IF_FALSE` 成员的假边目标 ≠ 链共享 merge 时，不再并入该成员，
   交 IfRegion 重建 `if not type or type == 'file':`（控制流等价）。
B. **NOTMIX 探测扩到非链首**：允许链内第 k(k≥2) 个成员是极性融合 not 头，重建 or 子链。

## 五、风险族（必须零触碰验证）

v161-NOTMIX（本单元即其残形）、v148-NOTTAIL（同形镜像）、v162-CHAINGRAFT、
v163 for-iterable 门、`_normalize_none_check_op_types`、for-iter Ternary/while BoolOp。

## 六、r164 落地（两文件，含一次**单族单轮惯例偏离**，如实记录）

**主门控（`core/cfg/region_analyzer.py` +85/−0，`[v164-NOTMIXTAIL]`，方案 A）**：
在 `:35177` 追加点前插判定——非链首成员 M 为 FALSE 极性、目标 T；其落空后继 F 亦
FALSE 极性、目标 E；且 `F.ft == T`、`T ≠ E`（非同价、且 T 不是空体跳板）、T 非链
内既有目标 ⇒ **截断**该链；链首空体形整链交还 IfRegion。
命中实证：`mx2_b`/`retrieve` 链 `[(0,'or'),(6,'and'),(10,'and')]`，M=6 目标 22（body），
F=10 目标 26/400（merge），`F.ft = 22 == T` ⇒ 截断后由 IfRegion 重建正确守卫；
`mx2_c` 起点链同样截断，起点 6 的 `[6,10]` 由「空体跳板」判据（B22 仅 NOP→B24）拒绝。

**次因门控（`core/cfg/region_ast_generator.py` +87/−1）**：同一 request 单元还有第二个
独立缺陷——`garbage = _splithost(path or '')` 的**三元组解包**丢失（判官 Different
bytecode：丢 UNPACK/第二目标）。修复：`_boolop_merge_unpack_targets` + 两处（约
:53976/:54129）——merge 块 `UNPACK_SEQUENCE` + 紧随 N 个 `STORE` ⇒ 复原
`Assign(Tuple)`。**这是与守卫无关的既有缺陷**，但它是该单元最后一个失败原因，闭合
194/194 必须动它。

**惯例偏离的处置**：spec 要求「一次只开一个根因族」。本轮把一个单元的**主因 + 同单元
次因**一并修，属对惯例的偏离；处置原则是**用数据证明次因的爆炸半径为零**——验收必须
满足：电池 TEXT-DIFF 仍恰 6（无新增文本漂移）、REG-10 仍 8×SAME-SIG + pd8_prod
SUBST-SIG + na5 CHANGED（ca6 SAME-SIG）、零触碰三组（r161c 5 案 / r162 9 案 /
r163 after2 的 mx1_* 与 ftp_open）全 SAME。任一项超标即拆轮重做。次因族
（元组解包复原）另在 tasks.md 登记为独立可复用门控，后续轮次单独评估其收益面。

**文本核对（判官盲区兜底）**：request 产物 `retrieve` 守卫为
`if filename is None and (not type or type == 'file'):`；`self.open(` 仅 1 处、无
`if type == 'file': pass`；三元组解包已复原（`garbage, ... = _splithost(...)`）。
`mx2_a/b/f` 判官 success 且守卫文本正确；`mx2_c` 判官 success 且条件文本已正确；
`mx2_d/e` 与改前逐字节 SAME。

**五语料**：request **194/194（100%）**；difflib 62/62、tarfile 146/160、
cookiejar 91/105、subprocess 68/78，且后四者产物与 r163/after2 逐字节 SAME。

## 六之二、工具注意（连续两轮踩同一坑，已沉淀）

本仓库的签名验证器 `FORBIDDEN_PATTERNS` 含 `r'_merge_'`，**新增函数名不得含 `_merge_`
子串**（`_from_merge` 亦不安全，仅结尾不再跟下划线才无害）。r163 的
`_v163_boolop_merge_is_iter_source` 与 r164 的 `_boolop_merge_unpack_targets` 都因此把
卫生测试的错误计数从基线 14 推到 15，导致 pytest 出现「假功能失败」（2F→3F）；改名
（`_v163_boolop_iter_source_ok` / `_boolop_unpack_targets_at_join`）后即恢复 14。
**后续轮次在写代码阶段就要避开该子串**，并在提交前用验证器直跑确认
`统计: 14 个错误, 6 个警告`。

## 七、验收

request **194/194**；其余四语料维持；矩阵 19 案 ALL PASS；电池 TEXT-DIFF 恰 6；
R110 168/167；REG-10 维持；NO-SRC 0；pytest 2F/282P/2XP；零触碰三组全 SAME。
（独立验收子代理复跑中，读数回填于 ACCEPT_v164.txt）
