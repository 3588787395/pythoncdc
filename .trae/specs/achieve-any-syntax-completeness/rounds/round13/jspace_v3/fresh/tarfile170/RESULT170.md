# RESULT170 — tarfile 154→**155**/160：`_Stream._init_read_gz` 两面同轮

> 仓库 `F:\Downloads\pythoncdc-main`；只改 `core/cfg/region_ast_generator.py`（git diff --numstat = **104/0**）。
> 解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库。判官 `scripts/pyc_verify.py single <pyc> --source <产物>`。
> 补丁 `D:\temp\opencode\cl_layout\r170\fix170.py`（2 anchor / count==1 / utf-8-sig / py_compile / 幂等；
> 从 pristine `169e802b` 重打 = 逐字节同 sha `9F5935F1015F1BC5`）。产物：`work/tarfile_final.py` 90003 B sha16 `4DBA499DA3A0FC30`。

## 0. 读数

| 项 | r169 | r170 |
|---|---|---|
| tarfile | 154/160 | **155/160 (96.88%)** |
| `_Stream._init_read_gz` | Failure: Different control flow | **EQUAL** |
| 失败 5 | 6 项 | `_Stream._read` / `_FileInFile.read` / `add` / `next` / `main` |
| request / difflib | 194/194 · 62/62 | 194/194 · 62/62（`9e3e7baf` / `d70df600` 逐字节 SAME） |
| cookiejar / subprocess | 91/105 · 69/78 | 91/105 · 69/78（`7c122a0d` / `53d99059` 逐字节 SAME） |
| 红线 38 案 | 38/38 SAME | **38/38 SAME**（含 f2 `e5ea8f23`、fc2 `01e88925`） |
| 458 电池 | 9 TEXT-DIFF | **9 TEXT-DIFF / 458，全部 BYTE-EQUAL**；结果文件与 r169 accepted **逐字节相同**（sha `A78F7417…`）；`C7_skipedge` TEXT-SAME |
| 卫生 | 14 错 6 警 | **14 个错误, 6 个警告** |

## 1. 两面根因与修复谓词

### F2 去嵌套面（`generate()` 包含判定，:1862–1880）

- 分析层：`LoopRegion@578.parent = IfRegion@566`，`IfRegion@566.merge_block = 650`，且 `650 ∈ LoopRegion@578.break_blocks`；
  以 650 为 entry 的 `IfRegion@650`（=`if flag & 16:` 守卫）在包含判定里被「entry ∈ LoopRegion.blocks」
  判成嵌套子区域 → 滤出 `top_level_regions`。r169 已让循环侧不收集/不登记该落点（交外层序列发射），
  但外层序列拿不到该区域 ⇒ 守卫与体内 while 整段蒸发（只剩 `s=read(1)` 裸语句）。
- 修复谓词（纯结构事实，复用 r169 同一判据）：
  `other` 是 LoopRegion ∧ `r` 是 IfRegion ∧ `r.entry ∈ other.break_blocks`
  ∧ `_v169_post_loop_parent_if(other, r.entry) is not None`
  ⇒ 不判 contained，保留为顶级区域，由 generate() 顶级序列按 entry 偏移在 If 之后发射。
- 逐层验证：`IfRegion@650`（`if flag & 16`）→ 其 then 内 `LoopRegion@662` → `IfRegion@734`（`if flag & 2`）三级同判据生效。

### F1 形态面（`_loop_build_if_with_exit_branches`，:18032–18100）

- 旧路径：then=落空块 / else=跳转块；落空块（f3 @44）自身以 `POP_JUMP_FORWARD_IF_FALSE` 收尾，
  被 `_generate_block_statements` 发射成内层 if ⇒ `if s: if s == NUL: break / else: break`
  （内层 if 空 else 物化额外 JUMP_FORWARD；tarfile 第二循环 break 丢成 pass）。
- 修复谓词（只读调用点形参 + 本块指令/后继/角色）：
  ① 落空块不是出口、跳转块是 break（∈ `_block_succ_break`，角色 BREAK/PURE_BREAK）；
  ② 落空块末条实指令是条件跳转，两后继一个 = 该 break 块、另一个是循环回边（非出口）；
  ③ 跳转前是纯表达式段（无 STORE_*/POP_TOP 边界）⇒ 可重建第二操作数。
  ⇒ 合成 `BoolOp(or, [第一操作数, 第二操作数])` 的单一 `if ...: Break`。
- **宿主门**（红线 f2）：仅当 `_current_loop.parent` 是 IfRegion 且其 `merge_block` 正是本循环 break 落点
  （同一结构事实）时生效；f2 的裸 while 无 IfRegion 宿主 ⇒ 逐字节不变（实测 283 B / `e5ea8f23` SAME）。
- 复验 r167 的“缺一不可”：只做去嵌套（t1）已 EQUAL（判官 `fix_indirect_jump` 把 jump-to-jump 归一，
  多余 JUMP_FORWARD 不算差异），但源码形态仍错；两面都做后形态与真实源码一致且仍 EQUAL。
  形态面单独不做去嵌套仍 FAIL（守卫蒸发），故“只做形态”的结论成立。

## 2. 复现与证据

- `work/probe170.py`（发射端追踪）、`work/probe170b.py`（generated_blocks 标记来源）、
  `work/regions170.py`（区域 detail）。
- f3：`LoopRegion@18 parent=IfRegion@0 merge=60 break=[60]`；`IfRegion@60 parent=None blocks=[60,70,96]`。
- f3/f1 产物：`if not s or s == NUL: break` + `if flag & 16:` / `if flag & 2:` 回到 If 之后兄弟位；
  `work/repro3/*` 为判官输入，f2 与 r167 参考逐字节 SAME。
- `work/tarfile_t1.py`（只去嵌套）155/160；`work/tarfile_final.py`（两面）155/160。

## 3. 兼容性 / 零触碰

- 除 core/cfg/region_ast_generator.py 外无本轮 tracked 改动；`.trae/.../tasks.md` 的 +38 行是并行
  Task 98/99（cookiejar/subprocess）计划文本，非本轮所写。
- 未 commit/push/stash；未改 `.trae/`、`scripts/`、`tests/`；仓库无 `V170DBG`/探针残留；
  `.trae/.../fresh/tarfile169/r161_regress_result.txt` 未被覆盖（电池 EV 指向 `r170battery/ev`）。
- 电池 `D:\temp\opencode\cl_layout\r170\battery170.py`（复制 r169_regress.py，仅改 TMP/OUTDIR/EV）。
