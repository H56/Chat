import Queue
from duplicity.asyncscheduler import thread
import threading
import getpass
import hashlib
import socket
import logging
from getch import getch

__author__ = 'hupeng'

BUFFERSIZE = 1024

REGISTER = 10
LOGIN = 11
LOGOUT = 12

SENDALL = 20
SENDTO = 21
SENDROOM = 22
CREATEROOM = 23

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
NOTINROOM = 57
LOGINED = 58


class Client(threading.Thread):
    def __init__(self, server_address=('localhost', 21313)):
        """
        :type server_port: int
        :type server_address: str
        """
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('Chat-Client')
        log_file = logging.FileHandler('Chat-Client.log')
        log_file.setLevel(logging.DEBUG)
        log_stream = logging.StreamHandler()
        log_stream.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(messages)s')
        log_stream.setFormatter(formatter)
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        self.logger.addHandler(log_stream)

        self.server_address = server_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server_address)
        self.message_queue = Queue.Queue()
        self.UserName = None
        self.receive = True

        self.timer_show = None
        self.timer_input = None
        self.default = HALL
        self.starter = None
        self.shut_status = False

    def show(self):
        while not self.message_queue.empty():
            print(self.message_queue.get_nowait())
        self.timer_show = threading.Timer(0.05, self.show, ())
        self.timer_show.start()

    def get_data(self):
        while self.timer_input:
            ch = getch()
            if ch == ' ':
                self.timer_show.cancel()
                msg = raw_input('->')
                self.show()
                end = 0
                operation, end = self.get_word(msg, end)
                if operation == 'sendall':
                    self.send_to_server(SENDALL, msg[end: len(msg)])
                elif operation == 'sendto':
                    user, end = self.get_word(msg, end)
                    if end >= len(msg):
                        print('''user name or messages can't be empty!\r\n''')
                    else:
                        self.send_to_server(SENDTO, user, msg[end: len(msg)])
                elif operation == 'sendroom':
                    room, end = self.get_word(msg, end)
                    if end >= len(msg):
                        print('''room or messages can't be empty!\r\n''')
                    else:
                        self.send_to_server(SENDROOM, room, msg[end: len(msg)])
                elif operation == 'enter':
                    room, end = self.get_word(msg, end)
                    if room == 'hall':
                        self.send_to_server(ENTERHALL)
                    elif room != '':
                        self.send_to_server(ENTERROOM, room)
                    else:
                        print('Room name can\' be blank.\r\n')
                elif operation == 'createroom':
                    room, end = self.get_word(msg, end)
                    if room != '':
                        self.send_to_server(CREATEROOM, room)
                    else:
                        print("Room name can't be blank!\r\n")
                elif operation == 'close':
                    self.shut()
                elif operation == 'help':
                    self.help()
                elif isinstance(operation, str):
                    print('''no the operation: ''' + operation + '\r\n')
                else:
                    print('''illegal input parameters\r\n''')

            elif ch == '\3':
                self.shut()
                break

    def run(self):
        print('1: Login\t 2: register\r\n')
        while True:
            choice = raw_input('Please choose the action number:')
            try:
                choice_num = int(choice)
            except Exception as e:
                self.logger.error('choice error: ' + str(e))
                if choice == '\3':
                    self.receive = False
                    return
                print('Please input the right number.\r\n')
            else:
                if 0 <= choice_num < 3:
                    break
                else:
                    print('Please input the right number.\r\n')
        if choice_num == 1:
            self.login()
        elif choice_num == 2:
            self.register()
        # data = ''
        while self.receive:
            try:
                data = self.socket.recv(BUFFERSIZE)
            except Exception as e:
                self.logger.info('exit' + str(e))
                self.shut()
                self.logger.error('Abnormal stop...')
                break
            # self.message_queue.put(data + '\r\n')
            if not data:
                self.shut()
                self.logger.info('stopping...')
                break
            else:
                self.sparse_data(data)
        self.logger.info('close the socket...')
        self.socket.close()
        exit(0)

    def sparse_data(self, data):
        start = 0
        end = data.find(u'\1', start)
        if end == -1:
            self.logger.error(u'''server's operation error!''')
            return
        operation = ord(data[start: end])
        if operation == REGISTER:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            status = ord(data[start: end])
            if status == HAVENAME:
                print('This name has been used, please rename your account!\r\n')
                self.register(0)
            elif status == NAMEOK:
                self.register(1)
            elif status == FAILED:
                print('Unknown reason made the register failed, please re-register!\r\n')
                self.register(0)
            elif status == SUCCESS:
                print('Congratulation! Registration successful!\r\n')
                print('Please login your account!\r\n')
                self.login()
            else:
                print('Unknown reason made the register failed, please re-register!\r\n')
                self.register(0)
        elif operation == LOGIN:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            status = ord(data[start: end])
            if status == SUCCESS:
                print('Congratulation! login is successful!\r\n')
                print('Press blank key to input data!\r\n')
                # -----------input thread-----------
                # self.starter = thread.start_new_thread(self.timer_starter, (self, ))
                self.show()
                self.timer_input = threading.Timer(0.05, self.get_data, ())
                self.timer_input.start()
            elif status == WRONGPASSWD or status == HAVENONAME:
                print('Username or passwd is not correct!\r\n')
                self.login()
            elif status == LOGINED:
                print('This user name has been logined!')
                self.login()
            elif status == FAILED:
                print('Unknown reason made the register failed, please re-login!\r\n')
                self.login()
            else:
                print('Unknown reason made the register failed, please re-login!\r\n')
                self.login()
        elif operation == SENDALL:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            user = data[start: end]
            self.message_queue.put('[HALL] ' + user + ' said: ' + data[end + 1: len(data)] + '\r\n')
        elif operation == SENDROOM:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            if end == len(data):
                status = ord(data[start: end])
                if NOTINROOM == status:
                    print('You are not in the room!\r\n')
                elif HAVENONAME == status:
                    print('Have no the room!\r\n')
                else:
                    print('Unknown error\r\n!')
            else:
                room = data[start: end]
                start = end + 1
                end = data.find(u'\1', start)
                if end == -1:
                    end = len(data)
                if start == end:
                    self.logger.error(u'''server's operation error!''')
                    return
                user = data[start: end]
                self.message_queue.put('[ROOM: ' + room + '] ' + user + ' said: ' + data[end + 1: len(data)] + u'\r\n')
        elif operation == SENDTO:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            if end == len(data):
                status = ord(data[start: end])
                if status == HAVENONAME:
                    print('He is not online or no the user!\r\n')
            else:
                user = data[start: end]
                self.message_queue.put('[' + user + ']' + ' said: ' + data[end + 1: len(data)] + u'\r\n')
        elif operation == CREATEROOM:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            status = ord(data[start: end])
            if SUCCESS == status:
                print('Congratulation, create room success!\r\n')
                print("You can use 'enter room-name' and 'sendroom room-name' to join in the room and"
                      " send room messages.\r\n")
            elif HAVENAME == status:
                print('The room name has been used.\r\n')
            else:
                print('Unknown errors make it failed!\r\n')
        elif operation == ENTERROOM:
            start = end + 1
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error(u'''server's operation error!''')
                return
            status = ord(data[start: end])
            if SUCCESS == status:
                print('Congratulation, enter the room success!\r\n')
            elif NOTINROOM == status:
                print('The room is not exist or you are not in the room!\r\n')

        elif operation == LOGOUT:
            pass

    def register(self, step=0):
        if step == 0:
            self.UserName = raw_input('User Name: ')
            if self.send_to_server(REGISTER, str(self.UserName)) < len(self.UserName):
                self.logger.error('REGISTER: set code error.')
        elif step == 1:
            password = getpass.getpass()
            count = 1
            while getpass.getpass('Verify your password: ') != password:
                print('The two password do not match! Please re-verify your password.\r\n')
                if count == 3:
                    print('It is failed to verify your password for too many times! Please retype your password.\r\n')
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
            send += u'\1' + s
        return self.socket.send(send)

    def shut(self):
        if not self.shut_status:
            self.receive = False
            self.socket.shutdown(socket.SHUT_RD)
            self.timer_show.cancel()
            self.timer_input = None
            print('Thank your trust!')
            self.shut_status = True

    @staticmethod
    def help():
        print('This is the simple help.\r\n')
        print("sendall messages: send your messages to hall.\r\n")
        print("sendroom room-name messages: send your messages to the room\r\n")
        print("sendto user-name messages: send your messages to the user\r\n")
        print("createroom room-name: create the room named room-name\r\n")
        print("enter room-name: enter the room, and you'll receive the messages from the roommates\r\n")

    @staticmethod
    def timer_starter(client):
        client.show()
        client.get_data()

    @staticmethod
    def get_word(s, start=0):
        begin = start
        length = len(s)
        while begin < length and s[begin].isspace():
            begin += 1
        if begin >= length:
            begin = length
        end = begin
        while end < length and not s[end].isspace():
            end += 1
        return s[begin: end], end


def main():
    client = Client()
    client.start()


if __name__ == '__main__':
    main()
