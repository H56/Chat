import hashlib
import socket
import select
import Queue
import logging
import errno
import access

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

class Server:
    class Info:
        def __init__(self, connection, address):
            self.user = None
            self.address = address
            self.socket = connection
            # personal message queues
            self.message_queues = Queue.Queue()

    def __init__(self, addr, port, timeout=-1):
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

    def server_thread(self):
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

        fd_to_info = {listen_socket.fileno(): self.Info(listen_socket, self.address), }
        while True:
            events = self.epoll.poll(self.timeout)
            if not events:
                continue
            for fd, event in events:
                client_socket = fd_to_info[fd].socket
                if event & select.EPOLLIN:
                    if client_socket == listen_socket:
                        connection, address = listen_socket.accept()
                        connection.setblocking(0)
                        self.epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                        fd_to_info[connection.fileno()] = self.Info(connection, address)
                    else:
                        # data may be very long
                        all_data = ''
                        while True:
                            try:
                                data = client_socket.recv(1024)
                                if not data and not all_data:
                                    self.epoll.unregister(fd)
                                    client_socket.close()
                                    self.logger.debug('%s, %d closed' % (fd_to_info[fd].address[0],
                                                                         fd_to_info[fd].address[1]))
                                    break
                                else:
                                    all_data += data
                            except socket.error, msg:
                                if msg.errno == errno.EAGAIN:
                                    self.logger.debug('%s receive %s' % (str(fd_to_info[fd].address), all_data))
                                    # ----------process the data-----------
                                    self.parse_data(all_data, fd_to_info, fd)
                                    self.epoll.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                else:
                                    self.epoll.unregister(fd)
                                    client_socket.close()
                                    self.logger.error('receive data error, socket error: ' + str(msg))
                                break
                elif event & select.EPOLLOUT:
                    try:
                        msg = fd_to_info[fd].message_queues.get_nowait()
                    except Queue.Empty:
                        print client_socket.getpeername(), " queue empty"
                        self.epoll.modify(fd, select.EPOLLIN)
                    else:
                        client_socket.send(msg)
                elif event & select.EPOLLHUP:
                    self.epoll.unregister(fd)
                    fd_to_info[fd].socket.close()
                    del fd_to_info[fd]
        self.epoll.unregister(listen_socket.fileno())
        self.epoll.close()
        listen_socket.close()

    def parse_data(self, data, fd_to_info, fd):
        end = data.find('\1')
        start = 0
        method = int(data[start: end])
        if method == REGISTER:
            start = end + 1
            end = data.find('\1', start)
            if end != -1 and end < len(data):
                uname = data[start, end]
                start = end + 1
                end = data.find('\1', start)
                passwd = data[start: end]
                self.access.register(uname, uname, passwd)
                fd_to_info[fd].socket.send(chr(method) + '\1' + str(int(True)))
            else:
                uname = data[start, end]
                fd_to_info[fd].socket.send(chr(method) + '\1' + str(int(self.access.have_id(uname))))
        elif method == LOGIN:
            start = end
        elif method == LOGOUT:
            pass


ser = Server()
ser.fun()
