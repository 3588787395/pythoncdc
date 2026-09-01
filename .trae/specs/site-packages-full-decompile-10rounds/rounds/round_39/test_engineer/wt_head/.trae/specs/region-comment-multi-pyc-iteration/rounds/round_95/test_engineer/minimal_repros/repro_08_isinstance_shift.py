# R95 minimal repro 08: isinstance check shift
def repro_08(fields):
    if isinstance(fields, str):
        fields = [fields]
    return fields
