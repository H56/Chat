import hashlib
import logging
import threading
import sqlite3

__author__ = 'HuPeng'

mutex_access = threading.Lock()


class AccessDao:
    def __new__(cls, *args, **kwargs):
        global mutex_access
        mutex_access.acquire()
        if not hasattr(cls, '_instance'):
            orig = super(AccessDao, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        mutex_access.release()
        return cls._instance

    def __init__(self):
        self.logger = logging.getLogger('Chat-Server-Access')
        log_file = logging.FileHandler('Chat-Server-Access.log')
        log_file.setLevel(logging.DEBUG)
        log_stream = logging.StreamHandler()
        log_stream.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        log_stream.setFormatter(formatter)
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        self.logger.addHandler(log_stream)

        self.conn = sqlite3.connect("Chat_Hu.db")

    def is_legal(self, uid, upasswd):
        sql = 'SELECT passwd FROM chat_user WHERE uid = ?'
        passwd = self.select_sql(sql, uid)
        return hashlib.sha1(upasswd).hexdigest() == passwd[0]

    def get_pre_login_time(self, uid):
        pass

    def get_name(self, uid):
        sql = 'SELECT uname FROM chat_user WHERE uid = ?'
        uname = self.select_sql(sql, uid)
        return uname[0]

    def logout(self, uid, data):
        pass

    def register(self, uid, uname, upasswd):
        if not self.have_id(uid):
            sql = u'''INSERT INTO chat_user(uid, uname, passwd) value(?, ?, ?)'''
            data = (uid, uname, hashlib.sha1(upasswd).hexdigest())
            self.change_sql(sql, data)
            return True
        else:
            return False

    def have_id(self, uid):
        sql = u'''SELECT * FROM chat_user WHERE uid = ?'''
        return len(self.execute_sql(sql, uid)) > 0

    def select_sql(self, sql, data):
        if sql is not None and sql != '':
            cursor = self.conn.cursor()
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            all_data = cursor.fetchall()
            cursor.close()
            return all_data
        else:
            raise Exception('sql have no data')

    def change_sql(self, sql, data):
        if sql is not None and sql != '':
            cursor = self.conn.cursor()
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            self.conn.commit()
            cursor.close()
        else:
            raise Exception('sql have no data')

    def test_table(self):
        # user
        self.__test__(u'chat_user',
                      u'''CREATE TABLE chat_user(uid VARCHAR(30) PRIMARY KEY, uname VARCHAR(100), passwd CHAR(40))''')

        # login and logout info
        self.__test__(u'logging_info', u'''CREATE TABLE logging_info(id INTEGER PRIMARY KEY, uid VARCHAR(30), '''
                                       u'''login FLOAT, logout FLOAT)''')

    def __test__(self, table, exe):
        try:
            self.con.execute("SELECT * FROM " + table)
        except Exception as e:
            self.logger.info('no' + table + ' table: ' + str(e))
            self.logger.info('======add ' + table + ' table: start======')
            try:
                self.con.execute(exe)
            except Exception as e:
                self.logger.error("create ' + table + ' table error: " + str(e))
                exit(-1)
            self.logger.info('======add ' + table + ' table: end======')
