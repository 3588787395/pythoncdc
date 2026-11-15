# FORM_AUDIT — r171 形态级（非判官）核验（终版）

> 对象：`fix171.py`（3 文件 6 anchor）引起的**文本**变化。判官看不见形态，故逐案把
> 「改前（HEAD=r170 基线）产物 / 改后产物 / 真实源码」三者对读。
> 取证：`r171/work/audit_dump.py`、`audit_diff.py`、`corpora_diff.py`、`one.py`、
> 逐案原文 `r171/work/audit/<case>.txt`、`r171/work/bisect/*`（逐锚点产物）。
> 源码来源：电池 `build_cases()` 的 `_src`（R110 = `.trae/.../fresh/**`、V118 =
> `matrix_v5r118.CASES`）；标准库语料取 `D:/Python/Lib/**`。

## A. 12 个新增 TEXT-DIFF 逐案判定

| # | 案名（组） | 改前 → 改后（一句话） | 判定 | 证据 |
|---|---|---|---|---|
| 1 | `mk_iterencode`（R110） | 两处各 5 条连续重复 `continue` → 各余 1 条 | **更接近**（余 1，部分闭合） | head:56-61/145-150 → cur:56/140；源 `_iterencode_list` 在 `yield from chunks` 后无 continue |
| 2 | `yp2`（R110） | 去掉循环体末尾源码里不存在的 `continue` | **更接近** | head L17 → cur 删除；源末句 `if v > 0: yield enc(v)` |
| 3 | `te_variants8`（R110） | v8 末尾伪 `continue` 删除 | **更接近** | 源 v8 `else: if v == 0: continue / out.append(v)` |
| 4 | `fdt`（R110） | `break` 之后的死 `continue` 删除 | **更接近** | 源 `elif isinstance(base, EnumType): … break` |
| 5 | `pc1`（R110） | 中间态 break 臂 + `elif` 被改成兄弟 `if`（源为 elif）→ **已加「break 臂 × elif 候选」宿主门，恢复 elif** | 中间态更远 → **已修**（现 TEXT-SAME） | 源 `if isinstance(d,int): … break` / `elif hasattr(d,'a') …` |
| 6 | `pc2`（R110） | 同上（源为 elif） | 中间态更远 → **已修**（现 TEXT-SAME） | 源 `elif d > 2:` |
| 7 | `pc3`（R110） | 中间态去掉尾伪 continue；加门后随 break-elif 形态回基线 | **等价**（= r170 基线，无回归） | 现 head==cur（9AED5861） |
| 8 | `pc4`（R110） | 中间态 `elif`→`if` 更接近（源为 if）；加门后回基线 elif | **等价**（= 基线；让位不可判对） | 现 head==cur（D48B0E47）；pc1/pc2/pc4 字节码同形不可判 |
| 9 | `pc12`（R110） | 两处 `else: pass` 后的重复 `continue` 删除 | **更接近** | 源两处 `else: pass` |
| 10 | `pc9`（R110） | 循环体末尾伪 `continue` 删除 | **更接近** | 源 `n += 3` 收尾 |
| 11 | `pm1`（R110） | 同上（`else: pass` 后伪 continue） | **更接近** | 源 `else: pass` |
| 12 | `E3_andnot_nochainstmt`（V118） | for 体末尾伪 `continue` 删除 | **更接近** | 源三分支 yield，无尾 continue |

**汇总：更接近 8（1,2,3,4,9,10,11,12）／等价 2（7,8，均回到 r170 基线）／更远 0。**
电池现读数：**17 TEXT-DIFF / 458**（基线 9 = v111×3 + E161×6；新增 8 = 上表
1,2,3,4,9,10,11,12，全部形态更接近源码），**458/458 BYTE-EQUAL**，`C7_skipedge` TEXT-SAME。

### 本轮加入的两个宿主门（Task C）

1. **break × elif 候选门**：`_v171_iter_exit_merge` 的 break 分支，else_succ 是纯条件块
   （前向条件跳转 + 2 条件后继）时不重算 merge，交既有 `_build_elif_region`。
   依据：pc1/pc2 源为 `elif`、pc4 源为 `if`，**三者字节码同形不可判**；旧行为对
   pc1/pc2 对、对 pc4 错，中间态反之 ⇒ 统一让位给基线 elif 构造器（C3 零行为差）。
