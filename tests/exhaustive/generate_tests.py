import os
import sys
import textwrap
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

EXHAUSTIVE_DIR = os.path.dirname(os.path.abspath(__file__))

VARIABLES = [
    'x', 'y', 'z', 'a', 'b', 'c', 'n', 'm', 'i', 'j', 'k',
    'val', 'result', 'data', 'item', 'count', 'total', 'flag',
    'name', 'key', 'value', 'num', 'idx', 'res', 'tmp',
]

CONSTANTS_INT = [
    '0', '1', '2', '3', '5', '10', '42', '100', '-1', '-5',
    '255', '1000', '999', '7', '16', '32', '64', '128',
]

CONSTANTS_STR = [
    "'hello'", "'world'", "'test'", "'abc'", "'xyz'",
    "'foo'", "'bar'", "'baz'", "'spam'", "'eggs'",
]

CONSTANTS_FLOAT = [
    '1.0', '3.14', '0.5', '2.718', '-1.0', '0.0', '99.9',
]

CONSTANTS_BOOL = ['True', 'False']

CONSTANTS_NONE = ['None']

EXCEPTIONS = [
    'ValueError', 'TypeError', 'KeyError', 'IndexError',
    'AttributeError', 'RuntimeError', 'StopIteration',
    'ZeroDivisionError', 'FileNotFoundError', 'OSError',
    'NameError', 'ImportError', 'OverflowError',
]

CALLABLES = [
    'print', 'len', 'range', 'str', 'int', 'float', 'list',
    'dict', 'set', 'tuple', 'abs', 'max', 'min', 'sum',
    'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
    'isinstance', 'hasattr', 'getattr', 'type', 'bool', 'hash',
]

BASIC_TEMPLATES: List[Tuple[str, str, str]] = [
    ("B01SimpleAssign_{var}_{const}", "BASIC", "{var} = {const}"),
    ("B02AugAssignAdd_{var}_{const}", "BASIC", "{var} += {const}"),
    ("B03AugAssignSub_{var}_{const}", "BASIC", "{var} -= {const}"),
    ("B04AugAssignMul_{var}_{const}", "BASIC", "{var} *= {const}"),
    ("B05AugAssignDiv_{var}_{const}", "BASIC", "{var} //= {const}"),
    ("B06AugAssignMod_{var}_{const}", "BASIC", "{var} %= {const}"),
    ("B07AugAssignPow_{var}_{const}", "BASIC", "{var} **= {const}"),
    ("B08AugAssignBitAnd_{var}_{const}", "BASIC", "{var} &= {const}"),
    ("B09AugAssignBitOr_{var}_{const}", "BASIC", "{var} |= {const}"),
    ("B10AugAssignBitXor_{var}_{const}", "BASIC", "{var} ^= {const}"),
    ("B11AugAssignLShift_{var}_{const}", "BASIC", "{var} <<= {const}"),
    ("B12AugAssignRShift_{var}_{const}", "BASIC", "{var} >>= {const}"),
    ("B13ExprCall_{func}_{var}", "BASIC", "{func}({var})"),
    ("B14ExprCallNoArg_{func}", "BASIC", "{func}()"),
    ("B15Return_{const}", "BASIC", "def f():\n    return {const}"),
    ("B16ReturnNone", "BASIC", "def f():\n    return None"),
    ("B17ReturnVar_{var}", "BASIC", "def f():\n    return {var}"),
    ("B18Pass", "BASIC", "pass"),
    ("B19Delete_{var}", "BASIC", "{var} = 1\ndel {var}"),
    ("B20Global_{var}", "BASIC", "global {var}"),
    ("B21Nonlocal_{var}", "BASIC", "def outer():\n    {var} = 1\n    def inner():\n        nonlocal {var}"),
    ("B22Yield_{const}", "BASIC", "def f():\n    yield {const}"),
    ("B23YieldFrom_{var}", "BASIC", "def f():\n    yield from {var}"),
    ("B24Raise_{exc}", "BASIC", "raise {exc}"),
    ("B25RaiseFrom_{exc}", "BASIC", "raise {exc} from None"),
    ("B26Import_{mod}", "BASIC", "import {mod}"),
    ("B27FromImport_{mod}_{name}", "BASIC", "from {mod} import {name}"),
    ("B28MultiAssign_{var1}_{var2}_{const}", "BASIC", "{var1} = {var2} = {const}"),
    ("B29TupleUnpack_{var1}_{var2}", "BASIC", "{var1}, {var2} = 1, 2"),
    ("B30SubscriptAssign_{var}_{const}", "BASIC", "{var}[0] = {const}"),
    ("B31AttrAssign_{var}_{const}", "BASIC", "{var}.attr = {const}"),
    ("B32ExprBinOp_{var}_{const}", "BASIC", "{var} + {const}"),
    ("B33ExprUnaryOp_{var}", "BASIC", "not {var}"),
    ("B34ExprCompare_{var}_{const}", "BASIC", "{var} > {const}"),
    ("B35Assert_{var}", "BASIC", "assert {var}"),
    ("B36AssertMsg_{var}", "BASIC", "assert {var}, 'error'"),
]

