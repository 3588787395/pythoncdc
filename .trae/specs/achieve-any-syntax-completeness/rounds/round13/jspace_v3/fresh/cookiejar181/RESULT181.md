# rr-v5r181 — cookiejar CJ6 TRYELSE (`deepvalues`) 收口报告

仓库 `F:\Downloads\pythoncdc-main`。唯一源码改动：`core/cfg/region_ast_generator.py`
（`git diff --numstat` = **25 / 1**，单个 hunk `@@ -41561,7 +41561,31 @@`，位于 R27-9
else 臂尾归属判据内部）。补丁脚本 `D:\temp\opencode\cl_layout\r181\fix181.py`
（anchor count==1、utf-8-sig、CRLF 保持、py_compile、幂等、`--revert` 可回退）。
本轮**零探针残留**（`CJ6DBG`/`V181DBG` grep = 0）；未改 `.trae/`、未 commit/push/stash。

## 1. 根因（逐指令 + 异常表实测，非 recon 定性）

`deepvalues` 源码（cookiejar.py L1227-1239）把 `yield from deepvalues(obj)` 写在
`try/except/else` 的 **`else: ` 臂内**。CPython 3.11 的布局：

```
 82..94   try 体 (obj.items)                     ← 异常表 [82,96) → 144
 96..98   else 臂首句 mapping = True             ← 不受保护
100..140  else 臂续：yield from（setup + SEND 自环）← 不受保护
142      JUMP_FORWARD 176                       ← try 语句的「越过 handler」跳转
144..174 handler (AttributeError: pass)
176      if not mapping: yield obj
```

修复前产物把 else 臂截断在 `mapping = True`（块@96），`yield from` 整段（块@132
SEND 自环 + 块@140 POP_TOP/JUMP_FORWARD）留给宿主 `for` 循环当 try 之后的兄弟语句发射：

| 项 | 修复前产物 | 原始 |
|---|---|---|
| 首个差异 | idx17 `JUMP_FORWARD to 58` | idx17 `LOAD_GLOBAL deepvalues` |
| 指令搬位 | 9 条（LOAD_GLOBAL…POP_TOP）从 idx17 搬到 idx29 | — |
| loops | `[(72,'JUMP_BACKWARD_NO_INTERRUPT',68), (78,…,16), (86,…,16)]` | `[(48,…,44), (78,…,16), (86,…,16)]` |
| 异常表 | `(24,30,36,1,F) (36,46,52,2,T) (50,52,52,2,T)` | `(24,30,54,1,F) (54,64,70,2,T) (68,70,70,2,T)` |

**异常表逐条结论**：第 1 条保护区间 `(24,30)` 不变、**target 54→36**（内容型变化：
handler 链整体被搬到 18 字节之前）；第 2、3 条 `start/end/target` 全部 −18 平移
（`36..46→52` / `50..52→52` 对 `54..64→70` / `68..70→70`）。三条都是同一次搬位的派生物，
**不是** erratum/recon 所说的「3 条只有 1 条变」——实为 1 条内容变 + 2 条整体平移，
修复后三条与原始**逐字段相同**。

根因位置：`region_ast_generator._generate_try` 的 R27-9「else 臂尾块归属」不动点
（`_r27_arm` 扩充）判据为「候选块**全部前驱**已在臂内」。`yield from` 的 SEND 轮询块
（块@132）以**自身为前驱**（自环回边），该判据永不成立 ⇒ 臂尾只到块@96；
后续块@132/140 从未被认领，最终由 `_loop_dispatch_block`（`is_yield_from_loop` 子区域
分支）在宿主循环里发射成 try 之后的兄弟语句。

## 2. 修复谓词 `[v181-TRYELSE-ARMSELF]`

```
                            if all(id(_p) in _r27_arm for _p in _r27_ps):
→                           if all(id(_p) in _r27_arm or _p is _r27_b for _p in _r27_ps):
```

自前驱（`p is b`，块内回边自指）不引入任何臂外控制流，故不否决臂成员资格；
**非自前驱仍必须全部在臂内**。判据只读 CFG 前驱身份 + 块偏移区间（无名字/阈值/异常表数值）。
认领后块@132 走既有 else 臂发射循环 → `get_entry_region_for_block` → `is_yield_from_loop`
子 LoopRegion 整树重建 `Expr(YieldFrom)` → `ast.Try.orelse`；块@140 由该子区域一并登记。

