## ADDED Requirements

### Requirement: Break in match case inside for loop preserved
When a `break` statement appears inside a match case that is within a for loop, the decompiled output SHALL contain the `break` statement.

#### Scenario: Break in match case in for loop
- **WHEN** source code is `for i in range(5):\n    match i%3:\n        case 0:\n            print('zero')\n        case 1:\n            continue\n        case _:\n            break`
- **THEN** decompiled output preserves the `break` in the wildcard case and `continue` in case 1

### Requirement: Continue in match case inside loop preserved
When a `continue` statement appears inside a match case that is within a loop, the decompiled output SHALL contain the `continue` statement.

#### Scenario: Continue in match case in for loop
- **WHEN** source code is `for i in range(5):\n    match x:\n        case 1:\n            continue\n        case _:\n            pass`
- **THEN** decompiled output contains `continue` in case 1

### Requirement: Return in match case inside loop preserved
When a `return` statement appears inside a match case within a loop inside a function, the decompiled output SHALL contain the `return` statement.

#### Scenario: Return in match case in loop inside function
- **WHEN** source code is `def f():\n    for i in range(5):\n        match i:\n            case 3:\n                return i`
- **THEN** decompiled output contains `return i` in case 3

### Requirement: Module-level return None filtered in nested bodies
When `return None` appears inside an if/for/while/match body at module level (where `return` is a syntax error), it SHALL be filtered out recursively, not just from the top-level module body.

#### Scenario: Return None inside module-level if
- **WHEN** `if x:\n    z = a if b else c` is decompiled at module level and the AST contains `return None` inside the if-body
- **THEN** the `return None` is removed from the if-body, producing valid Python syntax

#### Scenario: Return None inside module-level for
- **WHEN** `for i in range(3):\n    if i == 1:\n        break` is decompiled at module level and the AST contains `return None` inside the for-body
- **THEN** the `return None` is removed from the for-body
