# L4 语料外失败样本：源码级语义差异（§2 证据）

> 判据读数见 `logs/l4_offcorpus_table.md`；本表是**源码级**核对，不依赖判据 verdict。
> 「源=」指源码 AST 位置，「产物=」指 `offcorpus/<slug>OK.py` AST 位置。

## `repo_core_cfg_basic_block`（判据 failure）

- 源：`F:\Downloads\pythoncdc-main\core\cfg\basic_block.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\repo_core_cfg_basic_blockOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `BasicBlock` | L38 | L35 | 常量数: 源=148 产物=131；仅产物常量: 'BasicBlock(', 'Block ', 'JUMP_ABSOLUTE', 'JUMP_FORWARD', 'JUMP_IF_FALSE_OR_POP' |

### AST 结构差分（源 vs 产物）

**`BasicBlock`**（源 L38 ↔ 产物 L35）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='instructions',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='List', ctx=Load()),
-      slice=Name(id='Instruction', ctx=Load()),
-      ctx=Load()),
-     value=List(elts=[], ctx=Load()),
...(截断)
```

## `repo_core_cfg_builder`（判据 failure）

- 源：`F:\Downloads\pythoncdc-main\core\cfg\cfg_builder.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\repo_core_cfg_builderOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `ControlFlowGraph.to_dict` | L58 | L47 | return: 源=1 产物=0 |
| `CFGBuilder` | L68 | L49 | boolop: 源=22 产物=21；break: 源=8 产物=7；continue: 源=6 产物=15；return: 源=38 产物=39；slice: 源=3 产物=1；常量数: 源=268 产物=275 |
| `CFGBuilder.build` | L113 | L60 | （指纹一致） |
| `CFGBuilder._parse_instructions` | L133 | L74 | return: 源=0 产物=1；returns_ann: 源=1 产物=0 |
| `CFGBuilder._build_basic_blocks` | L200 | L120 | boolop: 源=7 产物=4；returns_ann: 源=1 产物=0；常量数: 源=19 产物=17 |
| `CFGBuilder._split_block_at_offset` | L327 | L213 | break: 源=2 产物=1；return: 源=3 产物=2；slice: 源=2 产物=0；常量数: 源=14 产物=16 |
| `CFGBuilder._r4g_stack_delta` | L420 | L257 | boolop: 源=1 产物=2；常量数: 源=87 产物=88 |
| `CFGBuilder._r4g_split_merge_target` | L478 | L312 | boolop: 源=4 产物=3；continue: 源=1 产物=3；常量数: 源=35 产物=43；仅源常量: True |
| `CFGPrinter.print_cfg` | L607 | L413 | comprehension: 源=1 产物=2；fstring: 源=7 产物=9；仅源常量: '=', 60；仅产物常量: '============================================================' |
| `None` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`ControlFlowGraph.to_dict`**（源 L58 ↔ 产物 L47）

```diff
-  Return(
+  Expr(
```

**`CFGBuilder`**（源 L68 ↔ 产物 L49）

```diff
-     Constant(value='JUMP_FORWARD'),
+     Constant(value='FOR_ITER'),
+     Constant(value='FOR_ITER_DICT'),
+     Constant(value='FOR_ITER_GEN'),
+     Constant(value='FOR_ITER_LIST'),
+     Constant(value='FOR_ITER_RANGE'),
+     Constant(value='FOR_ITER_TUPLE'),
-     Constant(value='POP_JUMP_IF_TRUE'),
-     Constant(value='POP_JUMP_IF_FALSE'),
-     Constant(value='POP_JUMP_FORWARD_IF_TRUE'),
+     Constant(value='JUMP_FORWARD'),
+     Constant(value='JUMP_IF_FALSE_OR_POP'),
+     Constant(value='JUMP_IF_TRUE_OR_POP'),
+     Constant(value='POP_JUMP_BACKWARD_IF_FALSE'),
...(截断)
```

**`CFGBuilder.build`**（源 L113 ↔ 产物 L60）

```diff
-   value=Call(
-    func=Name(id='ControlFlowGraph', ctx=Load()),
-    args=[
-     BoolOp(
-      op=Or(),
-      values=[
-       Name(id='name', ctx=Load()),
-       Attribute(
-        value=Name(id='code_obj', ctx=Load()),
-        attr='co_name',
-        ctx=Load())])],
-    keywords=[])),
+   value=BoolOp(
+    op=Or(),
...(截断)
```

**`CFGBuilder._parse_instructions`**（源 L133 ↔ 产物 L74）

```diff
-           Constant(value=None)]),
-         UnaryOp(
-          op=Not(),
-          operand=Call(
-           func=Name(id='isinstance', ctx=Load()),
-           args=[
-            Name(id='_argval', ctx=Load()),
-            Name(id='tuple', ctx=Load())],
-           keywords=[]))]),
+           Constant(value=None)])]),
-        keywords=[]))])],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))])],
...(截断)
```

**`CFGBuilder._build_basic_blocks`**（源 L200 ↔ 产物 L120）

```diff
-    Return()],
+    Return(
+     value=Constant(value=None))],
-            ctx=Load())])]),
-       BoolOp(
-        op=And(),
-        values=[
+            ctx=Load())]),
-            ctx=Load())])]),
-       BoolOp(
-        op=And(),
-        values=[
+            ctx=Load())]),
+            ctx=Load())]),
...(截断)
```

**`CFGBuilder._split_block_at_offset`**（源 L327 ↔ 产物 L213）

```diff
-       value=Name(id='block', ctx=Load())),
-      Break()],
+       value=Name(id='block', ctx=Load()))],
-    Return()],
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='split_idx', ctx=Store())],
-   value=Constant(value=None)),
-  For(
-   target=Tuple(
-    elts=[
-     Name(id='i', ctx=Store()),
-     Name(id='instr', ctx=Store())],
...(截断)
```

**`CFGBuilder._r4g_stack_delta`**（源 L420 ↔ 产物 L257）

```diff
+  Assign(
+   targets=[
+    Name(id='arg', ctx=Store())],
+   value=BoolOp(
+    op=Or(),
+    values=[
+     Attribute(
+      value=Name(id='instr', ctx=Load()),
+      attr='arg',
+      ctx=Load()),
+     Constant(value=0)])),
-   orelse=[]),
-  If(
-   test=Compare(
...(截断)
```

**`CFGBuilder._r4g_split_merge_target`**（源 L478 ↔ 产物 L312）

```diff
-    Return()],
+    Return(
+     value=Constant(value=None))],
-    Return()],
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='consumer', ctx=Store())],
-   value=Subscript(
-    value=Name(id='instrs', ctx=Load()),
-    slice=Name(id='consume_idx', ctx=Load()),
-    ctx=Load())),
-  If(
-   test=Compare(
...(截断)
```

**`CFGPrinter.print_cfg`**（源 L607 ↔ 产物 L413）

```diff
-        value=BinOp(
-         left=Constant(value='='),
-         op=Mult(),
-         right=Constant(value=60)),
+        value=Constant(value='============================================================'),
-        value=BinOp(
-         left=Constant(value='='),
-         op=Mult(),
-         right=Constant(value=60)),
+        value=Constant(value='============================================================'),
-        value=BinOp(
-         left=Constant(value='='),
-         op=Mult(),
-         right=Constant(value=60)),
...(截断)
```

## `repo_core_fast_stack`（判据 failure）

- 源：`F:\Downloads\pythoncdc-main\core\fast_stack.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\repo_core_fast_stackOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `FastStack` | L12 | L12 | return: 源=20 产物=25；常量数: 源=150 产物=154；仅源常量: 'FastStack'；仅产物常量: 'Stack resized to ' |
| `FastStack.swap` | L274 | L236 | 常量数: 源=10 产物=11 |
| `StackHistory` | L433 | L345 | 常量数: 源=11 产物=10 |
| `DebugStack` | L512 | L414 | 常量数: 源=26 产物=25 |

### AST 结构差分（源 vs 产物）

**`FastStack`**（源 L12 ↔ 产物 L12）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_stack',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='List', ctx=Load()),
-      slice=Name(id='Any', ctx=Load()),
-      ctx=Load()),
+    Assign(
...(截断)
```

**`FastStack.swap`**（源 L274 ↔ 产物 L236）

```diff
-    Return()],
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Call(
-     func=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='size',
-      ctx=Load()),
-     args=[],
-     keywords=[]),
-    ops=[
-     Lt()],
-    comparators=[
...(截断)
```

**`StackHistory`**（源 L433 ↔ 产物 L345）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_history',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='List', ctx=Load()),
-      slice=Name(id='FastStack', ctx=Load()),
-      ctx=Load()),
-     value=List(elts=[], ctx=Load()),
...(截断)
```

**`DebugStack`**（源 L512 ↔ 产物 L414）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_operation_history',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='List', ctx=Load()),
-      slice=Name(id='StackOperation', ctx=Load()),
-      ctx=Load()),
-     value=List(elts=[], ctx=Load()),
...(截断)
```

## `repo_tools_syntax_cov`（判据 failure）

- 源：`F:\Downloads\pythoncdc-main\tools\kb\syntax_coverage.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\repo_tools_syntax_covOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `main` | L79 | L42 | fstring: 源=0 产物=2；常量数: 源=260 产物=262；仅源常量: '  %-26s %s', 'BUILD_SLICE', 'BinOp'；仅产物常量: ' ', '26' |

### AST 结构差分（源 vs 产物）

**`main`**（源 L79 ↔ 产物 L42）

```diff
-     Constant(value='mod'),
-     Constant(value='stmt'),
+     Constant(value='boolop'),
+     Constant(value='cmpop'),
-     Constant(value='boolop'),
+     Constant(value='mod'),
-     Constant(value='unaryop'),
-     Constant(value='cmpop'),
+     Constant(value='pattern'),
+     Constant(value='slice'),
+     Constant(value='stmt'),
-     Constant(value='pattern'),
+     Constant(value='type_param'),
-     Constant(value='type_param'),
...(截断)
```

## `sp_anyio_fileio`（判据 failure）

- 源：`D:\Python\Lib\site-packages\anyio\_core\_fileio.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_anyio_fileioOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `AsyncFile` | L38 | L20 | return: 源=15 产物=19；常量数: 源=18 产物=10；仅源常量: Ellipsis |
| `AsyncFile.__aiter__` | L81 | L59 | returns_ann: 源=1 产物=0 |
| `_PathIterator` | L205 | L130 | 仅产物常量: 'Iterator[PathLike[str]]' |
| `_PathIterator.__anext__` | L208 | L132 | returns_ann: 源=1 产物=0；常量数: 源=4 产物=3 |
| `Path` | L218 | L136 | await: 源=42 产物=41；break: 源=0 产物=1；return: 源=83 产物=86；常量数: 源=138 产物=109；仅源常量: 438；仅产物常量: 'Any', 'ClassVar[ModuleType]' |
| `Path.iterdir` | L580 | L375 | await: 源=1 产物=0；returns_ann: 源=1 产物=0；常量数: 源=3 产物=2；仅源常量: True |
| `Path.walk` | L751 | L462 | ann_args: 源=3 产物=0；break: 源=0 产物=1；return: 源=3 产物=2；returns_ann: 源=1 产物=0；常量数: 源=8 产物=5 |

### AST 结构差分（源 vs 产物）

**`AsyncFile`**（源 L38 ↔ 产物 L20）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-     arg(
-      arg='fp',
-      annotation=Subscript(
-       value=Name(id='IO', ctx=Load()),
-       slice=Name(id='AnyStr', ctx=Load()),
-       ctx=Load()))],
-    kwonlyargs=[],
-    kw_defaults=[],
-    defaults=[]),
-   body=[
...(截断)
```

**`AsyncFile.__aiter__`**（源 L81 ↔ 产物 L59）

```diff
-    Assign(
-     targets=[
-      Name(id='line', ctx=Store())],
-     value=Await(
+    If(
+     test=Await(
-       keywords=[]))),
-    If(
-     test=Name(id='line', ctx=Load()),
+       keywords=[])),
- decorator_list=[],
- returns=Subscript(
-  value=Name(id='AsyncIterator', ctx=Load()),
-  slice=Name(id='AnyStr', ctx=Load()),
...(截断)
```

**`_PathIterator`**（源 L205 ↔ 产物 L130）

```diff
-   annotation=Subscript(
-    value=Name(id='Iterator', ctx=Load()),
-    slice=Subscript(
-     value=Name(id='PathLike', ctx=Load()),
-     slice=Name(id='str', ctx=Load()),
-     ctx=Load()),
-    ctx=Load()),
+   annotation=Constant(value='Iterator[PathLike[str]]'),
-    Assign(
-     targets=[
-      Name(id='nextval', ctx=Store())],
-     value=Await(
+    If(
+     test=Await(
...(截断)
```

**`_PathIterator.__anext__`**（源 L208 ↔ 产物 L132）

```diff
-  Assign(
-   targets=[
-    Name(id='nextval', ctx=Store())],
-   value=Await(
+  If(
+   test=Await(
-       value=Constant(value=True))]))),
-  If(
-   test=Compare(
-    left=Name(id='nextval', ctx=Load()),
-    ops=[
-     Is()],
-    comparators=[
-     Constant(value=None)]),
...(截断)
```

