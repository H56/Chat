import socket
from time import ctime

__author__ = 'HuPeng'

HOST = ''
PORT = 21311
BUFSIZE = 1024
ADDR = (HOST, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen(5)

while True:
    print('waiting for connection...')
    client, addr = server.accept()
    print('...connected from: ' + str(addr))
    while True:
        data = client.recv(BUFSIZE)
        if not data:
            break
        client.send('[%s] %s' %(ctime(), data))
    client.close()
server.close()

