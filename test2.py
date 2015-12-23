import socket

address = ('localhost', 21313)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(address)
except socket.error as e:
    if e.errno == 98:
        print('OK')
    print('socket.error: ' + str(e))
s.listen(5)
ss, addr = s.accept()
print 'get connected form', addr
s.send
