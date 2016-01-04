import Queue
import threading
import getpass
import hashlib
import socket
import logging
from threading import Timer
import getch

__author__ = 'hupeng'

REGISTER = 10
LOGIN = 11
LOGOUT = 12

SENDALL = 20
SENDTO = 21
SENDROOM = 22

ENTERHALL = 30
ENTERROOM = 31

HALL = 40
ROOM = 41

HAVENAME = 50
NAMEOK = 51
FAILED = 52
SUCCESS = 53
HAVENONAME = 54
WRONGPASSWD = 55

class Client(threading.Thread):
    def __init__(self, server_address=('localhost', '21313')):
        """
        :type server_port: int
        :type server_address: str
        """
        self.logger = logging.getLogger('Chat-Client')
        log_file = logging.FileHandler('Chat-Client.log')
        log_file.setLevel(logging.DEBUG)
        log_stream = logging.StreamHandler()
        log_stream.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        log_stream.setFormatter(formatter)
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        self.logger.addHandler(log_stream)

        self.server_address = server_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.message_queue = Queue.Queue()
        self.socket.connect(self.server_address)
        self.UserName = None
        self.receive = True

        self.timer_show = None
        self.default = HALL

    def __del__(self):
        self.socket.close()
        if self.timer_show is not None:
            self.timer_show.cancel()

    def show(self):
        while self.message_queue.empty():
            print(self.message_queue.get())
        self.timer_show = Timer(0.05, self.show, ())
        self.timer_show.start()

    def get_data(self):
        while True:
            ch = getch()
            if ch == ' ':
                self.timer_show.cancel()
                msg = input('->')
                self.show()
                end = 0
                operation, end = self.get_word(msg, end)
                if operation == 'sendall':
                    self.send_to_server(SENDALL, msg[end: -1])
                elif operation == 'sendto':
                    user = self.get_word(msg, end)
                    if end >= len(msg):
                        print('''user name or message can't be empty!''')
                    else:
                        self.send_to_server(SENDTO, user, msg[end: -1])
                elif operation == 'sendroom':
                    room = self.get_word(msg, end)
                    if end >= len(msg):
                        print('''room or message can't be empty!''')
                    else:
                        self.send_to_server(SENDROOM, room, msg[end: -1])
                elif operation == 'enter':
                    room = self.get_word(msg, end)
                    if room == 'hall':
                        self.send_to_server(ENTERHALL)
                    else:
                        self.send_to_server(ENTERROOM, room)


            elif ch == '\3':
                self.receive = False
                break

    def run(self):
        print('1: Login\t 2: register')
        while True:
            choice = raw_input('Please choose the action number:')
            try:
                choice_num = int(choice)
            except Exception as e:
                self.logger.error('choice error: ' + str(e))
                print('Please input the right number.')
            else:
                if 0 <= choice < 3:
                    break
                else:
                    print('Please input the right number.')
        if choice_num == 1:
            self.login()
        elif choice_num == 2:
            self.register()
        self.login()
        # -----------input thread-----------
        self.timer_show()
        # data = ''
        while self.receive:
            data = self.socket.recv(1024)
            # self.message_queue.put(data + '\r\n')
            self.sparse_data(data)

    def sparse_data(self, data):
        start = 0
        end = data.find('\1', start)
        operation = data[start: end]
        if operation == REGISTER:
            start = end + 1
            end = data.find('\1', start)
            status = data[start: end]
            if status == chr(HAVENAME):
                print('This name has been used, please rename your account!')
                self.register(0)
            elif status == chr(NAMEOK):
                self.register(1)
            elif status == chr(FAILED):
                print('Unknown reason made the register failed, please re-register!')
                self.register(0)
            elif status == chr(SUCCESS):
                print('Congratulation! Registration successful!')
            else:
                print('Unknown reason made the register failed, please re-register!')
                self.register(0)
        elif operation == LOGIN:
            start = end + 1
            end = data.find('\1', start)
            status = data[start: end]
            if status == SUCCESS:
                print('Congratulation! login is successful!')
            if status == WRONGPASSWD or status == HAVENONAME:
                print('Username or passwd is not correct!')
            elif status == FAILED:
                print('Unknown reason made the register failed, please re-register!')
            else:
                print('Unknown reason made the register failed, please re-register!')
        elif SENDALL:
            start = end + 1
            end = data.find('\1', start)
            user = data[start: end]
            self.message_queue.put('[HALL]' + user + 'said: ' + data[end + 1: -1] + '\r\n')
        elif SENDROOM:
            start = end + 1
            end = data.find('\1', start)
            room = data[start: end]
            start = end + 1
            end = data.find('\1', start)
            user = data[start: end]
            self.message_queue.put('[ROOM:' + room + ']' + user +'said: ' + data[end + 1: -1] + '\r\n')
        elif SENDTO:
            start = end + 1
            end = data.find('\1', start)
            user = data[start: end]
            self.message_queue.put(user + 'said: ' + data[end + 1: -1] + '\r\n')
        elif operation == LOGOUT:
            pass

    def register(self, step=0):
        if step == 0:
            self.UserName = raw_input('User Name: ')
            self.send_to_server(REGISTER, str(self.UserName))
        elif step == 1:
            password = getpass.getpass()
            count = 1
            while getpass.getpass('Verify your password: ') != password:
                print('The two password do not match! Please re-verify your password.')
                if count == 3:
                    print('It is failed to verify your password for too many times! Please retype your password.')
                    password = getpass.getpass('Retype Password: ')
                count += 1
            self.send_to_server(REGISTER, str(self.UserName), hashlib.sha1(password).hexdigest())

    def login(self):
        self.UserName = raw_input('User Name:')
        password = getpass.getpass()
        self.send_to_server(LOGIN, str(self.UserName), hashlib.sha1(password).hexdigest())

    def send_to_server(self, method, *msg):
        send = chr(method)
        for s in msg:
            send += '\1' + s
        self.socket.sendto(send)

    @staticmethod
    def get_word(s, start=0):
        begin = start
        length = len(s)
        while begin < length and s[begin].isspace():
            begin += 1
        if begin >= length:
            return -1
        end = begin
        while not s[end].isspace():
            end += 1
        return s[begin: end], end

def main():
    client = Client()
    client.start()
    client.get_data()


if __name__ == '__main__':
    main()
