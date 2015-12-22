import random
import time
import sys
import access

__author__ = 'HuPeng'


class User:
    uid = None
    name = None
    status = None
    passwd = None
    login_time = None
    logout_time = None

    def __init__(self, uid, status, passwd):
        self.uid = uid
        self.status = status
        self.passwd = passwd
        self.login_time = time.time()

    def is_legal(self):
        return access.islegal(self.name, self.passwd)

    def login(self):
        self.login_time = time.time()

    def logout(self):
        self.logout_time = time.time()
        access.logout(self.uid, [self.login_time, self.logout_time])

    def get_pre_login_time(self):
        return access.getprelogintime(self.name)

    def get_name(self):
        if self.name is not None:
            return self.name
        else:
            self.name = access.getname(self.uid)
            return self.name

    @staticmethod
    def register(info):
        if 'name' not in info:
            raise Exception('No name')
        if 'passwd' not in info:
            raise Exception('No passwd')
        if 'uid' in info:
            access.register(info['uid'], info['name'], info['passwd'])
        else:
            uid = random.randint(0, sys.maxint)
            while not access.have_id(uid):
                uid = random.randint(0, sys.maxint)
            access.register(uid, info['name'], info['passwd'])
