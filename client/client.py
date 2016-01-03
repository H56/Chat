import Queue
import threading
import getpass
import hashlib
import socket
import logging
from threading import Timer
import getch

__author__ = 'hupeng'

REGISTER = 0
LOGIN = 1
HEARTBEAT = 2
LOGOUT = 3
MESSAGE = 4


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
                msg = input('Message: ')
                self.show()
                self.send_to_server(MESSAGE, msg)
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
        while self.receive:
            data = self.socket.recv(1024)
            self.message_queue.put(data + '\r\n')

    def register(self):
        while True:
            self.UserName = raw_input('User Name: ')
            self.send_to_server(REGISTER, str(self.UserName))
            data = self.socket.recv(1024)
            mid = data.find('\1')
            if int(data[0: mid]) == REGISTER and int(data[mid: -1]) != 0:
                break
        password = getpass.getpass()
        count = 1
        while getpass.getpass('Verify your password: ') != password:
            print('The two password do not match! Please re-verify your password.')
            if count == 3:
                print('It is failed to verify your password for too many times! Please retype your password.')
                password = getpass.getpass('Retype Password: ')
            count += 1
        self.send_to_server(REGISTER, str(self.UserName) + '\1' + hashlib.sha1(password).hexdigest())

    def login(self):
        self.UserName = raw_input('User Name:')
        password = getpass.getpass()
        self.send_to_server(LOGIN, str(self.UserName) + hashlib.sha1(password).hexdigest())

    def send_to_server(self, method, msg):
        if method == REGISTER:
            self.socket.sendto(str(method) + '\1' + msg)
        elif method == LOGIN:
            self.socket.sendto(str(method) + '\1' + msg)
        elif method == HEARTBEAT:
            self.socket.sendto(str(method) + '\1' + msg)
        elif method == LOGOUT:
            self.socket.sendto(str(method) + '\1' + msg)


def main():
    client = Client()
    client.start()
    client.get_data()


if __name__ == '__main__':
    main()
