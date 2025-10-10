from .acquire import acquire
import threading
import gc


_GC_DISABLE_COUNT = 0
_GC_DISABLE_COUNT_LOCK = threading.Lock()


# 停用GC
def gc_disable():
    with acquire(_GC_DISABLE_COUNT_LOCK, timeout=1):
        global _GC_DISABLE_COUNT
        _GC_DISABLE_COUNT += 1
        if _GC_DISABLE_COUNT > 1:
            return
    gc.disable()


# 启用GC
def gc_enable():
    with acquire(_GC_DISABLE_COUNT_LOCK, timeout=1):
        global _GC_DISABLE_COUNT
        _GC_DISABLE_COUNT -= 1
        if _GC_DISABLE_COUNT > 0:
            return
    gc.enable()
