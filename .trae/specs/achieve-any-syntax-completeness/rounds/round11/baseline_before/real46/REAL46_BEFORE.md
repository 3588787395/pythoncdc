# 46 真实 pyc before 读数（Task 0.5）

命令（对每个样本）：

```
python -X utf8 scripts\pyc_verify.py single .trae\specs\attack-completeness-claims\rounds\round6\offcorpus\<slug>.pyc
```

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

## 汇总

| 项 | 数值 |
|---|---:|
| 样本总数（origin=real） | 46 |
| status=success（全单元 EQUAL） | 4 |
| status=compile_error（产物不可编译） | 7 |
| status=failure（部分单元差异） | 35 |
| 单元合计 | 2765/3079（89.80%） |

对照历史 L4 攻击读数（round6）：判据绿 **4/46**、不可编译 **7/46**、单元 **2765/3079** —— 本次复跑逐项一致。

## 明细

| slug | status | units | success_rate |
|---|---|---|---|
| stdlib_dataclasses | failure | 83/87 | 95.40% |
| stdlib_contextlib | failure | 80/86 | 93.02% |
| stdlib_functools | failure | 79/92 | 85.87% |
| stdlib_enum | compile_error | 0/0 | - |
| stdlib_asyncio_taskgroups | failure | 9/10 | 90.00% |
| stdlib_asyncio_timeouts | failure | 12/13 | 92.31% |
| stdlib_json_encoder | failure | 12/15 | 80.00% |
| stdlib_xml_ElementPath | failure | 35/39 | 89.74% |
| stdlib_tomllib_parser | failure | 31/43 | 72.09% |
| stdlib_re__parser | failure | 35/43 | 81.40% |
| stdlib_statistics | failure | 71/77 | 92.21% |
| stdlib_difflib | failure | 45/62 | 72.58% |
| stdlib_http_cookiejar | failure | 90/105 | 85.71% |
| stdlib_tarfile | failure | 141/160 | 88.12% |
| stdlib_subprocess | failure | 68/78 | 87.18% |
| stdlib_urllib_request | failure | 184/194 | 94.85% |
| stdlib_unittest_case | failure | 123/131 | 93.89% |
| stdlib_argparse | failure | 185/192 | 96.35% |
| stdlib_ipaddress | failure | 163/166 | 98.19% |
| stdlib_asyncio_base_events | failure | 99/119 | 83.19% |
| stdlib_asyncio_streams | failure | 53/60 | 88.33% |
| stdlib_typing | failure | 285/309 | 92.23% |
| stdlib_ast | failure | 170/185 | 91.89% |
| stdlib_csv | failure | 29/32 | 90.62% |
| stdlib_asyncio_tasks | failure | 43/53 | 81.13% |
| sp_anyio_fileio | failure | 116/124 | 93.55% |
| sp_anyio_sync | failure | 94/110 | 85.45% |
| sp_anyio_lowlevel | failure | 15/20 | 75.00% |
| sp_anyio_functools | failure | 26/34 | 76.47% |
| sp_packaging_specifiers | compile_error | 0/0 | - |
| sp_packaging_version | compile_error | 0/0 | - |
| sp_httpcore_models | failure | 33/41 | 80.49% |
| sp_starlette_formparsers | failure | 20/25 | 80.00% |
| sp_pydantic_dataclasses | compile_error | 0/0 | - |
| sp_pydantic_fields | compile_error | 0/0 | - |
| sp_pandas_indexing | failure | 97/119 | 81.51% |
| sp_sqlalchemy_collections | compile_error | 0/0 | - |
| sp_sympy_qexpr | success | 36/36 | 100.00% |
| repo_core_config | success | 15/15 | 100.00% |
| repo_core_fast_stack | failure | 53/57 | 92.98% |
| repo_core_object_pool | success | 30/30 | 100.00% |
| repo_core_cfg_basic_block | failure | 40/41 | 97.56% |
| repo_core_cfg_builder | failure | 33/43 | 76.74% |
| repo_parsers_ctx | success | 19/19 | 100.00% |
| repo_scripts_verify | compile_error | 0/0 | - |
| repo_tools_syntax_cov | failure | 13/14 | 92.86% |
