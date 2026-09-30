---
type: entity
title: ast_nodes.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
lines: 7076
patch_markers: 260
method_count: 513
sources:
  - core/ast_nodes.py
---

# core/ast_nodes.py

源文件：`core/ast_nodes.py`（7076 行，md5 `4058936d0217573b219ea1bd78d0b811`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 7076 |
| patch_markers | 260 |
| method_count | 513 |
| 顶层类/函数 | 92/22 |

## 摘要

AST节点模块

## 关键符号

### 类

- `NodeType` :139
- [[core-ast-nodes--ast-node|ASTNode]] :218
- [[core-ast-nodes--ast-node-list|ASTNodeList]] :274
- [[core-ast-nodes--ast-block|ASTBlock]] :540
- `ASTChainStore` :967
- [[core-ast-nodes--ast-store|ASTStore]] :979
- `ASTObject` :1067
- `ASTUnary` :1231
- [[core-ast-nodes--ast-binary|ASTBinary]] :1292
- `ASTCompare` :1460
- `ASTSlice` :1554
- `ASTSliceExpr` :1605
- `ASTSubscript` :1665
- [[core-ast-nodes--ast-call|ASTCall]] :1721
- `ASTKeyword` :1955
- `ASTList` :1980
- `ASTTuple` :2015
- `ASTDict` :2180
- `ASTSet` :2231
- `ASTConstant` :2255
- [[core-ast-nodes--ast-decorator-application|ASTDecoratorApplication]] :2333
- `ASTName` :2424
- `ASTModule` :2468
- [[core-ast-nodes--ast-function-def|ASTFunctionDef]] :2493
- `ASTClassDef` :2835
- `ASTAssign` :2954
- `ASTNamedExpr` :3034
- [[core-ast-nodes--ast-if|ASTIf]] :3086
- [[core-ast-nodes--ast-if-exp|ASTIfExp]] :3745
- [[core-ast-nodes--ast-for|ASTFor]] :3789
- `ASTWhile` :3925
- [[core-ast-nodes--ast-with|ASTWith]] :4025
- [[core-ast-nodes--ast-try|ASTTry]] :4139
- `ASTWithItem` :4280
- `ASTComprehension` :4316
- `ASTReturn` :4376
- `ASTYield` :4490
- `ASTFormattedValue` :4520
- `ASTJoinedStr` :4580
- `ASTExpr` :4627
- `ASTAttribute` :4655
- `ASTDelete` :4698
- `ASTGlobal` :4745
- `ASTNonlocal` :4764
- `ASTImport` :4783
- `ASTImportFrom` :4813
- `ASTAlias` :4852
- `ASTPass` :4878
- `ASTBreak` :4885
- `ASTContinue` :4897
- `ASTJump` :4909
- `ASTAssert` :4929
- `ASTAnnAssign` :4966
- `ASTAugAssign` :5004
- `ASTRaise` :5052
- `ASTLambda` :5278
- `ASTListComp` :5336
- `ASTSetComp` :5379
- `ASTDictComp` :5430
- `ASTGenExpr` :5488
- `ASTConditionalExp` :5539
- `ASTExceptHandler` :5591
- `ASTMatchClass` :5694
- `ASTMatchKeys` :5735
- `ASTMatchMapping` :5747
- `ASTMatchSequence` :5776
- `ASTMatch` :5813
- `ASTCase` :5863
- `ASTConstMap` :5935
- `ASTAwaitable` :5981
- `ASTLoadBuildClass` :5999
- `ASTKwNamesMap` :6020
- `ASTPrint` :6049
- `ASTConvert` :6104
- `ASTMatchKeys` :6121
- `ASTLocals` :6146
- [[core-ast-nodes--code-generator|CodeGenerator]] :6190
- `ASTTernary` :6280
- `ASTAnnotatedVar` :6319
- `ASTChainStore` :6342
- `ASTIs` :6375
- `ASTIn` :6398
- `ASTNotIn` :6421
- `ASTTryStar` :6444
- `ASTTypeIgnore` :6541
- `ASTTypeComment` :6560
- `ASTFormattedValue` :6576
- `ASTJoinedStr` :6633
- `ASTConstMap` :6699
- `ASTAnnotatedVar` :6738
- `ASTLocals` :6761
- [[core-ast-nodes--code-generator|CodeGenerator]] :6805

### 顶层函数

- `ast_debug_print()` :15
- `ordered_const_items()` :44
- `create_optimized_ast_node()` :75
- `monitor_ast_creation()` :90
- `_get_depth()` :115
- `_inc_depth()` :119
- `_dec_depth()` :124
- `create_comparison()` :6158
- `create_binary_op()` :6163
- `create_unary_op()` :6168
- `create_call()` :6173
- `create_name()` :6179
- `create_constant()` :6184
- `create_comparison()` :6773
- `create_binary_op()` :6778
- `create_unary_op()` :6783
- `create_call()` :6788
- `create_name()` :6794
- `create_constant()` :6799
- `enhance_ast_nodes()` :7040
- …共 22 个顶层函数，仅列体长前 20

## 相关页面

- [[index|Wiki Index]]