IF_TEMPLATES: List[Tuple[str, str, str]] = [
    ("IF01IfThen_{var}_{const}", "IF_REGION", "if {var} > {const}:\n    {var} = {const}"),
    ("IF02IfElse_{var}_{const}", "IF_REGION", "if {var} > {const}:\n    {var} = {const}\nelse:\n    {var} = 0"),
    ("IF03IfElif_{var}_{const1}_{const2}", "IF_REGION", "if {var} > {const1}:\n    {var} = 1\nelif {var} > {const2}:\n    {var} = 2"),
    ("IF04IfElifElse_{var}_{const1}_{const2}", "IF_REGION", "if {var} > {const1}:\n    {var} = 1\nelif {var} > {const2}:\n    {var} = 2\nelse:\n    {var} = 0"),
    ("IF05IfMultiElif_{var}", "IF_REGION", "if {var} == 1:\n    pass\nelif {var} == 2:\n    pass\nelif {var} == 3:\n    pass\nelse:\n    pass"),
    ("IF06NestedIf_{var}_{const}", "IF_REGION", "if {var} > 0:\n    if {var} > {const}:\n        {var} = {const}"),
    ("IF07IfReturn_{var}", "IF_REGION", "def f({var}):\n    if {var} > 0:\n        return {var}\n    return 0"),
    ("IF08IfBreak_{var}", "IF_REGION", "while True:\n    if {var} > 0:\n        break"),
    ("IF09IfContinue_{var}", "IF_REGION", "for {var} in range(10):\n    if {var} > 5:\n        continue"),
    ("IF10IfAnd_{var1}_{var2}", "IF_REGION", "if {var1} and {var2}:\n    pass"),
    ("IF11IfOr_{var1}_{var2}", "IF_REGION", "if {var1} or {var2}:\n    pass"),
    ("IF12IfNot_{var}", "IF_REGION", "if not {var}:\n    pass"),
    ("IF13IfCompare_{var}_{const}", "IF_REGION", "if {var} == {const}:\n    pass"),
    ("IF14IfIn_{var}", "IF_REGION", "if {var} in [1, 2, 3]:\n    pass"),
    ("IF15IfIs_{var}", "IF_REGION", "if {var} is None:\n    pass"),
    ("IF16IfIsNot_{var}", "IF_REGION", "if {var} is not None:\n    pass"),
    ("IF17IfNotIn_{var}", "IF_REGION", "if {var} not in [1, 2, 3]:\n    pass"),
    ("IF18IfChainCompare_{var}", "IF_REGION", "if 0 < {var} < 10:\n    pass"),
    ("IF19IfEq_{var}_{const}", "IF_REGION", "if {var} == {const}:\n    {var} = 0"),
    ("IF20IfNeq_{var}_{const}", "IF_REGION", "if {var} != {const}:\n    {var} = 0"),
    ("IF21IfLt_{var}_{const}", "IF_REGION", "if {var} < {const}:\n    {var} = 0"),
    ("IF22IfLe_{var}_{const}", "IF_REGION", "if {var} <= {const}:\n    {var} = 0"),
    ("IF23IfGe_{var}_{const}", "IF_REGION", "if {var} >= {const}:\n    {var} = 0"),
    ("IF24IfTrue_{var}", "IF_REGION", "if {var}:\n    pass"),
    ("IF25IfFalse_{var}", "IF_REGION", "if not {var}:\n    pass"),
    ("IF26IfNone_{var}", "IF_REGION", "if {var} is None:\n    {var} = 0"),
    ("IF27IfNotNone_{var}", "IF_REGION", "if {var} is not None:\n    {var} = 0"),
    ("IF28IfInList_{var}", "IF_REGION", "if {var} in [1, 2, 3]:\n    {var} = 0"),
    ("IF29IfNotInList_{var}", "IF_REGION", "if {var} not in [1, 2, 3]:\n    {var} = 0"),
    ("IF30IfElifElif_{var}", "IF_REGION", "if {var} > 10:\n    pass\nelif {var} > 5:\n    pass\nelif {var} > 0:\n    pass"),
    ("IF31IfElifElifElse_{var}", "IF_REGION", "if {var} > 10:\n    pass\nelif {var} > 5:\n    pass\nelif {var} > 0:\n    pass\nelse:\n    pass"),
    ("IF32NestedIfElse_{var1}_{var2}", "IF_REGION", "if {var1} > 0:\n    if {var2} > 0:\n        {var1} = 1\n    else:\n        {var1} = 2\nelse:\n    {var1} = 0"),
    ("IF33IfReturnElse_{var}", "IF_REGION", "def f({var}):\n    if {var} > 0:\n        return 1\n    else:\n        return 0"),
    ("IF34IfRaise_{var}_{exc}", "IF_REGION", "if {var} < 0:\n    raise {exc}"),
    ("IF35IfAssign_{var}_{const}", "IF_REGION", "if {var} > 0:\n    {var} = {const}\nelse:\n    {var} = 0"),
    ("IF36IfPass_{var}", "IF_REGION", "if {var} > 0:\n    pass"),
    ("IF37IfMultiStmt_{var}_{const}", "IF_REGION", "if {var} > 0:\n    {var} = {const}\n    {var} += 1"),
    ("IF38IfElseMultiStmt_{var}_{const}", "IF_REGION", "if {var} > 0:\n    {var} = {const}\n    {var} += 1\nelse:\n    {var} = 0\n    {var} -= 1"),
]

WHILE_TEMPLATES: List[Tuple[str, str, str]] = [
    ("WL01SimpleWhile_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1"),
    ("WL02WhileElse_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1\nelse:\n    {var} = 0"),
    ("WL03WhileBreak_{var}", "WHILE_LOOP", "while True:\n    {var} += 1\n    if {var} > 10:\n        break"),
    ("WL04WhileContinue_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1\n    if {var} == 5:\n        continue"),
    ("WL05WhileTrue", "WHILE_LOOP", "while True:\n    break"),
    ("WL06WhileTrueBreak_{var}", "WHILE_LOOP", "while True:\n    {var} += 1\n    if {var} > 100:\n        break"),
    ("WL07NestedWhile_{var1}_{var2}", "WHILE_LOOP", "while {var1} > 0:\n    while {var2} > 0:\n        {var2} -= 1\n    {var1} -= 1"),
    ("WL08WhileCompare_{var}_{const}", "WHILE_LOOP", "while {var} < {const}:\n    {var} += 1"),
    ("WL09WhileAnd_{var1}_{var2}", "WHILE_LOOP", "while {var1} > 0 and {var2} > 0:\n    {var1} -= 1"),
    ("WL10WhileOr_{var1}_{var2}", "WHILE_LOOP", "while {var1} > 0 or {var2} > 0:\n    {var1} -= 1"),
    ("WL11WhileNot_{var}", "WHILE_LOOP", "while not {var}:\n    {var} = True"),
    ("WL12WhileBreakElse_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1\n    if {var} == 3:\n        break\nelse:\n    {var} = -1"),
    ("WL13WhileTrueSimple", "WHILE_LOOP", "while True:\n    pass"),
    ("WL14WhileEq_{var}_{const}", "WHILE_LOOP", "while {var} == {const}:\n    {var} += 1"),
    ("WL15WhileNeq_{var}_{const}", "WHILE_LOOP", "while {var} != {const}:\n    {var} += 1"),
    ("WL16WhileLe_{var}_{const}", "WHILE_LOOP", "while {var} <= {const}:\n    {var} += 1"),
    ("WL17WhileGe_{var}_{const}", "WHILE_LOOP", "while {var} >= {const}:\n    {var} -= 1"),
    ("WL18WhileIn_{var}", "WHILE_LOOP", "while {var} in [1, 2, 3]:\n    {var} += 1"),
    ("WL19WhileNot_{var}", "WHILE_LOOP", "while not {var}:\n    {var} = True"),
    ("WL20WhileBreakContinue_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1\n    if {var} == 5:\n        continue\n    if {var} == 2:\n        break"),
    ("WL21WhileNestedIf_{var1}_{var2}", "WHILE_LOOP", "while {var1} > 0:\n    if {var2} > 0:\n        {var2} -= 1\n    {var1} -= 1"),
    ("WL22WhileTry_{var}_{exc}", "WHILE_LOOP", "while {var} > 0:\n    try:\n        {var} -= 1\n    except {exc}:\n        {var} = 0"),
    ("WL23WhileReturn_{var}", "WHILE_LOOP", "def f({var}):\n    while {var} > 0:\n        {var} -= 1\n        if {var} == 0:\n            return {var}"),
    ("WL24WhileAssign_{var}_{const}", "WHILE_LOOP", "while {var} < {const}:\n    {var} = {var} + 1"),
    ("WL25WhileMultiStmt_{var}", "WHILE_LOOP", "while {var} > 0:\n    {var} -= 1\n    {var} *= 2"),
]

