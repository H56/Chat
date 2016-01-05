import threading

__author__ = 'hupeng'

mutex = threading.Lock()


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            global mutex
            with mutex:
                instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton
