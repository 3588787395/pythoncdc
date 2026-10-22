# L4 失败样本根因分类（§2）

| slug | 根因类 | 失败单元数 |
|---|---|---|
| `repo_core_cfg_basic_block` | C6 | 1 |
| `repo_core_cfg_builder` | C2、C3、C6、C9 | 6 |
| `repo_core_fast_stack` | C2、C6 | 4 |
| `repo_tools_syntax_cov` | C1 | 1 |
| `sp_anyio_fileio` | C1、C2、C6 | 6 |
| `sp_anyio_functools` | C2、C5、C6 | 6 |
| `sp_anyio_lowlevel` | C2、C6 | 5 |
| `sp_anyio_sync` | C2、C6 | 6 |
| `sp_httpcore_models` | C2、C6 | 6 |
| `sp_pandas_indexing` | C14、C2、C6 | 6 |
| `sp_starlette_formparsers` | C2、C6 | 5 |
| `stdlib_argparse` | C10、C14、C2、C4 | 6 |
| `stdlib_ast` | C11、C14、C2 | 6 |
| `stdlib_asyncio_base_events` | C1、C10、C14、C2 | 6 |
| `stdlib_asyncio_streams` | C1、C2、C5 | 6 |
| `stdlib_asyncio_taskgroups` | C2 | 1 |
| `stdlib_asyncio_tasks` | C1、C10、C11、C14、C2、C4 | 6 |
| `stdlib_asyncio_timeouts` | C6 | 1 |
| `stdlib_contextlib` | C10、C14、C2、C5 | 6 |
| `stdlib_csv` | C2 | 3 |
| `stdlib_dataclasses` | C14、C2 | 4 |
| `stdlib_difflib` | C1、C2 | 6 |
| `stdlib_functools` | C10、C2 | 6 |
| `stdlib_http_cookiejar` | C2 | 6 |
| `stdlib_ipaddress` | C14、C2 | 3 |
| `stdlib_json_encoder` | C14、C2 | 3 |
| `stdlib_re__parser` | C2 | 6 |
| `stdlib_statistics` | C11、C14、C2 | 6 |
| `stdlib_subprocess` | C10、C2 | 6 |
| `stdlib_tarfile` | C10、C11、C2 | 6 |
| `stdlib_tomllib_parser` | C1、C2、C6、C9 | 6 |
| `stdlib_typing` | C2 | 6 |
| `stdlib_unittest_case` | C2、C4 | 6 |
| `stdlib_urllib_request` | C2、C9 | 6 |
| `stdlib_xml_ElementPath` | C2 | 4 |

## 分布（按样本）

- C2: 32
- C6: 12
- C14: 10
- C1: 7
- C10: 7
- C11: 4
- C9: 3
- C5: 3
- C4: 3
- C3: 1

## 分布（按失败单元）

- C2: 100
- C6: 31
- C14: 13
- C1: 10
- C10: 9
- C4: 4
- C11: 4
- C9: 3
- C5: 3
- C3: 1