FOR_TEMPLATES: List[Tuple[str, str, str]] = [
    ("FL01SimpleFor_{var}", "FOR_LOOP", "for {var} in range(10):\n    pass"),
    ("FL02ForElse_{var}", "FOR_LOOP", "for {var} in range(10):\n    pass\nelse:\n    {var} = -1"),
    ("FL03ForBreak_{var}", "FOR_LOOP", "for {var} in range(10):\n    if {var} == 5:\n        break"),
    ("FL04ForContinue_{var}", "FOR_LOOP", "for {var} in range(10):\n    if {var} == 5:\n        continue"),
    ("FL05ForRange_{var}_{const}", "FOR_LOOP", "for {var} in range({const}):\n    pass"),
    ("FL06ForRangeStep_{var}", "FOR_LOOP", "for {var} in range(0, 10, 2):\n    pass"),
    ("FL07ForEnumerate_{var1}_{var2}", "FOR_LOOP", "for {var1}, {var2} in enumerate([1, 2, 3]):\n    pass"),
    ("FL08ForList_{var}", "FOR_LOOP", "for {var} in [1, 2, 3]:\n    pass"),
    ("FL09ForDict_{var1}_{var2}", "FOR_LOOP", "for {var1}, {var2} in {{'a': 1}}.items():\n    pass"),
    ("FL10ForString_{var}", "FOR_LOOP", "for {var} in 'abc':\n    pass"),
    ("FL11ForZip_{var1}_{var2}", "FOR_LOOP", "for {var1}, {var2} in zip([1], [2]):\n    pass"),
    ("FL12NestedFor_{var1}_{var2}", "FOR_LOOP", "for {var1} in range(3):\n    for {var2} in range(3):\n        pass"),
    ("FL13ForBreakElse_{var}", "FOR_LOOP", "for {var} in range(10):\n    if {var} == 5:\n        break\nelse:\n    {var} = -1"),
    ("FL14ForAssign_{var}", "FOR_LOOP", "for {var} in range(10):\n    {var} = {var} * 2"),
    ("FL15ForTupleUnpack_{var1}_{var2}", "FOR_LOOP", "for {var1}, {var2} in [(1, 2), (3, 4)]:\n    pass"),
    ("FL16ForBreakContinue_{var}", "FOR_LOOP", "for {var} in range(20):\n    if {var} == 3:\n        continue\n    if {var} == 7:\n        break"),
    ("FL17ForNestedIf_{var1}_{var2}", "FOR_LOOP", "for {var1} in range(5):\n    if {var1} > 2:\n        {var2} = {var1}"),
    ("FL18ForTry_{var}_{exc}", "FOR_LOOP", "for {var} in range(5):\n    try:\n        pass\n    except {exc}:\n        continue"),
    ("FL19ForReturn_{var}", "FOR_LOOP", "def f():\n    for {var} in range(10):\n        if {var} == 5:\n            return {var}"),
    ("FL20ForAssign_{var}", "FOR_LOOP", "for {var} in range(5):\n    {var} = {var} * 2"),
    ("FL21ForMultiStmt_{var}", "FOR_LOOP", "for {var} in range(5):\n    {var} += 1\n    {var} *= 2"),
    ("FL22ForSet_{var}", "FOR_LOOP", "for {var} in {1, 2, 3}:\n    pass"),
    ("FL23ForDictKeys_{var1}_{var2}", "FOR_LOOP", "for {var1} in {{'a': 1}}:\n    pass"),
    ("FL24ForTuple_{var}", "FOR_LOOP", "for {var} in (1, 2, 3):\n    pass"),
    ("FL25ForReversed_{var}", "FOR_LOOP", "for {var} in reversed([1, 2, 3]):\n    pass"),
    ("FL26ForSorted_{var}", "FOR_LOOP", "for {var} in sorted([3, 1, 2]):\n    pass"),
    ("FL27ForMap_{var}", "FOR_LOOP", "for {var} in map(str, [1, 2, 3]):\n    pass"),
    ("FL28ForFilter_{var}", "FOR_LOOP", "for {var} in filter(None, [1, 0, 3]):\n    pass"),
]

