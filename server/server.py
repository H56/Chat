import hashlib
import socket
import select
import Queue
import logging
import errno
import threading
import access
import rooms
import user

__author__ = 'HuPeng'

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
UNLINE = 56
NONTINROOM = 57

Hall_message = Queue.Queue()


class Server(threading.Thread):
    class Info:
        def __init__(self, connection, address):
            self.user = None
            self.address = address
            self.socket = connection
            # personal message queues
            self.message_queues = Queue.Queue()
            self.rooms = []

    def __init__(self, addr='localhost', port=21313, timeout=-1):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('Chat-Server')
        log_file = logging.FileHandler('Chat-Server.log')
        log_file.setLevel(logging.DEBUG)
        log_stream = logging.StreamHandler()
        log_stream.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        log_stream.setFormatter(formatter)
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        self.logger.addHandler(log_stream)

        self.address = (addr, port)
        self.timeout = timeout
        self.epoll = None
        self.access = access.AccessDao()
        self.fd_to_info = {}
        self.user_to_fd = {}
        self.hall_message_queue = Queue.Queue()
        self.rooms_message_queues = {}
        self.hall_message = (0, [])
        self.rooms_message = {}
        self.rooms = rooms.Rooms()
        self.timer = None

    def run(self):
        try:
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_socket.bind(self.address)
            listen_socket.listen(5)
            listen_socket.setblocking(0)
        except socket.error, msg:
            self.logger.error('socket error: ' + str(msg))

        try:
            self.epoll = select.epoll()
            self.epoll.register(listen_socket.fileno(), select.EPOLLIN)
        except select.error, msg:
            self.logger.error('select error: ' + str(msg))

        self.fd_to_info = {listen_socket.fileno(): self.Info(listen_socket, self.address), }
        self.timer = threading.Timer(0.05, self.send_timer, ())
        while True:
            events = self.epoll.poll(self.timeout)
            if not events:
                continue
            for fd, event in events:
                client_socket = self.fd_to_info[fd].socket
                if event & select.EPOLLIN:
                    if client_socket == listen_socket:
                        connection, address = listen_socket.accept()
                        connection.setblocking(0)
                        self.epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                        self.fd_to_info[connection.fileno()] = self.Info(connection, address)
                        print('connet ok, from' + address)
                    else:
                        # data may be very long
                        all_data = ''
                        while True:
                            try:
                                data = client_socket.recv(1024)
                                if not data and not all_data:
                                    self.epoll.unregister(fd)
                                    client_socket.close()
                                    self.logger.debug('%s, %d closed' % (self.fd_to_info[fd].address[0],
                                                                         self.fd_to_info[fd].address[1]))
                                    break
                                else:
                                    all_data += data
                            except socket.error, msg:
                                if msg.errno == errno.EAGAIN:
                                    self.logger.debug('%s receive %s' % (str(self.fd_to_info[fd].address), all_data))
                                    # ----------process the data-----------
                                    self.parse_data(all_data, fd)
                                    self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                else:
                                    self.epoll.unregister(fd)
                                    client_socket.close()
                                    self.logger.error('receive data error, socket error: ' + str(msg))
                                break
                elif event & select.EPOLLOUT:
                    try:
                        msg = self.fd_to_info[fd].message_queues.get_nowait()
                    except Queue.Empty:
                        print client_socket.getpeername(), " queue empty"
                        self.epoll.modify(fd, select.EPOLLIN)
                    else:
                        client_socket.send(msg)
                    # send hall message
                    if self.hall_message[1] > 0:
                        self.hall_message[1] -= 1
                        for msg in self.hall_message[1]:
                            client_socket.send(msg)
                    # send room message
                    for room in self.fd_to_info[fd].rooms:
                        self.rooms_message[room][0] -= 1
                        for msg in self.rooms_message[room][1]:
                            client_socket.send(msg)
                    # send personal message
                    msg_queues = self.fd_to_info[fd].message_queues
                    while not msg_queues.empty():
                        client_socket.send(msg_queues.get_nowait())
                elif event & select.EPOLLHUP:
                    self.epoll.unregister(fd)
                    self.fd_to_info[fd].socket.close()
                    del self.fd_to_info[fd]
        self.epoll.unregister(listen_socket.fileno())
        self.epoll.close()
        listen_socket.close()

    def send_timer(self):
        if self.hall_message_queue[0] > 0:
            self.timer = threading.Timer(0.02, self.send_timer(), ())
            return
        for room in self.rooms_message:
            if self.rooms_message[room][0] > 0:
                self.timer = threading.Timer(0.02, self.send_timer(), ())
                return
        del self.hall_message[1][:]
        is_hall = False
        while not self.hall_message_queue.empty():
            self.hall_message[1].append(self.hall_message_queue.get_nowait())
        if len(self.hall_message_queue[1]) != 0:
            is_hall = True
        if is_hall:
            self.hall_message_queue[0] = len(self.user_to_fd)
            for usr in self.user_to_fd:
                self.epoll.modify(self.user_to_fd[usr], select.EPOLLOUT)
        else:
            for usr in self.user_to_fd:
                if not self.fd_to_info[self.user_to_fd[usr]].message_queues.empty() \
                        or len(self.fd_to_info[self.user_to_fd[usr]].room) > 0:
                    self.epoll.modify(self.user_to_fd[usr], select.EPOLLOUT)
        self.timer = threading.Timer(0.05, self.send_timer(), ())

    def parse_data(self, data, fd):
        end = data.find(u'\1')
        start = 0
        method = int(data[start: end])
        if method == SENDALL:
            self.hall_message_queue.put(self.fd_to_info[fd].user.name + data[end + 1: -1])
        elif method == SENDROOM:
            start = end + 1
            end = data.find(u'\1', start)
            room = data[start: end]
            if room in self.rooms_message_queues:
                if room in self.fd_to_info[fd].room:
                    self.rooms_message_queues[room].put(self.fd_to_info[fd].user.name + data[end + 1: -1])
                else:
                    self.fd_to_info[fd].socket.send(chr(method) + '\1' + chr(NONTINROOM))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
        elif method == SENDTO:
            start = end + 1
            end = data.find(u'\1', start)
            uname = data[start: end]
            if self.user_to_fd.has_key(uname):
                self.fd_to_info[self.user_to_fd[uname]].message_queues.put(
                    self.fd_to_info[fd].user.name + data[end + 1: -1])
            # elif self.access.have_id(uname):
            #     self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(UNLINE))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
        elif method == REGISTER:
            start = end + 1
            end = data.find(u'\1', start)
            uname = data[start: end]
            if end != -1 and end < len(data):
                start = end + 1
                end = data.find(u'\1', start)
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
            start = end + 1
            end = data.find(u'\1', start)
            uname = data[start: end]
            passwd = data[end + 1: -1]
            status = self.access.is_legal(uname, passwd)
            if status == 1:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(SUCCESS))
                self.fd_to_info[fd].user = user.User(uname, status)
            elif status == -1:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(HAVENONAME))
            else:
                self.fd_to_info[fd].socket.send(chr(method) + u'\1' + chr(WRONGPASSWD))
        elif method == LOGOUT:
            self.fd_to_info[fd].user.logout()
            del self.fd_to_info[fd]

    def __del__(self):
        self.epoll.close()


def main():
    server = Server()
    server.start()


if __name__ == '__main__':
    main()