2. **裸 break 臂门**：break 分支要求 then 臂无语句性指令（STORE_*/CALL/DELETE_* 等）。
   依据：tarfile `TarFile.next` 的 `if tarinfo is not None: append / else: _loaded=True`
   在带语句的 break 臂上重算 merge 后，`else` 极性守卫被折叠成无条件
   `self._loaded = True`（丢掉 `is None` 条件）= **形态更远**；纯 `if c: break`
   （tarfile `_Stream._read` 的 `if not buf: break`）不受影响，**+1 收益保留**。

## B. 三语料文本变化（因本补丁而变的函数，终版 sha）

| 语料 | 变的函数 | 改动 | 判定 |
|---|---|---|---|
| request `9e3e7baf…`→`db2172e8…`（87779→87699 B，194/194 不变） | `parse_http_list` | `if quote:` 分支 2 条重复 continue → 1（=源）；末尾 `part += cur` 后 3 条 → 1（源 0，余 1） | **更接近**（部分闭合） |
| 同上 | `ip2num`（内层 `elif fnmatch(...)`） | 删除 `return True` 后 2 条重复 continue，`elif` 保留 | **更接近** |
| tarfile `4dba499d…`→`fcb8a7fb…`（90003→89892 B，**155→156/160**） | **`_Stream._read`** | try/except + `t.append` + `c += len(buf)` 由「缩进在 `else:` 分支内」**退回 `while c < size:` 体层**（源层 530-555 同构）⇒ Failure → **EQUAL** | **更接近 + 真收益** |
| 同上 | `_apply_pax_info` | 3 条重复 continue 删除 | **更接近** |
| 同上 | `extractall` | `elif tarinfo.isdir():` → `if tarinfo.isdir():` | **更接近**（源 tarfile.py:2259 为 `if`） |
| 同上 | ~~`next`~~ | 裸 break 臂门后**已恢复基线文本**（不再变化） | —（本轮已消除） |
| subprocess `53d99059…`→`1ee06b68…`（69807→69763 B，69/78 不变） | `list2cmdline` | 2 条重复 continue 删除 | **更接近** |
| difflib `d70df600…` | — | 逐字节 SAME | — |

**tarfile 的 +1 是真收益**：失败 5→4，退出的单元 = **`_Stream._read`**
（Different control flow → **EQUAL**），余 `_FileInFile.read` / `TarFile.add` /
`TarFile.next` / `main`。它不是换写法刷读数：try/except 从伪 `else:` 分支退回循环体层，
与源码 `tarfile.py:530-555` 逐行同构。

**B 段结论**：三语料共 6 处文本变化（request 2 / tarfile 3 / subprocess 1），**6/6 更接近源码**。
其中 request `parse_http_list` 末尾仍余 1 条伪 continue（未闭合残余，非新错）。
四语料判官 194/194、156/160、69/78、62/62 **全部不减**；difflib 逐字节 SAME。

## C. 收窄后六项读数（终版）

| 项 | 读数 |
|---|---|
| cookiejar | **94/105**，69418 B `f2c8b33a…`（失败 11 = 原 14 − `<module>`/save/as_lwp_str） |
| tarfile | **156/160**，89892 B `fcb8a7fb…` |
| request | 194/194，87699 B `db2172e8…`（文本更接近，非 SAME） |
| difflib | 62/62，67855 B `d70df600…`（**SAME**） |
| subprocess | 69/78，69763 B `1ee06b68…`（文本更接近，非 SAME） |
| 458 电池 | **17 TEXT-DIFF / 458，全 BYTE-EQUAL**；新增 8 条全部更接近；`C7_skipedge` TEXT-SAME |
| 38 案红线 | 37 SAME + `r164 request_final`（= request 产物快照，判官 194/194，非手写红线） |
| 卫生 | 统计: 14 个错误, 6 个警告 |
| numstat | code_generator 66/0、region_analyzer 113/0、region_ast_generator 63/1 |

**未能满足「request/subprocess 产物回到逐字节 SAME」的原因（实测）**：G1 单独不改任何
语料（三语料 sha = r170 基线 `9e3e7baf`/`4dba499d`/`53d99059`）；R 单独改
（`cf132c0c`/`b8f562f2`/`1ee06b68`）、G2 单独改（`446acd73`/`d26e5e63`/`0ce53f2b`）；
而 cookiejar 94 需 R+G1+G2 协同（R 单独 92、G2 单独 92、G1G2 91）。所以「回到 SAME」
只能连同上述 6 处**更接近**的修正一起回退（= 只留 DOCESC：cookiejar 92/105、
tarfile 155/160、电池 9），需裁决。
