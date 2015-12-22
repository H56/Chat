import socket, select
import Queue

__author__ = 'HuPeng'


class server:
    def __init__(self):
        pass

    def fun(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ('localhost', 8080)
        server_socket.bind(server_address)
        server_socket.listen(1)
        server_socket.setblocking(0)
        timeout = 10
        epoll = select.epoll()
        epoll.register(server_socket.fileno(), select.EPOLLIN)
        message_queues = {}

        fd_to_socket = {server_socket.fileno(): server_socket, }
        while True:
            events = epoll.poll(timeout)
            if not events:
                continue
            for fd, event in events:
                client_socket = fd_to_socket[fd]
                if event & select.EPOLLIN:
                    if client_socket == server_socket:
                        connection, address = server_socket.accept()
                        connection.setblocking(0)
                        epoll.register(connection.fileno(), select.EPOLLIN)
                        fd_to_socket[connection.fileno()] = connection
                        message_queues[connection] = Queue.Queue()
                    else:
                        data = client_socket.recv(1024)
                        if data:
                            message_queues[client_socket].put(data)
                            epoll.modify(fd, select.EPOLLOUT)
                elif event & select.EPOLLOUT:
                    try:
                        msg = message_queues[client_socket].get_nowait()
                    except Queue.Empty:
                        print client_socket.getpeername(), " queue empty"
                        epoll.modify(fd, select.EPOLLIN)
                    else:
                        client_socket.send(msg)
                elif event & select.EPOLLHUP:
                    epoll.unregister(fd)
                    fd_to_socket[fd].close()
                    del fd_to_socket[fd]
        epoll.unregister(server_socket.fileno())
        epoll.close()
        server_socket.close()
ser = server()
ser.fun()
