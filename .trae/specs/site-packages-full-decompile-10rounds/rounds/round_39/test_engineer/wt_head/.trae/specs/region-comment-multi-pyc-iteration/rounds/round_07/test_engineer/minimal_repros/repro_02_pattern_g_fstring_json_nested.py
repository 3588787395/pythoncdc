# DEFECT-REPRO Pattern G: f-string JSON 风格嵌套字面花括号 + FormattedValue
# 镜像 backtestOK.py L69 的 user_code 结构（源码字面花括号已正确转义为 {{ }}）
DEFAULT_PORT = 9000
user_variables = 'uv'
user_code = f',\n    "debug_port": {DEFAULT_PORT!s},\n    "plugin": {{\n        "enabled": True,\n    }},\n    "opts": {{}},\n}}\n\nrun(user_variables={user_variables!s})\n'
print(user_code)
# DEFECT-REPRO
