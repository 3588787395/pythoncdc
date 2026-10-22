# L4 语料外逐样本结果（§2 表数据源）

| slug | 来源（真实源码路径） | 特征 | 判据 | 单元(成功/总) | 失败单元 | 根因类 | 具体差异（指令级，摘） |
|---|---|---|---|---|---|---|---|
| `repo_core_cfg_basic_block` | `F:\Downloads\pythoncdc-main\core\cfg\basic_block.py` | 装饰器、注解、f-string、dataclass | failure | 40/41 | 1 | C6 | - LOAD_CONST ('block', 'BasicBlock', 'return', None) ／ --- replace (orig[78:79] -> prod[77:78]) ／ - MAKE_FUNCTION 4 |
| `repo_core_cfg_builder` | `F:\Downloads\pythoncdc-main\core\cfg\cfg_builder.py` | 注解、装饰器、f-string | failure | 33/43 | 10 | C2、C3、C6、C9 | + POP_TOP None ／ + LOAD_CONST None |
| `repo_core_config` | `F:\Downloads\pythoncdc-main\core\config.py` | 注解、装饰器 | success | 15/15 | 0 |  |  |
| `repo_core_fast_stack` | `F:\Downloads\pythoncdc-main\core\fast_stack.py` | 注解、f-string | failure | 53/57 | 4 | C2、C6 | - LOAD_CONST ('return', None) ／ --- replace (orig[65:66] -> prod[64:65]) ／ - MAKE_FUNCTION 4 |
| `repo_core_object_pool` | `F:\Downloads\pythoncdc-main\core\object_pool.py` | 注解 | success | 30/30 | 0 |  |  |
| `repo_parsers_ctx` | `F:\Downloads\pythoncdc-main\parsers\context_manager.py` | 注解、f-string | success | 19/19 | 0 |  |  |
| `repo_scripts_verify` | `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py` | 注解、PEP604 | compile_error | 0/0 | 0 |  |  |
| `repo_tools_syntax_cov` | `F:\Downloads\pythoncdc-main\tools\kb\syntax_coverage.py` | except*、PEP604 | failure | 13/14 | 1 | C1 | - BUILD_LIST 0 ／ --- delete (orig[297:298] -> prod[296:296]) ／ - STORE_FAST extra_covered |
| `sp_anyio_fileio` | `D:\Python\Lib\site-packages\anyio\_core\_fileio.py` | 注解、装饰器、async、f-string、dataclass、生成器、PEP604 | failure | 116/124 | 8 | C1、C2、C6 | - NOP None ／ - NOP None ／ - NOP None |
| `sp_anyio_functools` | `D:\Python\Lib\site-packages\anyio\functools.py` | 注解、装饰器、async、海象、PEP604 | failure | 26/34 | 8 | C2、C5、C6 | - LOAD_CONST 'RunVar[WeakKeyDictionary[AsyncLRUCacheWrapper[Any, Any], OrderedDi ／ + LOAD_CONST "'RunVar[WeakKeyDictionary[AsyncLRUCacheWrapper[Any, Any], OrderedD ／ --- replace (orig[157:158] -> prod[157:158]) |
| `sp_anyio_lowlevel` | `D:\Python\Lib\site-packages\anyio\lowlevel.py` | 注解、async、装饰器链、装饰器、f-string、dataclass、PEP604 | failure | 15/20 | 5 | C2、C6 | - LOAD_CONST ('return', 'None') ／ --- replace (orig[74:75] -> prod[73:74]) ／ - MAKE_FUNCTION 4 |
| `sp_anyio_sync` | `D:\Python\Lib\site-packages\anyio\_core\_synchronization.py` | 装饰器、注解、async、海象、dataclass、PEP604 | failure | 94/110 | 16 | C2、C6 | - LOAD_CONST 'int' ／ + LOAD_CONST "'int'" |
| `sp_httpcore_models` | `D:\Python\Lib\site-packages\httpcore\_models.py` | 注解、async、装饰器、f-string、生成器、PEP604 | failure | 33/41 | 8 | C2、C6 | - LOAD_CONST ('value', 'bytes / str', 'name', 'str', 'return', 'bytes') ／ --- replace (orig[65:66] -> prod[64:65]) ／ - MAKE_FUNCTION 4 |
| `sp_packaging_specifiers` | `D:\Python\Lib\site-packages\packaging\specifiers.py` | 注解、装饰器、装饰器链、f-string、海象、生成器、PEP604 | compile_error | 0/0 | 0 |  |  |
| `sp_packaging_version` | `D:\Python\Lib\site-packages\packaging\version.py` | 注解、装饰器、装饰器链、f-string、海象、PEP604 | compile_error | 0/0 | 0 |  |  |
| `sp_pandas_indexing` | `D:\Python\Lib\site-packages\pandas\core\indexing.py` | 装饰器、注解、f-string、except*、PEP604 | failure | 97/119 | 22 | C14、C2、C6 | - LOAD_CONST ('ndim', 'int', 'loc', 'Hashable', 'return', 'tuple[Hashable / slic ／ --- replace (orig[349:350] -> prod[348:349]) ／ - MAKE_FUNCTION 4 |
| `sp_pydantic_dataclasses` | `D:\Python\Lib\site-packages\pydantic\_internal\_dataclasses.py` | 注解、装饰器、f-string、生成器、PEP604 | compile_error | 0/0 | 0 |  |  |
| `sp_pydantic_fields` | `D:\Python\Lib\site-packages\pydantic\fields.py` | 注解、装饰器、装饰器链、f-string、海象、dataclass、生成器、PEP604 | compile_error | 0/0 | 0 |  |  |
| `sp_sqlalchemy_collections` | `D:\Python\Lib\site-packages\sqlalchemy\orm\collections.py` | 注解、装饰器、装饰器链、except* | compile_error | 0/0 | 0 |  |  |
| `sp_starlette_formparsers` | `D:\Python\Lib\site-packages\starlette\formparsers.py` | 装饰器、注解、async、f-string、dataclass、PEP604 | failure | 20/25 | 5 | C2、C6 | - LOAD_CONST ('src', 'bytes / bytearray', 'codec', 'str', 'return', 'str') ／ --- replace (orig[144:145] -> prod[143:144]) ／ - MAKE_FUNCTION 4 |
| `sp_sympy_qexpr` | `D:\Python\Lib\site-packages\sympy\physics\quantum\qexpr.py` | 装饰器、except* | success | 36/36 | 0 |  |  |
| `stdlib_argparse` | `D:\Python\Lib\argparse.py` | f-string、生成器 | failure | 185/192 | 7 | C10、C14、C2、C4 | - JUMP_FORWARD T ／ + LOAD_GLOBAL range ／ + LOAD_FAST start |
| `stdlib_ast` | `D:\Python\Lib\ast.py` | 装饰器、海象、f-string、生成器、except* | failure | 170/185 | 15 | C11、C14、C2 | - LOAD_CONST Ellipsis ／ + LOAD_CONST None ／ --- replace (orig[249:250] -> prod[249:250]) |
| `stdlib_asyncio_base_events` | `D:\Python\Lib\asyncio\base_events.py` | async、装饰器、f-string、asyncio | failure | 99/119 | 20 | C1、C10、C14、C2 | - NOP None ／ + LOAD_CONST '' ／ + STORE_NAME __doc__ |
| `stdlib_asyncio_streams` | `D:\Python\Lib\asyncio\streams.py` | async、装饰器、f-string | failure | 53/60 | 7 | C1、C2、C5 | - POP_JUMP_FORWARD_IF_FALSE T ／ + POP_JUMP_FORWARD_IF_TRUE T |
| `stdlib_asyncio_taskgroups` | `D:\Python\Lib\asyncio\taskgroups.py` | async、注解、f-string、ExceptionGroup、TaskGroup、asyncio | failure | 9/10 | 1 | C2 | - POP_JUMP_FORWARD_IF_FALSE T ／ + POP_JUMP_FORWARD_IF_TRUE T |
| `stdlib_asyncio_tasks` | `D:\Python\Lib\asyncio\tasks.py` | async、装饰器、f-string、生成器、except*、asyncio | failure | 43/53 | 10 | C1、C10、C11、C14、C2、C4 |  |
| `stdlib_asyncio_timeouts` | `D:\Python\Lib\asyncio\timeouts.py` | 装饰器、注解、async、f-string、asyncio | failure | 12/13 | 1 | C6 | - LOAD_CONST ('return', 'Timeout') ／ --- replace (orig[49:50] -> prod[48:49]) ／ - MAKE_FUNCTION 4 |
| `stdlib_contextlib` | `D:\Python\Lib\contextlib.py` | 装饰器、async、f-string | failure | 80/86 | 6 | C10、C14、C2、C5 | - LOAD_FAST func ／ - LOAD_FAST args ／ --- delete (orig[13:14] -> prod[11:11]) |
| `stdlib_csv` | `D:\Python\Lib\csv.py` | 装饰器、except*、PEP604 | failure | 29/32 | 3 | C2 |  |
| `stdlib_dataclasses` | `D:\Python\Lib\dataclasses.py` | 装饰器、match、f-string、生成器 | failure | 83/87 | 4 | C14、C2 |  |
| `stdlib_difflib` | `D:\Python\Lib\difflib.py` | f-string、生成器 | failure | 45/62 | 17 | C1、C2 | - NOP None ／ - NOP None ／ --- delete (orig[89:91] -> prod[87:87]) |
| `stdlib_enum` | `D:\Python\Lib\enum.py` | 装饰器、生成器、PEP604 | compile_error | 0/0 | 0 |  |  |
| `stdlib_functools` | `D:\Python\Lib\functools.py` | 装饰器、f-string | failure | 79/92 | 13 | C10、C2 | + JUMP_FORWARD T ／ + PUSH_EXC_INFO None ／ + LOAD_GLOBAL AttributeError |
| `stdlib_http_cookiejar` | `D:\Python\Lib\http\cookiejar.py` | f-string、生成器、PEP604 | failure | 90/105 | 15 | C2 | - JUMP_FORWARD T ／ + LOAD_CONST None ／ + RETURN_VALUE None |
| `stdlib_ipaddress` | `D:\Python\Lib\ipaddress.py` | 装饰器、装饰器链、f-string、生成器、PEP604 | failure | 163/166 | 3 | C14、C2 | - COPY 1 ／ --- delete (orig[14:15] -> prod[13:13]) ／ - STORE_FAST last |
| `stdlib_json_encoder` | `D:\Python\Lib\json\encoder.py` | f-string、生成器、PEP604 | failure | 12/15 | 3 | C14、C2 | - MAKE_CELL _key_separator ／ --- delete (orig[67:68] -> prod[66:66]) ／ - LOAD_CLOSURE _key_separator |
| `stdlib_re__parser` | `D:\Python\Lib\re\_parser.py` | 装饰器、PEP604 | failure | 35/43 | 8 | C2 | - COPY 1 ／ --- delete (orig[10:11] -> prod[9:9]) ／ - STORE_FAST hi |
| `stdlib_statistics` | `D:\Python\Lib\statistics.py` | 注解、装饰器、f-string、海象、生成器、PEP604 | failure | 71/77 | 6 | C11、C14、C2 | - POP_JUMP_FORWARD_IF_FALSE T ／ + POP_JUMP_FORWARD_IF_TRUE T |
| `stdlib_subprocess` | `D:\Python\Lib\subprocess.py` | 装饰器、海象、f-string、生成器 | failure | 68/78 | 10 | C10、C2 | - LOAD_GLOBAL Popen ／ - LOAD_FAST popenargs ／ - BUILD_MAP 0 |
| `stdlib_tarfile` | `D:\Python\Lib\tarfile.py` | 装饰器、f-string、生成器、PEP604 | failure | 141/160 | 19 | C10、C11、C2 |  |
| `stdlib_tomllib_parser` | `D:\Python\Lib\tomllib\_parser.py` | 注解、f-string、PEP604 | failure | 31/43 | 12 | C1、C2、C6、C9 | - LOAD_CONST ('fp', 'BinaryIO', 'parse_float', 'ParseFloat', 'return', 'dict[str ／ --- replace (orig[175:176] -> prod[174:175]) ／ - MAKE_FUNCTION 6 |
| `stdlib_typing` | `D:\Python\Lib\typing.py` | 装饰器、装饰器链、注解、f-string、生成器、PEP604 | failure | 285/309 | 24 | C2 | - LOAD_CONST Ellipsis ／ + LOAD_CONST None ／ --- replace (orig[1455:1456] -> prod[1455:1456]) |
| `stdlib_unittest_case` | `D:\Python\Lib\unittest\case.py` | 装饰器、f-string、生成器 | failure | 123/131 | 8 | C2、C4 | + LOAD_FAST self ／ + LOAD_ATTR success ／ + JUMP_IF_FALSE_OR_POP T |
| `stdlib_urllib_request` | `D:\Python\Lib\urllib\request.py` | 装饰器、f-string、生成器、PEP604 | failure | 184/194 | 10 | C2、C9 | + JUMP_FORWARD T |
| `stdlib_xml_ElementPath` | `D:\Python\Lib\xml\etree\ElementPath.py` | f-string、海象、生成器 | failure | 35/39 | 4 | C2 |  |

## 逐样本失败单元与差异明细

### `repo_core_cfg_basic_block`（failure，40/41 单元）

- 来源：`F:\Downloads\pythoncdc-main\core\cfg\basic_block.py`
- 特征：装饰器、注解、f-string、dataclass
- **`BasicBlock`**（根因：C6；指令数 206→202）
  > --- delete (orig[76:77] -> prod[76:76])
  >   - LOAD_CONST ('block', 'BasicBlock', 'return', None)
  > --- replace (orig[78:79] -> prod[77:78])
  >   - MAKE_FUNCTION 4

### `repo_core_cfg_builder`（failure，33/43 单元）

- 来源：`F:\Downloads\pythoncdc-main\core\cfg\cfg_builder.py`
- 特征：注解、装饰器、f-string
- **`ControlFlowGraph.to_dict`**（根因：C2；指令数 35→37）
  > --- insert (orig[34:34] -> prod[34:36])
  >   + POP_TOP None
  >   + LOAD_CONST None
- **`CFGBuilder`**（根因：C6；指令数 138→130）
  > --- delete (orig[42:43] -> prod[42:42])
  >   - LOAD_CONST ('return', None)
  > --- replace (orig[44:45] -> prod[43:44])
  >   - MAKE_FUNCTION 4
- **`CFGBuilder.build`**（根因：C2；指令数 65→62）
  > --- delete (orig[9:10] -> prod[9:9])
  >   - LOAD_GLOBAL ControlFlowGraph
  > --- delete (orig[14:16] -> prod[13:13])
  >   - PRECALL 1
- **`CFGBuilder._parse_instructions`**（根因：C2；指令数 127→121）
  > --- delete (orig[25:31] -> prod[25:25])
  >   - LOAD_GLOBAL isinstance
  >   - LOAD_FAST _argval
  >   - LOAD_GLOBAL tuple
- **`CFGBuilder._build_basic_blocks`**（根因：C3；指令数 224→218）
  > --- replace (orig[87:88] -> prod[87:88])
  >   - JUMP_IF_TRUE_OR_POP T
  >   + JUMP_IF_FALSE_OR_POP T
  > --- replace (orig[102:103] -> prod[102:103])
- **`CFGBuilder._split_block_at_offset`**（根因：C9；指令数 212→60）
  > --- delete (orig[31:33] -> prod[31:31])
  >   - POP_TOP None
  >   - JUMP_FORWARD T
  > --- delete (orig[60:66] -> prod[58:58])

### `repo_core_fast_stack`（failure，53/57 单元）

- 来源：`F:\Downloads\pythoncdc-main\core\fast_stack.py`
- 特征：注解、f-string
- **`FastStack`**（根因：C6；指令数 184→180）
  > --- delete (orig[63:64] -> prod[63:63])
  >   - LOAD_CONST ('return', None)
  > --- replace (orig[65:66] -> prod[64:65])
  >   - MAKE_FUNCTION 4
- **`FastStack.swap`**（根因：C2；指令数 78→69）
  > --- replace (orig[49:50] -> prod[49:50])
  >   - LOAD_FAST idx2
  >   + LOAD_FAST idx1
  > --- delete (orig[54:63] -> prod[54:54])
- **`StackHistory`**（根因：C6；指令数 44→43）
  > --- delete (orig[38:39] -> prod[38:38])
  >   - LOAD_CONST ('return', None)
  > --- replace (orig[40:41] -> prod[39:40])
  >   - MAKE_FUNCTION 4
- **`DebugStack`**（根因：C6；指令数 82→81）
  > --- delete (orig[68:69] -> prod[68:68])
  >   - LOAD_CONST ('return', None)
  > --- replace (orig[70:71] -> prod[69:70])
  >   - MAKE_FUNCTION 4

### `repo_tools_syntax_cov`（failure，13/14 单元）

- 来源：`F:\Downloads\pythoncdc-main\tools\kb\syntax_coverage.py`
- 特征：except*、PEP604
- **`main`**（根因：C1；指令数 702→700）
  > --- delete (orig[295:296] -> prod[295:295])
  >   - BUILD_LIST 0
  > --- delete (orig[297:298] -> prod[296:296])
  >   - STORE_FAST extra_covered

### `sp_anyio_fileio`（failure，116/124 单元）

- 来源：`D:\Python\Lib\site-packages\anyio\_core\_fileio.py`
- 特征：注解、装饰器、async、f-string、dataclass、生成器、PEP604
- **`<module>`**（根因：C2；指令数 205→181）
  > --- replace (orig[125:133] -> prod[125:126])
  >   - NOP None
  >   - NOP None
  >   - NOP None
- **`AsyncFile`**（根因：C6；指令数 114→93）
  > --- delete (orig[7:8] -> prod[7:7])
  >   - LOAD_CONST ('fp', 'IO[AnyStr]', 'return', 'None')
  > --- replace (orig[9:10] -> prod[8:9])
  >   - MAKE_FUNCTION 4
- **`AsyncFile.__aiter__`**（根因：C1；指令数 26→24）
  > --- delete (orig[14:16] -> prod[14:14])
  >   - STORE_FAST line
  >   - LOAD_FAST line
  > --- replace (orig[17:18] -> prod[15:16])
- **`_PathIterator`**（根因：C6；指令数 16→15）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - LOAD_CONST 'Iterator[PathLike[str]]'
  >   + LOAD_CONST "'Iterator[PathLike[str]]'"
  > --- delete (orig[10:11] -> prod[10:10])
- **`_PathIterator.__anext__`**（根因：C1；指令数 30→28）
  > --- replace (orig[19:22] -> prod[19:20])
  >   - STORE_FAST nextval
  >   - LOAD_FAST nextval
  >   - POP_JUMP_FORWARD_IF_NOT_NONE T
- **`Path`**（根因：C6；指令数 594→482）
  > --- delete (orig[14:15] -> prod[14:14])
  >   - LOAD_CONST ('args', 'str / PathLike[str]', 'return', 'None')
  > --- replace (orig[16:17] -> prod[15:16])
  >   - MAKE_FUNCTION 4

### `sp_anyio_functools`（failure，26/34 单元）

- 来源：`D:\Python\Lib\site-packages\anyio\functools.py`
- 特征：注解、装饰器、async、海象、PEP604
- **`<module>`**（根因：C6；指令数 296→286）
  > --- replace (orig[140:141] -> prod[140:141])
  >   - LOAD_CONST 'RunVar[WeakKeyDictionary[AsyncLRUCacheWrapper[Any, Any], OrderedDict[Hashable, tuple[_InitialMissingType, Lock, float / None] / tuple[Any,
  >   + LOAD_CONST "'RunVar[WeakKeyDictionary[AsyncLRUCacheWrapper[Any, Any], OrderedDict[Hashable, tuple[_InitialMissingType, Lock, float / None] / tuple[Any
  > --- replace (orig[157:158] -> prod[157:158])
- **`AsyncCacheInfo`**（根因：C2；指令数 28→28）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - LOAD_CONST 'int'
  >   + LOAD_CONST "'int'"
  > --- replace (orig[10:11] -> prod[10:11])
- **`AsyncCacheParameters`**（根因：C2；指令数 24→24）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - LOAD_CONST 'int / None'
  >   + LOAD_CONST "'int / None'"
  > --- replace (orig[10:11] -> prod[10:11])
- **`_LRUMethodWrapper`**（根因：C6；指令数 27→22）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('wrapper', 'AsyncLRUCacheWrapper[..., T]', 'instance', 'object')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4
- **`AsyncLRUCacheWrapper`**（根因：C6；指令数 33→27）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('func', 'Callable[P, Awaitable[T]]', 'maxsize', 'int / None', 'typed', 'bool', 'always_checkpoint', 'bool', 'ttl', 'int / None')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4
- **`AsyncLRUCacheWrapper.__call__`**（根因：C5；指令数 383→362）
  > --- insert (orig[178:178] -> prod[178:179])
  >   + EXTENDED_ARG 1
  > --- insert (orig[180:180] -> prod[181:182])
  >   + EXTENDED_ARG 1

### `sp_anyio_lowlevel`（failure，15/20 单元）

- 来源：`D:\Python\Lib\site-packages\anyio\lowlevel.py`
- 特征：注解、async、装饰器链、装饰器、f-string、dataclass、PEP604
- **`<module>`**（根因：C6；指令数 151→147）
  > --- delete (orig[72:73] -> prod[72:72])
  >   - LOAD_CONST ('return', 'None')
  > --- replace (orig[74:75] -> prod[73:74])
  >   - MAKE_FUNCTION 4
- **`EventLoopToken`**（根因：C2；指令数 18→18）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'type[AsyncBackend]'
  >   + LOAD_CONST "'type[AsyncBackend]'"
  > --- replace (orig[12:13] -> prod[12:13])
- **`RunvarToken`**（根因：C6；指令数 21→18）
  > --- delete (orig[7:8] -> prod[7:7])
  >   - LOAD_CONST ('var', 'RunVar[T]', 'value', 'T / Literal[_NoValueSet.NO_VALUE_SET]')
  > --- replace (orig[9:10] -> prod[8:9])
  >   - MAKE_FUNCTION 4
- **`RunVar`**（根因：C6；指令数 64→56）
  > --- replace (orig[13:14] -> prod[13:14])
  >   - LOAD_CONST 'Literal[_NoValueSet.NO_VALUE_SET]'
  >   + LOAD_CONST "'Literal[_NoValueSet.NO_VALUE_SET]'"
  > --- delete (orig[19:20] -> prod[19:19])
- **`RunVar.get`**（根因：C6；指令数 3→3）

### `sp_anyio_sync`（failure，94/110 单元）

- 来源：`D:\Python\Lib\site-packages\anyio\_core\_synchronization.py`
- 特征：装饰器、注解、async、海象、dataclass、PEP604
- **`EventStatistics`**（根因：C2；指令数 14→14）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'int'
  >   + LOAD_CONST "'int'"
- **`CapacityLimiterStatistics`**（根因：C2；指令数 26→26）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'int'
  >   + LOAD_CONST "'int'"
  > --- replace (orig[12:13] -> prod[12:13])
- **`LockStatistics`**（根因：C2；指令数 22→22）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'bool'
  >   + LOAD_CONST "'bool'"
  > --- replace (orig[12:13] -> prod[12:13])
- **`ConditionStatistics`**（根因：C2；指令数 18→18）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'int'
  >   + LOAD_CONST "'int'"
  > --- replace (orig[12:13] -> prod[12:13])
- **`SemaphoreStatistics`**（根因：C2；指令数 14→14）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'int'
  >   + LOAD_CONST "'int'"
- **`Event`**（根因：C6；指令数 27→22）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('return', 'Event')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4

### `sp_httpcore_models`（failure，33/41 单元）

- 来源：`D:\Python\Lib\site-packages\httpcore\_models.py`
- 特征：注解、async、装饰器、f-string、生成器、PEP604
- **`<module>`**（根因：C6；指令数 143→138）
  > --- delete (orig[63:64] -> prod[63:63])
  >   - LOAD_CONST ('value', 'bytes / str', 'name', 'str', 'return', 'bytes')
  > --- replace (orig[65:66] -> prod[64:65])
  >   - MAKE_FUNCTION 4
- **`ByteStream`**（根因：C6；指令数 25→21）
  > --- delete (orig[7:8] -> prod[7:7])
  >   - LOAD_CONST ('content', 'bytes', 'return', 'None')
  > --- replace (orig[9:10] -> prod[8:9])
  >   - MAKE_FUNCTION 4
- **`Origin`**（根因：C6；指令数 19→16）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('scheme', 'bytes', 'host', 'bytes', 'port', 'int', 'return', 'None')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4
- **`URL`**（根因：C6；指令数 40→35）
  > --- delete (orig[15:16] -> prod[15:15])
  >   - LOAD_CONST ('url', 'bytes / str', 'scheme', 'bytes / str', 'host', 'bytes / str', 'port', 'int / None', 'target', 'bytes / str', 'return', 'None')
  > --- replace (orig[17:18] -> prod[16:17])
  >   - MAKE_FUNCTION 7
- **`URL.__init__`**（根因：C2；指令数 76→75）
  > --- delete (orig[26:30] -> prod[26:26])
  >   - LOAD_ATTR port
  >   - LOAD_FAST self
  >   - STORE_ATTR port
- **`Request`**（根因：C6；指令数 22→20）
  > --- delete (orig[12:13] -> prod[12:12])
  >   - LOAD_CONST ('method', 'bytes / str', 'url', 'URL / bytes / str', 'headers', 'HeaderTypes', 'content', 'bytes / typing.Iterable[bytes] / typing.AsyncIt
  > --- replace (orig[14:15] -> prod[13:14])
  >   - MAKE_FUNCTION 6

### `sp_pandas_indexing`（failure，97/119 单元）

- 来源：`D:\Python\Lib\site-packages\pandas\core\indexing.py`
- 特征：装饰器、注解、f-string、except*、PEP604
- **`<module>`**（根因：C6；指令数 387→379）
  > --- delete (orig[347:348] -> prod[347:347])
  >   - LOAD_CONST ('ndim', 'int', 'loc', 'Hashable', 'return', 'tuple[Hashable / slice, ...]')
  > --- replace (orig[349:350] -> prod[348:349])
  >   - MAKE_FUNCTION 4
- **`IndexingMixin`**（根因：C6；指令数 37→33）
  > --- delete (orig[8:9] -> prod[8:8])
  >   - LOAD_CONST ('return', '_iLocIndexer')
  > --- replace (orig[10:11] -> prod[9:10])
  >   - MAKE_FUNCTION 4
- **`_LocationIndexer`**（根因：C2；指令数 151→132）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - LOAD_CONST 'str'
  >   + LOAD_CONST "'str'"
  > --- replace (orig[12:13] -> prod[12:13])
- **`_LocationIndexer._getitem_lowerdim`**（根因：C2；指令数 221→211）
  > --- delete (orig[50:60] -> prod[50:50])
  >   - LOAD_GLOBAL any
  >   - LOAD_CONST <code:<genexpr>>
  >   - MAKE_FUNCTION 0
- **`_LocationIndexer._getitem_lowerdim.<genexpr>`**（根因：C14；指令数 None→None）
- **`_LocationIndexer._getitem_nested_tuple`**（根因：C2；指令数 170→166）
  > --- replace (orig[73:74] -> prod[73:75])
  >   - JUMP_FORWARD T
  >   + LOAD_CONST None
  >   + RETURN_VALUE None

### `sp_starlette_formparsers`（failure，20/25 单元）

- 来源：`D:\Python\Lib\site-packages\starlette\formparsers.py`
- 特征：装饰器、注解、async、f-string、dataclass、PEP604
- **`<module>`**（根因：C6；指令数 173→172）
  > --- delete (orig[142:143] -> prod[142:142])
  >   - LOAD_CONST ('src', 'bytes / bytearray', 'codec', 'str', 'return', 'str')
  > --- replace (orig[144:145] -> prod[143:144])
  >   - MAKE_FUNCTION 4
- **`MultipartPart`**（根因：C2；指令数 48→48）
  > --- replace (orig[8:9] -> prod[8:9])
  >   - LOAD_CONST 'bytes / None'
  >   + LOAD_CONST "'bytes / None'"
  > --- replace (orig[14:15] -> prod[14:15])
- **`MultiPartException`**（根因：C6；指令数 11→10）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('message', 'str', 'return', 'None')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4
- **`FormParser`**（根因：C6；指令数 35→28）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('headers', 'Headers', 'stream', 'AsyncGenerator[bytes, None]', 'return', 'None')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4
- **`MultiPartParser`**（根因：C6；指令数 58→48）
  > --- delete (orig[16:17] -> prod[16:16])
  >   - LOAD_CONST ('headers', 'Headers', 'stream', 'AsyncGenerator[bytes, None]', 'max_files', 'int / float', 'max_fields', 'int / float', 'max_part_size', '
  > --- replace (orig[18:19] -> prod[17:18])
  >   - MAKE_FUNCTION 6

### `stdlib_argparse`（failure，185/192 单元）

- 来源：`D:\Python\Lib\argparse.py`
- 特征：f-string、生成器
- **`HelpFormatter._format_actions_usage`**（根因：C2；指令数 423→426）
  > --- replace (orig[115:116] -> prod[115:131])
  >   - JUMP_FORWARD T
  >   + LOAD_GLOBAL range
  >   + LOAD_FAST start
- **`HelpFormatter._iter_indented_subactions`**（根因：C2；指令数 42→29）
  > --- delete (orig[0:2] -> prod[0:0])
  >   - RETURN_GENERATOR None
  >   - POP_TOP None
  > --- delete (orig[11:22] -> prod[9:9])
- **`_ActionsContainer.add_argument`**（根因：C2；指令数 181→180）
  > --- delete (orig[41:42] -> prod[41:41])
  >   - JUMP_FORWARD T
- **`ArgumentParser.__init__`**（根因：C10；指令数 160→161）
  > --- insert (orig[139:139] -> prod[139:151])
  >   + JUMP_FORWARD T
  >   + PUSH_EXC_INFO None
  >   + LOAD_GLOBAL AttributeError
- **`ArgumentParser._parse_known_args`**（根因：C2、C4；指令数 411→411）
- **`ArgumentParser._parse_known_args.consume_optional`**（根因：C14；指令数 None→None）

### `stdlib_ast`（failure，170/185 单元）

- 来源：`D:\Python\Lib\ast.py`
- 特征：装饰器、海象、f-string、生成器、except*
- **`<module>`**（根因：C2；指令数 405→405）
  > --- replace (orig[218:219] -> prod[218:219])
  >   - LOAD_CONST Ellipsis
  >   + LOAD_CONST None
  > --- replace (orig[249:250] -> prod[249:250])
- **`literal_eval._convert`**（根因：C14；指令数 None→None）
- **`dump._format`**（根因：C14；指令数 None→None）
- **`NodeVisitor.visit_Constant`**（根因：C11；指令数 86→86）
- **`Ellipsis.__new__`**（根因：C2；指令数 28→28）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - LOAD_CONST Ellipsis
  >   + LOAD_CONST None
- **`_Unparser.visit_ImportFrom`**（根因：C2；指令数 50→52）
  > --- insert (orig[29:29] -> prod[29:31])
  >   + LOAD_CONST None
  >   + RETURN_VALUE None

### `stdlib_asyncio_base_events`（failure，99/119 单元）

- 来源：`D:\Python\Lib\asyncio\base_events.py`
- 特征：async、装饰器、f-string、asyncio
- **`Server`**（根因：C2；指令数 51→52）
  > --- replace (orig[5:6] -> prod[5:7])
  >   - NOP None
  >   + LOAD_CONST ''
  >   + STORE_NAME __doc__
- **`Server.wait_closed`**（根因：C2；指令数 34→36）
  > --- insert (orig[34:34] -> prod[34:36])
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
- **`BaseEventLoop.shutdown_asyncgens`**（根因：C1；指令数 77→46）
  > --- delete (orig[14:45] -> prod[14:14])
  >   - LOAD_GLOBAL list
  >   - LOAD_FAST self
  >   - LOAD_ATTR _asyncgens
- **`BaseEventLoop.shutdown_asyncgens.<listcomp>`**（根因：C14；指令数 None→None）
- **`BaseEventLoop.run_until_complete`**（根因：C10；指令数 101→103）
  > --- replace (orig[57:58] -> prod[57:58])
  >   - POP_JUMP_FORWARD_IF_TRUE T
  >   + POP_JUMP_FORWARD_IF_FALSE T
  > --- insert (orig[63:63] -> prod[63:64])
- **`BaseEventLoop.close`**（根因：C2；指令数 63→60）
  > --- delete (orig[16:19] -> prod[16:16])
  >   - LOAD_FAST self
  >   - LOAD_ATTR _debug
  >   - POP_JUMP_FORWARD_IF_FALSE T

### `stdlib_asyncio_streams`（failure，53/60 单元）

- 来源：`D:\Python\Lib\asyncio\streams.py`
- 特征：async、装饰器、f-string
- **`FlowControlMixin.pause_writing`**（根因：C2；指令数 26→26）
  > --- replace (orig[3:4] -> prod[3:4])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`StreamWriter.drain`**（根因：C5；指令数 47→22）
  > --- delete (orig[17:34] -> prod[17:17])
  >   - LOAD_ATTR _transport
  >   - LOAD_METHOD is_closing
  >   - PRECALL 0
- **`StreamReader.feed_data`**（根因：C2；指令数 75→75）
  > --- replace (orig[3:4] -> prod[3:4])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`StreamReader._wait_for_data`**（根因：C2；指令数 64→64）
  > --- replace (orig[16:17] -> prod[16:17])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`StreamReader.readuntil`**（根因：C2；指令数 143→144）
  > --- insert (orig[69:69] -> prod[69:70])
  >   + JUMP_FORWARD T
- **`StreamReader.read`**（根因：C1；指令数 92→89）
  > --- delete (orig[34:36] -> prod[34:34])
  >   - STORE_FAST block
  >   - LOAD_FAST block
  > --- replace (orig[40:41] -> prod[38:39])

### `stdlib_asyncio_taskgroups`（failure，9/10 单元）

- 来源：`D:\Python\Lib\asyncio\taskgroups.py`
- 特征：async、注解、f-string、ExceptionGroup、TaskGroup、asyncio
- **`TaskGroup.__aexit__`**（根因：C2；指令数 167→167）
  > --- replace (orig[113:114] -> prod[113:114])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T

### `stdlib_asyncio_tasks`（failure，43/53 单元）

- 来源：`D:\Python\Lib\asyncio\tasks.py`
- 特征：async、装饰器、f-string、生成器、except*、asyncio
- **`<module>`**（根因：C11；指令数 298→298）
- **`_set_task_name`**（根因：C4；指令数 38→38）
- **`wait_for`**（根因：C10；指令数 244→229）
  > --- delete (orig[112:113] -> prod[112:112])
  >   - NOP None
  > --- delete (orig[121:169] -> prod[120:120])
  >   - JUMP_FORWARD T
- **`_wait`**（根因：C1；指令数 141→141）
  > --- insert (orig[72:72] -> prod[72:74])
  >   + POP_TOP None
  >   + LOAD_FAST fs
  > --- insert (orig[92:92] -> prod[94:96])
- **`_wait._on_completion`**（根因：C14；指令数 None→None）
- **`as_completed`**（根因：C2；指令数 123→125）
  > --- insert (orig[2:2] -> prod[2:3])
  >   + MAKE_CELL f
  > --- replace (orig[77:78] -> prod[78:80])
  >   - BUILD_TUPLE 1

### `stdlib_asyncio_timeouts`（failure，12/13 单元）

- 来源：`D:\Python\Lib\asyncio\timeouts.py`
- 特征：装饰器、注解、async、f-string、asyncio
- **`Timeout`**（根因：C6；指令数 79→77）
  > --- delete (orig[47:48] -> prod[47:47])
  >   - LOAD_CONST ('return', 'Timeout')
  > --- replace (orig[49:50] -> prod[48:49])
  >   - MAKE_FUNCTION 4

### `stdlib_contextlib`（failure，80/86 单元）

- 来源：`D:\Python\Lib\contextlib.py`
- 特征：装饰器、async、f-string
- **`_GeneratorContextManagerBase.__init__`**（根因：C2；指令数 40→39）
  > --- delete (orig[10:12] -> prod[10:10])
  >   - LOAD_FAST func
  >   - LOAD_FAST args
  > --- delete (orig[13:14] -> prod[11:11])
- **`_GeneratorContextManager.__exit__`**（根因：C10；指令数 160→161）
  > --- insert (orig[10:10] -> prod[10:23])
  >   + JUMP_FORWARD T
  >   + PUSH_EXC_INFO None
  >   + LOAD_GLOBAL StopIteration
- **`_AsyncGeneratorContextManager.__aexit__`**（根因：C5、C10；指令数 188→165）
  > --- replace (orig[18:41] -> prod[18:19])
  >   - NOP None
  >   - LOAD_GLOBAL RuntimeError
  >   - LOAD_CONST "generator didn't stop"
- **`ExitStack.__exit__._fix_exception_context`**（根因：C14；指令数 None→None）
- **`AsyncExitStack.__aexit__`**（根因：C2、C2；指令数 127→127）
- **`AsyncExitStack.__aexit__._fix_exception_context`**（根因：C14；指令数 None→None）

### `stdlib_csv`（failure，29/32 单元）

- 来源：`D:\Python\Lib\csv.py`
- 特征：装饰器、except*、PEP604
- **`Sniffer._guess_quote_and_delimiter`**（根因：C2；指令数 208→208）
- **`Sniffer._guess_delimiter`**（根因：C2；指令数 419→419）
  > --- delete (orig[41:42] -> prod[41:41])
  >   - LOAD_CONST 0
  > --- delete (orig[44:45] -> prod[43:43])
  >   - STORE_FAST start
- **`Sniffer.has_header`**（根因：C2；指令数 199→200）
  > --- replace (orig[173:178] -> prod[173:174])
  >   - LOAD_FAST hasHeader
  >   - LOAD_CONST 1
  >   - BINARY_OP 23

### `stdlib_dataclasses`（failure，83/87 单元）

- 来源：`D:\Python\Lib\dataclasses.py`
- 特征：装饰器、match、f-string、生成器
- **`_get_field`**（根因：C2；指令数 203→203）
- **`_hash_add.<listcomp>`**（根因：C14；指令数 None→None）
- **`_process_class`**（根因：C2；指令数 606→599）
  > --- insert (orig[158:158] -> prod[158:159])
  >   + JUMP_BACKWARD T
  > --- insert (orig[279:279] -> prod[280:281])
  >   + UNARY_NOT None
- **`_add_slots`**（根因：C2；指令数 144→148）
  > --- insert (orig[75:75] -> prod[75:79])
  >   + LOAD_CONST 1
  >   + LOAD_FAST cls_dict
  >   + LOAD_CONST '__slots__'

### `stdlib_difflib`（failure，45/62 单元）

- 来源：`D:\Python\Lib\difflib.py`
- 特征：f-string、生成器
- **`<module>`**（根因：C2；指令数 154→147）
  > --- delete (orig[80:82] -> prod[80:80])
  >   - NOP None
  >   - NOP None
  > --- delete (orig[89:91] -> prod[87:87])
- **`SequenceMatcher.__chain_b`**（根因：C1；指令数 134→128）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - COPY 1
  > --- delete (orig[8:9] -> prod[7:7])
  >   - STORE_FAST b2j
- **`SequenceMatcher.find_longest_match`**（根因：C2；指令数 407→346）
  > --- delete (orig[30:32] -> prod[30:30])
  >   - LOAD_FAST alo
  >   - LOAD_FAST blo
  > --- delete (orig[34:36] -> prod[32:32])
- **`SequenceMatcher.get_matching_blocks`**（根因：C1；指令数 196→182）
  > --- delete (orig[9:14] -> prod[9:9])
  >   - LOAD_ATTR a
  >   - PRECALL 1
  >   - CALL 1
- **`SequenceMatcher.get_opcodes`**（根因：C1；指令数 89→85）
  > --- delete (orig[8:9] -> prod[8:8])
  >   - COPY 1
  > --- delete (orig[10:11] -> prod[9:9])
  >   - STORE_FAST j
- **`SequenceMatcher.get_grouped_opcodes`**（根因：C2；指令数 198→200）
  > --- insert (orig[198:198] -> prod[198:200])
  >   + LOAD_CONST None
  >   + RETURN_VALUE None

### `stdlib_functools`（failure，79/92 单元）

- 来源：`D:\Python\Lib\functools.py`
- 特征：装饰器、f-string
- **`update_wrapper`**（根因：C10；指令数 56→57）
  > --- insert (orig[12:12] -> prod[12:24])
  >   + JUMP_FORWARD T
  >   + PUSH_EXC_INFO None
  >   + LOAD_GLOBAL AttributeError
- **`partial.__new__`**（根因：C2；指令数 54→49）
  > --- delete (orig[24:29] -> prod[24:24])
  >   - LOAD_FAST func
  >   - LOAD_ATTR keywords
  >   - DICT_UPDATE 1
- **`partial.__call__`**（根因：C2；指令数 23→18）
  > --- delete (orig[2:7] -> prod[2:2])
  >   - LOAD_FAST self
  >   - LOAD_ATTR keywords
  >   - DICT_UPDATE 1
- **`partial.__reduce__`**（根因：C2；指令数 23→8）
  > --- delete (orig[1:12] -> prod[1:1])
  >   - LOAD_GLOBAL type
  >   - LOAD_FAST self
  >   - PRECALL 1
- **`partial.__setstate__`**（根因：C2；指令数 108→114）
  > --- insert (orig[108:108] -> prod[108:114])
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
  >   + LOAD_CONST None
- **`partialmethod.__init__`**（根因：C2；指令数 58→53）
  > --- delete (orig[38:43] -> prod[38:38])
  >   - LOAD_FAST func
  >   - LOAD_ATTR keywords
  >   - DICT_UPDATE 1

### `stdlib_http_cookiejar`（failure，90/105 单元）

- 来源：`D:\Python\Lib\http\cookiejar.py`
- 特征：f-string、生成器、PEP604
- **`_timegm`**（根因：C2；指令数 84→101）
  > --- replace (orig[28:29] -> prod[28:30])
  >   - JUMP_FORWARD T
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
- **`split_header_words`**（根因：C2；指令数 179→179）
  > --- replace (orig[6:7] -> prod[6:7])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`user_domain_match`**（根因：C2；指令数 55→57）
  > --- insert (orig[55:55] -> prod[55:57])
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
- **`DefaultCookiePolicy.set_ok_version`**（根因：C2；指令数 47→47）
  > --- replace (orig[37:38] -> prod[37:38])
  >   - POP_JUMP_FORWARD_IF_TRUE T
  >   + POP_JUMP_FORWARD_IF_FALSE T
- **`DefaultCookiePolicy.set_ok_path`**（根因：C2；指令数 42→66）
  > --- insert (orig[14:14] -> prod[14:38])
  >   + LOAD_FAST self
  >   + LOAD_ATTR strict_ns_set_path
  >   + POP_JUMP_FORWARD_IF_FALSE T
- **`DefaultCookiePolicy.set_ok_domain`**（根因：C2；指令数 268→271）
  > --- insert (orig[49:49] -> prod[49:50])
  >   + EXTENDED_ARG 2
  > --- insert (orig[57:57] -> prod[58:59])
  >   + EXTENDED_ARG 2

### `stdlib_ipaddress`（failure，163/166 单元）

- 来源：`D:\Python\Lib\ipaddress.py`
- 特征：装饰器、装饰器链、f-string、生成器、PEP604
- **`_find_address_range`**（根因：C2；指令数 46→44）
  > --- delete (orig[12:13] -> prod[12:12])
  >   - COPY 1
  > --- delete (orig[14:15] -> prod[13:13])
  >   - STORE_FAST last
- **`_BaseNetwork.address_exclude`**（根因：C2；指令数 175→168）
  > --- delete (orig[101:107] -> prod[101:101])
  >   - LOAD_FAST other
  >   - LOAD_METHOD subnet_of
  >   - LOAD_FAST s2
- **`_BaseNetwork.is_private.<genexpr>`**（根因：C14；指令数 None→None）

### `stdlib_json_encoder`（failure，12/15 单元）

- 来源：`D:\Python\Lib\json\encoder.py`
- 特征：f-string、生成器、PEP604
- **`_make_iterencode`**（根因：C2；指令数 106→104）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - MAKE_CELL _key_separator
  > --- delete (orig[67:68] -> prod[66:66])
  >   - LOAD_CLOSURE _key_separator
- **`_make_iterencode._iterencode_list`**（根因：C14；指令数 None→None）
- **`_make_iterencode._iterencode_dict`**（根因：C14；指令数 None→None）

### `stdlib_re__parser`（failure，35/43 单元）

- 来源：`D:\Python\Lib\re\_parser.py`
- 特征：装饰器、PEP604
- **`SubPattern.getwidth`**（根因：C2；指令数 258→250）
  > --- delete (orig[8:9] -> prod[8:8])
  >   - COPY 1
  > --- delete (orig[10:11] -> prod[9:9])
  >   - STORE_FAST hi
- **`Tokenizer.getuntil`**（根因：C2；指令数 59→55）
  > --- replace (orig[13:14] -> prod[13:31])
  >   - POP_JUMP_FORWARD_IF_NOT_NONE T
  >   + POP_JUMP_FORWARD_IF_FALSE T
  >   + LOAD_FAST c
- **`_class_escape`**（根因：C2；指令数 358→365）
  > --- insert (orig[131:131] -> prod[131:138])
  >   + POP_JUMP_FORWARD_IF_FALSE T
  >   + LOAD_GLOBAL len
  >   + LOAD_FAST escape
- **`_escape`**（根因：C2；指令数 454→461）
  > --- insert (orig[125:125] -> prod[125:132])
  >   + POP_JUMP_FORWARD_IF_FALSE T
  >   + LOAD_GLOBAL len
  >   + LOAD_FAST escape
- **`_parse_sub`**（根因：C2；指令数 188→158）
  > --- replace (orig[34:49] -> prod[34:35])
  >   - PUSH_NULL None
  >   - LOAD_FAST sourcematch
  >   - LOAD_CONST '/'
- **`_parse`**（根因：C2；指令数 1756→1727）
  > --- replace (orig[56:57] -> prod[56:57])
  >   - POP_JUMP_FORWARD_IF_NONE T
  >   + POP_JUMP_FORWARD_IF_NOT_NONE T
  > --- replace (orig[62:63] -> prod[62:64])

### `stdlib_statistics`（failure，71/77 单元）

- 来源：`D:\Python\Lib\statistics.py`
- 特征：注解、装饰器、f-string、海象、生成器、PEP604
- **`_sum`**（根因：C2；指令数 99→99）
  > --- replace (orig[70:71] -> prod[70:71])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`_ss`**（根因：C2；指令数 181→181）
  > --- replace (orig[124:125] -> prod[124:125])
  >   - POP_JUMP_FORWARD_IF_FALSE T
  >   + POP_JUMP_FORWARD_IF_TRUE T
- **`_exact_ratio`**（根因：C2；指令数 68→68）
  > --- replace (orig[25:26] -> prod[25:26])
  >   - LOAD_ASSERTION_ERROR None
  >   + LOAD_GLOBAL AssertionError
- **`harmonic_mean`**（根因：C11；指令数 170→170）
- **`NormalDist.samples`**（根因：C2；指令数 37→31）
  > --- delete (orig[2:3] -> prod[2:2])
  >   - MAKE_CELL sigma
  > --- delete (orig[18:21] -> prod[17:17])
  >   - LOAD_FAST self
- **`NormalDist.samples.<listcomp>`**（根因：C14；指令数 None→None）

### `stdlib_subprocess`（failure，68/78 单元）

- 来源：`D:\Python\Lib\subprocess.py`
- 特征：装饰器、海象、f-string、生成器
- **`call`**（根因：C2；指令数 48→43）
  > --- delete (orig[1:4] -> prod[1:1])
  >   - LOAD_GLOBAL Popen
  >   - LOAD_FAST popenargs
  >   - BUILD_MAP 0
- **`run`**（根因：C2；指令数 153→148）
  > --- delete (orig[45:48] -> prod[45:45])
  >   - LOAD_GLOBAL Popen
  >   - LOAD_FAST popenargs
  >   - BUILD_MAP 0
- **`Popen.__init__`**（根因：C2；指令数 755→759）
  > --- replace (orig[69:70] -> prod[69:71])
  >   - JUMP_FORWARD T
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
- **`Popen.__exit__`**（根因：C10；指令数 118→121）
  > --- replace (orig[114:115] -> prod[114:118])
  >   - RERAISE 0
  >   + POP_TOP None
  >   + POP_EXCEPT None
- **`Popen._check_timeout`**（根因：C2；指令数 41→44）
  > --- insert (orig[14:14] -> prod[14:15])
  >   + LOAD_METHOD args
  > --- replace (orig[38:39] -> prod[39:40])
  >   - RAISE_VARARGS 1
- **`Popen._on_error_fd_closer`**（根因：C10；指令数 70→73）
  > --- insert (orig[29:29] -> prod[29:32])
  >   + POP_EXCEPT None
  >   + LOAD_CONST None
  >   + RETURN_VALUE None

### `stdlib_tarfile`（failure，141/160 单元）

- 来源：`D:\Python\Lib\tarfile.py`
- 特征：装饰器、f-string、生成器、PEP604
- **`itn`**（根因：C2；指令数 118→118）
- **`copyfileobj`**（根因：C2；指令数 95→10）
  > --- replace (orig[5:9] -> prod[5:8])
  >   - LOAD_FAST length
  >   - LOAD_CONST 0
  >   - COMPARE_OP ==
- **`_Stream.__init__`**（根因：C10；指令数 247→250）
  > --- insert (orig[240:240] -> prod[240:243])
  >   + POP_EXCEPT None
  >   + LOAD_CONST None
  >   + RETURN_VALUE None
- **`_Stream._init_read_gz`**（根因：C2；指令数 138→146）
  > --- insert (orig[104:104] -> prod[104:106])
  >   + JUMP_FORWARD T
  >   + JUMP_FORWARD T
  > --- insert (orig[122:122] -> prod[124:126])
- **`_Stream._read`**（根因：C11；指令数 112→112）
- **`_FileInFile.read`**（根因：C2；指令数 143→132）
  > --- delete (orig[25:26] -> prod[25:25])
  >   - EXTENDED_ARG 1
  > --- delete (orig[41:43] -> prod[40:40])
  >   - SWAP 2

### `stdlib_tomllib_parser`（failure，31/43 单元）

- 来源：`D:\Python\Lib\tomllib\_parser.py`
- 特征：注解、f-string、PEP604
- **`<module>`**（根因：C6；指令数 306→281）
  > --- delete (orig[173:174] -> prod[173:173])
  >   - LOAD_CONST ('fp', 'BinaryIO', 'parse_float', 'ParseFloat', 'return', 'dict[str, Any]')
  > --- replace (orig[175:176] -> prod[174:175])
  >   - MAKE_FUNCTION 6
- **`loads`**（根因：C2；指令数 200→200）
  > --- insert (orig[35:35] -> prod[35:44])
  >   + LOAD_FAST char
  >   + LOAD_CONST '\n'
  >   + COMPARE_OP ==
- **`Flags`**（根因：C6；指令数 37→31）
  > --- delete (orig[11:12] -> prod[11:11])
  >   - LOAD_CONST ('return', 'None')
  > --- replace (orig[13:14] -> prod[12:13])
  >   - MAKE_FUNCTION 4
- **`Flags.set`**（根因：C1、C9；指令数 73→65）
  > --- delete (orig[5:10] -> prod[5:5])
  >   - LOAD_CONST None
  >   - LOAD_CONST -1
  >   - BUILD_SLICE 2
- **`Flags.is_`**（根因：C2；指令数 67→67）
  > --- replace (orig[65:66] -> prod[65:66])
  >   - LOAD_CONST False
  >   + LOAD_CONST None
- **`NestedDict`**（根因：C6；指令数 22→19）
  > --- delete (orig[5:6] -> prod[5:5])
  >   - LOAD_CONST ('return', 'None')
  > --- replace (orig[7:8] -> prod[6:7])
  >   - MAKE_FUNCTION 4

### `stdlib_typing`（failure，285/309 单元）

- 来源：`D:\Python\Lib\typing.py`
- 特征：装饰器、装饰器链、注解、f-string、生成器、PEP604
- **`<module>`**（根因：C2；指令数 1473→1471）
  > --- replace (orig[1450:1451] -> prod[1450:1451])
  >   - LOAD_CONST Ellipsis
  >   + LOAD_CONST None
  > --- replace (orig[1455:1456] -> prod[1455:1456])
- **`_is_param_expr`**（根因：C2；指令数 15→15）
  > --- replace (orig[2:3] -> prod[2:3])
  >   - LOAD_CONST Ellipsis
  >   + LOAD_CONST None
- **`_should_unflatten_callable_args`**（根因：C2；指令数 23→23）
- **`_type_repr`**（根因：C2；指令数 57→55）
  > --- replace (orig[37:40] -> prod[37:38])
  >   - LOAD_CONST Ellipsis
  >   - IS_OP 0
  >   - POP_JUMP_FORWARD_IF_FALSE T
- **`_check_generic`**（根因：C2；指令数 45→44）
  > --- delete (orig[20:21] -> prod[20:20])
  >   - LOAD_GLOBAL TypeError
  > --- replace (orig[40:43] -> prod[39:40])
  >   - PRECALL 1
- **`_unpack_args`**（根因：C2；指令数 40→39）
  > --- replace (orig[21:24] -> prod[21:22])
  >   - LOAD_CONST Ellipsis
  >   - IS_OP 0
  >   - POP_JUMP_FORWARD_IF_TRUE T

### `stdlib_unittest_case`（failure，123/131 单元）

- 来源：`D:\Python\Lib\unittest\case.py`
- 特征：装饰器、f-string、生成器
- **`_Outcome.testPartExecutor`**（根因：C2；指令数 132→142）
  > --- insert (orig[14:14] -> prod[14:20])
  >   + LOAD_FAST self
  >   + LOAD_ATTR success
  >   + JUMP_IF_FALSE_OR_POP T
- **`TestCase._addExpectedFailure`**（根因：C4；指令数 40→40）
- **`TestCase._addUnexpectedSuccess`**（根因：C4；指令数 57→57）
- **`TestCase.run`**（根因：C2；指令数 318→417）
  > --- insert (orig[85:85] -> prod[85:99])
  >   + POP_TOP None
  >   + PUSH_NULL None
  >   + LOAD_FAST result
- **`TestCase.doCleanups`**（根因：C2；指令数 64→57）
  > --- delete (orig[1:8] -> prod[1:1])
  >   - LOAD_FAST self
  >   - LOAD_ATTR _outcome
  >   - JUMP_IF_TRUE_OR_POP T
- **`TestCase.debug`**（根因：C2；指令数 91→78）
  > --- delete (orig[71:84] -> prod[71:71])
  >   - PUSH_NULL None
  >   - LOAD_FAST self
  >   - LOAD_ATTR _callCleanup

### `stdlib_urllib_request`（failure，184/194 单元）

- 来源：`D:\Python\Lib\urllib\request.py`
- 特征：装饰器、f-string、生成器、PEP604
- **`urlretrieve`**（根因：C2；指令数 202→203）
  > --- insert (orig[46:46] -> prod[46:47])
  >   + JUMP_FORWARD T
- **`urlcleanup`**（根因：C9；指令数 37→33）
  > --- insert (orig[1:1] -> prod[1:2])
  >   + NOP None
  > --- delete (orig[24:29] -> prod[25:25])
  >   - LOAD_GLOBAL _url_tempfiles
- **`Request.header_items`**（根因：C2；指令数 17→11）
  > --- delete (orig[2:8] -> prod[2:2])
  >   - LOAD_FAST self
  >   - LOAD_ATTR unredirected_hdrs
  >   - DICT_UPDATE 1
- **`HTTPRedirectHandler.redirect_request`**（根因：C2；指令数 65→65）
- **`HTTPPasswordMgr.find_user_password`**（根因：C2；指令数 53→52）
  > --- delete (orig[41:42] -> prod[41:41])
  >   - SWAP 2
  > --- delete (orig[43:44] -> prod[42:42])
  >   - SWAP 2
- **`parse_http_list`**（根因：C2；指令数 81→80）
  > --- delete (orig[6:7] -> prod[6:6])
  >   - COPY 1
  > --- delete (orig[8:9] -> prod[7:7])
  >   - STORE_FAST quote

### `stdlib_xml_ElementPath`（failure，35/39 单元）

- 来源：`D:\Python\Lib\xml\etree\ElementPath.py`
- 特征：f-string、海象、生成器
- **`xpath_tokenizer`**（根因：C2、C2；指令数 120→120）
- **`get_parent_map`**（根因：C2；指令数 31→29）
  > --- delete (orig[7:8] -> prod[7:7])
  >   - COPY 1
  > --- delete (orig[10:11] -> prod[9:9])
  >   - STORE_FAST parent_map
- **`prepare_predicate`**（根因：C2；指令数 330→335）
  > --- delete (orig[10:29] -> prod[10:10])
  >   - NOP None
  >   - PUSH_NULL None
  >   - LOAD_FAST next
- **`iterfind`**（根因：C2；指令数 195→177）
  > --- delete (orig[36:37] -> prod[36:36])
  >   - EXTENDED_ARG 1
  > --- delete (orig[41:42] -> prod[40:40])
  >   - EXTENDED_ARG 1
