# DEFECT-REPRO Pattern T: with 块前置 + try/except，except handler entry 被 WithRegion 误消费导致 except 整段丢失
import shutil


def build(src, dst, content):
    with open(src, 'w') as fh:
        fh.write(content)
    error = None
    if error is not None:
        return ('err', error)
    else:
        with open(dst, 'w') as f:
            f.write(content)
        try:
            shutil.copy(src, dst)
        except FileExistsError as e:
            return ('fail', str(e))
    return ('ok', None)
# DEFECT-REPRO