**`Path`**（源 L218 ↔ 产物 L136）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-  AnnAssign(
-   target=Name(id='__weakref__', ctx=Store()),
-   annotation=Name(id='Any', ctx=Load()),
-   simple=1),
+  Assign(
+   targets=[
+    Subscript(
+     value=Name(id='__annotations__', ctx=Load()),
+     slice=Constant(value='__weakref__'),
+     ctx=Store())],
...(截断)
```

**`Path.iterdir`**（源 L580 ↔ 产物 L375）

```diff
-    orelse=Await(
-     value=Call(
-      func=Attribute(
-       value=Name(id='to_thread', ctx=Load()),
-       attr='run_sync',
-       ctx=Load()),
-      args=[
-       Attribute(
-        value=Attribute(
-         value=Name(id='self', ctx=Load()),
-         attr='_path',
-         ctx=Load()),
-        attr='iterdir',
-        ctx=Load())],
...(截断)
```

**`Path.walk`**（源 L751 ↔ 产物 L462）

```diff
-   arg(
-    arg='top_down',
-    annotation=Name(id='bool', ctx=Load())),
-   arg(
-    arg='on_error',
-    annotation=BinOp(
-     left=Subscript(
-      value=Name(id='Callable', ctx=Load()),
-      slice=Tuple(
-       elts=[
-        List(
-         elts=[
-          Name(id='OSError', ctx=Load())],
-         ctx=Load()),
...(截断)
```

## `sp_anyio_functools`（判据 failure）

- 源：`D:\Python\Lib\site-packages\anyio\functools.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_anyio_functoolsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `AsyncCacheInfo` | L68 | L28 | 常量数: 源=2 产物=5；仅源常量: None；仅产物常量: 'int | None', 'int' |
| `AsyncCacheParameters` | L76 | L34 | 常量数: 源=2 产物=4；仅源常量: None；仅产物常量: 'bool', 'int | None' |
| `_LRUMethodWrapper` | L83 | L39 | 常量数: 源=3 产物=1；仅源常量: Ellipsis |
| `AsyncLRUCacheWrapper` | L105 | L54 | await: 源=3 产物=2；class_body_stmts: 源=6 产物=7；return: 源=6 产物=8；star_args: 源=2 产物=1；常量数: 源=36 产物=34；仅源常量: Ellipsis；仅产物常量: '' |
| `AsyncLRUCacheWrapper.__call__` | L142 | L76 | await: 源=3 产物=2；returns_ann: 源=1 产物=0；star_args: 源=2 产物=1；常量数: 源=18 产物=17；仅源常量: Ellipsis |
| `_LRUCacheWrapper` | L231 | L130 | return: 源=2 产物=4；常量数: 源=6 产物=2；仅源常量: Ellipsis |
| `reduce` | L353 | L197 | ann_args: 源=3 产物=0；params: 源=1 产物=3；posonly: 源=2 产物=0；returns_ann: 源=1 产物=0；常量数: 源=9 产物=8 |

### AST 结构差分（源 vs 产物）

**`AsyncCacheInfo`**（源 L68 ↔ 产物 L28）

```diff
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
-   annotation=BinOp(
-    left=Name(id='int', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='int | None'),
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
-   annotation=BinOp(
-    left=Name(id='int', ctx=Load()),
-    op=BitOr(),
...(截断)
```

**`AsyncCacheParameters`**（源 L76 ↔ 产物 L34）

```diff
-   annotation=BinOp(
-    left=Name(id='int', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='int | None'),
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-   annotation=BinOp(
-    left=Name(id='int', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='int | None'),
...(截断)
```

**`_LRUMethodWrapper`**（源 L83 ↔ 产物 L39）

```diff
-     arg(
-      arg='wrapper',
-      annotation=Subscript(
-       value=Name(id='AsyncLRUCacheWrapper', ctx=Load()),
-       slice=Tuple(
-        elts=[
-         Constant(value=Ellipsis),
-         Name(id='T', ctx=Load())],
-        ctx=Load()),
-       ctx=Load())),
-     arg(
-      arg='instance',
-      annotation=Name(id='object', ctx=Load()))],
+     arg(arg='wrapper'),
...(截断)
```

**`AsyncLRUCacheWrapper`**（源 L105 ↔ 产物 L54）

```diff
-     arg(
-      arg='func',
-      annotation=Subscript(
-       value=Name(id='Callable', ctx=Load()),
-       slice=Tuple(
-        elts=[
-         Name(id='P', ctx=Load()),
-         Subscript(
-          value=Name(id='Awaitable', ctx=Load()),
-          slice=Name(id='T', ctx=Load()),
-          ctx=Load())],
-        ctx=Load()),
-       ctx=Load())),
-     arg(
...(截断)
```

**`AsyncLRUCacheWrapper.__call__`**（源 L142 ↔ 产物 L76）

```diff
-  vararg=arg(
-   arg='args',
-   annotation=Attribute(
-    value=Name(id='P', ctx=Load()),
-    attr='args',
-    ctx=Load())),
+  vararg=arg(arg='args'),
-  kwarg=arg(
-   arg='kwargs',
-   annotation=Attribute(
-    value=Name(id='P', ctx=Load()),
-    attr='kwargs',
-    ctx=Load())),
+  kwarg=arg(arg='kwargs'),
...(截断)
```

**`_LRUCacheWrapper`**（源 L231 ↔ 产物 L130）

```diff
-     arg(
-      arg='maxsize',
-      annotation=BinOp(
-       left=Name(id='int', ctx=Load()),
-       op=BitOr(),
-       right=Constant(value=None))),
-     arg(
-      arg='typed',
-      annotation=Name(id='bool', ctx=Load())),
-     arg(
-      arg='always_checkpoint',
-      annotation=Name(id='bool', ctx=Load())),
-     arg(
-      arg='ttl',
...(截断)
```

**`reduce`**（源 L353 ↔ 产物 L197）

```diff
-  posonlyargs=[
-   arg(
-    arg='function',
-    annotation=BinOp(
-     left=Subscript(
-      value=Name(id='Callable', ctx=Load()),
-      slice=Tuple(
-       elts=[
-        List(
-         elts=[
-          Name(id='T', ctx=Load()),
-          Name(id='T', ctx=Load())],
-         ctx=Load()),
-        Subscript(
...(截断)
```

## `sp_anyio_lowlevel`（判据 failure）

- 源：`D:\Python\Lib\site-packages\anyio\lowlevel.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_anyio_lowlevelOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `EventLoopToken` | L70 | L53 | 常量数: 源=3 产物=5；仅产物常量: 'object', 'type[AsyncBackend]' |
| `RunvarToken` | L104 | L78 | 常量数: 源=8 产物=4；仅源常量: None |
| `RunVar` | L124 | L88 | namedexpr: 源=0 产物=1；return: 源=7 产物=9；仅源常量: Ellipsis；仅产物常量: 'Literal[_NoValueSet.NO_VALUE_SET]' |
| `RunVar.get` | L157 | L114 | ann_args: 源=1 产物=0；returns_ann: 源=1 产物=0 |

### AST 结构差分（源 vs 产物）

**`EventLoopToken`**（源 L70 ↔ 产物 L53）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Subscript(
-    value=Name(id='type', ctx=Load()),
-    slice=Name(id='AsyncBackend', ctx=Load()),
-    ctx=Load()),
+   annotation=Constant(value='type[AsyncBackend]'),
-   annotation=Name(id='object', ctx=Load()),
+   annotation=Constant(value='object'),
```

**`RunvarToken`**（源 L104 ↔ 产物 L78）

```diff
-     arg(
-      arg='var',
-      annotation=Subscript(
-       value=Name(id='RunVar', ctx=Load()),
-       slice=Name(id='T', ctx=Load()),
-       ctx=Load())),
-     arg(
-      arg='value',
-      annotation=BinOp(
-       left=Name(id='T', ctx=Load()),
-       op=BitOr(),
-       right=Subscript(
-        value=Name(id='Literal', ctx=Load()),
-        slice=Attribute(
...(截断)
```

**`RunVar`**（源 L124 ↔ 产物 L88）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Subscript(
-    value=Name(id='Literal', ctx=Load()),
-    slice=Attribute(
-     value=Name(id='_NoValueSet', ctx=Load()),
-     attr='NO_VALUE_SET',
-     ctx=Load()),
-    ctx=Load()),
+   annotation=Constant(value='Literal[_NoValueSet.NO_VALUE_SET]'),
-     arg(
-      arg='name',
...(截断)
```

**`RunVar.get`**（源 L157 ↔ 产物 L114）

```diff
-   arg(
-    arg='default',
-    annotation=BinOp(
-     left=Name(id='D', ctx=Load()),
-     op=BitOr(),
-     right=Subscript(
-      value=Name(id='Literal', ctx=Load()),
-      slice=Attribute(
-       value=Name(id='_NoValueSet', ctx=Load()),
-       attr='NO_VALUE_SET',
-       ctx=Load()),
-      ctx=Load())))],
+   arg(arg='default')],
-         orelse=[])])])],
...(截断)
```

## `sp_anyio_sync`（判据 failure）

- 源：`D:\Python\Lib\site-packages\anyio\_core\_synchronization.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_anyio_syncOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `EventStatistics` | L20 | L18 | 常量数: 源=2 产物=3；仅产物常量: 'int' |
| `CapacityLimiterStatistics` | L29 | L24 | 常量数: 源=3 产物=6；仅源常量: Ellipsis；仅产物常量: 'float', 'int', 'tuple[object, ...]' |
| `LockStatistics` | L47 | L39 | 常量数: 源=3 产物=5；仅源常量: None；仅产物常量: 'TaskInfo | None', 'bool', 'int' |
| `ConditionStatistics` | L61 | L50 | 常量数: 源=2 产物=4；仅产物常量: 'LockStatistics', 'int' |
| `SemaphoreStatistics` | L73 | L59 | 常量数: 源=2 产物=3；仅产物常量: 'int' |
| `Event` | L82 | L65 | 常量数: 源=6 产物=4；仅源常量: None |
| `EventAdapter` | L112 | L89 | return: 源=6 产物=7；仅产物常量: 'Event | None', 'bool' |
| `Lock` | L150 | L119 | 常量数: 源=14 产物=6；仅源常量: None |
| `LockAdapter` | L198 | L153 | return: 源=5 产物=7；常量数: 源=23 产物=17；仅产物常量: 'Lock | None' |
| `Condition` | L262 | L200 | break: 源=1 产物=0；return: 源=3 产物=5；常量数: 源=28 产物=17；仅产物常量: 'TaskInfo | None' |
| `Condition.wait` | L326 | L246 | return: 源=0 产物=1；returns_ann: 源=1 产物=0 |
| `Semaphore` | L373 | L286 | 常量数: 源=26 产物=16 |
| `SemaphoreAdapter` | L457 | L337 | 常量数: 源=17 产物=10；仅产物常量: 'Semaphore | None' |
| `CapacityLimiter` | L516 | L370 | 常量数: 源=22 产物=10；仅源常量: None |
| `CapacityLimiterAdapter` | L632 | L466 | 常量数: 源=27 产物=15；仅产物常量: 'CapacityLimiter | None' |
| `ResourceGuard` | L725 | L527 | 常量数: 源=12 产物=7；仅源常量: None |

### AST 结构差分（源 vs 产物）

**`EventStatistics`**（源 L20 ↔ 产物 L18）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
```

**`CapacityLimiterStatistics`**（源 L29 ↔ 产物 L24）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
-   annotation=Name(id='float', ctx=Load()),
+   annotation=Constant(value='float'),
-   annotation=Subscript(
-    value=Name(id='tuple', ctx=Load()),
-    slice=Tuple(
-     elts=[
-      Name(id='object', ctx=Load()),
-      Constant(value=Ellipsis)],
...(截断)
```

**`LockStatistics`**（源 L47 ↔ 产物 L39）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-   annotation=BinOp(
-    left=Name(id='TaskInfo', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='TaskInfo | None'),
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
```

**`ConditionStatistics`**（源 L61 ↔ 产物 L50）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
-   annotation=Name(id='LockStatistics', ctx=Load()),
+   annotation=Constant(value='LockStatistics'),
```

**`SemaphoreStatistics`**（源 L73 ↔ 产物 L59）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='int', ctx=Load()),
+   annotation=Constant(value='int'),
```

**`Event`**（源 L82 ↔ 产物 L65）

```diff
-   decorator_list=[],
-   returns=Name(id='Event', ctx=Load())),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Constant(value=None)),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Name(id='bool', ctx=Load())),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Constant(value=None)),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Name(id='EventStatistics', ctx=Load()))],
...(截断)
```

**`EventAdapter`**（源 L112 ↔ 产物 L89）

```diff
-   annotation=BinOp(
-    left=Name(id='Event', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='Event | None'),
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-   decorator_list=[],
-   returns=Name(id='EventAdapter', ctx=Load())),
+   decorator_list=[]),
-    Name(id='property', ctx=Load())],
-   returns=Name(id='Event', ctx=Load())),
+    Name(id='property', ctx=Load())]),
-       value=Constant(value=True))],
...(截断)
```

**`Lock`**（源 L150 ↔ 产物 L119）

```diff
-     arg(
-      arg='fast_acquire',
-      annotation=Name(id='bool', ctx=Load()))],
+     arg(arg='fast_acquire')],
-   decorator_list=[],
-   returns=Name(id='Lock', ctx=Load())),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Constant(value=None)),
+   decorator_list=[]),
-     arg(
-      arg='exc_type',
-      annotation=BinOp(
-       left=Subscript(
...(截断)
```

**`LockAdapter`**（源 L198 ↔ 产物 L153）

```diff
-   annotation=BinOp(
-    left=Name(id='Lock', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='Lock | None'),
-     arg(
-      arg='fast_acquire',
-      annotation=Name(id='bool', ctx=Load()))],
+     arg(arg='fast_acquire')],
-   decorator_list=[],
-   returns=Name(id='LockAdapter', ctx=Load())),
+   decorator_list=[]),
-     arg(
-      arg='fast_acquire',
...(截断)
```

**`Condition`**（源 L262 ↔ 产物 L200）

```diff
-   annotation=BinOp(
-    left=Name(id='TaskInfo', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='TaskInfo | None'),
-     arg(
-      arg='lock',
-      annotation=BinOp(
-       left=Name(id='Lock', ctx=Load()),
-       op=BitOr(),
-       right=Constant(value=None)))],
+     arg(arg='lock')],
-    AnnAssign(
-     target=Attribute(
...(截断)
```

**`Condition.wait`**（源 L326 ↔ 产物 L246）

```diff
-         keywords=[])))])])],
- decorator_list=[],
- returns=Constant(value=None))
+         keywords=[]))),
+      Return(
+       value=Constant(value=None))])])],
+ decorator_list=[])
```

**`Semaphore`**（源 L373 ↔ 产物 L286）

```diff
-     arg(
-      arg='initial_value',
-      annotation=Name(id='int', ctx=Load()))],
+     arg(arg='initial_value')],
-     arg(
-      arg='max_value',
-      annotation=BinOp(
-       left=Name(id='int', ctx=Load()),
-       op=BitOr(),
-       right=Constant(value=None))),
-     arg(
-      arg='fast_acquire',
-      annotation=Name(id='bool', ctx=Load()))],
+     arg(arg='max_value'),
...(截断)
```

**`SemaphoreAdapter`**（源 L457 ↔ 产物 L337）

```diff
-   annotation=BinOp(
-    left=Name(id='Semaphore', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='Semaphore | None'),
-     arg(
-      arg='initial_value',
-      annotation=Name(id='int', ctx=Load()))],
+     arg(arg='initial_value')],
-     arg(
-      arg='max_value',
-      annotation=BinOp(
-       left=Name(id='int', ctx=Load()),
-       op=BitOr(),
...(截断)
```

**`CapacityLimiter`**（源 L516 ↔ 产物 L370）

```diff
-     arg(
-      arg='total_tokens',
-      annotation=Name(id='float', ctx=Load()))],
+     arg(arg='total_tokens')],
-   decorator_list=[],
-   returns=Name(id='CapacityLimiter', ctx=Load())),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Constant(value=None)),
+   decorator_list=[]),
-     arg(
-      arg='exc_type',
-      annotation=BinOp(
-       left=Subscript(
...(截断)
```

**`CapacityLimiterAdapter`**（源 L632 ↔ 产物 L466）

```diff
-   annotation=BinOp(
-    left=Name(id='CapacityLimiter', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='CapacityLimiter | None'),
-     arg(
-      arg='total_tokens',
-      annotation=Name(id='float', ctx=Load()))],
+     arg(arg='total_tokens')],
-   decorator_list=[],
-   returns=Name(id='CapacityLimiterAdapter', ctx=Load())),
+   decorator_list=[]),
-     arg(
-      arg='total_tokens',
...(截断)
```

**`ResourceGuard`**（源 L725 ↔ 产物 L527）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-     arg(
-      arg='action',
-      annotation=Name(id='str', ctx=Load()))],
+     arg(arg='action')],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='action',
-      ctx=Store()),
-     annotation=Name(id='str', ctx=Load()),
...(截断)
```

## `sp_httpcore_models`（判据 failure）

- 源：`D:\Python\Lib\site-packages\httpcore\_models.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_httpcore_modelsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `ByteStream` | L142 | L83 | 常量数: 源=5 产物=4；仅源常量: None |
| `Origin` | L161 | L96 | 常量数: 源=5 产物=4；仅源常量: None |
| `URL` | L182 | L108 | boolop: 源=4 产物=3；class_body_stmts: 源=6 产物=7；ternary: 源=1 产物=2；常量数: 源=37 产物=36 |
| `URL.__init__` | L249 | L175 | ann_args: 源=5 产物=0；boolop: 源=2 产物=1；returns_ann: 源=1 产物=0；ternary: 源=1 产物=2；常量数: 源=16 产物=14 |
| `Request` | L316 | L208 | return: 源=1 产物=3；常量数: 源=18 产物=17 |
| `Response` | L366 | L236 | return: 源=4 产物=6；常量数: 源=36 产物=33 |
| `Proxy` | L496 | L306 | return: 源=0 产物=1；常量数: 源=18 产物=15 |

### AST 结构差分（源 vs 产物）

**`ByteStream`**（源 L142 ↔ 产物 L83）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-     arg(
-      arg='content',
-      annotation=Name(id='bytes', ctx=Load()))],
+     arg(arg='content')],
-   decorator_list=[],
-   returns=Constant(value=None)),
+   decorator_list=[]),
-   decorator_list=[],
-   returns=Subscript(
-    value=Attribute(
...(截断)
```

**`Origin`**（源 L161 ↔ 产物 L96）

```diff
-     arg(
-      arg='scheme',
-      annotation=Name(id='bytes', ctx=Load())),
-     arg(
-      arg='host',
-      annotation=Name(id='bytes', ctx=Load())),
-     arg(
-      arg='port',
-      annotation=Name(id='int', ctx=Load()))],
+     arg(arg='scheme'),
+     arg(arg='host'),
+     arg(arg='port')],
-   decorator_list=[],
-   returns=Constant(value=None)),
...(截断)
```

**`URL`**（源 L182 ↔ 产物 L108）

```diff
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
+   value=Constant(value='\n    Represents the URL against which an HTTP request may be made.\n\n    The URL may either be specified as a plain string, for convienence:\n\n    ```python\n    url = httpcore.URL("https://w
-   value=Constant(value='\n    Represents the URL against which an HTTP request may be made.\n\n    The URL may either be specified as a plain string, for convienence:\n\n    ```python\n    url = httpcore.URL("https://w
+   value=Constant(value='')),
-     arg(
-      arg='url',
-      annotation=BinOp(
-       left=Name(id='bytes', ctx=Load()),
-       op=BitOr(),
-       right=Name(id='str', ctx=Load())))],
+     arg(arg='url')],
-     arg(
...(截断)
```

**`URL.__init__`**（源 L249 ↔ 产物 L175）

```diff
-   arg(
-    arg='url',
-    annotation=BinOp(
-     left=Name(id='bytes', ctx=Load()),
-     op=BitOr(),
-     right=Name(id='str', ctx=Load())))],
+   arg(arg='url')],
-   arg(
-    arg='scheme',
-    annotation=BinOp(
-     left=Name(id='bytes', ctx=Load()),
-     op=BitOr(),
-     right=Name(id='str', ctx=Load()))),
-   arg(
...(截断)
```

**`Request`**（源 L316 ↔ 产物 L208）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-     arg(
-      arg='method',
-      annotation=BinOp(
-       left=Name(id='bytes', ctx=Load()),
-       op=BitOr(),
-       right=Name(id='str', ctx=Load()))),
-     arg(
-      arg='url',
-      annotation=BinOp(
-       left=BinOp(
...(截断)
```

**`Response`**（源 L366 ↔ 产物 L236）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-     arg(
-      arg='status',
-      annotation=Name(id='int', ctx=Load()))],
+     arg(arg='status')],
-     arg(
-      arg='headers',
-      annotation=Name(id='HeaderTypes', ctx=Load())),
-     arg(
-      arg='content',
-      annotation=BinOp(
...(截断)
```

**`Proxy`**（源 L496 ↔ 产物 L306）

```diff
-     arg(
-      arg='url',
-      annotation=BinOp(
-       left=BinOp(
-        left=Name(id='URL', ctx=Load()),
-        op=BitOr(),
-        right=Name(id='bytes', ctx=Load())),
-       op=BitOr(),
-       right=Name(id='str', ctx=Load()))),
-     arg(
-      arg='auth',
-      annotation=BinOp(
-       left=Subscript(
-        value=Name(id='tuple', ctx=Load()),
...(截断)
```

## `sp_pandas_indexing`（判据 failure）

- 源：`D:\Python\Lib\site-packages\pandas\core\indexing.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_pandas_indexingOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `IndexingMixin` | L154 | L80 | （指纹一致） |
| `_LocationIndexer` | L753 | L673 | boolop: 源=16 产物=14；comprehension: 源=12 产物=11；continue: 源=2 产物=3；常量数: 源=90 产物=88；仅产物常量: 'AxisInt | None', 'bool', 'str' |
| `_LocationIndexer._getitem_lowerdim` | L1059 | L885 | ann_args: 源=1 产物=0；comprehension: 源=1 产物=0 |
| `_LocationIndexer._getitem_lowerdim.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_LocationIndexer._getitem_nested_tuple` | L1122 | L912 | ann_args: 源=1 产物=0；boolop: 源=4 产物=2；continue: 源=1 产物=2；常量数: 源=9 产物=7；仅源常量: 0, False |
| `_LocationIndexer._getitem_nested_tuple.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_LocIndexer` | L1231 | L974 | continue: 源=0 产物=1；return: 源=34 产物=35；常量数: 源=44 产物=45；仅源常量: True；仅产物常量: 'bool' |
| `_LocIndexer._getitem_axis` | L1415 | L1094 | ann_args: 源=1 产物=0；boolop: 源=3 产物=4 |
| `_LocIndexer._convert_to_indexer` | L1470 | L1133 | ann_args: 源=1 产物=0；return: 源=9 产物=10；常量数: 源=12 产物=13；仅产物常量: None |
| `_iLocIndexer` | L1582 | L1221 | boolop: 源=46 产物=42；continue: 源=1 产物=9；return: 源=43 产物=57；常量数: 源=171 产物=187 |
| `_iLocIndexer._validate_key` | L1592 | L1224 | ann_args: 源=1 产物=0；return: 源=3 产物=6；returns_ann: 源=1 产物=0；常量数: 源=11 产物=16 |
| `_iLocIndexer._setitem_new_column` | L1839 | L1406 | ann_args: 源=1 产物=0；return: 源=4 产物=3；returns_ann: 源=1 产物=0；常量数: 源=11 产物=13；仅源常量: Ellipsis |
| `_iLocIndexer._setitem_with_indexer_split_path` | L1957 | L1478 | ann_args: 源=1 产物=0；boolop: 源=10 产物=9；return: 源=1 产物=8；常量数: 源=30 产物=37；仅产物常量: None |
| `_iLocIndexer._setitem_single_column` | L2122 | L1569 | ann_args: 源=1 产物=0；boolop: 源=4 产物=2；return: 源=1 产物=3；returns_ann: 源=1 产物=0；常量数: 源=7 产物=8；仅源常量: 0 |
| `_iLocIndexer._setitem_single_block` | L2183 | L1598 | ann_args: 源=1 产物=0；returns_ann: 源=1 产物=0 |
| `_iLocIndexer._align_series` | L2339 | L1691 | ann_args: 源=3 产物=0；boolop: 源=9 产物=8 |
| `_iLocIndexer._align_series.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_ScalarAccessIndexer` | L2507 | L1807 | 仅源常量: None；仅产物常量: 'bool' |
| `_AtIndexer` | L2546 | L1834 | boolop: 源=6 产物=7 |
| `_iAtIndexer` | L2596 | L1864 | boolop: 源=0 产物=1；常量数: 源=5 产物=4；仅源常量: None |
| `check_dict_or_set_indexers` | L2780 | L1995 | boolop: 源=4 产物=3；return: 源=0 产物=1；returns_ann: 源=1 产物=0 |

### AST 结构差分（源 vs 产物）

**`IndexingMixin`**（源 L154 ↔ 产物 L80）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    Name(id='property', ctx=Load())],
-   returns=Name(id='_iLocIndexer', ctx=Load())),
+    Name(id='property', ctx=Load())]),
-    Name(id='property', ctx=Load())],
-   returns=Name(id='_LocIndexer', ctx=Load())),
+    Name(id='property', ctx=Load())]),
-    Name(id='property', ctx=Load())],
-   returns=Name(id='_AtIndexer', ctx=Load())),
+    Name(id='property', ctx=Load())]),
-    Name(id='property', ctx=Load())],
...(截断)
```

**`_LocationIndexer`**（源 L753 ↔ 产物 L673）

```diff
-   annotation=Name(id='str', ctx=Load()),
+   annotation=Constant(value='str'),
-   annotation=BinOp(
-    left=Name(id='AxisInt', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='AxisInt | None'),
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-     arg(
-      arg='axis',
-      annotation=BinOp(
-       left=Name(id='Axis', ctx=Load()),
-       op=BitOr(),
...(截断)
```

**`_LocationIndexer._getitem_lowerdim`**（源 L1059 ↔ 产物 L885）

```diff
-   arg(
-    arg='tup',
-    annotation=Name(id='tuple', ctx=Load()))],
+   arg(arg='tup')],
-   orelse=[]),
-  If(
-   test=Call(
-    func=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_is_nested_tuple_indexer',
-     ctx=Load()),
-    args=[
-     Name(id='tup', ctx=Load())],
-    keywords=[]),
...(截断)
```

**`_LocationIndexer._getitem_nested_tuple`**（源 L1122 ↔ 产物 L912）

```diff
-   arg(
-    arg='tup',
-    annotation=Name(id='tuple', ctx=Load()))],
+   arg(arg='tup')],
-     orelse=[]),
-    If(
-     test=Call(
-      func=Name(id='all', ctx=Load()),
-      args=[
-       GeneratorExp(
-        elt=BoolOp(
-         op=Or(),
-         values=[
-          Call(
...(截断)
```

**`_LocIndexer`**（源 L1231 ↔ 产物 L974）

```diff
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-     arg(
-      arg='axis',
-      annotation=Name(id='Axis', ctx=Load()))],
+     arg(arg='axis')],
-     test=BoolOp(
-      op=And(),
-      values=[
-       Call(
-        func=Name(id='isinstance', ctx=Load()),
-        args=[
-         Name(id='key', ctx=Load()),
-         Name(id='slice', ctx=Load())],
...(截断)
```

**`_LocIndexer._getitem_axis`**（源 L1415 ↔ 产物 L1094）

```diff
-   arg(
-    arg='axis',
-    annotation=Name(id='AxisInt', ctx=Load()))],
+   arg(arg='axis')],
-         test=UnaryOp(
-          op=Not(),
-          operand=BoolOp(
-           op=And(),
-           values=[
-            Call(
-             func=Name(id='isinstance', ctx=Load()),
-             args=[
-              Name(id='key', ctx=Load()),
-              Name(id='tuple', ctx=Load())],
...(截断)
```

**`_LocIndexer._convert_to_indexer`**（源 L1470 ↔ 产物 L1133）

```diff
-   arg(
-    arg='axis',
-    annotation=Name(id='AxisInt', ctx=Load()))],
+   arg(arg='axis')],
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Call(
-      func=Name(id='isinstance', ctx=Load()),
-      args=[
-       Name(id='key', ctx=Load()),
-       Name(id='tuple', ctx=Load())],
...(截断)
```

**`_iLocIndexer`**（源 L1582 ↔ 产物 L1221）

```diff
-     arg(
-      arg='axis',
-      annotation=Name(id='AxisInt', ctx=Load()))],
+     arg(arg='axis')],
+      Return(
+       value=Constant(value=None)),
-          Return()],
-         orelse=[]),
-        Raise(
-         exc=Call(
-          func=Name(id='ValueError', ctx=Load()),
-          args=[
-           Constant(value='iLocation based boolean indexing cannot use an indexable as a mask')],
-          keywords=[]))],
...(截断)
```

**`_iLocIndexer._validate_key`**（源 L1592 ↔ 产物 L1224）

```diff
-   arg(
-    arg='axis',
-    annotation=Name(id='AxisInt', ctx=Load()))],
+   arg(arg='axis')],
+    Return(
+     value=Constant(value=None)),
-        Return()],
-       orelse=[]),
-      Raise(
-       exc=Call(
-        func=Name(id='ValueError', ctx=Load()),
-        args=[
-         Constant(value='iLocation based boolean indexing cannot use an indexable as a mask')],
-        keywords=[]))],
...(截断)
```

**`_iLocIndexer._setitem_new_column`**（源 L1839 ↔ 产物 L1406）

```diff
-   arg(
-    arg='name',
-    annotation=Name(id='str', ctx=Load()))],
+   arg(arg='name')],
-    Return()],
-   orelse=[]),
-  If(
-   test=Call(
-    func=Attribute(
-     value=Name(id='com', ctx=Load()),
-     attr='is_null_slice',
-     ctx=Load()),
-    args=[
-     Subscript(
...(截断)
```

**`_iLocIndexer._setitem_with_indexer_split_path`**（源 L1957 ↔ 产物 L1478）

```diff
-   arg(
-    arg='name',
-    annotation=Name(id='str', ctx=Load()))],
+   arg(arg='name')],
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Call(
-      func=Name(id='isinstance', ctx=Load()),
-      args=[
-       Subscript(
-        value=Name(id='indexer', ctx=Load()),
...(截断)
```

**`_iLocIndexer._setitem_single_column`**（源 L2122 ↔ 产物 L1569）

```diff
-   arg(
-    arg='loc',
-    annotation=Name(id='int', ctx=Load())),
+   arg(arg='loc'),
-  Assign(
-   targets=[
-    Name(id='is_null_setter', ctx=Store())],
-   value=BoolOp(
-    op=Or(),
-    values=[
-     Call(
-      func=Attribute(
-       value=Name(id='com', ctx=Load()),
-       attr='is_empty_slice',
...(截断)
```

**`_iLocIndexer._setitem_single_block`**（源 L2183 ↔ 产物 L1598）

```diff
-   arg(
-    arg='name',
-    annotation=Name(id='str', ctx=Load()))],
+   arg(arg='name')],
-     test=BoolOp(
-      op=And(),
-      values=[
-       Compare(
-        left=Attribute(
-         value=Name(id='self', ctx=Load()),
-         attr='ndim',
-         ctx=Load()),
-        ops=[
-         Eq(),
...(截断)
```

**`_iLocIndexer._align_series`**（源 L2339 ↔ 产物 L1691）

```diff
-   arg(
-    arg='ser',
-    annotation=Name(id='Series', ctx=Load())),
-   arg(
-    arg='multiindex_indexer',
-    annotation=Name(id='bool', ctx=Load())),
-   arg(
-    arg='using_cow',
-    annotation=Name(id='bool', ctx=Load()))],
+   arg(arg='ser'),
+   arg(arg='multiindex_indexer'),
+   arg(arg='using_cow')],
-    If(
-     test=BoolOp(
...(截断)
```

**`_ScalarAccessIndexer`**（源 L2507 ↔ 产物 L1807）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-   annotation=Name(id='bool', ctx=Load()),
+   annotation=Constant(value='bool'),
-   decorator_list=[],
-   returns=Constant(value=None))],
+   decorator_list=[])],
```

**`_AtIndexer`**（源 L2546 ↔ 产物 L1834）

```diff
-    Name(id='property', ctx=Load())],
-   returns=Name(id='bool', ctx=Load())),
+    Name(id='property', ctx=Load())]),
-       test=BoolOp(
-        op=Or(),
-        values=[
-         UnaryOp(
-          op=Not(),
-          operand=Call(
+       test=UnaryOp(
+        op=Not(),
+        operand=BoolOp(
+         op=And(),
+         values=[
...(截断)
```

**`_iAtIndexer`**（源 L2596 ↔ 产物 L1864）

```diff
-     test=UnaryOp(
-      op=Not(),
-      operand=Name(id='CHAINED_WARNING_DISABLED', ctx=Load())),
-     body=[
-      If(
-       test=Compare(
+     test=BoolOp(
+      op=And(),
+      values=[
+       UnaryOp(
+        op=Not(),
+        operand=Name(id='CHAINED_WARNING_DISABLED', ctx=Load())),
+       Compare(
-         Name(id='REF_COUNT_IDX', ctx=Load())]),
...(截断)
```

**`check_dict_or_set_indexers`**（源 L2780 ↔ 产物 L1995）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=Or(),
-    values=[
-     Call(
-      func=Name(id='isinstance', ctx=Load()),
-      args=[
-       Name(id='key', ctx=Load()),
-       Name(id='dict', ctx=Load())],
-      keywords=[]),
-     BoolOp(
-      op=And(),
+   orelse=[
...(截断)
```

## `sp_starlette_formparsers`（判据 failure）

- 源：`D:\Python\Lib\site-packages\starlette\formparsers.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\sp_starlette_formparsersOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `MultipartPart` | L37 | L33 | 常量数: 源=5 产物=8；仅产物常量: 'UploadFile | None', 'bytearray', 'bytes | None', 'list[tuple[bytes, bytes]]', 'str' |
| `MultiPartException` | L52 | L44 | 常量数: 源=1 产物=0；仅源常量: None |
| `FormParser` | L57 | L47 | continue: 源=0 产物=3；常量数: 源=19 产物=12 |
| `MultiPartParser` | L125 | L97 | return: 源=1 产物=5；常量数: 源=62 产物=53；仅源常量: 'The maximum size of a part in the multipart request.', 'The maximum size of the spooled temporary file used to store file data.'；仅产物常量: 1048576 |

### AST 结构差分（源 vs 产物）

**`MultipartPart`**（源 L37 ↔ 产物 L33）

```diff
-   annotation=BinOp(
-    left=Name(id='bytes', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='bytes | None'),
-   annotation=Name(id='str', ctx=Load()),
+   annotation=Constant(value='str'),
-   annotation=Name(id='bytearray', ctx=Load()),
+   annotation=Constant(value='bytearray'),
-   annotation=BinOp(
-    left=Name(id='UploadFile', ctx=Load()),
-    op=BitOr(),
-    right=Constant(value=None)),
+   annotation=Constant(value='UploadFile | None'),
...(截断)
```

**`MultiPartException`**（源 L52 ↔ 产物 L44）

```diff
-     arg(
-      arg='message',
-      annotation=Name(id='str', ctx=Load()))],
+     arg(arg='message')],
-   decorator_list=[],
-   returns=Constant(value=None))],
+   decorator_list=[])],
```

**`FormParser`**（源 L57 ↔ 产物 L47）

```diff
-     arg(
-      arg='headers',
-      annotation=Name(id='Headers', ctx=Load())),
-     arg(
-      arg='stream',
-      annotation=Subscript(
-       value=Name(id='AsyncGenerator', ctx=Load()),
-       slice=Tuple(
-        elts=[
-         Name(id='bytes', ctx=Load()),
-         Constant(value=None)],
-        ctx=Load()),
-       ctx=Load()))],
+     arg(arg='headers'),
...(截断)
```

**`MultiPartParser`**（源 L125 ↔ 产物 L97）

```diff
-   value=BinOp(
-    left=Constant(value=1024),
-    op=Mult(),
-    right=Constant(value=1024))),
+   value=Constant(value=1048576)),
-   value=Constant(value='The maximum size of the spooled temporary file used to store file data.')),
+   value=Constant(value='')),
-   value=BinOp(
-    left=Constant(value=1024),
-    op=Mult(),
-    right=Constant(value=1024))),
+   value=Constant(value=1048576)),
-   value=Constant(value='The maximum size of a part in the multipart request.')),
+   value=Constant(value='')),
...(截断)
```

## `stdlib_argparse`（判据 failure）

- 源：`D:\Python\Lib\argparse.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_argparseOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `HelpFormatter._format_actions_usage` | L393 | L286 | continue: 源=1 产物=4；fstring: 源=1 产物=3；仅源常量: '%s %s', '%s *%s'；仅产物常量: ' *' |
| `HelpFormatter._iter_indented_subactions` | L642 | L477 | return: 源=0 产物=2；常量数: 源=0 产物=2；仅产物常量: None |
| `_ActionsContainer.add_argument` | L1419 | L891 | boolop: 源=3 产物=2；fstring: 源=0 产物=3；常量数: 源=18 产物=19；仅源常量: '%r is a FileType class object, instance of it must be passed', '%r is not callable', 'unknown action "%s"'；仅产物常量: ' is a FileType class object, instance of it must be passed', ' is not callable', '"', 'unknown action "' |
| `ArgumentParser.__init__` | L1737 | L1092 | （指纹一致） |
| `ArgumentParser._parse_known_args` | L1913 | L1185 | assert: 源=1 产物=0；continue: 源=1 产物=3；return: 源=4 产物=6；常量数: 源=35 产物=36 |
| `ArgumentParser._parse_known_args.consume_optional` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `ArgumentParser.parse_known_intermixed_args` | L2388 | L1454 | fstring: 源=0 产物=1；常量数: 源=10 产物=11；仅源常量: 'Do not expect %s in %s'；仅产物常量: ' in ', 'Do not expect ' |

### AST 结构差分（源 vs 产物）

**`HelpFormatter._format_actions_usage`**（源 L393 ↔ 产物 L286）

```diff
-        Continue()])],
+        Pass()])],
-             value=Constant(value=']'))],
+             value=Constant(value=']')),
+            For(
+             target=Name(id='i', ctx=Store()),
+             iter=Call(
+              func=Name(id='range', ctx=Load()),
+              args=[
+               BinOp(
+                left=Name(id='start', ctx=Load()),
+                op=Add(),
+                right=Constant(value=1)),
+               Name(id='end', ctx=Load())],
...(截断)
```

**`HelpFormatter._iter_indented_subactions`**（源 L642 ↔ 产物 L477）

```diff
-      Pass()])],
+      Return(
+       value=Constant(value=None))])],
-     value=YieldFrom(
-      value=Call(
-       func=Name(id='get_subactions', ctx=Load()),
-       args=[],
-       keywords=[]))),
-    Expr(
-      keywords=[]))],
+      keywords=[])),
+    Return(
+     value=Constant(value=None))],
```

**`_ActionsContainer.add_argument`**（源 L1419 ↔ 产物 L891）

```diff
-   test=BoolOp(
-    op=Or(),
-    values=[
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='args', ctx=Load())),
-     BoolOp(
+   test=Name(id='args', ctx=Load()),
+   body=[
+    If(
+     test=BoolOp(
-         Name(id='chars', ctx=Load())])])]),
-   body=[
-    If(
...(截断)
```

**`ArgumentParser.__init__`**（源 L1737 ↔ 产物 L1092）

```diff
-     orelse=[
-      Expr(
-       value=Call(
-        func=Attribute(
-         value=Attribute(
-          value=Name(id='self', ctx=Load()),
-          attr='_defaults',
-          ctx=Load()),
-         attr='update',
-         ctx=Load()),
-        args=[
-         Name(id='defaults', ctx=Load())],
-        keywords=[]))],
-     finalbody=[])],
...(截断)
```

**`ArgumentParser._parse_known_args`**（源 L1913 ↔ 产物 L1185）

```diff
-       orelse=[])],
+       orelse=[]),
+      Continue()],
+     orelse=[]),
+    Assign(
+     targets=[
+      Name(id='option_tuple', ctx=Store())],
+     value=Call(
+      func=Attribute(
+       value=Name(id='self', ctx=Load()),
+       attr='_parse_optional',
+       ctx=Load()),
+      args=[
+       Name(id='arg_string', ctx=Load())],
...(截断)
```

**`ArgumentParser.parse_known_intermixed_args`**（源 L2388 ↔ 产物 L1454）

```diff
-         List(
+         Tuple(
-   orelse=[]),
-  If(
-   test=ListComp(
-    elt=Attribute(
-     value=Name(id='action', ctx=Load()),
-     attr='dest',
-     ctx=Load()),
-    generators=[
-     comprehension(
-      target=Name(id='group', ctx=Store()),
-      iter=Attribute(
-       value=Name(id='self', ctx=Load()),
...(截断)
```

## `stdlib_ast`（判据 failure）

- 源：`D:\Python\Lib\ast.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_astOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `literal_eval._convert` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `dump._format` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `NodeVisitor.visit_Constant` | L430 | L394 | （指纹一致） |
| `Ellipsis.__new__` | L576 | L516 | 仅源常量: Ellipsis；仅产物常量: None |
| `_Unparser.visit_ImportFrom` | L861 | L732 | （指纹一致） |
| `_Unparser.visit_AnnAssign` | L885 | L757 | return: 源=0 产物=1；常量数: 源=4 产物=3；仅源常量: '(', ')'；仅产物常量: None |
| `_Unparser.visit_ExceptHandler` | L996 | L867 | return: 源=0 产物=1；ternary: 源=1 产物=0；常量数: 源=4 产物=3；仅源常量: 'except', 'except*'；仅产物常量: None |
| `_Unparser.visit_ClassDef` | L1007 | L877 | 常量数: 源=9 产物=7；仅源常量: '(', ')' |
| `_Unparser.visit_If` | L1071 | L934 | boolop: 源=1 产物=2；continue: 源=0 产物=1；常量数: 源=6 产物=8 |
| `_Unparser._str_literal_helper` | L1111 | L974 | boolop: 源=2 产物=3；lambda: 源=1 产物=0；常量数: 源=22 产物=20 |
| `_Unparser._str_literal_helper.<lambda>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_Unparser.visit_JoinedStr` | L1155 | L1005 | return: 源=1 产物=2；常量数: 源=11 产物=10；仅源常量: '"', '\'"'；仅产物常量: None |
| `_Unparser.visit_Constant` | L1264 | L1084 | return: 源=0 产物=2；常量数: 源=6 产物=8；仅源常量: Ellipsis；仅产物常量: None |
| `_Unparser.visit_Tuple` | L1361 | L1173 | return: 源=0 产物=1；常量数: 源=3 产物=2；仅源常量: '(', ')'；仅产物常量: None |

### AST 结构差分（源 vs 产物）

**`NodeVisitor.visit_Constant`**（源 L430 ↔ 产物 L394）

```diff
-        keywords=[]))],
-     handlers=[
-      ExceptHandler(
-       type=Name(id='AttributeError', ctx=Load()),
-       body=[
-        Pass()])],
-     orelse=[
+        keywords=[])),
+     handlers=[
+      ExceptHandler(
+       type=Name(id='AttributeError', ctx=Load()),
+       body=[
+        Pass()])],
+     orelse=[],
...(截断)
```

**`Ellipsis.__new__`**（源 L576 ↔ 产物 L516）

```diff
-       Constant(value=Ellipsis),
+       Constant(value=None),
-   orelse=[]),
-  Return(
-   value=Call(
-    func=Attribute(
-     value=Name(id='Constant', ctx=Load()),
-     attr='__new__',
-     ctx=Load()),
-    args=[
-     Name(id='cls', ctx=Load()),
-     Starred(
-      value=Name(id='args', ctx=Load()),
-      ctx=Load())],
...(截断)
```

**`_Unparser.visit_ImportFrom`**（源 L861 ↔ 产物 L732）

```diff
-   orelse=[]),
-  Expr(
-   value=Call(
-    func=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='write',
-     ctx=Load()),
-    args=[
-     Constant(value=' import ')],
-    keywords=[])),
-  Expr(
-   value=Call(
-    func=Attribute(
-     value=Name(id='self', ctx=Load()),
...(截断)
```

**`_Unparser.visit_AnnAssign`**（源 L885 ↔ 产物 L757）

```diff
+  Expr(
+   value=BoolOp(
+    op=And(),
+    values=[
+     UnaryOp(
+      op=Not(),
+      operand=Attribute(
+       value=Name(id='node', ctx=Load()),
+       attr='simple',
+       ctx=Load())),
+     Call(
+      func=Name(id='isinstance', ctx=Load()),
+      args=[
+       Attribute(
...(截断)
```

**`_Unparser.visit_ExceptHandler`**（源 L996 ↔ 产物 L867）

```diff
-  Expr(
-   value=Call(
-    func=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='fill',
-     ctx=Load()),
-    args=[
-     IfExp(
-      test=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='_in_try_star',
-       ctx=Load()),
-      body=Constant(value='except*'),
-      orelse=Constant(value='except'))],
...(截断)
```

**`_Unparser.visit_ClassDef`**（源 L1007 ↔ 产物 L877）

```diff
+  Expr(
+   value=BoolOp(
+    op=Or(),
+    values=[
+     Attribute(
+      value=Name(id='node', ctx=Load()),
+      attr='bases',
+      ctx=Load()),
+     Attribute(
+      value=Name(id='node', ctx=Load()),
+      attr='keywords',
+      ctx=Load())])),
-      func=Attribute(
-       value=Name(id='self', ctx=Load()),
...(截断)
```

**`_Unparser.visit_If`**（源 L1071 ↔ 产物 L934）

```diff
-  While(
+  If(
-       Constant(value=1)]),
-     Call(
+       Constant(value=1)])]),
+   body=[
+    While(
+     test=Call(
-      keywords=[])]),
-   body=[
-    Assign(
-     targets=[
-      Name(id='node', ctx=Store())],
-     value=Subscript(
...(截断)
```

**`_Unparser._str_literal_helper`**（源 L1111 ↔ 产物 L974）

```diff
-     orelse=[]),
-    Return(
-     value=Name(id='c', ctx=Load()))],
+     orelse=[
+      Return(
+       value=Name(id='c', ctx=Load()))])],
-   orelse=[]),
-  If(
-   test=Name(id='escaped_string', ctx=Load()),
-   body=[
-    Expr(
-     value=Call(
-      func=Attribute(
-       value=Name(id='possible_quotes', ctx=Load()),
...(截断)
```

**`_Unparser.visit_JoinedStr`**（源 L1155 ↔ 产物 L1005）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='fstring_parts', ctx=Store())],
-   value=List(elts=[], ctx=Load())),
-  For(
-   target=Name(id='value', ctx=Store()),
-   iter=Attribute(
-    value=Name(id='node', ctx=Load()),
-    attr='values',
-    ctx=Load()),
-   body=[
-    With(
-     items=[
...(截断)
```

**`_Unparser.visit_Constant`**（源 L1264 ↔ 产物 L1084）

```diff
-        keywords=[]))])],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))])],
-       Constant(value=Ellipsis)]),
+       Constant(value=None)]),
-        keywords=[]))],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))],
-       orelse=[]),
-      Expr(
-       value=Call(
-        func=Attribute(
...(截断)
```

**`_Unparser.visit_Tuple`**（源 L1361 ↔ 产物 L1173）

```diff
+  Expr(
+   value=BoolOp(
+    op=Or(),
+    values=[
+     Compare(
+      left=Call(
+       func=Name(id='len', ctx=Load()),
+       args=[
+        Attribute(
+         value=Name(id='node', ctx=Load()),
+         attr='elts',
+         ctx=Load())],
+       keywords=[]),
+      ops=[
...(截断)
```

## `stdlib_asyncio_base_events`（判据 failure）

- 源：`D:\Python\Lib\asyncio\base_events.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_asyncio_base_eventsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `Server` | L274 | L209 | boolop: 源=3 产物=1；class_body_stmts: 源=13 产物=14；return: 源=8 产物=11；常量数: 源=32 产物=39；仅产物常量: '' |
| `Server.wait_closed` | L379 | L297 | boolop: 源=1 产物=0；常量数: 源=2 产物=3 |
| `BaseEventLoop.shutdown_asyncgens` | L539 | L412 | await: 源=1 产物=0；comprehension: 源=1 产物=0；star_args: 源=1 产物=0；仅产物常量: None |
| `BaseEventLoop.shutdown_asyncgens.<listcomp>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `BaseEventLoop.run_until_complete` | L617 | L469 | boolop: 源=1 产物=0 |
| `BaseEventLoop.close` | L663 | L508 | return: 源=1 产物=3；常量数: 源=8 产物=11 |
| `BaseEventLoop._sock_sendfile_fallback` | L896 | L703 | await: 源=2 产物=1；break: 源=2 产物=3；slice: 源=2 产物=0；while: 源=1 产物=2；常量数: 源=6 产物=7；仅产物常量: False |
| `BaseEventLoop._connect_sock` | L943 | L738 | return: 源=1 产物=0；常量数: 源=12 产物=13 |
| `BaseEventLoop.create_connection` | L987 | L780 | break: 源=1 产物=0；continue: 源=1 产物=0 |
| `BaseEventLoop.sendfile` | L1152 | L861 | （指纹一致） |
| `BaseEventLoop._sendfile_fallback` | L1203 | L900 | augassign: 源=1 产物=0；await: 源=3 产物=4；boolop: 源=1 产物=2；break: 源=0 产物=1；return: 源=2 产物=0；slice: 源=2 产物=0；while: 源=1 产物=2；常量数: 源=8 产物=13；仅产物常量: False |
| `BaseEventLoop.create_datagram_endpoint` | L1276 | L957 | boolop: 源=9 产物=7；break: 源=1 产物=3；continue: 源=0 产物=1 |
| `BaseEventLoop.create_datagram_endpoint.<listcomp>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `BaseEventLoop._create_server_getaddrinfo` | L1422 | L1060 | （指纹一致） |
| `BaseEventLoop.create_server` | L1430 | L1065 | fstring: 源=1 产物=2；常量数: 源=43 产物=44；仅源常量: 'error while attempting to bind on address %r: %s'；仅产物常量: ': ', 'error while attempting to bind on address ' |
| `BaseEventLoop.connect_accepted_socket` | L1556 | L1147 | （指纹一致） |
| `BaseEventLoop.subprocess_shell` | L1631 | L1197 | await: 源=1 产物=0；常量数: 源=21 产物=20 |
| `BaseEventLoop.subprocess_exec` | L1667 | L1221 | await: 源=1 产物=0；常量数: 源=20 产物=19 |
| `BaseEventLoop.call_exception_handler` | L1773 | L1308 | return: 源=0 产物=5；常量数: 源=10 产物=15 |
| `BaseEventLoop._run_once` | L1845 | L1371 | continue: 源=1 产物=4；return: 源=0 产物=1 |

### AST 结构差分（源 vs 产物）

**`Server`**（源 L274 ↔ 产物 L209）

```diff
+  Expr(
+   value=Constant(value='')),
-     test=BoolOp(
-      op=And(),
-      values=[
-       Compare(
-        left=Attribute(
-         value=Name(id='self', ctx=Load()),
-         attr='_active_count',
-         ctx=Load()),
-        ops=[
-         Eq()],
-        comparators=[
-         Constant(value=0)]),
...(截断)
```

**`Server.wait_closed`**（源 L379 ↔ 产物 L297）

```diff
-   test=BoolOp(
-    op=Or(),
-    values=[
-     Compare(
-      left=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='_sockets',
-       ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Constant(value=None)]),
-     Compare(
+   test=Compare(
...(截断)
```

**`BaseEventLoop.shutdown_asyncgens`**（源 L539 ↔ 产物 L412）

```diff
-    Return()],
+    Return(
+     value=Constant(value=None))],
-  Assign(
-   targets=[
-    Name(id='closing_agens', ctx=Store())],
-   value=Call(
-    func=Name(id='list', ctx=Load()),
-    args=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_asyncgens',
-      ctx=Load())],
-    keywords=[])),
...(截断)
```

**`BaseEventLoop.run_until_complete`**（源 L617 ↔ 产物 L469）

```diff
-       test=BoolOp(
-        op=And(),
-        values=[
-         Name(id='new_task', ctx=Load()),
-         Call(
+       test=Name(id='new_task', ctx=Load()),
+       body=[
+        If(
+         test=Call(
-         UnaryOp(
-          op=Not(),
-          operand=Call(
-           func=Attribute(
-            value=Name(id='future', ctx=Load()),
...(截断)
```

**`BaseEventLoop.close`**（源 L663 ↔ 产物 L508）

```diff
-   orelse=[]),
-  If(
-   test=Attribute(
-    value=Name(id='self', ctx=Load()),
-    attr='_closed',
-    ctx=Load()),
-   body=[
-    Return()],
-   orelse=[]),
-  If(
-   test=Attribute(
-    value=Name(id='self', ctx=Load()),
-    attr='_debug',
-    ctx=Load()),
...(截断)
```

**`BaseEventLoop._sock_sendfile_fallback`**（源 L896 ↔ 产物 L703）

```diff
+     test=Constant(value=False),
+     body=[
+      Pass()],
+     orelse=[]),
+    While(
-        Assign(
-         targets=[
-          Name(id='blocksize', ctx=Store())],
-         value=Call(
-          func=Name(id='min', ctx=Load()),
-          args=[
-           BinOp(
-            left=Name(id='count', ctx=Load()),
-            op=Sub(),
...(截断)
```

**`BaseEventLoop._connect_sock`**（源 L943 ↔ 产物 L738）

```diff
-            keywords=[])),
-          Break()],
+            keywords=[]))],
-         orelse=[],
+         orelse=[
+          Break()],
-         orelse=[
-          Raise(
-           exc=Call(
-            func=Name(id='OSError', ctx=Load()),
-            args=[
-             JoinedStr(
-              values=[
-               Constant(value='no matching local address with family='),
...(截断)
```

**`BaseEventLoop.create_connection`**（源 L987 ↔ 产物 L780）

```diff
-     Compare(
-      left=Name(id='host', ctx=Load()),
-      ops=[
-       IsNot()],
-      comparators=[
-       Constant(value=None)]),
+     UnaryOp(
+      op=Not(),
+      operand=Compare(
+       left=Name(id='host', ctx=Load()),
+       ops=[
+        Is()],
+       comparators=[
+        Constant(value=None)])),
...(截断)
```

**`BaseEventLoop.sendfile`**（源 L1152 ↔ 产物 L861）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='mode', ctx=Load()),
-    ops=[
-     Is()],
-    comparators=[
-     Attribute(
-      value=Attribute(
-       value=Name(id='constants', ctx=Load()),
-       attr='_SendfileMode',
-       ctx=Load()),
-      attr='TRY_NATIVE',
-      ctx=Load())]),
...(截断)
```

**`BaseEventLoop._sendfile_fallback`**（源 L1203 ↔ 产物 L900）

```diff
+     test=Constant(value=False),
+     body=[
+      Pass()],
+     orelse=[]),
+    While(
-        Assign(
-         targets=[
-          Name(id='blocksize', ctx=Store())],
-         value=Call(
-          func=Name(id='min', ctx=Load()),
-          args=[
-           BinOp(
-            left=Name(id='count', ctx=Load()),
-            op=Sub(),
...(截断)
```

**`BaseEventLoop.create_datagram_endpoint`**（源 L1276 ↔ 产物 L957）

```diff
-     orelse=[]),
-    If(
-     test=BoolOp(
-      op=Or(),
-      values=[
-       Name(id='local_addr', ctx=Load()),
-       Name(id='remote_addr', ctx=Load()),
-       Name(id='family', ctx=Load()),
-       Name(id='proto', ctx=Load()),
-       Name(id='flags', ctx=Load()),
-       Name(id='reuse_port', ctx=Load()),
-       Name(id='allow_broadcast', ctx=Load())]),
-     body=[
-      Assign(
...(截断)
```

**`BaseEventLoop._create_server_getaddrinfo`**（源 L1422 ↔ 产物 L1060）

```diff
-  Assign(
-   targets=[
-    Name(id='infos', ctx=Store())],
-   value=Await(
-    value=Call(
-     func=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_ensure_resolved',
-      ctx=Load()),
-     args=[
-      Tuple(
-       elts=[
-        Name(id='host', ctx=Load()),
-        Name(id='port', ctx=Load())],
...(截断)
```

**`BaseEventLoop.create_server`**（源 L1430 ↔ 产物 L1065）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Name(id='ssl_handshake_timeout', ctx=Load()),
-      ops=[
-       IsNot()],
-      comparators=[
-       Constant(value=None)]),
-     Compare(
-      left=Name(id='ssl', ctx=Load()),
-      ops=[
...(截断)
```

**`BaseEventLoop.connect_accepted_socket`**（源 L1556 ↔ 产物 L1147）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Name(id='ssl_handshake_timeout', ctx=Load()),
-      ops=[
-       IsNot()],
-      comparators=[
-       Constant(value=None)]),
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='ssl', ctx=Load()))]),
...(截断)
```

**`BaseEventLoop.subprocess_shell`**（源 L1631 ↔ 产物 L1197）

```diff
-   orelse=[]),
-  If(
-   test=Name(id='universal_newlines', ctx=Load()),
-   body=[
-    Raise(
-     exc=Call(
-      func=Name(id='ValueError', ctx=Load()),
-      args=[
-       Constant(value='universal_newlines must be False')],
-      keywords=[]))],
-   orelse=[]),
-  If(
-   test=UnaryOp(
-    op=Not(),
...(截断)
```

**`BaseEventLoop.subprocess_exec`**（源 L1667 ↔ 产物 L1221）

```diff
-   orelse=[]),
-  If(
-   test=Name(id='shell', ctx=Load()),
-   body=[
-    Raise(
-     exc=Call(
-      func=Name(id='ValueError', ctx=Load()),
-      args=[
-       Constant(value='shell must be False')],
-      keywords=[]))],
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='bufsize', ctx=Load()),
...(截断)
```

**`BaseEventLoop.call_exception_handler`**（源 L1773 ↔ 产物 L1308）

```diff
-        keywords=[]))],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))],
-            value=Constant(value=True))]))])],
+            value=Constant(value=True))])),
+        Return(
+         value=Constant(value=None))])],
-   orelse=[
-    Try(
+   orelse=[]),
+  Try(
+   body=[
+    Expr(
...(截断)
```

**`BaseEventLoop._run_once`**（源 L1845 ↔ 产物 L1371）

```diff
-         value=Constant(value=False))],
-       orelse=[
-        Expr(
-         value=Call(
-          func=Attribute(
-           value=Name(id='new_scheduled', ctx=Load()),
-           attr='append',
-           ctx=Load()),
-          args=[
-           Name(id='handle', ctx=Load())],
-          keywords=[]))])],
+         value=Constant(value=False)),
+        Continue()],
+       orelse=[]),
...(截断)
```

## `stdlib_asyncio_streams`（判据 failure）

- 源：`D:\Python\Lib\asyncio\streams.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_asyncio_streamsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `FlowControlMixin.pause_writing` | L135 | L105 | return: 源=0 产物=2；常量数: 源=2 产物=4；仅产物常量: None |
| `StreamWriter.drain` | L366 | L300 | await: 源=2 产物=0；return: 源=0 产物=1；常量数: 源=4 产物=3；仅源常量: 0 |
| `StreamReader.feed_data` | L494 | L402 | boolop: 源=1 产物=0；return: 源=1 产物=3；常量数: 源=5 产物=8 |
| `StreamReader._wait_for_data` | L516 | L420 | （指纹一致） |
| `StreamReader.readuntil` | L575 | L467 | break: 源=1 产物=2 |
| `StreamReader.read` | L666 | L515 | boolop: 源=1 产物=2；delete: 源=1 产物=0；return: 源=3 产物=2；slice: 源=2 产物=0；常量数: 源=9 产物=10 |
| `StreamReader.__anext__` | L761 | L590 | （指纹一致） |