TRY_EXCEPT_TEMPLATES: List[Tuple[str, str, str]] = [
    ("TE01TryExcept_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    pass"),
    ("TE02TryExceptAs_{exc}_{var}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc} as {var}:\n    pass"),
    ("TE03TryMultiExcept_{exc1}_{exc2}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc1}:\n    pass\nexcept {exc2}:\n    pass"),
    ("TE04TryFinally", "TRY_EXCEPT", "try:\n    pass\nfinally:\n    pass"),
    ("TE05TryExceptFinally_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    pass\nfinally:\n    pass"),
    ("TE06TryExceptElse_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    pass\nelse:\n    pass"),
    ("TE07TryExceptElseFinally_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    pass\nelse:\n    pass\nfinally:\n    pass"),
    ("TE08TryExceptRaise_{exc}", "TRY_EXCEPT", "try:\n    raise {exc}\nexcept {exc}:\n    pass"),
    ("TE09TryExceptReraise_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    raise"),
    ("TE10NestedTry_{exc1}_{exc2}", "TRY_EXCEPT", "try:\n    try:\n        pass\n    except {exc1}:\n        pass\nexcept {exc2}:\n    pass"),
    ("TE11TryMultiExceptAs_{exc1}_{exc2}_{var}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc1} as {var}:\n    pass\nexcept {exc2}:\n    pass"),
    ("TE12TryExceptReturn_{exc}", "TRY_EXCEPT", "def f():\n    try:\n        return 1\n    except {exc}:\n        return 0"),
    ("TE13TryFinallyReturn", "TRY_EXCEPT", "def f():\n    try:\n        return 1\n    finally:\n        pass"),
    ("TE14TryExceptTuple_{exc1}_{exc2}", "TRY_EXCEPT", "try:\n    pass\nexcept ({exc1}, {exc2}):\n    pass"),
    ("TE15BareExcept", "TRY_EXCEPT", "try:\n    pass\nexcept:\n    pass"),
    ("TE16TryExceptPass_{exc}", "TRY_EXCEPT", "try:\n    x = 1\nexcept {exc}:\n    pass"),
    ("TE17TryExceptAssign_{exc}_{var}", "TRY_EXCEPT", "try:\n    {var} = 1\nexcept {exc}:\n    {var} = 0"),
    ("TE18TryExceptPrint_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    print('error')"),
    ("TE19TryExceptReraise_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    raise"),
    ("TE20TryExceptRaiseFrom_{exc}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc} as e:\n    raise ValueError from e"),
    ("TE21TryMultiExceptAs_{exc1}_{exc2}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc1} as e1:\n    pass\nexcept {exc2} as e2:\n    pass"),
    ("TE22TryExceptElseAssign_{exc}_{var}", "TRY_EXCEPT", "try:\n    pass\nexcept {exc}:\n    pass\nelse:\n    {var} = 1"),
    ("TE23TryFinallyAssign_{var}", "TRY_EXCEPT", "try:\n    {var} = 1\nfinally:\n    {var} = 0"),
    ("TE24TryExceptFinallyAssign_{exc}_{var}", "TRY_EXCEPT", "try:\n    {var} = 1\nexcept {exc}:\n    {var} = 0\nfinally:\n    {var} = -1"),
    ("TE25NestedTryExcept_{exc1}_{exc2}", "TRY_EXCEPT", "try:\n    try:\n        pass\n    except {exc1}:\n        pass\nexcept {exc2}:\n    pass"),
    ("TE26TryInWhile_{exc}_{var}", "TRY_EXCEPT", "while {var} > 0:\n    try:\n        {var} -= 1\n    except {exc}:\n        {var} = 0"),
    ("TE27TryInFor_{exc}_{var}", "TRY_EXCEPT", "for {var} in range(5):\n    try:\n        pass\n    except {exc}:\n        continue"),
    ("TE28TryInIf_{exc}_{var}", "TRY_EXCEPT", "if {var} > 0:\n    try:\n        pass\n    except {exc}:\n        pass"),
    ("TE29IfInTry_{exc}_{var}", "TRY_EXCEPT", "try:\n    if {var} > 0:\n        pass\nexcept {exc}:\n    pass"),
    ("TE30TryExceptBreak_{exc}_{var}", "TRY_EXCEPT", "for {var} in range(10):\n    try:\n        if {var} == 5:\n            break\n    except {exc}:\n        pass"),
    ("TE31TryExceptContinue_{exc}_{var}", "TRY_EXCEPT", "for {var} in range(10):\n    try:\n        if {var} == 5:\n            continue\n    except {exc}:\n        pass"),
    ("TE32TryExceptReturn_{exc}", "TRY_EXCEPT", "def f():\n    try:\n        return 1\n    except {exc}:\n        return 0"),
    ("TE33TryFinallyReturn", "TRY_EXCEPT", "def f():\n    try:\n        return 1\n    finally:\n        pass"),
    ("TE34TryExceptElseFinally_{exc}_{var}", "TRY_EXCEPT", "try:\n    {var} = 1\nexcept {exc}:\n    {var} = 0\nelse:\n    {var} += 1\nfinally:\n    {var} = -1"),
]

WITH_TEMPLATES: List[Tuple[str, str, str]] = [
    ("W01WithAs_{var}", "WITH_REGION", "with open('f') as {var}:\n    pass"),
    ("W02WithAsExpr_{var}", "WITH_REGION", "with open('f') as {var}:\n    {var}.read()"),
    ("W03MultiContext_{var1}_{var2}", "WITH_REGION", "with open('a') as {var1}, open('b') as {var2}:\n    pass"),
    ("W04NestedWith_{var1}_{var2}", "WITH_REGION", "with open('a') as {var1}:\n    with open('b') as {var2}:\n        pass"),
    ("W05WithTry_{var}_{exc}", "WITH_REGION", "try:\n    with open('f') as {var}:\n        pass\nexcept {exc}:\n    pass"),
    ("W06WithReturn_{var}", "WITH_REGION", "def f():\n    with open('f') as {var}:\n        return {var}"),
    ("W07WithRaise_{var}_{exc}", "WITH_REGION", "with open('f') as {var}:\n    raise {exc}"),
    ("W08WithBreak_{var}", "WITH_REGION", "for {var} in range(10):\n    with open('f') as f:\n        break"),
    ("W09WithNoAs", "WITH_REGION", "with open('f'):\n    pass"),
    ("W10WithMultiStmt_{var}", "WITH_REGION", "with open('f') as {var}:\n    {var}.read()\n    {var}.close()"),
    ("W11WithAssign_{var}", "WITH_REGION", "with open('f') as {var}:\n    x = {var}"),
    ("W12WithIf_{var}", "WITH_REGION", "with open('f') as {var}:\n    if {var}:\n        pass"),
    ("W13WithFor_{var}", "WITH_REGION", "with open('f') as {var}:\n    for i in range(3):\n        pass"),
    ("W14WithWhile_{var}", "WITH_REGION", "with open('f') as {var}:\n    while {var}:\n        break"),
    ("W15WithTry_{var}_{exc}", "WITH_REGION", "with open('f') as {var}:\n    try:\n        pass\n    except {exc}:\n        pass"),
    ("W16NestedWith_{var1}_{var2}", "WITH_REGION", "with open('a') as {var1}:\n    with open('b') as {var2}:\n        pass"),
    ("W17WithReturn_{var}", "WITH_REGION", "def f():\n    with open('f') as {var}:\n        return {var}"),
    ("W18WithRaise_{var}_{exc}", "WITH_REGION", "with open('f') as {var}:\n    raise {exc}"),
    ("W19WithBreak_{var}", "WITH_REGION", "for {var} in range(10):\n    with open('f') as f:\n        break"),
    ("W20WithContinue_{var}", "WITH_REGION", "for {var} in range(10):\n    with open('f') as f:\n        continue"),
    ("W21WithElse_{var}", "WITH_REGION", "with open('f') as {var}:\n    pass\nx = 1"),
    ("W22WithMultiContext_{var1}_{var2}", "WITH_REGION", "with open('a') as {var1}, open('b') as {var2}:\n    pass"),
    ("W23WithInTry_{var}_{exc}", "WITH_REGION", "try:\n    with open('f') as {var}:\n        pass\nexcept {exc}:\n    pass"),
    ("W24WithInIf_{var}", "WITH_REGION", "if True:\n    with open('f') as {var}:\n        pass"),
    ("W25WithInFor_{var}", "WITH_REGION", "for i in range(3):\n    with open('f') as {var}:\n        pass"),
    ("W26WithInWhile_{var}", "WITH_REGION", "while True:\n    with open('f') as {var}:\n        break"),
    ("W27WithAssert_{var}", "WITH_REGION", "with open('f') as {var}:\n    assert {var}"),
    ("W28WithPass_{var}", "WITH_REGION", "with open('f') as {var}:\n    pass"),
    ("W29WithPrint_{var}", "WITH_REGION", "with open('f') as {var}:\n    print({var})"),
    ("W30WithCustomCtx", "WITH_REGION", "class Ctx:\n    def __enter__(self): return self\n    def __exit__(self, *a): pass\nwith Ctx() as c:\n    pass"),
    ("W31WithLock", "WITH_REGION", "import threading\nlock = threading.Lock()\nwith lock:\n    pass"),
]

