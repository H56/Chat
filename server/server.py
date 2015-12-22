import socket, select
import Queue

__author__ = 'HuPeng'

class server:
    def __init__(self):
        pass

    def fun(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ("192.168.1.5", 8080)
        serversocket.bind(server_address)
        serversocket.listen(1)
        print  "�����������ɹ�������IP��" , server_address
        serversocket.setblocking(0)
        timeout = 10
        #�½�epoll�¼����󣬺���Ҫ��ص��¼���ӵ�����
        epoll = select.epoll()
        #��ӷ���������fd���ȴ����¼�����
        epoll.register(serversocket.fileno(), select.EPOLLIN)
        message_queues = {}

        fd_to_socket = {serversocket.fileno():serversocket,}
        while True:
          print "�ȴ������......"
          #��ѯע����¼�����
          events = epoll.poll(timeout)
          if not events:
             print "epoll��ʱ�޻���ӣ�������ѯ......"
             continue
          print "��" , len(events), "�����¼�����ʼ����......"
          for fd, event in events:
             socket = fd_to_socket[fd]
             #�ɶ��¼�
             if event & select.EPOLLIN:
                 #����socketΪ����������������������
                 if socket == serversocket:
                    connection, address = serversocket.accept()
                    print "�����ӣ�" , address
                    connection.setblocking(0)
                    #ע��������fd�������¼�����
                    epoll.register(connection.fileno(), select.EPOLLIN)
                    fd_to_socket[connection.fileno()] = connection
                    message_queues[connection]  = Queue.Queue()
                 #����Ϊ�ͻ��˷��͵�����
                 else:
                    data = socket.recv(1024)
                    if data:
                       print "�յ����ݣ�" , data , "�ͻ��ˣ�" , socket.getpeername()
                       message_queues[socket].put(data)
                       #�޸Ķ�ȡ����Ϣ�����ӵ��ȴ�д�¼�����
                       epoll.modify(fd, select.EPOLLOUT)
             #��д�¼�
             elif event & select.EPOLLOUT:
                try:
                   msg = message_queues[socket].get_nowait()
                except Queue.Empty:
                   print socket.getpeername() , " queue empty"
                   epoll.modify(fd, select.EPOLLIN)
                else :
                   print "�������ݣ�" , data , "�ͻ��ˣ�" , socket.getpeername()
                   socket.send(msg)
             #�ر��¼�
             elif event & select.EPOLLHUP:
                epoll.unregister(fd)
                fd_to_socket[fd].close()
                del fd_to_socket[fd]
        epoll.unregister(serversocket.fileno())
        epoll.close()
        serversocket.close()
