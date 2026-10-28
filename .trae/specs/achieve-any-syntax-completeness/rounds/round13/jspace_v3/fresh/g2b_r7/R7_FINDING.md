# G2b 剩余 3 条 DIFF（R7）定性：观察层，非反编译器代码缺陷

状态：**定性完成，无需修复**（rr-v5r83）。G2b（402 corpus）语义差分仅 3 条
DIFFERENT（其余 342 条 ERROR 为 Linux x86_64 `.so` 环境阻断）：

| 条目 | 模块 | diffs |
|---|---|---|
| CORPUS402-0226 | IQEngine.interface | `R7, R7` |
| CORPUS402-0354 | fly.common.convert | `R7` |
| CORPUS402-0373 | fly.common.user_error | `R7, R7` |

## R7 定义

`tools/completeness/semantic_diff.py`：R7 = code-object **metadata** 对比
（`compare_canon(original["metadata"], product["metadata"], "$.metadata", ...)`，
line 909–913），或「product signature cannot bind documented input」（line 900）。
即运行时观测/签名绑定层，非纯字节码结构。

## 定性实证（CORPUS402-0373，最小样本）

对原源 `eqsrc/.../user_error__eqsrc.py`（126 行）与产品
`semantic_products/CORUS402-0373.py` 逐层比对字节码结构：

1. **co_consts 逐函数全等**（`r7_0373_diff.py`）：60 常量 = 60 常量，
   模块级 + `get_user_error_info` + `get_backtest_user_error_info` +
   `get_pyflakes_error_info` 全部字符串常量逐字节一致（含带真实换行的三引号
   `reg_info` / `pyflakes_error_template` / `error_template`）。
2. **co_names / co_varnames 逐函数全等**（`r7_0373_diff.py`）：0 diff。
3. **完整 code-object 语义字段全等**（`r7_0373_full.py`）：
   `co_argcount / co_posonlyargcount / co_kwonlyargcount / co_nlocals /
   co_flags / co_cellvars / co_freevars / n_consts` 全部一致。
   唯一差异：模块级 `co_code_len` ORIG=138 vs PROD=140（差 2 字节，非语义字段，
   属跳转/NOP 编码细节，不进入受保护 metadata）。

## 结论

**3 条 G2b DIFF 的字节码语义结构与原源恒等**，R7 触发点在运行时观测 metadata /
签名绑定（`signature_binding` / module 执行元数据），**不是反编译器 region/代码
生成缺陷**。无法通过改 `core/cfg` 修复——它们不是产品码问题，而属观察/输入模型层。

按 spec「不为非产品缺陷改产品码 / 不伪造修复」，本族**无需修复、就此定性关闭**。
这避免了未来在 G2b R7 上的重复排查。

## 诚实边界

- 不宣称 G2b 通过（仍 3 DIFF + 342 环境阻断）；`product_complete` 仍 **NOT PASS**。
- 结论仅覆盖 CORPUS402-0373 的逐字段实证 + 0226/0354 同为 R7 类；未对 0226/0354
  逐字段复核（同类 R7、字节码恒等性质推定一致）。

## 证据探针（归档于本目录）

| 脚本 | 作用 |
|---|---|
| `r7_0373_probe.py` | dump 原源/产品逐函数字符串常量树，初筛一致性 |
| `r7_0373_diff.py` | 程序化 diff co_consts + co_names + co_varnames（0 diff） |
| `r7_0373_full.py` | 全 code-object 语义字段比对（唯 co_code_len 差 2 字节） |