MATCH_TEMPLATES: List[Tuple[str, str, str]] = [
    ("M01MatchLiteral_{var}", "MATCH_REGION", "match {var}:\n    case 1:\n        pass\n    case 2:\n        pass"),
    ("M02MatchLiteralStr_{var}", "MATCH_REGION", "match {var}:\n    case 'a':\n        pass\n    case 'b':\n        pass"),
    ("M03MatchClass_{var}", "MATCH_REGION", "match {var}:\n    case int():\n        pass\n    case str():\n        pass"),
    ("M04MatchSequence_{var1}_{var2}", "MATCH_REGION", "match [{var1}, {var2}]:\n    case [1, 2]:\n        pass\n    case [3, 4]:\n        pass"),
    ("M05MatchMapping_{var}", "MATCH_REGION", "match {var}:\n    case {{'key': 1}}:\n        pass"),
    ("M06MatchGuard_{var}", "MATCH_REGION", "match {var}:\n    case int() if {var} > 0:\n        pass"),
    ("M07MatchDefault_{var}", "MATCH_REGION", "match {var}:\n    case 1:\n        pass\n    case _:\n        pass"),
    ("M08MatchOr_{var}", "MATCH_REGION", "match {var}:\n    case 1 | 2:\n        pass"),
    ("M09MatchAs_{var1}_{var2}", "MATCH_REGION", "match {var}:\n    case [1, 2] as {var2}:\n        pass"),
    ("M10MatchStar_{var1}_{var2}", "MATCH_REGION", "match {var1}:\n    case [1, *{var2}]:\n        pass"),
    ("M11MatchMultiCase_{var}", "MATCH_REGION", "match {var}:\n    case 1:\n        pass\n    case 2:\n        pass\n    case 3:\n        pass"),
    ("M12MatchMultiType_{var}", "MATCH_REGION", "match {var}:\n    case int():\n        pass\n    case str():\n        pass\n    case float():\n        pass"),
    ("M13MatchClassArgs_{var}", "MATCH_REGION", "match {var}:\n    case int(1):\n        pass\n    case int(2):\n        pass"),
    ("M14MatchSequenceLong_{var1}_{var2}", "MATCH_REGION", "match [{var1}, {var2}, 3]:\n    case [1, 2, 3]:\n        pass\n    case [4, 5, 6]:\n        pass"),
    ("M15MatchMappingKey_{var}", "MATCH_REGION", "match {var}:\n    case {{'x': 1}}:\n        pass\n    case {{'y': 2}}:\n        pass"),
    ("M16MatchGuardComplex_{var}", "MATCH_REGION", "match {var}:\n    case int() if {var} > 0 and {var} < 100:\n        pass"),
    ("M17MatchOrMulti_{var}", "MATCH_REGION", "match {var}:\n    case 1 | 2 | 3:\n        pass"),
    ("M18MatchAsUse_{var1}_{var2}", "MATCH_REGION", "match {var1}:\n    case int() as {var2}:\n        pass"),
    ("M19MatchStarMiddle_{var1}_{var2}", "MATCH_REGION", "match {var1}:\n    case [1, *{var2}, 3]:\n        pass"),
    ("M20MatchDefaultFirst_{var}", "MATCH_REGION", "match {var}:\n    case _:\n        pass"),
    ("M21MatchNested_{var}", "MATCH_REGION", "match {var}:\n    case [1, [2, 3]]:\n        pass\n    case [4, [5, 6]]:\n        pass"),
    ("M22MatchInIf_{var}", "MATCH_REGION", "if True:\n    match {var}:\n        case 1:\n            pass"),
    ("M23MatchInFor_{var}", "MATCH_REGION", "for i in range(3):\n    match {var}:\n        case 1:\n            pass"),
    ("M24MatchInTry_{var}_{exc}", "MATCH_REGION", "try:\n    match {var}:\n        case 1:\n            pass\nexcept {exc}:\n    pass"),
    ("M25MatchReturn_{var}", "MATCH_REGION", "def f({var}):\n    match {var}:\n        case 1:\n            return 1\n        case _:\n            return 0"),
    ("M26MatchAssign_{var}", "MATCH_REGION", "match {var}:\n    case 1:\n        x = 1\n    case _:\n        x = 0"),
    ("M27MatchBool_{var}", "MATCH_REGION", "match {var}:\n    case True:\n        pass\n    case False:\n        pass"),
    ("M28MatchNone_{var}", "MATCH_REGION", "match {var}:\n    case None:\n        pass"),
    ("M29MatchStringMulti_{var}", "MATCH_REGION", "match {var}:\n    case 'a':\n        pass\n    case 'b':\n        pass\n    case 'c':\n        pass"),
    ("M30MatchClassMultiAttr_{var}", "MATCH_REGION", "match {var}:\n    case int(x=1):\n        pass"),
]

