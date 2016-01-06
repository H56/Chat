import random
import time
import sys
import access

__author__ = 'HuPeng'


class User:
    uid = None
    name = None
    status = None
    login_time = None
    logout_time = None

    def __init__(self, uid, status):
        self.uid = uid
        self.name = uid
        self.status = status
        self.login_time = time.time()
        self.login()
        self.access = None

    def login(self):
        self.login_time = time.time()

    def logout(self):
        self.logout_time = time.time()
        if not self.access:
            self.access = access.AccessDao()
        self.access.logout(self.uid, [self.login_time, self.logout_time])

    def get_pre_login_time(self):
        if not self.access:
            self.access = access.AccessDao
        return self.access.getprelogintime(self.name)

    def get_name(self):
        if self.name:
            return self.name
        else:
            if not self.access:
                self.access = access.AccessDao()
            self.name = self.access.getname(self.uid)
            return self.name

    def register(self, info):
        if 'name' not in info:
            raise Exception('No name')
        if 'passwd' not in info:
            raise Exception('No passwd')
        if 'uid' in info:
            if not self.access:
                self.access = access.AccessDao()
            self.access.register(info['uid'], info['name'], info['passwd'])
        else:
            uid = random.randint(0, sys.maxint)
            while not self.access.have_id(uid):
                uid = random.randint(0, sys.maxint)
            if not self.access:
                self.access = access.AccessDao()
            self.access.register(uid, info['name'], info['passwd'])
