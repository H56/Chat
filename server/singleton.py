import threading

__author__ = 'hupeng'

mutex = threading.Lock()
mutex_dict = {}


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        global mutex
        with mutex:
            if cls not in mutex_dict:
                mutex_dict[cls] = threading.Lock()

        with mutex_dict[cls]:
            if cls not in instances:
                instances[cls] = cls(*args, **kw)
            return instances[cls]

    return _singleton
