"""m11: module-level try/finally only plus trailing statements."""
try:
    BASE = 1
finally:
    UNIT = 'f'
AFTER = BASE + 1
for i in range(1):
    AFTER += i
