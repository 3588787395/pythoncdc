# rr-v5r154 [v154-KWMERGE] kwargs 保序溅射族（REAL46-014 tarfile 142→144/160）

## 功效案（来自 tarfile sweep 的 18 差单元中 tar_filter/data_filter 的字节差）

```python
def tar_filter(member, dest_path):
    new_attrs = _get_filtered_attrs(member, dest_path, False)
    if new_attrs:
        return member.replace(**new_attrs, deep=False)
    return member
```

v153 渲染 `member.replace(**({'deep': False}))`——`**new_attrs` 整体丢失（真实 R1：
过滤属性未传入 replace）。

## 根因

`f(**a, k=v)` 编译为 `BUILD_MAP 0; LOAD a; DICT_MERGE 1; {k:v}; BUILD_MAP 1;
DICT_MERGE 1; CALL_FUNCTION_EX 1`——kwargs 字典是**多段合并链**。重建器
（ast_generator_v2）产出**保序** kwargs 列表 `[KeywordStarred(a), keyword(k=v)]`
（探针实证节点正确），但 `ast_converter._convert_call` 的 kwargs 循环把溅射存进
**单个局部变量 `kw_arg`**（后写覆盖前写）且 ASTCall 模型只支持单个 `kw` 溅射 →
除最后一个溅射外全部丢失；且具名关键字排在溅射前渲染时源级顺序反转
（HEAD 渲染 `f(deep=False, **(new_attrs))`——若 a 含 'deep' 语义不同且字节不同）。

## 修复（只增不破，三文件 +57/−9≈）

1. **ast_nodes.ASTCall**：新增 `_kw_ordered` 保序通道（元素=ASTKeyword 具名关键字
   或其他 ASTNode **splat 值）；旧 kwparams/var/kw 路径逐位保留。
2. **ast_converter._convert_call**：存在多个溅射或溅射先于具名关键字时，按重建器
   kwargs 列表的源级顺序构建 `kw_ordered`；单溅射形维持旧路径。
3. **code_generator ASTCall 渲染**：`kw_ordered` 非空时按序发射（ASTKeyword=具名、
   其他=**splat，yield 实参括号规则镜像），空时逐位落回旧路径。
4. **ast_generator_v2._flatten_dict_merge_to_kwargs**：DictMerge.d2 为字面量 Dict 时
   展开为具名关键字项（`f(**a, deep=False)` 文本还原关键字形——重编译同一
   BUILD_MAP+DICT_MERGE 字节逐位不变）；非字面量维持 **splat 项。

三变体渲染与源级逐字一致：
- `member.replace(**new_attrs, deep=False)` ✓
- `d.call(**kw, x=1, y=2)` ✓
- `d.call(**a, **b)` ✓

## 验收

- kwmerge 判官 4 单元全 Equal；tarfile **142→144/160（90.00%）**——tar_filter/
  data_filter 闭合（tarfile_judge_v153.txt=142/160 基线、v154b=144/160 终态）
- cookiejar 91/105、subprocess 68/78、urllib.request 185/194 维持登记基线（本族
  不触达，零回归）
- 矩阵 16 案 ALL PASS（E1-E5 功效案 HEAD TEXT-DIFF→v154 JUDGE-EQUAL；C1 单溅射/
  C2 纯具名/C3 星号/C4 星+溅射/C5 全 legacy/C6 字典显示 **update/C7-C10 前轮家族
  全 SAME+JUDGE-EQUAL；C11 B116 SAME 预存在 DIFF 维持）。矩阵 A/B 交换集
  修正为本轮三文件（ast_nodes/ast_converter/code_generator）
- 电池 357 案（R110 169 + V111..V154 累计 + V154 16）——五文件交换
  （analyzer/generator/ast_nodes/ast_converter/code_generator）
- pytest 2F/277P/2XP 冻结基线
- REAL46 全量 sweep 小修口径豁免

## 文件

- matrix_v5r154.py / matrix_v5r154_result.txt（r154matrix）
- r154_regress.py / r154_regress_result.txt
- tarfile_judge_v153.txt（基线 142/160）/ tarfile_judge_v154.txt（+2 后 144/160）
  / tarfile_judge_v154b.txt（文本润色后维持 144/160）
- cj_judge_v154.txt / sp_judge_v154.txt / ur_judge_v154.txt（三包基线维持）
- kwmerge_src.py / kwmerge.pyc / kwmerge_out.py（三变体复现）
- fix154.py（三文件补丁）/ derive154.py
- fix_patch_v5r154.diff
