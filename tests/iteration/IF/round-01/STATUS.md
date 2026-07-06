# Round 01 - IF

- **State**: insufficient_bugs
- **Total tested**: 491
- **Bugs found**: 4 (non-C: 4, C-class: 0)
- **Bugs fixed**: 0
- **Threshold met**: False

## Bug List

- **422**: MISSING_ELIF
- **429**: MISSING_ELIF
- **430**: MISSING_ELIF
- **431**: MISSING_ELIF

## Bug Details

### 422: MISSING_ELIF
**Source:**
```python
if a and (b or c):
    r = 1
elif z:
    r = 2
```
**Actual:**
```python
b if a else z
```

### 429: MISSING_ELIF
**Source:**
```python
if a and b:
    if c:
        r = 1
    elif d:
        r = 2
elif z:
    r = 3
```
**Actual:**
```python
c if a and b and c else z
```

### 430: MISSING_ELIF
**Source:**
```python
if a or b:
    if c:
        r = 1
    else:
        r = 2
elif z:
    r = 3
```
**Actual:**
```python
if b if a else c or b and c:
    r = 1
else:
    r = 2
if z:
    r = 3
```

### 431: MISSING_ELIF
**Source:**
```python
if a and b:
    if c or d:
        r = 1
    else:
        r = 2
elif z:
    r = 3
```
**Actual:**
```python
if a and b and c or d:
    r = 1
else:
    r = 2
if z:
    r = 3
```
