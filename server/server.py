import random
import socket
import select
import Queue
import errno
import threading
import time
import access
import rooms
import user
from calculator import calculator
from logger import Logger

__author__ = 'HuPeng'

BUFFERSIZE = 1024

REGISTER = 10
LOGIN = 11
LOGOUT = 12
SERVERMESSAGE = 13

SENDALL = 20
SENDTO = 21
SENDROOM = 22
CREATEROOM = 23
LEAVEROOM = 24
GAME21 = 25
GAME21WINNER = 26

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
UNLINE = 56
NOTINROOM = 57
LOGINED = 58
GAMEOVER = 59

Hall_message = Queue.Queue()


class Server(threading.Thread):
    class Info:
        def __init__(self, connection, address):
            self.user = None
            self.address = address
            self.socket = connection
            # personal messages queues
            self.message_queues = Queue.Queue()
            self.rooms = []

    def __init__(self, addr='localhost', port=2131, timeout=-1):
        threading.Thread.__init__(self)
        self.logger = Logger()
        self.address = (addr, port)
        self.timeout = timeout
        self.epoll = None
        self.access = None
        self.fd_to_info = {}
        self.user_to_fd = {}
        self.hall_message_queue = Queue.Queue()
        # self.rooms_message_queues = {}
        self.rooms = rooms.Rooms()
        self.timer = None
        self.game_timer = None
        self.game21 = None
        self.game_result = {}
        self.evaluation = None
        self.listen_socket = None

    def run(self):
        self.access = access.AccessDao()
        try:
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind(self.address)
            self.listen_socket.listen(1)
            self.listen_socket.setblocking(0)
        except socket.error, msg:
            self.logger.error('socket error: ' + str(msg))

        try:
            self.epoll = select.epoll()
            self.epoll.register(self.listen_socket.fileno(), select.EPOLLIN)
        except select.error, msg:
            self.logger.error('select error: ' + str(msg))

        self.fd_to_info = {self.listen_socket.fileno(): self.Info(self.listen_socket, self.address), }
        self.timer = threading.Timer(0.5, self.send_timer, ())
        self.timer.start()
        self.game_timer = threading.Timer(self.compute_time(), self.game21_timer, ())
        self.game_timer.start()
        while True:
            events = self.epoll.poll(self.timeout)
            if not events:
                continue
            for fd, event in events:
                client_socket = self.fd_to_info[fd].socket
                if fd == self.listen_socket.fileno():
                    connection, address = self.listen_socket.accept()
                    connection.setblocking(0)
                    self.epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                    self.fd_to_info[connection.fileno()] = self.Info(connection, address)
                    print('connet ok, from' + str(address))
                elif event & select.EPOLLIN:
                    # data may be very long
                    all_data = ''
                    while True:
                        try:
                            data = client_socket.recv(BUFFERSIZE)
                            if not data and not all_data:
                                # self.epoll.unregister(fd)
                                # client_socket.close()
                                self.logger.debug('%s, %d closed' % (self.fd_to_info[fd].address[0],
                                                                     self.fd_to_info[fd].address[1]))
                                # self.epoll.modify(fd, 0)
                                # client_socket.shutdown(socket.SHUT_RDWR)
                                self.remove(fd)
                                break
                            else:
                                all_data += data
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                self.logger.debug('%s receive %s' % (str(self.fd_to_info[fd].address), all_data))
                                # ----------process the data-----------
                                self.parse_data(all_data, fd)
                            else:
                                # self.epoll.modify(fd, 0)
                                # client_socket.shutdown(socket.SHUT_RDWR)
                                self.remove(fd)
                                self.logger.error('receive data error, socket error: ' + str(msg))
                            break
                elif event & select.EPOLLHUP:
                    self.remove(fd)
                elif event & select.EPOLLOUT:
                    # try:
                    #     msg = self.fd_to_info[fd].message_queues.get_nowait()
                    # except Queue.Empty:
                    #     print client_socket.getpeername(), " queue empty"
                    #     self.epoll.modify(fd, select.EPOLLIN)
                    # else:
                    #     client_socket.send(msg)
                    # send messages
                    msg_queues = self.fd_to_info[fd].message_queues
                    while not msg_queues.empty():
                        send_msg = msg_queues.get_nowait()
                        send_len = 0
                        while True:
                            send_len += client_socket.send(send_msg[send_len:])
                            if send_len >= len(send_msg):
                                break
                            elif send_len == 0:
                                self.logger.info('send to ' + self.fd_to_info[fd].user.uid + ' failed')
                                break
                    self.epoll.modify(fd, select.EPOLLIN | select.EPOLLET)
                else:
                    continue

        self.epoll.unregister(self.listen_socket.fileno())
        self.epoll.close()
        self.listen_socket.close()

    def send_timer(self):
        is_hall = not self.hall_message_queue.empty()
        fd_set = set()
        # hall messages
        while not self.hall_message_queue.empty():
            msg = self.hall_message_queue.get_nowait()
            for fd in self.fd_to_info:
                if self.fd_to_info[fd].user:
                    self.fd_to_info[fd].message_queues.put(msg)
                    self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)
        # personal messages
        if not is_hall:
            for fd in self.fd_to_info:
                if not self.fd_to_info[fd].message_queues.empty():
                    fd_set.add(fd)
        # room messages
        for room in self.rooms:
            msgs = self.rooms[room].get_all_messages()
            if len(msgs) > 0:
                for member in self.rooms[room]:
                    try:
                        fd = self.user_to_fd[member]
                    except KeyError:
                        # not in the online users
                        pass
                    else:
                        if not is_hall:
                            fd_set.add(fd)
                        for msg in msgs:
                            self.fd_to_info[fd].message_queues.put(msg)

        if not is_hall:
            for fd in fd_set:
                self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)
        self.timer = threading.Timer(0.05, self.send_timer, ())
        self.timer.start()

    def parse_data(self, data, fd):
        end = data.find(u'\1')
        if end == -1:
            self.logger.error('Wrong format!')
            return
        start = 0
        try:
            method = ord(data[start: end])
        except Exception as e:
            self.logger.error('Wrong format: ' + str(e))
            return
        start = end + 1
        if method == SENDALL:
            self.hall_message_queue.put(chr(method) + '\1' + self.fd_to_info[fd].user.name + '\1' + data[start: len(data)])
        elif method == SENDROOM:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            room = data[start: end]
            if room in self.rooms:
                if self.fd_to_info[fd].user.uid in self.rooms[room]:
                    # self.rooms_message_queues[room].put(self.fd_to_info[fd].user.name + '\1' + data[end + 1: len(data)])
                    self.rooms[room].add_message(chr(method) + '\1' + room + '\1' + self.fd_to_info[fd].user.name + '\1' + data[end + 1: len(data)])
                else:
                    self.fd_to_info[fd].socket.send(chr(method) + '\1' + chr(NOTINROOM))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
        elif method == SENDTO:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            uname = data[start: end]
            if uname in self.user_to_fd:
                self.fd_to_info[self.user_to_fd[uname]].message_queues.put(chr(method) + '\1' +
                    self.fd_to_info[fd].user.name + '\1' + data[end + 1: len(data)])
            # elif self.access.have_id(uname):
            #     self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(UNLINE))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
        elif method == REGISTER:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            uname = data[start: end]
            if end != -1 and end < len(data):
                start = end + 1
                end = data.find(u'\1', start)
                if end == -1:
                    end = len(data)
                if start == end:
                    self.logger.error('Wrong format!')
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                    return
                passwd = data[start: end]
                status = self.access.register(uname, uname, passwd)
                if status:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
                else:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
            else:
                status = self.access.have_id(uname)
                if status:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENAME))
                else:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(NAMEOK))
        elif method == LOGIN:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            uname = data[start: end]
            passwd = data[end + 1: len(data)]
            if uname in self.user_to_fd:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(LOGINED))
                return
            status = self.access.is_legal(uname, passwd)
            if status == 1:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
                self.user_to_fd[uname] = fd
                self.fd_to_info[fd].user = user.User(uname, status)
                # self.logger.debug('User: [' + uname + '] login success')
                print('User: [' + uname + '] login success')
                self.logger.info('User: [' + uname + '] login success')
            elif status == -1:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(WRONGPASSWD))

        elif method == ENTERROOM:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            room = data[start: end]
            if room in self.rooms:
                ok = self.rooms[room].add_member(self.fd_to_info[fd].user.uid)
                if ok:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
                else:
                    self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
            else:
                # self.logger.warn('No room ' + str(room))
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(NOTINROOM))

        elif method == LEAVEROOM:
            end = data.find(u'\1', start)
            if end == -1:
                end = len(data)
            if start == end:
                self.logger.error('Wrong format!')
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
                return
            room = data[start: end]
            if room in self.rooms:
                self.rooms[room].remove(self.fd_to_info[fd].user.uid)
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(NOTINROOM))

        elif method == CREATEROOM:
            room, end = self.get_next(data, start, method, fd)
            if room == -1:
                return
            if self.access.create_room(room, room, self.fd_to_info[fd].user.uid):
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
                self.rooms.add(room, room, self.fd_to_info[fd].user.uid)
                self.rooms[room].add_member(self.fd_to_info[fd].user.uid)
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENAME))
        elif method == SERVERMESSAGE:
            option, end = self.get_next(data, start, method, fd)
            if option != -1:
                option = ord(option)
                if option == GAME21:
                    if not self.game21:
                        self.fd_to_info[fd].message_queues.put(chr(method) + u'\1' + chr(GAMEOVER))
                        return
                    start = end + 1
                    solution = data[start:]
                    if len(solution) > 20:
                        self.fd_to_info[fd].message_queues.put(chr(method) + u'\1' + chr(FAILED))
                        return
                    nums = []
                    try:
                        result = calculator(solution, nums_list=nums)
                    except Exception as e:
                        self.fd_to_info[fd].message_queues.put(chr(method) + u'\1' + chr(FAILED))
                    else:
                        if len(nums) != len(self.game21) or sorted(nums) != sorted(self.game21):
                            self.fd_to_info[fd].message_queues.put(chr(method) + u'\1' + chr(FAILED))
                        else:
                            result = 21
                            if result == 21:
                                self.game21 = []
                                self.game_result = {}
                                self.evaluation.cancel()
                                self.send_winner(self.fd_to_info[fd].user.uid)
                            elif result not in self.game_result:
                                self.game_result[result] = fd

        elif method == LOGOUT:
            # self.fd_to_info[fd].user.logout()
            # del self.user_to_fd[self.fd_to_info[fd].user.uid]
            # del self.fd_to_info[fd]
            pass

    def game21_timer(self):
        self.game21 = []
        game21_str = ''
        for i in range(0, 4):
            self.game21.append(random.randint(1, 10))
            game21_str += '\1' + str(self.game21[i])
        for fd in self.fd_to_info:
            if self.fd_to_info[fd].user:
                self.fd_to_info[fd].message_queues.put(chr(SERVERMESSAGE) + u'\1' + chr(GAME21) + game21_str)
                self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)
        self.evaluation = threading.Timer(15, self.evaluation21_timer, ())
        self.evaluation.start()
        self.game_timer = threading.Timer(self.compute_time(), self.game21_timer, ())
        self.game_timer.start()

    def evaluation21_timer(self):
        self.game21 = []
        if self.game_result:
            max_index = max(self.game_result)
            fd = self.game_result[max_index]
            if fd in self.fd_to_info:
                winner = self.fd_to_info[fd].user.uid
            else:
                winner = -1
            self.game_result = {}
        else:
            winner = -1
        self.send_winner(winner)

    def send_winner(self, winner):
        if winner == -1:
            winner = ''
        for fd in self.fd_to_info:
            if self.fd_to_info[fd].user:
                self.fd_to_info[fd].message_queues.put(chr(SERVERMESSAGE) + u'\1' + chr(GAME21WINNER) + '\1' + winner)
                self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)

    def __del__(self):
        self.epoll.close()

    def remove(self, fd):
        self.epoll.unregister(fd)
        self.fd_to_info[fd].socket.close()
        if self.fd_to_info[fd].user:
            name = self.fd_to_info[fd].user.uid
            # for room in self.rooms:
            #     self.rooms[room].remove(name)
            self.fd_to_info[fd].user.logout()
            del self.user_to_fd[name]
            # self.logger.debug('User [' + name + '] logout success!')
            print('User [' + name + '] logout success!')
        del self.fd_to_info[fd]

    def get_next(self, data, start, method, fd):
        end = data.find(u'\1', start)
        if end == -1:
            end = len(data)
        if start == end:
            self.logger.error('Wrong format!')
            self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(FAILED))
            return -1, end
        return data[start: end], end

    @staticmethod
    def compute_time():
        # now = time.localtime(time.time())
        # if now.tm_min + now.tm_sec / 60.0 < 30:
        #     ret = (30 - now.tm_min) * 60 - now.tm.sec
        # else:
        #     ret = (60 - now.tm_min) * 60 - now.tm_sec
        min = 29
        sec = 0
        if min + sec / 60.0 < 30:
            ret = (30 - min) * 60 - sec
        else:
            ret = (60 - min) * 60 - sec
        return ret

def main():
    server = Server()
    server.start()


if __name__ == '__main__':
    main()
