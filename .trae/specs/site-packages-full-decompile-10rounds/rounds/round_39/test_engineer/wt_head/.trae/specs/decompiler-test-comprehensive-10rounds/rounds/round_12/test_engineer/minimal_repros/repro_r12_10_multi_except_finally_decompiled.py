def process(data):
    results = []
    for item in data:
        try:
            v = int(item)
            results.append(v)
        except TypeError:
            results.append(0)
        except ValueError:
            results.append(-1)
        except Exception:
            results.append(-2)
        finally:
            print(f'done {item}')
    else:
        return results
