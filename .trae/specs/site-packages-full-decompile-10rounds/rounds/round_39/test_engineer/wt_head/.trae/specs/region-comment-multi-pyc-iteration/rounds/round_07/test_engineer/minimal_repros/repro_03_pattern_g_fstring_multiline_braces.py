# DEFECT-REPRO Pattern G: 多行 f-string 字面花括号 + 两个 FormattedValue
host = '127.0.0.1'
port = 80
cfg = f'{{\n    "host": "{host!s}",\n    "port": {port!s},\n    "opts": {{}},\n}}\n'
print(cfg)
# DEFECT-REPRO