BOOLOP_TEMPLATES: List[Tuple[str, str, str]] = [
    ("BO01And_{var1}_{var2}", "BOOL_OP", "{var1} and {var2}"),
    ("BO02Or_{var1}_{var2}", "BOOL_OP", "{var1} or {var2}"),
    ("BO03Not_{var}", "BOOL_OP", "not {var}"),
    ("BO04AndOr_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} and {var2} or {var3}"),
    ("BO05OrAnd_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} or {var2} and {var3}"),
    ("BO06AndAssign_{var1}_{var2}", "BOOL_OP", "{var1} = {var2} and True"),
    ("BO07OrAssign_{var1}_{var2}", "BOOL_OP", "{var1} = {var2} or False"),
    ("BO08AndCondition_{var1}_{var2}", "BOOL_OP", "if {var1} and {var2}:\n    pass"),
    ("BO09OrCondition_{var1}_{var2}", "BOOL_OP", "if {var1} or {var2}:\n    pass"),
    ("BO10NotCondition_{var}", "BOOL_OP", "if not {var}:\n    pass"),
    ("BO11CompoundAnd_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} and {var2} and {var3}"),
    ("BO12CompoundOr_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} or {var2} or {var3}"),
    ("BO13NotAnd_{var1}_{var2}", "BOOL_OP", "not ({var1} and {var2})"),
    ("BO14NotOr_{var1}_{var2}", "BOOL_OP", "not ({var1} or {var2})"),
    ("BO15AndReturn_{var1}_{var2}", "BOOL_OP", "def f():\n    return {var1} and {var2}"),
    ("BO16OrReturn_{var1}_{var2}", "BOOL_OP", "def f():\n    return {var1} or {var2}"),
    ("BO17AndWhile_{var1}_{var2}", "BOOL_OP", "while {var1} and {var2}:\n    {var1} = False"),
    ("BO18OrWhile_{var1}_{var2}", "BOOL_OP", "while {var1} or {var2}:\n    {var1} = False"),
    ("BO19CompareAnd_{var1}_{var2}", "BOOL_OP", "{var1} > 0 and {var2} > 0"),
    ("BO20CompareOr_{var1}_{var2}", "BOOL_OP", "{var1} > 0 or {var2} > 0"),
    ("BO21And3_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} and {var2} and {var3}"),
    ("BO22Or3_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} or {var2} or {var3}"),
    ("BO23AndOrAnd_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} and {var2} or {var3} and True"),
    ("BO24OrAndOr_{var1}_{var2}_{var3}", "BOOL_OP", "{var1} or {var2} and {var3} or False"),
    ("BO25NotAnd_{var1}_{var2}", "BOOL_OP", "not {var1} and {var2}"),
    ("BO26NotOr_{var1}_{var2}", "BOOL_OP", "not {var1} or {var2}"),
    ("BO27AndCompare_{var1}_{var2}", "BOOL_OP", "{var1} > 0 and {var2} < 10"),
    ("BO28OrCompare_{var1}_{var2}", "BOOL_OP", "{var1} > 0 or {var2} < 10"),
    ("BO29AndAssignVar_{var1}_{var2}", "BOOL_OP", "{var1} = {var2} and 3"),
    ("BO30OrAssignVar_{var1}_{var2}", "BOOL_OP", "{var1} = {var2} or 3"),
    ("BO31AndInIf_{var1}_{var2}", "BOOL_OP", "if {var1} and {var2}:\n    {var1} = 0"),
    ("BO32OrInIf_{var1}_{var2}", "BOOL_OP", "if {var1} or {var2}:\n    {var1} = 0"),
    ("BO33AndInWhile_{var1}_{var2}", "BOOL_OP", "while {var1} and {var2}:\n    {var1} = 0"),
    ("BO34OrInWhile_{var1}_{var2}", "BOOL_OP", "while {var1} or {var2}:\n    {var1} = 0"),
    ("BO35AndReturn_{var1}_{var2}", "BOOL_OP", "def f():\n    return {var1} and {var2}"),
    ("BO36OrReturn_{var1}_{var2}", "BOOL_OP", "def f():\n    return {var1} or {var2}"),
    ("BO37NotCompare_{var}", "BOOL_OP", "not {var} > 0"),
    ("BO38AndNone_{var1}_{var2}", "BOOL_OP", "{var1} is not None and {var2} is not None"),
    ("BO39OrNone_{var1}_{var2}", "BOOL_OP", "{var1} is None or {var2} is None"),
    ("BO40AndIn_{var1}_{var2}", "BOOL_OP", "{var1} in [1, 2] and {var2} in [3, 4]"),
]

TERNARY_TEMPLATES: List[Tuple[str, str, str]] = [
    ("TN01SimpleTernary_{var}_{const}", "TERNARY", "{var} if {var} > 0 else {const}"),
    ("TN02TernaryAssign_{var1}_{var2}_{const}", "TERNARY", "{var1} = {var2} if {var2} > 0 else {const}"),
    ("TN03TernaryReturn_{var}_{const}", "TERNARY", "def f({var}):\n    return {var} if {var} > 0 else {const}"),
    ("TN04NestedTernary_{var}", "TERNARY", "'a' if {var} > 0 else 'b' if {var} == 0 else 'c'"),
    ("TN05TernaryAsArg_{var}", "TERNARY", "print({var} if {var} > 0 else 0)"),
    ("TN06TernaryCompare_{var1}_{var2}", "TERNARY", "{var1} if {var1} > {var2} else {var2}"),
    ("TN07TernaryBool_{var1}_{var2}", "TERNARY", "{var1} if {var1} and {var2} else 0"),
    ("TN08TernaryAssignNested_{var1}_{var2}", "TERNARY", "{var1} = 1 if {var2} > 0 else 2 if {var2} == 0 else 3"),
    ("TN09TernaryInList_{var}", "TERNARY", "[{var} if {var} > 0 else 0]"),
    ("TN10TernaryInDict_{var}", "TERNARY", "{{'k': {var} if {var} > 0 else 0}}"),
    ("TN11TernaryEq_{var}_{const}", "TERNARY", "{var} if {var} == {const} else 0"),
    ("TN12TernaryNeq_{var}_{const}", "TERNARY", "{var} if {var} != {const} else 0"),
    ("TN13TernaryLt_{var}_{const}", "TERNARY", "{var} if {var} < {const} else 0"),
    ("TN14TernaryGt_{var}_{const}", "TERNARY", "{var} if {var} > {const} else 0"),
    ("TN15TernaryLe_{var}_{const}", "TERNARY", "{var} if {var} <= {const} else 0"),
    ("TN16TernaryGe_{var}_{const}", "TERNARY", "{var} if {var} >= {const} else 0"),
    ("TN17TernaryIn_{var}", "TERNARY", "{var} if {var} in [1, 2] else 0"),
    ("TN18TernaryNotIn_{var}", "TERNARY", "{var} if {var} not in [1, 2] else 0"),
    ("TN19TernaryIs_{var}", "TERNARY", "{var} if {var} is not None else 0"),
    ("TN20TernaryAnd_{var1}_{var2}", "TERNARY", "{var1} if {var1} and {var2} else 0"),
    ("TN21TernaryOr_{var1}_{var2}", "TERNARY", "{var1} if {var1} or {var2} else 0"),
    ("TN22TernaryNot_{var}", "TERNARY", "{var} if not {var} else 0"),
    ("TN23TernaryStr_{var}", "TERNARY", "'yes' if {var} else 'no'"),
    ("TN24TernaryBool_{var}", "TERNARY", "True if {var} else False"),
    ("TN25TernaryNone_{var}", "TERNARY", "{var} if {var} else None"),
]

