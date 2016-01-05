#!/usr/bin/python
# -*- coding: utf-8 -*-
from threading import Timer
import sys
from getch import getch
import socket
import time
import logging

timer1 = None
time2 = None
s = ''


logger = logging.getLogger("network-client")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("network-client.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == "__main__":
    try:
        connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error(msg)

    try:
        connFd.connect(("localhost", 21313))
        logger.debug("connect to network server success")
    except socket.error,msg:
        logger.error(msg)

    while True:
        data = raw_input("input: ")
        if data == '\3':
            break
        if connFd.send(data) != len(data):
            logger.error("send data to network server failed")
            break
        readData = connFd.recv(1024)
        print readData
        time.sleep(1)

    connFd.close()

def generate(a, b):
    global timer1
    global s
    s += str((a, b)) + '\r\n'
    timer1 = Timer(1, generate, (a + 1, b + 1))
    timer1.start()


def output():
    global time2
    global s
    if len(s) > 0:
        print(s)
    s = ''
    time2 = Timer(0.1, output, ())
    time2.start()


generate(1, 2)
output()
command = ""
while True:
    ch = getch()
    if ch == '\3':
        print('Exist')
        break
    time2.cancel()
    s1 = raw_input('Message:')
    print('input: ' + s1)
    output()

timer1.cancel()
time2.cancel()
