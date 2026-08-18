"""复现01: try-except内嵌for-else，break后return False被错误放置"""
def validate_data(data):
    if not data:
        return False
    else:
        try:
            for item in data:
                if isinstance(item, int):
                    if item < 0:
                        continue
                    elif item > 100:
                        break
                    else:
                        continue
                else:
                    break
            else:
                return True
            return False
        except Exception as e:
            return False
