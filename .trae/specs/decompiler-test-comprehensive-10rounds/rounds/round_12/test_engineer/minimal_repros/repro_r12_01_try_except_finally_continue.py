# R12 MinRepro 01: try-except-finally with continue (R11 root cause fixed)
# Validates _collect_finally_body_blocks enhancement

def process_items(items):
    results = []
    for item in items:
        try:
            if isinstance(item, str):
                continue
            converted = int(item)
        except (ValueError, TypeError):
            continue
        finally:
            print(f'处理完成项目: {item}')
        results.append(converted)
    return results