产物（修复后）：

```
        else:
            mapping = True
            yield from deepvalues(obj)
        if not mapping:
            yield obj
```

## 3. 判官

- `deepvalues` 判官 **EQUAL**（`cf_equiv=True` 18/18 节点 24/24 边、46/46 指令、
  loops 三条逐条相同、异常表三条逐字段相同）。
- cookiejar **102/105 → 103/105**；失败名单 3→2：去掉 `deepvalues`，
  余 `_timegm` / `set_ok_path`（与任务书一致）。

## 4. 其他语料（对照 r180verify/products）

| 语料 | 读数 | 产物 |
|---|---|---|
| request | 194/194 | BYTE-SAME `db2172e8f1a69af6` |
| difflib | 62/62 | BYTE-SAME `d70df6006a50f33f` |
| tarfile | 156/160 | BYTE-SAME `fcb8a7fbb7b246b2`（失败 4 项同前） |
| subprocess | 75/78 | BYTE-SAME `557b9b0bfe9ef4e2`（失败 3 项同前） |
| cookiejar | 103/105 | DIFF `d39c77eeb6774b18`（设计内，+4 字节） |

## 5. 458 电池（硬门）

`r181\battery181.py`（由已提交 `...\fresh\tarfile167\r170_regress.py` 复制，仅改
TMP/OUTDIR/EV；仓库内脚本未动）先删 scratch 再跑：

- `r181battery\ev\r161_regress_result.txt`（22636 B）与 r180 的
  **SHA256 逐字节相同** `35320ED2…7C79`。
- TEXT-DIFF **17/458**，恰为允许集（R110 7 + V111 3 + V118 1 + V161 6），**全 BYTE-EQUAL**；
  集外新增 0、缺项 0。
- `C7_skipedge` **TEXT-SAME**；R110 **161/167**；REG-10 段与 r180 逐字 IDENTICAL。

## 6. AST / 剪枝风险

五语料 `If`/`stmt`/`Pass` 前后**全部 +0**（request 286/1725/17、difflib 114/737/9、
tarfile 325/1754/16、cookiejar 240/1213/8、subprocess 270/1125/22）。
`deepvalues` 单元内：源码 / r180 / r181 = **If 1 / stmt 10 / Pass 1** 三者完全相同
（同一批语句改归属位置，无新增、无删除、无幻影 if、无 Pass 增删）。

## 7. 红线 + 零触碰

- 零触碰 38 案：**PASS**（37 案 BYTE-SAME；唯一 DIFF = 允许例外 r164/request_final，
  且等于本轮 request 产物；非允许差异 0）。
- 红线 23 个单元（cookiejar 12 名含 `_str2time`；subprocess 8 名 → 11 单元，
  `_execute_child`/`__del__`/`__exit__` 各双 class）：**ALL BYTE-SAME**。
  `deepvalues` 单独列（设计内变化，13→13 行，`+1` 缩进层级）。

## 8. 与 r172 / r178 同域判据的交叉确认

- `git diff -U0` = **1 个 hunk**，落在 R27-9 else 臂尾块归属内部；
  `v172-NESTED`/`v172-RAISE`（r172）与 `v178-ORPHAN-HDR`（r178，`_rag_is_unemitted_try_handler_entry`）
  的代码与注释**一字未动**（v172 另动 `region_analyzer.py`，本轮该文件 **0 改动**）。
- r172 的两个目标单元 `_check_timeout` / `_execute_child`(双 class) 与 r178 的目标
  `Popen.__exit__` 均在本轮红线表内，**逐单元 BYTE-SAME**；subprocess 产物整体
  逐字节未变（75/78、失败名单同前）。
- tarfile 产物逐字节未变（r172 判据在 tarfile 侧的形态全部保持）。

## 9. 卫生

`scripts/validate_region_generator_signatures.py` → **统计: 14 个错误, 6 个警告**（达标）。

## 10. numstat

```
25  0  .trae/specs/achieve-any-syntax-completeness/tasks.md   ← 本轮开始前既有改动，非本轮
25  1  core/cfg/region_ast_generator.py                       ← 本轮唯一改动
```

## 11. 复现/回退

- 应用：`D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r181\fix181.py`
- 回退：同命令加 `--revert`（实测回退后 `git diff` 为空、源文件 sha
  `5FD49C64…A800` 与 HEAD 一致；再应用后产物 sha 与首次应用**逐字节相同**）。
