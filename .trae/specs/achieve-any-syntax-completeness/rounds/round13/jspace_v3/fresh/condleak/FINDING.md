# rr-v5r155 [v155-CONDLEAK] 值上下文 BoolOp merge 块条件串扰族（REAL46-014 tarfile 144→145/160）

## 功效案（tarfile.copyfileobj 实形）

```python
def copyfileobj(src, dst, length=None, exception=OSError, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    if length is None:
        shutil.copyfileobj(src, dst, bufsize)
        return
    ...
```

v154 渲染 `if bufsize or 16384: return None`——`if length == 0:` 的条件被前一条
赋值语句的 or-BoolOp 串扰（真实 R1：函数每次调用提前返回、永不拷贝）。

## 根因

`bufsize = bufsize or 16*1024` 与 `if length == 0:` 的 STORE + COMPARE 测试被
CPython 划进**同一基本块**（B8：[STORE bufsize, LOAD length, COMPARE ==,
POP_JUMP_FORWARD_IF_FALSE 26]）。B8 既是值上下文 BoolOpRegion（blocks=[0,6,8]、
value_target='bufsize'）的 merge 块，又是 IfRegion 的 entry/condition_block——
双角色块。分析器例外链：`_is_merge_if_condition`（值上下文 + COMPARE_OP + 前向
跳转）为真 → 压过例外3（`_value_merge_hosts_next_if` 语言级精确判据——探针实证
对 B8 返回 True）→ `guard_clause_prefix_end` 标记不写下 → 生成器把 BoolOp 表达式
当作 if 测试。elif 链路径另有独立缺口：`_elif_boolop_merge_owner` 查找跳过
'generating'/'generated' 台账中的 owner（EBM_DEBUG 探针实证 skip=['generating']）
——无 A2b/H2 变体（_if_generate_normal 有、链构建器没有）→ 条件扫描从块首 STORE
起算、条件段被错读成赋值段。

## 修复（只增不破，双文件两处）

1. **region_analyzer（fix155）**：`_merge_boolop_guard_prefix_end` 门析取加上
   `_is_merge_if_condition ∧ _value_merge_hosts_next_if(block, _owning_boolop)`——
   例外3 的语言级精确判据同时成立时同样写下标记（R36 双角色路径发射
   "<BoolOp 赋值语句> + If(块尾测试, ...)"）。例外2/3 既有路径逐位不变。
2. **region_ast_generator（fix155b）**：elif 链构建器的 `_elif_boolop_merge_owner`
   补 A2b/H2 变体扫（owner 在 generating/generated 台账中时不进主查找，补扫命中
   后以 `_elif_bo_skip_generate` 跳过再次 `_generate_boolop`（赋值发射权归 owner
   帧，原则 2），仍以 value_target 作 boolop_merge_target 提取块尾条件。

## 验收

- cfo2/condleak 复现案判官全 Equal/Equal；最小形重复赋值缺陷同轮消失
- tarfile **144→145/160（90.62%）**——copyfileobj 闭合
- 矩阵 11 案 ALL PASS（E1 cfo2/E2 minimal HEAD TEXT-DIFF→v155 JUDGE-EQUAL；
  E3 例外2 guard-clause 多 STORE 形/E4 例外3 PRECALL 形/E5 条件上下文 if 全
  SAME+JUDGE-EQUAL=既有域零触碰；C1 kwmerge/C2 dual_unpack/C3 mdiff3/C4 latch_if/
  C5 na5 全 SAME；C6 B116 SAME 预存在 DIFF 维持）
- 电池 368 案（R110 169 + V111..V155 累计 + V155 11）——五文件交换
- pytest 2F/277P/2XP 冻结基线
- REAL46 全量 sweep 小修口径豁免

## 文件

- matrix_v5r155.py / matrix_v5r155_result.txt（r155matrix）
- r155_regress.py / r155_regress_result.txt
- tarfile_judge_v154b.txt（144/160 基线）/ tarfile_judge_v155.txt（145/160 终态）
- cfo2_src.py / cfo2.pyc / cfo2_out3.py、condleak_src.py / condleak_out2.py（复现）
- fix155.py（analyzer）/ fix155b.py（generator）/ derive155.py
- fix_patch_v5r155.diff