NESTED_TEMPLATES: List[Tuple[str, str, str]] = [
    ("N01IfInWhile_{var}", "NESTED", "while {var} > 0:\n    if {var} > 5:\n        {var} -= 2\n    else:\n        {var} -= 1"),
    ("N02IfInFor_{var}", "NESTED", "for {var} in range(10):\n    if {var} > 5:\n        continue"),
    ("N03ForInIf_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    for {var2} in range({var1}):\n        pass"),
    ("N04WhileInIf_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    while {var2} > 0:\n        {var2} -= 1"),
    ("N05TryInFor_{var}_{exc}", "NESTED", "for {var} in range(10):\n    try:\n        pass\n    except {exc}:\n        continue"),
    ("N06ForInTry_{var}_{exc}", "NESTED", "try:\n    for {var} in range(10):\n        pass\nexcept {exc}:\n    pass"),
    ("N07IfInTry_{var}_{exc}", "NESTED", "try:\n    if {var} > 0:\n        pass\nexcept {exc}:\n    pass"),
    ("N08TryInIf_{var}_{exc}", "NESTED", "if {var} > 0:\n    try:\n        pass\n    except {exc}:\n        pass"),
    ("N09WhileInWhile_{var1}_{var2}", "NESTED", "while {var1} > 0:\n    {var2} = 5\n    while {var2} > 0:\n        {var2} -= 1\n    {var1} -= 1"),
    ("N10ForInFor_{var1}_{var2}", "NESTED", "for {var1} in range(3):\n    for {var2} in range(3):\n        pass"),
    ("N11IfInIf_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    if {var2} > 0:\n        pass"),
    ("N12IfElifInFor_{var}", "NESTED", "for {var} in range(10):\n    if {var} > 7:\n        pass\n    elif {var} > 3:\n        pass\n    else:\n        pass"),
    ("N13TryInWhile_{var}_{exc}", "NESTED", "while {var} > 0:\n    try:\n        {var} -= 1\n    except {exc}:\n        {var} = 0"),
    ("N14WithInFor_{var}", "NESTED", "for {var} in range(3):\n    with open('f') as f:\n        pass"),
    ("N15ForInWhile_{var1}_{var2}", "NESTED", "while {var1} > 0:\n    for {var2} in range({var1}):\n        pass\n    {var1} -= 1"),
    ("N16IfInIfElse_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    if {var2} > 0:\n        pass\n    else:\n        pass\nelse:\n    pass"),
    ("N17ForInIfElse_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    for {var2} in range(3):\n        pass\nelse:\n    pass"),
    ("N18WhileInIfElse_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    while {var2} > 0:\n        {var2} -= 1\nelse:\n    {var1} = 0"),
    ("N19TryInIfElse_{var1}_{exc}", "NESTED", "if {var1} > 0:\n    try:\n        pass\n    except {exc}:\n        pass\nelse:\n    pass"),
    ("N20IfInForBody_{var1}_{var2}", "NESTED", "for {var1} in range(5):\n    if {var1} > 2:\n        {var2} = {var1}"),
    ("N21IfInWhileBody_{var1}_{var2}", "NESTED", "while {var1} > 0:\n    if {var1} > 2:\n        {var2} = {var1}\n    {var1} -= 1"),
    ("N22ForInForBreak_{var1}_{var2}", "NESTED", "for {var1} in range(3):\n    for {var2} in range(3):\n        if {var2} == 1:\n            break"),
    ("N23WhileInWhileBreak_{var1}_{var2}", "NESTED", "while {var1} > 0:\n    while {var2} > 0:\n        {var2} -= 1\n        if {var2} == 0:\n            break\n    {var1} -= 1"),
    ("N24TryInTry_{exc1}_{exc2}", "NESTED", "try:\n    try:\n        pass\n    except {exc1}:\n        pass\nexcept {exc2}:\n    pass"),
    ("N25WithInWith_{var1}_{var2}", "NESTED", "with open('a') as {var1}:\n    with open('b') as {var2}:\n        pass"),
    ("N26IfInTryExcept_{var}_{exc}", "NESTED", "try:\n    if {var} > 0:\n        pass\nexcept {exc}:\n    pass"),
    ("N27ForInTryExcept_{var}_{exc}", "NESTED", "try:\n    for {var} in range(3):\n        pass\nexcept {exc}:\n    pass"),
    ("N28WhileInTryExcept_{var}_{exc}", "NESTED", "try:\n    while {var} > 0:\n        {var} -= 1\nexcept {exc}:\n    pass"),
    ("N29IfElifInWhile_{var1}_{var2}", "NESTED", "while {var1} > 0:\n    if {var1} > 5:\n        {var1} -= 2\n    elif {var1} > 2:\n        {var1} -= 1\n    else:\n        {var1} = 0"),
    ("N30IfInForBreak_{var1}_{var2}", "NESTED", "for {var1} in range(10):\n    if {var1} > 5:\n        break"),
    ("N31ForInIfBreak_{var1}_{var2}", "NESTED", "if {var1} > 0:\n    for {var2} in range(10):\n        if {var2} > 5:\n            break"),
    ("N32TryInForBreak_{var1}_{exc}", "NESTED", "for {var1} in range(10):\n    try:\n        if {var1} == 5:\n            break\n    except {exc}:\n        continue"),
    ("N33IfInTryFinally_{var}_{exc}", "NESTED", "try:\n    if {var} > 0:\n        pass\nexcept {exc}:\n    pass\nfinally:\n    pass"),
    ("N34ForWhileIf_{var1}_{var2}", "NESTED", "for {var1} in range(5):\n    while {var2} > 0:\n        if {var2} > 2:\n            {var2} -= 1\n        else:\n            break"),
    ("N35DeepNested_{var1}_{var2}_{exc}", "NESTED", "if {var1} > 0:\n    for {var2} in range(3):\n        try:\n            if {var2} == 1:\n                pass\n        except {exc}:\n            pass"),
]

