
---

## 5. 解剖结论（diag1 判读）

### 5.1 三个臂到底各改了哪些 hunk

| 臂 | spec | tick_direction 指标 | 相对 landed 的改动 |
|---|---|---|---|
| absj | `abs1`+`abs2_orphan_child_emit` | hunks 12 / norm 2 / first 4 / sd 184 | 该单元**零变化** |
| absj3 | absj + `try7_3`（5 edits：`78eea71b` T1/T2、`343e05ae` T4、`66486c1d`、`0b10b201`、`861c978c` T6） | hunks 12 / norm 2 / first 4 / sd 184 | 该单元**零变化**（指标与 landed 逐位相同） |
| absj9 | absj + `try7_9`（7 edits = try7_3 的 5 处 + **`31b0d3fa` `_try_has_return` 守卫** + **`2b9410cc` T7**） | hunks 5 / norm **3** / first 4 / sd **4** | 结构被改写，见 5.2 |
| absjt / try7_10d | absj + `try7_10d`（同 7 处，`31b0d3fa` 换成 2931 B 长版、带 BDBG 调试输出） | hunks 5 / norm 3 / first 4 / sd 4 | 与 absj9 在本单元**读数完全相同** |

- 即：`try7_3` 完全不含这两处新增编辑，所以 **absj3 过 ADR-1 是因为它根本没碰这个单元的形状**，不是因为它在该单元上做得更好。
- 真正改变本单元的是 `try7_9`/`try7_10d` 新增的 2 处编辑；两者在本单元产生逐位相同的读数，因此**第 2 处编辑（T7，`2b9410cc`）足以复现该回退**；第 1 处（`_try_has_return` 守卫）是否单独致回退未隔离（diag1 只读，不做建臂实验，留 fix1 隔离：`absj+edit5` 与 `absj+edit6` 各建一臂跑 ADR）。

### 5.2 结构被改成了什么（`build_landed` vs `build_absj9` 源码差，78 行 vs 78 行）

```diff
-                try:                                   |            else:
-                    if redata:                          |                if flag == 1:
-                        if tick_direction_in_dict=='1': |                    system_log.debug(...)
-                            return redata               |                elif flag == -1:
-                        ...                             |                    system_log.debug(...)
-                        return pd_dict                  |                return redata
-                    else:                               |            try:
-                        system_log.debug(...)           |                if redata:
-                except Exception as e:                  |                    ...
-                    system_log.debug(get_traceback_message())
-                return pd_dict                      |            except Exception as e:
-            elif flag == 1: ...                    |                system_log.debug(...)
-            elif flag == -1: ...                   |
-            return redata                          |
```

- landed：`if redata:` 链把 `flag==1 / flag==-1 / return redata` 当成**同级 `elif`** 挂在 try 外侧（结构错，`return pd_dict` 停在 if 链内）。
- absj9（T7）：改成 `if A: P else: <flag 链>; return redata`，try 从 if 链里切出、在链后重发——**这正是 T7 注释描述的原始结构**，因此 `sdelta 184→4`、`hunks 12→5`（三条跳转差只剩 1 条 `to 512→to 516 (+4)`）。
- 代价：切出/重发后，**尾部共享 `return pd_dict` 没有被重新发射**，产品函数尾变成 `return redata` + 隐式 `return None`。

### 5.3 第 3 个（以及前两个）归一化 hunk 的字节内容

matched 空间（`idx / offset / opname`），orig vs `absj9`：

| # | 归一化 hunk | orig | absj9 产品 | 字节 |
|---|---|---|---|---|
| 1 | replace | `231 JUMP_FORWARD to 512` | `231 LOAD_CONST None` + `232 RETURN_VALUE` | 跳转被物化成 `return None` |
| 2 | replace | `247 JUMP_FORWARD to 512`（except 清理后 `DELETE_FAST e` → 跳共享尾） | `248 LOAD_CONST None` + `249 RETURN_VALUE` | 同上，字节 `6400 5300`（`LOAD_CONST None; RETURN_VALUE` @496/498） |
| 3 | replace | `256 LOAD_FAST pd_dict` @512 → `257 RETURN_VALUE` @514 | `258 LOAD_CONST None` @516 → `259 RETURN_VALUE` @518 | 尾部返回值 `pd_dict`→`None`，字节 `7c08 5300`（orig）vs `6400 5300`（产品） |

三条 hunk 全部是同一件事的三个投影：**产品少了「共享尾 `return pd_dict`」**，于是
两个前跳出口物化成 `return None`、最后一跳的返回值变 `None`。

### 5.4 为什么 absj 过、`+try7_9`/`+try7_10d` 不过

1. landed/absj/absj3 的 2 个归一化 hunk 是「整块搬移」形状（`delete orig[148:174]` + `insert prod[232:259]`）——SequenceMatcher 把错位的 flag 块当作一个 replace/delete 对，**尾部 `return pd_dict` 的差异被包进这个 insert 段里，不再单独计数**。
2. T7 把结构摆正后，大块搬移消失（hunks 12→5、sd 184→4），剩下 3 处**真实的出口差异**被逐个计为独立 hunk ⇒ `hunks_norm 2→3`。
3. ADR-1 是「任一指标变差即整件拒收」：`hunks ✓ 12→5`、`sdelta ✓ 184→4`、`first_diff = 4→4` 都不触发，只有 `hunks_norm 2→3` 触发 ⇒ 拒收。

**判读**：该回退是 **ADR-1 的计分形状效应（把『搬移』记成 1 个 hunk、把『修好的结构 + 3 处真实出口差』记成 3 个 hunk）叠加一个真实缺陷（共享尾 `return pd_dict` 未重新发射）**。
fix1 的正确姿势不是放弃 T7，而是**给 T7 补上尾部共享块的重发射**（或按 `handlers._target` 已验证的行表判据：不物化编译器生成的 `return None`、让各出口 `JUMP_FORWARD` 到共享尾），使 `hunks_norm ≤ 2` 后重跑 ADR-1。