### AST 结构差分（源 vs 产物）

**`FlowControlMixin.pause_writing`**（源 L135 ↔ 产物 L105）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_paused',
-     ctx=Load()))),
+   test=Attribute(
+    value=Name(id='self', ctx=Load()),
+    attr='_paused',
+    ctx=Load())),
-      keywords=[]))],
-   orelse=[])],
+      keywords=[])),
+    Return(
...(截断)
```

**`StreamWriter.drain`**（源 L366 ↔ 产物 L300）

```diff
-  If(
-   test=Call(
+  Return(
+   value=Call(
-      attr='_transport',
+      attr='_protocol',
-     attr='is_closing',
+     attr='_drain_helper',
-    keywords=[]),
-   body=[
-    Expr(
-     value=Await(
-      value=Call(
-       func=Name(id='sleep', ctx=Load()),
...(截断)
```

**`StreamReader.feed_data`**（源 L494 ↔ 产物 L402）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_eof',
-     ctx=Load())),
+   test=Attribute(
+    value=Name(id='self', ctx=Load()),
+    attr='_eof',
+    ctx=Load()),
-    Return()],
-   orelse=[]),
-  Expr(
-   value=Call(
...(截断)
```

**`StreamReader._wait_for_data`**（源 L516 ↔ 产物 L420）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_eof',
-     ctx=Load())),
+   test=Attribute(
+    value=Name(id='self', ctx=Load()),
+    attr='_eof',
+    ctx=Load()),
```

**`StreamReader.readuntil`**（源 L575 ↔ 产物 L467）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_exception',
-     ctx=Load()),
-    ops=[
-     IsNot()],
-    comparators=[
-     Constant(value=None)]),
-   body=[
-    Raise(
-     exc=Attribute(
...(截断)
```

**`StreamReader.read`**（源 L666 ↔ 产物 L515）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='n', ctx=Load()),
-    ops=[
-     Eq()],
-    comparators=[
-     Constant(value=0)]),
-   body=[
-    Return(
-     value=Constant(value=b''))],
-   orelse=[]),
-  If(
-   test=Compare(
...(截断)
```

**`StreamReader.__anext__`**（源 L761 ↔ 产物 L590）

```diff
-  Assign(
-   targets=[
-    Name(id='val', ctx=Store())],
-   value=Await(
-    value=Call(
-     func=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='readline',
-      ctx=Load()),
-     args=[],
-     keywords=[]))),
-    left=Name(id='val', ctx=Load()),
+    left=Await(
+     value=Call(
...(截断)
```

## `stdlib_asyncio_taskgroups`（判据 failure）

- 源：`D:\Python\Lib\asyncio\taskgroups.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_asyncio_taskgroupsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `TaskGroup.__aexit__` | L68 | L57 | boolop: 源=3 产物=5 |

### AST 结构差分（源 vs 产物）

**`TaskGroup.__aexit__`**（源 L68 ↔ 产物 L57）

```diff
-   test=Attribute(
-    value=Name(id='self', ctx=Load()),
-    attr='_parent_cancel_requested',
-    ctx=Load()),
-   body=[
-    If(
-     test=Compare(
+   test=BoolOp(
+    op=And(),
+    values=[
+     Attribute(
+      value=Name(id='self', ctx=Load()),
+      attr='_parent_cancel_requested',
+      ctx=Load()),
...(截断)
```

## `stdlib_asyncio_tasks`（判据 failure）

- 源：`D:\Python\Lib\asyncio\tasks.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_asyncio_tasksOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_set_task_name` | L65 | L41 | return: 源=0 产物=2；常量数: 源=3 产物=5 |
| `wait_for` | L436 | L299 | await: 源=5 产物=4；try: 源=4 产物=3 |
| `_wait` | L507 | L347 | boolop: 源=3 产物=1；continue: 源=0 产物=2；return: 源=1 产物=3；常量数: 源=10 产物=11 |
| `_wait._on_completion` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `as_completed` | L568 | L396 | boolop: 源=3 产物=2；return: 源=2 产物=3；常量数: 源=8 产物=9 |
| `as_completed._wait_for_one` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `sleep` | L637 | L456 | await: 源=2 产物=1；return: 源=2 产物=1 |
| `_wrap_awaitable` | L688 | L495 | return: 源=1 产物=0 |
| `gather._done_callback` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`_set_task_name`**（源 L65 ↔ 产物 L41）

```diff
-        ctx=Load()))],
+        ctx=Load())),
+      Expr(
+       value=Call(
+        func=Name(id='set_name', ctx=Load()),
+        args=[
+         Name(id='name', ctx=Load())],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))],
-            value=Constant(value=3))]))])],
-     orelse=[
-      Expr(
-       value=Call(
...(截断)
```

**`wait_for`**（源 L436 ↔ 产物 L299）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='timeout', ctx=Load()),
-    ops=[
-     LtE()],
-    comparators=[
-     Constant(value=0)]),
-   body=[
-    Assign(
-     targets=[
-      Name(id='fut', ctx=Store())],
-     value=Call(
-      func=Name(id='ensure_future', ctx=Load()),
...(截断)
```

**`_wait`**（源 L507 ↔ 产物 L347）

```diff
-       BoolOp(
-        op=And(),
-        values=[
-         Compare(
-          left=Name(id='return_when', ctx=Load()),
-          ops=[
-           Eq()],
-          comparators=[
-           Name(id='FIRST_EXCEPTION', ctx=Load())]),
-         BoolOp(
-          op=And(),
-          values=[
-           UnaryOp(
-            op=Not(),
...(截断)
```

**`as_completed`**（源 L568 ↔ 产物 L396）

```diff
-      Return()],
-     orelse=[]),
-    Expr(
-     value=Call(
-      func=Attribute(
-       value=Name(id='todo', ctx=Load()),
-       attr='remove',
-       ctx=Load()),
-      args=[
-       Name(id='f', ctx=Load())],
-      keywords=[])),
-    Expr(
-     value=Call(
-      func=Attribute(
...(截断)
```

**`sleep`**（源 L637 ↔ 产物 L456）

```diff
-    Return(
-     value=Await(
-      value=Name(id='future', ctx=Load())))],
+    Pass()],
```

**`_wrap_awaitable`**（源 L688 ↔ 产物 L495）

```diff
-  Return(
+  Expr(
```

## `stdlib_asyncio_timeouts`（判据 failure）

- 源：`D:\Python\Lib\asyncio\timeouts.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_asyncio_timeoutsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `Timeout` | L27 | L18 | return: 源=5 产物=7；仅源常量: 'Timeout' |

### AST 结构差分（源 vs 产物）

**`Timeout`**（源 L27 ↔ 产物 L18）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_timeout_handler',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='Optional', ctx=Load()),
-      slice=Attribute(
-       value=Name(id='events', ctx=Load()),
-       attr='TimerHandle',
...(截断)
```

## `stdlib_contextlib`（判据 failure）

- 源：`D:\Python\Lib\contextlib.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_contextlibOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_GeneratorContextManagerBase.__init__` | L104 | L76 | 常量数: 源=3 产物=5 |
| `_GeneratorContextManager.__exit__` | L141 | L97 | （指纹一致） |
| `_AsyncGeneratorContextManager.__aexit__` | L214 | L141 | await: 源=4 产物=2 |
| `ExitStack.__exit__._fix_exception_context` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `AsyncExitStack.__aexit__` | L698 | L516 | boolop: 源=2 产物=1；break: 源=1 产物=3；continue: 源=0 产物=1；常量数: 源=18 产物=19 |
| `AsyncExitStack.__aexit__._fix_exception_context` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`_GeneratorContextManagerBase.__init__`**（源 L104 ↔ 产物 L76）

```diff
-    Tuple(
-     elts=[
-      Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='func',
-       ctx=Store()),
-      Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='args',
-       ctx=Store()),
-      Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='kwds',
-       ctx=Store())],
...(截断)
```

**`_GeneratorContextManager.__exit__`**（源 L141 ↔ 产物 L97）

```diff
-     orelse=[
-      Try(
-       body=[
-        Raise(
-         exc=Call(
-          func=Name(id='RuntimeError', ctx=Load()),
-          args=[
-           Constant(value="generator didn't stop")],
-          keywords=[]))],
-       handlers=[],
-       orelse=[],
-       finalbody=[
-        Expr(
-         value=Call(
...(截断)
```

**`_AsyncGeneratorContextManager.__aexit__`**（源 L214 ↔ 产物 L141）

```diff
-     orelse=[
-      Try(
-       body=[
-        Raise(
-         exc=Call(
-          func=Name(id='RuntimeError', ctx=Load()),
-          args=[
-           Constant(value="generator didn't stop")],
-          keywords=[]))],
-       handlers=[],
-       orelse=[],
-       finalbody=[
-        Expr(
-         value=Await(
...(截断)
```

**`AsyncExitStack.__aexit__`**（源 L698 ↔ 产物 L516）

```diff
-     test=Constant(value=1),
+     test=Constant(value=True),
-       test=BoolOp(
-        op=Or(),
-        values=[
-         Compare(
-          left=Name(id='exc_context', ctx=Load()),
-          ops=[
-           Is()],
-          comparators=[
-           Constant(value=None)]),
-         Compare(
-          left=Name(id='exc_context', ctx=Load()),
-          ops=[
...(截断)
```

## `stdlib_csv`（判据 failure）

- 源：`D:\Python\Lib\csv.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_csvOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `Sniffer._guess_quote_and_delimiter` | L204 | L152 | boolop: 源=2 产物=0 |
| `Sniffer._guess_delimiter` | L280 | L211 | boolop: 源=5 产物=4；continue: 源=1 产物=2；常量数: 源=46 产物=45 |
| `Sniffer.has_header` | L383 | L285 | continue: 源=1 产物=5 |

### AST 结构差分（源 vs 产物）

**`Sniffer._guess_quote_and_delimiter`**（源 L204 ↔ 产物 L152）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       Name(id='key', ctx=Load()),
-       BoolOp(
-        op=Or(),
-        values=[
-         Compare(
-          left=Name(id='delimiters', ctx=Load()),
-          ops=[
-           Is()],
-          comparators=[
-           Constant(value=None)]),
-         Compare(
...(截断)
```

**`Sniffer._guess_delimiter`**（源 L280 ↔ 产物 L211）

```diff
-    Tuple(
-     elts=[
-      Name(id='start', ctx=Store()),
-      Name(id='end', ctx=Store())],
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     Constant(value=0),
-     Name(id='chunkLength', ctx=Load())],
-    ctx=Load())),
+    Name(id='end', ctx=Store())],
+   value=Name(id='chunkLength', ctx=Load())),
-       orelse=[]),
-      If(
...(截断)
```

**`Sniffer.has_header`**（源 L383 ↔ 产物 L285）

```diff
-           value=Name(id='thisType', ctx=Load()))],
-         orelse=[
-          Delete(
-           targets=[
-            Subscript(
-             value=Name(id='columnTypes', ctx=Load()),
-             slice=Name(id='col', ctx=Load()),
-             ctx=Del())])])],
+           value=Name(id='thisType', ctx=Load())),
+          Continue()],
+         orelse=[]),
+        Delete(
+         targets=[
+          Subscript(
...(截断)
```

## `stdlib_dataclasses`（判据 failure）

- 源：`D:\Python\Lib\dataclasses.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_dataclassesOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_get_field` | L723 | L244 | boolop: 源=5 产物=6 |
| `_hash_add.<listcomp>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_process_class` | L884 | L294 | boolop: 源=9 产物=7；continue: 源=0 产物=3；raise: 源=8 产物=7；常量数: 源=53 产物=52；仅源常量: 'eq must be true if order is true'；仅产物常量: 1 |
| `_add_slots` | L1147 | L403 | 常量数: 源=16 产物=18 |

### AST 结构差分（源 vs 产物）

**`_get_field`**（源 L723 ↔ 产物 L244）

```diff
-   test=Name(id='typing', ctx=Load()),
-   body=[
-    If(
-     test=BoolOp(
+   test=BoolOp(
+    op=And(),
+    values=[
+     Name(id='typing', ctx=Load()),
+     BoolOp(
-          keywords=[])])]),
-     body=[
-      Assign(
-       targets=[
-        Attribute(
...(截断)
```

**`_process_class`**（源 L884 ↔ 产物 L294）

```diff
-     test=BoolOp(
-      op=Or(),
-      values=[
-       Call(
-        func=Name(id='_is_kw_only', ctx=Load()),
-        args=[
-         Name(id='type', ctx=Load()),
-         Name(id='dataclasses', ctx=Load())],
-        keywords=[]),
-       BoolOp(
+     test=UnaryOp(
+      op=Not(),
+      operand=Call(
+       func=Name(id='_is_kw_only', ctx=Load()),
...(截断)
```

**`_add_slots`**（源 L1147 ↔ 产物 L403）

```diff
+  Assign(
+   targets=[
+    Subscript(
+     value=Name(id='cls_dict', ctx=Load()),
+     slice=Constant(value='__slots__'),
+     ctx=Store())],
+   value=Constant(value=1)),
```

## `stdlib_difflib`（判据 failure）

- 源：`D:\Python\Lib\difflib.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_difflibOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `SequenceMatcher.__chain_b` | L266 | L204 | boolop: 源=1 产物=0 |
| `SequenceMatcher.find_longest_match` | L305 | L228 | boolop: 源=4 产物=6；continue: 源=1 产物=2；namedexpr: 源=0 产物=1；while: 源=4 产物=3；常量数: 源=27 产物=26 |
| `SequenceMatcher.get_matching_blocks` | L421 | L315 | continue: 源=0 产物=1；namedexpr: 源=0 产物=1 |
| `SequenceMatcher.get_opcodes` | L492 | L363 | （指纹一致） |
| `SequenceMatcher.get_grouped_opcodes` | L547 | L410 | boolop: 源=3 产物=1；return: 源=0 产物=1；常量数: 源=22 产物=23；仅产物常量: None |
| `SequenceMatcher.quick_ratio` | L622 | L480 | （指纹一致） |
| `get_close_matches` | L666 | L511 | fstring: 源=0 产物=1；raise: 源=2 产物=1；常量数: 源=8 产物=7；仅源常量: 'cutoff must be in [0.0, 1.0]: %r', 'n must be > 0: %r'；仅产物常量: 'n must be > 0: ' |
| `Differ._fancy_replace` | L893 | L712 | continue: 源=1 产物=6；fstring: 源=0 产物=1；常量数: 源=25 产物=26；仅源常量: '\n        When replacing one block of lines with another, search the blocks\n        for *similar* lines; the best-matching pair (if any) is used as a\n        synch point, and intraline difference marking is done on the\n        similar pair. Lots of work, but often worth it.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._fancy_replace([\'abcDefghiJkl\\n\'], 0, 1,\n        ...                            [\'abcdefGhijkl\\n\'], 0, 1)\n        >>> print(\'\'.join(results), end="")\n        - abcDefghiJkl\n        ?    ^  ^  ^\n        + abcdefGhijkl\n        ?    ^  ^  ^\n        ', 'unknown tag %r'；仅产物常量: '\n        When replacing one block of lines with another, search the blocks\n        for *similar* lines; the best-matching pair (if any) is used as a\n        synch point, and intraline difference marking is done on the\n        similar pair. Lots of work, but often worth it.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._fancy_replace([\'abcDefghiJkl\n\'], 0, 1,\n        ...                            [\'abcdefGhijkl\n\'], 0, 1)\n        >>> print(\'\'.join(results), end="")\n        - abcDefghiJkl\n        ?    ^  ^  ^\n        + abcdefGhijkl\n        ?    ^  ^  ^\n        ', 'unknown tag ' |
| `Differ._qformat` | L999 | L790 | return: 源=0 产物=2；yield: 源=4 产物=2；仅源常量: '+ ', '- ', '\n        Format "?" output and deal with tabs.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._qformat(\'\\tabcDefghiJkl\\n\', \'\\tabcdefGhijkl\\n\',\n        ...                      \'  ^ ^  ^      \', \'  ^ ^  ^      \')\n        >>> for line in results: print(repr(line))\n        ...\n        \'- \\tabcDefghiJkl\\n\'\n        \'? \\t ^ ^  ^\\n\'\n        \'+ \\tabcdefGhijkl\\n\'\n        \'? \\t ^ ^  ^\\n\'\n        '；仅产物常量: '\n        Format "?" output and deal with tabs.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._qformat(\'\tabcDefghiJkl\n\', \'\tabcdefGhijkl\n\',\n        ...                      \'  ^ ^  ^      \', \'  ^ ^  ^      \')\n        >>> for line in results: print(repr(line))\n        ...\n        \'- \tabcDefghiJkl\n\'\n        \'? \t ^ ^  ^\n\'\n        \'+ \tabcdefGhijkl\n\'\n        \'? \t ^ ^  ^\n\'\n        ', None |
| `unified_diff` | L1095 | L855 | 常量数: 源=31 产物=30；仅源常量: 0 |
| `context_diff` | L1180 | L928 | yield: 源=7 产物=6；常量数: 源=35 产物=34；仅源常量: '***************', '\n    Compare two sequences of lines; generate the delta as a context diff.\n\n    Context diffs are a compact way of showing line changes and a few\n    lines of context.  The number of context lines is set by \'n\' which\n    defaults to three.\n\n    By default, the diff control lines (those with *** or ---) are\n    created with a trailing newline.  This is helpful so that inputs\n    created from file.readlines() result in diffs that are suitable for\n    file.writelines() since both the inputs and outputs have trailing\n    newlines.\n\n    For inputs that do not have trailing newlines, set the lineterm\n    argument to "" so that the output will be uniformly newline free.\n\n    The context diff format normally has a header for filenames and\n    modification times.  Any or all of these may be specified using\n    strings for \'fromfile\', \'tofile\', \'fromfiledate\', and \'tofiledate\'.\n    The modification times are normally expressed in the ISO 8601 format.\n    If not specified, the strings default to blanks.\n\n    Example:\n\n    >>> print(\'\'.join(context_diff(\'one\\ntwo\\nthree\\nfour\\n\'.splitlines(True),\n    ...       \'zero\\none\\ntree\\nfour\\n\'.splitlines(True), \'Original\', \'Current\')),\n    ...       end="")\n    *** Original\n    --- Current\n    ***************\n    *** 1,4 ****\n      one\n    ! two\n    ! three\n      four\n    --- 1,4 ----\n    + zero\n      one\n    ! tree\n      four\n    '；仅产物常量: '\n    Compare two sequences of lines; generate the delta as a context diff.\n\n    Context diffs are a compact way of showing line changes and a few\n    lines of context.  The number of context lines is set by \'n\' which\n    defaults to three.\n\n    By default, the diff control lines (those with *** or ---) are\n    created with a trailing newline.  This is helpful so that inputs\n    created from file.readlines() result in diffs that are suitable for\n    file.writelines() since both the inputs and outputs have trailing\n    newlines.\n\n    For inputs that do not have trailing newlines, set the lineterm\n    argument to "" so that the output will be uniformly newline free.\n\n    The context diff format normally has a header for filenames and\n    modification times.  Any or all of these may be specified using\n    strings for \'fromfile\', \'tofile\', \'fromfiledate\', and \'tofiledate\'.\n    The modification times are normally expressed in the ISO 8601 format.\n    If not specified, the strings default to blanks.\n\n    Example:\n\n    >>> print(\'\'.join(context_diff(\'one\ntwo\nthree\nfour\n\'.splitlines(True),\n    ...       \'zero\none\ntree\nfour\n\'.splitlines(True), \'Original\', \'Current\')),\n    ...       end="")\n    *** Original\n    --- Current\n    ***************\n    *** 1,4 ****\n      one\n    ! two\n    ! three\n      four\n    --- 1,4 ----\n    + zero\n      one\n    ! tree\n      four\n    ' |
| `_mdiff` | L1340 | L1065 | boolop: 源=2 产物=1；break: 源=0 产物=4；continue: 源=8 产物=9；return: 源=7 产物=5；仅源常量: 'Returns generator yielding marked up from/to side by side differences.\n\n    Arguments:\n    fromlines -- list of text lines to compared to tolines\n    tolines -- list of text lines to be compared to fromlines\n    context -- number of context lines to display on each side of difference,\n               if None, all from/to text lines will be generated.\n    linejunk -- passed on to ndiff (see ndiff documentation)\n    charjunk -- passed on to ndiff (see ndiff documentation)\n\n    This function returns an iterator which returns a tuple:\n    (from line tuple, to line tuple, boolean flag)\n\n    from/to line tuple -- (line num, line text)\n        line num -- integer or None (to indicate a context separation)\n        line text -- original line text with following markers inserted:\n            \'\\0+\' -- marks start of added text\n            \'\\0-\' -- marks start of deleted text\n            \'\\0^\' -- marks start of changed text\n            \'\\1\' -- marks end of added/deleted/changed text\n\n    boolean flag -- None indicates context separation, True indicates\n        either "from" or "to" line contains a change, otherwise False.\n\n    This function/iterator was originally developed to generate side by side\n    file difference for making HTML pages (see HtmlDiff class for example\n    usage).\n\n    Note, this function utilizes the ndiff function to generate the side by\n    side difference markup.  Optional ndiff arguments may be passed to this\n    function and they in turn will be passed to ndiff.\n    '；仅产物常量: 'Returns generator yielding marked up from/to side by side differences.\n\n    Arguments:\n    fromlines -- list of text lines to compared to tolines\n    tolines -- list of text lines to be compared to fromlines\n    context -- number of context lines to display on each side of difference,\n               if None, all from/to text lines will be generated.\n    linejunk -- passed on to ndiff (see ndiff documentation)\n    charjunk -- passed on to ndiff (see ndiff documentation)\n\n    This function returns an iterator which returns a tuple:\n    (from line tuple, to line tuple, boolean flag)\n\n    from/to line tuple -- (line num, line text)\n        line num -- integer or None (to indicate a context separation)\n        line text -- original line text with following markers inserted:\n            \'\x00+\' -- marks start of added text\n            \'\x00-\' -- marks start of deleted text\n            \'\x00^\' -- marks start of changed text\n            \'\x01\' -- marks end of added/deleted/changed text\n\n    boolean flag -- None indicates context separation, True indicates\n        either "from" or "to" line contains a change, otherwise False.\n\n    This function/iterator was originally developed to generate side by side\n    file difference for making HTML pages (see HtmlDiff class for example\n    usage).\n\n    Note, this function utilizes the ndiff function to generate the side by\n    side difference markup.  Optional ndiff arguments may be passed to this\n    function and they in turn will be passed to ndiff.\n    ' |
| `_mdiff._make_line` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_mdiff._line_pair_iterator` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `HtmlDiff._line_wrapper` | L1810 | L1443 | boolop: 源=1 产物=0；continue: 源=1 产物=3 |
| `HtmlDiff._collect_lines` | L1838 | L1467 | （指纹一致） |

### AST 结构差分（源 vs 产物）

**`SequenceMatcher.__chain_b`**（源 L266 ↔ 产物 L204）

```diff
-     ctx=Store()),
-    Name(id='b2j', ctx=Store())],
+     ctx=Store())],
-     ctx=Store()),
-    Name(id='junk', ctx=Store())],
+     ctx=Store())],
-     ctx=Store()),
-    Name(id='popular', ctx=Store())],
+     ctx=Store())],
-   test=BoolOp(
-    op=And(),
-    values=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
...(截断)
```

**`SequenceMatcher.find_longest_match`**（源 L305 ↔ 产物 L228）

```diff
-    Tuple(
-     elts=[
-      Name(id='besti', ctx=Store()),
-      Name(id='bestj', ctx=Store()),
-      Name(id='bestsize', ctx=Store())],
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     Name(id='alo', ctx=Load()),
-     Name(id='blo', ctx=Load()),
-     Constant(value=0)],
-    ctx=Load())),
+    Name(id='bestsize', ctx=Store())],
+   value=Constant(value=0)),
...(截断)
```

**`SequenceMatcher.get_matching_blocks`**（源 L421 ↔ 产物 L315）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Tuple(
-     elts=[
-      Name(id='la', ctx=Store()),
+   orelse=[
+    Assign(
+     targets=[
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     Call(
-      func=Name(id='len', ctx=Load()),
...(截断)
```

**`SequenceMatcher.get_opcodes`**（源 L492 ↔ 产物 L363）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='i', ctx=Store()),
-    Name(id='j', ctx=Store())],
-   value=Constant(value=0)),
-  Assign(
-   targets=[
-    Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='opcodes',
-     ctx=Store()),
-    Name(id='answer', ctx=Store())],
-   value=List(elts=[], ctx=Load())),
...(截断)
```

**`SequenceMatcher.get_grouped_opcodes`**（源 L547 ↔ 产物 L410）

```diff
-   test=BoolOp(
-    op=And(),
-    values=[
-     Name(id='group', ctx=Load()),
-     UnaryOp(
-      op=Not(),
-      operand=BoolOp(
-       op=And(),
-       values=[
-        Compare(
-         left=Call(
-          func=Name(id='len', ctx=Load()),
-          args=[
-           Name(id='group', ctx=Load())],
...(截断)
```

**`SequenceMatcher.quick_ratio`**（源 L622 ↔ 产物 L480）

```diff
-       ctx=Store()),
-      Name(id='fullbcount', ctx=Store())],
+       ctx=Store())],
-    Tuple(
-     elts=[
-      Name(id='availhas', ctx=Store()),
-      Name(id='matches', ctx=Store())],
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     Attribute(
-      value=Name(id='avail', ctx=Load()),
-      attr='__contains__',
-      ctx=Load()),
...(截断)
```

**`get_close_matches`**（源 L666 ↔ 产物 L511）

```diff
-       BinOp(
-        left=Constant(value='n must be > 0: %r'),
-        op=Mod(),
-        right=Tuple(
-         elts=[
-          Name(id='n', ctx=Load())],
-         ctx=Load()))],
+       JoinedStr(
+        values=[
+         Constant(value='n must be > 0: '),
+         FormattedValue(
+          value=Name(id='n', ctx=Load()),
+          conversion=114)])],
-   orelse=[]),
...(截断)
```

**`Differ._fancy_replace`**（源 L893 ↔ 产物 L712）

```diff
-   value=Constant(value='\n        When replacing one block of lines with another, search the blocks\n        for *similar* lines; the best-matching pair (if any) is used as a\n        synch point, and intraline differe
+   value=Constant(value='\n        When replacing one block of lines with another, search the blocks\n        for *similar* lines; the best-matching pair (if any) is used as a\n        synch point, and intraline differe
-         orelse=[]),
+         orelse=[
+          Continue()]),
-      Return()],
+      Return(
+       value=Constant(value=None))],
-      Name(id='atags', ctx=Store()),
-      Name(id='btags', ctx=Store())],
+      Name(id='atags', ctx=Store())],
-          right=Name(id='lb', ctx=Load())))],
+          right=Name(id='lb', ctx=Load()))),
+        Continue()],
...(截断)
```

**`Differ._qformat`**（源 L999 ↔ 产物 L790）

```diff
-   value=Constant(value='\n        Format "?" output and deal with tabs.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._qformat(\'\\tabcDefghiJkl\\n\', \'\\tabcdefGhijkl\\n\',\n        ...    
+   value=Constant(value='\n        Format "?" output and deal with tabs.\n\n        Example:\n\n        >>> d = Differ()\n        >>> results = d._qformat(\'\tabcDefghiJkl\n\', \'\tabcdefGhijkl\n\',\n        ...        
-  Expr(
-   value=Yield(
-    value=BinOp(
-     left=Constant(value='- '),
-     op=Add(),
-     right=Name(id='aline', ctx=Load())))),
-  Expr(
-   value=Yield(
-    value=BinOp(
-     left=Constant(value='+ '),
-     op=Add(),
-     right=Name(id='bline', ctx=Load())))),
...(截断)
```

**`unified_diff`**（源 L1095 ↔ 产物 L855）

```diff
-      Tuple(
-       elts=[
-        Name(id='first', ctx=Store()),
-        Name(id='last', ctx=Store())],
-       ctx=Store())],
-     value=Tuple(
-      elts=[
-       Subscript(
-        value=Name(id='group', ctx=Load()),
-        slice=Constant(value=0),
-        ctx=Load()),
-       Subscript(
-        value=Name(id='group', ctx=Load()),
-        slice=UnaryOp(
...(截断)
```

**`context_diff`**（源 L1180 ↔ 产物 L928）

```diff
-   value=Constant(value='\n    Compare two sequences of lines; generate the delta as a context diff.\n\n    Context diffs are a compact way of showing line changes and a few\n    lines of context.  The number of context
+   value=Constant(value='\n    Compare two sequences of lines; generate the delta as a context diff.\n\n    Context diffs are a compact way of showing line changes and a few\n    lines of context.  The number of context
-    Expr(
-     value=Yield(
-      value=BinOp(
-       left=Constant(value='***************'),
-       op=Add(),
-       right=Name(id='lineterm', ctx=Load())))),
-            Constant(value='replace'),
-            Constant(value='delete')])]),
+            Constant(value='delete'),
+            Constant(value='replace')])]),
-            Constant(value='replace'),
-            Constant(value='insert')])]),
...(截断)
```

**`_mdiff`**（源 L1340 ↔ 产物 L1065）

```diff
-   value=Constant(value='Returns generator yielding marked up from/to side by side differences.\n\n    Arguments:\n    fromlines -- list of text lines to compared to tolines\n    tolines -- list of text lines to be comp
+   value=Constant(value='Returns generator yielding marked up from/to side by side differences.\n\n    Arguments:\n    fromlines -- list of text lines to compared to tolines\n    tolines -- list of text lines to be comp
-     orelse=[]),
-    If(
-     test=Compare(
-      left=Name(id='format_key', ctx=Load()),
-      ops=[
-       Eq()],
-      comparators=[
-       Constant(value='?')]),
-     body=[
-      Assign(
-       targets=[
-        Tuple(
...(截断)
```

**`HtmlDiff._line_wrapper`**（源 L1810 ↔ 产物 L1443）

```diff
-        Tuple(
-         elts=[
-          Name(id='fromline', ctx=Store()),
-          Name(id='fromtext', ctx=Store())],
-         ctx=Store()),
-        Tuple(
-         elts=[
-          Name(id='toline', ctx=Store()),
-          Name(id='totext', ctx=Store())],
-         ctx=Store())],
+        Name(id='fromline', ctx=Store()),
+        Name(id='fromtext', ctx=Store())],
-     value=Tuple(
-      elts=[
...(截断)
```

**`HtmlDiff._collect_lines`**（源 L1838 ↔ 产物 L1467）

```diff
-    Tuple(
-     elts=[
-      Name(id='fromlist', ctx=Store()),
-      Name(id='tolist', ctx=Store()),
-      Name(id='flaglist', ctx=Store())],
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     List(elts=[], ctx=Load()),
-     List(elts=[], ctx=Load()),
-     List(elts=[], ctx=Load())],
-    ctx=Load())),
+    Name(id='flaglist', ctx=Store())],
+   value=List(elts=[], ctx=Load())),
...(截断)
```

## `stdlib_functools`（判据 failure）

- 源：`D:\Python\Lib\functools.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_functoolsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `update_wrapper` | L35 | L14 | （指纹一致） |
| `partial.__new__` | L283 | L188 | params: 源=0 产物=2；posonly: 源=2 产物=0 |
| `partial.__call__` | L299 | L200 | params: 源=0 产物=1；posonly: 源=1 产物=0 |
| `partial.__reduce__` | L313 | L213 | boolop: 源=2 产物=1；常量数: 源=2 产物=1 |
| `partial.__setstate__` | L317 | L216 | （指纹一致） |
| `partialmethod.__init__` | L355 | L249 | params: 源=0 产物=2；posonly: 源=2 产物=0；return: 源=0 产物=1；常量数: 源=2 产物=3；仅产物常量: None |
| `partialmethod._make_unbound_method._method` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `lru_cache` | L479 | L331 | lambda: 源=2 产物=1；常量数: 源=12 产物=10 |
| `lru_cache.<lambda>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_lru_cache_wrapper.wrapper` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_c3_merge` | L660 | L456 | （指纹一致） |
| `_c3_mro` | L687 | L482 | （指纹一致） |
| `_find_impl` | L774 | L551 | continue: 源=0 产物=1 |

### AST 结构差分（源 vs 产物）

**`update_wrapper`**（源 L35 ↔ 产物 L14）

```diff
-     orelse=[
-      Expr(
-       value=Call(
-        func=Name(id='setattr', ctx=Load()),
-        args=[
-         Name(id='wrapper', ctx=Load()),
-         Name(id='attr', ctx=Load()),
-         Name(id='value', ctx=Load())],
-        keywords=[]))],
-     finalbody=[])],
+     orelse=[],
+     finalbody=[]),
+    Expr(
+     value=Call(
...(截断)
```

**`partial.__new__`**（源 L283 ↔ 产物 L188）

```diff
-  posonlyargs=[
+  posonlyargs=[],
+  args=[
-  args=[],
-   orelse=[]),
-  If(
-   test=Call(
-    func=Name(id='hasattr', ctx=Load()),
-    args=[
-     Name(id='func', ctx=Load()),
-     Constant(value='func')],
-    keywords=[]),
-   body=[
-    Assign(
...(截断)
```

**`partial.__call__`**（源 L299 ↔ 产物 L200）

```diff
-  posonlyargs=[
+  posonlyargs=[],
+  args=[
-  args=[],
-   value=Dict(
-    keys=[
-     None,
-     None],
-    values=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='keywords',
-      ctx=Load()),
-     Name(id='keywords', ctx=Load())])),
...(截断)
```

**`partial.__reduce__`**（源 L313 ↔ 产物 L213）

```diff
+  Expr(
+   value=BoolOp(
+    op=Or(),
+    values=[
+     Attribute(
+      value=Name(id='self', ctx=Load()),
+      attr='keywords',
+      ctx=Load()),
+     Constant(value=None)])),
-     Call(
-      func=Name(id='type', ctx=Load()),
-      args=[
-       Name(id='self', ctx=Load())],
-      keywords=[]),
...(截断)
```

**`partial.__setstate__`**（源 L317 ↔ 产物 L216）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Call(
-     func=Name(id='len', ctx=Load()),
-     args=[
-      Name(id='state', ctx=Load())],
-     keywords=[]),
-    ops=[
-     NotEq()],
-    comparators=[
-     Constant(value=4)]),
-   body=[
-    Raise(
...(截断)
```

**`partialmethod.__init__`**（源 L355 ↔ 产物 L249）

```diff
-  posonlyargs=[
+  posonlyargs=[],
+  args=[
-  args=[],
-   test=BoolOp(
-    op=And(),
-    values=[
-     UnaryOp(
-      op=Not(),
-      operand=Call(
+   test=UnaryOp(
+    op=Not(),
+    operand=BoolOp(
+     op=Or(),
...(截断)
```

**`lru_cache`**（源 L479 ↔ 产物 L331）

```diff
-      Assign(
-       targets=[
-        Name(id='wrapper', ctx=Store())],
-       value=Call(
-        func=Name(id='_lru_cache_wrapper', ctx=Load()),
-        args=[
-         Name(id='user_function', ctx=Load()),
-         Name(id='maxsize', ctx=Load()),
-         Name(id='typed', ctx=Load()),
-         Name(id='_CacheInfo', ctx=Load())],
-        keywords=[])),
-      Assign(
-       targets=[
-        Attribute(
...(截断)
```

**`_c3_merge`**（源 L660 ↔ 产物 L456）

```diff
-     test=UnaryOp(
-      op=Not(),
-      operand=Name(id='sequences', ctx=Load())),
+     test=Name(id='sequences', ctx=Load()),
-      Return(
-       value=Name(id='result', ctx=Load()))],
-     orelse=[]),
-    For(
-     target=Name(id='s1', ctx=Store()),
-     iter=Name(id='sequences', ctx=Load()),
-     body=[
-      Assign(
-       targets=[
-        Name(id='candidate', ctx=Store())],
...(截断)
```

**`_c3_mro`**（源 L687 ↔ 产物 L482）

```diff
-     orelse=[])],
+     orelse=[]),
+    Assign(
+     targets=[
+      Name(id='abcs', ctx=Store())],
+     value=IfExp(
+      test=Name(id='abcs', ctx=Load()),
+      body=Call(
+       func=Name(id='list', ctx=Load()),
+       args=[
+        Name(id='abcs', ctx=Load())],
+       keywords=[]),
+      orelse=List(elts=[], ctx=Load())))],
-  Assign(
...(截断)
```

**`_find_impl`**（源 L774 ↔ 产物 L551）

```diff
+       test=Compare(
+        left=Name(id='t', ctx=Load()),
+        ops=[
+         NotIn()],
+        comparators=[
+         Attribute(
+          value=Name(id='cls', ctx=Load()),
+          attr='__mro__',
+          ctx=Load())]),
+       body=[
+        If(
+         test=Compare(
+          left=Name(id='match', ctx=Load()),
+          ops=[
...(截断)
```

## `stdlib_http_cookiejar`（判据 failure）

- 源：`D:\Python\Lib\http\cookiejar.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_http_cookiejarOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_timegm` | L81 | L72 | boolop: 源=1 产物=2；return: 源=2 产物=1；常量数: 源=12 产物=13；仅源常量: None |
| `split_header_words` | L348 | L289 | fstring: 源=0 产物=1；常量数: 源=12 产物=14；仅源常量: "split_header_words bug: '%s', '%s', %s", 'Parse header values into a list of lists containing key,value pairs.\n\n    The function knows how to deal with ",", ";" and "=" as well as quoted\n    values after "=".  A list of space separated tokens are parsed as if they\n    were separated by ";".\n\n    If the header_values passed as argument contains multiple values, then they\n    are treated as if they were a single value separated by comma ",".\n\n    This means that this function is useful for parsing header fields that\n    follow this syntax (BNF as from the HTTP/1.1 specification, but we relax\n    the requirement for tokens).\n\n      headers           = #header\n      header            = (token | parameter) *( [";"] (token | parameter))\n\n      token             = 1*<any CHAR except CTLs or separators>\n      separators        = "(" | ")" | "<" | ">" | "@"\n                        | "," | ";" | ":" | "\\" | <">\n                        | "/" | "[" | "]" | "?" | "="\n                        | "{" | "}" | SP | HT\n\n      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )\n      qdtext            = <any TEXT except <">>\n      quoted-pair       = "\\" CHAR\n\n      parameter         = attribute "=" value\n      attribute         = token\n      value             = token | quoted-string\n\n    Each header is represented by a list of key/value pairs.  The value for a\n    simple token (not part of a parameter) is None.  Syntactically incorrect\n    headers will not necessarily be parsed as you would want.\n\n    This is easier to describe with some examples:\n\n    >>> split_header_words([\'foo="bar"; port="80,81"; discard, bar=baz\'])\n    [[(\'foo\', \'bar\'), (\'port\', \'80,81\'), (\'discard\', None)], [(\'bar\', \'baz\')]]\n    >>> split_header_words([\'text/html; charset="iso-8859-1"\'])\n    [[(\'text/html\', None), (\'charset\', \'iso-8859-1\')]]\n    >>> split_header_words([r\'Basic realm="\\"foo\\bar\\""\'])\n    [[(\'Basic\', None), (\'realm\', \'"foobar"\')]]\n\n    '；仅产物常量: "', ", "', '", "split_header_words bug: '", 'Parse header values into a list of lists containing key,value pairs.\n\n    The function knows how to deal with ",", ";" and "=" as well as quoted\n    values after "=".  A list of space separated tokens are parsed as if they\n    were separated by ";".\n\n    If the header_values passed as argument contains multiple values, then they\n    are treated as if they were a single value separated by comma ",".\n\n    This means that this function is useful for parsing header fields that\n    follow this syntax (BNF as from the HTTP/1.1 specification, but we relax\n    the requirement for tokens).\n\n      headers           = #header\n      header            = (token | parameter) *( [";"] (token | parameter))\n\n      token             = 1*<any CHAR except CTLs or separators>\n      separators        = "(" | ")" | "<" | ">" | "@"\n                        | "," | ";" | ":" | "" | <">\n                        | "/" | "[" | "]" | "?" | "="\n                        | "{" | "}" | SP | HT\n\n      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )\n      qdtext            = <any TEXT except <">>\n      quoted-pair       = "" CHAR\n\n      parameter         = attribute "=" value\n      attribute         = token\n      value             = token | quoted-string\n\n    Each header is represented by a list of key/value pairs.  The value for a\n    simple token (not part of a parameter) is None.  Syntactically incorrect\n    headers will not necessarily be parsed as you would want.\n\n    This is easier to describe with some examples:\n\n    >>> split_header_words([\'foo="bar"; port="80,81"; discard, bar=baz\'])\n    [[(\'foo\', \'bar\'), (\'port\', \'80,81\'), (\'discard\', None)], [(\'bar\', \'baz\')]]\n    >>> split_header_words([\'text/html; charset="iso-8859-1"\'])\n    [[(\'text/html\', None), (\'charset\', \'iso-8859-1\')]]\n    >>> split_header_words([r\'Basic realm=""foo\x08ar""\'])\n    [[(\'Basic\', None), (\'realm\', \'"foobar"\')]]\n\n    ' |
| `user_domain_match` | L599 | L507 | boolop: 源=3 产物=2 |
| `DefaultCookiePolicy.set_ok_version` | L968 | L800 | （指纹一致） |
| `DefaultCookiePolicy.set_ok_path` | L1004 | L826 | boolop: 源=3 产物=1 |
| `DefaultCookiePolicy.set_ok_domain` | L1015 | L838 | boolop: 源=9 产物=7 |
| `deepvalues` | L1227 | L1000 | （指纹一致） |
| `CookieJar.add_cookie_header` | L1356 | L1100 | boolop: 源=1 产物=2；continue: 源=0 产物=1；常量数: 源=9 产物=10；仅产物常量: None |
| `CookieJar._normalized_cookie_tuples` | L1389 | L1124 | continue: 源=4 产物=7 |
| `CookieJar.make_cookies` | L1599 | L1267 | 常量数: 源=4 产物=5 |
| `CookieJar.set_cookie_if_ok` | L1654 | L1303 | 常量数: 源=1 产物=2；仅产物常量: None |
| `CookieJar.clear` | L1692 | L1338 | boolop: 源=1 产物=0；return: 源=0 产物=3；常量数: 源=12 产物=15 |
| `FileCookieJar.revert` | L1804 | L1444 | return: 源=0 产物=1；常量数: 源=6 产物=7 |
| `LWPCookieJar.as_lwp_str` | L1872 | L1511 | boolop: 源=2 产物=0；continue: 源=2 产物=3；仅源常量: 'Return cookies as a string of "\\n"-separated "Set-Cookie3" headers.\n\n        ignore_discard and ignore_expires: see docstring for FileCookieJar.save\n\n        '；仅产物常量: 'Return cookies as a string of "\n"-separated "Set-Cookie3" headers.\n\n        ignore_discard and ignore_expires: see docstring for FileCookieJar.save\n\n        ' |
| `MozillaCookieJar.save` | L2087 | L1677 | boolop: 源=2 产物=0；return: 源=0 产物=1；常量数: 源=18 产物=19 |

### AST 结构差分（源 vs 产物）

**`_timegm`**（源 L81 ↔ 产物 L72）

```diff
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Name(id='year', ctx=Load()),
-      ops=[
-       GtE()],
-      comparators=[
-       Name(id='EPOCH_YEAR', ctx=Load())]),
-     Compare(
-      left=Constant(value=1),
-      ops=[
-       LtE(),
-       LtE()],
...(截断)
```

**`split_header_words`**（源 L348 ↔ 产物 L289）

```diff
-   value=Constant(value='Parse header values into a list of lists containing key,value pairs.\n\n    The function knows how to deal with ",", ";" and "=" as well as quoted\n    values after "=".  A list of space separat
+   value=Constant(value='Parse header values into a list of lists containing key,value pairs.\n\n    The function knows how to deal with ",", ";" and "=" as well as quoted\n    values after "=".  A list of space separat
-   test=UnaryOp(
-    op=Not(),
-    operand=Call(
-     func=Name(id='isinstance', ctx=Load()),
-     args=[
-      Name(id='header_values', ctx=Load()),
-      Name(id='str', ctx=Load())],
-     keywords=[]))),
+   test=Call(
+    func=Name(id='isinstance', ctx=Load()),
+    args=[
+     Name(id='header_values', ctx=Load()),
...(截断)
```

**`user_domain_match`**（源 L599 ↔ 产物 L507）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=BoolOp(
-     op=And(),
-     values=[
-      Call(
-       func=Name(id='liberal_is_HDN', ctx=Load()),
-       args=[
-        Name(id='A', ctx=Load())],
-       keywords=[]),
-      Call(
+   test=Call(
+    func=Name(id='liberal_is_HDN', ctx=Load()),
+    args=[
...(截断)
```

**`DefaultCookiePolicy.set_ok_version`**（源 L968 ↔ 产物 L800）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Attribute(
-       value=Name(id='cookie', ctx=Load()),
-       attr='version',
-       ctx=Load()),
-      ops=[
-       Gt()],
-      comparators=[
-       Constant(value=0)]),
...(截断)
```

**`DefaultCookiePolicy.set_ok_path`**（源 L1004 ↔ 产物 L826）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       BoolOp(
-        op=Or(),
+     test=UnaryOp(
+      op=Not(),
+      operand=Compare(
+       left=Attribute(
+        value=Name(id='cookie', ctx=Load()),
+        attr='version',
+        ctx=Load()),
+       ops=[
+        Gt()],
...(截断)
```

**`DefaultCookiePolicy.set_ok_domain`**（源 L1015 ↔ 产物 L838）

```diff
-   orelse=[]),
-  If(
-   test=Call(
-    func=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='is_not_allowed',
-     ctx=Load()),
-    args=[
-     Attribute(
-      value=Name(id='cookie', ctx=Load()),
-      attr='domain',
-      ctx=Load())],
-    keywords=[]),
-   body=[
...(截断)
```

**`deepvalues`**（源 L1227 ↔ 产物 L1000）

```diff
-       value=Constant(value=True)),
-      Expr(
-       value=YieldFrom(
-        value=Call(
-         func=Name(id='deepvalues', ctx=Load()),
-         args=[
-          Name(id='obj', ctx=Load())],
-         keywords=[])))],
+       value=Constant(value=True))],
+    Expr(
+     value=YieldFrom(
+      value=Call(
+       func=Name(id='deepvalues', ctx=Load()),
+       args=[
...(截断)
```

**`CookieJar.add_cookie_header`**（源 L1356 ↔ 产物 L1100）

```diff
-       ctx=Store()),
-      Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='_now',
+    Assign(
+     targets=[
+      Attribute(
+       value=Name(id='self', ctx=Load()),
+       attr='_now',
+       ctx=Store())],
+     value=Constant(value=None)),
-     test=Name(id='attrs', ctx=Load()),
-     body=[
-      If(
...(截断)
```

**`CookieJar._normalized_cookie_tuples`**（源 L1389 ↔ 产物 L1124）

```diff
-       orelse=[]),
-      If(
-       test=Compare(
-        left=Name(id='k', ctx=Load()),
-        ops=[
-         Eq()],
-        comparators=[
-         Constant(value='domain')]),
-       body=[
+       orelse=[
-          left=Name(id='v', ctx=Load()),
-          ops=[
-           Is()],
-          comparators=[
...(截断)
```

**`CookieJar.make_cookies`**（源 L1599 ↔ 产物 L1267）

```diff
-     ctx=Store()),
-    Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='_now',
+    Attribute(
+     value=Name(id='self', ctx=Load()),
+     attr='_now',
+     ctx=Store())],
+   value=Constant(value=None)),
+  Assign(
+   targets=[
-    op=Or(),
+    op=And(),
-      op=And(),
...(截断)
```

**`CookieJar.set_cookie_if_ok`**（源 L1654 ↔ 产物 L1303）

```diff
-       ctx=Store()),
-      Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='_now',
+    Assign(
+     targets=[
+      Attribute(
+       value=Name(id='self', ctx=Load()),
+       attr='_now',
+       ctx=Store())],
+     value=Constant(value=None)),
```

**`CookieJar.clear`**（源 L1692 ↔ 产物 L1338）

```diff
-     test=BoolOp(
-      op=Or(),
-      values=[
-       Compare(
-        left=Name(id='domain', ctx=Load()),
+     test=Compare(
+      left=Name(id='domain', ctx=Load()),
+      ops=[
+       IsNot()],
+      comparators=[
+       Constant(value=None)]),
+     body=[
+      If(
+       test=Compare(
...(截断)
```

**`FileCookieJar.revert`**（源 L1804 ↔ 产物 L1444）

```diff
-     finalbody=[])],
+     finalbody=[]),
+    Expr(
+     value=Call(
+      func=Attribute(
+       value=Attribute(
+        value=Name(id='self', ctx=Load()),
+        attr='_cookies_lock',
+        ctx=Load()),
+       attr='release',
+       ctx=Load()),
+      args=[],
+      keywords=[])),
+    Return(
...(截断)
```

**`LWPCookieJar.as_lwp_str`**（源 L1872 ↔ 产物 L1511）

```diff
-   value=Constant(value='Return cookies as a string of "\\n"-separated "Set-Cookie3" headers.\n\n        ignore_discard and ignore_expires: see docstring for FileCookieJar.save\n\n        ')),
+   value=Constant(value='Return cookies as a string of "\n"-separated "Set-Cookie3" headers.\n\n        ignore_discard and ignore_expires: see docstring for FileCookieJar.save\n\n        ')),
-     test=BoolOp(
-      op=And(),
-      values=[
-       UnaryOp(
-        op=Not(),
-        operand=Name(id='ignore_discard', ctx=Load())),
-       Attribute(
+     test=UnaryOp(
+      op=Not(),
+      operand=Name(id='ignore_discard', ctx=Load())),
+     body=[
+      If(
...(截断)
```

**`MozillaCookieJar.save`**（源 L2087 ↔ 产物 L1677）

```diff
-       test=BoolOp(
-        op=And(),
-        values=[
-         UnaryOp(
-          op=Not(),
-          operand=Name(id='ignore_discard', ctx=Load())),
-         Attribute(
+       test=UnaryOp(
+        op=Not(),
+        operand=Name(id='ignore_discard', ctx=Load())),
+       body=[
+        If(
+         test=Attribute(
-          ctx=Load())]),
...(截断)
```

## `stdlib_ipaddress`（判据 failure）

- 源：`D:\Python\Lib\ipaddress.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_ipaddressOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_find_address_range` | L164 | L137 | （指纹一致） |
| `_BaseNetwork.address_exclude` | L796 | L649 | fstring: 源=0 产物=5；return: 源=1 产物=3；常量数: 源=7 产物=15；仅源常量: '%s and %s are not of the same version', '%s not contained in %s', '%s/%s', 'Error performing exclusion: s1: %s s2: %s other: %s'；仅产物常量: ' and ', ' are not of the same version', ' not contained in ', ' other: ', ' s2: ', '/', 'Error performing exclusion: s1: ', None |
| `_BaseNetwork.is_private.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`_find_address_range`**（源 L164 ↔ 产物 L137）

```diff
-    Name(id='first', ctx=Store()),
-    Name(id='last', ctx=Store())],
+    Name(id='first', ctx=Store())],
```

**`_BaseNetwork.address_exclude`**（源 L796 ↔ 产物 L649）

```diff
-       BinOp(
-        left=Constant(value='%s and %s are not of the same version'),
-        op=Mod(),
-        right=Tuple(
-         elts=[
-          Name(id='self', ctx=Load()),
-          Name(id='other', ctx=Load())],
-         ctx=Load()))],
+       JoinedStr(
+        values=[
+         FormattedValue(
+          value=Name(id='self', ctx=Load()),
+          conversion=115),
+         Constant(value=' and '),
...(截断)
```

## `stdlib_json_encoder`（判据 failure）

- 源：`D:\Python\Lib\json\encoder.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_json_encoderOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_make_iterencode` | L260 | L213 | continue: 源=1 产物=15；return: 源=3 产物=17；yield: 源=30 产物=25；常量数: 源=60 产物=73；仅源常量: ']', '{', '}' |
| `_make_iterencode._iterencode_list` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_make_iterencode._iterencode_dict` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`_make_iterencode`**（源 L260 ↔ 产物 L213）

```diff
-      Return()],
-     orelse=[]),
-    If(
-     test=Compare(
-      left=Name(id='markers', ctx=Load()),
-      ops=[
-       IsNot()],
-      comparators=[
-       Constant(value=None)]),
-     body=[
-      Assign(
-       targets=[
-        Name(id='markerid', ctx=Store())],
-       value=Call(
...(截断)
```

## `stdlib_re__parser`（判据 failure）

- 源：`D:\Python\Lib\re\_parser.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_re__parserOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `SubPattern.getwidth` | L178 | L124 | continue: 源=0 产物=7 |
| `Tokenizer.getuntil` | L274 | L225 | break: 源=1 产物=2；常量数: 源=7 产物=6；仅源常量: None |
| `_class_escape` | L316 | L263 | 常量数: 源=38 产物=39 |
| `_escape` | L376 | L315 | 常量数: 源=46 产物=47；仅源常量: 4 |
| `_parse_sub` | L456 | L381 | break: 源=6 产物=5；continue: 源=1 产物=4；常量数: 源=16 产物=15；仅源常量: '|' |
| `_parse` | L516 | L427 | boolop: 源=13 产物=15；break: 源=6 产物=10；continue: 源=9 产物=7；fstring: 源=0 产物=4；namedexpr: 源=0 产物=1；常量数: 源=205 产物=204；仅源常量: 'Possible set %s at position %d', 'Possible set difference at position %d' |
| `_parse_flags` | L903 | L729 | assert: 源=1 产物=0；break: 源=2 产物=4；continue: 源=0 产物=2；常量数: 源=35 产物=32；仅源常量: 'bad inline flags: cannot turn off global flag' |
| `parse_template.<listcomp>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`SubPattern.getwidth`**（源 L178 ↔ 产物 L124）

```diff
-    Name(id='lo', ctx=Store()),
-    Name(id='hi', ctx=Store())],
+    Name(id='lo', ctx=Store())],
-        right=Name(id='j', ctx=Load())))],
+        right=Name(id='j', ctx=Load()))),
+      Continue()],
-          Tuple(
-           elts=[
-            Name(id='i', ctx=Store()),
-            Name(id='j', ctx=Store())],
-           ctx=Store())],
+          Name(id='i', ctx=Store())],
-          right=Name(id='j', ctx=Load())))],
+          right=Name(id='j', ctx=Load()))),
...(截断)
```

**`Tokenizer.getuntil`**（源 L274 ↔ 产物 L225）

```diff
-       attr='__next',
+       attr='_Tokenizer__next',
-     test=Compare(
-      left=Name(id='c', ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Constant(value=None)]),
+     test=Name(id='c', ctx=Load()),
+      If(
+       test=Compare(
+        left=Name(id='c', ctx=Load()),
+        ops=[
+         Eq()],
...(截断)
```

**`_class_escape`**（源 L316 ↔ 产物 L263）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='code', ctx=Store())],
-   value=Call(
-    func=Attribute(
-     value=Name(id='CATEGORIES', ctx=Load()),
-     attr='get',
-     ctx=Load()),
-    args=[
-     Name(id='escape', ctx=Load())],
-    keywords=[])),
-  If(
-   test=BoolOp(
...(截断)
```

**`_escape`**（源 L376 ↔ 产物 L315）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='code', ctx=Store())],
-   value=Call(
-    func=Attribute(
-     value=Name(id='ESCAPES', ctx=Load()),
-     attr='get',
-     ctx=Load()),
-    args=[
-     Name(id='escape', ctx=Load())],
-    keywords=[])),
-  If(
-   test=Name(id='code', ctx=Load()),
...(截断)
```

**`_parse_sub`**（源 L456 ↔ 产物 L381）

```diff
-    If(
-     test=UnaryOp(
-      op=Not(),
-      operand=Call(
-       func=Name(id='sourcematch', ctx=Load()),
-       args=[
-        Constant(value='|')],
-       keywords=[])),
-     body=[
-      Break()],
-     orelse=[]),
+    Break(),
-       orelse=[]),
+       orelse=[
...(截断)
```

**`_parse`**（源 L516 ↔ 产物 L427）

```diff
-     test=Compare(
-      left=Name(id='this', ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Constant(value=None)]),
+     test=UnaryOp(
+      op=Not(),
+      operand=Compare(
+       left=Name(id='this', ctx=Load()),
+       ops=[
+        IsNot()],
+       comparators=[
+        Constant(value=None)])),
...(截断)
```

**`_parse_flags`**（源 L903 ↔ 产物 L729）

```diff
-         orelse=[])]),
+         orelse=[
+          Break()])]),
-       orelse=[]),
+       orelse=[
+        Break()]),
-       orelse=[]),
-      If(
-       test=Compare(
-        left=Name(id='char', ctx=Load()),
-        ops=[
-         In()],
-        comparators=[
-         Constant(value=')-:')]),
...(截断)
```

## `stdlib_statistics`（判据 failure）

- 源：`D:\Python\Lib\statistics.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_statisticsOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_sum` | L154 | L125 | （指纹一致） |
| `_ss` | L208 | L174 | （指纹一致） |
| `_exact_ratio` | L287 | L243 | assert: 源=1 产物=0；raise: 源=1 产物=2；return: 源=3 产物=4；常量数: 源=4 产物=5 |
| `harmonic_mean` | L493 | L392 | （指纹一致） |
| `NormalDist.samples` | L1192 | L934 | （指纹一致） |
| `NormalDist.samples.<listcomp>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |

### AST 结构差分（源 vs 产物）

**`_sum`**（源 L154 ↔ 产物 L125）

```diff
-     test=UnaryOp(
-      op=Not(),
-      operand=Call(
-       func=Name(id='_isfinite', ctx=Load()),
-       args=[
-        Name(id='total', ctx=Load())],
-       keywords=[])))],
+     test=Call(
+      func=Name(id='_isfinite', ctx=Load()),
+      args=[
+       Name(id='total', ctx=Load())],
+      keywords=[]))],
```

**`_ss`**（源 L208 ↔ 产物 L174）

```diff
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='count', ctx=Store())],
-   value=Constant(value=0)),
-  Assign(
-   targets=[
-    Name(id='types', ctx=Store())],
-   value=Call(
-    func=Name(id='set', ctx=Load()),
-    args=[],
-    keywords=[])),
-  Assign(
-   targets=[
...(截断)
```

**`_exact_ratio`**（源 L287 ↔ 产物 L243）

```diff
-      Assert(
-       test=UnaryOp(
-        op=Not(),
-        operand=Call(
-         func=Name(id='_isfinite', ctx=Load()),
-         args=[
-          Name(id='x', ctx=Load())],
-         keywords=[]))),
+      If(
+       test=Call(
+        func=Name(id='_isfinite', ctx=Load()),
+        args=[
+         Name(id='x', ctx=Load())],
+        keywords=[]),
...(截断)
```

**`harmonic_mean`**（源 L493 ↔ 产物 L392）

```diff
-     orelse=[])]),
-  If(
-   test=Compare(
-    left=Name(id='weights', ctx=Load()),
-    ops=[
-     Is()],
-    comparators=[
-     Constant(value=None)]),
-   body=[
-    Assign(
-     targets=[
-      Name(id='weights', ctx=Store())],
-     value=Call(
-      func=Name(id='repeat', ctx=Load()),
...(截断)
```

**`NormalDist.samples`**（源 L1192 ↔ 产物 L934）

```diff
-    Tuple(
-     elts=[
-      Name(id='mu', ctx=Store()),
-      Name(id='sigma', ctx=Store())],
-     ctx=Store())],
-   value=Tuple(
-    elts=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_mu',
-      ctx=Load()),
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_sigma',
...(截断)
```

## `stdlib_subprocess`（判据 failure）

- 源：`D:\Python\Lib\subprocess.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_subprocessOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `call` | L381 | L253 | star_args: 源=1 产物=0 |
| `run` | L506 | L357 | boolop: 源=2 产物=1；star_args: 源=1 产物=0 |
| `Popen.__init__` | L807 | L597 | boolop: 源=5 产物=4；continue: 源=0 产物=2；raise: 源=21 产物=20；常量数: 源=99 产物=97；仅源常量: 0.25 |
| `Popen.__exit__` | L1092 | L767 | return: 源=1 产物=2；常量数: 源=2 产物=4；仅产物常量: None |
| `Popen._check_timeout` | L1247 | L888 | raise: 源=1 产物=0；常量数: 源=7 产物=8 |
| `Popen._on_error_fd_closer` | L1312 | L933 | return: 源=0 产物=1；常量数: 源=2 产物=3；仅产物常量: None |
| `Popen._execute_child` | L1789 | L1261 | boolop: 源=6 产物=7；break: 源=1 产物=2；常量数: 源=44 产物=45；仅源常量: b'0' |
| `Popen._execute_child` | L1789 | L1261 | boolop: 源=6 产物=7；break: 源=1 产物=2；常量数: 源=44 产物=45；仅源常量: b'0' |
| `Popen._internal_poll` | L1966 | L1361 | 常量数: 源=8 产物=7 |
| `Popen._wait` | L2014 | L1394 | break: 源=3 产物=2；raise: 源=1 产物=2；常量数: 源=14 产物=13；仅源常量: 0.05, 2 |

### AST 结构差分（源 vs 产物）

**`call`**（源 L381 ↔ 产物 L253）

```diff
-     context_expr=Call(
-      func=Name(id='Popen', ctx=Load()),
-      args=[
-       Starred(
-        value=Name(id='popenargs', ctx=Load()),
-        ctx=Load())],
-      keywords=[
-       keyword(
-        value=Name(id='kwargs', ctx=Load()))]),
+     context_expr=Name(id='kwargs', ctx=Load()),
```

**`run`**（源 L506 ↔ 产物 L357）

```diff
-     test=BoolOp(
-      op=Or(),
-      values=[
-       Compare(
-        left=Call(
-         func=Attribute(
-          value=Name(id='kwargs', ctx=Load()),
-          attr='get',
-          ctx=Load()),
-         args=[
-          Constant(value='stdout')],
-         keywords=[]),
-        ops=[
-         IsNot()],
...(截断)
```

**`Popen.__init__`**（源 L807 ↔ 产物 L597）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='pipesize', ctx=Load()),
-    ops=[
-     Is()],
-    comparators=[
-     Constant(value=None)]),
-   body=[
-    Assign(
-     targets=[
-      Name(id='pipesize', ctx=Store())],
-     value=UnaryOp(
-      op=USub(),
...(截断)
```

**`Popen.__exit__`**（源 L1092 ↔ 产物 L767）

```diff
-      Return()],
-     orelse=[]),
-    Expr(
-     value=Call(
-      func=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='wait',
-       ctx=Load()),
-      args=[],
-      keywords=[]))])],
+      Return(
+       value=Constant(value=None))],
+     orelse=[
+      Expr(
...(截断)
```

**`Popen._check_timeout`**（源 L1247 ↔ 产物 L888）

```diff
-    Return()],
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=Or(),
-    values=[
-     Name(id='skip_check_and_raise', ctx=Load()),
-     Compare(
-      left=Call(
-       func=Name(id='_time', ctx=Load()),
-       args=[],
-       keywords=[]),
-      ops=[
-       Gt()],
...(截断)
```

**`Popen._on_error_fd_closer`**（源 L1312 ↔ 产物 L933）

```diff
-      value=Name(id='to_close', ctx=Load())))],
+      value=Name(id='to_close', ctx=Load()))),
+    Return(
+     value=Constant(value=None))],
-       orelse=[]),
-      For(
-       target=Name(id='fd', ctx=Store()),
-       iter=Name(id='to_close', ctx=Load()),
-       body=[
-        Try(
+       orelse=[
+        For(
+         target=Name(id='fd', ctx=Store()),
+         iter=Name(id='to_close', ctx=Load()),
...(截断)
```

**`Popen._execute_child`**（源 L1789 ↔ 产物 L1261）

```diff
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='close_fds', ctx=Load())),
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='pass_fds', ctx=Load())),
-     Compare(
-      left=Name(id='cwd', ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Constant(value=None)]),
+     BoolOp(
+      op=Or(),
...(截断)
```

**`Popen._execute_child`**（源 L1789 ↔ 产物 L1261）

```diff
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='close_fds', ctx=Load())),
-     UnaryOp(
-      op=Not(),
-      operand=Name(id='pass_fds', ctx=Load())),
-     Compare(
-      left=Name(id='cwd', ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Constant(value=None)]),
+     BoolOp(
+      op=Or(),
...(截断)
```

**`Popen._internal_poll`**（源 L1966 ↔ 产物 L1361）

```diff
-     orelse=[]),
-    Try(
-     body=[
-      If(
-       test=Compare(
-        left=Attribute(
-         value=Name(id='self', ctx=Load()),
-         attr='returncode',
-         ctx=Load()),
-        ops=[
-         IsNot()],
-        comparators=[
-         Constant(value=None)]),
+     orelse=[
...(截断)
```

**`Popen._wait`**（源 L2014 ↔ 产物 L1394）

```diff
-   orelse=[]),
-  If(
+   orelse=[
+    If(
+     test=Compare(
+      left=Name(id='timeout', ctx=Load()),
+      ops=[
+       IsNot()],
+      comparators=[
+       Constant(value=None)]),
+     body=[
+      Assign(
+       targets=[
+        Name(id='endtime', ctx=Store())],
...(截断)
```

## `stdlib_tarfile`（判据 failure）

- 源：`D:\Python\Lib\tarfile.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_tarfileOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `itn` | L196 | L102 | boolop: 源=1 产物=0 |
| `copyfileobj` | L239 | L134 | boolop: 源=1 产物=2；常量数: 源=10 产物=12；仅源常量: 1024, 16；仅产物常量: 16384 |
| `_Stream.__init__` | L343 | L210 | return: 源=0 产物=7；常量数: 源=27 产物=34 |
| `_Stream._init_read_gz` | L474 | L330 | boolop: 源=2 产物=0；break: 源=2 产物=3；return: 源=0 产物=1；常量数: 源=22 产物=23；仅产物常量: None |
| `_Stream._read` | L530 | L386 | （指纹一致） |
| `_FileInFile.read` | L668 | L503 | break: 源=1 产物=0；continue: 源=0 产物=1；while: 源=2 产物=1 |
| `tar_filter` | L819 | L616 | 常量数: 源=2 产物=3；仅产物常量: 'deep' |
| `data_filter` | L825 | L622 | 常量数: 源=2 产物=3；仅产物常量: 'deep' |
| `TarInfo.create_pax_header` | L1024 | L744 | （指纹一致） |
| `TarFile.__init__` | L1643 | L1164 | return: 源=0 产物=1；常量数: 源=52 产物=53 |
| `TarFile.close` | L1956 | L1412 | 常量数: 源=8 产物=9；仅产物常量: None |
| `TarFile.gettarinfo` | L2004 | L1452 | （指纹一致） |
| `TarFile.list` | L2103 | L1528 | boolop: 源=3 产物=1；常量数: 源=18 产物=17；仅源常量: '%s/%s' |
| `TarFile.add` | L2141 | L1563 | return: 源=3 产物=5；常量数: 源=18 产物=23 |
| `TarFile.next` | L2581 | L1925 | break: 源=1 产物=2 |
| `TarFile._getmember` | L2646 | L1983 | （指纹一致） |
| `TarFile._load` | L2686 | L2012 | return: 源=0 产物=1 |
| `TarFile._check` | L2696 | L2021 | boolop: 源=1 产物=0；return: 源=0 产物=1；常量数: 源=5 产物=6 |
| `main` | L2800 | L2105 | return: 源=0 产物=8；with: 源=4 产物=3；常量数: 源=74 产物=82 |

### AST 结构差分（源 vs 产物）

**`itn`**（源 L196 ↔ 产物 L102）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       Compare(
-        left=Name(id='format', ctx=Load()),
-        ops=[
-         Eq()],
-        comparators=[
-         Name(id='GNU_FORMAT', ctx=Load())]),
-       Compare(
+     test=Compare(
+      left=Name(id='format', ctx=Load()),
+      ops=[
+       Eq()],
...(截断)
```

**`copyfileobj`**（源 L239 ↔ 产物 L134）

```diff
-     BinOp(
-      left=Constant(value=16),
-      op=Mult(),
-      right=Constant(value=1024))])),
+     Constant(value=16384)])),
-   test=Compare(
-    left=Name(id='length', ctx=Load()),
-    ops=[
-     Eq()],
-    comparators=[
-     Constant(value=0)]),
+   test=BoolOp(
+    op=Or(),
+    values=[
...(截断)
```

**`_Stream.__init__`**（源 L343 ↔ 产物 L210）

```diff
-          keywords=[]))],
+          keywords=[])),
+        Return(
+         value=Constant(value=None))],
-          keywords=[]))])],
+          keywords=[])),
+        Return(
+         value=Constant(value=None))])],
-           value=Name(id='OSError', ctx=Load()))],
+           value=Name(id='OSError', ctx=Load())),
+          Return(
+           value=Constant(value=None))],
-            keywords=[]))])],
+            keywords=[])),
...(截断)
```

**`_Stream._init_read_gz`**（源 L474 ↔ 产物 L330）

```diff
-      attr='__read',
+      attr='_Stream__read',
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Call(
-     func=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='__read',
-      ctx=Load()),
-     args=[
-      Constant(value=1)],
-     keywords=[]),
-    ops=[
...(截断)
```

**`_Stream._read`**（源 L530 ↔ 产物 L386）

```diff
-       attr='__read',
+       attr='_Stream__read',
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='c', ctx=Store())],
-   value=Call(
-    func=Name(id='len', ctx=Load()),
-    args=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='dbuf',
-      ctx=Load())],
-    keywords=[])),
...(截断)
```

**`_FileInFile.read`**（源 L668 ↔ 产物 L503）

```diff
-  While(
+  If(
-         LtE(),
-         Lt()],
+         LtE()],
-          ctx=Load()),
-         Name(id='stop', ctx=Load())]),
+          ctx=Load())]),
-        Break()],
+        Pass()],
+       orelse=[
+        Pass()]),
+      AugAssign(
+       target=Attribute(
...(截断)
```

**`tar_filter`**（源 L819 ↔ 产物 L616）

```diff
-        value=Name(id='new_attrs', ctx=Load())),
-       keyword(
-        arg='deep',
-        value=Constant(value=False))]))],
-   orelse=[]),
-  Return(
-   value=Name(id='member', ctx=Load()))],
+        value=Dict(
+         keys=[
+          Constant(value='deep')],
+         values=[
+          Constant(value=False)]))]))],
+   orelse=[
+    Return(
...(截断)
```

**`data_filter`**（源 L825 ↔ 产物 L622）

```diff
-        value=Name(id='new_attrs', ctx=Load())),
-       keyword(
-        arg='deep',
-        value=Constant(value=False))]))],
-   orelse=[]),
-  Return(
-   value=Name(id='member', ctx=Load()))],
+        value=Dict(
+         keys=[
+          Constant(value='deep')],
+         values=[
+          Constant(value=False)]))]))],
+   orelse=[
+    Return(
...(截断)
```

**`TarInfo.create_pax_header`**（源 L1024 ↔ 产物 L744）

```diff
-     orelse=[
-      If(
-       test=Name(id='val_is_float', ctx=Load()),
-       body=[
-        Assign(
-         targets=[
-          Subscript(
-           value=Name(id='info', ctx=Load()),
-           slice=Name(id='name', ctx=Load()),
-           ctx=Store())],
-         value=Name(id='val_int', ctx=Load())),
-        Assign(
-         targets=[
-          Name(id='needs_pax', ctx=Store())],
...(截断)
```

**`TarFile.__init__`**（源 L1643 ↔ 产物 L1164）

```diff
-       orelse=[])],
-     orelse=[]),
-    If(
-     test=Compare(
-      left=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='mode',
-       ctx=Load()),
-      ops=[
-       In()],
-      comparators=[
-       Tuple(
-        elts=[
-         Constant(value='a'),
...(截断)
```

**`TarFile.close`**（源 L1956 ↔ 产物 L1412）

```diff
-    Return()],
+    Return(
+     value=Constant(value=None))],
-          left=Name(id='NUL', ctx=Load()),
+          left=BinOp(
+           left=Name(id='NUL', ctx=Load()),
+           op=Mult(),
+           right=Name(id='BLOCKSIZE', ctx=Load())),
-          right=BinOp(
-           left=Name(id='BLOCKSIZE', ctx=Load()),
-           op=Mult(),
-           right=Constant(value=2)))],
+          right=Constant(value=2))],
```

**`TarFile.gettarinfo`**（源 L2004 ↔ 产物 L1452）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       UnaryOp(
-        op=Not(),
-        operand=Attribute(
-         value=Name(id='self', ctx=Load()),
-         attr='dereference',
-         ctx=Load())),
-       Compare(
-        left=Attribute(
-         value=Name(id='statres', ctx=Load()),
-         attr='st_nlink',
-         ctx=Load()),
...(截断)
```

**`TarFile.list`**（源 L2103 ↔ 产物 L1528）

```diff
-       value=Call(
-        func=Name(id='_safe_print', ctx=Load()),
-        args=[
-         BinOp(
-          left=Constant(value='%s/%s'),
-          op=Mod(),
-          right=Tuple(
-           elts=[
-            BoolOp(
-             op=Or(),
-             values=[
-              Attribute(
-               value=Name(id='tarinfo', ctx=Load()),
-               attr='uname',
...(截断)
```

**`TarFile.add`**（源 L2141 ↔ 产物 L1563）

```diff
-    Return()],
+    Return(
+     value=Constant(value=None))],
-    Return()],
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Name(id='filter', ctx=Load()),
-    ops=[
-     IsNot()],
-    comparators=[
-     Constant(value=None)]),
-   body=[
-    Assign(
...(截断)
```

**`TarFile.next`**（源 L2581 ↔ 产物 L1925）

```diff
-   orelse=[]),
-  If(
-   test=Compare(
-    left=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='offset',
-     ctx=Load()),
-    ops=[
-     NotEq()],
-    comparators=[
-     Call(
-      func=Attribute(
-       value=Attribute(
-        value=Name(id='self', ctx=Load()),
...(截断)
```

**`TarFile._getmember`**（源 L2646 ↔ 产物 L1983）

```diff
-       orelse=[]),
-      Continue()],
-     orelse=[]),
-    If(
-     test=Name(id='normalize', ctx=Load()),
-     body=[
-      Assign(
-       targets=[
-        Name(id='member_name', ctx=Store())],
-       value=Call(
-        func=Attribute(
+       orelse=[
+        Continue()])],
+     orelse=[
...(截断)
```

**`TarFile._load`**（源 L2686 ↔ 产物 L2012）

```diff
-    Assign(
-     targets=[
-      Name(id='tarinfo', ctx=Store())],
-     value=Call(
-      func=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='next',
-       ctx=Load()),
-      args=[],
-      keywords=[])),
-     test=Compare(
-      left=Name(id='tarinfo', ctx=Load()),
-      ops=[
-       Is()],
...(截断)
```

**`TarFile._check`**（源 L2696 ↔ 产物 L2021）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
+   orelse=[
+    If(
+     test=Compare(
-     Compare(
-      left=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='mode',
-       ctx=Load()),
...(截断)
```

**`main`**（源 L2800 ↔ 产物 L2105）

```diff
-          keywords=[]))],
-       orelse=[])],
+          keywords=[])),
+        Return(
+         value=Constant(value=None))],
+       orelse=[
+        Return(
+         value=Constant(value=None))])],
-        keywords=[]))])],
+        keywords=[])),
+      Return(
+       value=Constant(value=None))])],
-          keywords=[]))])],
+          keywords=[])),
...(截断)
```

## `stdlib_tomllib_parser`（判据 failure）

- 源：`D:\Python\Lib\tomllib\_parser.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_tomllib_parserOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `loads` | L69 | L36 | ann_args: 源=2 产物=0；params: 源=1 产物=2；posonly: 源=1 产物=0；returns_ann: 源=1 产物=0；常量数: 源=17 产物=16 |
| `Flags` | L135 | L81 | return: 源=6 产物=7；slice: 源=3 产物=2；常量数: 源=34 产物=29 |
| `Flags.set` | L164 | L103 | ann_args: 源=3 产物=0；return: 源=0 产物=1；returns_ann: 源=1 产物=0；slice: 源=1 产物=0；常量数: 源=12 产物=10；仅源常量: None |
| `Flags.is_` | L175 | L113 | ann_args: 源=2 产物=0；return: 源=5 产物=4；returns_ann: 源=1 产物=0；常量数: 源=10 产物=9 |
| `NestedDict` | L193 | L130 | return: 源=1 产物=2；常量数: 源=8 产物=7 |
| `Output` | L227 | L155 | 常量数: 源=0 产物=2；仅产物常量: 'Flags', 'NestedDict' |
| `key_value_rule` | L323 | L223 | ann_args: 源=5 产物=0；returns_ann: 源=1 产物=0；slice: 源=2 产物=1；常量数: 源=9 产物=8 |
| `parse_inline_table` | L436 | L310 | ann_args: 源=3 产物=0；returns_ann: 源=1 产物=0；slice: 源=2 产物=1；常量数: 源=18 产物=17 |
| `parse_basic_str` | L552 | L406 | ann_args: 源=3 产物=0；continue: 源=2 产物=3；returns_ann: 源=1 产物=0 |
| `suffixed_err` | L652 | L488 | ann_args: 源=3 产物=0；returns_ann: 源=1 产物=0 |
| `make_safe_parse_float` | L673 | L506 | ann_args: 源=1 产物=0；returns_ann: 源=1 产物=0 |

### AST 结构差分（源 vs 产物）

**`loads`**（源 L69 ↔ 产物 L36）

```diff
-  posonlyargs=[
-   arg(
-    arg='s',
-    annotation=Name(id='str', ctx=Load()))],
-  args=[],
+  posonlyargs=[],
+  args=[
+   arg(arg='s')],
-   arg(
-    arg='parse_float',
-    annotation=Name(id='ParseFloat', ctx=Load()))],
+   arg(arg='parse_float')],
-  AnnAssign(
-   target=Name(id='header', ctx=Store()),
...(截断)
```

**`Flags`**（源 L135 ↔ 产物 L81）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_flags',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='dict', ctx=Load()),
-      slice=Tuple(
-       elts=[
-        Name(id='str', ctx=Load()),
...(截断)
```

**`Flags.set`**（源 L164 ↔ 产物 L103）

```diff
-   arg(
-    arg='key',
-    annotation=Name(id='Key', ctx=Load())),
-   arg(
-    arg='flag',
-    annotation=Name(id='int', ctx=Load()))],
+   arg(arg='key'),
+   arg(arg='flag')],
-   arg(
-    arg='recursive',
-    annotation=Name(id='bool', ctx=Load()))],
+   arg(arg='recursive')],
-    Tuple(
-     elts=[
...(截断)
```

**`Flags.is_`**（源 L175 ↔ 产物 L113）

```diff
-   arg(
-    arg='key',
-    annotation=Name(id='Key', ctx=Load())),
-   arg(
-    arg='flag',
-    annotation=Name(id='int', ctx=Load()))],
+   arg(arg='key'),
+   arg(arg='flag')],
-   orelse=[]),
-  Assign(
-   targets=[
-    Name(id='cont', ctx=Store())],
-   value=Attribute(
-    value=Name(id='self', ctx=Load()),
...(截断)
```

**`NestedDict`**（源 L193 ↔ 产物 L130）

```diff
-    AnnAssign(
-     target=Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='dict',
-      ctx=Store()),
-     annotation=Subscript(
-      value=Name(id='dict', ctx=Load()),
-      slice=Tuple(
-       elts=[
-        Name(id='str', ctx=Load()),
-        Name(id='Any', ctx=Load())],
-       ctx=Load()),
-      ctx=Load()),
-     value=Dict(keys=[], values=[]),
...(截断)
```

**`Output`**（源 L227 ↔ 产物 L155）

```diff
-   annotation=Name(id='NestedDict', ctx=Load()),
+   annotation=Constant(value='NestedDict'),
-   annotation=Name(id='Flags', ctx=Load()),
+   annotation=Constant(value='Flags'),
```

**`key_value_rule`**（源 L323 ↔ 产物 L223）

```diff
-   arg(
-    arg='src',
-    annotation=Name(id='str', ctx=Load())),
-   arg(
-    arg='pos',
-    annotation=Name(id='Pos', ctx=Load())),
-   arg(
-    arg='out',
-    annotation=Name(id='Output', ctx=Load())),
-   arg(
-    arg='header',
-    annotation=Name(id='Key', ctx=Load())),
-   arg(
-    arg='parse_float',
...(截断)
```

**`parse_inline_table`**（源 L436 ↔ 产物 L310）

```diff
-   arg(
-    arg='src',
-    annotation=Name(id='str', ctx=Load())),
-   arg(
-    arg='pos',
-    annotation=Name(id='Pos', ctx=Load())),
-   arg(
-    arg='parse_float',
-    annotation=Name(id='ParseFloat', ctx=Load()))],
+   arg(arg='src'),
+   arg(arg='pos'),
+   arg(arg='parse_float')],
-   orelse=[]),
-  While(
...(截断)
```

**`parse_basic_str`**（源 L552 ↔ 产物 L406）

```diff
-   arg(
-    arg='src',
-    annotation=Name(id='str', ctx=Load())),
-   arg(
-    arg='pos',
-    annotation=Name(id='Pos', ctx=Load()))],
+   arg(arg='src'),
+   arg(arg='pos')],
-   arg(
-    arg='multiline',
-    annotation=Name(id='bool', ctx=Load()))],
+   arg(arg='multiline')],
-       orelse=[]),
+       orelse=[
...(截断)
```

**`suffixed_err`**（源 L652 ↔ 产物 L488）

```diff
-   arg(
-    arg='src',
-    annotation=Name(id='str', ctx=Load())),
-   arg(
-    arg='pos',
-    annotation=Name(id='Pos', ctx=Load())),
-   arg(
-    arg='msg',
-    annotation=Name(id='str', ctx=Load()))],
+   arg(arg='src'),
+   arg(arg='pos'),
+   arg(arg='msg')],
-     arg(
-      arg='src',
...(截断)
```

**`make_safe_parse_float`**（源 L673 ↔ 产物 L506）

```diff
-   arg(
-    arg='parse_float',
-    annotation=Name(id='ParseFloat', ctx=Load()))],
+   arg(arg='parse_float')],
-   orelse=[]),
-  FunctionDef(
-   name='safe_parse_float',
-   args=arguments(
-    posonlyargs=[],
-    args=[
-     arg(
-      arg='float_str',
-      annotation=Name(id='str', ctx=Load()))],
-    kwonlyargs=[],
...(截断)
```

## `stdlib_typing`（判据 failure）

- 源：`D:\Python\Lib\typing.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_typingOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_is_param_expr` | L201 | L80 | 仅源常量: Ellipsis；仅产物常量: None |
| `_should_unflatten_callable_args` | L206 | L82 | boolop: 源=2 产物=1 |
| `_type_repr` | L230 | L101 | 仅源常量: Ellipsis；仅产物常量: None |
| `_check_generic` | L284 | L154 | raise: 源=2 产物=1 |
| `_unpack_args` | L296 | L164 | boolop: 源=2 产物=1；continue: 源=0 产物=1；仅源常量: Ellipsis |
| `_deduplicate` | L306 | L175 | （指纹一致） |
| `Concatenate` | L768 | L567 | 仅源常量: Ellipsis；仅产物常量: None |
| `TypeVarTuple.__typing_prepare_subst__` | L1091 | L837 | 仅源常量: Ellipsis |
| `ParamSpec.__typing_prepare_subst__` | L1238 | L963 | （指纹一致） |
| `_GenericAlias.__init__.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `_GenericAlias.__getitem__` | L1388 | L1053 | （指纹一致） |
| `_GenericAlias._determine_new_args` | L1419 | L1066 | raise: 源=1 产物=0 |
| `_GenericAlias.__mro_entries__` | L1536 | L1134 | return: 源=4 产物=5 |
| `_CallableGenericAlias.__reduce__` | L1612 | L1195 | boolop: 源=1 产物=0 |
| `_TupleType.__getitem__` | L1655 | L1227 | 仅源常量: Ellipsis；仅产物常量: None |
| `_ProtocolMeta.__instancecheck__` | L1990 | L1472 | boolop: 源=5 产物=4；常量数: 源=12 产物=11 |
| `_ProtocolMeta.__instancecheck__.<genexpr>` | — | — | 源码中未按 qualname 定位到（可能是模块级或嵌套 code object） |
| `Protocol.__init_subclass__` | L2052 | L1515 | boolop: 源=4 产物=3；break: 源=2 产物=4；continue: 源=0 产物=1；return: 源=7 产物=9；常量数: 源=14 产物=17 |
| `_make_nmtuple` | L2872 | L2178 | 常量数: 源=2 产物=3；仅产物常量: None |
| `NamedTupleMeta.__new__` | L2891 | L2188 | continue: 源=0 产物=2；raise: 源=3 产物=2 |
| `IO` | L3233 | L2460 | return: 源=0 产物=20；常量数: 源=11 产物=27；仅源常量: 'IO[AnyStr]' |
| `BinaryIO` | L3332 | L2536 | return: 源=0 产物=2；常量数: 源=2 产物=3；仅源常量: 'BinaryIO'；仅产物常量: None |
| `TextIO` | L3346 | L2545 | return: 源=0 产物=6；常量数: 源=2 产物=7；仅源常量: 'TextIO'；仅产物常量: None |

### AST 结构差分（源 vs 产物）

**`_is_param_expr`**（源 L201 ↔ 产物 L80）

```diff
-       Constant(value=Ellipsis)]),
+       Constant(value=None)]),
```

**`_should_unflatten_callable_args`**（源 L206 ↔ 产物 L82）

```diff
-   value=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Attribute(
-       value=Name(id='typ', ctx=Load()),
-       attr='__origin__',
-       ctx=Load()),
-      ops=[
-       Is()],
-      comparators=[
-       Attribute(
-        value=Attribute(
-         value=Name(id='collections', ctx=Load()),
...(截断)
```

**`_type_repr`**（源 L230 ↔ 产物 L101）

```diff
-   orelse=[]),
-  If(
-   test=Call(
-    func=Name(id='isinstance', ctx=Load()),
-    args=[
-     Name(id='obj', ctx=Load()),
-     Name(id='type', ctx=Load())],
-    keywords=[]),
-   body=[
+   orelse=[
-     test=Compare(
-      left=Attribute(
-       value=Name(id='obj', ctx=Load()),
-       attr='__module__',
...(截断)
```

**`_check_generic`**（源 L284 ↔ 产物 L154）

```diff
-    Raise(
-     exc=Call(
-      func=Name(id='TypeError', ctx=Load()),
-      args=[
-       JoinedStr(
-        values=[
-         Constant(value='Too '),
-         FormattedValue(
-          value=IfExp(
-           test=Compare(
-            left=Name(id='alen', ctx=Load()),
-            ops=[
-             Gt()],
-            comparators=[
...(截断)
```

**`_unpack_args`**（源 L296 ↔ 产物 L164）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       Compare(
-        left=Name(id='subargs', ctx=Load()),
-        ops=[
-         IsNot()],
-        comparators=[
-         Constant(value=None)]),
-       UnaryOp(
+     test=Compare(
+      left=Name(id='subargs', ctx=Load()),
+      ops=[
+       IsNot()],
...(截断)
```

**`_deduplicate`**（源 L306 ↔ 产物 L175）

```diff
-     test=UnaryOp(
-      op=Not(),
-      operand=Name(id='all_params', ctx=Load())),
+     test=Name(id='all_params', ctx=Load()),
```

**`Concatenate`**（源 L768 ↔ 产物 L567）

```diff
-        Constant(value=Ellipsis)]),
+        Constant(value=None)]),
```

**`TypeVarTuple.__typing_prepare_subst__`**（源 L1091 ↔ 产物 L837）

```diff
-           Constant(value=Ellipsis)])]),
+           Constant(value=None)])]),
```

**`ParamSpec.__typing_prepare_subst__`**（源 L1238 ↔ 产物 L963）

```diff
-   orelse=[]),
-  If(
-   test=BoolOp(
-    op=And(),
-    values=[
-     Compare(
-      left=Call(
-       func=Name(id='len', ctx=Load()),
-       args=[
-        Name(id='params', ctx=Load())],
-       keywords=[]),
-      ops=[
-       Eq()],
-      comparators=[
...(截断)
```

**`_GenericAlias.__getitem__`**（源 L1388 ↔ 产物 L1053）

```diff
-   orelse=[]),
-  If(
-   test=UnaryOp(
-    op=Not(),
-    operand=Attribute(
-     value=Name(id='self', ctx=Load()),
-     attr='__parameters__',
-     ctx=Load())),
-   body=[
-    Raise(
-     exc=Call(
-      func=Name(id='TypeError', ctx=Load()),
-      args=[
-       JoinedStr(
...(截断)
```

**`_GenericAlias._determine_new_args`**（源 L1419 ↔ 产物 L1066）

```diff
-    Raise(
-     exc=Call(
-      func=Name(id='TypeError', ctx=Load()),
-      args=[
-       JoinedStr(
-        values=[
-         Constant(value='Too '),
-         FormattedValue(
-          value=IfExp(
-           test=Compare(
-            left=Name(id='alen', ctx=Load()),
-            ops=[
-             Gt()],
-            comparators=[
...(截断)
```

**`_GenericAlias.__mro_entries__`**（源 L1536 ↔ 产物 L1134）

```diff
-   orelse=[]),
-  If(
-   test=Attribute(
-    value=Name(id='self', ctx=Load()),
-    attr='_name',
-    ctx=Load()),
-   body=[
-    Return(
-     value=Call(
-      func=Attribute(
-       value=Call(
-        func=Name(id='super', ctx=Load()),
-        args=[],
-        keywords=[]),
...(截断)
```

**`_CallableGenericAlias.__reduce__`**（源 L1612 ↔ 产物 L1195）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=BoolOp(
-     op=And(),
-     values=[
-      Compare(
-       left=Call(
-        func=Name(id='len', ctx=Load()),
-        args=[
-         Name(id='args', ctx=Load())],
-        keywords=[]),
-       ops=[
-        Eq()],
-       comparators=[
...(截断)
```

**`_TupleType.__getitem__`**（源 L1655 ↔ 产物 L1227）

```diff
-       Constant(value=Ellipsis)])]),
+       Constant(value=None)])]),
```

**`_ProtocolMeta.__instancecheck__`**（源 L1990 ↔ 产物 L1472）

```diff
-   test=Attribute(
-    value=Name(id='cls', ctx=Load()),
-    attr='_is_protocol',
-    ctx=Load()),
-   body=[
-    If(
-     test=Call(
+   test=BoolOp(
+    op=And(),
+    values=[
+     Attribute(
+      value=Name(id='cls', ctx=Load()),
+      attr='_is_protocol',
+      ctx=Load()),
...(截断)
```

**`Protocol.__init_subclass__`**（源 L2052 ↔ 产物 L1515）

```diff
-     orelse=[]),
-    If(
-     test=UnaryOp(
-      op=Not(),
-      operand=Call(
-       func=Name(id='getattr', ctx=Load()),
-       args=[
-        Name(id='cls', ctx=Load()),
-        Constant(value='_is_runtime_protocol'),
-        Constant(value=False)],
-       keywords=[])),
-     body=[
+     orelse=[
-       test=Call(
...(截断)
```

**`_make_nmtuple`**（源 L2872 ↔ 产物 L2178）

```diff
-     ctx=Store()),
+     ctx=Store())],
+   value=Name(id='types', ctx=Load())),
+  Assign(
+   targets=[
-   value=Name(id='types', ctx=Load())),
+   value=Constant(value=None)),
```

**`NamedTupleMeta.__new__`**（源 L2891 ↔ 产物 L2188）

```diff
-        keywords=[]))],
+        keywords=[])),
+      Continue()],
-        Raise(
-         exc=Call(
-          func=Name(id='TypeError', ctx=Load()),
-          args=[
-           JoinedStr(
-            values=[
-             Constant(value='Non-default namedtuple field '),
-             FormattedValue(
-              value=Name(id='field_name', ctx=Load()),
-              conversion=-1),
-             Constant(value=' cannot follow default field'),
...(截断)
```

**`IO`**（源 L3233 ↔ 产物 L2460）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
-   decorator_list=[
-    Name(id='abstractmethod', ctx=Load())],
-   returns=Constant(value=None)),
...(截断)
```

**`BinaryIO`**（源 L3332 ↔ 产物 L2536）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Name(id='abstractmethod', ctx=Load())],
-   returns=Constant(value='BinaryIO'))],
+    Name(id='abstractmethod', ctx=Load())])],
```

**`TextIO`**（源 L3346 ↔ 产物 L2545）

```diff
-  Expr(
+  Assign(
+   targets=[
+    Name(id='__doc__', ctx=Store())],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
+    Return(
+     value=Constant(value=None))],
-    Pass()],
...(截断)
```

## `stdlib_unittest_case`（判据 failure）

- 源：`D:\Python\Lib\unittest\case.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_unittest_caseOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `_Outcome.testPartExecutor` | L53 | L44 | 常量数: 源=6 产物=8 |
| `TestCase._addExpectedFailure` | L550 | L450 | return: 源=0 产物=2；常量数: 源=1 产物=3；仅产物常量: None |
| `TestCase._addUnexpectedSuccess` | L560 | L459 | return: 源=0 产物=2；常量数: 源=2 产物=4 |
| `TestCase.run` | L589 | L483 | return: 源=2 产物=3；常量数: 源=25 产物=28 |
| `TestCase.doCleanups` | L652 | L538 | boolop: 源=1 产物=0 |
| `TestCase.debug` | L680 | L559 | star_args: 源=1 产物=0 |
| `TestCase.assertSequenceEqual` | L964 | L787 | break: 源=3 产物=1；fstring: 源=0 产物=2；常量数: 源=25 产物=29；仅源常量: 'First sequence is not a %s: %s', 'Second sequence is not a %s: %s'；仅产物常量: ': ', 'First sequence is not a ', 'Second sequence is not a ' |
| `TestCase.assertCountEqual` | L1203 | L1012 | return: 源=1 产物=2；常量数: 源=5 产物=7 |

### AST 结构差分（源 vs 产物）

**`_Outcome.testPartExecutor`**（源 L53 ↔ 产物 L44）

```diff
-    Expr(value=Yield())],
+    Expr(
+     value=Yield(
+      value=Constant(value=None))),
+    Assign(
+     targets=[
+      Attribute(
+       value=Name(id='self', ctx=Load()),
+       attr='success',
+       ctx=Store())],
+     value=BoolOp(
+      op=And(),
+      values=[
+       Attribute(
...(截断)
```

**`TestCase._addExpectedFailure`**（源 L550 ↔ 产物 L450）

```diff
-      ctx=Load()))],
+      ctx=Load())),
+    Expr(
+     value=Call(
+      func=Name(id='addExpectedFailure', ctx=Load()),
+      args=[
+       Name(id='self', ctx=Load()),
+       Name(id='exc_info', ctx=Load())],
+      keywords=[])),
+    Return(
+     value=Constant(value=None))],
-        keywords=[]))])],
-   orelse=[
-    Expr(
...(截断)
```

**`TestCase._addUnexpectedSuccess`**（源 L560 ↔ 产物 L459）

```diff
-      ctx=Load()))],
+      ctx=Load())),
+    Expr(
+     value=Call(
+      func=Name(id='addUnexpectedSuccess', ctx=Load()),
+      args=[
+       Name(id='self', ctx=Load())],
+      keywords=[])),
+    Return(
+     value=Constant(value=None))],
-            keywords=[]))])],
+            keywords=[])),
+          Return(
+           value=Constant(value=None))])],
...(截断)
```

**`TestCase.run`**（源 L589 ↔ 产物 L483）

```diff
-      Return(
-       value=Name(id='result', ctx=Load()))],
+      Expr(
+       value=Name(id='result', ctx=Load())),
+      Expr(
+       value=Call(
+        func=Attribute(
+         value=Name(id='result', ctx=Load()),
+         attr='stopTest',
+         ctx=Load()),
+        args=[
+         Name(id='self', ctx=Load())],
+        keywords=[])),
+      If(
...(截断)
```

**`TestCase.doCleanups`**（源 L652 ↔ 产物 L538）

```diff
-  Assign(
-   targets=[
-    Name(id='outcome', ctx=Store())],
-   value=BoolOp(
-    op=Or(),
-    values=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='_outcome',
-      ctx=Load()),
-     Call(
-      func=Name(id='_Outcome', ctx=Load()),
-      args=[],
-      keywords=[])])),
...(截断)
```

**`TestCase.debug`**（源 L680 ↔ 产物 L559）

```diff
-      keywords=[])),
-    Expr(
-     value=Call(
-      func=Attribute(
-       value=Name(id='self', ctx=Load()),
-       attr='_callCleanup',
-       ctx=Load()),
-      args=[
-       Name(id='function', ctx=Load()),
-       Starred(
-        value=Name(id='args', ctx=Load()),
-        ctx=Load())],
-      keywords=[
-       keyword(
...(截断)
```

**`TestCase.assertSequenceEqual`**（源 L964 ↔ 产物 L787）

```diff
-         BinOp(
-          left=Constant(value='First sequence is not a %s: %s'),
-          op=Mod(),
-          right=Tuple(
-           elts=[
-            Name(id='seq_type_name', ctx=Load()),
-            Call(
+         JoinedStr(
+          values=[
+           Constant(value='First sequence is not a '),
+           FormattedValue(
+            value=Name(id='seq_type_name', ctx=Load()),
+            conversion=115),
+           Constant(value=': '),
...(截断)
```

**`TestCase.assertCountEqual`**（源 L1203 ↔ 产物 L1012）

```diff
-      Return()],
-     orelse=[]),
-    Assign(
-     targets=[
-      Name(id='differences', ctx=Store())],
-     value=Call(
-      func=Name(id='_count_diff_hashable', ctx=Load()),
-      args=[
-       Name(id='first_seq', ctx=Load()),
-       Name(id='second_seq', ctx=Load())],
-      keywords=[]))],
+      Pass()],
+     orelse=[
+      Assign(
...(截断)
```

## `stdlib_urllib_request`（判据 failure）

- 源：`D:\Python\Lib\urllib\request.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_urllib_requestOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `urlretrieve` | L223 | L176 | boolop: 源=2 产物=1；常量数: 源=18 产物=17；仅源常量: 1024, 8；仅产物常量: 8192 |
| `urlcleanup` | L286 | L226 | delete: 源=1 产物=0；docstring: 源=1 产物=0；return: 源=0 产物=2；slice: 源=1 产物=0；常量数: 源=2 产物=4 |
| `Request.header_items` | L422 | L337 | （指纹一致） |
| `HTTPRedirectHandler.redirect_request` | L653 | L508 | boolop: 源=3 产物=2 |
| `HTTPPasswordMgr.find_user_password` | L850 | L625 | 常量数: 源=4 产物=5 |
| `parse_http_list` | L1431 | L1009 | （指纹一致） |
| `FileHandler.open_local_file` | L1498 | L1061 | boolop: 源=3 产物=2 |
| `FTPHandler.ftp_open` | L1532 | L1094 | boolop: 源=7 产物=9；常量数: 源=25 产物=27 |
| `URLopener.retrieve` | L1806 | L1303 | boolop: 源=7 产物=6；常量数: 源=25 产物=23；仅源常量: 1024, 8；仅产物常量: 8192, True |
| `FancyURLopener.http_error_302` | L2152 | L1606 | 常量数: 源=7 产物=8 |

### AST 结构差分（源 vs 产物）

**`urlretrieve`**（源 L223 ↔ 产物 L176）

```diff
-     test=BoolOp(
-      op=And(),
-      values=[
-       Compare(
-        left=Name(id='url_type', ctx=Load()),
-        ops=[
-         Eq()],
-        comparators=[
-         Constant(value='file')]),
-       UnaryOp(
+     test=Compare(
+      left=Name(id='url_type', ctx=Load()),
+      ops=[
+       Eq()],
...(截断)
```

**`urlcleanup`**（源 L286 ↔ 产物 L226）

```diff
+  Global(
+   names=[
+    '_opener']),
-  Delete(
-   targets=[
-    Subscript(
-     value=Name(id='_url_tempfiles', ctx=Load()),
-     slice=Slice(),
-     ctx=Del())]),
-  Global(
-   names=[
-    '_opener']),
+     value=Constant(value=None)),
+    Return(
...(截断)
```

**`Request.header_items`**（源 L422 ↔ 产物 L337）

```diff
-   value=Dict(
-    keys=[
-     None,
-     None],
-    values=[
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='unredirected_hdrs',
-      ctx=Load()),
-     Attribute(
-      value=Name(id='self', ctx=Load()),
-      attr='headers',
-      ctx=Load())])),
+   value=Dict(keys=[], values=[])),
...(截断)
```

**`HTTPRedirectHandler.redirect_request`**（源 L653 ↔ 产物 L508）

```diff
-   test=UnaryOp(
-    op=Not(),
-    operand=BoolOp(
-     op=Or(),
-     values=[
-      BoolOp(
-       op=And(),
+   test=Compare(
+    left=Name(id='code', ctx=Load()),
+    ops=[
+     In()],
+    comparators=[
+     Tuple(
+      elts=[
...(截断)
```

**`HTTPPasswordMgr.find_user_password`**（源 L850 ↔ 产物 L625）

```diff
+          Expr(
+           value=Name(id='authinfo', ctx=Load())),
-           value=Name(id='authinfo', ctx=Load()))],
+           value=Constant(value=None))],
```

**`parse_http_list`**（源 L1431 ↔ 产物 L1009）

```diff
-    Name(id='escape', ctx=Store()),
-    Name(id='quote', ctx=Store())],
+    Name(id='escape', ctx=Store())],
+       orelse=[]),
+      If(
+       test=Compare(
+        left=Name(id='cur', ctx=Load()),
+        ops=[
+         Eq()],
+        comparators=[
+         Constant(value='"')]),
+       body=[
+        Assign(
+         targets=[
...(截断)
```

**`FileHandler.open_local_file`**（源 L1498 ↔ 产物 L1061）

```diff
-     test=BoolOp(
-      op=Or(),
-      values=[
-       UnaryOp(
-        op=Not(),
-        operand=Name(id='host', ctx=Load())),
-       BoolOp(
+     test=Name(id='host', ctx=Load()),
+     body=[
+      If(
+       test=BoolOp(
-            keywords=[])])])]),
-     body=[
-      If(
...(截断)
```

**`FTPHandler.ftp_open`**（源 L1532 ↔ 产物 L1094）

```diff
-     iter=Name(id='attrs', ctx=Load()),
+     iter=BoolOp(
+      op=Or(),
+      values=[
+       BoolOp(
+        op=And(),
+        values=[
+         Name(id='file', ctx=Load()),
+         Constant(value='I')]),
+       Constant(value='D')]),
```

**`URLopener.retrieve`**（源 L1806 ↔ 产物 L1303）

```diff
-     BoolOp(
-      op=Or(),
-      values=[
-       UnaryOp(
-        op=Not(),
-        operand=Name(id='type', ctx=Load())),
-       Compare(
-        left=Name(id='type', ctx=Load()),
-        ops=[
-         Eq()],
-        comparators=[
-         Constant(value='file')])])]),
+     Name(id='type', ctx=Load())]),
+    If(
...(截断)
```

**`FancyURLopener.http_error_302`**（源 L2152 ↔ 产物 L1606）

```diff
-      Return(
+      Expr(
-        keywords=[]))],
+        keywords=[])),
+      Return(
+       value=Constant(value=0))],
```

## `stdlib_xml_ElementPath`（判据 failure）

- 源：`D:\Python\Lib\xml\etree\ElementPath.py`
- 产物：`F:\Downloads\pythoncdc-main\.trae\specs\attack-completeness-claims\rounds\round6\offcorpus\stdlib_xml_ElementPathOK.py`

| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |
|---|---|---|---|
| `xpath_tokenizer` | L74 | L6 | boolop: 源=2 产物=1；continue: 源=0 产物=2；fstring: 源=0 产物=2；常量数: 源=15 产物=17；仅源常量: '{%s}%s'；仅产物常量: '}' |
| `get_parent_map` | L98 | L31 | （指纹一致） |
| `prepare_predicate` | L227 | L141 | return: 源=6 产物=5 |
| `iterfind` | L360 | L246 | break: 源=1 产物=0；while: 源=1 产物=0；常量数: 源=14 产物=13 |

### AST 结构差分（源 vs 产物）

**`xpath_tokenizer`**（源 L74 ↔ 产物 L6）

```diff
-              BinOp(
-               left=Constant(value='{%s}%s'),
-               op=Mod(),
-               right=Tuple(
-                elts=[
-                 Subscript(
+              JoinedStr(
+               values=[
+                Constant(value='{'),
+                FormattedValue(
+                 value=Subscript(
-                 Name(id='uri', ctx=Load())],
-                ctx=Load()))],
+                 conversion=115),
...(截断)
```

**`get_parent_map`**（源 L98 ↔ 产物 L31）

```diff
-       ctx=Store()),
-      Name(id='parent_map', ctx=Store())],
+       ctx=Store())],
```

**`prepare_predicate`**（源 L227 ↔ 产物 L141）

```diff
-   test=Constant(value=1),
+   test=Constant(value=True),
-    Try(
-     body=[
-      Assign(
-       targets=[
-        Name(id='token', ctx=Store())],
-       value=Call(
-        func=Name(id='next', ctx=Load()),
-        args=[],
-        keywords=[]))],
-     handlers=[
-      ExceptHandler(
-       type=Name(id='StopIteration', ctx=Load()),
...(截断)
```

**`iterfind`**（源 L360 ↔ 产物 L246）

```diff
-          Return()])],
+          Return(
+           value=Constant(value=None))])],
-      While(
-       test=Constant(value=1),
-       body=[
-        Try(
-         body=[
-          Expr(
-           value=Call(
-            func=Attribute(
-             value=Name(id='selector', ctx=Load()),
-             attr='append',
-             ctx=Load()),
...(截断)
```