ALL_TEMPLATES: Dict[str, List[Tuple[str, str, str]]] = {
    'basic': BASIC_TEMPLATES,
    'if_region': IF_TEMPLATES,
    'while_loop': WHILE_TEMPLATES,
    'for_loop': FOR_TEMPLATES,
    'try_except': TRY_EXCEPT_TEMPLATES,
    'with_region': WITH_TEMPLATES,
    'match_region': MATCH_TEMPLATES,
    'boolop': BOOLOP_TEMPLATES,
    'ternary': TERNARY_TEMPLATES,
    'nested': NESTED_TEMPLATES,
}

REGION_DIR_MAP = {
    'basic': 'basic',
    'if_region': 'if_region',
    'while_loop': 'while_loop',
    'for_loop': 'for_loop',
    'try_except': 'try_except',
    'with_region': 'with_region',
    'match_region': 'match_region',
    'boolop': 'boolop',
    'ternary': 'ternary',
    'nested': 'nested',
}


def _pick_vars(n: int, offset: int = 0) -> List[str]:
    return [VARIABLES[(i + offset) % len(VARIABLES)] for i in range(n)]


def _pick_consts(n: int, offset: int = 0) -> List[str]:
    pool = CONSTANTS_INT + CONSTANTS_STR + CONSTANTS_FLOAT
    return [pool[(i + offset) % len(pool)] for i in range(n)]


def _pick_exc(n: int, offset: int = 0) -> List[str]:
    return [EXCEPTIONS[(i + offset) % len(EXCEPTIONS)] for i in range(n)]


def _pick_funcs(n: int, offset: int = 0) -> List[str]:
    return [CALLABLES[(i + offset) % len(CALLABLES)] for i in range(n)]


def _resolve_template(template_name: str, source_template: str, variant: int) -> Tuple[str, str]:
    var_count = source_template.count('{var') + source_template.count('{var1}') + source_template.count('{var2}') + source_template.count('{var3}')
    const_count = source_template.count('{const') + source_template.count('{const1}') + source_template.count('{const2}')
    exc_count = source_template.count('{exc') + source_template.count('{exc1}') + source_template.count('{exc2}')
    func_count = source_template.count('{func')
    mod_count = source_template.count('{mod}')
    name_count = source_template.count('{name}')

    kwargs = {}
    offset = variant * 3

    var_idx = 0
    for key in ['var', 'var1', 'var2', 'var3']:
        if '{' + key + '}' in source_template or ('{' + key + '_') in source_template:
            kwargs[key] = _pick_vars(1, offset + var_idx)[0]
            var_idx += 1

    const_idx = 0
    for key in ['const', 'const1', 'const2']:
        if '{' + key + '}' in source_template:
            kwargs[key] = _pick_consts(1, offset + const_idx)[0]
            const_idx += 1

    exc_idx = 0
    for key in ['exc', 'exc1', 'exc2']:
        if '{' + key + '}' in source_template:
            kwargs[key] = _pick_exc(1, offset + exc_idx)[0]
            exc_idx += 1

    for key in ['func']:
        if '{' + key + '}' in source_template:
            kwargs[key] = _pick_funcs(1, offset)[0]

    for key in ['mod']:
        if '{' + key + '}' in source_template:
            modules = ['os', 'sys', 'json', 'math', 're', 'collections', 'itertools', 'functools']
            kwargs[key] = modules[(offset) % len(modules)]

    for key in ['name']:
        if '{' + key + '}' in source_template:
            names = ['path', 'exit', 'dumps', 'sqrt', 'findall', 'Counter', 'chain', 'partial']
            kwargs[key] = names[(offset) % len(names)]

    try:
        resolved_source = source_template.format(**kwargs)
    except KeyError:
        resolved_source = source_template

    safe_name = template_name
    for k, v in kwargs.items():
        safe_name = safe_name.replace('{' + k + '}', str(v))
    safe_name = safe_name.replace('{', '').replace('}', '')

    return safe_name, resolved_source


def generate_test_file(region_type: str, template: Tuple[str, str, str], variant: int, output_dir: str) -> str:
    template_name, region, source_template = template

    safe_name, resolved_source = _resolve_template(template_name, source_template, variant)

    class_name = f"Test{safe_name}"
    file_name = f"test_{safe_name.lower()}.py"
    file_path = os.path.join(output_dir, file_name)

    escaped_source = resolved_source.replace('\\', '\\\\').replace("'''", "\\'\\'\\'")

    content = f'''import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class {class_name}(ExhaustiveTestCase):
    SOURCE_CODE = """{escaped_source}"""
    REGION_TYPE = "{region}"

    def test_decompile(self):
        self.verify_decompilation()
'''

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path


def generate_all_tests(target_types: List[str] = None, variants_per_template: int = 3) -> Dict[str, int]:
    counts = {}

    types_to_generate = target_types if target_types else list(ALL_TEMPLATES.keys())

    for region_type in types_to_generate:
        templates = ALL_TEMPLATES.get(region_type, [])
        if not templates:
            continue

        dir_name = REGION_DIR_MAP.get(region_type, region_type)
        output_dir = os.path.join(EXHAUSTIVE_DIR, dir_name)
        os.makedirs(output_dir, exist_ok=True)

        count = 0
        for template in templates:
            for variant in range(variants_per_template):
                try:
                    generate_test_file(region_type, template, variant, output_dir)
                    count += 1
                except Exception as e:
                    print(f"警告: 生成测试失败 {template[0]} variant={variant}: {e}")

        counts[region_type] = count
        print(f"  {region_type}: 生成 {count} 个测试文件")

    return counts


def main():
    import argparse

    parser = argparse.ArgumentParser(description='穷举测试自动生成器')
    parser.add_argument(
        '--type', '-t',
        nargs='*',
        choices=list(ALL_TEMPLATES.keys()),
        help='指定要生成的区域类型（可多选）'
    )
    parser.add_argument(
        '--variants', '-v',
        type=int,
        default=3,
        help='每个模板生成的变体数量（默认3）'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("穷举测试自动生成器")
    print("=" * 60)
    print()

    counts = generate_all_tests(args.type, args.variants)

    total = sum(counts.values())
    print(f"\n总计生成 {total} 个测试文件")
    print(f"覆盖 {len(counts)} 种区域类型")


if __name__ == '__main__':
    main()
